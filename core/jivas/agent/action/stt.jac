import from jivas.agent.core.app { App }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.core.agents { Agents }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }
import from fastapi { UploadFile }

walker stt {
    
    has file: UploadFile;
    has agent_id:str;

    class __specs__ {
        static has private: bool = False;
        static has methods: list = ["post"];
        static has path: str = "{agent_id}";
    }

    can on_app with App entry {
        # spawn agents node if not there
        visit [-->](`?Agents) else {
            self.logger.warning('Import an Agent to continue...');
        }
    }

    can on_agents with Agents entry {

        agent_node = None;

        if not self.agent_id {
            Jac.get_context().status = 400;
            report "Missing Agent ID";
            disengage;
        }

        try {
            agent_node = &self.agent_id;
        } except Exception as e {
            Jac.get_context().status = 400;
            report "Invalid agent id";
            disengage;
        }

        if not agent_node.published {
            Jac.get_context().status = 404;
            report "Agent is not published";
            disengage;
        }

        visit agent_node;
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

        report {
            "duration": result["duration"],
            "transcript": result["transcript"]
        };

        
    }
}
