import:py from typing { Any, Optional }
import:py from uuid { uuid4 }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from interaction { Interaction }
import:jac from interaction_response { InteractionResponse, TextInteractionMessage }
import:jac from jivas.agent.core.graph_node { GraphNode }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from tail { Tail }
import:jac from advance { Advance }
import:jac from retrace { Retrace }

node Frame :GraphNode: {
    # represents the root node of a collection of interactions beloning to a single user (session)
    has agent_id: str = "";
    has session_id: str = str(uuid4());
    has user_name: str = "";
    has variables: dict = {};

    can variable_get(key:str, default:Optional[Any] = None) -> Any {
        # retrieves a named variable by key
        if (variable := self.variables.get(key)) {
            return variable;
        } elif( default ) {
            return default;
        } else {
            return None;
        }
    }

    can variable_set(key:str, value:Any) {
        # sets a named variable by key
        self.variables[key] = value;
    }

    can variable_del(key:str) {
        # completely removes the variable and value from frame
        if key in self.variables.keys() {
            del self.variables[key];
        }
    }

    can get_last_interaction() -> Interaction {
        # retrieves the last interaction in this frame
        if(result := [-:Tail:->](`?Interaction)) {
            return Utils.node_obj(result);
        }
        return None;
    }

    can is_first_interaction -> bool {
        # denotes the very first interaction of this frame
        last_interaction = self.get_last_interaction();
        return ("new_user" in last_interaction.context_data);
    }

    can set_resume_action(action_label:str) {
        # adds a named resume action node name to the context_data of the interaction
        # the interact walker will head straight here once it's turn comes back up
        if(last_interaction := self.get_last_interaction()) {
            last_interaction.context_data["resume_action"] = action_label;
        }
    }

    can get_resume_action(last_interaction_node: Interaction) -> InteractAction {
        # gets a named resume action node from the context_data of the interaction
        # the interact walker will head straight here once it's turn comes back up
        action_node = None;

        if(last_interaction_node) {
            if("resume_action" in last_interaction_node.context_data) {
                agent_node = self.get_agent();
                action_label = last_interaction_node.context_data["resume_action"];
                action_node = agent_node.get_actions().get(action_label = action_label);
            }
        }

        return action_node;
    }

    can add_interaction(utterance:str, channel:str='default') -> Interaction {
        # adds new prompted interaction to the end of the frame and sets the channel

        last_interaction_node = self.get_last_interaction();

        interaction_node = Interaction(
            agent_id=self.agent_id,
            channel=channel,
            utterance=utterance,
            response = InteractionResponse(session_id=self.session_id).export()
        );

        return self.insert_interaction(interaction_node, last_interaction_node);
    }


    can add_unprompted_interaction(message:str, channel:str='default') -> Interaction {
        # adds new unprompted interaction to the end of the frame and sets the channel
        # these are interactions which are sent by AI without human utterance or from humans intervening
        # mainly for inserting items into the message history

        last_interaction_node = self.get_last_interaction();

        interaction_node = Interaction(
            agent_id=self.agent_id,
            channel=channel,
            response=InteractionResponse(
                session_id=self.session_id,
                message=TextInteractionMessage(content=message).export()
            ).export()
        );

        return self.insert_interaction(interaction_node, last_interaction_node);
    }

    can insert_interaction(interaction_node:Interaction, last_interaction_node:Interaction=None) -> Interaction {
        # inserts an interaction node with reference to the last interaction node, if any

        if (not last_interaction_node and not [-:Advance:->]) {

            # if there is no interaction from the root frame, attach the first one
            self +:Advance:+> interaction_node;
            self <+:Retrace:+ interaction_node;
            # add a tail reference
            self +:Tail:+> interaction_node;
            # this is a first-time interaction, add the new_user flag
            interaction_node.context_data["new_user"] = True;

        } else {

            # if there is an interaction, let's attach a fresh one at the end of the last_interaction_node...
            # remove the tail edge, if it exists
            if ([-:Tail:->]) {
                # remove the tail to the old last interaction
                self del-:Tail:-> [-:Tail:->];
                # add the tail to the new interaction
                self +:Tail:+> interaction_node;
                # attach the new interaction_node to the last interaction
                last_interaction_node.attach_interaction(interaction_node);
            }
        }

        return interaction_node;
    }

    can get_transcript_statements(interactions:int = 10, max_statement_length:int = 0, with_events:bool = False) -> list[dict] {
        # returns the transcript of the last specified number of interactions as a list
        return (self spawn _get_transcript_statements(interactions, max_statement_length, with_events=with_events)).statements;
    }

    can get_transcript(interactions:int = 10, max_statement_length:int = 0, with_events:bool = False) -> str {
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

    can get_interactions() -> list {
        return (self spawn _get_interactions()).interactions;
    }

    can get_agent() {
        return &self.agent_id;
    }

    can prune_interactions(frame_size:int) {
        # prunes the given frame of interaction nodes by the specified amount.
        # operation will leave 'frame_size' nodes or less in the frame and remove all older nodes
        self spawn _prune_interactions(frame_size=frame_size);
    }

    can refresh_interactions() {
        # prunes the given frame of interaction nodes down to 1.
        self.prune_interactions(frame_size=1);
    }

    can get_user_name(full:bool=False) {
        # returns a set user name or default if not set

        if(self.user_name and full) {
            return self.user_name;
        } elif(self.user_name) {
            return Utils.extract_first_name(self.user_name);
        } else {
            return "user";
        }
    }

    can set_user_name(user_name:str) {
        # sets user name for this session
        if user_name {
            self.user_name = user_name;
        }
    }
}

walker _get_transcript_statements {
    # returns the transcript of the last specified number of interactions as a list

    has interactions:int = 1;
    has max_statement_length:int = 0;

    has statements:list = [];
    has last_interaction:Interaction = None;
    has retrace_count:int = 0;
    has with_events:bool = False;

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_frame with Frame entry {
        last_interaction = here.get_last_interaction();
        visit last_interaction;
    }

    can on_interaction with Interaction entry {
        # if we're at the last interaction, retrace
        if (here == self.last_interaction) {
            visit [-:Retrace:->](`?Interaction) else {
                disengage;
            }
        } elif (self.retrace_count < self.interactions) {

            ai_statement = "";
            human_statement = "";

            # add events to the transcript
            if (here.events and self.with_events) {
                for event in here.events {
                    self.statements.append({"ai": f"event: {event}"});
                }
            }

            if (here.has_response()) {
                content = here.get_message().get_content();
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

            if (here.utterance) {
                human_statement = Utils.escape_string(here.utterance);
                human_statement = self.chunk_message(message=human_statement);
                self.statements.append({"human": human_statement});
            }

            self.retrace_count += 1;
            visit [-:Retrace:->](`?Interaction);
        }

    }

    can chunk_message(message:str) -> str {
        if(self.max_statement_length > 0){
            message_chunks = Utils.chunk_long_message(message=message, max_length=self.max_statement_length, chunk_length=self.max_statement_length);
            if (len(message_chunks) > 1) {
                message = message_chunks[0];
            }
        }

        return message;
    }

    can on_exit with exit {
        (self.statements).reverse();
    }
}

walker _get_interactions {
    # returns the list of interactions of a frame.
    has interactions:list = [];

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_frame with Frame entry {
        visit [-:Advance:->](`?Interaction);
    }

    can on_interaction with Interaction entry {
        self.interactions.append(here);
        visit [-:Advance:->](`?Interaction);
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

        if (self.interaction_head) {
            here +:Advance:+> self.interaction_head;
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
        if ((self.retraces == self.frame_size) and ([-:Retrace:->](`?Interaction))) {
            # make a note of the new interaction head node
            self.interaction_head = here;
            # set a course to continue upwards in the chain, deleting old interactions as we go..
            visit [-:Retrace:->](`?Interaction);
            # now, remove the retrace edge to the node before it
            here del--> [-:Retrace:->](`?Interaction);
            # add a new retrace edge to the frame node from here so it doesnt orphan the rest of the chain..
            if (not [-:Retrace:->](`?Frame)) {
                here +:Retrace:+> self.frame_node;
            }

        } elif (self.retraces > self.frame_size) {
            # if we're here, it means we are in pruning mode
            visit [-:Retrace:->](`?Interaction) else {
                del here;
            }
        } else {
            visit [-:Retrace:->](`?Interaction);
        }
    }

}
