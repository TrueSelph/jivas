import from jivas.agent.core.agent {Agent}
import from jivas.agent.action.agent_graph_walker {agent_graph_walker}
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }

walker healthcheck(agent_graph_walker) {
    # performs agent healthcheck; triggers the healthcheck ability of all actions on an agent

    class __specs__ {
        static has private: bool = False;
        static has methods: list = ["get"];
        static has auth: bool = False;
        static has path: str = "{agent_id}";
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
