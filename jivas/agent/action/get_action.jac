import:py os;
import:py yaml;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.agent {Agent}
import:jac from action {Action}
import:jac from jivas.agent.action.actions {Actions}
import:jac from interact_graph_walker {interact_graph_walker}

walker get_action :interact_graph_walker: {
    # retrieves a named action package and metadata
    # must be spawned on agent or actions node or supplied with agent_id
    has agent_id: str = "";
    has action_id: str = "";
    has action_data: dict = {};
    # set up logger
    static has logger: Logger = logging.getLogger(__name__);

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {

        for action_node in here.get_all() {
            if (self.action_id == action_node.id) {
                visit action_node;
            }
        }

    }

    can on_action with Action entry {
        # load the action data
        self.action_data = here.export();
        # report it
        report self.action_data;
    }

}