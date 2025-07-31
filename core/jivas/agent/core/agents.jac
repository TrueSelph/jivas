import logging;
import traceback;
import from logging { Logger }

import from jivas.agent.modules.system.common { node_obj }

import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.core.purge { purge }

node Agents(GraphNode) {
    # branch node for all agent nodes

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    def get_all() -> list {
        # returns a list of all agent nodes
        return [-->];
    }

    def get_by_name(name:str) {
        # returns an agent node by name or None
        return node_obj([-->](?name == name));
    }

    def get_by_id(id:str) {
        # returns an agent node by name or None
        return node_obj([-->](?id == id));
    }

    def delete(id:str) {
        # removes an agent node by id
        if(agent_node := self.get_by_id(id)) {
            agent_node.get_actions().deregister_actions();
            # Delete agent node
            # self del--> agent_node;
            agent_node spawn purge();
            # self del--> agent_node;
            return agent_node;
        }

        return None;
    }

    def delete_all() {
        # removes all agents from the graph
        agent_nodes = [];

        for agent_node in self.get_all() {
            agent_nodes.append(self.delete(agent_node.id));
        }

        return agent_nodes;
    }

}