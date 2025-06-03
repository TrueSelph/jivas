import:py from typing { Optional }
import:jac from jivas.agent.memory.memory_frame_walker { memory_frame_walker }
import:jac from jivas.agent.memory.memory { Memory }

walker delete_frame :memory_frame_walker: {
    # endpoint to delete a frame and all interactions from memory

    has session_id:str = "";

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_memory with Memory entry {

        if(not self.session_id) {
            Jac.get_context().status = 400;
            report f'missing session_id';
            return;
        }

        deleted_nodes = here.purge(self.session_id);

        if(not deleted_nodes) {
            Jac.get_context().status = 500;
            report f'unable to delete frame with session_id {self.session_id}';
            return;
        }

        report deleted_nodes;
    }

}
