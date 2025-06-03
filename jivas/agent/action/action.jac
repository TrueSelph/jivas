import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.graph_node { GraphNode }
import:jac from jivas.agent.memory.collection { Collection }

node Action :GraphNode: {
    # represents an execution on the agent action graph

    has agent_id:str = "";
    has version: str = "";
    has label: str = "";
    has description: str = "basic agent action";
    has enabled: bool = True;
    has _package: dict = {};
    # set up logger
    static has logger:Logger = logging.getLogger(__name__);
    # [Bug] Do not do `can init` this without setting the has vars
    # can init {
    #     # override to initialize the action
    # }
    can postinit {
        super.postinit();
        # add of node attributes which are protected from update operation
        self.protected_attrs += ['_package', 'label', 'version', 'agent_id'];
        # add of node attributes which should be excluded from export
        self.transient_attrs += ['agent_id'];
    }

    can on_register {
        # override to execute operations upon registration of action
    }

    can post_register {
        # override to execute any setup code when all actions are in place
    }

    can on_enable {
        # override to execute operations upon enabling of action
    }

    can on_disable {
        # override to execute operations upon disabling of action
    }

    can on_deregister {
        # override to execute operations upon deregistration of action
    }

    can pulse() {
        # override to implement pulse operation
    }

    can analytics() {
        # override to furnish analytics data for the action
    }

    can healthcheck() -> Union[bool, dict] {
        # override to implement healthcheck operation
        # optionally returns a dict of (status:bool, severity:str [error|warning], message:str) if more information is needed
        return True;
    }

    can update(data: dict = {}) -> GraphNode {
        # updates an action node; expects a dict of attribute names mapped to values for updating
        # overridden to respond to enable / disable updates
        if (data) {

            for attr in data.keys() {

                if (attr not in self.protected_attrs) {
                    # check if attribute is a node attribute
                    if (hasattr(self, attr)) {

                        # handle changes in disabled/enabled status
                        if attr == 'enabled' and ((getattr(self, attr)) != data[attr]) {
                            if data[attr] == True {
                                self.on_enable();
                            } else {
                                self.on_disable();
                            }
                        }
                        setattr(self, attr, data[attr]);
                    } else {
                        # Note: There is no global context in nodes like in jac v1, as such we store the data in the _context attribute
                        self._context[attr] = data[attr];
                    }
                }
            }
        }
        # update the agent descriptor with changes
        self.get_agent().dump_descriptor();
        # trigger post_update
        self.post_update();

        return self;
    }

    can get_agent() {
        # returns the agent node to which this action is attached
        return &self.agent_id;
    }

    can get_namespace() {
        return self._package.get('config', {}).get('namespace', None);
    }

    can get_module() {
        return self._package.get('config', {}).get('module', None);
    }

    can get_module_root() {
        return self._package.get('config', {}).get('module_root', None);
    }

    can get_package_path() {
        return self._package.get('config', {}).get('path', None);
    }

    can get_version() {
        return self.version;
    }

    can get_package_name() {
        return self._package.get('config', {}).get('package_name', None);
    }

    can get_namespace_package_name() {
        return self._package.get('name', None);
    }

    can get_collection() -> Collection {
        # returns a collection node reference to be used as the action's graph-based data store
        return self.get_agent().get_memory().get_collection(self.label);
    }

    can remove_collection() -> list {
        # removes a collection node and its contents used as the action's graph-based data store
        return self.get_agent().get_memory().purge_collection_memory(self.label);
    }

    can get_file(path: str) -> bytes | None {
        # retrieves a file associated with this action by path
        return self.get_agent().get_file(f"{self.get_type()}/{path}");
    }

    can save_file(path: str, content: bytes) -> bool {
        # saves a file associated with this action at the given path
        return self.get_agent().save_file(f"{self.get_type()}/{path}", content);
    }

    can delete_file(path: str) -> bool {
        # deletes a file associated with this action by path
        return self.get_agent().delete_file(f"{self.get_type()}/{path}");
    }

    can get_file_url(path: str) -> str | None {
        # retrieves a URL to access a file associated with this action
        return self.get_agent().get_file_url(f"{self.get_type()}/{path}");
    }

    can get_short_file_url(path: str, with_filename: bool = False) -> str | None {
        # retrieves a shortened URL to access a file, optionally including the filename
        return self.get_agent().get_short_file_url(f"{self.get_type()}/{path}", with_filename);
    }
}