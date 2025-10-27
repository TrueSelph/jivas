import logging;
import traceback;
import from typing { Union }
import from logging { Logger }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.action.subgraph_action.state { State }
import from jivas.agent.memory.frame { Frame }



node CompletedState(GraphNode) {
    # Represents an execution on a subgraph on the agent action graph
    has collection_id: str = "";
    has auto_confirm: bool = False;
    has model_action: str = "LangChainModelAction";
    has model_name: str = "gpt-4o";
    has model_max_tokens:int = 4096;
    has model_temperature: float = 0.3;
    has history: bool = True;
    has history_size: int = 3;
    has max_statement_length: int = 2048;
    has label: str = "";
    has state_info:dict = {};
    has enabled: bool = True;

    has directive: str = """
        Perform the following steps to confirm user submission:
        a. Summarize submission:
            - Extract all user-provided submission details from:
                {summary}
            - Format them as a clear, bulleted list under a statement that indicates that it is a list of the information gathered.
            - Do not put internal settings such as "revised" or "confirm response" in the displayed list
            - Do not put any items on the list with a value of N/A
        b. Request Explicit Confirmation:
            Present the key and summary followed by:
                - a request to know if the presented details are accurate
                - a message to inform the user that they can request changes or cancel altogether.
    """;

    has prompt:str = """
        Analyze **ONLY the latest user message** the conversation history above. Detect ONLY explicit signals for confirmation (yes/affirmative)
        Follow these rules:

        # Confirmation Detection
        Set "confirm_response" to true for: "yes", "sure", "confirmed", "yeah", "yep", "absolutely", "okay" + clear context.
        Set "confirm_response" to false ONLY for explicit negative or revision signals, including:
            - Direct negatives: "no"
            - Revision or correction requests: "I'd like to make an adjustment", "need to make a change", "revision", "change my answer", "not correct", "incorrect", "needs update"
            - Suggestions to edit or change: phrases like "actually, please change...", "no, can you change...", "can you update...", "please edit...", "I'd like to change...", "can you correct...", "let's fix...", "could you modify...", or similar expressions indicating a desire to alter or correct previous information.


        Return ONLY a JSON structure with a single detected key (confirm_response) set to true,
        or "confirm_response" set to false otherwise. No commentary.
        If nothing is detected, return an empty JSON object. No delimiters!
    """;

    # override to execute operations upon enabling of action
    def on_enable() { }

    # override to execute operations upon disabling of action
    def on_disable() { }

    def touch(frame:Frame) -> bool {
        return True;
    }

    def run(frame:Frame) -> Union[str, bool] {
        frame_node = frame.frame_node;
        agent_node = frame.agent_node;

        states_data = frame.frame_node.data_get(key=f"{frame.action_label}_results");
        revised = states_data.get("revised", False);

        if self.auto_confirm {
            branch_choice_response ={"confirm_response": True};
            self.update_responses(branch_choice_response, frame);
        }
        elif not revised{
            # Check for confirmation in the latest user message
            branch_choice_response = self.call_llm(self.prompt, history=True, json_only=True, frame_node=frame_node, agent_node=agent_node);
            self.update_responses(branch_choice_response, frame);
        }
        elif revised{
            branch_choice_response = {};
        }

        confirmed = branch_choice_response.get('confirm_response', None);


        # If there is no confirmation or abortion
        if not branch_choice_response {
            # Retrieve the interview session from the frame node
            responses = frame_node.data_get(key=f"{frame.action_label}_results");

            if responses and isinstance(responses, dict) and len(responses) > 0 {
                summary_lines = [];
                for (field, value) in responses.items() {
                    summary_lines.append(f"- **{field}**: {value}");
                }
                summary = "\n".join(summary_lines);
            } else {
                summary = "";
            }

            directive = self.directive.replace("{summary}", summary);

            # Change revised in frame to false
            revised_state = {"revised":False};
            self.update_responses(revised_state, frame);
            return directive;
        }
        elif confirmed{
            return True;
        }
        elif not confirmed{
            return False;
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
    }

    def update_responses(responses:dict, frame:Frame) {
        print(f"New responses to merge: {responses}");
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