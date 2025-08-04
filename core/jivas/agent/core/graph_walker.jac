import logging;
import traceback;
import from typing { Optional }
import from logging { Logger }
import from jivas.agent.core.app { App }
import from jivas.agent.core.graph_node { GraphNode }

import from jivas.agent.modules.data.serialization { export_to_dict }

import from jac_cloud.core.archetype { NodeAnchor }

walker graph_walker {
    # base walker designed to traverse along app graph;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    class __specs__ {
        # all graph_walkers are private by default, unless overridden
        static has private: bool = True;
    }

    def get_type() -> str {
        # returns the string-based representation of the class name
        return type(self).__name__;
    }

    def get_module() -> str {
        # returns the string-based representation of the class module
        return type(self).__module__;
    }

    can on_root with `root entry {
        # spawn app node if not there
        visit [-->](`?App) else {

            if hasattr(self.__specs__, 'auth') {
                if self.__specs__.auth == False {
                    # if walker has explicitly set itself to be unauthenticated, transparently load app root
                    app_root = self.get_app_root();
                    if not app_root {
                        self.logger.error('Unable to load app root');
                        disengage;
                    }
                    visit app_root;
                } else {
                    self.logger.warning('Import an Agent to continue...');
                }
            } else {
                self.logger.warning('Import an Agent to continue...');
            }

        }
    }

    def export(ignore_keys: list = ['__jac__']) {
        # convert the object to dictionary
        node_export = export_to_dict(self, ignore_keys);
        return node_export;
    }

    def update(data: dict = {}) -> graph_walker {
        # updates a graph node; expects a dict of attribute names mapped to values for updating
        if(data) {
            for attr in data.keys() {
                # check if attribute is a node attribute
                if (hasattr(self, attr)) {
                    self.attr = data[attr];
                }
            }
        }
        self.post_update();
        return self;
    }

    # can be overriden to execute following a walker update
    def post_update { }

    def :protect get_app_root() -> Optional[GraphNode] {
        # retrieves the app root Node from graph and elevates its owner to system root for access
        item = NodeAnchor.Collection.find_one({"name": "App"});

        if item and (root_id := item.root) {
            # now found, we need to elevate the root for access
            _root = &(f"n::{root_id}");
            jctx = _.get_context();
            jctx.system_root = _root.__jac__;
            jctx.root_state = jctx.system_root;
            return _root;
        }
        return None;
    }

}
