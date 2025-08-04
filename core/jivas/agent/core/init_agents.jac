import os;
import yaml;
import io;
import logging;
import traceback;
import from logging { Logger }
import from jivas.agent.core.app { App }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.core.agents { Agents }
import from jivas.agent.core.graph_walker { graph_walker }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }

walker init_agents(graph_walker) {
    # reloads actions for all agents on the graph using the graph in the DB

    has reporting:bool = False;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_app with App entry {
        # spawn agents node if not there
        visit [-->](`?Agents) else {
            self.logger.warning('Import an Agent to continue...');
        }
    }

    can on_agents with Agents entry {
        visit [-->](`?Agent);
    }

    can on_agent with Agent entry {
        try {
            reloaded = here.get_actions().reload_actions();
            message = f'loaded {here.name}' if reloaded else f'failed to load {here.name}';
            self.logger.info(message);
            if not reloaded {
                Jac.get_context().status = 500;
            }
            if self.reporting {
                report message;
            }
        } except Exception as e {
            message = f"an exception occurred, {traceback.format_exc()}";
            if self.reporting {
                report message;
            }
            Jac.get_context().status = 500;
            self.logger.error(message);
        }
    }

}
