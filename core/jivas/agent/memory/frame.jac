import from datetime { datetime, timezone }
import from typing { Any, Optional }
import from uuid { uuid4 }

import from jivas.agent.modules.text.chunking { chunk_long_message }
import from jivas.agent.modules.text.formatting { escape_string }
import from jivas.agent.modules.text.parsing { extract_first_name }

import from jivas.agent.memory.interaction { Interaction }
import from jivas.agent.memory.interaction_response { InteractionResponse, TextInteractionMessage }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.action.interact_action { InteractAction }
import from jivas.agent.memory.tail { Tail }
import from jivas.agent.memory.advance { Advance }
import from jivas.agent.memory.retrace { Retrace }
import from jac_cloud.plugin.jaseci { JacPlugin as Jac }

node Frame(GraphNode) {
    # represents the root node of a collection of interactions beloning to a single user (session)
    has :priv agent_id: str = "";
    has :priv session_id: str = str(uuid4());
    has :priv label: str = "";
    has :priv user_name: str = "";
    has :priv created_on:str = str((datetime.now(timezone.utc)).isoformat());
    has :priv last_interacted_on:str = str((datetime.now(timezone.utc)).isoformat());

    def postinit {
        super.postinit();
        # add of node attributes which are protected from update operation
        self.protected_attrs += ['agent_id'];
    }

    def get_last_interaction(retraces:int=1) -> Interaction {
        # retrieves the last interaction in this frame by default;
        # can attempt to retrace by a number specified in the retraces param to retrieve older interactions
        return (self spawn _get_interaction_by_retraces(retraces = retraces)).interaction_node;
    }

    def is_first_interaction -> bool {
        # denotes the very first interaction of this frame
        last_interaction = self.get_last_interaction();
        return (last_interaction.data_get("new_user") is not None);
    }

    def set_resume_action(action_label:str) {
        # adds a named resume action node name to the context_data of the interaction
        # the interact walker will head straight here once it's turn comes back up
        if(last_interaction := self.get_last_interaction()) {
            last_interaction.data_set(key="resume_action", value=action_label);
        }
    }

    def get_resume_action(last_interaction_node: Interaction) -> InteractAction {
        # gets a named resume action node from the context_data of the interaction
        # the interact walker will head straight here once it's turn comes back up
        action_node = None;

        if(last_interaction_node) {
            if(action_label := last_interaction_node.data_get("resume_action")) {
                agent_node = self.get_agent();
                action_node = agent_node.get_action(action_label = action_label);
            }
        }

        return action_node;
    }

    def set_label(label:str) {
        self.label = label;
    }

    def add_interaction(utterance:str, channel:str='default') -> Interaction {
        # adds new prompted interaction to the end of the frame and sets the channel

        last_interaction_node = self.get_last_interaction();

        interaction_node = Interaction(
            agent_id=self.agent_id,
            channel=channel,
            utterance=utterance,
            response = InteractionResponse(session_id=self.session_id)
        );

        return self.insert_interaction(interaction_node, last_interaction_node);
    }


    def add_unprompted_interaction(message:str, channel:str='default') -> Interaction {
        # adds new unprompted interaction to the end of the frame and sets the channel
        # these are interactions which are sent by AI without human utterance or from humans intervening
        # mainly for inserting items into the message history

        last_interaction_node = self.get_last_interaction();

        interaction_node = Interaction(
            agent_id=self.agent_id,
            channel=channel,
            response=InteractionResponse(
                session_id=self.session_id,
                message=TextInteractionMessage(content=message)
            )
        );

        # close the unprompted interaction
        interaction_node.close();

        return self.insert_interaction(interaction_node, last_interaction_node);
    }

    def insert_interaction(interaction_node:Interaction, last_interaction_node:Interaction=None) -> Interaction {
        # inserts an interaction node with reference to the last interaction node, if any

        if (not last_interaction_node and not [->:Advance:->]) {

            # if there is no interaction from the root frame, attach the first one
            self +>:Advance:+> interaction_node;
            self <+:Retrace:<+ interaction_node;
            # add a tail reference
            self +>:Tail:+> interaction_node;
            # this is a first-time interaction, add the new_user flag
            interaction_node.data_set(key="new_user", value=True);

        } else {

            # if there is an interaction, let's attach a fresh one at the end of the last_interaction_node...
            # remove the tail edge, if it exists
            if ([->:Tail:->]) {
                # remove the tail to the old last interaction
                self del->:Tail:-> [->:Tail:->];
                # add the tail to the new interaction
                self +>:Tail:+> interaction_node;
                # attach the new interaction_node to the last interaction
                last_interaction_node.attach_interaction(interaction_node);
            }
        }

        # set last updated on timestamp
        self.last_interacted_on = str((datetime.now(timezone.utc)).isoformat());

        return interaction_node;
    }

    def get_interaction_history(interactions:int = 0) -> list[Optional[Interaction]] {
        # returns the list of interactions in this frame with optional limit
        return (self spawn _get_interaction_history(interactions=interactions)).interaction_nodes;
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
        # returns the transcript of the last specified number of interactions as a list
        statements = (self spawn _get_transcript_statements(interactions, max_statement_length, with_events=with_events)).statements;
        return statements;
    }

    def get_active_event_statements() -> list[dict] {
        # returns a list of events to inform prompt of system-level events
        interaction_node = self.get_last_interaction();
        statements = [];
        if(interaction_node) {
            for event in interaction_node.events {
                statements.append({"ai": f"event: {event}"});
            }
        }
        return statements;
    }

    def get_interactions() -> list {
        # returns the list of interactions in this frame (in chronoligical order)
        return (self spawn _get_interactions()).interactions;
    }

    def get_agent() {
        return &self.agent_id;
    }

    def prune_interactions(frame_size:int) {
        # prunes the given frame of interaction nodes by the specified amount.
        # operation will leave 'frame_size' nodes or less in the frame and remove all older nodes
        self spawn _prune_interactions(frame_size=frame_size);
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

walker _get_interaction_history {
    # returns a collection of closed (complete) interactions in a frame by retracing from the last interaction node
    has interactions:int = 0; # number of recent interactions to retrieve; 0 is all
    has interaction_nodes:list = [];
    has walks:int = 0;

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_frame with Frame entry {
        visit [->:Tail:->](`?Interaction);
    }

    can on_interaction with Interaction entry {

        if here.is_closed() {
            self.walks += 1;
            if(self.interactions > 0 and (self.interactions == self.walks) ) {
                self.interaction_nodes.reverse();
                disengage;
            }
            self.interaction_nodes.append(here);
        }

        visit [->:Retrace:->](`?Interaction)(?closed == True);
    }

    can on_exit with exit {
        # reverse the order of recent interaction nodes to be in chronological order
        self.interaction_nodes.reverse();
    }
}

walker _get_transcript_statements {
    # returns the transcript of the last specified number of interactions as a list

    has interactions:int = 1;
    has max_statement_length:int = 0;
    has with_events:bool = False;
    has statements:list = [];

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_frame with Frame entry {

        interaction_nodes = (here spawn _get_interaction_history(interactions=self.interactions)).interaction_nodes;

        for interaction in interaction_nodes {
            ai_statement = "";
            human_statement = "";

            # record the user utterance
            if (interaction.utterance) {
                human_statement = escape_string(interaction.utterance);
                human_statement = self.chunk_message(message=human_statement);
                self.statements.append({"human": human_statement});
            }

            # record the AI response
            if (interaction.has_response()) {
                content = interaction.get_message().get_content();
                if(type(content) == list){
                    for item in content {
                        ai_statement = item['content'];
                        if (ai_statement) {
                            ai_statement = self.chunk_message(message=ai_statement);
                            self.statements.append({"ai": ai_statement});
                        }
                    }
                }else{
                    ai_statement = self.chunk_message(message=content);
                    self.statements.append({"ai": ai_statement});
                }
            }

            # add events to the transcript
            if (interaction.events and self.with_events) {
                for event in interaction.events {
                    self.statements.append({"ai": f"event: {event}"});
                }
            }
        }
    }

    def chunk_message(message:str) -> str {
        if(self.max_statement_length > 0){
            message_chunks = chunk_long_message(message=message, max_length=self.max_statement_length, chunk_length=self.max_statement_length);
            if (len(message_chunks) > 1) {
                message = message_chunks[0];
            }
        }
        return message;
    }
}

walker _get_interactions {
    # returns the list of interactions of a frame (in chronoligcal order)
    has interactions:list = [];

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_frame with Frame entry {
        visit [->:Advance:->](`?Interaction);
    }

    can on_interaction with Interaction entry {
        self.interactions.append(here);
        visit [->:Advance:->](`?Interaction);
    }
}

walker _get_interaction_by_retraces {
    # retraces from frame by a factor of 'retraces' to retrieve any interaction found
    has retraces:int = 1;
    has walks:int = 0;
    has interaction_node:Interaction = None;

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_frame with Frame entry {
        visit [->:Tail:->](`?Interaction);
    }

    can on_interaction with Interaction entry {

        self.walks += 1;

        if(self.retraces == self.walks) {
            self.interaction_node = here;
            disengage;
        }

        visit [->:Retrace:->](`?Interaction);
    }
}

walker _prune_interactions {
    # prunes the given frame of interaction nodes by the specified amount.
    # operation will leave 'frame_size' nodes or less in the frame and remove all older nodes
    has frame_size:int = 1;
    has frame_node:Frame = None;
    has interaction_head:Interaction = None;
    has retraces:int = 0;

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_frame with Frame entry {
        # if we're here, we'need to connect the advance edge to the new top of the interaction chain
        self.frame_node = here;

        if (self.frame_size <= 0)  {
        	disengage;
        }

        if (self.interaction_head) {
            here +>:Advance:+> self.interaction_head;
        } else {
            # take to last interaction node
            visit here.get_last_interaction();
        }
    }

    can on_interaction with Interaction entry {
        # should be starting off at the very last interaction...let's count retraces until frame_size
        # once frame size is met, link to frame_node..then keep retracing and deleting interaction nodes
        # until frame node is met

        self.retraces += 1;
        # once we get to the interaction node numbering frame_size and it had nodes before it, it becomes our new interaction_head
        if ((self.retraces == self.frame_size) and ([->:Retrace:->](`?Interaction))) {
            # make a note of the new interaction head node
            self.interaction_head = here;
            # set a course to continue upwards in the chain, deleting old interactions as we go..
            visit [->:Retrace:->](`?Interaction);
            # now, remove the retrace edge to the node before it
            here del --> [->:Retrace:->](`?Interaction);
            # add a new retrace edge to the frame node from here so it doesnt orphan the rest of the chain..
            if (not [->:Retrace:->](`?Frame)) {
                here +>:Retrace:+> self.frame_node;
            }

        } elif (self.retraces > self.frame_size) {
            # if we're here, it means we are in pruning mode
            visit [->:Retrace:->](`?Interaction) else {
                Jac.destroy(here);
            }
        } else {
            visit [->:Retrace:->](`?Interaction);
        }
    }

}
