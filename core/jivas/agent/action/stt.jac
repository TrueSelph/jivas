import from jivas.agent.core.app { App }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.core.agents { Agents }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }
import from fastapi { UploadFile }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }
import asyncio;

walker stt(agent_graph_walker) {
    has file: UploadFile;

    obj __specs__ {
        static has private: bool = False;
        static has path: str = "{agent_id}";
        static has auth: bool = False;
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

        if 'audio' not in self.file.content_type  {
            Jac.get_context().status = 400;
            report "Invalid file type, must be audio";
            disengage;
        }

        loop = asyncio.new_event_loop();

        try {
	        result = stt_action.invoke_file(
	        	audio_content=loop.run_until_complete(self.file.read()),
	            audio_type=self.file.content_type
	        );
        } except Exception as e {
        	self.logger.error(f"Unable to process audio file: {str(e)}");
        } finally {
	        loop.close();
		}

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
