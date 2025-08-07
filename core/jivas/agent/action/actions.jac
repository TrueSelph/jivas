import io;
import os;
import re;
import subprocess;
import shutil;
import sys;
import types;
import yaml;
import logging;
import traceback;
import tarfile;
import requests;
import importlib.metadata;
import from typing { Union, Optional }
import from logging { Logger }
import from packaging.version { Version, parse as parse_version }
import from packaging.specifiers { SpecifierSet }

import from jivas.agent.modules.action.ordering { order_interact_actions }
import from jivas.agent.modules.action.path { find_package_folder }
import from jivas.agent.modules.action.path { path_to_module }
import from jivas.agent.modules.system.common { get_jivas_version }
import from jvserve.cli { reload_server }

import from jvcli.api { RegistryAPI }
import from jvcli.utils { is_version_compatible }
import from jaclang { JacMachine }
import from jac_cloud.core.archetype { BaseCollection, NodeAnchor }
import from jivas.agent.action.action { Action }
import from jivas.agent.action.interact_action { InteractAction }
import from jivas.agent.core.graph_node { GraphNode }
import from jivas.agent.action.exit_interact_action { ExitInteractAction }
import from jivas.agent.core.purge { purge }

node Actions(GraphNode) {
    #*
    Central node for managing agent actions including registration, loading, and execution.
    Maintains a collection of action nodes and provides utilities for action management.
    *#

    static has logger: Logger = logging.getLogger(__name__);

    def get(action_label: str = "", action_type: str = "", only_enabled: bool = True) -> Union[Action, list, None] {
        #*
        Returns an action by label or by type.

        Args:
            action_label: Unique identifier for the action
            action_type: Type of action to retrieve
            only_enabled: Whether to include only enabled actions

        Returns:
            Action if found by label, list of actions if found by type, None otherwise
        *#
        if not action_label and not action_type {
            return None;
        }

        if (action_type and not action_label) {
            return self.get_by_type(action_type, only_enabled);
        } else {
            return self.get_by_label(action_label, only_enabled);
        };
    }

    def get_by_label(action_label: str, only_enabled: bool = True) -> Action {
        #* Returns a single action by its label *#
        actions = self.get_all(only_enabled=only_enabled);
        return next((action for action in actions if action.label == action_label), None);
    }

    def get_by_type(action_type: str, only_enabled: bool = True) -> list {
        #* Returns all actions of a specific type *#
        return [action for action in self.get_all(only_enabled=only_enabled)
                if action_type == action.get_type()];
    }

    def get_all(only_interact_actions: bool = False, only_enabled: bool = False) -> list {
        #* Returns all actions, optionally filtered by type and enabled status *#
        if(only_interact_actions) {
           walker_obj = _get_interact_actions(filter_enabled=only_enabled);
        } else {
           walker_obj = _get_actions(filter_enabled=only_enabled);
        }

        return (self spawn walker_obj).action_nodes;
    }

    def queue_interact_actions(actions: list) -> list {
        #*
        Organizes interact actions in execution queue based on weights.

        Args:
            actions: List of InteractAction objects to queue

        Returns:
            Sorted list of actions by weight
        *#
        # Sort actions by their weight attribute without using a lambda
        def get_weight(action: InteractAction) -> int {
            return action.weight;
        }

        return sorted(actions, key=get_weight);
    }

    def get_action_info(namespace_package_name: str, version: str = None, jpr_api_key: str = None) -> dict {
        #*
        Retrieves action package info either locally or from package registry.

        Args:
            namespace_package_name: Namespace/package format identifier
            version: Version requirement string
            jpr_api_key: API key for registry access

        Returns:
            Dictionary containing package info or empty dict if not found
        *#
        (namespace, package_name) = namespace_package_name.split('/');
        action_info = self.get_local_action_info(namespace_package_name, version) or
                     self.get_remote_action_info(namespace_package_name, version, jpr_api_key);

        if action_info {
            action_info['config']['namespace'] = namespace;
            action_info['config']['package_name'] = package_name;
        }
        return action_info;
    }

    def :priv get_local_action_info(namespace_package_name: str, version: str) -> dict {
        #* Helper to get action info from local filesystem *#
        if not (package_path := find_package_folder(self.get_actions_root(), namespace_package_name)) {
            return {};
        }

        info_yaml_path = os.path.join(package_path, 'info.yaml');
        try {
            with open(info_yaml_path, 'r') as file {
                _info = yaml.safe_load(file);
                package_version = _info.get('package', {}).get('version', '~0.0.1');

                if is_version_compatible(package_version, version) {
                    self.logger.info(f'{namespace_package_name} {package_version} loaded locally');
                    module_root = path_to_module(package_path);
                    has_app = os.path.isfile(os.path.join(package_path, 'app', 'app.py'));

                    action_info = _info['package'];
                    action_info['config'].update({
                        'path': package_path,
                        'app': has_app,
                        'module_root': module_root,
                        'module': f"{module_root}.{namespace_package_name.split('/')[-1]}"
                    });
                    return action_info;
                }
            }
        } except (yaml.YAMLError, IOError) as e {
            self.logger.error(f"Error loading local action info: {traceback.format_exc()}");
        }
        return {};
    }

    def :priv get_remote_action_info(namespace_package_name: str, version: str, jpr_api_key: str) -> dict {
        #* Helper to get action info from remote registry *#
        if _info := RegistryAPI.get_package_info(namespace_package_name, version, api_key=jpr_api_key) {
            self.logger.info(f'{namespace_package_name} {version} found in registry');
            return _info.get('package', {});
        }
        return {};
    }

    def import_action(action_data: dict) -> bool {
        #*
        Imports the action module into the JacMachine.

        Args:
            action_data: Dictionary containing action configuration

        Returns:
            True if import succeeded, False otherwise
        *#
        module_root = action_data.get('context', {}).get('_package', {}).get('config', {}).get('module_root');

        if not module_root {
            return False;
        }

        module_name = f"{module_root}.lib";
        try {
            JacMachine.jac_import(target=module_name, base_path="./", reload_module=True);
            return True;
        } except Exception as e {
            self.logger.error(f"Unable to load module {module_name}: {e}");
            return False;
        }
    }

    def register_action(action_data: dict, parent: str = "") -> Optional[Action] {
        #*
        Registers an action with the agent.

        Args:
            action_data: Dictionary containing action configuration
            parent: Optional parent action type

        Returns:
            Registered Action node or None if failed
        *#
        if not action_data {
            self.logger.error("Unable to register action, missing or invalid action data");
            return None;
        }

        context = action_data.get('context', {});
        package = context.get('_package', {});
        config = package.get('config', {});
        meta = package.get('meta', {});

        label = context.get('label', action_data.get('action'));
        archetype = package.get('archetype');
        module = config.get('module');
        singleton = config.get('singleton', False);
        action_type = meta.get('type', 'action');

        if not all([archetype, module, label]) {
            self.logger.error(f"Unable to register action {label or ''} - missing required fields");
            return None;
        }

        try {
            # Check for existing action
            if singleton and self.get(action_type=label, only_enabled=False) {
                self.logger.error(f"Singleton action already exists: {label}");
                return None;
            } elif not singleton and self.get(action_label=label, only_enabled=False) {
                self.logger.error(f"Action already exists: {label}");
                return None;
            }

            if not JacMachine.loaded_modules.get(module) {
                raise ValueError(f"Unable to spawn: {archetype}, module not loaded.");
            }

            # Spawn and configure action node
            action_node = JacMachine.spawn_node(node_name=archetype, module_name=module);
            if not action_node {
                raise ValueError(f"Unable to spawn: {archetype}");
            }

            # Update node attributes
            for (attr, value) in context.items() {
                if hasattr(action_node, attr) {
                    setattr(action_node, attr, value);
                } else {
                    action_node._context[attr] = value;
                }
            }

            # Connect to parent
            action_parent_node = self if not parent else self.get_by_type(action_type=parent, only_enabled=False);
            action_parent_node ++> action_node;

            # Initialize action
            action_node.on_register();
            self.logger.info(f"Registered action: {action_node.label}");

            # Handle child actions
            if "children" in action_data and action_type == 'interact_action' {
                for child_data in action_data["children"] {
                    self.register_action(action_data=child_data, parent=archetype);
                }
            }

            return action_node;
        } except Exception as e {
            self.logger.error(f"Error registering action {label}: {traceback.format_exc()}");
            return None;
        }
    }

    def install_actions(agent_id: str, action_list: list, jpr_api_key: str = None, clean_actions: bool = False) -> bool {
        #*
        Installs and registers a list of actions.

        Args:
            agent_id: Identifier for the agent
            action_list: List of action descriptors
            jpr_api_key: API key for registry access

        Returns:
            True if installation succeeded, False otherwise
        *#
        if not agent_id or not (loaded_actions_data := self.load_actions(agent_id, action_list, jpr_api_key)) {
            self.logger.error('No actions loaded; unable to proceed with import');
            return False;
        }

        # Clean slate installation
        self.deregister_actions(clean_actions=clean_actions);

        # Register all actions
        for action_data in loaded_actions_data {
            self.register_action(action_data=action_data);
        }

        # Add system exit action
        self ++> ExitInteractAction();

        # Post-registration setup
        for action_node in self.get_all() {
            action_node.post_register();
        }

        return True;
    }

    def reload_actions() -> bool {
        #*
        Reloads all registered actions from the database.

        Returns:
            True if all actions imported successfully, False if any import failed
            (continues processing all actions regardless of individual failures)
        *#
        source = jid(self);
        edge_ids = [i.id for i in self.__jac__.edges];
        all_success = True;

        action_nodes = [
            NodeAnchor.ref(anchor_ref).archetype
            for ed in BaseCollection.get_collection("edge").find({"_id": {"$in": edge_ids}})
            if (anchor_ref := ed["target"] if ed["source"] == source else None) is not None
        ];

        # Process all actions
        for action_node in action_nodes {

            action_data = {"context": action_node.__dict__};
            # skip over ExitInteractAction
            if action_data.get('context', {}).get('label', '') == 'ExitInteractAction' {
                continue;
            }
            pip_deps = action_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('pip', {});

            # Install dependencies if they exist and have not been installed
            if pip_deps and not self.has_pip_packages(pip_deps) {
                self.batch_pip_package_install(pip_deps);
            }

            # Attempt import and track success
            if not self.import_action(action_data) {
                all_success = False;
                self.logger.error(f"Failed to import action: {action_node.label}");
            } else {
                # call on_load method on action to reinit
                # (&(action_node.id)).on_register();
            }



        }

        return all_success;
    }

    def deregister_action(action_type: str = "", action_label: str = "", clean_action: bool=False) {
        #*
        Deregisters a specific action by type or label.

        Args:
            action_type: Type of action to deregister
            action_label: Label of action to deregister
        *#
        if (action_type and not action_label) {
            targets = self.get_by_type(action_type, only_enabled=False);
        } else {
            targets = [self.get_by_label(action_label, only_enabled=False)] if action_label else [];
        }

        for action_node in targets {
            if action_node {
                # call on_deregister
                action_node.on_deregister();
                # remove from graph
                action_node spawn purge();
                # remove package folder if clean action is set
                if clean_action {
                    package_path = action_node._package.get('config', {}).get('path');
                    if package_path and os.path.exists(package_path) {
                        try {
                            shutil.rmtree(package_path);
                        } except Exception as e {
                            self.logger.error(f"Error removing action package: {e}");
                        }
                    }
                }
            }
        }
    }

    def deregister_actions(clean_actions: bool = False) {
        #* Deregisters all actions and optionally removes the package folder if clean_actions is set *#
        all_actions = self.get_all();
        # call on_deregister on all actions
        for action_node in all_actions {
            action_node.on_deregister();
        }
        # purge them from the graph
        self spawn purge(purge_spawn_node=False);
        # finally remove their packages from filesystem if clean actions is set
        if clean_actions {
            for action_node in all_actions {
                # Clean up module files
                package_path = action_node._package.get('config', {}).get('path');
                if package_path and os.path.exists(package_path) {
                    try {
                        shutil.rmtree(package_path);
                    } except Exception as e {
                        self.logger.error(f"Error removing action package: {e}");
                    }
                }
            }
        }
    }

    # Utility Methods
    def search_action_list(namespace_package_name: str, action_list: list) -> dict {
        #* Searches action list for specific package *#
        return next((action for action in action_list
                    if action.get('action') == namespace_package_name), {});
    }

    def index_action_packages(agent_id: str, action_list: list, action_index: dict = {}, jpr_api_key: str = "") -> dict {
        #*
        Recursively indexes action packages and their dependencies.

        Args:
            agent_id: Agent identifier
            action_list: List of action descriptors
            action_index: Accumulator for indexed actions
            jpr_api_key: API key for registry access

        Returns:
            Dictionary of indexed actions
        *#
        for action_data in action_list {
            namespace_package_name = action_data.get('action');
            package_version = action_data.get('context', {}).get('version', '~0.0.1');

            if not namespace_package_name or namespace_package_name in action_index {
                continue;
            }

            if action_info := self.get_action_info(namespace_package_name, package_version, jpr_api_key) {
                # Prepare action data
                context = action_data.get('context', {});
                context.update({
                    'agent_id': agent_id,
                    '_package': action_info,
                    'label': context.get('label', action_info.get('archetype')),
                    'description': action_info.get('meta', {}).get('description', '')
                });

                # Handle dependencies
                if action_deps := action_info.get('dependencies', {}).get('actions', {}) {
                    dep_list = [{
                        "action": dep,
                        "context": {"version": ver, "enabled": True}
                    } for (dep, ver) in action_deps.items()];

                    action_index = self.index_action_packages(
                        agent_id, dep_list, action_index, jpr_api_key
                    );

                    ::py::
                    if not all(key in action_index.keys() for key in action_deps.keys()):
                        continue
                    ::py::
                }

                # Handle children
                if "children" in action_data {
                    action_index = self.index_action_packages(
                        agent_id, action_data["children"], action_index, jpr_api_key
                    );
                }

                # Add to index
                action_index[namespace_package_name] = action_data;
            } else {
                self.logger.error(f"Unable to find action {namespace_package_name} {package_version}");
            }
        }
        return action_index;
    }

    def index_pip_packages(action_data_index: dict) -> dict {
        #* Creates index of pip dependencies across all actions *#
        pip_index = {};
        for action_data in action_data_index.values() {
            pip_deps = action_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('pip', {});
            pip_index.update(pip_deps);
        }
        return pip_index;
    }

    def batch_pip_package_install(packages: dict) {
        #*
        Installs multiple pip packages with version requirements.

        Args:
            packages: Dictionary of {package: version_spec} pairs
        *#
        package_specs = [];
        for (pkg, ver) in packages.items() {
            if not ver {
                package_specs.append(pkg);
            } elif not re.match(r'^(==|>=|<=|>|<|~=|!=)', ver) {
                package_specs.append(f"{pkg}=={ver}");
            } else {
                package_specs.append(f"{pkg}{ver}");
            }
        }

        if not package_specs {
            return;
        }

        command = [sys.executable, "-m", "pip", "install", "--upgrade", "--no-input", *package_specs];
        self.logger.info(f"Installing package dependencies: {package_specs}");

        try {
            subprocess.run(command, check=True, stderr=None, stdout=None);
            self.logger.info("Package dependencies installed successfully.");
        } except subprocess.CalledProcessError as e {
            self.logger.error("Error installing package dependencies.");
        }
    }

    def has_pip_package(package_name: str, version: str = None) -> bool {
        #*
        Checks if a pip package is installed with optional version requirement.

        Args:
            package_name: Name of package to check
            version: Optional version requirement

        Returns:
            True if package meets requirements, False otherwise
        *#
        try {
            installed_version = importlib.metadata.version(package_name);
            if not version {
                return True;
            }

            if not re.match(r'^(==|>=|<=|>|<|~=|!=)', version) {
                version = f"=={version}";
            }

            return Version(installed_version) in SpecifierSet(version);
        } except Exception as e {
            return False;
        }
    }

    def has_pip_packages(packages: dict) -> bool {
        #* Checks if multiple pip packages are installed with version requirements *#
        return all([self.has_pip_package(pkg, ver) for (pkg, ver) in packages.items()]);
    }

    def has_action_dependencies(action_data_index: dict, action_dependencies: dict) -> bool {
        #* Checks if all action dependencies are satisfied *#
        return all([key in action_data_index.keys() for key in action_dependencies.keys()]);
    }

    def load_action_package(indexed_action_data: dict, jpr_api_key: str = "") -> dict {
        #*
        Loads an action package either from local storage or remote registry.

        Args:
            indexed_action_data: Action descriptor with package info
            jpr_api_key: API key for registry access

        Returns:
            Updated action data or empty dict if failed
        *#
        context = indexed_action_data.get('context', {});
        package = context.get('_package', {});
        config = package.get('config', {});

        namespace_package_name = package.get('name');
        package_version = context.get('version', '~0.0.1');
        required_jivas_version = package.get('dependencies', {}).get('jivas');
        jivas_version = get_jivas_version();

        # Version check
        if not is_version_compatible(jivas_version, required_jivas_version) {
            self.logger.error(
                f"Incompatible JIVAS version for {namespace_package_name} "
                f"(required: {required_jivas_version}, system: {jivas_version})"
            );
            return {};
        }

        # Download package if not local
        if not config.get('path') and not self.download_action_package(namespace_package_name, package_version, jpr_api_key) {
            return {};
        }

        # Refresh package info
        if refreshed_info := self.get_action_info(namespace_package_name, package_version, jpr_api_key) {
            context['_package'] = refreshed_info;
            return indexed_action_data;
        }

        return {};
    }

    def :priv download_action_package(namespace_package_name: str, version: str, jpr_api_key: str) -> bool {
        #* Downloads and extracts action package from registry *#
        if not (package_data := RegistryAPI.download_package(namespace_package_name, version, api_key=jpr_api_key)) {
            return False;
        }

        try {
            response = requests.get(package_data["file"]);
            target_dir = os.path.join(self.get_actions_root(), namespace_package_name);
            os.makedirs(target_dir, exist_ok=True);

            with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar {
                tar.extractall(target_dir);
            }

            self.logger.info(f"Downloaded action package: {namespace_package_name} {version}");
            return True;
        } except Exception as e {
            self.logger.error(f"Error downloading package {namespace_package_name}: {e}");
            return False;
        }
    }

    def load_actions(agent_id: str, action_list: list, jpr_api_key: str = None) -> list {
        #*
        Main method for loading actions and their dependencies.

        Args:
            agent_id: Agent identifier
            action_list: List of action descriptors
            jpr_api_key: API key for registry access

        Returns:
            List of loaded action data in execution order
        *#
        # Index and order all actions
        action_index = self.index_action_packages(agent_id, action_list, jpr_api_key=jpr_api_key);
        if not action_index {
            return [];
        }

        # Install system and package dependencies
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--root-user-action=ignore"]);
        self.batch_pip_package_install(self.index_pip_packages(action_index));

        # Process each action
        action_index_copy = action_index.copy();
        for (namespace, action_data) in action_index_copy.items() {
            loaded_data = self.load_action_package(action_data, jpr_api_key);
            if not loaded_data {
                del action_index[namespace];
                continue;
            }

            # Check dependencies
            pip_deps = loaded_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('pip', {});
            action_deps = loaded_data.get('context', {}).get('_package', {}).get('dependencies', {}).get('actions', {});

            if not self.has_pip_packages(pip_deps) or not self.has_action_dependencies(action_index, action_deps) {
                self.logger.error(f"Dependency check failed for {namespace}");
                del action_index[namespace];
                continue;
            }

            # Handle children
            if "children" in loaded_data and loaded_data.get('context', {}).get('_package', {}).get('meta', {}).get('type') == "interact_action" {
                ::py::
                def update_children(children):
                    for i, child in enumerate(children):
                        if child_name := child.get('action'):
                            if child_name in action_index:
                                children[i] = action_index[child_name]
                                del action_index[child_name]
                            if "children" in child:
                                update_children(child["children"])
                ::py::
                update_children(loaded_data["children"]);
            }

            # Import action
            self.import_action(loaded_data);
            action_index[namespace] = loaded_data;
        }

        # Rebuild original order
        loaded_actions = [];
        for action_data in action_list {
            if loaded_data := action_index.pop(action_data.get('action'), None) {
                loaded_data['context'].update(action_data.get('context', {}));
                loaded_actions.append(loaded_data);
            }
        }

        # Add any remaining actions (dependencies not in original list)
        loaded_actions.extend(action_index.values());

        # Return ordered list
        try {
            return order_interact_actions(loaded_actions);
        } except Exception as e {
            self.logger.error('Dependency conflict detected - loading unordered actions');
            return loaded_actions;
        }
    }

    def get_actions_root() -> str {
        #* Returns the root directory for action packages *#
        path = os.environ.get('JIVAS_ACTIONS_ROOT_PATH', 'actions');
        os.makedirs(path, exist_ok=True);
        return path;
    }

}

# Private Walkers
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
