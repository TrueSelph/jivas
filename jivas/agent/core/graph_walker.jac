import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from app { App }
import:jac from agents { Agents }

walker graph_walker {
    # base walker designed to traverse along app graph;
    has agent_id: str = "";
    has reporting: bool = True;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        # all graph_walkers are private by default, unless overridden
        static has private: bool = True;
    }

    can export(ignore_keys: list = ['__jac__']) {
        # convert the object to dictionary
        node_export = Utils.export_to_dict(self, ignore_keys);
        return node_export;
    }

    can update(data: dict = {}) -> graph_walker {
        # updates a graph node; expects a dict of attribute names mapped to values for updating
        if(data) {
            for attr in data.keys() {
                # check if attribute is a node attribute
                if (hasattr(self, attr)) {
                    self.attr = data[attr];
                }
            }
        }
        self.postupdate();

        return self;
    }

    can postupdate {
        # can be overriden to execute following a walker update
    }

    can on_root with `root entry {
        # spawn app node if not there
        visit [-->](`?App) else {
            self.logger.debug('app node created');
            app_node = here ++> App();
            visit app_node;
        }
    }

    can on_app with App entry {
        # spawn agents node if not there
        visit [-->](`?Agents) else {
            self.logger.debug('agents node created');
            agents_node = here ++> Agents();
            visit agents_node;
        }
    }

    can on_agents with Agents entry {

        if(self.agent_id) {

            try {

                if(agent_node := &self.agent_id) {

                    if agent_node.published {
                        visit agent_node;
                    }

                }

            } except Exception as e {
                Jac.get_context().status = 400;
                report "Invalid agent id";
                disengage;
            }
        }
    }
}
