import:jac from jivas.agent.core.agent_graph_walker { agent_graph_walker }
import:jac from jivas.agent.core.app { App }
import:jac from jivas.agent.core.agents { Agents }

walker list_agents :agent_graph_walker: {
    # lists all agents in the graph

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
        static has excluded: list = [
            "agent_id" # inherited agent_id not relevant for list agents params
        ];
    }

    can on_agents with Agents entry {
        if(agents := here.get_all()) {
            for agent in agents {
                report agent.export();
            }
        }
    }

}