"""Start project command."""

import os

import click

from jvcli import __supported__jivas__versions__
from jvcli.utils import TEMPLATES_DIR


@click.command()
@click.argument("project_name")
@click.option(
    "--version",
    default=max(__supported__jivas__versions__),
    show_default=True,
    help="Jivas project version to use for scaffolding.",
)
@click.option(
    "--no-env",
    is_flag=True,
    default=False,
    help="Skip generating the .env file.",
)
def startproject(project_name: str, version: str, no_env: bool) -> None:
    """
    Initialize a new Jivas project with the necessary structure.

    Usage:
        jvcli startproject <project_name> [--version <jivas_version>] [--no-env]
    """

    template_path = os.path.join(TEMPLATES_DIR, version, "project")

    if not os.path.exists(template_path):
        click.secho(f"Template for Jivas version {version} not found.", fg="red")
        return

    project_structure: dict = {
        "tests": [],
        "actions": [],
        "daf": [],
    }

    try:
        print(f"Creating project: {project_name} (Version: {version})")
        os.makedirs(project_name, exist_ok=True)

        # Create directories
        for folder in project_structure.keys():
            os.makedirs(os.path.join(project_name, folder), exist_ok=True)

        # Copy template files and folders from the selected version
        for root, dirs, files in os.walk(template_path):
            relative_path = os.path.relpath(root, template_path)
            target_dir = os.path.join(project_name, relative_path)

            # Create directories
            for dir_name in dirs:
                os.makedirs(os.path.join(target_dir, dir_name), exist_ok=True)

            # Copy files
            for file_name in files:
                template_file_path = os.path.join(root, file_name)
                target_file_path = os.path.join(target_dir, file_name)

                with open(template_file_path, "r") as template_file:
                    contents = template_file.read()

                if file_name == "gitignore.example":
                    # Write `.gitignore`
                    target_file_path_gitignore = os.path.join(target_dir, ".gitignore")
                    with open(target_file_path_gitignore, "w") as gitignore_file:
                        gitignore_file.write(contents)

                if file_name == "env.example":
                    # Write `.env` only if no-env flag is not set
                    if not no_env:
                        target_file_path_env = os.path.join(target_dir, ".env")
                        with open(target_file_path_env, "w") as env_file:
                            env_file.write(contents)

                    # Always write `env.example`
                    target_file_path_example = os.path.join(target_dir, "env.example")
                    with open(target_file_path_example, "w") as example_file:
                        example_file.write(contents)

                with open(target_file_path, "w") as project_file:
                    project_file.write(contents)

        click.secho(
            f"Successfully created Jivas project: {project_name} (Version: {version}){' (without .env file)' if no_env else ''}",
            fg="green",
        )

    except Exception as e:
        click.secho(f"Error creating project: {e}", fg="red")
