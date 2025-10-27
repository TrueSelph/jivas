import logging;
import traceback;
import from typing { Union }
import from logging { Logger }
import from jivas.agent.action.subgraph_action.state { State }
import from jivas.agent.memory.frame { Frame }


node ConfirmedState(State) {
    # Represents an execution on a subgraph on the agent action graph

    has collection_id: str = "";
    has enabled: bool = True;
    has state_info:dict = {};
    has directive: str = "Tell the user you have completed the process";

    # override to execute operations upon enabling of action
    def on_enable() { }

    # override to execute operations upon disabling of action
    def on_disable() { }

    def touch(frame:Frame) -> bool {
        # Always allow entering the COMPLETED state
        return True;
    }

    def run(frame:Frame) {
        frame_node = frame.frame_node;
        agent_node = frame.agent_node;

        # set any custom directive from daf
        if ( directive := self.state_info.get("directive", "") ){
            self.directive = directive;
        }
        return self.directive;
    }
}