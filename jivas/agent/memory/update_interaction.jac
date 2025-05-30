import:py logging;
import:py from logging { Logger }
import:jac from jivas.agent.memory.interaction { Interaction }
import:jac from jivas.agent.core.graph_walker { graph_walker }
import:py from jac_cloud.core.architype { NodeAnchor }

walker update_interaction :graph_walker: {
    # Walker for updating interaction node data

    # set up logger
    static has logger: Logger = logging.getLogger(__name__);

    # params
    has interaction_data: dict = {};


    obj __specs__ {
        static has auth: bool = True;
        static has private: bool = False;
    }

    can on_interaction with Interaction entry {
        if (not self.interaction_data) {
    		self.logger.error("no interaction data");
            return;
        }
        here.update(data = self.interaction_data);
        here.close();
    }
}
