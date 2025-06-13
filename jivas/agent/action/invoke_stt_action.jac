import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:py os;
import:py uuid;
import:py base64;

walker invoke_stt_action :interact_graph_walker: {
    has files: list[dict] = [];

    can on_agent with Agent entry {
        action_node = here.get_stt_action();

        if not self.files {
            self.response = {"success": False, "message": "No audio file provided"};
        } else {
            file = self.files[0];

            if ('audio' in file['type']
                or file['type'] == "application/octet-stream") {
                result = action_node.invoke_file(
                    audio_content=file['content'],
                    audio_type=file['type']
                );
                self.response = {
                    "success": True,
                    "duration": result["duration"],
                    "transcript": result["transcript"]
                };
            } else {
                self.response = {
                    "success": False,
                    "message": "Invalid file type, must be audio"
                };
            }
        }

    }
}
