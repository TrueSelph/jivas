import:jac from jivas.agent.memory.memory_frame_walker { memory_frame_walker }
import:jac from jivas.agent.memory.memory { Memory }

walker get_frames :memory_frame_walker: {
    # endpoint to retrieve a list of frames with optional session_id filter

    has session_id:str = "";

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_memory with Memory entry {
        frame_nodes = here.get_frames(self.session_id);
        for frame_node in frame_nodes {
            report frame_node.export();
        }
    }

}