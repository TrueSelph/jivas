import logging;
import from logging { Logger }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.action.action { Action }
import from jivas.agent.action.actions { Actions }
import from jivas.agent.action.subgraph_action.subgraph_action { SubgraphAction }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }


walker update_state(agent_graph_walker) {
    # action endpoint for updating states in a subgraph

    has state_id:str = "";
    has data:dict = {};
    has response:dict = {};
    has reporting:bool = True;
    has label:str = "";

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    class __specs__ {
        static has private: bool = False;
        static has excluded: list[str] = ["response"];  # exclude response from the specs
    }

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?SubgraphAction)(?enabled==True)(?label==self.label);
    }


    can on_action with Action entry {
        self.response = here.update_state(id = self.state_id, data = self.data);

        if self.reporting {
            report self.response;
        }
    }
}