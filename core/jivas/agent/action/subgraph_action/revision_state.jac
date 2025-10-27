import logging;
import traceback;
import from typing { Union }
import from logging { Logger }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.action.subgraph_action.state { State }
import from jivas.agent.memory.frame { Frame }



node RevisionState(GraphNode) {
    # Represents an execution on a subgraph on the agent action graph
    has collection_id: str = "";
    has label: str = "";
    has state_info:dict = {};
    has states:list = [];
    has model_action: str = "LangChainModelAction";
    has model_name: str = "gpt-4o";
    has model_max_tokens:int = 4096;
    has model_temperature: float = 0.3;
    has history: bool = True;
    has history_size: int = 3;
    has max_statement_length: int = 2048;
    has directive: str = "Encourage the user to suggest any changes to the information provided.";
    has enabled: bool = True;

    has prompt:str = """
        Review the user's message and the recorded responses to accurately extract the following entities and update the relevant recorded responses.
        Be strict on the constraints specified for each entity. Return a JSON object with keys exactly as listed below.
        Include only keys for which you could extract a valid revised value adhering to all constraints.
        Do not extract value if it is the same as the one in responses but always extract if the user states a different value from the one in the recorded responses.

        Entities to extract:
        {entities}

        Recorded responses:
        {responses}

        Return ONLY the JSON object with the revised entities, no delimiters. Do not include any other text or explanation.
        Return an empty JSON if no changes were made.
        The JSON must have the following structure (only include keys with valid values):
        {sample_json}
    """;

    # override to execute operations upon enabling of action
    def on_enable() { }

    # override to execute operations upon disabling of action
    def on_disable() { }

    def touch(frame:Frame) -> bool {
        states_data = frame.frame_node.data_get(key=f"{frame.action_label}_results");
        state_value = states_data.get("confirm_response", "");
        if state_value{
            return False;
        }
        else{
            return True;
        }
    }

    def run(frame:Frame) -> Union[str, bool] {
        frame_node = frame.frame_node;
        agent_node = frame.agent_node;

        # Check for any changes in the latest user message
        prompt = self.generate_revision_extraction_prompt(frame);
        extraction_result = self.call_llm(prompt, history=True, json_only=True, frame_node=frame_node, agent_node=agent_node);

        # If there is no confirmation or abortion
        if extraction_result{
            # store the result in the frame node
            self.update_responses(extraction_result, frame);

            #clearing confirm response so that completed state can processs it
            confirm_response = {"confirm_response":{}, "revised":True};
            self.update_responses(confirm_response, frame);
            return True;
        }
        else{
            directive = self.directive;
            return directive;
        }
    }

    def generate_revision_extraction_prompt(frame:Frame) -> str {
        # prepares the revision extraction prompt

        entities_list = [];
        sample_json_lines = [];

        for state_info in self.states {
            constraints = state_info.get('constraints', {});

            if not constraints {
                continue;
            }

            desc = constraints.get('description', '');
            other_constraints = {k: v for (k, v) in constraints.items() if k != 'description'};
            constraint_strs = [f"{k}: {v}" for (k, v) in other_constraints.items()];
            constraint_part = f" ({', '.join(constraint_strs)})" if constraint_strs else "";
            entities_list.append(f"- {state_info.get("name")}: {desc}{constraint_part}");
            sample_json_lines.append(f"  '{state_info.get("name")}': '<extracted value>'");
        }

        responses = frame.frame_node.data_get(key=f"{frame.action_label}_results");
        # Convert the responses dict to a markdown bulleted list
        if responses and isinstance(responses, dict) and len(responses) > 0 {
            summary_lines = [];
            for (field, value) in responses.items() {
                summary_lines.append(f"- **{field}**: {value}");
            }
            responses = "\n".join(summary_lines);
        }

        entities = "\n".join(entities_list);
        sample_json = '{\n' + ',\n'.join(sample_json_lines) + '\n}';
        # prepate the prompt
        prompt = self.prompt.format(entities=entities, responses=responses, sample_json=sample_json);
        # escape the conflicting symbols
        prompt = prompt.replace('{', '{{').replace('}','}}');

        return prompt;
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