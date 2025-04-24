import:py os;
import:py io;
import:py yaml;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils, jvdata_file_interface }
import:jac from jivas.agent.core.agent {Agent}
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.core.agent_graph_walker {agent_graph_walker}
import:jac from jivas.agent.core.import_agent {import_agent}

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

        descriptor_data = {};

        try {
        	file_bytes = jvdata_file_interface.get_file(here.descriptor);
			file = io.BytesIO(file_bytes);
            descriptor_data = yaml.safe_load(file);

            if(not descriptor_data) {
                message = f"unable to load descriptor: {here.descriptor}";
                self.logger.error(message);
                Jac.get_context().status = 500;
                report message;
                return None;
            }
        } except Exception as e {
            message = f"an exception occurred, {traceback.format_exc()}";
            self.logger.error(message);
            Jac.get_context().status = 500;
            report message;
            return None;
        }

        dep_action_info = here.get_actions().get_action_info(
            namespace_package_name=self.package_name,
            version=self.version,
            jpr_api_key=self.jpr_api_key
        );

        if(dep_action_info) {

            try {
                action_info = {
                    "action": dep_action_info.get('name'),
                    "context": {
                        "version": dep_action_info.get('version'),
                        "enabled": True
                    }
                };

                action_exists = False;
                for action in descriptor_data['actions'] {
                    if(action['action'] == self.package_name) {
                        if(self.override_action) {
                            action['context'] = action_info['context'];
                        } else{
                            action['context'].update(action_info['context']);
                        }
                        action_exists = True;
                    }
                }

                if(not action_exists) {
                    # if the action does not exist, insert it
                    descriptor_data['actions'].append(action_info);
                }

                if ( here.update(data=descriptor_data, with_actions=True, jpr_api_key=self.jpr_api_key)) {
                    Jac.get_context().status = 200;
                    report f"{self.package_name} {self.version} installed successfully";
                } else {
                    Jac.get_context().status = 500;
                    report f"unable to install action {self.package_name} {self.version}";
                }

            } except Exception as e {
                message = f"an exception occurred, {traceback.format_exc()}";
                self.logger.error(message);
                Jac.get_context().status = 500;
                report message;
                return None;
            }

        } else {
            Jac.get_context().status = 403;
            report f"unable to locate action {self.package_name} {self.version}";
        }

    }

}
