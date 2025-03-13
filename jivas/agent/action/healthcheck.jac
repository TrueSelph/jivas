import:jac from action {Action}
import:jac from jivas.agent.core.agent {Agent}
import:jac from jivas.agent.action.actions {Actions}
import:jac from interact_graph_walker {interact_graph_walker}

walker healthcheck :interact_graph_walker: {
    # performs agent healthcheck; triggers the healthcheck ability of all actions on an agent

    has trace:dict = {};

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        # head to actions
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        # head to action
        visit [-->](`?Action)(?enabled==True);
    }

    can on_action with Action entry {
        # trigger healthcheck ability
        self.trace[here.label] = here.healthcheck();;
    }

    can on_exit with exit {
        if self.trace {
            Jac.get_context().status = 200;
            health = {"agent": "OK"};

            for action in self.trace {
                if self.trace[action] == False {
                    Jac.get_context().status = 503;
                    health = self.trace;
                }
            }
        } else {
            Jac.get_context().status = 503;
            health = self.trace;
        }

        report health;
    }

}
