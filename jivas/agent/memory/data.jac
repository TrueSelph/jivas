import:py from jivas.agent.modules.agentlib.utils { Utils }

obj Data {
    # an extracted data item related to an interaction
    has label: str = "";
    has meta: dict = {};
    has content: any = "";

    can load(data:dict) {
        # loads a compatible data struct
        if (data) {
            for attr in data.keys() {
                # set if attribute is a valid attribute
                if (hasattr(self, attr)) {
                    setattr(self, attr, data[attr]);
                }
            }
        }
    }

    can export(ignore_keys: list = ['__jac__']) {
        # convert the object to dictionary
        node_export = Utils.export_to_dict(self, ignore_keys);
        return node_export;
    }
}