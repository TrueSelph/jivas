import:py io;
import:py yaml;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.core.agent_graph_walker {agent_graph_walker}


walker install_action :agent_graph_walker: {
    # installs a single action on an agent

    has reporting:bool = False;  # Flag to enable reporting
    has override_action:bool = True;  # when set, will install with action defaults instead of preserving descriptor settings
    has package_name: str = "";  # Action name
    has version: str = "";  # Action version
    has jpr_api_key: str = ""; # any jpr_api_key for package access

    static has logger:Logger = logging.getLogger(__name__);  # Logger instance

    obj __specs__ {
        static has private: bool = False;  # Private specification
    }

    can on_agent with Agent entry {
        # updates the agent descriptor with the action to be installed; returns the updated descriptor data

        action_exists = False;
        descriptor_data = here.get_descriptor();

        if not descriptor_data {
            message = f"unable to load descriptor data";
            self.logger.error(message);
            Jac.get_context().status = 500;
            report message;
            return False;
        }

        dep_action_info = here.get_actions().get_action_info(
            namespace_package_name=self.package_name,
            version=self.version,
            jpr_api_key=self.jpr_api_key
        );

        if not dep_action_info {
            message = f"unable to locate action {self.package_name} {self.version}";
            self.logger.error(message);
            Jac.get_context().status = 403;
            report message;
            return False;
        }

        try {

            action_info = {
                "action": dep_action_info.get('name'),
                "context": {
                    "version": dep_action_info.get('version'),
                    "enabled": True
                }
            };

            # evaluate whether the action already exists
            for action in descriptor_data['actions'] {

                if(action['action'] == self.package_name) {

                    if(self.override_action) {
                        # if it exists and override is set, deregiter it, replace its context
                        action['context'] = action_info['context'];
                        # deregistering it ensures the package folder is removed
                        here.get_actions().deregister_action(action_label=action.get('context', {}).get('label', ''));
                    } else{
                        # if it exists and override is not set, update its version
                        action['context']['version'] = action_info['context']['version'];
                    }
                    action_exists = True;
                    break;
                }

            }

            if(not action_exists) {
                # if the action does not exist, insert it
                descriptor_data['actions'].append(action_info);
            }

            # now that the descriptor data is updated, update the agent and actions, this will reinstall actions and update descriptor
            if ( here.update(data=descriptor_data, with_actions=True, jpr_api_key=self.jpr_api_key) ) {
                message = f"{self.package_name} {self.version} installed successfully";
                self.logger.info(message);
                Jac.get_context().status = 200;
                report message;
                return True;
            } else {
                message = f"unable to install action {self.package_name} {self.version}";
                self.logger.error(message);
                Jac.get_context().status = 500;
                report message;
                return False;
            }

        } except Exception as e {
            message = f"unable to complete operation, {traceback.format_exc()}";
            self.logger.error(message);
            Jac.get_context().status = 500;
            report message;
            return False;
        }

    }

}
