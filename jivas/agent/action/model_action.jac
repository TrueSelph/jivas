import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.action.action { Action }
import:py from jivas.agent.modules.agentlib.utils { Utils }

node ModelAction :Action: {
    # Generic model action node architype for abstracted, standardized LLM interfacing

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has api_key:str = "";
    has model_name:str = "gpt-4o";
    has model_temperature:float = 0.7;
    has model_max_tokens:int = 2048;

    # abstract invoke ability for the model meant to be overidden with specifics of model call
    can invoke(
        prompt_messages:list,
        prompt_variables:dict,
        kwargs:dict = {}
    ) -> ModelActionResult abs;

    can call_model(
        prompt_messages:list,
        prompt_variables:dict,
        kwargs:dict = {},
        interaction_node:Optional[Interaction]=None,
        logging:bool = False
    ) {
        if( model_action_result := self.invoke(
            prompt_messages,
            prompt_variables,
            kwargs
        )) {

            if(interaction_node) {
                # add exported model action result to context data
                if('ModelActionResult' not in interaction_node.context_data) {
                    interaction_node.context_data['ModelActionResult'] = [];
                }

                interaction_node.context_data['ModelActionResult'].append(model_action_result.export());
                # update token tally
                interaction_node.add_tokens(model_action_result.get_tokens());

            }

            if(logging) {
                self.logger.warning(model_action_result.get_result());
            }

            return model_action_result;
        }

        return None;
    }

}

obj ModelActionResult {

    # encapsulates a language model prompt, result and related tokens
    # this is meant to be instantiated with attr values and serve as the standard when interfacing with llms asyncronously

    has prompt:str = "";
    has functions:str = "";
    has result:str = "";
    has tokens:int = 0;
    has temperature:float = 0;
    has model_name:str = "";
    has max_tokens:int = 0;
    has meta:dict = {};

    can get_prompt() {
        return self.prompt;
    }

    can get_functions() {
        return self.functions;
    }

    can get_result() {

        if(self.result) {
            return self.result;
        } else {
            return None;
        }

    }

    can get_json_result() {
        #  convert result to json and return it
        if( json_result := Utils.convert_str_to_json(self.result)) {
            return json_result;
        } else {
            return {};
        }
    }

    can get_tokens() {
        return self.tokens;
    }

    can get_max_tokens() {
        return self.max_tokens;
    }

    can get_temperature() {
        return self.temperature;
    }

    can get_model_name() {
        return self.model_name;
    }

    can get_meta() {
        return self.meta;
    }

    can export(ignore_keys: list = ['__jac__']) {
        # convert the object to dictionary
        node_export = Utils.export_to_dict(self, ignore_keys);
        return node_export;
    }
}