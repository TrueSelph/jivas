import from enum { unique }
import:jac from interact_action { InteractAction }
import:jac from interact_graph_walker { interact_graph_walker }
import:py from jivas.agent.modules.agentlib.openai_function_generator { OpenAIFunctionGenerator }

node InterviewInteractAction :InteractAction: {
    #*
    * represents a multiturn interactive execution on the agent action graph
    * designed to allow implementors to specify a sequence of required and non-required fields
    * for extracting from the user while maintaining session tracking for the multiturn conversation extractions
    *#

    has model_action: str = "LangChainModelAction";
    has model_name: str = "gpt-4o";
    has model_max_tokens:int = 4096;
    has model_temperature: float = 0.1;

    has history: bool = True;
    has history_size: int = 3;
    has max_statement_length: int = 500;

    has question_directive:str = "Ask the question: '{question}'.";
    has insist_response_directive:str = "Insist that a response is required then ask the question: '{question}'.";
    has insist_format_directive:str = "Insist that a response following this format ({format}) is required then ask the question: '{question}'.";
    has confirmation_directive: str = "Ask the user to confirm that the information captured is correct.";
    has auto_intents:bool = True;
    has auto_functions:bool = True;
    has question_functions:list = [];
    has confirm_function:dict = {
        "type": "function",
        "function": {
            "name": "extract_confirmation_choice",
            "description": "Analyzes user responses to determine explicit confirmation. Handles all affirmative (yes/yeah/yep/sure) and negative (no/nope/nah) variations, including those with punctuation or capitalization. Returns false for ambiguous, neutral, or non-committal responses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "boolean",
                        "description": "True only for explicit affirmations. False for explicit rejections, uncertain responses, or any message not clearly confirming."
                    }
                },
                "required": ["response"]
            }
        }
    };
    has abort_function:dict = {
        "type": "function",
        "function": {
            "name": "extract_abort_choice",
            "description": "Identifies explicit user requests to terminate the ongoing interaction. Recognizes direct termination commands ('stop', 'cancel', 'abort'), procedural phrases ('end conversation', 'exit chat'), and common colloquialisms ('nevermind', 'scratch that'). Handles capitalization variations and punctuation. Returns false for ambiguous statements, in-context cancellation requests (e.g., cancel subscription), or continuation attempts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "boolean",
                        "description": "True only for clear termination attempts targeting the conversation itself. False for indirect statements ('I need to go'), ambiguous phrases ('maybe later'), or cancellation references to external entities."
                    }
                },
                "required": ["response"]
            }
        }
    };
    has decline_function:dict = {
        "type": "function",
        "function": {
            "name": "extract_decline_choice",
            "description": "Detects when a user declines to answer, expresses uncertainty, provides no response, or indicates they have nothing to submit for the current question. Recognizes explicit refusals (e.g., 'I decline to answer', 'no comment', 'I'd rather not say'), uncertainty ('not sure', 'I don't know', 'unsure'), requests to skip ('skip', 'next question', 'can we move on'), statements indicating lack of information ('I have no idea', 'no response', 'nothing to add'), and cases where the user states they have nothing to submit (e.g., 'I don't have any', 'no documents to provide', 'nothing to share for this'). Handles variations in phrasing, capitalization, and punctuation. Returns true for any clear or ambiguous indication that the user cannot, will not, or has nothing to provide in response, including silence or non-committal responses. Returns false for direct answers or attempts to engage with the question.",
            "parameters": {
            "type": "object",
            "properties": {
                "response": {
                "type": "boolean",
                "description": "True if the user clearly or ambiguously declines, skips, cannot answer, or indicates they have nothing to submit for the question. False if the user provides a direct answer or attempts to answer."
                }
            },
            "required": ["response"]
            }
        }
    };
    has question_index:dict = {};

    can setup() {
        if self.auto_functions {
            self.generate_functions();
        }
        if self.auto_intents {
            self.generate_intents();
        }
    }

    can on_register() {
        self.setup();
    }

    can post_update() {
        self.setup();
    }

    can touch(visitor: interact_graph_walker) -> bool {
        has_intent = False;
        if(self.get_agent().get_action("IntentInteractAction")) {
            has_intent = (self.label in visitor.interaction_node.intents);
        } else {
            has_intent = True;
        }
        return (has_intent and (visitor.utterance or visitor.data));
    }

    can execute(visitor: interact_graph_walker) -> dict {
        # initializes the session and calls the process response ability, then exports the visitor obj
        visitor = self.init_session(visitor);
        # call process_response which needs to be implemented
        _visitor = self.process_response(visitor);
        if _visitor and isinstance(_visitor, interact_graph_walker) {
            visitor = _visitor;
        }
        # call exit session for cleanup
        visitor = self.exit_session(visitor);
        return visitor.export();
    }

    # abstract ability meant to contain handling logic for based on the extracted interview data
    can process_response(visitor: interact_graph_walker) -> interact_graph_walker abs;

    can exit_session(visitor: interact_graph_walker) -> interact_graph_walker {
        # handles removal of completed session data once process_response runs
        interview_session = self.get_session(visitor);

        if not interview_session {
            return visitor;
        }
        # remove session if previously ABORTED or CONFIRMED
        if interview_session.get_state() in [SessionState.ABORTED, SessionState.CONFIRMED] {
            visitor = self.delete_session(visitor);
        }

        return visitor;
    }

    can healthcheck() -> Union[bool, dict] {
        valid_question_index = True;
        if isinstance(self.question_index, dict) {
            for (key, question_info) in self.question_index.items() {
                if not isinstance(question_info, dict) or "question" not in question_info or "extraction_guidance" not in question_info {
                    valid_question_index = False;
                    break;
                }
                eg = question_info["extraction_guidance"];
                if not isinstance(eg, dict) {
                    valid_question_index = False;
                    break;
                }
                # description: str, type: str, required: bool
                if "description" not in eg or not isinstance(eg["description"], str) {
                    valid_question_index = False;
                    break;
                }
                if "type" not in eg or not isinstance(eg["type"], str) {
                    valid_question_index = False;
                    break;
                }
                if "required" not in eg or not isinstance(eg["required"], bool) {
                    valid_question_index = False;
                    break;
                }
            }
        } else {
            valid_question_index = False;
        }
        if not valid_question_index {
            return {
                "status": False,
                "message": "Malformed question index. Check your configuration and try again",
                "severity": "error"
            };
        }
        return True;
    }

    can generate_intents() {
        # generates a list of formatted intents based on question index and sets them to self.intents
        intents = [];
        if not isinstance(self.question_index, dict) {
            return [];
        }

        # prepare consolidated list of functions
        functions = [
            self.confirm_function,
            self.abort_function,
            self.decline_function
        ];
        functions.extend(self.question_functions);


        for function in functions {
            description = function.get('function', {}).get('description', '');
            # Compose a simple intent statement
            intent = f"MESSAGE {description}";
            intents.append(intent);
        }
        self.anchors = intents;
    }

    can generate_functions() -> list {
         # converts the question index items to functions in order to perform extraction
        generator = OpenAIFunctionGenerator(self.question_index);
        self.question_functions = generator.generate_openai_functions();
    }

    can create_session(visitor: interact_graph_walker) -> interact_graph_walker {
        # adds a new interview session to the frame for the current user
        all_fields = self.get_question_fields();
        required_fields = [key for key in all_fields if self.question_index[key]["extraction_guidance"].get("required", False)];
        interview_session = InterviewSession(all_fields=all_fields, required_fields=required_fields);
        interview_session.get_next_field(); # initialize active field
        visitor.frame_node.variable_set(key=f"{self.get_type()}_session", value=interview_session.export());

        return visitor;
    }

    can delete_session(visitor: interact_graph_walker) -> interact_graph_walker {
        # removes the session object from the current user's frame
        visitor.frame_node.variable_del(key=f"{self.get_type()}_session");

        return visitor;
    }

    can update_session(session_data:dict, visitor: interact_graph_walker) -> interact_graph_walker {
        # updates interview session for the current user
        visitor.frame_node.variable_set(key=f"{self.get_type()}_session", value=session_data);

        return visitor;
    }

    can get_question_fields() -> dict {
        # returns the list of question fields (keys)
        return list(self.question_index.keys());
    }

    can get_next_question(interview_session: InterviewSession) -> str {
        # returns the next question based on the state of the session, or None if no more
        field = interview_session.get_next_field();
        return self.question_index.get(field, {}).get('question', "");
    }

    can get_next_question_directive(interview_session: InterviewSession) -> str {
        # composes the next question directive based on the next question
        return self.question_directive.format(question=self.get_next_question(interview_session)) if (next_question := self.get_next_question(interview_session)) else "";
    }

    can filter_question_functions(interview_session: InterviewSession) -> list {
        # reutrns a list of question functions which are applicable to the session state and remaining fields

        # cater to OPEN state
        if interview_session.get_state() == SessionState.OPEN {
            filtered_functions = [];
            # return the question functions based on
            unanswered_fields = interview_session.get_unanswered_fields();

            for function in self.question_functions {
                field = function.get('function', {}).get('name');
                if(field in unanswered_fields) {
                    filtered_functions.append(function);
                }
            }

            return filtered_functions;
        }

        # return all question functions by default
        return self.question_functions;
    }

    can get_session(visitor:interact_graph_walker) -> InterviewSession {
        # retrieves the active session, if any
        interview_session_data = visitor.frame_node.variable_get(key=f"{self.get_type()}_session");
        if interview_session_data and isinstance(interview_session_data, dict) {

            # load session state, if any
            state = interview_session_data.get('state', 'OPEN');
            session_state = SessionState.OPEN;
            # interpret and assign SessionState
            if (state == SessionState.READY.value) {
                session_state = SessionState.READY;
            } elif (state == SessionState.COMPLETED.value) {
                session_state = SessionState.COMPLETED;
            } elif (state == SessionState.CONFIRMED.value) {
                session_state = SessionState.CONFIRMED;
            } elif (state == SessionState.REVISION.value) {
                session_state = SessionState.REVISION;
            } elif (state == SessionState.ABORTED.value) {
                session_state = SessionState.ABORTED;
            } else {
                session_state = SessionState.OPEN;
            }

            # return session object
            return InterviewSession(
                state=session_state,
                all_fields=interview_session_data.get('all_fields', []),
                required_fields=interview_session_data.get('required_fields', []),
                active_field=interview_session_data.get('active_field', ''),
                responses=interview_session_data.get('responses', {})
            );
        }

        return None;
    }

    can init_session(visitor: interact_graph_walker) -> interact_graph_walker {
        # performs extraction and updates the session responses
        interview_session = self.get_session(visitor);

        # Create new session if none exists
        if not interview_session {
            visitor = self.create_session(visitor);
            interview_session = self.get_session(visitor);
        }

        # Check for abort response
        abort_response = self.extract([self.abort_function], visitor);
        if abort_response.get('extract_abort_choice', False) {
            interview_session.set_state(SessionState.ABORTED);
            visitor = self.update_session(interview_session.export(), visitor);
            return visitor;
        }

        # Check for decline-to-answer response
        decline_response = self.extract([self.decline_function], visitor);
        if decline_response.get('extract_decline_choice', False) {

            # get field status - required or not
            if interview_session.on_required_field() {

                # insist that user must answer
                insist_directive = self.insist_response_directive.format(question=self.get_next_question(interview_session));
                visitor.interaction_node.add_directive(directive=insist_directive);
                visitor = self.update_session(interview_session.export(), visitor);
                return visitor;

            } else {
                # apply 'n/a' to field response
                field = interview_session.get_next_field();
                self.logger.error(f'required field {field}');
                question_response = {field : "declined to answer"};
                interview_session = self.update_responses(question_response, interview_session);
                visitor = self.update_session(interview_session.export(), visitor);

                # if no more fields and we have an extraction, set to completed for confirmation
                if not interview_session.get_next_field() {
                    # new_state = SessionState.READY if interview_session.has_ignored_responses() else SessionState.COMPLETED;
                    interview_session.set_state(SessionState.COMPLETED);
                    visitor = self.update_session(interview_session.export(), visitor);
                }

                return visitor;
            }

        }

        # Handle confirmation for COMPLETED or READY states
        if interview_session.get_state() in [SessionState.COMPLETED, SessionState.READY] {
            confirmation_response = self.extract([self.confirm_function], visitor);
            confirmed = confirmation_response.get('extract_confirmation_choice', None);

            if confirmed is True {

                interview_session.set_state(SessionState.CONFIRMED);
                visitor = self.update_session(interview_session.export(), visitor);

            } elif confirmed is False {

                interview_session.set_state(SessionState.REVISION);
                visitor = self.update_session(interview_session.export(), visitor);

            }

            return visitor;
        }

        # Process OPEN or REVISION states
        if interview_session.get_state() in [SessionState.OPEN, SessionState.REVISION] {

            question_functions = self.filter_question_functions(interview_session);
            question_responses = self.extract(question_functions, visitor);
            interview_session = self.update_responses(question_responses, interview_session);
            visitor = self.update_session(interview_session.export(), visitor);

            # if no more fields and we have an extraction, set to completed for confirmation
            if not interview_session.get_next_field() {
                # new_state = SessionState.READY if interview_session.has_ignored_responses() else SessionState.COMPLETED;
                interview_session.set_state(SessionState.COMPLETED);
                visitor = self.update_session(interview_session.export(), visitor);
                return visitor;
            }
        }

        return visitor;
    }

    can extract(functions:list, visitor: interact_graph_walker) -> dict {
        # performs function tool calling for extracting question responses based on question

        prompt_messages = [];

        if not functions {
            return {};
        }

        if self.history {
            statements = visitor.frame_node.get_transcript_statements(interactions=self.history_size, max_statement_length=self.max_statement_length);
            prompt_messages.extend(statements or []);
        } else {
            prompt_messages.append({"human": visitor.utterance});
        }

        model_action = self.get_agent().get_action(action_label=self.model_action);
        if model_action {
            model_action_result = model_action.call_model(
                prompt_messages=prompt_messages,
                prompt_variables={},
                kwargs={
                    "functions": functions,
                    "model_name": self.model_name,
                    "model_temperature": self.model_temperature,
                    "model_max_tokens": self.model_max_tokens
                },
                interaction_node=visitor.interaction_node
            );

            if model_action_result {
                tools = model_action_result.get_result();

                if type(tools) == list {
                    responses = {};
                    for item in tools {
                        name = item.get('name');
                        args = item.get('args', {});
                        response = args.get('response');
                        responses[name] = response;
                    }
                    return responses;
                } else {
                    return {};
                }
            }
        }

        return {};
    }

    can update_responses(responses:dict, interview_session:InterviewSession) -> InterviewSession {
        for (field, response) in responses.items() {
            if field and response {
                interview_session.set_response(field, response);
            }
        }
        return interview_session;
    }
}

@unique
enum SessionState {
    OPEN = 'OPEN', # session is open for extractions -> collect responses
    READY = 'READY', # all required responses have been collected, there are unrequired, ignored responses left; -> prompt to confirm
    COMPLETED = 'COMPLETED', # all responses have been collected -> prompt to confirm
    CONFIRMED = 'CONFIRMED', # user has confirmed all responses -> close the session
    REVISION = 'REVISION', # user has not confirmed responses -> prompt for review -> set to complete/ready
    ABORTED = 'ABORTED', # user has chosen to abandon the process -> remove the session
}

obj InterviewSession {
    has state:SessionState = SessionState.OPEN;
    has all_fields: list = [];
    has required_fields: list = [];
    has active_field: str = "";
    has responses: dict = {};

    can get_state() -> SessionState {
        return self.state;
    }

    can set_state(state:SessionState) {
        self.state = state;
    }

    can get_next_field() -> str {

        response_fields = self.responses.keys();

        for item in self.all_fields {
            if item not in response_fields {
                self.active_field = item;
                return item;
            }
        }

        return None;
    }

    can on_required_field() -> boolean {
        return (self.active_field in self.get_required_fields());
    }

    can get_answered_fields() -> list {
        return list(self.responses.keys()) or [];
    }

    can get_unanswered_fields() -> list {
        return [field for field in self.all_fields if field not in self.get_answered_fields()];
    }

    can get_required_fields() -> list {
        return self.required_fields;
    }

    can set_response(field: str, response: str) {
        self.responses[field] = response;
    }

    can export() -> dict {
        return {
            'state': self.state.value,
            'all_fields': self.all_fields,
            'required_fields': self.required_fields,
            'active_field': self.active_field,
            'responses': self.responses
        };
    }
}