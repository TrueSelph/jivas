import from datetime { datetime, timezone }
import from jivas.agent.modules.agentlib.utils { Utils }
import from jivas.agent.memory.data { Data }
import from jivas.agent.memory.advance { Advance }
import from jivas.agent.memory.retrace { Retrace }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.memory.interaction_response { InteractionMessage, InteractionResponse, TextInteractionMessage }

node Interaction(GraphNode) {

    has :priv agent_id: str = "";
    has :priv channel: str = "";
    has :priv utterance: str = "";
    has :priv tokens: int = 0;
    has :priv time_stamp: str = str((datetime.now(timezone.utc)).isoformat());
    has :priv trail: list = [];
    has :priv intents: list = []; # TODO: make this private; this holds the node names of actions which must be executed; capable of multiple intent executions...
    has :priv functions: dict = {}; # holds the intended action as the key and classified tool calls as values
    has :priv directives: list = []; # TODO: make this private; holds queued directives for from interact_actions
    has :priv events: list = [];
    has :priv response: InteractionResponse = None;
    has :priv data: dict = {}; # holds data items which are not part of the response, but are relevant to the interaction
    has :priv closed: bool = False; # flag to determine whether interaction is complete / closed or not

    def postinit {
        super.postinit();
        # add of node attributes which are protected from update operation
        self.protected_attrs += ['agent_id'];
    }

    def attach_interaction(interaction_node: Interaction) {
        # attaches a new interaction node to this one
        self +>:Advance:+> interaction_node;
        self <+:Retrace:<+ interaction_node;
    }

    def is_new_user() -> bool {
        return (self.get_data_item('new_user') is not None);
    }

    def set_text_message(message: str) {
        self.set_message(TextInteractionMessage(content=message));
    }

    def set_message(message: InteractionMessage) {
        # set the interaction response message object
        self.get_response().set_message(message);
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

    def has_response -> bool {
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

    def set_data_item(label: str, content: any, meta: dict = {}) {
        # adds or updates a data item on the current interaction
        if (data_obj := self.get_data_item(label)) {
            if (type(meta) == dict) {
                data_obj.meta = meta;
            }
            if (content) {
                data_obj.content = content;
            }
            self.data[label] = data_obj;
        } else {
            data_obj = Data(label=label, meta=meta, content=content);
            self.data[label] = data_obj;
        }
    }

    def append_data_item(label: str, content: any, meta: dict = {}) {
        # appends a content item to an existing data item
        if (data_item := self.get_data_item(label)) {
            if (type(meta) == dict) {
                data_item.meta.update(meta);
            }
            if (content) {
                if (type(data_item.content) == list) {
                    data_item.content.append(content);
                } else {
                    data_item.content = [data_item.content, content];
                }
            }
            self.data[label] = data_item;
        } else {
            self.set_data_item(label, content, meta);
        }
    }

    def get_data_item(label: str) -> Data {
        # retrieves a data item of the current interaction
        if (data_item := self.data.get(label)) {
            return data_item;
        }

        return None;
    }

    def get_data_items() -> list {
        # retrieves all data items belonging to the current interaction
        return self.data;
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

    def get_functions(action_label: str) -> list {
        return self.functions.get(action_label, []);
    }

    def is_closed() -> bool {
        return self.closed;
    }

    def close() {
        self.closed = True;
    }

}
