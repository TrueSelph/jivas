import:py os;
import:py yaml;
import:py io;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.agent {Agent}
import:jac from agents {Agents}
import:jac from graph_walker {graph_walker}
import:jac from import_agent {import_agent}
import:py from jivas.agent.modules.agentlib.utils { jvdata_file_interface }

walker init_agents :graph_walker: {
    # initializes agents on the graph using the existing file-based descriptor

    has reporting:bool = False;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agents with Agents entry {

        if(agent_nodes := here.get_all()) {
            for agent_node in agent_nodes {

                try {
                    self.logger.info(f'initializing agent {agent_node.name}');
                    file_bytes = jvdata_file_interface.get_file(agent_node.descriptor);

                    if (not file_bytes) {
                        self.logger.error(f"agent descriptor not found: {agent_node.descriptor}");
                        continue;
                    }

                    descriptor = "";

					file = io.BytesIO(file_bytes);
            		descriptor = yaml.safe_load(file);

                    if(descriptor) {
                        here spawn import_agent(descriptor = descriptor, reporting = self.reporting);
                    }

                } except Exception as e {
                    self.logger.error(f"an exception occurred, {traceback.format_exc()}");
                }
            }
        }
    }

}
