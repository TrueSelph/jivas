import from jivas.agent.core.agent { Agent }
import from jivas.agent.action.action { Action }
import from jivas.agent.action.actions { Actions }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }

walker do_pulse(agent_graph_walker) {
    # when triggered, will trigger the pulse_action's relay pulse ability based on args supplied
    # this works in conjunction with the AgentPulse service

    has action_label:str = "";

    class __specs__ {
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        # head to actions
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        # head to pulse action
        visit [-->](`?Action)(?enabled==True)(?label==self.action_label);
    }

    can on_action with Action entry {
        # trigger it's pulse ability
        here.pulse();
    }

}