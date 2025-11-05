import logging;
import from logging { Logger }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.action.action { Action }
import from jivas.agent.action.actions { Actions }
import from jivas.agent.action.subgraph_action.subgraph_action { SubgraphAction }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }


walker list_states(agent_graph_walker) {
    # action endpoint for listing all documents processed by the deepdoc service

    has page:int = 1;
    has per_page:int = 10;
    has all:bool = True;  # new flag to indicate whether to return all documents
    has response:list[dict] = [];
    has reporting:bool = True;
    has agent_id:str = "";
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
        # get the list of documents from the manifest

        if self.all {
            self.response = here.list_states(page=self.page, limit=100);  # fetch all documents
        } else {
            self.response = here.list_states(page=self.page, limit=self.per_page);  # fetch paged documents
        }

        if self.reporting {
            report self.response;
        }
    }
}