import:py os;
import:py yaml;
import:py io;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.core.agents { Agents }
import:jac from jivas.agent.core.agent_graph_walker { agent_graph_walker }
import:jac from jivas.agent.core.import_agent {import_agent}
import:py from jivas.agent.modules.agentlib.utils { Utils, jvdata_file_interface }

walker init_agents :agent_graph_walker: {
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

            # TODO: remove the legacy jvdata_file_interface once all instances are updated
            file_bytes = here.get_file(here.descriptor) or jvdata_file_interface.get_file(here.descriptor);

            if (not file_bytes) {
                self.logger.error(f"agent descriptor not found: {here.descriptor}");
                skip;
            }

            file = io.BytesIO(file_bytes);
            descriptor = yaml.safe_load(file);
            agents_node = Utils.node_obj([<--](`?Agents));

            if(descriptor) {
                agents_node spawn import_agent(descriptor = descriptor, reporting = self.reporting);
            }

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }
    }

}
