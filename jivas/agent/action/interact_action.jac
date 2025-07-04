import from jivas.agent.action.action { Action }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }

node InteractAction(Action) {
    # represents an interactive execution on the agent action graph

    # an interact action may specify descriptive texts to influence intent classification
    # when the intent_action is in play
    has anchors: list = [];
    has functions: list = [];
    has weight:int = 0;

    # implement to authorize, redirect or deny the interact walker from running execute
    def touch(visitor:agent_graph_walker) -> bool abs;

    # implement action execution
    def execute(visitor:agent_graph_walker) abs;

    # override to implement action access denial
    def deny(visitor:agent_graph_walker) { }

    def get_children() {
        # returns immediate child actions of this action
        return [-->](`?Action);
    }

    def get_root_action() {
        # returns the interact action which is the top-level ancestor of this interact action
        return (self spawn _get_root_action()).root_action;
    }
}

walker _get_root_action {

    has root_action:InteractAction = None;

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_action with InteractAction entry {
        visit [<--](`?InteractAction) else {
            self.root_action = here;
        }
    }
}