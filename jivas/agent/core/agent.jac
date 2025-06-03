import:py logging;
import:py traceback;
import:py os;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.core { graph_node, purge }
import:jac from graph_node { GraphNode }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.memory.memory { Memory }
import:py from typing { Union }
import:py from jvserve.lib.file_interface { file_interface }
import:py from jac_cloud.core.architype { NodeAnchor }

node Agent :GraphNode: {
    # represents an agent on the graph

    # set up logger
    static has logger: Logger = logging.getLogger(__name__);

    has published: bool = True;
    has name: str = "";
    has description: str = "";
    has descriptor: str = "";
    has jpr_api_key: str = "";
    has agent_logging: bool = True; # when set, agent will log interactions
    has message_limit: int = 1024;
    has flood_control: bool = True; # set to activate interact flood control
    has flood_block_time: int = 300; # in seconds
    has window_time: int = 20; # in seconds, the time window we are monitoring
    has flood_threshold: int = 4; # in messages per window time
    has frame_size: int = 10; # keeps up to 10 interactions in the frame
    has tts_action: str = "ElevenLabsTTSAction";
    has stt_action: str = "DeepgramSTTAction";
    has vector_store_action: str = "TypesenseVectorStoreAction";
    has healthcheck_status: int = 501;
    has meta: dict = {};

    can postinit {
        super.postinit();
        # node attributes which are protected from update operation
        self.protected_attrs += ["id", "actions", "descriptor", "healthcheck_status"];
    }

    can get_memory() -> Memory {
        # returns a reference to the agent's memory node

        memory_node = Utils.node_obj([-->](`?Memory));

        # Attach memory and actions node if not exists
        if (not memory_node) {
            self ++> (memory_node := Memory());
            self.logger.debug('memory node created');
        }

        return memory_node;
    }

    can get_actions() -> Actions {
        # returns a reference to the agent's actions node

        actions_node = Utils.node_obj([-->](`?Actions));

        # Attach actions node if not exists
        if (not actions_node) {
            self ++> (actions_node := Actions());
            self.logger.debug('actions node created');
        }

        return actions_node;
    }

    can get_action(action_label: str="", action_type:str="", only_enabled: bool=True) -> Union[Action, None, list] {
        # fetch action node if enabled and configured
        # by action type or label

        if(action_node := self.get_actions().get(
            action_label=action_label,
            action_type=action_type,
            only_enabled=only_enabled)) {
            return action_node;
        }

        return None;
    }

    can get_tts_action() -> Union[Action, None] {
        # fetch text to speech action node if enabled and configured

        if(tts_action_node := self.get_action(action_label=self.tts_action)) {
            return tts_action_node;
        }

        return None;
    }

    can get_stt_action() -> Union[Action, None] {
        # fetch speech to text action node if enabled and configured

        if(stt_action_node := self.get_action(action_label=self.stt_action)) {
            return stt_action_node;
        }

        return None;
    }

    can get_vector_store_action() -> Union[Action, None] {
        # fetch vector store action node if enabled and configured

        if(vector_store_action_node := self.get_action(action_label=self.vector_store_action)) {
            return vector_store_action_node;
        }

        return None;
    }

    can update(data: dict={}, with_actions: bool=False, jpr_api_key: str = "", with_healthcheck:bool=False) -> Agent {
        # performs a shallow update (no action updates),
        # or deep update (re-registers all actions),
        # with or without a healtcheck report
        # if called without params, it will simply dump the descriptor based on the current agent state

        # trigger the parent update routine
        agent_node = super.update(data=data);

        # now handle actions if present and with_actions flag is set...
        if (with_actions) {

            actions = data.get('actions');

            # ensure we validate actions before proceeding
            if not isinstance(actions, list) {
                return agent_node;
            }

            if (len(actions) == 0) {
                return agent_node;
            }

            # use supplied jpr_api_key if provided, fall back on agent's jpr key
            if(not jpr_api_key) {
                jpr_api_key = self.jpr_api_key;
            }

            self.get_actions().install_actions(
                agent_id=self.id,
                action_list=data['actions'],
                jpr_api_key=jpr_api_key
            );
        }

        if(with_healthcheck) {
            # perform healthcheck and log error / warning details
            healthcheck_report = self.healthcheck();
            if (healthcheck_report['status'] == 200) {
                self.logger.info(healthcheck_report['message']);
            } else {
                for (label, detail) in (healthcheck_report['trace']).items() {
                    if (detail.get("status") == False) {
                        self.logger.error(f"[{label}] {detail.get("message")}");
                    } elif (detail.get("status") == True and detail.get("severity") == "warning") {
                        self.logger.warning(f"[{label}] {detail.get("message")}");
                    }
                }
            }
        }

        # if the agent node is valid, we can update the descriptor
        if agent_node {
            self.dump_descriptor();
        }

        return agent_node;
    }

    can is_logging() -> bool {
        return self.agent_logging;
    }

    can set_logging(agent_logging: bool) {
        self.agent_logging = agent_logging;
    }

    can get_descriptor(as_yaml:bool=False, clean:bool=False) -> Union[str, dict] {
        # converts an agent to a descriptor and returns it as yaml, json or dict (default)
        # if 'clean' is set to True, descriptor data will be without snapshot state containing keys and configs (good for dafs)
        try  {
            agent_data = {};
            agent_actions = [];
            agent_ignore_keys = [];
            action_ignore_keys = ['_package'];

            if(clean) {
                agent_ignore_keys = self.protected_attrs + ['meta'];
                action_ignore_keys = [
                    'id', 'description', '_package', 'weight', 'api_key', 'secret_key', 'token',
                    "host", "port", "protocol", "api_key_name", "connection_timeout", "collection_name"
                ];
            }

            # get agent data
            agent_data = self.export(agent_ignore_keys, clean);
            # get action data
            agent_actions = (self spawn _export_actions(action_ignore_keys, clean)).action_nodes;
            # add agent actions to agent data
            agent_data = {**agent_data, **{"actions": agent_actions or []}};

            # return as YAML
            if (as_yaml) {
                return Utils.yaml_dumps(agent_data);
            }

            return agent_data;

        } except Exception as e {
            self.logger.error(
                f"an exception occurred, {traceback.format_exc()}"
            );
        }

        return {};
    }

    can get_daf_info() -> dict {
        # prepares daf info struct based on agent descriptor
        daf_info = {
            "package": {
                "name": self.meta.get('namespace', f'default/{Utils.to_snake_case(self.name)}'),
                "author": self.meta.get('author', ''),
                "version": self.meta.get('version', '0.0.1'),
                "meta": {
                    "title": self.name,
                    "description": self.description,
                    "type": "daf"
                }
            }
        };
        if(dependencies := self.meta.get('dependencies')) {
            daf_info["package"]["dependencies"] = dependencies;
        }

        return daf_info;
    }

    can dump_descriptor() {
        # exports agent and writes descriptor to .jvdata

        # get agent descriptor data
        agent_data = self.get_descriptor(clean=False);
        # Save agent state to file in .jvdata
        if (yaml_output := Utils.yaml_dumps(agent_data)) {
            self.save_file(self.descriptor, yaml_output.encode("utf-8"));
        } else {
            self.logger.error("Unable to dump agent descriptor to file");
        }
    }

    can healthcheck() -> Union[bool, dict] {
        # performs agent core healthcheck and return trace result
        trace = {};

        # Check each attribute for valid values and add to trace
        if not self.published {
            trace['published'] = {
                "status": False,
                "message": "Agent must be published to interact with it.",
                "severity": "error"
            };
        }

        if len(self.jpr_api_key.strip()) == 0 {
            trace['jpr_api_key'] = {
            "status": True,
            "message": "JPR API key not set. Your agent will not be able to access private JIVAS package repo items.",
            "severity": "warning"
            };
        }

        if isinstance(self.name, str) and len(self.name.strip()) == 0 {
            trace['name'] = {
            "status": False,
            "message": "Agent name must be a non-empty string with no leading or trailing spaces.",
            "severity": "error"
            };
        }

        if isinstance(self.description, str) and len(self.description.strip()) == 0 {
            trace['description'] = {
            "status": False,
            "message": "Agent description must be a non-empty string with no leading or trailing spaces.",
            "severity": "error"
            };
        }

        if len(self.descriptor.strip()) == 0 {
            trace['descriptor'] = {
            "status": False,
            "message": "Agent descriptor path not set.",
            "severity": "error"
            };
        }

        if not isinstance(self.message_limit, int) or self.message_limit <= 0 {
            trace['message_limit'] = {
            "status": False,
            "message": "Message limit must be a positive integer.",
            "severity": "error"
            };
        }

        if not isinstance(self.flood_block_time, int) or self.flood_block_time <= 0 {
            trace['flood_block_time'] = {
            "status": False,
            "message": "Flood block time must be a positive integer representing seconds.",
            "severity": "error"
            };
        }

        if not isinstance(self.window_time, int) or self.window_time <= 0 {
            trace['window_time'] = {
            "status": False,
            "message": "Window time must be a positive integer representing seconds.",
            "severity": "error"
            };
        }

        if not isinstance(self.flood_threshold, int) or self.flood_threshold <= 0 {
            trace['flood_threshold'] = {
            "status": False,
            "message": "Flood threshold must be a positive integer.",
            "severity": "error"
            };
        }

        if not isinstance(self.frame_size, int) or self.frame_size <= -1 {
            trace['frame_size'] = {
            "status": False,
            "message": "Frame size must be 0 or a positive integer.",
            "severity": "error"
            };
        }

        return trace;
    }

    can get_healthcheck_report() -> dict {
        # performs agent healthcheck and actions healthcheck; returns full status report

        result = {
            'status': 501,
            'message': 'Agent healthcheck was unable to execute.',
            'trace': {}
        };

        error_warning_trace = {};
        # perform healthcheck on agent core
        trace = self.healthcheck();
        # triggers the healthcheck ability of all actions on an agent
        trace.update( (self spawn _healthcheck_actions()).trace );

        # review trace to assess healthcheck status
        # iterate through the trace and check for any False values
        for (key, value) in trace.items() {
            if (isinstance(value, dict)) {
                if (value.get("status") == False) {
                    result['status'] = 503;
                    error_warning_trace[key] = {
                        "status": False,
                        "message": value.get("message", f"Agent healthcheck failed on {key}. Inspect configuration and try again."),
                        "severity": value.get("severity")
                    };
                } elif(value.get("status") == True and value.get("severity") == "warning") {
                    error_warning_trace[key] = {
                        "status": True,
                        "message": value.get("message", f"Agent healthcheck warning on {key}."),
                        "severity": value.get("severity")
                    };
                }
            } elif (value == False) {
                result['status'] = 503;
                error_warning_trace[key] = {
                    "status": False,
                    "message": f"Agent healthcheck failed on {key}. Inspect configuration and try again.",
                    "severity": "error"
                };
            }
        }

        if (result['status'] == 501) {
            # if we didn't find any issues, set status to 200
            result['status'] = 200;
            result['message'] = f"Agent healthcheck passed.";
            result['trace'] = error_warning_trace;
        } elif result['status'] == 503 {
            # if we found issues, report them
            result['message'] = f"Agent healthcheck failed.";
            result['trace'] = error_warning_trace;
        }

        # update the healthcheck status
        self.healthcheck_status = result['status'];

        return result;
    }

    can get_file(path: str) -> bytes | None {
        # Retrieves a file for this agent by path.
        return file_interface.get_file(f"{self.id}/{path}");
    }

    can save_file(path: str, content: bytes) -> bool {
        # Saves a file for this agent at the given path.
        return file_interface.save_file(f"{self.id}/{path}", content);
    }

    can delete_file(path: str) -> bool {
        # Deletes a file for this agent at the given path.
        return file_interface.delete_file(f"{self.id}/{path}");
    }

    can get_file_url(path: str) -> str | None {
        # Gets the direct URL for a file belonging to this agent.
        return file_interface.get_file_url(f"{self.id}/{path}");
    }

    can get_short_file_url(path: str, with_filename: bool = False) -> str | None {
        # Gets a short/proxied URL for a file, optionally including the filename.
        collection = NodeAnchor.Collection.get_collection("url_proxies");

        if (url := file_interface.get_file_url(f"{self.id}/{path}")) {
            if (url_proxy := collection.insert_one({ "agent_id": self.id, "path": f"{self.id}/{path}" })) {
                base_url = f"{os.environ.get('JIVAS_FILES_URL','http://localhost:9000')}/f";

                if (not with_filename) {
                    return f"{base_url}/{url_proxy.inserted_id}";
                }

                path_segments = path.split('/');
                filename = path_segments[-1];
                return f"{base_url}/{url_proxy.inserted_id}/{filename}";
            }
        }

        return None;
    }
}

walker _healthcheck_actions {
    # performs agent healthcheck; triggers the healthcheck ability of all actions on an agent

    has trace:dict = {};

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_agent with Agent entry {
        # head to actions
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        # head to enabled action
        visit [-->](`?Action)(?enabled==True);
    }

    can on_action with Action entry {
        # trigger healthcheck ability
        self.trace[here.label] = here.healthcheck();
    }

}

walker _export_actions {
    # retrieves a list of all actions and sub actions
    # must be spawned on agent or actions node
    has ignore_keys:list = ['_package'];
    has action_nodes: list = [];
    has node_index: dict = {};
    has clean: bool = False;

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action);
    }

    can on_action with Action entry {

        # skip over the exit action
        if(here.label != "ExitInteractAction") {

            # handle any children (only for InteractActions)
            children = [];

            if(isinstance(here, InteractAction)) {
                child_nodes = here.get_children();
                for child in child_nodes {
                    children.append(child.id);
                }
            }

            self.node_index.update({
                here.id: {
                    "action": here._package['name'],
                    "context": here.export(self.ignore_keys, self.clean),
                    "children": children
                }
            });

            # we're done here, don't revisit
            ignore here;
        }

        # attempt to visit any child actions
        visit [-->](`?Action);
    }

    can on_exit with exit {
        # now, let's map the graph

        if(self.node_index) {
            node_keys = list(self.node_index.keys());
            node_keys.reverse();

            for key in node_keys {
                # iterate thru list of nodes in reverse and resolve children
                resolved_nodes = [];
                for child_id in self.node_index[key]["children"] {
                    resolved_nodes.append(self.node_index[child_id]);
                    # now remove the resolved child id
                    self.node_index.pop(child_id);
                }
                if(resolved_nodes) {
                    self.node_index[key]["children"] = resolved_nodes;
                } else {
                    self.node_index[key].pop("children");
                }
            }

            # now add all remaining values to action_nodes
            self.action_nodes = list(self.node_index.values());
        }
    }
}
