import:py os;
import:py pytz;
import:py json;
import:py logging;
import:py traceback;
import:py from typing { Optional }
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:py from datetime { datetime, timezone, timedelta }
import:jac from jivas.agent.action.actions { Actions }
import:jac from interact_action { InteractAction }
import:jac from exit_interact_action { ExitInteractAction }
import:jac from jivas.agent.memory.memory { Memory }
import:jac from jivas.agent.memory.frame { Frame }
import:jac from jivas.agent.memory.interaction { Interaction }
import:jac from jivas.agent.memory.interaction_response { InteractionResponse, InteractionMessage, SilentInteractionMessage }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.core.agents { Agents }
import:jac from jivas.agent.core.app { App }
import:jac from jivas.agent.action { interact_graph_walker }
import:py from jac_cloud.core.architype { NodeAnchor }
import:py json;


walker interact :interact_graph_walker: {
    # Walker for interacting with the agent

    # set up logger
    static has logger: Logger = logging.getLogger(__name__);
    # params
    has agent_id: str = "";
    has session_id: str = "";
    has utterance: str = "";
    has channel: str = "default"; # other channels: 'kiosk', 'whatsapp', 'fbm', 'slack', etc.
    has data: dict = {};
    has verbose: bool = False;
    has tts: bool = False;
    # protected vars
    has response: dict = {};
    has message: InteractionMessage = None;
    has execute: bool = False;
    has context_data: dict = {};
    has frame_node: Frame = None;
    has interaction_node: Interaction = None;
    has last_interaction_node: InteractAction = None;
    has agent_node: Agent = None;

    obj __specs__ {
        static has auth: bool = True;
        static has private: bool = True;
        static has excluded: list = [
            "response",
            "execute",
            "context_data",
            "frame_node",
            "interaction_node",
            "last_interaction_node",
            "agent_node"
        ]; # Supported in jac-cloud > 0.0.3
    }
    can on_root with `root entry {
        # validate interaction or disengage

        if (self.init_interaction()) {
            # head to agent node if valid
            visit self.agent_node;
        } else {
            disengage;
        }
    }

    can on_agent with Agent entry {
        # traverse to actions branch node
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        # if we have a resume action... head there instead
        # ensure we include a resume flag in the context_data of the
        # current interaction node for the benefit of action handlers

        # the interact walk, sorts the interact actions by weight to preserve execution order before walk

        if (resume_action_node := self.frame_node.get_resume_action(self.last_interaction_node)) {
            # add any resumption directives from the last interaction node of the frame...
            root_action_node = resume_action_node.get_root_action();
            self.interaction_node.add_intent(root_action_node.label);
            visit here.queue_interact_actions(
                [-->](`?InteractAction)(?enabled == True)
            );

            if( self.subqueue_interact_action(resume_action_node, root_action_node) ) {
                self.interaction_node.context_data["resumed"] = True;
            }
        }
        else{
            queued_actions = here.queue_interact_actions(
                [-->](`?InteractAction)(?enabled == True)
            );
            visit queued_actions;
        }
        self.logger.debug(f"Utterance: {self.utterance}");
    }

    can on_action with InteractAction entry {

        # performs execute routine for action nodes
        result = {};

        intended = self.is_intended(here);
        has_access = self.has_access(here);
        has_function = self.has_function(here);

        if (intended) {

            if(has_access) {
                # execute touch
                self.logger.debug(f"Touching: {here.label}");
                self.execute = here.touch(visitor=self);
                if (self.execute) {

                    # execute the action
                    self.logger.debug(f"Executing: {here.label}");
                    if (result := here.execute(visitor=self)) {
                        # if theres an update to this walker, effect it..
                        self.update(result);
                    }

                    self.interaction_node.trail.append(here.label);
                    self.execute = False;
                }

                self.update(result);
            } else {
                # execute the deny ability to handle access denial condition
                here.deny(visitor=self);
            }


        }
    }

    can on_exit with exit {
        # prepare and return response, then exit
        self.respond();
    }

    can init_interaction() -> bool {
        # performs validation checks on the interaction
        try  {
            self.agent_node = &self.agent_id;
            if(not self.agent_node) {
                return False;
            }
        } except Exception as e {
            Jac.get_context().status = 400;
            self.logger.error("invalid agent id");
            return False;
        }

        # load config from jivas.agent_node or defaults
        message_limit = self.agent_node.message_limit;
        flood_block_time = self.agent_node.flood_block_time;
        window_time = self.agent_node.window_time;
        flood_threshold = self.agent_node.flood_threshold;

        # load or spawn a frame for this interaction
        self.frame_node = self.agent_node.get_memory().get_frame(
            agent_id=self.agent_node.id,
            session_id=self.session_id
        );

        if (not self.frame_node) {
            Jac.get_context().status = 500;
            self.logger.error("unable to initiate a frame");
            return False;
        }

        # validate message length
        chunks = Utils.chunk_long_message(
            message=self.utterance,
            max_length=message_limit,
            chunk_length=message_limit
        );

        if (len(chunks) > 1) {
            Jac.get_context().status = 400;
            self.logger.warning(
                "unable to process message; message length exceeds limit"
            );
            return False;
        }

        # for converting datetimes before comparison
        utc = pytz.UTC;

        # handle flood control
        now = datetime.now(timezone.utc);

        # check if flood is active
        flood = self.frame_node.variable_get(key="flood");

        if (flood) {
            # check if flood is still active
            if (utc.localize(flood["expiration"]) > now) {
                Jac.get_context().status = 429;
                self.logger.warning("flood control active");
                return False;
            }
        }

        # track message window count
        message_window = self.frame_node.variable_get(key="message_window");

        if (message_window) {
            # Convert items to datetime objects
            keys = ["start", "end"];
            ::py::
            message_window = {key: utc.localize(value) if isinstance(value, datetime) else datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f") for key, value in message_window.items() if key in keys};
            ::py::

            if (message_window.get("end", 0) <= now) {
                # reset window
                message_window["start"] = now;
                message_window["end"] = now + timedelta(seconds=window_time);
                message_window["count"] = 0;
            } else {
                # increment message count
                message_window["count"] = message_window.get("count", 0) + 1;
            }

            # check if message count exceeds threshold
            if (message_window.get("count", 0) > flood_threshold) {
                # set flood control
                flood = {"expiration": now + timedelta(seconds=flood_block_time)};
                self.frame_node.variable_set(key="flood", value=flood);

                Jac.get_context().status = 429;
                self.logger.warning("flood control active");
                return False;
            }
        } else {
            # initialize message window
            message_window = {
                "start": now,
                "end": now + timedelta(seconds=window_time),
                "count": 1
            };

            self.frame_node.variable_set(
                key="message_window",
                value=message_window
            );
        }

        # save last interaction, if any
        self.last_interaction_node = self.frame_node.get_last_interaction();

        # add new interaction node to the frame
        self.interaction_node = self.frame_node.add_interaction(
            utterance=self.utterance,
            channel=self.channel
        );

        if (not self.interaction_node) {
            return False;
        }

        # add any data to the interaction for processing later...

        if (self.data) {
            required_fields = ["label", "data_type", "content"];
            if (all([field in self.data for field in required_fields])) {
                if (self.data["label"]
                    and self.data["data_type"]
                    and self.data["content"]) {
                    self.interaction_node.set_data_item(
                        label=self.data["label"],
                        meta={'type': self.data["data_type"]},
                        content=self.data["content"]
                    );
                } else {
                    Jac.get_context().status = 400;
                    self.logger.error(
                        f"malformed data payload; requires {required_fields} {values}"
                    );
                }
            } else {
                Jac.get_context().status = 400;
                self.logger.error(
                    f"malformed data payload; requires {required_fields} {values}"
                );
            }
        }

        return True;
    }

    can set_next_action(action_label:str, action_node:Optional[InteractAction]=None) {
        # inserts the supplied action as the next action in the walk path
        next_action_node = None;

        if(action_label) {
            next_action_node = self.agent_node.get_actions().get(action_label=action_label);
        } elif(action_node) {
            next_action_node = action_node;
        }

        if(next_action_node) {
            self.prepend_interact_action(next_action_node);
        }
    }

    can set_resume_action(action_label:str, action_node:Optional[InteractAction]=None) {
        # queues the supplied action as the first action on the next turn
        resume_action_label = None;

        if(action_label) {
            resume_action_label = action_label;
        } elif(action_node) {
            resume_action_label = action_node.label;
        }

        if(resume_action_label) {
            self.frame_node.set_resume_action(
                action_label=resume_action_label
            );
        }
    }

    can append_action(action_label:str, action_node:Optional[InteractAction]=None) {
        # appends the supplied action to the end of the walk path (before exit)
        append_action_node = None;

        if(action_label) {
            append_action_node = self.agent_node.get_actions().get(action_label=action_label);
        } elif(action_node) {
            append_action_node = action_node;
        }

        if(append_action_node) {
            self.append_interact_action(append_action_node);
        }
    }

    can dequeue_action(action_label:str, action_node:Optional[InteractAction]=None) {
        # dequeue the supplied action as the next action in the walk path

        if(action_label) {
            action_node = self.agent_node.get_actions().get(action_label=action_label);
        }

        if(action_node) {
            self.dequeue_interact_action(action_node);
        }
    }

    can append_interact_action(interact_action: InteractAction) {
        # adds the interact action to the end of the active walk path (before exit)

        # first grab exit action
        if (exit_action := self.agent_node.get_actions().get(action_label="ExitInteractAction") ) {
            exit_action_node_ref = None;
            # remove and save the exit action
            for (i, node_ref) in enumerate(self.__jac__.next) {
                if (f'{node_ref.id}' == f'{exit_action.__jac__.id}') {
                    exit_action_node_ref = self.__jac__.next[i];
                    self.__jac__.next.pop(i);
                    break;
                }
            }

            # dequeue the action if it already exists in walk path
            self.dequeue_interact_action(interact_action);

            # add the next action at the end of walk path (without exit)
            visit interact_action;
            # then re-add the exit action after it
            self.__jac__.next.append(exit_action_node_ref);

            return self.__jac__.next;


        } else {
            visit interact_action;
        }

        return None;
    }

    can dequeue_interact_action(interact_action: InteractAction) {
        # removes the interact action from the active walk path
        if (self.__jac__.next and interact_action) {
            for (i, node_ref) in enumerate(self.__jac__.next) {
                if (f'{node_ref.id}' == f'{interact_action.__jac__.id}') {
                    self.__jac__.next.pop(i);
                    break;
                }
            }

            return self.__jac__.next;
        }

        return None;
    }

    can prepend_interact_action(interact_action: InteractAction) {
        # adds the interact action to the head of the active walk path
        if( self.dequeue_interact_action(interact_action) ) {

            # backup the clean path
            path = self.__jac__.next;
            # reset the walk path
            self.__jac__.next = [];
            # reinsert the interact action at the head of walk path
            visit interact_action;
            # restore the remaining walk path after the interact action
            self.__jac__.next.extend(path);

            return self.__jac__.next;
        }

        return None;
    }

    can subqueue_interact_action(interact_action: InteractAction, index_interact_action: InteractAction) {
        # adds the interact action to the head of a subset of the walk path following index interact action

        if( interact_action and index_interact_action ) {

            if( (exit_action := self.agent_node.get_actions().get(action_label="ExitInteractAction"))
                and self.in_next_queue(index_interact_action) ) {
                jac_next_copy = self.__jac__.next.copy();
                jac_trail = enumerate(jac_next_copy, start=0);

                # remove all actions from head up to and including index
                for (i, node_ref) in jac_trail {
                    if (f'{node_ref.id}' == f'{index_interact_action.__jac__.id}') {
                        break;
                    } elif(f'{node_ref.id}' != f'{exit_action.__jac__.id}') {
                        self.__jac__.next.pop(0);
                    }
                }
            }

            # then prepend interact action
            if( self.prepend_interact_action(interact_action) ) {
                return self.__jac__.next;
            }

        }

        return None;

    }

    can in_next_queue(action_node: InteractAction) -> bool {
        # checks if the action node is in the next queue
        if (action_node) {
            for node_ref in self.__jac__.next{
                if (f'{node_ref.id}' == f'{action_node.__jac__.id}') {
                    return True;
                }
            }
        }

        return False;
    }

    can has_access(action_node: Action) -> bool {
        # implements access control routine if access_control_action is in play, then executes touch if permitted

        access = True;
        if (action_node.get_type() in ['AccessControlAction', 'ExitInteractAction']) {
            return True;
        }
        if (access_control_action_node := (self.agent_node.get_actions().get(
            action_label='AccessControlAction'
        ))) {

            access = access_control_action_node.has_action_access(
                session_id=self.frame_node.session_id,
                action_label=action_node.get_type(),
                channel=self.interaction_node.channel
            );
        }

        return access;
    }

    can has_function(action_node: InteractAction) -> bool {
        # determines whether action is intended to be triggered by the intent within the interaction, then executes touch if permitted
        if (action_node.get_type() in ['IntentInteractAction', 'FunctionInteractAction', 'ExitInteractAction']) {
            return True;
        }
        if ((function_interact_action_node := self.agent_node.get_actions().get(
            action_label='FunctionInteractAction'
        ))) {
            if (function_interact_action_node.enabled
                and function_interact_action_node.strict) {

                # if the intent classification action is enabled and at play, then we enforce access per classification
                if (action_node.label not in (self.interaction_node.get_intents() + function_interact_action_node.exceptions)) {
                    return False;
                }
            }
        }

        return True;
    }

    can is_intended(action_node: InteractAction) -> bool {
        # determines whether action is intended to be triggered by the intent within the interaction, then executes touch if permitted
        if (action_node.get_type() in ['IntentInteractAction', 'FunctionInteractAction', 'ExitInteractAction']) {
            return True;
        }
        if (intent_interact_action_node := self.agent_node.get_actions().get(
            action_label='IntentInteractAction'
        )) {
            if (intent_interact_action_node.enabled
                and intent_interact_action_node.strict) {

                # if the intent classification action is enabled and at play, then we enforce access per classification
                if (action_node.label not in (self.interaction_node.get_intents() + intent_interact_action_node.exceptions)) {
                    return False;
                }
            }
        }

        return True;
    }

    can respond() {

        if (self.agent_node and self.interaction_node) {
            # init var
            interaction_data = {};

            # lets return the generated response, if we have one...
            has_response = self.interaction_node.has_response();
            if (has_response) {

                try  {

                    # set the message obj
                    self.message = self.interaction_node.get_message();

                    # prepare the response payload
                    interaction_data = self.interaction_node.export();

                    # handle verbose mode
                    if (self.verbose) {
                        interaction_data['frame'] = self.frame_node.export();
                        self.response = interaction_data;
                    } else {
                        self.response = {"response": self.interaction_node.get_response().export()};
                    }

                    if( self.agent_node.is_logging() ) {
                        # log interaction
                        self.log_interaction(data = interaction_data);
                    }

                } except Exception as e {
                    self.logger.error(
                        f"an exception occurred, {traceback.format_exc()}"
                    );
                }
            }

            if (not has_response or not self.response) {
                self.message = SilentInteractionMessage();
                self.response = InteractionResponse(
                    session_id=self.frame_node.session_id,
                    message=self.message.export()
                ).export();
            }

            # activate pruning protocol to shed old interactions beyond frame_size limit from this interaction frame

            self.frame_node.prune_interactions(
                frame_size=self.agent_node.frame_size
            );

        } else {
            self.message = SilentInteractionMessage();
            self.response = InteractionResponse(message=self.message.export()).export();
        }

        # handle text-to-speech if enabled
        if (self.tts) {
            if (tts_action := self.agent_node.get_tts_action()) {

                content = self.message.get_meta('phoneme_content')
                    or self.message.get_content();

                # perform TTS
                audio = tts_action.invoke(text=content, as_url=True);

                if (audio) {
                    self.response["response"].update({"audio_url": audio});
                }
            }
        }
        if (self.reporting) {
            report self.response;
        }
    }

    can log_interaction(data: dict) {
        collection = NodeAnchor.Collection.get_collection("interactions");
        collection.insert_one(json.loads(json.dumps(data)));
    }
}
