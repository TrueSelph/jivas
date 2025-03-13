import:py logging;
import:py traceback;
import:py from logging {Logger}
import:jac from graph_node { GraphNode }

walker purge {
    # removes all nodes extending from the node on which it is spawned and the spawn node too

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can delete with GraphNode entry {
        self.logger.info(f"deleting node: {here}");
        visit [-->];
        Jac.destroy(here);
    }
}