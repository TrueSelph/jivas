import from datetime { datetime, timezone }
import from jivas.agent.modules.system.common { node_obj }
import from jivas.agent.core.graph_object { GraphObject }
import from jivas.agent.memory.interaction_response { InteractionMessage, InteractionResponse, TextInteractionMessage }

obj Interaction(GraphObject) {
    # represents a single interaction with the agent

    has :priv agent_id: str = "";
    has :priv frame_id: str = "";
    has :priv channel: str = "";
    has :priv utterance: str = "";
    has :priv tokens: int = 0;
    has :priv time_stamp: str = str((datetime.now(timezone.utc)).isoformat());
    has :priv trail: list = [];
    has :priv intents: list = []; # this holds the node names of actions which must be executed; capable of multiple intent executions...
    has :priv functions: dict = {}; # holds the intended action as the key and classified tool calls as values
    has :priv directives: list = []; # holds queued directives for from interact_actions
    has :priv events: list = [];
    has :priv response: InteractionResponse = None;
    has :priv data: dict = {}; # holds data items which are not part of the response, but are relevant to the interaction
    has :priv closed: bool = False; # flag to determine whether interaction is complete / closed or not


    def is_new_user() -> bool {
        return (self.data_get('new_user') is not None);
    }

    def set_text_message(message: str) {
        self.set_message(TextInteractionMessage(content=message));
    }

    def set_message(message: InteractionMessage) {
        # set the interaction response message object
        self.get_response().set_message(message);
    }

    def get_utterance() -> str {
        # returns the utterance of the interaction
        return self.utterance;
    }

    def get_message() -> InteractionMessage {
        # get the interaction response message object
        if (response := self.get_response()) {
            return response.get_message();
        }
        return None;
    }

    def get_response() -> InteractionResponse {
        # loads an existing interaction response object or returns a fresh one
        if not self.response {
            self.response = InteractionResponse();
        }
        return self.response;
    }

    def has_response() -> bool {
        # evaluates whether the interaction holds a valid response
        if (self.get_message()) {
            return True;
        }
        return False;
    }

    def has_intent(intent: str) {
        # checks if intent exists in interaction
        return (intent in self.intents);
    }

    def add_directive(directive: str) {
        self.directives.append(directive);
    }

    def get_directives() -> list {
        return self.directives;
    }

    def add_intent(intent: str) {
        if (intent not in self.intents) {
            self.intents.append(intent);
        }
    }

    def add_event(event: str) {
        # adds a stated event to interaction
        self.events.append(event);
    }

    def get_events() -> list {
        return self.events;
    }

    def add_tokens(tokens: int) {
        # update token tally
        self.tokens += tokens;
        # update token tally in response obj
        self.get_response().set_tokens(self.tokens);
    }

    def get_intents() -> list {
        return self.intents;
    }

    def add_function(action_label: str, function: dict) {

        if (self.functions.get(action_label, None)) {
            self.functions[action_label].append(function);
        } else {
            self.functions[action_label] = [function];
            self.add_intent(action_label);
        }

    }

    def set_resume_action(action_label:str) {
        # adds a named resume action node name to the context_data of the interaction
        self.data_set(key="resume_action", value=action_label);
    }

    def get_resume_action() -> str {
        # gets the name of the resume action node from the context_data of the interaction
        return self.data_get("resume_action", None);
    }

    def get_functions(action_label: str) -> list {
        return self.functions.get(action_label, []);
    }

    def get_frame() -> GraphNode {
        return &self.frame_id;
    }

    def is_closed() -> bool {
        return self.closed;
    }

    def close() {
        self.closed = True;
    }

}