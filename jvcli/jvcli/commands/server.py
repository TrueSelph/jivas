"""Server command group for interfacing with the Jivas Server."""

import json
import os
import subprocess
import sys
from typing import Optional

import click
import requests

from jvcli.auth import login_jivas
from jvcli.utils import is_server_running, load_env_if_present

load_env_if_present()


@click.group()
def server() -> None:
    """Group for interfacing with the Jivas Server."""
    pass  # pragma: no cover


@server.command()
@click.option(
    "--jac-file",
    default="main.jac",
    help="Path to the JAC file to run. Defaults to main.jac in the current directory.",
)
@click.option(
    "--host",
    default=os.environ.get("JIVAS_HOST", "localhost"),
    help="Host address for Jivas login.",
)
@click.option(
    "--port",
    default=os.environ.get("JIVAS_PORT", 8000),
    help="Port for Jivas login.",
)
def launch(jac_file: str, host: str, port: int) -> None:
    """Launch the Jivas Server by running the specified JAC file."""
    click.echo(f"Launching Jivas Server with JAC file: {jac_file}...")
    subprocess.call(["jac", "jvserve", jac_file, "--host", host, "--port", str(port)])


@server.command()
@click.option(
    "--email",
    required=False,
    help="Email address for Jivas login.",
)
@click.option(
    "--password",
    required=False,
    hide_input=True,
    help="Password for Jivas login.",
)
def login(email: Optional[str] = None, password: Optional[str] = None) -> Optional[str]:
    """Login to Jivas Server and get an authentication token."""
    email = os.environ.get("JIVAS_USER") or email
    password = os.environ.get("JIVAS_PASSWORD") or password

    if email is None:
        email = click.prompt("Email")
    if password is None:
        password = click.prompt("Password", hide_input=True)

    click.echo(f"Logging in to Jivas Server as {email}...")

    login_url = (
        f"{os.environ.get('JIVAS_BASE_URL', 'http://localhost:8000')}/user/login"
    )

    try:
        response = requests.post(login_url, json={"email": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            token = data["token"]
            os.environ["JIVAS_TOKEN"] = token
            click.secho("Login successful!", fg="green", bold=True)
            click.echo(f"Token: {token}")
            return token
        else:
            click.secho(f"Login failed: {response.text}", fg="red", bold=True)
            return None
    except Exception as e:
        click.secho(f"Error connecting to Jivas Server: {str(e)}", fg="red", bold=True)
        return None


@server.command()
@click.option(
    "--email",
    required=False,
    help="Email address for the system admin.",
)
@click.option(
    "--password",
    required=False,
    hide_input=True,
    help="Password for the system admin.",
)
def createadmin(email: Optional[str] = None, password: Optional[str] = None) -> None:
    """Create a system administrator account."""
    email = os.environ.get("JIVAS_USER") or email
    password = os.environ.get("JIVAS_PASSWORD") or password

    if email is None:
        email = click.prompt("Email")
    if password is None:
        password = click.prompt("Password", hide_input=True)

    database_host = os.environ.get("DATABASE_HOST")

    if not database_host:
        click.echo("Database host is not set. Using signup endpoint...")
        signup_url = (
            f"{os.environ.get('JIVAS_BASE_URL', 'http://localhost:8000')}/user/register"
        )

        try:
            response = requests.post(
                signup_url, json={"email": email, "password": password}
            )
            if response.status_code in (200, 201):
                click.secho("Admin user created successfully!", fg="green", bold=True)
                return response.json()
            else:
                click.secho(
                    f"Failed to create admin: {response.text}", fg="red", bold=True
                )
        except Exception as e:
            click.secho(
                f"Error connecting to Jivas Server: {str(e)}", fg="red", bold=True
            )
    else:
        click.echo("Creating system admin...")
        try:
            result = subprocess.call(
                [
                    "jac",
                    "create_system_admin",
                    "main.jac",
                    "--email",
                    email,
                    "--password",
                    password,
                ]
            )
            if result == 0:
                click.secho("Admin user created successfully!", fg="green", bold=True)
            else:
                click.secho("Failed to create admin user", fg="red", bold=True)
        except Exception as e:
            click.secho(f"Error running jac command: {str(e)}", fg="red", bold=True)


@server.command()
def initagents() -> None:
    """
    Initialize agents in the Jivas system.

    Usage:
        jvcli server initagents
    """

    # Check if server is running
    if not is_server_running():
        click.secho("Server is not running. Please start the server first.", fg="red")
        sys.exit(1)

    # Login to Jivas
    token = login_jivas()
    if not token:
        click.secho("Failed to login to Jivas.", fg="red")
        sys.exit(1)
    click.secho("Logged in to Jivas successfully.", fg="green")

    # Initialize agents
    try:
        response = requests.post(
            f"{os.environ['JIVAS_BASE_URL']}/walker/init_agents",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json={},  # Add empty JSON object as request data
        )

        if response.status_code == 200:
            data = response.json()
            click.secho(f"Successfully initialized agents: {data}", fg="green")
        else:
            click.secho("Failed to initialize agents", fg="red")
            sys.exit(1)
    except requests.RequestException as e:
        click.secho(f"Error during request: {e}", fg="red")
        sys.exit(1)


@server.command()
@click.argument("agent_name")
@click.argument("version", required=False)
def importagent(agent_name: str, version: str) -> None:
    """
    Import an agent from a DAF package.

    Usage:
        jvcli server importagent <agent_name> [--version <jivas_version>]
    """

    # Check if server is running
    if not is_server_running():
        click.secho("Server is not running. Please start the server first.", fg="red")
        sys.exit(1)

    # Login to Jivas
    token = login_jivas()
    if not token:
        click.secho("Failed to login to Jivas.", fg="red")
        sys.exit(1)
    click.secho("Logged in to Jivas successfully.", fg="green")

    # Check if version is provided
    if not version:
        version = "latest"

    try:
        response = requests.post(
            f"{os.environ.get('JIVAS_BASE_URL', 'http://localhost:8000')}/walker/import_agent",
            json={"daf_name": agent_name, "daf_version": version},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

        if response.status_code == 200:
            try:
                data = response.json()
                agent_id = data.get("id")
                if agent_id:
                    click.secho(
                        f"Successfully imported agent. Agent ID: {agent_id}", fg="green"
                    )
                else:
                    click.secho(
                        "Agent imported but no ID was returned in the response",
                        fg="yellow",
                    )
            except json.JSONDecodeError:
                click.secho("Invalid JSON response from server", fg="red")
                sys.exit(1)
        else:
            click.secho(
                f"Failed to import agent. Status: {response.status_code}", fg="red"
            )
            click.echo(response.text)
            sys.exit(1)
    except requests.RequestException as e:
        click.secho(f"Request failed: {e}", fg="red")
        sys.exit(1)
