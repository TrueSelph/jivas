"""Info command group for getting info about resources on the Jivas Package Repository."""

import sys

import click
from pyaml import yaml

from jvcli.api import RegistryAPI
from jvcli.auth import load_token


@click.group()
def info() -> None:
    """Group for getting info about resources like actions."""
    pass  # pragma: no cover


@info.command(name="action")
@click.argument("name")
@click.argument("version", required=False)
def get_action_info(name: str, version: str) -> None:
    """
    Get info for an action package by name and version.
    If version is not provided, the latest version will be fetched.
    """

    token = load_token().get("token")

    # If version is not provided, fetch latest version
    if not version:
        click.echo("Checking the latest version of the action...")
        version = "latest"

    # Use the API function to fetch the action
    try:
        package_info = RegistryAPI.get_package_info(name, version, token=token)

        if not package_info:
            click.secho("Failed to locate the action package.", fg="red")
            return

        click.secho("======= PACKAGE INFO ========", fg="green")
        yaml.safe_dump(
            package_info,
            sys.stdout,
            width=100,
            allow_unicode=True,
            default_flow_style=False,
        )
        click.secho("=============================", fg="green")

    except Exception as e:
        click.secho(f"Error retrieving the action info: {e}", fg="red")


@info.command(name="agent")
@click.argument("name")
@click.argument("version", required=False)
def get_agent_info(name: str, version: str) -> None:
    """
    Get info for an agent package by name and version.
    If version is not provided, the latest version will be fetched.
    """

    token = load_token().get("token")

    # If version is not provided, fetch latest version
    if not version:
        click.echo("Checking the latest version of the agent package...")
        version = "latest"

    # Use the API function to fetch the agent
    try:
        package_info = RegistryAPI.get_package_info(name, version, token=token)

        if not package_info:
            click.secho("Failed to locate the agent package.", fg="red")
            return

        click.secho("======= PACKAGE INFO ========", fg="green")
        yaml.safe_dump(
            package_info,
            sys.stdout,
            width=100,
            allow_unicode=True,
            default_flow_style=False,
        )
        click.secho("=============================", fg="green")

    except Exception as e:
        click.secho(f"Error retrieving the agent package info: {e}", fg="red")
