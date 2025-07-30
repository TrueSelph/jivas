import from jivas.agent.core.app { App }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.core.agents { Agents }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }
import from fastapi { UploadFile }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }

walker stt(agent_graph_walker) {

    has file: UploadFile = None;

    obj __specs__ {
        static has private: bool = False;
        static has path: str = "{agent_id}";
    }

    can on_agent with Agent entry {

        stt_action = here.get_stt_action();

        if not stt_action {
            Jac.get_context().status = 503;
            report "Unable to load STT Action for Agent";
            disengage;
        }

        if not self.file {
            Jac.get_context().status = 400;
            report "No audio file provided";
            disengage;
        }

        if 'audio' not in self.file.type or self.file.type != "application/octet-stream" {
            Jac.get_context().status = 400;
            report "Invalid file type, must be audio";
            disengage;
        }

        result = stt_action.invoke_file(
            audio_content=self.file.content,
            audio_type=self.file.type
        );

        if not isinstance(result, dict) or 'duration' not in result or 'transcript' not in result {
            Jac.get_context().status = 500;
            report "Invalid STT response format";
            disengage;
        }

        report {
            "duration": result["duration"],
            "transcript": result["transcript"]
        };


    }
}
