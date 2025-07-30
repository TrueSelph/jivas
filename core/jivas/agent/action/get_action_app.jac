import os;
import yaml;
import logging;
import traceback;
import from logging { Logger }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.action.action { Action }
import from jivas.agent.action.actions { Actions }
import from agent_graph_walker { agent_graph_walker }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }

walker get_action_app(agent_graph_walker) {
    # retrieves the action app source for the named action

    has action: str = "";
    has action_app: str = "";

    # set up logger
    static has logger: Logger = logging.getLogger(__name__);

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
        static has excluded: list = ['action_app'];
    }

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?label==self.action) else {
            message = f"Action not found: {self.action}";
            self.logger.error(message);
            Jac.get_context().status = 404;
            report message;
        }
    }

    can on_action with Action entry {
        # load the action data
        action_path = f"{here._package.get('config', {}).get('path', '')}/app/app.py";

        # read file contents of action_path and return text source
        try {
            if os.path.exists(action_path) {
                with open(action_path, 'r') as file {
                    self.action_app = file.read();
                }
            } else {
                message = f"Action app file not found: {action_path}";
                self.logger.warning(message);
                Jac.get_context().status = 404;
                report message;
                return;
            }
        } except Exception as e {
            message = f"Error reading action app file: {str(e)}";
            self.logger.error(message);
            self.logger.error(traceback.format_exc());
            Jac.get_context().status = 500;
            report message;
            return;
        }

        report self.action_app;
    }
}