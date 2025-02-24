import:jac from jivas.agent.core.agent {Agent}
import:jac from action {Action}
import:jac from jivas.agent.action.actions {Actions}
import:jac from interact_graph_walker {interact_graph_walker}

walker pulse :interact_graph_walker: {
    # when triggered, will trigger the pulse_action's relay pulse ability based on args supplied
    # this works in conjunction with the AgentPulse service

    has action_label:str = "";
    has agent_id:str = "";

    obj __specs__ {
        static has auth: bool = True;
    }

    can on_agent with Agent entry {
        # head to actions
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        # head to pulse action
        visit [-->](`?Action)(?label==self.action_label);
    }

    can on_action with Action entry {
        # trigger it's pulse ability
        here.pulse();
    }

}