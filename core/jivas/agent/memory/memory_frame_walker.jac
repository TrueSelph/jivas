import from jivas.agent.core.agent { Agent }
import from jivas.agent.memory.memory { Memory }
import from jivas.agent.memory.frame { Frame }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }

walker memory_frame_walker(agent_graph_walker) {
    # base walker for agent memory frame graph traversal
    has session_id: str = "";

    can on_agent with Agent entry {
        visit [-->](`?Memory);
    }

    can on_memory with Memory entry {
        visit [-->](`?Frame)(?session_id == self.session_id);
    }
}