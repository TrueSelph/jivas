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
import:py from logging { Logger }
import:py from jaclang { jac_import }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:py from jvcli.api { RegistryAPI }
import:py from jvcli.utils { is_version_compatible }
import:py from jvserve.lib.agent_interface { AgentInterface }
import:jac from action { Action }
import:jac from interact_action { InteractAction }
import:jac from interact_graph_walker { interact_graph_walker }
import:jac from jivas.agent.core.graph_node { GraphNode }
import:jac from exit_interact_action { ExitInteractAction }

node Actions :GraphNode: {

    # set up logger
    static has logger: Logger = logging.getLogger(__name__);
    # action packages root folder
    static has package_root: str = Utils.get_actions_root();

    can get(action_type: str="", action_label: str="") {
        # returns an action by label or by type

        result = None;

        if action_type and not action_label {
            # there can be multiple actions of the same type, this returns a list
            result = self.get_by_type(action_type);
        } elif action_label and not action_type {
            # there can only be one action with a particular label, this returns a action
            result = self.get_by_label(action_label);
        }

        return result;
    }

    can get_by_label(action_label: str) -> Action {
        # returns an action by label
        for action_node in self.get_all() {
            if (action_node.label == action_label) {
                return action_node;
            }
        }

        return None;
    }

    can get_by_type(action_type: str) -> list {
        # returns an action by type; there may be multiple instances of the same action so a list is returned

        result = [];
        for action_node in self.get_all() {
            if (action_type == action_node.get_type()) {
                result.append(action_node);
            }
        }

        return result;
    }

    can get_all(filter_interact_actions:bool=False, filter_enabled_actions:bool=False) -> list {
        # returns a list of all actions, even nested ones
        if (filter_interact_actions) {
            return ((self spawn _get_interact_actions(filter_enabled=filter_enabled_actions)).action_nodes);
        }
        return ((self spawn _get_actions(filter_enabled=filter_enabled_actions)).action_nodes);
    }

    can queue_interact_actions(actions:list) -> list {
        # accepts a list of interact actions and organizes them in an execution queue
        # based on weights and precedence specified in _package.config.order

        # this is the Jaclang equivalent of a lamda function
        # return sorted(objects, key=lambda InteractAction:obj.weight)
        return sorted(actions, key = with action:InteractAction can action.weight );
    }

    can get_action_info(namespace_package_name:str, version:str=None, jpr_api_key:str=None) {
        # retrieves the info.yaml data for a named action by version either locally first or on package manager

        action_info = None;

        # extract the namespace, package name
        (namespace, package_name) = namespace_package_name.split('/');
        # attempt to find the package locally, first...
        if (package_path := Utils.find_package_folder(self.package_root, namespace_package_name) ) {

            info_yaml_path = os.path.join(package_path, 'info.yaml');

            with open(info_yaml_path, 'r') as file {
                try  {
                    # load the action info content
                    _info = yaml.safe_load(file);
                    # grab info package version
                    package_version = _info.get('package', {}).get('version', None);

                    # validate the version
                    if is_version_compatible(package_version, version) {
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
                } except yaml.YAMLError as e {
                    self.logger.error(
                        f"an exception occurred, {traceback.format_exc()}"
                    );
                }
            }
        }

        if(not action_info) {

            # if no action_info found locally, we fetch from package repo
            self.logger.info(f'attempting to fetch action info remotely for {namespace_package_name} {version}');

            if( _info := RegistryAPI.get_package_info(namespace_package_name, version, api_key=jpr_api_key) ) {

                self.logger.info(f'found action info remotely for {namespace_package_name} {version}');
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

    can import_action(action_data:dict) {
        # prepares the module path to lib.jac and imports the module
        module_root = action_data.get('context', {}).get('_package', {}).get('config', {}).get('module_root', None);

        if(module_root) {
            jac_import(f"{module_root}.lib", base_path="./");
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
                if (existing_action := self.get(action_type=label)) {
                    self.logger.error(f"action already exists: {label}");
                    return None;
                }
            } elif (existing_action := (self.get(action_label=label))) {
                # check if non singleton action has unique label
                self.logger.error(f"action already exists: {existing_action.label}");
                return None;
            }

            # register action
            # TODO: add a check here before node register in cases where this is an init
            # and the node architype props changed compared to saved descriptor
            self.logger.info(f"Registering action {label} with architype {architype} from module {module}");
            action_node = AgentInterface.spawn_node(
                node_name=architype,
                attributes=action_data.get('context', {}),
                module_name=module
            );

            # at this point all architypes related to this action are registered, let's map
            if (action_node) {
                # get action parent node
                if (not parent) {
                    action_parent_node = self;
                } else {
                    action_parent_node = self.get_by_type(action_type=parent);
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

    can install_actions(agent_id:str, data: dict, jpr_api_key:str=None) {
        # accepts the list of action data and related configurations and coordinates the importation and registration of action packages
        loaded_actions_data = None;

        if(agent_id) {
            loaded_actions_data = self.load_action_packages(agent_id, data, jpr_api_key=jpr_api_key);
        }

        # if actions data is empty, quit right here with error
        if(not loaded_actions_data) {
            self.logger.error('no actions loaded; unable to proceed with actions install');
            return None;
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
    }

    can deregister_action(action_type: str="", action_label: str="") {
        # gracefully disposes of each action, calling the on_deregister on each action node before destruction
        # can perform deregistration by type or by label

        target = [];

        if action_type and not action_label {
            target = self.get_by_type(action_type);
        } elif action_label and not action_type {
            target.append(self.get_by_label(action_label));
        }
        for action_node in target {
            action_node.on_deregister();
            # TODO: remove the action module folder and related modules
            Jac.destroy(action_node);
        }

    }

    can deregister_actions() {
        # gracefully disposes of each action, calling the on_deregister on each action node before destruction
        for action_node in self.get_all() {
            action_node.on_deregister();
            # TODO: remove the action module folder and related modules
            Jac.destroy(action_node);
        }
    }

    # UTILS

    can index_action_data(data:dict) {
        # returns a flat dictionary of action data where the key is the action package name and value is the action data
        action_data_index = {};

        ::py::

        def flatten_actions(action_list):
            for action_data in action_list:
                if namespace_package_name := action_data.get('action', None):
                    action_data_index[namespace_package_name] = action_data

                    # Handle child actions recursively
                    if "children" in action_data:
                        flatten_actions(action_data["children"])

        # Start the flattening with the top-level data
        flatten_actions(data)

        ::py::

        return action_data_index;
    }

    can index_pip_packages(indexed_action_data:dict) {
        # returns a flat dictionary of pip packages where the key is the package name and value is the package version
        pip_packages_index = {};

        for (namespace_package_name, action_data) in indexed_action_data.items() {
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

    can has_pip_packages(packages:dict) {
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

    can has_pip_package(package_name:str, version:str=None) {
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

    can load_action_packages(agent_id:str, data: dict, jpr_api_key:str=None) {
        # accepts an agent descriptor listing of actions, prepares a loading manifest of ordered deps, loads them and returns loaded action data

        # grab flattened list of action data indexed by namespace package name
        action_data_index = self.index_action_data(data);

        try {

            # make a working copy to iterate thru
            action_data_index_copy = action_data_index.copy();
            # go through index and load up package info and dependencies
            for (namespace_package_name, action_data) in action_data_index_copy.items() {

                (namespace, package_name) = namespace_package_name.split('/');
                package_version = action_data.get('context', {}).get('version', None);

                if( action_info := self.get_action_info(namespace_package_name, package_version, jpr_api_key) ) {

                    action_data['context']['_package'] = action_info;
                    action_data['context']['agent_id'] = agent_id;
                    # grab the action architype name
                    architype = action_info.get('architype', None);
                    # label, if set will be used, otherwise use architype
                    action_data['context']['label'] = action_data.get('context', {}).get('label', architype);
                    # apply the description in the info file to the action entry
                    action_data['context']['description'] = action_info.get('meta', {}).get('description', '');

                    # if action dependencies exist, check and load as needed
                    action_deps = action_info.get('dependencies', {}).get('actions', {});

                    loaded_action_deps = {};

                    for action_dep in action_deps.keys() {
                        if action_dep not in action_data_index.keys() {
                            action_dep_version = action_deps[action_dep];

                            if( dep_action_info := self.get_action_info( action_dep, action_dep_version, jpr_api_key )) {
                                # add action descriptor entry based on dep action info
                                loaded_action_deps[action_dep] = {
                                    "action": action_dep,
                                    "context": {
                                        "version": action_dep_version,
                                        "enabled": True,
                                        "agent_id": agent_id,
                                        "_package": dep_action_info,
                                        "label": dep_action_info.get('architype', None),
                                        "description": dep_action_info.get('meta', {}).get('description', '')
                                    }
                                };
                            } else {
                                self.logger.error(f"unable to find action {action_dep} {action_dep_version}");
                                continue;
                            }
                        }
                    }
                    # add loaded deps to the action data index
                    action_data_index.update(loaded_action_deps);
                    # update the action_data on the corresponding index key
                    action_data_index[namespace_package_name] = action_data;

                } else {
                    # if we were unable to successfully get info and load a package on index, remove it
                    if(namespace_package_name in action_data_index) {
                        # remove the issue index so it is not loaded
                        del action_data_index[namespace_package_name];
                        # raise the error
                        self.logger.error(f"unable to find action {namespace_package_name} {package_version}");
                        continue;
                    }
                }
            }

        } except ImportError as e {
            self.logger.error(
                f"an exception occurred wile loading action, {traceback.format_exc()}"
            );
        }

        # now that action data index is loaded, we proceed to
        # download and load what's needed, which includes action and pip packages

        # make sure we upgrade pip before we proceed
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--root-user-action=ignore"]);

        # preprocess all pip depenedencies and install them in batch
        indexed_pip_packages = self.index_pip_packages(action_data_index);
        self.batch_pip_package_install(indexed_pip_packages);

        # make a working copy to iterate thru
        action_data_index_copy = action_data_index.copy();
        for (namespace_package_name, action_data) in action_data_index_copy.items() {

            package_path = action_data.get('context', {}).get('_package', {}).get('config', {}).get('path', None);
            # if an action package is already downloaded, there will be a 'path' variable in the '_package' key
            # if not, we need to download it and refresh the _package values
            if package_path is None {

                package_version = action_data.get('context', {}).get('version', None);

                try {
                    self.logger.info(f'attempting to download action for {namespace_package_name} {package_version}');
                    # download package from package repo
                    package_data = RegistryAPI.download_package(namespace_package_name, package_version, api_key=jpr_api_key);

                    if not package_data {
                        # remove the entry from the index
                        if(namespace_package_name in action_data_index) {
                            del action_data_index[namespace_package_name];
                        }
                        self.logger.error(f'unable to download package {namespace_package_name} {package_version} ...skipping');
                        continue;
                    }

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

                    # attempt to refresh and replace action _package data
                    if( action_info := self.get_action_info(namespace_package_name, package_version, jpr_api_key) ) {

                        action_data['context']['_package'] = action_info;
                        if( not action_info.get('config', {}).get('path', None) ) {
                            # if download and reload unsuccessful,
                            # remove the entry from the index
                            if(namespace_package_name in action_data_index) {
                                del action_data_index[namespace_package_name];
                            }
                            # report and skip to next item
                            self.logger.error(f'unable to download package {namespace_package_name}...skipping');
                            continue;
                        }

                    }
                } except Exception as e {
                    # remove the entry from the index
                    if(namespace_package_name in action_data_index) {
                        del action_data_index[namespace_package_name];
                    }
                    self.logger.error(f'unable to download and load package {namespace_package_name}...skipping, {e}');
                    continue;
                }

            }

            # now we load the pip packages that aren't loaded
            if(self.has_pip_packages( action_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('pip', {}) )) {
                # once successful, we import the action modules into runtime
                self.import_action(action_data);
            } else {
                # if we were unable to successfully load a package on index, remove it from the index and report
                if(namespace_package_name in action_data_index) {
                    # remove the issue index so it is not loaded
                    del action_data_index[namespace_package_name];
                    # raise the error
                    self.logger.error(f"unable to load pip packages for action {namespace_package_name}");
                    continue;
                }
            }
        }

        # at this point, our action_data_index only contains all successfully loaded actions
        # we update the corresponding children and remove the top level dups

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

        # make a working copy to iterate thru
        action_data_index_copy = action_data_index.copy();
        # handle child actions many levels deep
        for (namespace_package_name, action_data) in action_data_index_copy.items() {
            action_type = action_data.get('context', {}).get('_package', {}).get('meta', {}).get('type','action');

            if("children" in action_data and action_type == "interact_action") {
                update_child_actions(action_data["children"]);
            }
        }

        # assign ordering weights to all interact actions then return
        return Utils.order_interact_actions(action_data_index.values());
    }

    can healthcheck() {
        # performs agent healthcheck; triggers the healthcheck ability of all actions on an agent
        # this is a wrapper for the _healthcheck_actions walker

        self.logger.info("performing agent healthcheck");
        return ((self spawn _healthcheck_actions()).trace);
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

walker _healthcheck_actions {
    # performs agent healthcheck; triggers the healthcheck ability of all actions on an agent

    has trace:dict = {};

    obj __specs__ {
        # make this a private walker
        static has private: bool = True;
    }

    can on_actions with Actions entry {
        # head to action
        visit [-->](`?Action)(?enabled==True);
    }

    can on_action with Action entry {
        # trigger healthcheck ability
        self.trace[here.label] = here.healthcheck();;
    }

}

