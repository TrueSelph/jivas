import os;
import logging;
import traceback;
import json;
import from logging { Logger }
import from datetime { datetime, timedelta }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }
import from jivas.agent.core.agent { Agent }
import from jac_cloud.core.archetype { NodeAnchor }

walker get_interaction_logs(agent_graph_walker) {
	# returns the list of interactions within a date range
	has start_date: str = "";
	has end_date: str = "";
	has session_id: str = "";
	has frame_id: str = "";
	has channel: str = "";
	has timezone: str = "UTC";
	has page: int = 1;
	has per_page: int = 10;

    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        try {
            start = datetime.strptime(f"{self.start_date}T00:00:00+00:00", '%Y-%m-%dT%H:%M:%S%z');
            end = datetime.strptime(f"{self.end_date}T00:00:00+00:00", '%Y-%m-%dT%H:%M:%S%z');
            end = end + timedelta(days=1) - timedelta(milliseconds=1);

            collection = NodeAnchor.Collection.get_collection("interactions");

            match_criteria = {
                "agent_id": self.agent_id,
                "time_stamp": {
                    "$gte": start.isoformat(),
                    "$lte": end.isoformat()
                }
            };

            if self.frame_id {
                match_criteria["frame_id"] = self.frame_id;
            }

            if self.session_id {
                match_criteria["response.session_id"] = self.session_id;
            }

            if self.channel {
                match_criteria["channel"] = self.channel;
			}

		    # Get total count first
			count_pipeline = [
				{"$match": match_criteria},
				{"$count": "total"}
			];

			count_result = list(collection.aggregate(count_pipeline));
			total_count = count_result[0]["total"] if count_result else 0;

			# Calculate pagination
			skip_count = (self.page - 1) * self.per_page;
			total_pages = (total_count + self.per_page - 1) // self.per_page;

			pipeline = [
				{"$match": match_criteria},
				{"$sort": {"time_stamp": -1}},
				{"$skip": skip_count},
				{"$limit": self.per_page}
			];

			result = list(collection.aggregate(pipeline));

			report {
				"total": total_count,
				"data": json.loads(json.dumps(result, default=str)),
				"pages": total_pages
			};

		} except Exception as e {
			self.logger.error(f"An error occurred while fetching interaction logs: {traceback.format_exc()}");
			report {"error": str(e)};
		}
	}
}
