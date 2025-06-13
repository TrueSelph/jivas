import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:py os;
import:py uuid;
import:py base64;

walker invoke_stt_action :interact_graph_walker: {

    has files: list[dict] = [];
    has response:dict = {};

    can on_agent with Agent entry {

        try {
            action_node = here.get_stt_action();
            if not action_node {
                self.response = {
                    "success": false,
                    "message": "Speech-to-text action not configured"
                };
                return;
            }

            if not self.files or not is_type(self.files, "list") or len(self.files) == 0 {
                self.response = {
                    "success": false,
                    "message": "No audio file provided"
                };
                return;
            }

            file = self.files[0];
            if not file or not is_type(file, "dict")
                or "type" not in file or "content" not in file {
                self.response = {
                    "success": false,
                    "message": "Invalid file format"
                };
                return;
            }

            if 'audio' in file['type'].lower()
                or file['type'].lower() == "application/octet-stream" {

                result = action_node.invoke_file(
                    audio_content=file['content'],
                    audio_type=file['type']
                );

                if not result or not is_type(result, "dict")
                    or "duration" not in result or "transcript" not in result {
                    self.response = {
                        "success": false,
                        "message": "Invalid response from STT service"
                    };
                    return;
                }

                self.response = {
                    "success": True,
                    "duration": result["duration"],
                    "transcript": result["transcript"]
                };
            } else {
                self.response = {
                    "success": False,
                    "message": f"Invalid file type: {file['type']}, must be audio"
                };
            }
        } except Exception as e {
            self.response = {
                "success": False,
                "message": f"Error processing audio: {str(e)}"
            };
        }
    }
}
