import logging;
import traceback;
import from typing { Union }
import from logging { Logger }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.memory.frame { Frame }
import from jivas.agent.action.action { Action }

node State(GraphNode) {
    # represents an execution on a subgraph on the agent action graph

    has collection_id:str = "";
    has label: str = "";
    has description: str = "specialized state";
    has enabled: bool = True;
    has state_info: dict = {};


    #llm model parameters
    has model_action: str = "LangChainModelAction";
    has model_name: str = "gpt-4o";
    has model_max_tokens:int = 4096;
    has model_temperature: float = 0.3;
    has history: bool = True;
    has history_size: int = 3;
    has max_statement_length: int = 2048;

    has extraction_prompt:str = """
        Review the user's message and the conversation history to accurately extract the following entities.
        Only extract data that has not been specifically cancelled.
        Be strict on the constraints specified for each entity. Return a JSON object with keys exactly as listed below.
        Include only keys for which you could extract a valid value adhering to all constraints.

        Entities to extract:
        {entities}

        Return ONLY the JSON object with the extracted entities, no delimiters. Do not include any other text or explanation.
        The JSON must have the following structure (only include keys with valid values):
        {sample_json}
    """;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);


    def postinit {
        super.postinit();
        # list of node attributes which are protected from update operation
        self.protected_attrs += ['_package', 'label', 'version', 'agent_id'];
        # list of node attributes which should be excluded from export
        self.transient_attrs += ['agent_id'];
    }

    # override to execute operations upon enabling of action
    def on_enable() { }

    # override to execute operations upon disabling of action
    def on_disable() { }

    def touch(frame:Frame) -> bool {
        frame_node = frame.frame_node;

        state_data = frame_node.data_get(key=f"{frame.action_label}_results");
        if state_data{
            state_value = state_data.get(self.label, None);
            confirmed = state_data.get("confirm_response", False);
        }
        else{
            state_value = {};
            confirmed = False;
        }

        if state_value or confirmed{
            return False;
        }

        if (conditional := self.state_info.get('conditional', {})) {

            for (field, expected_value) in conditional.items(){
                actual_value = state_data.get(field, None);
                if actual_value != expected_value{
                    return False;
                }
            }
        }

        # authorize the walker to run this action
        return True;

    }

    def run(frame:Frame)->Union[str, bool]{
        agent_node = frame.agent_node;
        frame_node = frame.frame_node;
        required = self.state_info.get("required","");

        prompt = self.generate_extraction_prompt();

        extraction_result = self.call_llm(prompt=prompt, history=True, json_only=True, frame_node=frame_node, agent_node=agent_node);

        if required is True and not extraction_result{
            question = self.state_info.get("question", "");
            constraints = self.state_info.get("constraints", {});
            description = constraints.get("description", "");

            directive = "Tailor your response to get the information needed based on the following description: \n" + description + "\n Eg." + question;

            if(options:= constraints.get("options", "")){
                directive = directive + "\n They can choose from the list of options below\n" + str(options);
            }
            frame_node.data_set(key="directive", value=directive);
            return directive;
        }
        elif required == False {
            if not extraction_result{
                # set extraction result to N/A
                extraction_result = {self.label:"N/A"};
                self.update_responses(extraction_result, frame);
            }
        }
        if extraction_result{
            # store the result in the frame node
            self.update_responses(extraction_result, frame);
            return True;
        }
    }

    def generate_extraction_prompt() -> str {
        # accepts the question index schema and prepares an extraction prompt
        entities_list = [];
        sample_json_lines = [];

        if(constraints := self.state_info.get('constraints', {})){

            desc = constraints.get('description', '');
            other_constraints = {k: v for (k, v) in constraints.items() if k != 'description'};
            constraint_strs = [f"{k}: {v}" for (k, v) in other_constraints.items()];
            constraint_part = f" ({', '.join(constraint_strs)})" if constraint_strs else "";
            entities_list.append(f"- {self.state_info.get("name")}: {desc}{constraint_part}");
            sample_json_lines.append(f"  '{self.state_info.get("name")}': '<extracted value>'");


            entities = "\n".join(entities_list);
            sample_json = '{\n' + ',\n'.join(sample_json_lines) + '\n}';
            # prepate the prompt
            prompt = self.extraction_prompt.format(entities=entities, sample_json=sample_json);
            # escape the conflicting symbols
            prompt = prompt.replace('{', '{{').replace('}','}}');

            return prompt;
        }
        else {
            return "";
        }
    }

    def call_llm(prompt:str, history:Union[bool,None] = None, json_only:bool = False, frame_node:Frame, agent_node:GraphNode) -> Union[str, dict, None] {
        # performs function tool calling for extracting question responses based on question
        prompt_messages = [];

        if not prompt {
            return None;
        }

        use_history = self.history;
        if history is not None {
            use_history = history;
        }
        visitor_utterance = frame_node.data_get(key="visitor_utterance");
        if not visitor_utterance {
            return None;
        }

        prompt_messages = [
            {"human":visitor_utterance},
            {"system":prompt}
        ];

        # prepare the final prompt with history.
        if (use_history) {
            statements = frame_node.get_transcript_statements(interactions = self.history_size, max_statement_length = self.max_statement_length, with_events = True);

            if (statements) {
                # prepend statements to the prompt messages
                prompt_messages = statements + prompt_messages;
            }

        }

        model_action = agent_node.get_action(action_label=self.model_action);

        if model_action {
            model_action_result = model_action.call_model(
            prompt_messages=prompt_messages,
            prompt_variables={},
            model_name=self.model_name,
            model_temperature=self.model_temperature,
            model_max_tokens=self.model_max_tokens
        );

            if model_action_result {
                if json_only {
                    return model_action_result.get_json_result();
                } else {
                    return model_action_result.get_result();
                }
            }
            else {
                return None;
            }
        }

        # return None;
    }

    def update_responses(responses:dict, frame:Frame) {
        stored_responses = frame.frame_node.data_get(key=f"{frame.action_label}_results");

        if type(stored_responses) is not dict or not stored_responses {
            stored_responses = {};
        }

        # Merge new responses into stored_responses
        for (key, value) in responses.items() {
            stored_responses[key] = value;
        }

        frame.frame_node.data_set(key=f"{frame.action_label}_results", value=stored_responses);
    }


}
