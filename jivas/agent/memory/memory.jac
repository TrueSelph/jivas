import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.core.graph_node { GraphNode }
import:jac from frame { Frame }
import:jac from retrace { Retrace }
import:jac from tail { Tail }
import:jac from interaction { Interaction }
import:py dotenv;
import:py os;
import:py json;
import:py uuid;
import:py yaml;

node Memory :GraphNode: {
    # represents the root memory node for an agent

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can get_frame(agent_id:str, session_id:str, force_session:bool=False, lookup:bool=False) -> Frame {
        # attempt to retrieve an existing session or spawn then traverse to a new one if force is on

        frame_node = Utils.node_obj( [-->](`?Frame)(?session_id == session_id) );

        if not frame_node and not lookup {
            if(force_session) {
                frame_node = Frame(agent_id=agent_id, session_id = session_id);
            } else {
                frame_node = Frame(agent_id=agent_id);
            }
            # attach new frame to memory graph
            self ++> frame_node;
        }

        return frame_node;
    }

    can get_frames() -> list[Frame] {
        # returns a list of all frame nodes attached to memory
        return [-->](`?Frame);
    }

    can import_memory(data:dict, overwrite:bool=True) {
        # imports a structured memory dump into memory
        # set overwrite to True in order to wipe memory first
        if not data or not isinstance(data, dict) {
            return False;
        }

        if overwrite {
            # first purge memory
            self.purge();
        }

        # grab agent node
        agent_node = self.get_agent();

        try {
            for frame_data in data.get('memory') {

                # add the session id if we can grab it
                if(session_id := frame_data.get('frame', {}).get('context', {}).get('session_id', None)) {

                    # add the frame node
                    frame_node = self.get_frame(agent_id=agent_node.id, session_id=session_id, force_session=True);
                    # add the properties under context
                    frame_node.update(frame_data.get('frame', {}).get('context', {}));

                    for interaction_data in frame_data.get('frame', {}).get('interactions', []) {
                        # get last interaction node
                        last_interaction_node = frame_node.get_last_interaction();
                        # create the interaction node
                        interaction_node = Interaction(agent_id = agent_node.id);
                        # if session_id is not in interaction data, add it (for legacy)
                        if( not (interaction_data.get('interaction', {}).get('context',{}).get('response',{}).get('session_id')) ) {
                            interaction_data['interaction']['context']['response']['session_id'] = frame_node.session_id;
                        }
                        interaction_node.update(interaction_data.get('interaction', {}).get('context', {}));
                        # insert the interaction node
                        frame_node.insert_interaction(interaction_node, last_interaction_node);
                    }

                    self.logger.info(f"uploaded memory of: {frame_node.session_id}");
                } else {
                    self.logger.error(f"invalid session ID on frame, skipping...");
                }
            }

            return True;
        } except Exception as e {
            self.logger.warning(f"uploaded memory failed: {e}");
        }

        return False;
    }

    can export_memory(agent_id:str, session_id:str, json:bool, save_to_file:bool) {
        # return a structured memory dump
        return (self spawn _export_memory(agent_id=agent_id, session_id=session_id, json=json, save_to_file=save_to_file)).frame_data;
    }

    can memory_healthcheck(agent_id:str, session_id:str = "", verbose:bool=False) {
        # init stats
        total_users = 0;
        total_interactions = 0;

        # grab all frames and count length
        total_users = len(self.get_frames());

        # loop through frames and count interactions
        for user in self.get_frames() {
            # count interactions and add to total
            total_interactions += len(user.get_interactions());
        }

        return {
            "total_users": total_users,
            "total_interactions": total_interactions
        };
    }

    can purge(session_id:str=None) {
        # removes all frames and interactions (or by session_id)
        return (self spawn _purge(session_id)).removed;
    }

    can refresh(session_id:str) {
        # prunes interactions under frame down to the last, most recent one
        if ( frame_node := self.get_frame(None, session_id = session_id) ) {
            frame_node.refresh_interactions();
            return True;
        }

        return False;
    }

    can get_agent() {
        return Utils.node_obj([<--]);
    }
}

walker _purge {
    # walker which carries out the traversal and purging of frames and related interactions

    has session_id:str = "";
    has removed:list = [];

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_memory with Memory entry {
        if(self.session_id) {
            visit [-->](`?Frame)(?session_id == self.session_id);
        } else {
            visit [-->](`?Frame);
        }
    }

    can on_frame with Frame entry {
        visit [-:Tail:->] else {
            self.removed.append(here);
            Jac.destroy(here);
        }
    }

    can on_interaction with Interaction entry {
        visit [-:Retrace:->];
        self.removed.append(here);
        Jac.destroy(here);
    }
}

walker _export_memory {
    # walker which carries out the traversal and purging of frames and related interactions

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has status:int = 200;
    has response:str = "";
    has session_id:str = "";
    has agent_id:str = ""; # TODO: Add agent id validation
    has frame_data:dict = {}; # dict with id of frame as key mapping to all interactions on that frame
    has file_url:str = "";
    has file_path:str = "";
    has json:bool = false;
    has save_to_file:bool = false;

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_memory with Memory entry {
        # init frame data
        self.frame_data = {
            "memory": []
        };

        # navigate to frames
        if(self.session_id) {
            # only export the session
            visit [-->](`?Frame)(?session_id == self.session_id);
        } else {
            # export all frames
            visit [-->](`?Frame);
        }
    }

    can on_frame with Frame entry {

        # grab interactions object
        interactions = here.get_interactions();

        # init interactions
        interaction_nodes = [];

        # fix interaction object by exporting what we
        for interaction_node in interactions {
            # add to interactions
            interaction_nodes.append({"interaction": {"context": interaction_node.export()}});
        }

        # grab interactions and add to frame data
        self.frame_data["memory"].append(
            {
                "frame": {
                    "context": here.export(),
                    "interactions": interaction_nodes
                }
            }
        );

    }

    can export_memory with exit {
        # load env variables from .env file
        dotenv.load_dotenv();

        # output the yaml
        if(None) {
            # create file path
            file_name = f"memory/{str(uuid.uuid4())}";

            if(not self.json){
                # set file path
                self.file_path = f"{file_name}.yaml";

                # write to file
                Utils.dump_yaml_file(self.file_path, self.frame_data);
            }else{
                # set file path
                self.file_path = f"{file_name}.json";

                # write to file
                Utils.dump_json_file(self.file_path, self.frame_data);
            }

        }
    }
}
