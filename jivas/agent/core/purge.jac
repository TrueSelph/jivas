import:py logging;
import:py traceback;
import:py from logging {Logger}

walker purge {
    # removes all nodes extending from the node on which it is spawned and the spawn node too

    has purge_spawn_node: bool = True;
    has walks:int = 0;
    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        # all graph_walkers are private by default, unless overridden
        static has private: bool = True;
    }

    can delete with Node entry {

        visit [-->]; # queue up next node(s), if any
        here del --> [-->]; # take care of the current edge(s) to any nodes

        if self.walks == 0 and not self.purge_spawn_node {
            skip;
        }

        self.logger.info(f"deleting node: {here}");
        Jac.destroy(here); # remove the current node
    }
}