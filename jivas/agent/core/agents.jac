import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from graph_node { GraphNode }
import:jac from purge { purge }

node Agents :GraphNode: {
    # branch node for all agent nodes

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can get_all() -> list {
        # returns a list of all agent nodes
        return [-->];
    }

    can get_by_name(name:str) {
        # returns an agent node by name or None
        return Utils.node_obj([-->](?name == name));
    }

    can get_by_id(id:str) {
        # returns an agent node by name or None
        return Utils.node_obj([-->](?id == id));
    }

    can delete(id:str) {
        # removes an agent node by id
        if(agent_node := self.get_by_id(id)) {
            agent_node.get_actions().deregister_actions();
            # Delete agent node
            # self del--> agent_node;
            agent_node spawn purge();
            return agent_node;
        }

        return None;
    }

    can delete_all() {
        # removes all agents from the graph
        agent_nodes = [];

        for agent_node in self.get_all() {
            agent_nodes.append(self.delete(agent_node.id));
        }

        return agent_nodes;
    }

}