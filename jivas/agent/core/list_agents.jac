import:jac from graph_walker { graph_walker }
import:jac from app { App }
import:jac from agents { Agents }

walker list_agents :graph_walker: {
    # lists all agents in the graph

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_app with App entry {
        # spawn agents node if not there
        visit [-->](`?Agents) else {
            self.logger.debug('agents node created');
            agents_node = here ++> Agents();
            visit agents_node;
        }
    }

    can on_agents with Agents entry {
        if(agents := here.get_all()) {
            for agent in agents {
                report agent.export();
            }
        }
    }

}