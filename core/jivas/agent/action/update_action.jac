import os;
import yaml;
import logging;
import traceback;
import from logging { Logger }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.action.action { Action }
import from jivas.agent.action.actions { Actions }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }

walker update_action(agent_graph_walker) {
    # updates an action based on action_data
    # must be spawned on agent or actions node or supplied with agent_id, action_id

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
        visit [-->](`?Action)(?id==self.action_id);
    }

    can on_action with Action entry {

        if(action_node:=here.update(data = self.action_data)) {
            report action_node.export();
        }
    }
}