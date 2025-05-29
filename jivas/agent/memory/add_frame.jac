import:py from typing { Optional }
import:jac from jivas.agent.memory.memory_frame_walker { memory_frame_walker }
import:jac from jivas.agent.memory.memory { Memory }

walker add_frame :memory_frame_walker: {
    # endpoint to add a new frame to memory

    has label:str="";
    has user_name:str="";
    has session_id:Optional[str] = "";
    has force_session:Optional[bool] = True;

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_memory with Memory entry {

        frame_node = here.get_frame(
            agent_id=self.agent_id,
            user_name=self.user_name,
            label=self.label,
            session_id=self.session_id,
            force_session=self.force_session
        );

        if(not frame_node) {
            Jac.get_context().status = 500;
            report f'unable to add frame node';
            return;
        }

        report frame_node.export();
    }

}
