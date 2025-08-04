"""Publish command group for the Jivas Package Repository CLI."""

import os
import tempfile

import click
from pyaml import yaml

from jvcli.api import RegistryAPI
from jvcli.auth import load_token
from jvcli.utils import (
    compress_package_to_tgz,
    validate_dependencies,
    validate_package_name,
    validate_yaml_format,
)


# Main `publish` group command
@click.group()
def publish() -> None:
    """
    Publish resources to the Jivas environment.
    Available subcommands: action, agent.
    """
    pass  # pragma: no cover


@publish.command(name="action")
@click.option(
    "--path",
    required=True,
    help="Path to the directory containing the action to publish.",
)
@click.option(
    "--visibility",
    type=click.Choice(["public", "private"], case_sensitive=False),
    default="public",
    show_default=True,
    help="Visibility of the published action (public or private).",
)
@click.option(
    "--package-only",
    is_flag=True,
    default=False,
    show_default=True,
    help="Only generate the package without publishing.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    required=False,
    help="Output path for generated package.",
)
@click.option(
    "--namespace",
    required=False,  # Initially not required
    help="Namespace of the package (required when --path is a tarball).",
)
def publish_action(
    path: str, visibility: str, package_only: bool, output: str, namespace: str
) -> None:
    """Publish an action to the Jivas environment."""

    if path.endswith(".tar.gz") and not namespace:
        raise ValueError("--namespace is required when --path is a tarball (.tar.gz).")

    _publish_common(path, visibility, package_only, output, "action", namespace)


@publish.command(name="agent")
@click.option(
    "--path",
    required=True,
    help="Path to the directory containing the agent to publish.",
)
@click.option(
    "--visibility",
    type=click.Choice(["public", "private"], case_sensitive=False),
    default="public",
    show_default=True,
    help="Visibility of the published agent (public or private).",
)
@click.option(
    "--package-only",
    is_flag=True,
    default=False,
    show_default=True,
    help="Only generate the package without publishing.",
)
@click.option(
    "--output",
    "-o",
    required=False,
    help="Output path for generated package.",
)
@click.option(
    "--namespace",
    required=False,  # Initially not required
    help="Namespace of the package (required when --path is a tarball).",
)
def publish_agent(
    path: str, visibility: str, package_only: bool, output: str, namespace: str
) -> None:
    """Publish an agent to the Jivas environment."""

    if path.endswith(".tar.gz") and not namespace:
        raise ValueError("--namespace is required when --path is a tarball (.tar.gz).")

    _publish_common(path, visibility, package_only, output, "agent", namespace)


def _publish_common(
    path: str,
    visibility: str,
    package_only: bool,
    output: str,
    publish_type: str,
    namespace: str,
) -> None:

    token = load_token().get("token")
    if not token and not package_only:
        click.secho("You need to login first.", fg="red")
        return

    # Check if path is directory
    if os.path.isdir(path):

        info_path = os.path.join(path, "info.yaml")
        if not os.path.exists(info_path):
            click.secho(
                f"Error: 'info.yaml' not found in the directory '{path}'.", fg="red"
            )
            return

        click.secho(f"Preparing {publish_type} from directory: {path}", fg="yellow")

        with open(info_path, "r") as info_file:
            info_data = yaml.safe_load(info_file)

        if validate_yaml_format(info_data, type=publish_type):
            click.secho("info.yaml validated successfully.", fg="yellow")
        else:
            click.secho(f"Error validating 'info.yaml' for {publish_type}.", fg="red")
            return

        try:
            package_name = info_data["package"].get("name")
            validate_package_name(package_name)
            click.secho(
                f"Package name '{package_name}' validated successfully.", fg="yellow"
            )
        except ValueError as e:
            click.secho(f"Error validating package name: {e}", fg="red")
            return

        try:
            validate_dependencies(info_data["package"].get("dependencies", {}), token)
            click.secho("Dependencies validated successfully.", fg="yellow")
        except ValueError as e:
            click.secho(f"Error validating dependencies: {e}", fg="red")
            return

        package_namespace, name = package_name.split("/", 1)

        # verify that publish namespace matches package namespace
        if (namespace and package_namespace) and (namespace != package_namespace):
            click.secho(
                f"Error validating namespace: You provided '{namespace}', but '{package_namespace}' was found in the package info file.",
                fg="red",
            )
            return

        # we need to ensure that the namespace is not None i.e namespace not used in cli
        namespace = namespace or package_namespace

        if package_only and not output:
            output = "."

        tgz_file_path = _prepare_package(namespace, name, path, publish_type, output)
        click.secho(f"Compressed {publish_type} to: {tgz_file_path}", fg="yellow")

    # check if path is already a tgz file
    elif path.endswith(".tar.gz"):
        click.secho(f"Preparing {publish_type} from tgz file: {path}", fg="yellow")
        tgz_file_path = path

    else:
        click.secho(
            f"Unable to publish {publish_type} from the path: {path}, unsupported file format"
        )
        return

    if not package_only:
        click.secho(
            f"Publishing {publish_type} with visibility: {visibility}", fg="blue"
        )
        response = RegistryAPI.publish_action(
            tgz_file_path, visibility, str(token), namespace or ""
        )
        if response:
            click.secho(
                f"{publish_type.capitalize()} published successfully!", fg="green"
            )


def _prepare_package(
    namespace: str, name: str, path: str, publish_type: str, output: str
) -> str:
    """Prepare the package for publishing."""
    tgz_filename = os.path.join(
        output if output else tempfile.gettempdir(), f"{namespace}_{name}.tar.gz"
    )
    tgz_file_path = compress_package_to_tgz(path, tgz_filename)
    click.secho(f"Compressed {publish_type} to: {tgz_file_path}", fg="yellow")
    return tgz_file_path
