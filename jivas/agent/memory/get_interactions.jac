import:jac from jivas.agent.memory.memory_frame_walker { memory_frame_walker }
import:jac from jivas.agent.memory.interaction { Interaction }
import:jac from jivas.agent.memory.advance { Advance }
import:jac from jivas.agent.memory.memory { Memory }
import:jac from jivas.agent.memory.frame { Frame }

walker get_interactions :memory_frame_walker: {
    # endpoint to retrieve a list of interactions with optional session_id filter

    has session_id:str = "";

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_memory with Memory entry {
        if(self.session_id) {
            visit [-->](`?Frame)(?session_id == self.session_id);
        } else {
            visit [-->](`?Frame);
        }
    }

    can on_frame with Frame entry {
        visit [-:Advance:->](`?Interaction);
    }

    can on_interaction with Interaction entry {
        report here.export();
        visit [-:Advance:->](`?Interaction);
    }

}