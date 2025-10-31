import from datetime { datetime, timezone }
import from typing { Any, Optional }
import from uuid { uuid4 }
import from jivas.agent.modules.text.chunking { chunk_long_message }
import from jivas.agent.modules.text.formatting { escape_string }
import from jivas.agent.modules.text.parsing { extract_first_name }
import from jivas.agent.memory.interaction { Interaction }
import from jivas.agent.memory.interaction_response { InteractionResponse, TextInteractionMessage }
import from jivas.agent.core.graph_node { GraphNode }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }

node Frame(GraphNode) {
    # represents the root node of a collection of interactions beloning to a single user (session)
    has :priv agent_id: str = "";
    has :priv session_id: str = str(uuid4());
    has :priv label: str = "";
    has :priv user_name: str = "";
    has :priv created_on:str = str((datetime.now(timezone.utc)).isoformat());
    has :priv last_interacted_on:str = str((datetime.now(timezone.utc)).isoformat());
    has :priv interactions:list[Interaction] = [];  # list of interactions in this frame

    def postinit {
        super.postinit();
        # add of node attributes which are protected from update operation
        self.protected_attrs += ['agent_id'];
    }

    def get_last_interaction() -> Optional[Interaction] {
        # retrieves the current interaction in this frame, i.e. the interaction which was last added;
        return self.get_interactions()[0] if self.get_interactions() else None;
    }

    def set_label(label:str) {
        self.label = label;
    }

    def create_interaction(utterance:str, channel:str='default') -> Interaction {
        # creates a new interaction object and returns it

        interaction = Interaction(
            agent_id=self.agent_id,
            frame_id=self.id,
            channel=channel,
            utterance=utterance,
            response = InteractionResponse(session_id=self.session_id)
        );
        if not self.interactions {
            # this is a first-time interaction, add the new_user flag
            interaction.data_set(key="new_user", value=True);
        }
        return interaction;
    }

    def add_unprompted_interaction(message:str, channel:str='default') -> Interaction {
        # adds new unprompted interaction to the head of the queue and sets the channel
        # these are interactions which are sent by AI without human utterance or from humans intervening
        # mainly for inserting items into the message history
        interaction = Interaction(
            agent_id=self.agent_id,
            frame_id=self.id,
            channel=channel,
            response=InteractionResponse(
                session_id=self.session_id,
                message=TextInteractionMessage(content=message)
            )
        );
        # close the unprompted interaction
        interaction.close();
         # attach the new interaction to the head of the frame
        return self.insert_interaction(interaction);
    }

    def insert_interaction(interaction:Interaction) -> Interaction {
        # inserts an interaction node at the head of the queue
        self.interactions.insert(0, interaction);
        # set last updated on timestamp
        self.last_interacted_on = str((datetime.now(timezone.utc)).isoformat());
        return interaction;
    }

    def get_interaction_history(interactions:int = 0) -> list[Optional[Interaction]] {
        # returns the last n interactions in this frame in chronological order
        # if n interactions is not specified, returns all interactions
        if interactions <= 0 {
            # Return all interactions in chronological order (oldest first)
            return list(reversed(self.get_interactions()));
        }

        # Return most recent 'n' interactions in chronological order
        n = min(interactions, len(self.get_interactions()));
        recent = self.get_interactions()[:n];
        return list(reversed(recent));
    }

    def get_transcript(interactions:int = 10, max_statement_length:int = 0, with_events:bool = False) -> str {
        # returns the transcript of the last specified number of interactions as a string

        transcript = "";
        statements = self.get_transcript_statements(interactions, max_statement_length, with_events=with_events);

        for item in statements {
            key = next(iter(item));
            value = item[key];
            transcript += f"{key} : {value} \n";
        }

        return transcript;
    }

    def get_transcript_statements(interactions:int = 10, max_statement_length:int = 0, with_events:bool = False) -> list[dict] {
        # returns the transcript of the last n interactions in this frame in chronological order
        # if n interactions is not specified, returns all interactions
        statements = [];
        interaction_nodes = self.get_interaction_history(interactions=interactions);

        def chunk_message(message:str) -> str {
            if(max_statement_length > 0) {
                message_chunks = chunk_long_message(message=message, max_length=max_statement_length, chunk_length=max_statement_length);
                if (len(message_chunks) > 1) {
                    message = message_chunks[0];
                }
            }
            return message;
        }

        for interaction in interaction_nodes {
            ai_statement = "";
            human_statement = "";

            # record the user utterance
            if (interaction.get_utterance()) {
                human_statement = escape_string(interaction.get_utterance());
                human_statement = chunk_message(message=human_statement);
                statements.append({"human": human_statement});
            }

            # record the AI response
            if (interaction.has_response()) {
                content = interaction.get_message().get_content();
                if(type(content) == list){
                    for item in content {
                        ai_statement = item['content'];
                        if (ai_statement) {
                            ai_statement = chunk_message(message=ai_statement);
                            statements.append({"ai": ai_statement});
                        }
                    }
                }else{
                    ai_statement = chunk_message(message=content);
                    statements.append({"ai": ai_statement});
                }
            }

            # add events to the transcript
            if (interaction.events and with_events) {
                for event in interaction.events {
                    statements.insert(-1, {"ai": f"event: {event}"});
                }
            }
        }

        return statements;
    }


    def get_active_event_statements() -> list[dict] {
        # returns a list of events to inform prompt of system-level events
        interaction = self.get_last_interaction();
        statements = [];
        if(interaction) {
            for event in interaction.events {
                statements.append({"ai": f"event: {event}"});
            }
        }
        return statements;
    }

    def get_interactions() -> list {
        # returns the list of interactions in this frame (in chronoligical order)
        return self.interactions;
    }

    def get_agent() {
        return &self.agent_id;
    }

    def prune_interactions(frame_size:int) {
        # prunes the list of interactions by the specified amount.
        # operation will leave 'frame_size' nodes or less in the frame and remove all older interactions
        if frame_size <= 0 {
            self.interactions = [];
            return;
        }

        if len(self.interactions) > frame_size {
            self.interactions = self.interactions[:frame_size];
        }
    }

    def refresh_interactions() {
        # prunes the given frame of interaction nodes down to 1.
        self.prune_interactions(frame_size=1);
    }

    def get_user_name(full:bool=False) {
        # returns a set user name or default if not set

        if(self.user_name and full) {
            return self.user_name;
        } elif(self.user_name) {
            return extract_first_name(self.user_name);
        } else {
            return "user";
        }
    }

    def set_user_name(user_name:str) {
        # sets user name for this session
        if user_name {
            self.user_name = user_name;
        }
    }
}
