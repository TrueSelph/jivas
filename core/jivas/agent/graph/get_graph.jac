import logging;
import traceback;
import json;
import from logging { Logger }
import from jac_cloud.core.archetype { NodeAnchor }
import from bson { ObjectId }

walker get_graph {
	has root_node: str = "";
	# set up logger
    static has logger:Logger = logging.getLogger(__name__);

	obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

	can on_entry with entry {
	    try {
            edge_collection = NodeAnchor.Collection.get_collection("edge");
            node_collection = NodeAnchor.Collection.get_collection("node");

            edges = [];
            nodes = [];

            for node in node_collection.find({"root": ObjectId(self.root_node)}) {
                nodes.append({
                    "id": node["_id"],
                    "data": node["archetype"],
                    "name": node["name"]
                });
            }

            for edge in edge_collection.find({"root": ObjectId(self.root_node)}) {
                edges.append({
                    "id": edge["_id"],
                    "name": edge["name"],
                    "source": edge["source"],
                    "target": edge["target"],
                    "data": edge["archetype"]
                });
            }

			report  json.loads(json.dumps({
				"nodes": nodes,
				"edges": edges
			}, default=str));

		} except Exception as e {
			self.logger.error(f"an exception occurred, {traceback.format_exc()}");
		}
    }
}
