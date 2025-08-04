import from jivas.agent.core.agent { Agent }
import from jivas.agent.memory.memory { Memory }
import from jivas.agent.memory.frame { Frame }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }

walker memory_collection_walker(agent_graph_walker) {
    # base walker for agent memory collection graph traversal
    has collection_name: str = "";

    can on_agent with Agent entry {
        visit [-->](`?Memory);
    }

    can on_memory with Memory entry {
        visit [-->](`?Collection)(?collection_name == self.name);
    }
}