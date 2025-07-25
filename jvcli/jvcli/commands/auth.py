"""Auth commands for the Jivas Package Repository CLI."""

import click

from jvcli.api import RegistryAPI
from jvcli.auth import delete_token, save_token


@click.command()
@click.option("--username", prompt=True, help="Your username.")
@click.option("--email", prompt=True, help="Your email address.")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Your password.",
)
def signup(username: str, email: str, password: str) -> None:
    """Sign up for a Jivas Package Repository account."""
    data = RegistryAPI.signup(username, email, password)
    if data and "token" in data and "namespaces" in data and "email" in data:
        save_token(data["token"], data["namespaces"], data["email"])
        click.secho("Signup successful! Token saved.", fg="green", bold=True)


@click.command()
@click.option(
    "--username",
    help="Your email address or username.",
    prompt="Login (username or email)",
)
@click.option("--password", prompt=True, hide_input=True, help="Your password.")
def login(username: str, password: str) -> None:
    """Log in to your Jivas Package Repository account."""
    data = RegistryAPI.login(username, password)
    if data and "token" in data and "namespaces" in data and "email" in data:
        save_token(data["token"], data["namespaces"], data["email"])
        click.secho("Login successful! Token saved.", fg="green", bold=True)


@click.command()
def logout() -> None:
    """Log out by clearing the saved token."""
    delete_token()
    click.secho("You have been logged out.", fg="green", bold=True)
