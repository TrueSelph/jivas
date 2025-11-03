import logging;
import traceback;
import from typing { Union }
import from logging { Logger }
import from jivas.agent.action.subgraph_action.state { State }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.memory.frame { Frame }


node InitialState(State) {
    # Represents an execution on a subgraph on the agent action graph

    has collection_id: str = "";
    has label: str = "";
    has enabled: bool = True;
    has state_info:dict = {};
    has abort:bool = False;

    has directive:str = "Tell the user that you will cancel the process";
    has prompt: str = """
        Analyze **ONLY the latest user message** the conversation history above. Detect ONLY explicit signals for
        conversation termination (abort/stop), decline-to-answer (no answer/can't respond).
        Follow these rules:
        # Abort Detection
        Set "abort_response" to true for: "stop", "cancel", "exit", "end chat", "nevermind", "abort", "terminate".
        Do NOT include "abort_response" if not explicitly stated.
        # Decline Detection
        Set "decline_response" to true for: "no answer", "I don't know", "I have none", "no comment", "can't say", "nothing", "n/a", "decline to answer".
        Do NOT include "decline_response" for partial answers, topic changes, or ambiguous non-responses.

        Return ONLY a JSON structure with a single detected key (abort_response, decline_response) set to true.
        If nothing is detected, return an empty JSON object. No delimiters!
        No commentary. Never guess - ambiguous cases = empty JSON.

    """;

    def touch(frame:Frame) -> bool {
        # Always allow entering the Initial state
        return True;
    }

    def run(frame:Frame) {
        frame_node = frame.frame_node;
        agent_node = frame.agent_node;

        # check if abort was set to true
        if self.abort{
            frame_node.data_set(key=f"{frame.action_label}_results", value={});
            self.abort = False;
            return "";
        }else{
            response = self.call_llm(self.prompt, history=True, json_only=True, frame_node=frame_node, agent_node=agent_node);
            if response.get("abort_response"){
                frame_node.data_set(key=f"{frame.action_label}_results", value={});
                return self.directive;
            }
            else{
                return True;
            }
        }
    }
}