"""Client command group for interfacing with the Jivas Client."""

import subprocess

import click


@click.group()
def client() -> None:
    """Group for interfacing with the Jivas Client."""
    pass  # pragma: no cover


@client.command()
def launch() -> None:
    """Launch the Jivas Client by running the jvmanager launch command."""
    click.echo("Launching Jivas Client...")
    try:
        subprocess.call(["jvmanager", "launch"])
    except FileNotFoundError:
        click.secho(
            "Error: 'jvmanager' command not found. Make sure it is installed and in your PATH.",
            fg="red",
        )
    except Exception as e:
        click.secho(f"An error occurred: {e}", fg="red")
