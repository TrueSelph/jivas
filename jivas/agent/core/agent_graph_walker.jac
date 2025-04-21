import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from app { App }
import:jac from agents { Agents }
import:jac from graph_walker { graph_walker }

walker agent_graph_walker :graph_walker: {
    # base walker designed to traverse graph specific to agent_id;

    has agent_id: str = "";

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can on_app with App entry {
        # spawn agents node if not there
        visit [-->](`?Agents) else {
            self.logger.error('App graph not initialized. Import an agent and try again.');
        }
    }

    can on_agents with Agents entry {

        if(self.agent_id) {

            try {

                if(agent_node := &self.agent_id) {

                    if agent_node.published {
                        visit agent_node;
                    }

                } else {
                    Jac.get_context().status = 400;
                    report "Invalid agent id";
                    disengage;
                }

            } except Exception as e {
                Jac.get_context().status = 400;
                report "Invalid agent id";
                disengage;
            }
        }
    }

}
