import:py io;
import:py os;
import:py json;
import:py yaml;
import:py requests;
import:py tarfile;
import:py logging;
import:py traceback;
import:py from typing { Union }
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:py from jvcli.api { RegistryAPI }
import:py from jvcli.utils { is_version_compatible }
import:jac from app { App }
import:jac from jivas.agent.core.agent { Agent }
import:jac from agents { Agents }
import:jac from jivas.agent.memory.memory { Memory }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.actions { Actions }

walker import_agent {
    # creates or refreshes an agent via json data or yaml source

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has descriptor: str = "";
    has daf_name: str = "";
    has daf_version: str = "";
    has jpr_api_key: str = "";
    has reporting: bool = True;

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    # sets up app graph on first time traversal prior to agent import

    can on_root with `root entry {
        # spawn app node if not there
        visit [-->](`?App) else {
            self.logger.info('App node created');
            app_node = here ++> App();
            visit app_node;
        }
    }

    can on_app with App entry {
        # spawn agents node if not there
        visit [-->](`?Agents) else {
            self.logger.info('Agents node created');
            agents_node = here ++> Agents();
            visit agents_node;
        }
    }

    can on_agents with Agents entry {

        # routine to import a JIVAS agent by descriptor
        if(self.descriptor) {
            if(agent_node := self.import_from_descriptor(here, self.descriptor)) {
                if(self.reporting) {
                    report agent_node.export();
                }
            }
        } elif (self.daf_name) {
            if(agent_node := self.import_from_daf(here, self.daf_name, self.daf_version, self.jpr_api_key)) {
                if(self.reporting) {
                    report agent_node.export();
                }
            }
        }
    }

    can import_from_descriptor(agents_node:Agents, descriptor:Union[str, dict]) -> Agent {
        # imports an agent from an agent descriptor supplied as YAML, JSON or dict

        agent_data = {};
        agent_node = None;

        if(not descriptor) {
            return None;
        }

        # TODO: build an agent data validator and execute at this point

        # Try to parse the content as JSON
        if(isinstance(descriptor, str)) {
            try {
                agent_data = json.loads(descriptor);
            } except json.JSONDecodeError {}

            # Try to parse the content as YAML
            try {
                agent_data = yaml.safe_load(descriptor);
            } except yaml.YAMLError {}

        } else {
            agent_data = descriptor;
        }

        if(not agent_data) {
            self.logger.error('no agent data available for import');
            return None;
        }

        # Update agent node if exists or create new
        if (agent_data.get('id', None)) {

            try {
                agent_node = &agent_data["id"];
            } except Exception as e {
                self.logger.error(f"an exception occurred, {traceback.format_exc()}");
                return None;
            }

        } else {
            agent_name = agent_data.get('name');
            # if agent has same name as existing agent, update
            if(_node := agents_node.get_by_name(agent_name)) {
                agent_node = _node;
            } else {
                # otherwise we create a new agent
                if( agent_node := Agent(
                    name=agent_name,
                    description=agent_data.get('description', '')
                )) {
                    # attach the agent node if new and unattached
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
            # retrieves existing descriptor root folder or creates it
            descriptor_root = Utils.get_descriptor_root();
            # map to agent descriptor
            agent_node.descriptor = f"{descriptor_root}/{agent_node.id}.yaml";

            # Attach memory and actions node if not exists
            agent_node.get_memory();
            agent_node.get_actions();

            # import requires that agent re-install all actions
            if(agent_node := agent_node.update(
                data=agent_data,
                with_actions=True
            )) {
                return agent_node;
            }

        }

        return None;
    }

    can import_from_daf(agents_node:Agents, daf_name:str, version:Optional[str]="", jpr_api_key:Optional[str]="") -> Agent {
        # imports the agent as a digital agent freight package
        agent_node = None;
        safe_to_import = False;
        daf_info = {};
        # daf packages root folder
        package_root = Utils.get_daf_root();
        # extract the namespace, package name
        (namespace, package_name) = daf_name.split('/');

        # attempt to find the package locally, first...
        if (package_path := Utils.find_package_folder(package_root, daf_name) ) {

            info_yaml_path = os.path.join(package_path, 'info.yaml');

            if(os.path.exists(info_yaml_path)) {
                with open(info_yaml_path, 'r') as file {
                    try  {
                        # load the package info content
                        daf_info = yaml.safe_load(file);
                        # grab info package version
                        package_version = daf_info.get('package', {}).get('version', None);
                        # validate the version, if present
                        if(version) {
                            if(is_version_compatible(version, package_version)) {
                                safe_to_import = True;
                            }
                        } else {
                            safe_to_import = True;
                        }
                    } except yaml.YAMLError as e {
                        self.logger.error(
                            f"an exception occurred, {traceback.format_exc()}"
                        );
                    }
                }
            }
        }

        if (not safe_to_import) {
            # this means we'll need to try the package registry

            # download package from package registry
            if(package_data := RegistryAPI.download_package(daf_name, version, api_key=jpr_api_key)) {

                try {
                    package_file = requests.get(package_data["file"]);
                    # Save and extract the package
                    target_dir = os.path.join(package_root, daf_name);
                    os.makedirs(target_dir, exist_ok=True);

                    # Assuming the package_data is a ZIP file
                    with tarfile.open(
                        fileobj=io.BytesIO(package_file.content),
                        mode="r:gz"
                    ) as tar_file {
                        tar_file.extractall(target_dir);
                    }

                    safe_to_import = True;

                } except Exception as e {
                    self.logger.error(
                        f"an exception occurred, {traceback.format_exc()}"
                    );
                }
            }
        }

        if(safe_to_import and (package_path := Utils.find_package_folder(package_root, daf_name) )) {

            info_yaml_path = os.path.join(package_path, 'info.yaml');
            descriptor_yaml_path = os.path.join(package_path, 'descriptor.yaml');
            memory_yaml_path = os.path.join(package_path, 'memory.yaml');
            knowledge_yaml_path = os.path.join(package_path, 'knowledge.yaml');

            if(os.path.exists(info_yaml_path)) {
                with open(info_yaml_path, 'r') as file {
                    try  {
                        daf_info = yaml.safe_load(file);
                    } except Exception as e {
                        self.logger.error(
                            f"an exception occurred, {traceback.format_exc()}"
                        );
                        return None;
                    }
                }
            }

            # if agent has a descriptor.yaml file, we need to import it
            if(os.path.exists(descriptor_yaml_path)) {
                with open(descriptor_yaml_path, 'r') as file {
                    try  {
                        descriptor_data = yaml.safe_load(file);

                        # add jpr_api_key if provided
                        if(jpr_api_key) {
                            descriptor_data["jpr_api_key"] = jpr_api_key;
                        }
                        # add the daf info as metadata
                        descriptor_data["meta"] = {
                            "namespace": daf_info.get('package', {}).get('name'),
                            "version": daf_info.get('package', {}).get('version'),
                            "author": daf_info.get('package', {}).get('author'),
                            "dependencies": daf_info.get('package', {}).get('dependencies')
                        };

                        agent_node = self.import_from_descriptor(agents_node, descriptor_data);

                    } except Exception as e {
                        self.logger.error(
                            f"an exception occurred, {traceback.format_exc()}"
                        );
                        return None;
                    }
                }
            }

            # if agent does not pass healthcheck, halt here
            if(agent_node) {
                if(agent_node.healthcheck_status != 200) {
                    self.logger.error(
                        f"{agent_node.name} failed healthcheck. Any memory or knowledge queued for import will be deferred."
                    );
                    return agent_node;
                }
            }

            # if agent has a memory.yaml file, we need to import it
            if(agent_node and os.path.exists(memory_yaml_path)) {
                with open(memory_yaml_path, 'r') as file {
                    try  {
                        # load the package info content
                        _info = yaml.safe_load(file);
                        # call import memory
                        agent_node.get_memory().import_memory(data=_info);
                    } except Exception as e {
                        self.logger.error(
                            f"an exception occurred, {traceback.format_exc()}"
                        );
                    }
                }
            }
            # if agent has a knowledge.yaml file, we need to import it
            if(agent_node and os.path.exists(knowledge_yaml_path)) {

                with open(knowledge_yaml_path, 'r') as file {
                    try {

                        knode_yaml = file.read();
                        knode_yaml_data = yaml.safe_load(knode_yaml);

                        # if theres a configured vector store action for this agent, let's grab and import knodes
                        if(vector_store_action := agent_node.get_vector_store_action()) {
                            if('vec' in knode_yaml_data[0]) {
                                # if we have embeddings with the import
                                vector_store_action.add_embeddings(knode_yaml);
                            } else {
                                #load the knodes, as per norm
                                vector_store_action.import_knodes(knode_yaml);
                            }
                        }
                    } except Exception as e {
                        self.logger.error(
                            f"an exception occurred while importing agent knowledge, {traceback.format_exc()}"
                        );
                    }
                }
            }
        }

        return agent_node;
    }

}