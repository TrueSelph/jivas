import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.action.interact_action { InteractAction }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }

node ExitInteractAction(InteractAction) {
# core exit action is always present on all action graphs at the very end of the graph
# it serves to directly reference with take to force the interact walker to exit and return
    has label: str = "ExitInteractAction";
    has description: str = "core exit action node for walker cleanup and return";
    has weight:int = 10000; # should always be last

    def touch(visitor: agent_graph_walker) -> bool {
        return True; # authorize the interact to run for tracking in trail
    }

    def execute(visitor: agent_graph_walker) -> None {
        # null implementation for execution
        return {};
    }
}