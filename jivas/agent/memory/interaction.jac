import from datetime { datetime, timezone }
import from jivas.agent.modules.agentlib.utils { Utils }
import from jivas.agent.memory.data { Data }
import from jivas.agent.memory.advance { Advance }
import from jivas.agent.memory.retrace { Retrace }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.memory.interaction_response { InteractionMessage, InteractionResponse, TextInteractionMessage }

node Interaction(GraphNode) {

    has agent_id: str = "";
    has channel: str = "";
    has utterance: str = "";
    has tokens: int = 0;
    has time_stamp: str = str((datetime.now(timezone.utc)).isoformat());
    has trail: list = [];
    has intents: list = []; # TODO: make this private; this holds the node names of actions which must be executed; capable of multiple intent executions...
    has functions: dict = {}; # holds the intended action as the key and classified tool calls as values
    has directives: list = []; # TODO: make this private; holds queued directives for from interact_actions
    has context_data: dict = {};
    has events: list = [];
    has response: dict = {};
    has data: dict = {};
    has closed: bool = False; # flag to determine whether interaction is complete / closed or not
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
        return self.context_data.get('new_user', False);
    }

    def set_text_message(message: str) {
        self.set_message(TextInteractionMessage(content=message));
    }

    def set_message(message: InteractionMessage) {
        # set the interaction response message object
        # loads an existing interaction response object or returns a fresh one

        interaction_response = self.get_response() or InteractionResponse();
        interaction_response.set_message(message);
        self.response = interaction_response.export();
    }

    def get_message() -> InteractionMessage {
        # get the interaction response message object
        if (interaction_response := self.get_response()) {
            return interaction_response.get_message();
        }

        return None;
    }

    def get_response() -> InteractionResponse {
        # loads an existing interaction response object or returns a fresh one
        interaction_response = None;
        if (self.response) {
            interaction_response = InteractionResponse();
            interaction_response.load(self.response);
        }

        return interaction_response;
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

    def set_data_item(label: str, meta: dict, content: any) {
        # adds or updates a data node on the current interaction
        if (data_obj := self.get_data_item(label)) {
            if (type(meta) == dict) {
                data_obj.meta = meta;
            }
            if (content) {
                data_obj.content = content;
            }
            self.data[label] = data_obj.export();
        } else {
            data_obj = Data(label=label, meta=meta, content=content);
            self.data[label] = data_obj.export();
        }
    }

    def get_data_item(label: str) -> Data {
        # retrieves a data item of the current interaction
        if (data_item := self.data.get(label)) {
            data_obj = Data();
            data_obj.load(data_item);
            return data_obj;
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
        if (response := self.get_response()) {
            response.set_tokens(self.tokens);
            self.response = response.export();
        }
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
