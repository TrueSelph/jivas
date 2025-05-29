import:py from datetime { datetime }
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.core.graph_node { GraphNode }
import:jac from frame { Frame }
import:jac from collection { Collection }
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

    can get_frame(agent_id:str, session_id:str, label:str="", user_name:str="", force_session:bool=False, lookup:bool=False) -> Frame {
        # attempt to retrieve an existing session or spawn then traverse to a new one if force is on
        # if lookup is on, it operates in search mode

        frame_node = Utils.node_obj( [-->](`?Frame)(?session_id == session_id) );

        if not frame_node and not lookup {
            if(force_session) {
                frame_node = Frame(agent_id=agent_id, label=label, user_name=user_name, session_id = session_id);
            } else {
                frame_node = Frame(agent_id=agent_id, label=label, user_name=user_name);
            }
            # attach new frame to memory graph
            self ++> frame_node;
        }

        return frame_node;
    }

    can get_frames(session_id:str="") -> list[Frame] {
        # returns a list of all frame nodes attached to memory or specific ones by session_id if supplied

        if session_id {
            return [-->](`?Frame)(?session_id == session_id);
        }

        frames = [-->](`?Frame);
        # sort frames by 'created_on' ISO datetime string
        return sorted(frames, key = with frame:Frame can datetime.fromisoformat(frame.created_on) if hasattr(frame, 'created_on') and frame.created_on else "", reverse=True);
    }

    can get_collection(collection_name:str) -> Collection {
        # attempt to retrieve an existing collection or spawn then traverse to a new one if it doesnt exist

        collection_node = Utils.node_obj( [-->](`?Collection)(?name == collection_name) );

        if not collection_node {
            collection_node = Collection(name=collection_name);
            # attach new collection to memory graph
            self ++> collection_node;
        }

        return collection_node;
    }

    can import_memory(data:dict, overwrite:bool=True) -> bool {
        # imports a structured memory dump into memory
        # set overwrite to True in order to wipe memory first
        if not data or not isinstance(data, dict) {
            return False;
        }

        try {

            if overwrite {
                # first purge memory
                self.purge();
            }

            # grab agent node
            agent_node = self.get_agent();

            for frame_data in data.get('memory') {

                # add the session id if we can grab it
                if(session_id := frame_data.get('frame', {}).get('context', {}).get('session_id', None)) {

                    # add the frame node
                    frame_node = self.get_frame(agent_id=agent_node.id, session_id=session_id, force_session=True);
                    # add the properties under context
                    frame_node.update(frame_data.get('frame', {}).get('context', {}));

                    interactions = frame_data.get('frame', {}).get('interactions', []);
                    for interaction_data in interactions {
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

    can export_memory(session_id:str="") {
        # return a structured memory dump of all agent frames or only those with session_id if supplied
        return (self spawn _export_memory(session_id=session_id)).frame_data;
    }

    can memory_healthcheck(session_id:str = "") {

        # init stats
        total_frames = 0;
        total_interactions = 0;

        # grab frames and count length
        frames = self.get_frames(session_id);
        total_frames = len(frames);

        # loop through frames and count interactions
        for frame in frames {
            # count interactions and add to total
            total_interactions += len(frame.get_interactions());
        }

        return {
            "total_frames": total_frames,
            "total_interactions": total_interactions
        };
    }

    can purge(session_id:str=None) {
        # backwards compat for older actions
        return self.purge_frame_memory(session_id);
    }

    can purge_frame_memory(session_id:str=None) {
        # removes all frames and interactions (or by session_id)
        return (self spawn _purge_frames(session_id=session_id)).removed;
    }

    can purge_collection_memory(collection_name:str=None) {
        # removes all collections and related child nodes (or by collection_name)
        return (self spawn _purge_collections(collection_name=collection_name)).removed;
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

walker _purge_frames {
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

walker _purge_collections {
    # walker which carries out the traversal and purging of collections and any related child nodes

    has collection_name:str = "";
    has removed:list = [];

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_memory with Memory entry {
        if(self.collection_name) {
            visit [-->](`?Collection)(?name == self.collection_name);
        } else {
            visit [-->](`?Collection);
        }
    }

    can on_collection with Collection entry {
        visit [-->] else {
            self.removed.append(here);
            Jac.destroy(here);
        }
    }

    can on_collection_node with Node entry {
        visit [-->];
        self.removed.append(here);
        Jac.destroy(here);
    }
}

walker _export_memory {
    # visits all frames which belong to an optional session_id and returns them and related interactions

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has session_id:str = ""; # optional, if not supplied, all frames will be exported
    has frame_data:dict = {}; # dict with id of frame as key mapping to all interactions on that frame

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_memory with Memory entry {
        # init frame data
        self.frame_data = {
            "memory": []
        };

        if(self.session_id) {
            # if session_id is supplied, filter frames
            visit [-->](`?Frame)(?session_id == self.session_id);
        } else {
            # otherwise export all frames
            visit [-->](`?Frame);
        }
    }

    can on_frame with Frame entry {

        interaction_data = [];

        # grab interactions
        interactions = here.get_interactions();

        # fix interaction object by exporting what we
        for interaction_node in interactions {
            # add to interactions
            interaction_data.append({"interaction": {"context": interaction_node.export()}});
        }

        # grab interactions and add to frame data
        self.frame_data["memory"].append(
            {
                "frame": {
                    "context": here.export(),
                    "interactions": interaction_data
                }
            }
        );

    }

}
