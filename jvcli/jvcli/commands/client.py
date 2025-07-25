"""Client command group for deploying and interfacing with the Jivas Client."""

import os
import subprocess
from pathlib import Path

import click


@click.group()
def client() -> None:
    """Group for managing Jivas Client resources."""
    pass  # pragma: no cover


@client.command()
@click.option("--port", default=8501, help="Port for the client to launch on.")
@click.option(
    "--jivas_url",
    default=os.environ.get("JIVAS_BASE_URL", "http://localhost:8000"),
    help="URL for the Jivas API.",
)
@click.option(
    "--studio_url",
    default=os.environ.get("JIVAS_STUDIO_URL", "http://localhost:8989"),
    help="URL for the Jivas Studio.",
)
def launch(port: int, jivas_url: str, studio_url: str) -> None:
    """Launch the Jivas Client."""
    click.echo(
        f"Launching Jivas Client on port {port}, loading action apps from {jivas_url}..."
    )
    os.environ["JIVAS_BASE_URL"] = jivas_url
    os.environ["JIVAS_STUDIO_URL"] = studio_url
    subprocess.call(
        [
            "streamlit",
            "run",
            "--server.port={}".format(port),
            "--client.showSidebarNavigation=False",
            "--client.showErrorDetails=False",
            "--global.showWarningOnDirectExecution=False",
            Path(__file__)
            .resolve()
            .parent.parent.joinpath("client")
            .joinpath("app.py")
            .resolve()
            .__str__(),
        ]
    )
