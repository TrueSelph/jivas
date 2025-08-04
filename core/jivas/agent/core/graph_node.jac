import inspect;
import logging;
import from logging { Logger }

import from jivas.agent.modules.action.cleaning { clean_context }
import from jivas.agent.modules.data.serialization { export_to_dict }

import from typing { Optional, Type, Union, Any }
import from dataclasses { fields, MISSING }

node GraphNode {
    # base graph node for all nodes in agent graph, under app node.
    has :protect id: str = "";
    # list of node attributes which are protected from update operation
    has :protect protected_attrs: list = ["id"];
    # list of node attributes which should be excluded from export
    has :protect transient_attrs: list = ['__jac__', 'protected_attrs', 'transient_attrs', 'package_path'];
    # for storing data items
    has :priv data: dict = {};
    # for storing extended attributes
    has :priv _context: dict = {};
    # set up logger
    static has :priv logger:Logger = logging.getLogger(__name__);

    def postinit {
        if (not self.id) {
            self.id = jid(self);
        }
    }

    def data_get(key:str, default:Optional[Any] = None) -> Any {
        # retrieves a named variable by key
        return self.data.get(key, default);
    }

    def data_set(key:str, value:Any) {
        # sets a named variable by key
        self.data[key] = value;
    }

    def data_append(key: str, value: Any) -> None {
        current = self.data.get(key, None);
        if current is None {
            self.data[key] = [value];
        } elif isinstance(current, list) {
            current.append(value);
        } else {
            self.data[key] = [current, value];
        }
    }

    def data_keys() -> list[str] {
        # Return all current keys (snapshot copy).
        return list(self.data.keys());
    }

    def data_items() -> list {
        # Return all items (snapshot copy).
        return list(self.data.items());
    }

    def data_del(key:str) -> None {
        # completely removes the data item and value
        self.data.pop(key, None);
    }

    def data_clear() -> None {
        # clears all data items
        self.data = {};
    }

    def get_type() -> str {
        # returns the string-based representation of the class name
        return type(self).__name__;
    }

    def get_parent_type() -> str {
        # returns the string-based representation of the class name
        return type(super()).__name__;
    }

    def export(ignore_keys: list = [], clean: bool = False) -> dict {
        # exports graph node as dict; if clean is set, exports a snapshot of node which matches archetype initializations

        if(clean) {
            ignore_keys = ignore_keys + self.transient_attrs;

            archetype_context = {};
            for f in fields(self) {
                if f.default is not MISSING {
                    archetype_context[f.name] = f.default;
                }
                elif f.default_factory is not MISSING {
                    archetype_context[f.name] = f.default_factory();
                }
            }

            node_export = export_to_dict(self, ignore_keys);
            # we have to merge contents of _context into top-level dict; _context contains injected attributes
            if (isinstance(node_export['_context'], dict)) {
                node_export.update(node_export['_context']);
                # now remove the original _context
                del node_export['_context'];
            }

            return clean_context(node_context=node_export, archetype_context=archetype_context, ignore_keys=ignore_keys);

        } else {
            # set the keys to ignore
            ignore_keys = ignore_keys + self.transient_attrs;
            # convert the object to dictionary
            node_export = export_to_dict(self, ignore_keys);
            # we have to merge contents of _context into top-level dict; _context contains injected attributes
            if (isinstance(node_export['_context'], dict)) {
                node_export.update(node_export['_context']);
                # now remove the original _context
                del node_export['_context'];
            }
            return node_export;
        }
    }

    def update(data: dict = {}) -> GraphNode {
        # updates a graph node; expects a dict of attribute names mapped to values for updating
        if (data) {
            for attr in data.keys() {
                if (attr not in self.protected_attrs) {

                    # check if attribute is a node attribute
                    if (hasattr(self, attr)) {
                        setattr(self, attr, data[attr]);
                    } else {
                        self._context[attr] = data[attr];
                    }
                }
            }
        }
        self.post_update();

        return self;
    }

    def post_update {
        # can be overriden to execute following a node update
    }
}
