import:jac from graph_walker { graph_walker }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.actions { Actions }

walker export_agent :graph_walker: {
    # accepts agent_id and returns dict of exported agent descriptor

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        if(self.reporting) {
            report here.export_descriptor();
        }
    }
}