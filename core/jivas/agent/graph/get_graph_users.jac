import logging;
import json;
import traceback;
import from logging { Logger }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }
import from jac_cloud.core.archetype { NodeAnchor }

walker get_graph_users {
	# set up logger
    static has logger:Logger = logging.getLogger(__name__);

	obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

	can on_entry with entry {
	    try {
            user_collection = NodeAnchor.Collection.get_collection("user");
            users = [];

            for user in user_collection.find() {
            	users.append({
                    "id": user["_id"],
                    "root_id": user["root_id"],
                    "email": user["email"]
                });
            }

			report json.loads(json.dumps(users, default=str));
		} except Exception as e {
			self.logger.error(f"an exception occurred, {traceback.format_exc()}");
		}
    }
}
