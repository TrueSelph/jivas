import os;
import yaml;
import logging;
import traceback;
import from logging { Logger }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.action.action { Action }
import from jivas.agent.action.actions { Actions }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }
import from jivas.agent.action.interact_action { InteractAction }

walker list_actions(agent_graph_walker) {
    # retrieves a list of all action package metadata
    # must be spawned on agent or actions node or supplied with agent_id

    has actions: list = [];
    # set up logger
    static has logger: Logger = logging.getLogger(__name__);

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
        static has excluded: list = ['actions'];
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

        def get_weight(action:dict) -> int {
            return int(action.get('weight', 0));
        }

        self.actions = (
            sorted(interact_actions, key=get_weight)
        ) + other_actions;

        report self.actions;
    }

}