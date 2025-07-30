import logging;
import traceback;
import from logging { Logger }
import from jivas.agent.core.app { App }
import from jivas.agent.core.agents { Agents }
import from jivas.agent.core.graph_walker { graph_walker }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }

walker agent_graph_walker(graph_walker) {
    # base walker designed to traverse graph specific to agent_id;

    has agent_id: str;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    class __specs__ {
        static has private: bool = True;
        static has path: str = "{agent_id}";
    }

    can on_app with App entry {
        # spawn agents node if not there
        visit [-->](`?Agents) else {
            self.logger.warning('Import an Agent to continue...');
        }
    }

    can on_agents with Agents entry {

        agent_node = None;

        if not self.agent_id {
            Jac.get_context().status = 400;
            report "Missing Agent ID";
            disengage;
        }

        try {
            agent_node = &self.agent_id;
        } except Exception as e {
            Jac.get_context().status = 400;
            report "Invalid agent id";
            disengage;
        }

        if not agent_node.published {
            Jac.get_context().status = 404;
            report "Agent is not published";
            disengage;
        }

        visit agent_node;
    }

}
