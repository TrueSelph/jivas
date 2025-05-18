import:py logging;
import:py traceback;
import:py from typing { Optional }
import:py from logging { Logger }
import:jac from jivas.agent.action.action { Action }
import:py from jivas.agent.modules.agentlib.utils { Utils }

node ModelAction :Action: {
    # Generic model action node architype for abstracted, standardized LLM interfacing

    # set up logger
    static has logger: Logger = logging.getLogger(__name__);

    has api_key: str = "";
    has model_name: str = "gpt-4o";
    has model_temperature: float = 0.7;
    has model_max_tokens: int = 2048;

    # abstract invoke ability for the model meant to be overidden with specifics of model call
    can invoke(prompt_messages: list, prompt_variables: dict, kwargs: dict={}) -> Optional[ModelActionResult] abs;

    can call_model(
        prompt_messages: list,
        prompt_variables: dict,
        interaction_node: Optional[Interaction]=None,
        logging: bool=False,
        streaming: bool=False,
        kwargs: dict={}
    ) -> Optional[ModelActionResult] {

        # add streaming flag in kwargs
        kwargs.update({"streaming":streaming});

        if (model_action_result := self.invoke(
            prompt_messages,
            prompt_variables,
            kwargs
        )) {
            if (interaction_node) {
                # add exported model action result to context data
                if ('ModelActionResult' not in interaction_node.context_data) {
                    interaction_node.context_data['ModelActionResult'] = [];
                }
                interaction_node.context_data['ModelActionResult'].append(
                    model_action_result.export()
                );
                # update token tally
                interaction_node.add_tokens(
                    model_action_result.get_tokens()
                );
            }
            if (logging) {
                self.logger.warning(model_action_result.get_result());
            }

            return model_action_result;
        }

        return None;
    }

    can healthcheck() -> Union[bool, dict] {
        if (self.model_name == "" or self.api_key == "") {
            return False;
        }

        test_prompt_messages = [{"system": "Output the result of 2 + 2"}];
        test_kwargs = {
            "model_name": self.model_name,
            "model_temperature": self.model_temperature,
            "model_max_tokens": self.model_max_tokens
        };
        try  {
            if (model_action_result := self.call_model(
                prompt_messages=test_prompt_messages,
                prompt_variables={},
                kwargs=test_kwargs
            )) { # set the interaction message+


            interaction_message = model_action_result.get_result();
            if not interaction_message {
                return False;
            } else {
                return True;
            }
            }
            return False;
        } except Exception as e {
            self.logger.error(
                f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n"
            );
            return False;
        }
    }

}

obj ModelActionResult {

    # encapsulates a language model prompt, result and related tokens
    # this is meant to be instantiated with attr values and serve as the standard when interfacing with llms asyncronously

    has prompt: str = "";
    has functions: str = "";
    has result: str = "";
    has generator: any = None;
    has tokens: int = 0;
    has temperature: float = 0;
    has model_name: str = "";
    has max_tokens: int = 0;
    has meta: dict = {};

    can get_prompt() {
        return self.prompt;
    }

    can get_functions() {
        return self.functions;
    }

    can get_result() {

        if (self.result) {
            return self.result;
        } else {
            return None;
        }

    }

    can get_json_result() {
        #  convert result to json and return it
        if (json_result := Utils.convert_str_to_json(self.result)) {
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

    can get_generator() {
        return self.generator;
    }

    can export(ignore_keys: list=['__jac__']) {
        # convert the object to dictionary
        node_export = Utils.export_to_dict(self, ignore_keys);
        return node_export;
    }
}
