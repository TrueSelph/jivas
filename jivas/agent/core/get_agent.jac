import:jac from agent_graph_walker { agent_graph_walker }
import:jac from jivas.agent.core.agent { Agent }

walker get_agent :agent_graph_walker: {

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        report here.export();
    }

}