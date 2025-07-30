import os;
import yaml;
import logging;
import traceback;
import from logging { Logger }
import from jivas.agent.core.agent {Agent}
import from jivas.agent.action.action {Action}
import from jivas.agent.action.actions {Actions}
import from agent_graph_walker {agent_graph_walker}

walker get_action(agent_graph_walker) {
    # retrieves a named action package and metadata
    # must be spawned on agent or actions node or supplied with agent_id
    has action_id: str = "";
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
        if here.id == self.action_id {
            # if the action is found, we def export its data
            report here.export();
            disengage;
        }
    }

}