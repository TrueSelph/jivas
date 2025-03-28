import:py inspect;
import:py logging;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:py from typing { Optional, Type, Union }
import:py from dataclasses { fields, MISSING }

node GraphNode {
    # base graph node for all nodes in agent graph, under app node.
    has id: str = "";
    # flag to permit export of children nodes in agent graph export
    has graph_children: bool = False;
    # flag to permit export of itself in agent graph export
    has graph_self: bool = True;
    # list of node attributes which are protected from update operation
    has protected_attrs: list = ["id"];
    # list of node attributes which should be excluded from export
    has transient_attrs: list = ['__jac__', 'protected_attrs', 'transient_attrs', 'graph_children', 'graph_self', 'package_path'];
    # for storing extended attributes
    has _context: dict = {};
    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can postinit {
        if (not self.id) {
            self.id = jid(self);
        }
    }

    can get_type -> str {
        # returns the string-based representation of the class name
        return type(self).__name__;
    }

    can get_parent_type -> str {
        # returns the string-based representation of the class name
        return type(super()).__name__;
    }

    can export(ignore_keys: list = [], modified_context: bool = False) -> dict {

        if(modified_context) {
            ignore_keys = ignore_keys + self.transient_attrs;

            cls = type(self);
            default_values = {};
            for f in fields(self){
                if f.default is not MISSING{
                    default_values[f.name] = f.default;
                }
                elif f.default_factory is not MISSING{
                    default_values[f.name] = f.default_factory();
                }
            }

            node_export = Utils.export_to_dict(self, ignore_keys);
            return Utils.sanitize_dict_context(descriptor_data = node_export, action_data = default_values, keys_to_remove= ignore_keys);

        } else {
            # set the keys to ignore
            ignore_keys = ignore_keys + self.transient_attrs;
            # convert the object to dictionary
            node_export = Utils.export_to_dict(self, ignore_keys);
            # we have to merge contents of _context into top-level dict; _context contains injected attributes
            if (isinstance(node_export['_context'], dict)) {
                node_export.update(node_export['_context']);
                # now remove the original _context
                del node_export['_context'];
            }
            return node_export;
        }
    }

    can update(data: dict = {}) -> GraphNode {
        # updates a graph node; expects a dict of attribute names mapped to values for updating
        if (data) {
            for attr in data.keys() {
                if (attr not in self.protected_attrs) {

                    # check if attribute is a node attribute
                    if (hasattr(self, attr)) {
                        setattr(self, attr, data[attr]);
                    } else {
                        # Note: There is no global context in nodes like in jac v1, as such we store the data in the _context attribute
                        self._context[attr] = data[attr];
                    }
                }
            }
        }
        self.postupdate();

        return self;
    }

    can postupdate {
        # can be overriden to execute following a node update
    }
}
