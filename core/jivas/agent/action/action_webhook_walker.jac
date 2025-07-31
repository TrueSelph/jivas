import json;
import logging;
import traceback;
import asyncio;
import from json { loads }
import from bson { ObjectId }
import from bson.errors { InvalidId }
import from logging { Logger }
import from types { SimpleNamespace }
import from pydantic { ValidationError }
import from pymongo.errors { ConnectionFailure, OperationFailure }
import from jac_cloud.jaseci.dtos { GenerateKey, KeyIDs }
import from jac_cloud.jaseci.models { Webhook }
import from jac_cloud.jaseci.datasources.redis { WebhookRedis }
import from jac_cloud.core.archetype { NodeAnchor }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }
import from jac_cloud.core.archetype { BulkWrite }

import from jivas.agent.modules.action.path { action_webhook_path }

import from jac_cloud.jaseci.routers.webhook { generate_key, delete }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }

walker action_webhook_walker(agent_graph_walker) {
    # base walker for action webhook implementations

    has agent_id: str;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    class __specs__ {
        static has webhook: dict = {
            "type": "path",
            "name": "key"
        };
        static has path: str = action_webhook_path(__module__);
        static has methods: list = ["get", "post"];
        static has private: bool = True; # hide endpoint in parent
    }

    # return the request object passed to the callback
    def get_request() -> Request {
        return _.get_context().connection;
    }

    # returns the json payload passed to the callback
    def get_request_json() -> dict {
        return asyncio.run(_.get_context().connection.json());
    }

    # generates webhook key and full webhook callback url
    def get_callback_url(
        base_url:str,
        agent_id:str,
        expiration:int=60) -> str
    {

        item = NodeAnchor.Collection.find_one({"name": "App"});
        if not item {
            return "";
        }

        # get callback path template
        path = action_webhook_path(self.get_module());
        # get walker name
        walker_name = self.get_type();

        # remove any existing webhook keys for this walker
        self.delete_webhook_key(walker_name);

        # Create mock request with user context
        request = SimpleNamespace();
        request._user = SimpleNamespace(root_id=ObjectId(str(item.root)));

        # Construct and validate the GenerateKey DTO
        try {
            params = GenerateKey.model_validate({
                "name": walker_name,
                "walkers": [walker_name],
                "nodes": ["root"],
                "expiration": {
                    "count": expiration,
                    "interval": "days"  # Consider making this configurable
                }
            });
        } except ValidationError as e {
            self.logger.error(f"Invalid key generation parameters: {str(e)}");
            return "";
        }

        # Generate new key
        try {
            result = generate_key(request, params);
            payload = json.loads(result.body.decode());
            webhook_key = payload.get("key");

            if not webhook_key {
                self.logger.error("Key generation returned empty key");
                return "";
            }
        } except (json.JSONDecodeError, AttributeError, KeyError) as e {
            self.logger.error(f"Failed to generate webhook key: {str(e)}");
            return "";
        }

        # Construct and return the full URL
        callback_path = path.format(agent_id=agent_id, key=webhook_key);
        return f"{base_url.rstrip('/')}/{callback_path.lstrip('/')}";

    }

    # Clean up existing key if present
    def delete_webhook_key(webhook_name:str) -> bool {
        # Clean up existing key if present
        session = Webhook.Collection.get_session();
        session.start_transaction();
        retry = 0;
        max_retry = BulkWrite.SESSION_MAX_TRANSACTION_RETRY;
        while retry <= max_retry {
            try {
                filter = {"name": {"$in": [webhook_name]}};
                whs = Webhook.Collection.find(filter);
                if Webhook.Collection.delete(filter, session).deleted_count == 1 {
                    for wh in whs {
                        WebhookRedis.hdelete(wh.key);
                    }
                    BulkWrite.commit(session);
                    return True;
                }
                break;
            } except (ConnectionFailure, OperationFailure) as ex {
                if ex.has_error_label("TransientTransactionError") {
                    retry += 1;
                    self.logger.error(
                        f"Error executing transaction! Retrying [{retry}/{max_retry}] ..."
                    );
                    continue;
                }
                self.logger.exception("Error executing transaction!");
                session.abort_transaction();
                break;
            } except Exception {
                self.logger.exception("Error executing transaction!");
                session.abort_transaction();
                break;
            }
        }

        return False;
    }

}
