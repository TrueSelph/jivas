import:py from typing { Optional }
import:jac from jivas.agent.memory.memory_frame_walker { memory_frame_walker }
import:jac from jivas.agent.memory.memory { Memory }

walker update_frame :memory_frame_walker: {
    # endpoint to update a frame label or user_name

    has session_id:str = "";
    has label:str="";
    has user_name:str="";

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_memory with Memory entry {

        if not self.session_id {
            Jac.get_context().status = 400;
            report f'missing session_id';
            return;
        }

        if(not self.label or self.user_name) {
            Jac.get_context().status = 400;
            report f'nothing supplied to update frame';
            return;
        }

        frame_node = here.get_frame(
            agent_id=self.agent_id,
            session_id=self.session_id
        );

        if(not frame_node) {
            Jac.get_context().status = 500;
            report f'unable to update frame node';
            return;
        }

        frame_node.set_label(self.label);
        frame_node.set_user_name(self.user_name);
        frame_node.update();

        report frame_node.export();
    }

}
