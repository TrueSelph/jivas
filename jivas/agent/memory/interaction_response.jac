import from enum { unique }
import from typing { Any }
import from jivas.agent.modules.agentlib.utils { Utils }

@unique
enum MessageType {
    TEXT = 'TEXT',
    MEDIA = 'MEDIA',
    MULTI = 'MULTI',
    SILENCE = 'SILENCE'
}

obj InteractionMessage {
    # abstract base class for interaction message
    has message_type:str = None;
    has content:Any=None;
    has meta:dict = {};

    def load(data:dict) {
        # loads a compatible interaction message data struct
        if (data and isinstance(data, dict)) {
            for attr in data.keys() {
                # set if attribute is a valid attribute
                if (hasattr(self, attr)) {
                    setattr(self, attr, data[attr]);
                }
            }
        }
    }

    def get_type() -> str {
        return self.message_type;
    }

    def set_meta(key:str, value: any) {
        self.meta[key] = value;
    }

    def get_meta(key:str) {
        return self.meta.get(key, None);
    }

    def get_content() {
        return self.content;
    }

    def has_content() -> bool {
        # abstract has content check
        if self.content {
            return True;
        }
        return False;
    }

    def export(ignore_keys: list = ['__jac__']) {
        # convert the object to dictionary
        node_export = Utils.export_to_dict(self, ignore_keys);
        return node_export;
    }
}

obj SilentInteractionMessage(InteractionMessage) {
    has message_type:str = MessageType.SILENCE.value;
    has content:str = "...";
}

obj TextInteractionMessage(InteractionMessage) {

    has message_type:str = MessageType.TEXT.value;
    has content:str = "";
}

obj MediaInteractionMessage(InteractionMessage) {

    has message_type:str = MessageType.MEDIA.value;
    has mime:str = "";
    has data:Any = None;
    has content:str = "";

    def has_content() -> bool {
        # content check
        if self.data {
            return True;
        }
        return False;
    }
}

obj MultiInteractionMessage(InteractionMessage) {

    has message_type:str = MessageType.MULTI.value;
    has content:list[dict] = [];

    def load(data:dict) {
        # loads a compatible interaction message data struct
        if (data) {
            for attr in data.keys() {
                # set if attribute is a valid attribute
                if (hasattr(self, attr)) {
                    setattr(self, attr, data[attr]);
                }
            }
        }
    }

    def add_interaction_message(message:InteractionMessage) {
        if( not isinstance(message, MultiInteractionMessage) ) {
            self.content.append(message.export());
        }
    }

    def clear_interaction_messages() {
        self.content = [];
    }

    def has_content() -> bool {
        # abstract has content check
        if type(self.content) == list {
            if len(self.content) > 0 {
                return True;
            }
        }
        return False;
    }

    def get_content() {
        content = "";
        for content_item in self.content {
            content = f"{content} \n {content_item.get('content')}";
        }
        return content;
    }

    def get_content_items() {

        content_items = [];

        if(self.content) {
            # for each item, instantiate the message object based on the set type
            for content_item in self.content {

                message = SilentInteractionMessage();

                if(content_item.get('message_type') == MessageType.MULTI.value) {
                    message = MultiInteractionMessage();
                } elif (content_item.get('message_type') == MessageType.MEDIA.value) {
                    message = MediaInteractionMessage();
                } elif (content_item.get('message_type') == MessageType.TEXT.value) {
                    message = TextInteractionMessage();
                }

                message.load(content_item);
                content_items.append(message);
            }
        }

        return content_items;
    }
}

obj InteractionResponse {

    has session_id:str = "";
    has message_type:str = MessageType.TEXT.value;
    has message:dict = {};
    has tokens:int = 0;

    def load(data:dict) {
        # loads a compatible interaction response data struct
        if (data) {
            for attr in data.keys() {
                # set if attribute is a valid attribute
                if (hasattr(self, attr)) {
                    setattr(self, attr, data[attr]);
                }
            }
        }
    }

    def set_message(message:InteractionMessage) {

        if(message) {
            self.message = message.export();
            # auto-update the type based on the type
            self.message_type = message.get_type();
        }

    }

    def set_tokens(tokens:int) {
        self.tokens = tokens;
    }

    def get_type() {
        return self.message_type;
    }

    def get_message() -> InteractionMessage {

        # loads an existing message object or returns None
        message = None;

        if(self.message) {
            # instantiate the message object based on the set type
            if(self.message_type == MessageType.MULTI.value) {
                message = MultiInteractionMessage();
            } elif (self.message_type == MessageType.MEDIA.value) {
                message = MediaInteractionMessage();
            } elif (self.message_type == MessageType.TEXT.value) {
                message = TextInteractionMessage();
            } else {
                message = SilentInteractionMessage();
            }

            message.load(self.message);
        }

        return message;
    }

    def export(ignore_keys: list = ['__jac__']) {
        # convert the object to dictionary
        node_export = Utils.export_to_dict(self, ignore_keys);
        return node_export;
    }
}
