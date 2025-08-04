import logging;
import traceback;
import from typing { Union }
import from logging { Logger }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.memory.collection { Collection }

node Action(GraphNode) {
    # represents an execution on the agent action graph

    has agent_id:str = "";
    has version: str = "";
    has label: str = "";
    has description: str = "basic agent action";
    has enabled: bool = True;
    has _package: dict = {};
    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    def postinit {
        super.postinit();
        # list of node attributes which are protected from update operation
        self.protected_attrs += ['_package', 'label', 'version', 'agent_id'];
        # list of node attributes which should be excluded from export
        self.transient_attrs += ['agent_id'];
    }

    # override to execute operations upon registration of action
    def on_register() { }

    # override to execute operations upon the reload of action
    def on_reload() { }

    # override to execute any setup code when all actions are in place
    def post_register() { }

    # override to execute operations upon enabling of action
    def on_enable() { }

    # override to execute operations upon disabling of action
    def on_disable() { }

    # override to execute operations upon deregistration of action
    def on_deregister() { }

    # override to implement pulse operation
    def pulse() { }

    # override to furnish analytics data for the action
    def analytics() { }

    def healthcheck() -> Union[bool, dict] {
        # override to implement healthcheck operation
        # optionally returns a dict of (status:bool, severity:str [error|warning], message:str) if more information is needed
        return True;
    }

    def update(data: dict = {}) -> GraphNode {
        # updates an action node; expects a dict of attribute names mapped to values for updating
        # overridden to respond to enable / disable updates
        enabled_changed = False;
        non_enabled_changed = False;

        if (data) {
            for attr in data.keys() {
                if (attr not in self.protected_attrs) {
                    # check if attribute is a node attribute
                    if (hasattr(self, attr)) {
                        # handle changes in disabled/enabled status
                        if attr == 'enabled' {
                            current_val = getattr(self, 'enabled');
                            if current_val != data[attr] {
                                enabled_changed = True;
                                if data[attr] == True {
                                    self.on_enable();
                                } else {
                                    self.on_disable();
                                }
                                setattr(self, attr, data[attr]);
                            }
                        } else {
                            current_val = getattr(self, attr);
                            if current_val != data[attr] {
                                non_enabled_changed = True;
                            }
                            setattr(self, attr, data[attr]);
                        }
                    } else {
                        # Handle context attributes; only mark as changed if the value is new or different
                        if (attr in self._context) {
                            if self._context[attr] != data[attr] {
                                non_enabled_changed = True;
                                self._context[attr] = data[attr];
                            }
                        } else {
                            non_enabled_changed = True;
                            self._context[attr] = data[attr];
                        }
                    }
                }
            }
        }

        # Conditionally trigger post_update only when:
        # 1. Node is enabled AND
        # 2. There were non-enabled changes OR no enabled changes occurred
        if self.enabled and (non_enabled_changed or not enabled_changed) {
            self.post_update();
        }

        return self;
    }

    def get_agent() -> GraphNode {
        # returns the agent node to which this action is attached
        return &self.agent_id;
    }

    def get_namespace() -> str {
        return self._package.get('config', {}).get('namespace', None);
    }

    def get_module() -> str {
        return self._package.get('config', {}).get('module', None);
    }

    def get_module_root() -> str {
        return self._package.get('config', {}).get('module_root', None);
    }

    def get_package_path() -> str {
        return self._package.get('config', {}).get('path', None);
    }

    def get_version() -> str {
        return self.version;
    }

    def get_package_name() -> str {
        return self._package.get('config', {}).get('package_name', None);
    }

    def get_namespace_package_name() -> str {
        return self._package.get('name', None);
    }

    def get_collection() -> Collection {
        # returns a collection node reference to be used as the action's graph-based data store
        return self.get_agent().get_memory().get_collection(self.label);
    }

    def remove_collection() -> list {
        # removes a collection node and its contents used as the action's graph-based data store
        return self.get_agent().get_memory().purge_collection_memory(self.label);
    }

    def get_file(path: str) -> bytes | None {
        # retrieves a file associated with this action by path
        return self.get_agent().get_file(f"{self.get_type()}/{path}");
    }

    def save_file(path: str, content: bytes) -> bool {
        # saves a file associated with this action at the given path
        return self.get_agent().save_file(f"{self.get_type()}/{path}", content);
    }

    def delete_file(path: str) -> bool {
        # deletes a file associated with this action by path
        return self.get_agent().delete_file(f"{self.get_type()}/{path}");
    }

    def get_file_url(path: str) -> str | None {
        # retrieves a URL to access a file associated with this action
        return self.get_agent().get_file_url(f"{self.get_type()}/{path}");
    }

    def get_short_file_url(path: str, with_filename: bool = False) -> str | None {
        # retrieves a shortened URL to access a file, optionally including the filename
        return self.get_agent().get_short_file_url(f"{self.get_type()}/{path}", with_filename);
    }
}