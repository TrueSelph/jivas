import logging;
import traceback;
import from enum { unique }
import from logging { Logger }
import from jivas.agent.action.action { Action }
import from jivas.agent.modules.data.node_get { node_get }
import from jivas.agent.modules.system.common { node_obj }
import from jac_cloud.core.archetype {BaseCollection, NodeAnchor}
import from jivas.agent.modules.data.node_pager { NodePager }
import from jivas.agent.action.subgraph_action.state { State }
import from jivas.agent.action.subgraph_action.completed_state { CompletedState }
import from jivas.agent.action.subgraph_action.confirmed_state { ConfirmedState }
import from jivas.agent.action.subgraph_action.revision_state { RevisionState }
import from jivas.agent.action.subgraph_action.initial_state { InitialState }
import from jivas.agent.memory.collection { Collection }
import from jivas.agent.memory.frame { Frame }
import from jivas.agent.core.graph_walker { graph_walker }
import from jivas.agent.core.graph_node { GraphNode }


node SubgraphAction(Action) {
    # represents an execution on a subgraph on the agent action graph
    has persona_action:str = "PersonaInteractAction";
    has label: str = "";
    has description: str = "subgraph action that executes a series of states";
    has enabled: bool = True;
    has states: list = [];
    has initial_state:dict = {};
    has completed_state: dict = {};
    has confirmed_state:dict = {};
    has revision_state: dict = {};
    has parameters: list = [];


    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    def postinit {
        super.postinit();
        # list of node attributes which are protected from update operation
        self.protected_attrs += ['label', 'version', 'agent_id'];
        # list of node attributes which should be excluded from export
        self.transient_attrs += ['agent_id'];
    }

    # creates the subgraph based on data in 'states'
    def on_register(){
        agent_node = &self.agent_id;
        persona_action = agent_node.get_action(action_label=self.persona_action);
        persona_action.import_parameters(self.parameters);

        self.get_agent().get_memory().purge_collection_memory(self.label);

        collection = self.get_collection();
        index = 1;
        states_created = {};

        # initialize initial_state with optional prompt/directive if present
        if ("prompt" in self.initial_state and "directive" in self.initial_state) {
            initial_state = InitialState(
                collection_id=collection.id,
                prompt=self.initial_state.get("prompt"),
                directive=self.initial_state.get("directive"),
                label="initial_state"
            );
        }
        elif ("prompt" in self.initial_state) {
            initial_state = InitialState(
                collection_id=collection.id,
                prompt=self.initial_state.get("prompt"),
                label="initial_state"
            );
        }
        elif ("directive" in self.initial_state) {
            initial_state = InitialState(
                collection_id=collection.id,
                directive=self.initial_state.get("directive"),
                label="initial_state"
            );
        }
        else {
            initial_state = InitialState(
                collection_id=collection.id,
                label="initial_state"
            );
        }

        collection ++> initial_state;

        for state_info in self.states {
            states_created[f"state{index}"] = State(state_info=state_info, collection_id=collection.id, label=state_info.get("name", f"state{index}"));

            if(index == 1){
                initial_state ++> states_created[f"state{index}"];
            }
            else {
                states_created[f"state{index - 1}"] ++> states_created[f"state{index}"];
            }
            index += 1;
        }

        # initialize completed_state with optional prompt/directive if present
        if ("prompt" in self.completed_state and "directive" in self.completed_state) {
            completed_state = CompletedState(
                collection_id=collection.id,
                auto_confirm=self.completed_state.get("auto_confirm", False),
                prompt=self.completed_state.get("prompt"),
                directive=self.completed_state.get("directive"),
                label="completed_state"
            );
        }
        elif ("prompt" in self.completed_state) {
            completed_state = CompletedState(
                collection_id=collection.id,
                auto_confirm=self.completed_state.get("auto_confirm", False),
                prompt=self.completed_state.get("prompt"),
                label="completed_state"
            );
        }
        elif ("directive" in self.completed_state) {
            completed_state = CompletedState(
                collection_id=collection.id,
                auto_confirm=self.completed_state.get("auto_confirm", False),
                directive=self.completed_state.get("directive"),
                label="completed_state"
            );
        }
        else {
            completed_state = CompletedState(
                collection_id=collection.id,
                auto_confirm=self.completed_state.get("auto_confirm", False),
                label="completed_state"
            );
        }

        if ("directive" in self.confirmed_state) {
            confirmed_state = ConfirmedState(
                collection_id=collection.id,
                directive=self.confirmed_state.get("directive"),
                label="confirmed_state"
            );
        }else{
            confirmed_state = ConfirmedState(
                collection_id=collection.id,
                label="confirmed_state"
            );
        }

        # initialize revision_state with optional prompt/directive if present
        if ("prompt" in self.revision_state and "directive" in self.revision_state) {
            revision_state = RevisionState(
                collection_id=collection.id,
                states=self.states,
                prompt=self.revision_state.get("prompt"),
                directive=self.revision_state.get("directive"),
                label="revision_state"
            );
        }
        elif ("prompt" in self.revision_state) {
            revision_state = RevisionState(
                collection_id=collection.id,
                states=self.states,
                prompt=self.revision_state.get("prompt"),
                label="revision_state"
            );
        }
        elif ("directive" in self.revision_state) {
            revision_state = RevisionState(
                collection_id=collection.id,
                states=self.states,
                directive=self.revision_state.get("directive"),
                label="revision_state"
            );
        }
        else {
            revision_state = RevisionState(
                collection_id=collection.id,
                states=self.states,
                label="revision_state"
            );
        }

        states_created[f"state{index - 1}"] ++> completed_state;
        completed_state ++> confirmed_state;
        completed_state  ++> revision_state;

        self.logger.info(f"Created states in subgraph");
    }

    def run(frame_node:Frame, interaction_node:Interaction) -> str {
        directives = [];
        pre_process = self.pre_process(frame_node, interaction_node);
        if type(pre_process) is str{
            directives = [pre_process];
        }
        elif type(pre_process) is list{
            directives = pre_process;
        }
        walker_result = self.walk_subgraph(frame_node);
        directives.extend(walker_result.directives);

        walker_result.directives = {};

        responses = frame_node.data_get(key=f"{self.label}_results") or {};

        custom_directives = self.process_response(responses, frame_node, interaction_node);
        if custom_directives{
            directives = (custom_directives);
        }

        if (responses.get("confirm_response", "")){
            frame_node.data_set(key=f"{self.label}_results", value={});
        }
        return directives;
    }

    def set_directives(directive:str){
        self.directives.append(directive);
    }

    def walk_subgraph(frame_node:Frame) -> Union[str, dict] {
        collection = self.get_collection();
        walker_result = collection spawn _subgraph(frame_node=frame_node, agent_node=&self.agent_id, action_label=self.label);
        return walker_result;
    }

    def update_response(responses:dict, frame:Frame) {
        stored_responses = frame.data_get(key=f"{self.label}_results");

        if type(stored_responses) is not dict or not stored_responses {
            stored_responses = {};
        }

        # Merge new responses into stored_responses
        for (key, value) in responses.items() {
            stored_responses[key] = value;
        }

        frame.data_set(key=f"{self.label}_results", value=stored_responses);
    }

    def get_states(){
        collection = self.get_collection();

        states_list = node_get({
            "archetype.collection_id": collection.id,
        });
        return states_list;
    }

    def list_states(page:int=1, limit:int=20) -> list[dict]{
        collection = self.get_collection();

        # Initialize pager
        pager = NodePager(NodeAnchor.Collection, page_size=limit, current_page=page);

        # Get a page of results
        items = pager.get_page({
            "$or": [
                {"$and": [{"name": "InitialState"}, {"archetype.collection_id": collection.id}]},
                {"$and": [{"name": "State"}, {"archetype.collection_id": collection.id}]},
                {"$and": [{"name": "CompletedState"}, {"archetype.collection_id": collection.id}]},
                {"$and": [{"name": "ConfirmedState"}, {"archetype.collection_id": collection.id}]},
                {"$and": [{"name": "RevisionState"}, {"archetype.collection_id": collection.id}]}
            ]
        });

        if not items {
            return {};
        }

        # call export on each and convert it to a dict
        items = [item.export() for item in items];

        # get all info as a dict
        pagination_info = pager.to_dict();

        return {
            "page": page,
            "limit": limit,
            "items": items
        };
    }

    def get_state(label:str){
        collection = self.get_collection();

        state_node = node_obj(node_get({
            "archetype.collection_id": collection.id,
            "archetype.label": label
        }));

        return state_node;
    }

    def update_state(id:str, data:dict) -> GraphNode {
        collection = self.get_collection();

        state_node = node_obj(node_get({
            "archetype.collection_id": collection.id,
            "archetype.id": id
        }));

        # updates an state node; expects a dict of attribute names mapped to values for updating
        # overridden to respond to enable / disable updates
        enabled_changed = False;
        non_enabled_changed = False;

        if (data) {
            for attr in data.keys() {
                if (attr not in state_node.protected_attrs) {
                    # check if attribute is a node attribute
                    if (hasattr(state_node, attr)) {
                        # handle changes in disabled/enabled status
                        if attr == 'enabled' {
                            current_val = getattr(state_node, 'enabled');
                            if current_val != data[attr] {
                                enabled_changed = True;
                                if data[attr] == True {
                                    state_node.on_enable();
                                } else {
                                    state_node.on_disable();
                                }
                                setattr(state_node, attr, data[attr]);
                            }
                        } else {
                            current_val = getattr(state_node, attr);
                            if current_val != data[attr] {
                                non_enabled_changed = True;
                            }
                            setattr(state_node, attr, data[attr]);
                        }
                    } else {
                        # Handle context attributes; only mark as changed if the value is new or different
                        if (attr in state_node._context) {
                            if state_node._context[attr] != data[attr] {
                                non_enabled_changed = True;
                                state_node._context[attr] = data[attr];
                            }
                        } else {
                            non_enabled_changed = True;
                            state_node._context[attr] = data[attr];
                        }
                    }
                }
            }
        }

        # Conditionally trigger post_update only when:
        # 1. Node is enabled AND
        # 2. There were non-enabled changes OR no enabled changes occurred
        if state_node.enabled and (non_enabled_changed or not enabled_changed) {
            state_node.post_update();
        }

        return state_node;
    }

    def abort_process(value:bool = True){
        initial_state = self.get_state("initial_state");
        initial_state.abort = value;
    }

    def process_response(responses:dict, frame_node:Frame, interaction_node:Interaction) abs;

    def pre_process(frame_node:Frame, interaction_node:Interaction) abs;

}

walker _subgraph {
    # set up logger
    static has logger: Logger = logging.getLogger(__name__);

    has directives: list = [];
    has action_label: str = "";
    has agent_node: GraphNode = None;
    has frame_node: Frame = None;

    obj __specs__ {
        static has private:bool = True;
    }

    can on_collection with Collection entry {
        visit [-->] (`?State) else {
            disengage;
        }
    }

    can on_state with State entry {
        if here.touch(self) and here.enabled {
            # execute the action
            response = here.run(self);
            if(type(response) is bool) {
                visit [-->] else {
                    disengage;
                }
            }
            elif(type(response) is str) {
                self.set_directives(response);
                disengage;
            }
        }
        else {
            visit [-->] else {
                disengage;
            }
        }
    }

    can on_completed_state with CompletedState entry {
        if here.touch(self) {
            # execute the action
            response=here.run(self);
            if response == True {
                visit[-->](`?ConfirmedState) else {
                    disengage;
                }
            }
            elif response == False{
                visit[-->](`?RevisionState)else{
                    disengage;
                }
            }
            elif(type(response) is str) {
                self.set_directives(response);
                disengage;
            }
        }
    }
    can on_confirmed_state with ConfirmedState entry{
        response = here.run(self);
        self.set_directives(response);
    }
    def set_directives(directive:str){
        self.directives.append(directive);
    }
    can on_revision_state with RevisionState entry{
        if here.touch(self) {
            # execute the action
            response=here.run(self);
            if response is True {
                visit [<--](`?CompletedState) else {
                    disengage;
                }
            }
            elif(type(response) is str) {
                self.set_directives(response);
                disengage;
            }
        }
    }
    can on_exit with exit {
    }
    def set_directives(directive:str){
        self.directives.append(directive);
    }
}
