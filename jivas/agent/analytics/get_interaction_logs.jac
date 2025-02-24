import:py os;
import:py logging;
import:py traceback;
import:py json;
import:py from logging { Logger }
import:py from datetime { datetime, timedelta }
import:jac from jivas.agent.core.graph_walker { graph_walker }
import:jac from jivas.agent.core.agent { Agent }
import:py from jac_cloud.core.architype { NodeAnchor }

walker get_interaction_logs :graph_walker: {
	# returns the list of interactions within a date range
    has start_date: str = "";
    has end_date: str = "";
    has session_id: str = "";
    has channel: str = "";
    has timezone: str = "UTC";

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

            if self.session_id {
                match_criteria["session_id"] = self.session_id;
            }

            if self.channel {
                match_criteria["channel"] = self.channel;
			}

            pipeline = [
                {"$match": match_criteria},
                {"$sort": {"time_stamp": 1}}
            ];

            result = list(collection.aggregate(pipeline));


            report {
                "total": len(result),
                "data": json.loads(json.dumps(result, default=str))
            };

        } except Exception as e {
            self.logger.error(f"An error occurred while fetching interaction logs: {traceback.format_exc()}");
            report {"error": str(e)};
        }
    }
}
