import from typing { Optional, Any }

import from jivas.agent.modules.data.serialization { export_to_dict }


obj GraphObject {
    # base graph object to be used in JIVAS graph.
    has :protect id: str = "";
    has :priv data: dict = {};

    def postinit {
        if (not self.id) {
            self.id = jid(self);
        }
    }

    def load(data:dict) {
        # loads a compatible data struct
        if (data and isinstance(data, dict)) {
            for attr in data.keys() {
                # set if attribute is a valid attribute
                if (hasattr(self, attr)) {
                    setattr(self, attr, data[attr]);
                }
            }
        }
    }

    def data_get(key:str, default:Optional[Any] = None) -> Any {
        # retrieves a named variable by key
        if isinstance(self.data, dict) {
            return self.data.get(key, default);
        }
        return None;
    }

    def data_set(key:str, value:Any) {
        # sets a named variable by key
        if isinstance(self.data, dict) {
            self.data[key] = value;
        } else {
           self.data = {key: value};
        }
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
        # completely removes the variable and value from frame
        self.data.pop(key, None);
    }

    def data_clear() -> None {
        # clears all data items
        self.data = {};
    }

    def export(ignore_keys: list = ["__jac__"]) -> dict {
        # returns a dictionary representation of the object
        return export_to_dict(self, ignore_keys);
    }
}
