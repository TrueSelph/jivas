import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:py os;
import:py uuid;
import:py base64;

walker invoke_stt_action :interact_graph_walker: {

    has files: list[dict] = [];
    has response: dict = {};

    can on_agent with Agent entry {
        # Check if current node has STT action
        action_node = here.get_stt_action();
        if not action_node {
            self.response = {"success": False, "message": "STT action not configured"};
            return;
        }

        # Validate files list
        if not isinstance(self.files, list) {
            self.response = {"success": False, "message": "Invalid files format"};
            return;
        }

        if not self.files {
            self.response = {"success": False, "message": "No audio file provided"};
            return;
        }

        # Validate first file
        file = self.files[0];
        if not isinstance(file, dict) or 'type' not in file or 'content' not in file {
            self.response = {"success": False, "message": "Invalid file format"};
            return;
        }

        # Check file type
        if ('audio' in file['type'] or file['type'] == "application/octet-stream") {
            try {
                result = action_node.invoke_file(
                    audio_content=file['content'],
                    audio_type=file['type']
                );

                if not isinstance(result, dict) or 'duration' not in result or 'transcript' not in result {
                    self.response = {"success": False, "message": "Invalid STT response format"};
                    return;
                }

                self.response = {
                    "success": True,
                    "duration": result["duration"],
                    "transcript": result["transcript"]
                };
            } except Exception as e {
                self.response = {"success": False, "message": str(e)};
            }
        } else {
            self.response = {
                "success": False,
                "message": "Invalid file type, must be audio"
            };
        }
    }
}
