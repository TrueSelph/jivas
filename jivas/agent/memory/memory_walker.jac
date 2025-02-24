import:jac from jivas.agent.core.agent { Agent }
import:jac from memory { Memory }
import:jac from frame { Frame }
import:jac from jivas.agent.core { graph_walker }

walker memory_walker :graph_walker: {
    # base walker for agent memory graph traversal
    has session_id: str = "";

    can on_agent with Agent entry {
        visit [-->](`?Memory);
    }

    can on_memory with Memory entry {
        visit [-->](`?Frame)(?session_id == self.session_id);
    }
}