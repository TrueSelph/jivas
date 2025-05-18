import:py io;
import:py yaml;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.agent {Agent}
import:jac from jivas.agent.core.agent_graph_walker {agent_graph_walker}


walker uninstall_action :agent_graph_walker: {
    # uninstalls a single action on an agent

    has package_name: str = "";  # Action name, e.g. jivas/intro_interact_action

    static has logger:Logger = logging.getLogger(__name__);  # Logger instance

    obj __specs__ {
        static has private: bool = False;  # Private specification
    }

    can on_agent with Agent entry {
        # updates the agent descriptor with the action to be installed; returns the updated descriptor data

        descriptor_data = here.get_descriptor();

        if not descriptor_data {
            message = f"unable to load descriptor data";
            self.logger.error(message);
            Jac.get_context().status = 500;
            report message;
            return False;
        }

        try {

            action_removed = False;
            actions_node = here.get_actions();
            updated_actions = [];
            # find the action to uninstall
            for action in descriptor_data['actions'] {

                if(action.get('action') == self.package_name) {
                    # remove the entry once found
                    action_label = action.get('context', {}).get('label');
                    actions_node.deregister_action(action_label=action_label);
                    action_removed = True;
                } else {
                    updated_actions.append(action);
                }

            }

            if(action_removed) {
                # if the action was removed, update actions
                descriptor_data['actions'] = updated_actions;
            } else {
                message = f"unable to find action for uninstall: {self.package_name} {self.version}";
                self.logger.error(message);
                Jac.get_context().status = 500;
                report message;
                return False;
            }

            # now that the descriptor data is updated, update the agent and actions, this will reinstall actions and update descriptor
            if ( here.update(data=descriptor_data, with_actions=True) ) {
                message = f"{self.package_name} {self.version} uninstalled successfully";
                self.logger.info(message);
                Jac.get_context().status = 200;
                report message;
                return True;
            } else {
                message = f"unable to update agent after uninstall of {self.package_name} {self.version}";
                self.logger.error(message);
                Jac.get_context().status = 500;
                report message;
                return False;
            }

        } except Exception as e {
            message = f"unable to complete operation, {traceback.format_exc()}";
            self.logger.error(traceback.format_exc());
            Jac.get_context().status = 500;
            report message;
            return False;
        }

    }

}
