import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from graph_walker { graph_walker }
import:jac from export_agent { export_agent }
import:jac from jivas.agent.core.agent { Agent }

walker update_agent :graph_walker: {
    has agent_id: str = "";
    has agent_data: dict = {};
    has with_actions: bool = False; # set True if you'd like actions to be re-registered with this update
    has reporting: bool = True;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {

        if(agent_node := here.update(data = self.agent_data, with_actions = self.with_actions)) {
            if(agent_node) {
                if(self.reporting) {
                    report agent_node.export_descriptor();
                }
            } else {
                self.logger.error(f'unable to update agent');
                if(self.reporting) {
                    Jac.get_context().status = 500;
                    report f'unable to update agent';
                }
            }
        }

    }
}