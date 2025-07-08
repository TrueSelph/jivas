import from jivas.agent.core.graph_node { GraphNode }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }

node Collection(GraphNode) {
    # represents a named collection for long-term memory storage
    has name:str = "";
    has data:dict = {};

    def get_name() -> str {
        return self.name;
    }

    def set_name(name:str) -> None {
        self.name = name;
    }

    def delete() -> list {
        return (self spawn _purge_collection()).removed;
    }
}


walker _purge_collection {
    # walker which carries out the traversal and purging of this collection and any related child nodes

    has removed:list = [];

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_collection with Collection entry {
        visit [-->] else {
            self.removed.append(here);
            Jac.destroy(here);
        }
    }

    can on_collection_node with GraphNode entry {
        visit [-->];
        self.removed.append(here);
        Jac.destroy(here);
    }
}
