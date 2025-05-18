import:py io;
import:py zipfile;
import:jac from agent_graph_walker { agent_graph_walker }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.actions { Actions }
import:py from jivas.agent.modules.agentlib.utils { Utils }


walker export_daf :agent_graph_walker: {
    # exports and packages an agent daf, saves it to file and returns the URL for download

    has clean:bool = False;
    has with_knowledge: bool = True;
    has with_memory: bool = False;

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {

        daf_contents = {};

        daf_name = here.meta.get('namespace', 'agent_daf');
        # prepare the daf info
        daf_info_yaml = Utils.yaml_dumps( here.get_daf_info() );
        # prepare the agent descriptor
        daf_descriptor_yaml = here.get_descriptor(as_yaml=True, clean=self.clean);

        if(daf_info_yaml and daf_descriptor_yaml) {
            daf_contents = {
                "info.yaml" : daf_info_yaml,
                "descriptor.yaml": daf_descriptor_yaml,
            };
        } else {
            Jac.get_context().status = 503;
            report "no valid daf info or descriptor generated, unable to complete export";
            disengage;
        }

        if(self.with_memory) {
            # prepare memory descriptor
            daf_memory_data = here.get_memory().export_memory();
            if( daf_memory_yaml := Utils.yaml_dumps(daf_memory_data)) {
                daf_contents['memory.yaml'] = daf_memory_yaml;
            } else {
                self.logger.error("Unable to export memory. It may be blank or there may be a YAML conversion issue.");
            }
        }

        if(self.with_knowledge) {
            # prepare knowledge
            daf_knowledge = [];
            try {
                if(vector_store_action := here.get_action(action_label = here.get_vector_store_action())) {
                    if( daf_knowledge_yaml := vector_store_action.export_knodes()) {
                        daf_contents['knowledge.yaml'] = daf_knowledge_yaml;
                    } else {
                        self.logger.error("Unable to export knowledge. It may be blank or there may be a YAML conversion issue.");
                    }
                }
            } except Exception as e {
                Jac.get_context().status = 503;
                error_message = f"Unable to export knowledge : {e}";
                self.logger.error(error_message);
                report error_message;
                disengage;
            }
        }

        # let's output and archive the zipfile as bytes
        buffer = io.BytesIO();
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf {
            for (fname, content) in daf_contents.items() {
                zipf.writestr(fname, content);
            }
        }
        daf_bytes = buffer.getvalue();
        daf_output_filename = f"dafs/{daf_name.replace('/','_')}.daf.zip";
        if( here.save_file(daf_output_filename, daf_bytes) ) {
            Jac.get_context().status = 200;
            # return the fileserved URL
            report here.get_file_url(daf_output_filename);
        } else {
            Jac.get_context().status = 503;
            error_message = "There was a problem generating the DAF";
            self.logger.error(error_message);
            report error_message;
        }
    }
}