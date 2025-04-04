import:jac from action {Action}
import:jac from jivas.agent.core.agent {Agent}
import:jac from jivas.agent.action.actions {Actions}
import:jac from interact_graph_walker {interact_graph_walker}

walker healthcheck :interact_graph_walker: {
    # performs agent healthcheck; triggers the healthcheck ability of all actions on an agent

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        # head to actions
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        # call healthcheck on all actions
        if(trace := here.healthcheck()) {

            Jac.get_context().status = 200;

            for action_label in trace.keys() {
                if trace[action_label] == False {
                    Jac.get_context().status = 503;
                    break;
                }
            }

        } else {
            Jac.get_context().status = 503;
        }

        report trace;
    }

}
