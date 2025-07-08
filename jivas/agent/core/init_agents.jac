import os;
import yaml;
import io;
import logging;
import traceback;
import from logging { Logger }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.core.agents { Agents }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }
import from jivas.agent.core.import_agent {import_agent}
import from jivas.agent.modules.agentlib.utils { Utils, jvdata_file_interface }

walker init_agents(agent_graph_walker) {
    # initializes agents on the graph using the existing file-based descriptor

    has reporting:bool = False;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
        static has excluded: list = [
            "agent_id" # inherited agent_id not relevant for list agents params
        ];
    }

    can on_agents with Agents entry {
        visit [-->](`?Agent);
    }

    can on_agent with Agent entry {
        try {
            self.logger.info(f'initializing agent {here.name}');
            file_bytes = here.get_file(here.descriptor);

            if (not file_bytes) {
                self.logger.error(f"agent descriptor not found: {here.descriptor}");
                skip;
            }

            file = io.BytesIO(file_bytes);
            descriptor_data = yaml.safe_load(file);
            jpr_api_key = descriptor_data.get('jpr_api_key', None);

            if(descriptor_data) {
                here.get_actions().init_actions(agent_id=here.id, action_list=descriptor_data.get('actions', []), jpr_api_key=jpr_api_key);
            }

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }
    }

}
