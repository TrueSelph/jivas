"""Create commands for the CLI tool."""

import os

import click

from jvcli import __supported__jivas__versions__  # type: ignore[attr-defined]
from jvcli.api import RegistryAPI
from jvcli.auth import load_token, save_token
from jvcli.utils import TEMPLATES_DIR, validate_name, validate_snake_case

TYPE_SUFFIX_MAP = {
    "action": "_action",
    "interact_action": "_interact_action",
    "vector_store_action": "_vector_store_action",
}


@click.group()
def create() -> None:
    """Group for creating resources like actions"""
    pass  # pragma: no cover


@create.command(name="action")
@click.option(
    "--name",
    prompt=True,
    callback=validate_snake_case,
    help="Name of the action (must be snake_case).",
)
@click.option(
    "--version", default="0.0.1", show_default=True, help="Version of the action."
)
@click.option(
    "--jivas_version",
    default=max(__supported__jivas__versions__),
    show_default=True,
    help="Version of Jivas.",
)
@click.option(
    "--description",
    default="No description provided.",
    help="Description of the action.",
)
@click.option(
    "--singleton",
    default=True,
    type=bool,
    show_default=True,
    help="Indicate if the action is singleton.",
)
@click.option(
    "--type",
    default="action",
    type=click.Choice(TYPE_SUFFIX_MAP.keys(), case_sensitive=False),
    show_default=True,
    help="Type of the action.",
)
@click.option(
    "--path",
    default="./actions",
    show_default=True,
    help="Directory to create the action folder in.",
)
@click.option(
    "--namespace",
    default=None,
    help="Namespace for the action. Defaults to the username in the token.",
)
def create_action(
    name: str,
    version: str,
    jivas_version: str,
    description: str,
    singleton: bool,
    type: str,
    path: str,
    namespace: str,
) -> None:
    """Create a new action with its folder, associated files, and an app folder."""

    # Retrieve the email from the token or set it as blank
    token = load_token()
    namespace = namespace or token.get("namespaces", {}).get("default", "anonymous")
    author = token.get("email", "unknown@example.com")

    suffix = TYPE_SUFFIX_MAP[type]
    if not name.endswith(suffix):
        name += suffix

    # Format the full action name with namespace
    full_name = f"{namespace}/{name}"

    # Generate class name (CamelCase)
    archetype = "".join(word.capitalize() for word in name.split("_"))

    # Validate the Jivas version
    if str(jivas_version) not in __supported__jivas__versions__:
        click.secho(
            f"Jivas version {jivas_version} is not supported. Supported versions are: {__supported__jivas__versions__}.",
            fg="red",
        )
        return

    # Prepare the template path
    template_path = os.path.join(
        TEMPLATES_DIR, jivas_version, "sourcefiles", "action_info.yaml"
    )
    if not os.path.exists(template_path):
        click.secho(
            f"Template for version {jivas_version} not found in {TEMPLATES_DIR}.",
            fg="red",
        )
        return

    # Prepare target folder
    namespace_dir = os.path.join(path, namespace)
    action_dir = os.path.join(namespace_dir, name)
    os.makedirs(action_dir, exist_ok=True)

    # Load and substitute YAML template
    with open(template_path, "r") as file:
        template = file.read()

    title = name.replace("_", " ").title()

    data = {
        "name": full_name,  # Include namespace in the package name
        "author": author,
        "archetype": archetype,
        "version": version,
        "title": title,
        "description": description,
        "group": "contrib",
        "type": type,
        "singleton": str(singleton).lower(),
        "jivas_version": jivas_version,
    }

    yaml_content = template
    for key, value in data.items():
        yaml_content = yaml_content.replace(f"{{{{{key}}}}}", str(value))

    # Write info.yaml
    yaml_path = os.path.join(action_dir, "info.yaml")
    with open(yaml_path, "w") as file:
        file.write(yaml_content)

    # Create lib.jac
    lib_path = os.path.join(action_dir, "lib.jac")
    lib_template_path = os.path.join(
        TEMPLATES_DIR, jivas_version, "sourcefiles", "action_lib.jac"
    )
    if not os.path.exists(lib_template_path):
        click.secho(
            f"Lib template for version {jivas_version} not found in {TEMPLATES_DIR}.",
            fg="red",
        )
        return

    with open(lib_template_path, "r") as file:
        lib_content = file.read()

    lib_data = {
        "namespace": namespace,
        "name": name,
        "imports": name,
    }

    for key, value in lib_data.items():
        lib_content = lib_content.replace(f"{{{{{key}}}}}", str(value))

    with open(lib_path, "w") as file:
        file.write(lib_content)

    # Create action-specific .jac file
    action_jac_path = os.path.join(action_dir, f"{name}.jac")
    if type == "action":
        action_template_path = os.path.join(
            TEMPLATES_DIR, jivas_version, "sourcefiles", "action_archetype.jac"
        )
    elif type == "interact_action":
        action_template_path = os.path.join(
            TEMPLATES_DIR, jivas_version, "sourcefiles", "interact_action_archetype.jac"
        )
    else:
        action_template_path = os.path.join(
            TEMPLATES_DIR, jivas_version, "sourcefiles", "action_archetype.jac"
        )

    if not os.path.exists(action_template_path):
        click.secho(
            f"Action template for version {jivas_version} not found in {TEMPLATES_DIR}.",
            fg="red",
        )
        return

    with open(action_template_path, "r") as file:
        node_content = file.read()

    action_data = {
        "archetype": archetype,
    }

    for key, value in action_data.items():
        node_content = node_content.replace(f"{{{{{key}}}}}", str(value))

    with open(action_jac_path, "w") as file:
        file.write(node_content.strip())

    # Create the 'app' folder and default 'app.py'
    app_dir = os.path.join(action_dir, "app")
    os.makedirs(app_dir, exist_ok=True)
    app_file_path = os.path.join(app_dir, "app.py")
    app_template_path = os.path.join(
        TEMPLATES_DIR, jivas_version, "sourcefiles", "action_app.py"
    )

    if not os.path.exists(app_template_path):
        click.secho(
            f"App template for version {jivas_version} not found in {TEMPLATES_DIR}.",
            fg="red",
        )
        return

    with open(app_template_path, "r") as file:
        app_code = file.read()

    app_code = app_code.replace("{{title}}", title)
    with open(app_file_path, "w") as app_file:
        app_file.write(app_code)

    create_docs(action_dir, title, version, "action", jivas_version, description)

    click.secho(
        f"Action '{name}' created successfully in {action_dir}!", fg="green", bold=True
    )


@create.command(name="namespace")
@click.option(
    "--name", prompt=True, callback=validate_name, help="Name of the namespace."
)
def create_namespace(name: str) -> None:
    """
    Create a new namespace through the API and update the local token file.

    name: The name of the new namespace to create.
    """
    # Load the token data
    token_data = load_token()
    if not token_data:
        click.secho(
            "You are not logged in. Please log in before creating a namespace.",
            fg="red",
        )
        return

    # Extract the token
    token = token_data.get("token")
    if not token:
        click.secho(
            "Token missing from the local configuration. Please log in again.", fg="red"
        )
        return

    # Call the API to create the namespace
    updated_namespaces = RegistryAPI.create_namespace(name, token)

    if updated_namespaces:

        # Fetch namespace object
        namespaces = token_data.get(
            "namespaces", {"default": "anonymous", "groups": []}
        )  # TODO: Remove default when API is updated

        if name not in namespaces["groups"]:
            namespaces["groups"].append(name)

        click.secho(f"Namespace '{name}' created successfully!", fg="green", bold=True)

        # Update the local token file with the new namespaces
        save_token(token, namespaces, str(token_data.get("email")))


@create.command(name="agent")
@click.option(
    "--name",
    prompt=True,
    callback=validate_snake_case,
    help="Name of the agent (must be snake_case).",
)
@click.option(
    "--version", default="0.0.1", show_default=True, help="Version of the agent."
)
@click.option(
    "--jivas_version",
    default=max(__supported__jivas__versions__),
    show_default=True,
    help="Version of Jivas.",
)
@click.option(
    "--description",
    default="A jivas agent autocreated by the jvcli.",
    help="Description of the agent.",
)
@click.option(
    "--path",
    default="./daf",
    show_default=True,
    help="Directory to create the agent.",
)
@click.option(
    "--namespace",
    default=None,
    help="Namespace for the agent. Defaults to the username in the token.",
)
def create_agent(
    name: str,
    version: str,
    jivas_version: str,
    description: str,
    path: str,
    namespace: str,
) -> None:
    """Create a new agent with its folder and associated files."""

    title = name.replace("_", " ").title()

    # Retrieve token info
    token = load_token()
    namespace = namespace or token.get("namespaces", {}).get("default", "anonymous")
    author = token.get("email", "unknown@example.com")

    # Validate Jivas version
    if str(jivas_version) not in __supported__jivas__versions__:
        click.secho(
            f"Jivas version {jivas_version} is not supported. Supported versions are: {__supported__jivas__versions__}.",
            fg="red",
        )
        return

    # Prepare paths
    namespace_dir = os.path.join(path, namespace)
    daf_dir = os.path.join(namespace_dir, name)
    os.makedirs(daf_dir, exist_ok=True)

    # Load templates
    template_paths = {
        "info.yaml": os.path.join(
            TEMPLATES_DIR, jivas_version, "sourcefiles", "agent_info.yaml"
        ),
        "descriptor.yaml": os.path.join(
            TEMPLATES_DIR, jivas_version, "sourcefiles", "agent_descriptor.yaml"
        ),
        "knowledge.yaml": os.path.join(
            TEMPLATES_DIR, jivas_version, "sourcefiles", "agent_knowledge.yaml"
        ),
        "memory.yaml": os.path.join(
            TEMPLATES_DIR, jivas_version, "sourcefiles", "agent_memory.yaml"
        ),
    }

    # Check if all templates exist
    for filename, template_path in template_paths.items():
        if not os.path.exists(template_path):
            click.secho(f"Template {filename} not found in TEMPLATES_DIR.", fg="red")
            return

    # Read templates
    templates = {}
    for key, path in template_paths.items():
        with open(path, "r") as file:
            templates[key] = file.read()

    # Replace placeholders
    data = {
        "name": f"{namespace}/{name}",
        "author": author,
        "version": version,
        "title": title,
        "description": description,
        "type": "agent",
        "jivas_version": jivas_version,
    }

    for filename, template_content in templates.items():
        for key, value in data.items():
            template_content = template_content.replace(f"{{{{{key}}}}}", str(value))

        with open(os.path.join(daf_dir, filename), "w") as file:
            file.write(template_content)

    # Create documentation
    create_docs(daf_dir, title, version, "agent", jivas_version, description)

    # Success message
    click.secho(
        f"Agent '{name}' created successfully in {daf_dir}!", fg="green", bold=True
    )


def create_docs(
    path: str,
    title: str,
    version: str,
    package_type: str,
    jivas_version: str,
    description: str = "",
) -> None:
    """Update README.md and CHANGELOG.md templates with name and version."""

    # Create README
    readme_template = os.path.join(
        TEMPLATES_DIR, jivas_version, "sourcefiles", "README.md"
    )
    if os.path.exists(readme_template):
        with open(readme_template, "r") as file:
            readme_content = file.read()

        readme_content = readme_content.replace("{{version}}", version)
        readme_content = readme_content.replace("{{title}}", title)
        readme_content = readme_content.replace("{{description}}", description)

        target_readme = os.path.join(path, "README.md")
        with open(target_readme, "w") as file:
            file.write(readme_content)

    # Create CHANGELOG
    changelog_template = os.path.join(
        TEMPLATES_DIR, jivas_version, "sourcefiles", "CHANGELOG.md"
    )
    if os.path.exists(changelog_template):
        with open(changelog_template, "r") as file:
            changelog_content = file.read()

        changelog_content = changelog_content.replace("{{version}}", version)
        changelog_content = changelog_content.replace("{{package_type}}", package_type)

        target_changelog = os.path.join(path, "CHANGELOG.md")
        with open(target_changelog, "w") as file:
            file.write(changelog_content)
