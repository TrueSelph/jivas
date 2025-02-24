import:jac from graph_walker { graph_walker }
import:jac from agents { Agents }

walker delete_agent :graph_walker: {
    has agent_id: str = "";

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agents with Agents entry {
        # Delete agent node
        agent_node = here.delete(self.agent_id);

        if (self.reporting) {
            report agent_node;
        }
    }
}