import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.core { graph_node, purge }
import:jac from graph_node { GraphNode }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.memory.memory { Memory }

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
    has flood_block_time: int = 300; # in seconds
    has window_time: int = 20; # in seconds, the time window we are monitoring
    has flood_threshold: int = 4; # in messages per window time
    has frame_size: int = 10; # keeps up to 10 interactions in the frame
    has tts_action: str = "ElevenlabsTTSAction";
    has stt_action: str = "DeepgramSTTAction";
    has vector_store_action: str = "TypesenseVectorStoreAction";
    has healthcheck_status: int = 501;
    has meta: dict = {};

    can postinit {
        super.postinit();
        # node attributes which are protected from update operation
        self.protected_attrs += ["id", "actions", "descriptor", "healthcheck_status", "meta"];
    }

    can get_memory() {
        # returns a reference to the agent's memory node

        memory_node = Utils.node_obj([-->](`?Memory));

        # Attach memory and actions node if not exists
        if (not memory_node) {
            self ++> (memory_node := Memory());
            self.logger.debug('memory node created');
        }

        return memory_node;
    }

    can get_actions() {
        # returns a reference to the agent's actions node

        actions_node = Utils.node_obj([-->](`?Actions));

        # Attach actions node if not exists
        if (not actions_node) {
            self ++> (actions_node := Actions());
            self.logger.debug('actions node created');
        }

        return actions_node;
    }

    can get_tts_action() {
        # fetch text to speech action node if enabled and configured

        if(tts_action_node := self.get_actions().get(action_label=self.tts_action)) {
            if(tts_action_node.enabled) {
                return tts_action_node;
            }
        }

        return None;
    }

    can get_stt_action() {
        # fetch speech to text action node if enabled and configured

        if(stt_action_node := self.get_actions().get(action_label=self.stt_action)) {
            if(stt_action_node.enabled) {
                return stt_action_node;
            }
        }

        return None;
    }

    can get_vector_store_action() {
        # fetch vector store action node if enabled and configured

        if(vector_store_action_node := self.get_actions().get(action_label=self.vector_store_action)) {
            if(vector_store_action_node.enabled) {
                return vector_store_action_node;
            }
        }

        return None;
    }

    can update(data: dict={}, with_actions: bool=False) -> Agent {
        # performs a shallow update (no action updates), or deep update (re-registers all actions)

        # trigger the parent update routine
        agent_node = super.update(data=data);

        # now handle actions if present and with_actions flag is set...
        if (with_actions
            and (len(data.get('actions', [])) > 0)) {
            self.get_actions().install_actions(
                self.id,
                data['actions'],
                self.jpr_api_key
            );
        }

        # perform healthcheck and log error / warning details
        healthcheck_report = self.get_healthcheck_report();
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

        return agent_node;
    }

    can is_logging() {
        return self.agent_logging;
    }

    can set_logging(agent_logging: bool) {
        self.agent_logging = agent_logging;
    }

    can export_descriptor(file_path: str="", modified_context:bool=False) -> dict {
        # converts an agent to a descriptor and exports it...
        # if file_path is provided, it will output to specified file path
        # otherwise, it will output to agent's descriptor path
        # returns descriptor dict.
        try  {
            self.logger.debug(f"exporting agent: {self.name}");

            agent_data = self.export([], modified_context);
            agent_actions = [];
            # Gather agent actions
            agent_actions = (self spawn _export_actions(modified_context=modified_context)).action_nodes;

            # Add agent actions to agent data

            agent_data = {**agent_data, **{"actions": agent_actions}};

            # Save agent state to file
            if (file_path) {
                Utils.dump_yaml_file(
                    file_path=file_path,
                    data=agent_data
                );
            } else {
                Utils.dump_yaml_file(
                    file_path=self.descriptor,
                    data=agent_data
                );
            }

            return agent_data;

        } except Exception as e {
            self.logger.error(
                f"an exception occurred, {traceback.format_exc()}"
            );
        }

        return {};
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
    has transient_export_attrs:list = ['_package'];
    has action_nodes: list = [];
    has node_index: dict = {};
    has modified_context: bool = False;

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
                    "context": here.export(self.transient_export_attrs, self.modified_context),
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