import:jac from jivas.agent.core.agent {Agent}
import:jac from agent_graph_walker {agent_graph_walker}

walker healthcheck :agent_graph_walker: {
    # performs agent healthcheck; triggers the healthcheck ability of all actions on an agent

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        # head to actions
        healthcheck_report = here.get_healthcheck_report();

        if(healthcheck_report.get('status', 503) == 200) {
            Jac.get_context().status = 200;
        } else {
            Jac.get_context().status = 503;
        }

        report healthcheck_report;
    }

}
