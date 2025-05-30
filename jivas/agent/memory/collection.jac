import:jac from jivas.agent.core.graph_node { GraphNode }

node Collection :GraphNode: {
    # represents a named collection for long-term memory storage
    has name:str = "";
    has data:dict = {};

    can get_name() -> str {
        return self.name;
    }

    can set_name(name:str) -> None {
        self.name = name;
    }

    can get_data_item(label:str) -> any {
        return self.data.get(label, None);
    }

    can set_data_item(label:str, value:any) {
        self.data[label] = value;
    }

}