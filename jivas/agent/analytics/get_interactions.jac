import:py os;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.core.graph_walker { graph_walker }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.memory.memory { Memory }
import:jac from jivas.agent.memory.frame { Frame }


walker get_interactions :graph_walker: {
    # returns the list of interactions of a frame.
    has interactions:dict = {};
    has session_id:str = "";

    static has logger:Logger = logging.getLogger(__name__);

	obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        visit [-->](`?Memory);
    }

    can on_memory with Memory entry {
        if(self.session_id) {
            visit [-->](`?Frame)(?session_id == self.session_id);
        } else {
            visit [-->](`?Frame);
        }
    }

    can on_frame with Frame entry {
        interaction_list = here.get_interactions();
        self.interactions[here.session_id] = interaction_list;
    }

    can on_exit with exit {
        report self.interactions;
    }

}

