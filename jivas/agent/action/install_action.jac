import:py os;
import:py io;
import:py yaml;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils, jvdata_file_interface }
import:jac from jivas.agent.core.agent {Agent}
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.core.graph_walker {graph_walker}
import:jac from jivas.agent.core.import_agent {import_agent}

walker install_action :graph_walker: {
    # installs a single action on an agent

    has reporting:bool = False;  # Flag to enable reporting
    has override_action:bool = True;  # when set, will install with action defaults instead of preserving descriptor settings
    has package_name: str = "";  # Action name
    has version: str = "";  # Action version

    static has logger:Logger = logging.getLogger(__name__);  # Logger instance

    obj __specs__ {
        static has private: bool = False;  # Private specification
    }

    can on_agent with Agent entry {
        # updates the agent descriptor with the action to be installed; returns the updated descriptor data

        descriptor_data = None;

        try {
        	file_bytes = jvdata_file_interface.get_file(here.descriptor);
			file = io.BytesIO(file_bytes);
            descriptor_data = yaml.safe_load(file);

            if(not descriptor_data) {
                self.logger.error(f"unable to load descriptor: {here.descriptor}");
                return None;
            }
        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
            return None;
        }

        # Handle the actions entry point
        jpr_api_key = descriptor_data.get('jpr_api_key');
        dep_action_info = here.get_actions().get_action_info(namespace_package_name=self.package_name, version=self.version, jpr_api_key=jpr_api_key);

        if(dep_action_info) {
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
                descriptor_data['actions'].append(action_info);
            }

            self.import_from_descriptor(descriptor_data);
        }

    }

    can import_from_descriptor(descriptor:dict) -> Agent {
        # Import agent from descriptor
        if (descriptor.get('id', None)) {
            try {
                agent_node = &descriptor["id"];
            } except Exception as e {
                self.logger.error(f"an exception occurred, {traceback.format_exc()}");
                return None;
            }
        }
        else {
            agent_name = descriptor.get('name');
            if(_node := agents_node.get_by_name(agent_name)) {
                agent_node = _node;
            } else {
                if( agent_node := Agent(
                    name=agent_name,
                    description=descriptor.get('description', '')
                )) {
                    if(not agents_node.get_by_id(agent_node.id)) {
                        agents_node ++> agent_node;
                    }
                    self.logger.info(f"agent created: {agent_node.name}");
                } else {
                    self.logger.error(f"unable to create agent: {agent_name}");
                }
            }
        }

        if(agent_node) {
            descriptor_root = Utils.get_descriptor_root();
            agent_node.descriptor = f"{descriptor_root}/{agent_node.id}.yaml";
            agent_node.get_memory();
            agent_node.get_actions();

            if(agent_node := agent_node.update(
                data=descriptor,
                with_actions=True
            )) {
                agent_node.export_descriptor();
                return agent_node;
            }
        }
        return None;
    }
}
