import:py io;
import:py os;
import:py re;
import:py subprocess;
import:py pkg_resources;
import:py sys;
import:py yaml;
import:py logging;
import:py traceback;
import:py tarfile;
import:py requests;
import:py from typing { Union }
import:py from logging { Logger }
import:py from jaclang { jac_import }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:py from jvcli.api { RegistryAPI }
import:py from jvcli.utils { is_version_compatible }
import:py from jvserve.lib.agent_interface { AgentInterface }
import:jac from action { Action }
import:jac from interact_action { InteractAction }
import:jac from jivas.agent.core.graph_node { GraphNode }
import:jac from exit_interact_action { ExitInteractAction }
import:jac from jivas.agent.core.purge { purge }

node Actions :GraphNode: {

    # set up logger
    static has logger: Logger = logging.getLogger(__name__);
    # action packages root folder
    static has package_root: str = Utils.get_actions_root();

    can get(action_label: str="", action_type: str="", only_enabled:bool=True) -> Union[Action, list, None] {
        # returns an action by label or by type, enabled actions by default
        result = None;

        if action_type and not action_label {
            # there can be multiple actions of the same type, this returns a list
            result = self.get_by_type(action_type, only_enabled);
        } elif action_label and not action_type {
            # there can only be one action with a particular label, this returns a action
            result = self.get_by_label(action_label, only_enabled);
        }

        return result;
    }

    can get_by_label(action_label: str, only_enabled:bool=True) -> Action {
        # returns an action by label
        actions = self.get_all(only_enabled=only_enabled);
        for action_node in actions {
            if (action_node.label == action_label) {
                return action_node;
            }
        }

        return None;
    }

    can get_by_type(action_type: str, only_enabled:bool=True) -> list {
        # returns an action by type; there may be multiple instances of the same action so a list is returned
        result = [];
        actions = self.get_all(only_enabled=only_enabled);

        for action_node in actions {
            if (action_type == action_node.get_type()) {
                result.append(action_node);
            }
        }

        return result;
    }

    can get_all(only_interact_actions:bool=False, only_enabled:bool=False) -> list {
        # returns a list of all actions, even nested ones
        if (only_interact_actions) {
            return ((self spawn _get_interact_actions(filter_enabled=only_enabled)).action_nodes);
        }
        return ((self spawn _get_actions(filter_enabled=only_enabled)).action_nodes);
    }

    can queue_interact_actions(actions:list) -> list {
        # accepts a list of interact actions and organizes them in an execution queue
        # based on weights and precedence specified in _package.config.order

        # this is the Jaclang equivalent of a lamda function
        # return sorted(objects, key=lambda InteractAction:obj.weight)
        return sorted(actions, key = with action:InteractAction can action.weight );
    }

    can get_action_info(namespace_package_name:str, version:str=None, jpr_api_key:str=None) -> dict {
        # retrieves the info.yaml data for a named action by version either locally first or on package manager

        action_info = {};

        # extract the namespace, package name
        (namespace, package_name) = namespace_package_name.split('/');

        # attempt to find the package locally, first...
        if (package_path := Utils.find_package_folder(self.package_root, namespace_package_name) ) {

            info_yaml_path = os.path.join(package_path, 'info.yaml');

            try  {

                with open(info_yaml_path, 'r') as file {
                    # load the action info content
                    _info = yaml.safe_load(file);
                    # grab info package version
                    package_version = _info.get('package', {}).get('version', '~0.0.1');

                    # validate the version
                    if is_version_compatible(package_version, version) { # failing on 0.0.5 == ^0.0.1
                        # log that we found it
                        self.logger.info(f'{namespace_package_name} {package_version} loaded locally');
                        # craft the module root
                        module_root = Utils.path_to_module(package_path);
                        # determine whether we have an app in this package
                        has_app = os.path.isfile( os.path.join(package_path, 'app', 'app.py') );
                        # set the package info
                        action_info = _info['package'];
                        # set info package path
                        action_info['config']['path'] = package_path;
                        # dynamically set action app flag
                        action_info['config']['app'] = has_app;
                        # add the module root
                        action_info['config']['module_root'] = module_root;
                        # add the action module for loading
                        action_info['config']['module'] = f"{module_root}.{package_name}";
                    }
                }
            } except yaml.YAMLError as e {
                self.logger.error(
                    f"an exception occurred, {traceback.format_exc()}"
                );
            }
        }

        if(not action_info) {

            if( _info := RegistryAPI.get_package_info(namespace_package_name, version, api_key=jpr_api_key) ) {
                self.logger.info(f'{namespace_package_name} {version} found in registry');
                # set the package info
                action_info = _info.get('package', None);
            }
        }

        # perform final preprocessing on action info
        if(action_info) {
            action_info['config']['namespace'] = namespace;
            action_info['config']['package_name'] = package_name;
        }

        return action_info;
    }

    can import_action(action_data:dict) -> bool {
        # prepares the module path to lib.jac and imports the module
        module_root = action_data.get('context', {}).get('_package', {}).get('config', {}).get('module_root', None);

        if(module_root) {
            jac_import(f"{module_root}.lib", base_path="./", reload_module = True);
            return True;
        }

        return False;
    }

    can register_action(action_data: dict, parent: str="") -> Action {
        # registers an agent action
        # expects an action descriptor object with optional architype source embeddings;
        action_node = None;

        if(not action_data) {
            self.logger.error(f"unable to register action {label}, missing or invalid action data");
            return None;
        }

        label = action_data.get('context', {}).get('label', action_data.get('action', None));
        architype = action_data.get('context', {}).get('_package', {}).get('architype', None);
        module = action_data.get('context', {}).get('_package', {}).get('config', {}).get('module', None);
        singleton = action_data.get('context', {}).get('_package', {}).get('config', {}).get('singleton', False);
        action_type = action_data.get('context', {}).get('_package', {}).get('meta', {}).get('type','action');

        if (not architype or not module or not label) {
            self.logger.error(f"unable to register action {label}, missing label, architype or module name");
            return None;
        }

        try  {

            if (singleton) {
                # check if action is a singleton action with duplicate type
                if (existing_action := self.get(action_type=label, only_enabled=False)) {
                    self.logger.error(f"action already exists: {label}");
                    return None;
                }
            } elif (existing_action := (self.get(action_label=label, only_enabled=False))) {
                # check if non singleton action has unique label
                self.logger.error(f"action already exists: {existing_action.label}");
                return None;
            }

            # spawn the action node without any prop values, then do a update - it's safer this way
            action_node = AgentInterface.spawn_node(
                node_name=architype,
                attributes={},
                module_name=module
            );

            # at this point all architypes related to this action are registered, let's map
            if (action_node) {

                # update the action node with the action data
                attributes = action_data.get('context', {});
                for attr in attributes.keys() {
                    if (hasattr(action_node, attr)) {
                        setattr(action_node, attr, attributes[attr]);
                    } else {
                        # we place all non attributes in _context for integration later
                        action_node._context[attr] = attributes[attr];
                    }
                }

                # get action parent node
                if (not parent) {
                    action_parent_node = self;
                } else {
                    action_parent_node = self.get_by_type(action_type=parent, only_enabled=False);
                }
                # map the action
                action_parent_node ++> action_node;

                # execute the action's on_register ability for on registration inits
                action_node.on_register();

                # log success if all went well
                self.logger.info(f"registered action: {action_node.label}");
            }

            # Handle child actions; only interact_actions can have child actions
            # we also cannot nest regular actions under interact_actions
            if ("children" in action_data and action_type == 'interact_action') {
                for child_data in action_data["children"] {
                    self.register_action(
                        action_data=child_data,
                        parent=architype
                    );
                }
            }

        } except Exception as e {
            self.logger.error(
                f"an exception occurred wile registering action {label}, {traceback.format_exc()}"
            );
        }

    }

    can install_actions(agent_id:str, action_list: list, jpr_api_key:str=None) -> bool {
        # accepts the list of action data and related configurations and coordinates the importation and registration of action packages
        loaded_actions_data = None;

        if(agent_id) {
            loaded_actions_data = self.load_actions(agent_id=agent_id, action_list=action_list, jpr_api_key=jpr_api_key);
        }

        # if actions data is empty, quit right here with error
        if(not loaded_actions_data) {
            self.logger.error('no actions loaded; unable to proceed with import');
            return False;
        }

        # purge all actions and related imported modules
        self.deregister_actions();

        # now register all the action nodes on loaded action data...
        for action_data in loaded_actions_data {
            self.register_action(action_data=action_data);
        }

        # Add systems exit action, last
        self ++> ExitInteractAction();

        # Now call post_register() on each action to execute any setup code which relies on all actions being in place
        for action_node in self.get_all() {
            action_node.post_register();
        }

        return True;
    }

    can deregister_action(action_type: str="", action_label: str="") {
        # gracefully disposes of an action, calling the on_deregister on each action node before destruction
        # can perform deregistration by type or by label

        target = [];

        if action_type and not action_label {
            target = self.get_by_type(action_type=action_type, only_enabled=False);
        } elif action_label and not action_type {
            target.append(self.get_by_label(action_label=action_label, only_enabled=False));
        }
        for action_node in target {
            action_node.on_deregister();
            # remove the action module folder and (TODO: related modules)
            # Utils.clean_action(action_node._package.get('name')); # cant remove this until we can unload module in runtime
            # purge action from graph
            action_node spawn purge();
        }

    }

    can deregister_actions() {
        # gracefully disposes of each action, calling the on_deregister on each action node before destruction

        # call deregister on all legit actions
        for action_node in self.get_all() {
            action_node.on_deregister();
            # TODO: remove the action module folder and related modules
        }

        # remove all nodes under Actions except Actions itself
        self spawn purge(purge_spawn_node=False);

        # jac clean actions folder
        Utils.jac_clean_actions();
    }

    # UTILS

    can search_action_list(namespace_package_name:str, action_list:list) -> dict {
        # searches an action list for the entry based on the namespace_package_name

        for action_data in action_list {
            if action_data.get('action') == namespace_package_name {
                return action_data;
            }
        }

        return {};
    }

    can index_action_packages(agent_id:str, action_list:list, action_index:dict={}, jpr_api_key:str="") -> dict {
        # recursive operation which flattens the action list, loads all actions, their children and their dependencies,
        # builds list ensuring dependencies precede dependent actions
        # returns a loaded list of valid actions as a dictionary, indexed by namespace_package name

        for action_data in action_list {

            namespace_package_name = action_data.get('action', None);
            is_not_indexed = (namespace_package_name not in action_index.keys());
            package_version = action_data.get('context', {}).get('version', '~0.0.1');

            if ( is_not_indexed and namespace_package_name) {

                # validate the existence of action package and add package metadata to action in index
                if((action_info := self.get_action_info(namespace_package_name, package_version, jpr_api_key))) {

                    action_data['context']['agent_id'] = agent_id;
                    action_data['context']['_package'] = action_info;
                    # grab the action architype name
                    architype = action_info.get('architype', None);
                    # label, if set will be used, otherwise use architype
                    action_data['context']['label'] = action_data.get('context', {}).get('label', architype);
                    # apply the description in the info file to the action entry
                    action_data['context']['description'] = action_info.get('meta', {}).get('description', '');

                    # handle any dependencies of this action recursively and add them first, if not already there
                    if( action_deps := action_info.get('dependencies', {}).get('actions', {}) ) {

                        action_dep_list = [];
                        for action_dep in action_deps.keys() {
                            # prepare dependency action data list
                            action_dep_version = action_deps[action_dep];
                            action_dep_list.append( {
                                "action": action_dep,
                                "context": {
                                    "version": action_dep_version,
                                    "enabled": True
                                }
                            });
                        }

                        # recursively add dependency entries to running action index
                        action_index = self.index_action_packages(
                            agent_id=agent_id,
                            action_list=action_dep_list,
                            action_index=action_index,
                            jpr_api_key=jpr_api_key
                        );

                        # need to skip to next iteration if the dependency is not resolved so action is not added to index
                        ::py::
                        if not all(key in action_index.keys() for key in action_deps.keys()):
                            continue
                        ::py::
                    }

                    # Handle child actions recursively
                    if "children" in action_data {
                        action_index = self.index_action_packages(
                            agent_id=agent_id,
                            action_list=action_data["children"],
                            action_index=action_index,
                            jpr_api_key=jpr_api_key
                        );
                    }

                    # add it to action index if not already there
                    if(namespace_package_name not in action_index.keys()) {
                        # add to action index
                        action_index[namespace_package_name] = action_data;
                    }

                } else {
                    self.logger.error(f"unable to find action {namespace_package_name} {package_version}");
                }
            }
        }

        return action_index;
    }

    can index_pip_packages(action_data_index:dict) -> dict {
        # returns a flat dictionary of pip packages where the key is the package name and value is the package version
        pip_packages_index = {};

        for (namespace_package_name, action_data) in action_data_index.items() {
            if(pip_packages := action_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('pip', {})) {
                pip_packages_index.update(pip_packages);
            }
        }

        return pip_packages_index;
    }

    can batch_pip_package_install(packages:dict) {
        # """
        # Installs multiple pip packages quietly, non-interactively,
        # and auto-resolving conflicts. If no operator is provided in
        # version spec, '==' is assumed.

        # Args:
        #     packages (dict): Dictionary in {"package": "[operator]version"} format.
        #                     e.g. {"numpy": "1.23.0", "pandas": ">=1.5.0"}
        #     quiet (bool): Runs pip install quietly if True.
        #     resolve_conflicts (bool): Aggressively resolve package version conflicts.

        # Returns:
        #     None
        # """

        package_specs = [];

        for (pkg, ver) in packages.items() {
            if (not ver) {
                package_specs.append(pkg);
            }
            elif ( bool(re.match(r'^(==|>=|<=|>|<|~=|!=)', ver)) ) {
                package_specs.append(f"{pkg}{ver}");
            }
            else {
                package_specs.append(f"{pkg}=={ver}");
            }
        }

        command = [sys.executable, "-m", "pip", "install", "--upgrade", "--no-input"];
        command.extend(package_specs);

        self.logger.info(f"Attempting to install package dependencies: {package_specs}");

        try {
            subprocess.run(command, check=True, stderr=None, stdout=None);
            self.logger.info("Package dependencies installed successfully.");
        } except subprocess.CalledProcessError as e {
            self.logger.error(f"An error occurred while installing one or more package dependencies. There may be a conflict or a missing package.");
        }
    }

    can has_pip_package(package_name:str, version:str=None) -> bool {
        # """
        # Checks if a pip package is installed and optionally verifies the version with optional comparator operators.

        # Parameters:
        # package_name (str): The name of the package to check.
        # version (str, optional): The specific version to check for, with optional comparator operators (e.g., >=, <=, etc.). Defaults to None.

        # Returns:
        # bool: True if the package is installed and the version matches the condition (if specified), otherwise False.
        # """
        try {
            package_distribution = pkg_resources.get_distribution(package_name);

            if version is None {
                # If no version is specified, simply confirm the package is installed
                return True;
            } else {
                # If no operator is detected, assume '=='
                if (not re.match(r'^(==|>=|<=|>|<|~=|!=)', version)) {
                    version = f"=={version}";
                }
                # Compare the installed package's version with the specified version
                return pkg_resources.parse_version(package_distribution.version) in pkg_resources.Requirement.parse(f"{package_name}{version}");
            }
        } except pkg_resources.DistributionNotFound {
            return False;
        }
    }

    can has_pip_packages(packages:dict) -> bool {
        # """
        # Checks if multiple pip packages are installed.

        # Args:
        #     packages (dict): Dictionary in {"package": "version"} format.
        #                     e.g. {"numpy": ">=1.23.0", "pandas": "1.5.0"}

        # Returns:
        #     bool: True if all packages are installed and versions match, otherwise False.
        # """

        for (pkg, ver) in packages.items() {
            if (not self.has_pip_package(pkg, ver)) {
                return False;
            }
        }

        return True;
    }

    can has_action_dependencies(action_data_index:dict, action_dependencies:dict) -> bool {
        # determines whether all dependencies have been loaded
        ::py::
        if not all(key in action_data_index.keys() for key in action_dependencies.keys()):
            return False
        ::py::

        return True;
    }

    can load_action_package(indexed_action_data:dict, jpr_api_key:str="") -> dict {
        # loads a single action package based on indexed action package information
        # loading entails downloading the package or ensuring the package exists in the actions root
        # returns empty dict if loading goes wrong, otherwise returns loaded, refreshed action data

        namespace_package_name = indexed_action_data.get('context', {}).get('_package', {}).get('name');
        package_version = indexed_action_data.get('context', {}).get('version', '~0.0.1');
        required_jivas_version = indexed_action_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('jivas', None);
        package_path = indexed_action_data.get('context', {}).get('_package', {}).get('config', {}).get('path', None);
        jivas_version = Utils.get_jivas_version();

        # check jivas version compatibility
        if (not is_version_compatible(jivas_version, required_jivas_version)) {
            self.logger.error(f'incompatible JIVAS version for: {namespace_package_name} ( required: {required_jivas_version}  system: {jivas_version} ) ...skipping');
            return {};
        }

        # if an action package is already downloaded, there will be a 'path' variable in the '_package' key
        # if not, we need to download it and refresh the _package values
        if package_path is None {

            # download package from package repo
            package_data = RegistryAPI.download_package(namespace_package_name, package_version, api_key=jpr_api_key);

            if not package_data {
                self.logger.error(f'unable to load action package: {namespace_package_name} {package_version} ...skipping');
                return {};
            }

            try {
                package_file = requests.get(package_data["file"]);
                # Save and extract the package
                target_dir = os.path.join(self.package_root, namespace_package_name);
                os.makedirs(target_dir, exist_ok=True);
                # Assuming the package_data is a ZIP file
                with tarfile.open(
                    fileobj=io.BytesIO(package_file.content),
                    mode="r:gz"
                ) as tar_file {
                    tar_file.extractall(target_dir);
                }
                self.logger.info(f'downloaded action package: {namespace_package_name} {package_version}');
            } except Exception as e {
                self.logger.error(f'unable to save action package: {namespace_package_name}...skipping, {e}');
                return {};
            }

            # attempt to refresh and replace action _package data, now that the path is in place
            if( action_info := self.get_action_info(namespace_package_name, package_version, jpr_api_key) ) {
                indexed_action_data['context']['_package'] = action_info;
                if( not action_info.get('config', {}).get('path', None) ) {
                    # if download and reload unsuccessful,
                    # report and skip to next item
                    self.logger.error(f'unable to load action package: {namespace_package_name} {package_version}...skipping');
                    return {};
                }
            }

        }

        return indexed_action_data;
    }

    can load_actions(agent_id:str, action_list:list, jpr_api_key:str=None) -> list {
        # accepts an agent descriptor listing of actions, prepares a loading manifest of ordered deps,
        # loads them and returns ordered, loaded action data

        # grab flattened list of action data indexed by namespace package name, ordered by action deps
        action_data_index = self.index_action_packages(agent_id=agent_id, action_list=action_list, jpr_api_key=jpr_api_key);

        ## NOTHING TO LOAD?
        if not action_data_index {
            return [];
        }

        ## INSTALL ALL PIP DEPENDENCIES ACROSS ACTIONS
        # preprocess all pip depenedencies and install them in batch
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--root-user-action=ignore"]);
        indexed_pip_packages = self.index_pip_packages(action_data_index);
        self.batch_pip_package_install(indexed_pip_packages);

        # make a working copy to iterate thru
        action_data_index_copy = action_data_index.copy();
        for (namespace_package_name, action_data) in action_data_index_copy.items() {

            ## LOAD THE ACTION
            loaded_action_data = self.load_action_package(indexed_action_data=action_data, jpr_api_key=jpr_api_key);

            ## ACTION LOADED?
            if not loaded_action_data {
                # remove the related entry from action_data_index if unsuccessful
                del action_data_index[namespace_package_name];
                continue;
            }

            ## PIP PACKAGES LOADED ?
            if(not self.has_pip_packages( loaded_action_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('pip', {}) )) {
                # report and continue
                self.logger.error(f'missing pip package dependencies for {namespace_package_name}...skipping');
                # remove the related entry from action_data_index
                del action_data_index[namespace_package_name];
                continue;
            }

            # HANDLE ANY CHILDREN
            # we need to unflatten the index and restore child action hierarchy in full, per action
            action_type = loaded_action_data.get('context', {}).get('_package', {}).get('meta', {}).get('type','action');
            if("children" in loaded_action_data and action_type == "interact_action") {
                ::py::
                def update_child_actions(child_action_list):
                    for i, child_action_data in enumerate(child_action_list):
                        action_type = child_action_data.get('context', {}).get('_package', {}).get('meta', {}).get('type','action');

                        if namespace_package_name := child_action_data.get('action', None):
                            if namespace_package_name in action_data_index:
                                child_action_list[i] = action_data_index[namespace_package_name]
                                # remove the child entry from action_data_index
                                del action_data_index[namespace_package_name]

                            # Handle child actions recursively
                            if "children" in child_action_data and action_type == "interact_action":
                                update_child_actions(child_action_data["children"])
                ::py::

                update_child_actions(loaded_action_data["children"]);
            }

            # update action data index with the loaded action data
            action_data_index[namespace_package_name] = loaded_action_data;

            # ALL ACTION DEPENDENCIES LOADED FOR THIS ACTION ?
            action_deps = loaded_action_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('actions', {});
            if( not self.has_action_dependencies(action_data_index, action_deps) ) {
                self.logger.error(f'missing action dependencies for {namespace_package_name}...skipping');
                # remove the entry from action_data_index if not
                del action_data_index[namespace_package_name];
                continue;
            }

            ## ALL GOOD, IMPORT THE ACTION LIB
            # if all deps installed successfully for this action, proceed to importing it in preparation for registration
            self.import_action(loaded_action_data);
        }

        ## REBUILD ACTION DATA LIST WITH ORIGINAL DESCRIPTOR ORDER
        loaded_action_list = [];
        for action_data in action_list {
            namespace_package_name = action_data.get('action');
            if( loaded_action_data := action_data_index.get(namespace_package_name)) {
                # refresh descriptor context data if present before adding to finalizing list
                action_entry = self.search_action_list(namespace_package_name, action_list);
                loaded_action_data['context'].update(action_entry.get('context', {}));
                # add to loaded action list
                loaded_action_list.append(loaded_action_data);
                # remove the entry in action_data_index
                del action_data_index[namespace_package_name];
            }
        }
        # add any remaining values from action_data_index to loaded action list
        # these may be deps which were not originally added to the descriptor
        loaded_action_list.extend(action_data_index.values());

        ## RETURN DESCRIPTOR, INTERACT ORDERED, FULLY LOADED ACTION LIST
        try {
            ordered_action_list = Utils.order_interact_actions(loaded_action_list);
            return ordered_action_list;
        } except Exception as e {
            self.logger.error('A dependency conflict was detected among configured actions. Unordered actions will be loaded but functionality may be impaired.');
            return loaded_action_list;
        }
    }

}

walker _get_actions {
    # retrieves a list of all actions and sub actions
    # must be spawned on agent or actions node or supplied with agent_id

    has action_nodes: list = [];
    has filter_enabled: bool = False;

    obj __specs__ {
        # all graph_walkers are private by default, unless overridden
        static has private: bool = True;
    }

    can on_actions with Actions entry {
        if(self.filter_enabled) {
            visit [-->](`?Action)(?enabled==True);
        } else {
            visit [-->](`?Action);
        }
    }

    can on_action with Action entry {
        # add the action node to the list
        self.action_nodes.append(here);
        # attempt to visit any child actions
        visit [-->](`?Action);
    }
}

walker _get_interact_actions {
    # retrieves a list of all interact actions and sub actions
    # must be spawned on agent or actions node or supplied with agent_id

    has action_nodes: list = [];
    has filter_enabled:bool = False;

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_actions with Actions entry {
        if(self.filter_enabled) {
            visit [-->](`?InteractAction)(?enabled==True);
        } else {
            visit [-->](`?InteractAction);
        }
    }

    can on_action with InteractAction entry {

        # add the action node to the list
        self.action_nodes.append(here);
        # attempt to visit any child actions
        visit [-->](`?InteractAction);
    }
}

