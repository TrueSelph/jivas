import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.graph_node { GraphNode }
import:jac from interact_graph_walker { interact_graph_walker }

node Action :GraphNode: {
    # represents an execution on the agent action graph

    has version: str = "";
    has label: str = "";
    has description: str = "basic agent action";
    has enabled: bool = True;
    has _package: dict = {};
    has agent_id:str = "";
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

    can healthcheck() -> bool {
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
        self.get_agent().export_descriptor();
        # trigger postupdate
        self.postupdate();

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
}