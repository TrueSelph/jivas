import:py json;
import from enum { unique }
import:py from openai { OpenAI }
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
    has model_temperature: float = 0.0;

    has history: bool = True;
    has history_size: int = 1;
    has max_statement_length: int = 2048;

    has question_directive:str = "Ask the question: '{question}'.";
    has insist_response_directive:str = "Insist that a response is required then ask the question: '{question}'.";
    has insist_format_directive:str = "Insist that a response following this format ({format}) is required then ask the question: '{question}'.";
    has confirmation_directive: str = "Ask the user to confirm that the information captured is correct.";
    has revision_directive: str = "Encourage the user to suggest any changes to the information provided.";
    has auto_intents:bool = True;
    has auto_functions:bool = True;
    has auto_confirm:bool = False; # set True if you wish to skip the user confirmation step
    has question_functions:list = [];
    has branch_choice_prompt:str = """
        Analyze the conversation history above. Detect ONLY explicit signals for confirmation (yes/affirmative),
        conversation termination (abort/stop), decline-to-answer (no answer/can't respond), or upload completion.
        Follow these rules:

        # Confirmation Detection
        Set "confirm_response" to true for: "yes", "sure", "confirmed", "yeah", "yep", "absolutely", "okay" + clear context.
        Set "confirm_response" to false ONLY for explicit negative or revision signals, including:
            - Direct negatives: "no"
            - Revision or correction requests: "I'd like to make an adjustment", "need to make a change", "revision", "change my answer", "not correct", "incorrect", "needs update"
            - Suggestions to edit or change: phrases like "actually, please change...", "no, can you change...", "can you update...", "please edit...", "I'd like to change...", "can you correct...", "let's fix...", "could you modify...", or similar expressions indicating a desire to alter or correct previous information.
        Do NOT set "confirm_response" to false for ambiguous, neutral, or indirect responses.

        # Abort Detection
        Set "abort_response" to true for: "stop", "cancel", "exit", "end chat", "nevermind", "abort", "terminate".
        Do NOT include "abort_response" if not explicitly stated.

        # Decline Detection
        Set "decline_response" to true for: "no answer", "I don't know", "I have none", "no comment", "can't say", "nothing", "n/a", "decline to answer".
        Do NOT include "decline_response" for partial answers, topic changes, or ambiguous non-responses.

        # Upload Complete Detection
        Set "upload_complete_response" to true for explicit statements indicating the user has finished uploading all intended files, such as:
            - "I'm done", "upload complete", "done uploading", "finished uploading", "all files uploaded", "that's all the files", "I've uploaded everything", "finished with uploads", "done with uploads", "that's everything", "all done uploading", "uploads finished", "uploads are complete".
        Do NOT include "upload_complete_response" unless the user clearly indicates all uploads are finished.

        Return ONLY a JSON structure with a single detected key (confirm_response, abort_response, decline_response, or upload_complete_response) set to true,
        or "confirm_response" set to false if a negative/revision is detected. If nothing is detected, return an empty JSON object.
        Never include keys with false values except for "confirm_response" as described. No commentary. Never guess - ambiguous cases = empty JSON.
        """;
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

    can execute(visitor: interact_graph_walker) {
        # initializes the session and calls the process response ability, then exports the visitor obj
        interview_session = self.init_session(visitor);
        # call process_response which needs to be implemented
        self.process_response(interview_session, visitor);
        # call exit session for cleanup
        self.exit_session(interview_session, visitor);
    }

    # abstract ability meant to contain handling logic for based on the extracted interview data
    can process_response(visitor: interact_graph_walker) abs;

    can exit_session(interview_session: InterviewSession, visitor: interact_graph_walker) {

        # ensure we update the session in frame before export
        self.update_session(interview_session, visitor);
        # remove session if previously ABORTED or CONFIRMED
        if interview_session.get_state() in [SessionState.ABORTED, SessionState.CONFIRMED] {
            self.delete_session(visitor);
        }

    }

    can healthcheck() -> Union[bool, dict] {

        invalid_question_message = "";
        if isinstance(self.question_index, dict) {
            for (key, question_info) in self.question_index.items() {
                if not isinstance(question_info, dict) or "question" not in question_info or "extraction_guidance" not in question_info {
                    valid_question_index = False;
                    break;
                }
                eg = question_info["extraction_guidance"];
                if not isinstance(eg, dict) {
                    invalid_question_message = f"extraction_guidance must be a dictionary. Hint: {key}";
                    break;
                }
                # description: str, type: str, required: bool
                if "description" not in eg or not isinstance(eg["description"], str) {
                    invalid_question_message = f"description must be a string. Hint: {key}";
                    break;
                }
                if "type" not in eg or not isinstance(eg["type"], str) {
                    invalid_question_message = f"type must be a string. Hint: {key}";
                    break;
                }
                if "required" not in question_info or not isinstance(question_info["required"], bool) {
                    invalid_question_message = f"required must be a boolean. Hint: {key}";
                    break;
                }
            }
        }

        if invalid_question_message {
            return {
                "status": False,
                "message": f"Malformed question index. Check your configuration and try again. Hint: {invalid_question_message}",
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

        for function in self.question_functions {
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

    can create_session(visitor: interact_graph_walker) -> InterviewSession {
        # adds a new interview session to the frame for the current user

        all_fields = self.get_question_fields();
        required_fields = [
            key for key in all_fields
            if "extraction_guidance" in self.question_index.get(key, {})
            and self.question_index[key]["extraction_guidance"].get("required", False)
        ];
        interview_session = InterviewSession(all_fields=all_fields, required_fields=required_fields);
        # initialize active field
        interview_session.get_next_field();
        # add to the frame node
        visitor.frame_node.variable_set(key=f"{self.get_type()}_session", value=interview_session.export());

        return interview_session;
    }

    can delete_session(visitor: interact_graph_walker) {
        # removes the session object from the current user's frame
        visitor.frame_node.variable_del(key=f"{self.get_type()}_session");
    }

    can update_session(interview_session:InterviewSession, visitor: interact_graph_walker) {
        # updates interview session for the current user
        visitor.frame_node.variable_set(key=f"{self.get_type()}_session", value=interview_session.export());
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

    can init_session(visitor: interact_graph_walker) -> InterviewSession {
        # performs extraction and updates the session responses
        interview_session = self.get_session(visitor);

        # Create new session if none exists
        if not interview_session {
            interview_session = self.create_session(visitor);
        }

        # load any branch choice results for detection
        branch_choice_response = self.llm(self.branch_choice_prompt, visitor, json_only=True);

        if interview_session.get_state() in [SessionState.OPEN, SessionState.COMPLETED, SessionState.READY] {
            # Check for abort response
            if branch_choice_response.get('abort_response', False) {
                interview_session.set_state(SessionState.ABORTED);
                return interview_session;
            }
        }

        if interview_session.get_state() == SessionState.UPLOADING {
            # Check for receiving complete response
            if branch_choice_response.get('upload_complete_response', False) {

                # check if there are any more questions
                has_fields = (interview_session.get_next_field() is not None);

                if has_fields {
                    interview_session.set_state(SessionState.OPEN);
                } elif self.auto_confirm {
                    interview_session.set_state(SessionState.CONFIRMED);
                } else {
                    interview_session.set_state(SessionState.COMPLETED);
                }

                return interview_session;
            }
        }

        # Check for decline-to-answer response
        if branch_choice_response.get('decline_response', False) {

            # get field status - required or not
            if interview_session.on_required_field() {
                # insist that user must answer
                insist_directive = self.insist_response_directive.format(question=self.get_next_question(interview_session));
                visitor.interaction_node.add_directive(directive=insist_directive);
                return interview_session;

            } else {
                # apply 'n/a' to field response
                field = interview_session.get_next_field();
                question_response = {field : "n/a"};
                self.update_responses(question_response, interview_session);

                # if no more fields and we have an extraction, set to completed for confirmation
                if not interview_session.get_next_field() {
                    # new_state = SessionState.READY if interview_session.has_ignored_responses() else SessionState.COMPLETED;
                    interview_session.set_state(SessionState.COMPLETED);
                }

                return interview_session;
            }
        }

        # Handle confirmation for COMPLETED or READY states
        if interview_session.get_state() in [SessionState.COMPLETED, SessionState.READY, SessionState.REVISION] {

            confirmed = branch_choice_response.get('confirm_response', None);

            # handle auto-confirm when it's set
            if confirmed is True or self.auto_confirm {
                interview_session.set_state(SessionState.CONFIRMED);
                return interview_session;
            } elif confirmed is False {
                interview_session.set_state(SessionState.REVISION);
            }
        }

        # Process OPEN or REVISION states
        if interview_session.get_state() in [SessionState.OPEN, SessionState.REVISION] {

            question_functions = self.filter_question_functions(interview_session);
            question_responses = self.extract(question_functions, visitor);
            self.update_responses(question_responses, interview_session);

            # if no more fields and we have an extraction, set to completed for confirmation
            if not interview_session.get_next_field() {
                # eval auto-confirm or modfications following revision
                if self.auto_confirm {
                    interview_session.set_state(SessionState.CONFIRMED);
                } elif question_responses {
                    interview_session.set_state(SessionState.COMPLETED);
                }
            }
        }

        return interview_session;
    }

    can extract(functions:list, visitor: interact_graph_walker, history:Union[bool,None] = None) -> dict {
        # performs function tool calling for extracting question responses based on question

        prompt_messages = [];

        if not functions {
            return {};
        }

        use_history = self.history;
        if history is not None {
            use_history = history;
        }

        # prepare the final prompt with history.
        if (use_history) {
            # grab the history
            prompt_messages = [];

            statements = visitor.frame_node.get_transcript_statements(interactions = self.history_size, max_statement_length = self.max_statement_length, with_events = True);

            if (statements) {
                prompt_messages.extend(statements);
                self.logger.debug(f"history: {json.dumps(statements)}");
            }

        } else {
            # here we cater to whether we have context information or not..
            prompt_messages = [
                {"human": visitor.utterance}
            ];
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

    can llm(prompt:str, visitor: interact_graph_walker, history:Union[bool,None] = None, json_only:bool = False) -> dict {
        # performs function tool calling for extracting question responses based on question

        prompt_messages = [];

        if not prompt {
            return {};
        }

        use_history = self.history;
        if history is not None {
            use_history = history;
        }

        # prepare the final prompt with history.
        if (use_history) {
            # grab the history
            prompt_messages = [];

            statements = visitor.frame_node.get_transcript_statements(interactions = self.history_size, max_statement_length = self.max_statement_length, with_events = True);

            if (statements) {
                prompt_messages.extend(statements);
                self.logger.debug(f"history: {json.dumps(statements)}");
            }

            prompt_messages.extend([{"system": prompt}]);

        } else {
            # here we cater to whether we have context information or not..
            prompt_messages = [
                {"system": prompt},
                {"human": visitor.utterance}
            ];
        }

        model_action = self.get_agent().get_action(action_label=self.model_action);
        if model_action {
            model_action_result = model_action.call_model(
                prompt_messages=prompt_messages,
                prompt_variables={},
                kwargs={
                    "model_name": self.model_name,
                    "model_temperature": self.model_temperature,
                    "model_max_tokens": self.model_max_tokens
                },
                interaction_node=visitor.interaction_node
            );

            if model_action_result {
                if json_only {
                    return model_action_result.get_json_result();
                } else {
                    return model_action_result.get_result();
                }
            }
        }

        return {};
    }

    can update_responses(responses:dict, interview_session:InterviewSession) {
        for (field, response) in responses.items() {
            if field and response {
                interview_session.set_response(field, response);
            }
        }
    }
}

@unique
enum SessionState {
    OPEN = 'OPEN', # session is open for extractions -> collect responses
    UPLOADING = 'UPLOADING', # in silent mode, accepting uploads over several messages, user must state complete or done to continue
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
        return (self.get_next_field() in self.get_required_fields());
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

    can get_response(field: str) -> str {
        return self.responses.get(field, "");
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