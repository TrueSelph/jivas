import logging;
import json;
import traceback;
import from logging { Logger }
import from jac_cloud.core.archetype { NodeAnchor }
import from bson { ObjectId }

walker get_node_connections {
	has node_id: str = "";
	has depth: int = 0;
	# set up logger
    static has logger:Logger = logging.getLogger(__name__);

	obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

	can on_entry with entry {
		try {
			nid = self.node_id.split(":")[-1];
            current_depth = 0;
            nodes = [];
            edges = [];

            edge_collection = NodeAnchor.Collection.get_collection("edge");
            node_collection = NodeAnchor.Collection.get_collection("node");

            self.get_nodes_and_edges(
                nid,
                current_depth,
                self.depth,
                nodes,
                edges,
                node_collection,
                edge_collection,
            );


			report json.loads(json.dumps({
				"nodes": nodes,
				"edges": edges
			}, default=str));

		} except Exception as e {
			self.logger.error(f"an exception occurred, {traceback.format_exc()}");
		}
    }


	def get_nodes_and_edges(
	    nid: str,
	    current_depth: int,
	    depth: int,
	    nodes: list,
	    edges: list,
	    node_collection: NodeAnchor.Collection,
	    edge_collection: NodeAnchor.Collection,
	)  {
		    if (current_depth >= depth) {
		        return;
			}

		    outgoing_edges = edge_collection.find(
		        {
		            "$or": [
		                {"source": nid},
		                {"source": {"$regex": f"{nid}$"}},
		            ]
		        }
		    );

		    for edge in outgoing_edges {
		        edges.append(
		            {
		                "id": edge["_id"],
		                "name": edge["name"],
		                "source": edge["source"],
		                "target": edge["target"],
		                "data": edge["archetype"],
		            }
		        );

		        node_id = edge["target"].split(":")[-1];
		        connected_nodes = node_collection.find({"_id": ObjectId(node_id)});

		        for node in connected_nodes {
		            nodes.append(
		                {
		                    "id": node["_id"],
		                    "data": node["archetype"],
		                    "name": node["name"],
		                }
		            );

		            self.get_nodes_and_edges(
		                node["_id"],
		                current_depth + 1,
		                depth,
		                nodes,
		                edges,
		                node_collection,
		                edge_collection,
		            );
				}
			}
	    }
}
