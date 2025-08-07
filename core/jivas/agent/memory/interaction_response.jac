import from enum { unique }
import from typing { Any }


import from jivas.agent.core.graph_object { GraphObject }

@unique
enum MessageType {
    TEXT = 'TEXT',
    MEDIA = 'MEDIA',
    MULTI = 'MULTI',
    SILENCE = 'SILENCE'
}

obj InteractionMessage(GraphObject) {
    # abstract base class for interaction message
    has message_type:str = None;
    has content:Any=None;
    has mime:str = "";
    has data:Any = None;

    def get_type() -> str {
        return self.message_type;
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

}

obj SilentInteractionMessage(InteractionMessage) {
    has message_type:MessageType = MessageType.SILENCE.value;
    has content:str = "...";
}

obj TextInteractionMessage(InteractionMessage) {

    has message_type:MessageType = MessageType.TEXT.value;
    has content:str = "";
}

obj MediaInteractionMessage(InteractionMessage) {

    has message_type:MessageType = MessageType.MEDIA.value;
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

    has message_type:MessageType = MessageType.MULTI.value;
    has content:list[InteractionMessage] = [];

    def add_interaction_message(message:InteractionMessage) {
        if( not isinstance(message, MultiInteractionMessage) ) {
            self.content.append(message);
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
            content = f"{content} \n {content_item.get_content()}";
        }
        return content;
    }

    def get_content_items() {
        return self.content;
    }
}

obj InteractionResponse(GraphObject) {

    has session_id:str = "";
    has message_type:MessageType = MessageType.TEXT.value;
    has message:InteractionMessage = None;
    has tokens:int = 0;

    def set_message(message:InteractionMessage) {

        if(message) {
            self.message = message;
            # auto-update the type based on the type
            self.message_type = message.get_type();
        }

    }

    def set_tokens(tokens:int) {
        self.tokens = tokens;
    }

    def get_type() -> MessageType {
        return self.message_type;
    }

    def get_message() -> Union[InteractionMessage, None] {
        # loads an existing message object or returns None
        return self.message;
    }

}
