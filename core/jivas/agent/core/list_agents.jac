import from jivas.agent.core.graph_walker { graph_walker }
import from jivas.agent.core.app { App }
import from jivas.agent.core.agents { Agents }

walker list_agents(graph_walker) {
    # lists all agents in the graph

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_app with App entry {
        # spawn agents node if not there
        visit [-->](`?Agents) else {
            self.logger.warning('Import an Agent to continue...');
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