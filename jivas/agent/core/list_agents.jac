import:jac from graph_walker { graph_walker }
import:jac from agents { Agents }

walker list_agents :graph_walker: {
    # lists all agents in the graph

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agents with Agents entry {
        if(agents := here.get_all()) {
            for agent in agents {
                report agent.export();
            }
        }
    }

}