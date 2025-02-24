import:py os;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from datetime { datetime, timedelta }
import:jac from jivas.agent.core.graph_walker { graph_walker }
import:jac from jivas.agent.core.agent { Agent }
import:py from jac_cloud.core.architype { NodeAnchor }

walker get_channels_by_date :graph_walker: {

    has start_date: str = "";
    has end_date: str = "";
	has timezone: str = "UTC";

	# set up logger
    static has logger:Logger = logging.getLogger(__name__);

	obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

	can on_agent with Agent entry {
		# Calculate number of days
		start = datetime.strptime(f"{self.start_date}T00:00:00+00:00", '%Y-%m-%dT%H:%M:%S%z');
        end = datetime.strptime(f"{self.end_date}T00:00:00+00:00", '%Y-%m-%dT%H:%M:%S%z');
		end = end + timedelta(days=1) - timedelta(milliseconds=1);

		days = 1 if (end - start).days == 0 else (end - start).days;



	    try {
			collection = NodeAnchor.Collection.get_collection("interactions");

			# Aggregation pipeline
			pipeline = [
				# Match documents within the given date range for the specified agent
				{
					"$match": {
						"agent_id": self.agent_id,
						"time_stamp": {
							"$gte": self.start_date,
							"$lte": self.end_date
						}
					}
				},
				# Convert string timestamp to date object and group by local date
				{
					"$group": {
						"_id": {
							"$dateToString": {
								"format": "%Y-%m-%dT00:00:00.000Z" if days > 1 else "%Y-%m-%dT%H:00:00.000Z",
								"date": {
									"$dateFromString": {
										"dateString": "$time_stamp"
									}
								},
								"timezone": self.timezone
							}
						},
						"unique_users": {"$addToSet": "$channel"}
					}
				},
				# Project to calculate unique user count
				{
					"$project": {
						"_id": 0,
						"date": "$_id",
						"count": {"$size": "$unique_users"}
					}
				},
				# Sort by date
				{
					"$sort": {"date": 1}
				}
			];

			# Execute aggregation pipeline
			result = list(collection.aggregate(pipeline));

			# Calculate total unique users
			total = sum([doc["count"] for doc in result]);

			# Format the report
			report  {
				"total": total,
				"data": result
			};

		} except Exception as e {
			self.logger.error(f"an exception occurred, {traceback.format_exc()}");
		}
    }
}
