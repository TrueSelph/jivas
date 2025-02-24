import:py os;
import:py yaml;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.agent { Agent }
import:jac from action { Action }
import:jac from jivas.agent.action.actions { Actions }
import:jac from interact_graph_walker { interact_graph_walker }
import:jac from interact_action { InteractAction }

walker list_actions :interact_graph_walker: {
    # retrieves a list of all action package metadata
    # must be spawned on agent or actions node or supplied with agent_id
    has agent_id: str = "";
    has actions: list = [];
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
        visit [-->](`?Action);
    }

    can on_action with Action entry {
        # load the action data
        action_data = here.export();
        self.actions.append(action_data);

        # attempt to visit any child actions
        visit [-->](`?Action);
    }

    can on_exit with exit {
        # order actions by weight if available
        other_actions = [
            action for action in self.actions
            if (action.get('_package', {}).get('meta', {}).get('type', 'action') != 'interact_action'
            and action['label'] != 'ExitInteractAction')
        ];
        interact_actions = [
            action for action in self.actions
            if (action.get('_package', {}).get('meta', {}).get('type', 'action') == 'interact_action'
            or action['label'] == 'ExitInteractAction')
        ];
        self.actions = (sorted(interact_actions, key = with action:int can action['weight'] )) + other_actions;

        report self.actions;
    }
}