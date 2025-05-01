import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from app { App }

walker graph_walker {
    # base walker designed to traverse along app graph;

    has reporting: bool = True;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        # all graph_walkers are private by default, unless overridden
        static has private: bool = True;
    }

    can on_root with `root entry {
        # spawn app node if not there
        visit [-->](`?App) else {
            self.logger.error('App graph not initialized. Import an agent and try again.');
        }
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
        self.post_update();

        return self;
    }

    can post_update {
        # can be overriden to execute following a walker update
    }

}
