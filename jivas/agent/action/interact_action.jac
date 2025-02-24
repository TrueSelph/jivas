import:jac from action { Action }
import:jac from interact_graph_walker { interact_graph_walker }

node InteractAction :Action: {
    # represents an interactive execution on the agent action graph

    # an interact action may specify descriptive texts to influence intent classification
    # when the intent_action is in play
    has anchors: list = [];
    has functions: list = [];
    has weight:int = 0;

    can touch(visitor: interact_graph_walker) -> bool {
        # override to authorize, redirect or deny the interact walker from running execute
    }

    can execute(visitor: interact_graph_walker) -> dict {
        # override to implement action execution
    }

    can deny(visitor: interact_graph_walker) -> dict {
        # override to implement action access denial
    }

    can get_children() {
        # returns immediate child actions of this action
        return [-->](`?Action);
    }

    can get_root_action() {
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