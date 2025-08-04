import logging;
import traceback;
import from typing { Union }
import from logging { Logger }

node {{archetype}}(InteractAction) {

    # Declare your has variables to be persisted here
    # e.g has var_a : str = "string";
    
    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can touch(visitor: interact_graph_walker) -> bool {
        # override to authorize, redirect or deny the interact walker from running execute
    }

    can execute(visitor: interact_graph_walker) -> dict {
        # override to implement action execution
    }

    def healthcheck() -> Union[bool, dict] {
        # override to implement healthcheck operation
        # optionally returns a dict of (status:bool, severity:str [error|warning], message:str) if more information is needed
        return True;
    }

    #*     
    (Optional Abilities - Uncomment and implement as needed)

    # override to execute operations upon registration of action
    def on_register() { }

    # override to execute operations upon the reload of action
    def on_reload() { }

    # override to execute any setup code when all actions are in place
    def post_register() { }

    # override to execute operations upon enabling of action
    def on_enable() { }

    # override to execute operations upon disabling of action
    def on_disable() { }

    # override to execute operations upon deregistration of action
    def on_deregister() { }

    # override to implement pulse operation
    def pulse() { }

    # override to furnish analytics data for the action
    def analytics() { }

    *#
}
