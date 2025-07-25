"""JVGraph command group for deploying and interfacing with the Jivas Graph."""

import subprocess

import click


@click.group()
def graph() -> None:
    """Group for managing Jivas Studio resources."""
    pass  # pragma: no cover


@graph.command()
@click.option("--port", default=8989, help="Port for jvgraph to launch on.")
@click.option(
    "--require-auth", default=False, help="Require authentication for jvgraph api."
)
def launch(port: int, require_auth: bool) -> None:
    """Launch the Jivas Studio on the specified port."""
    # run jvgraph launch command as subprocess
    subprocess.run(
        ["jvgraph", "launch", "--port", str(port), "--require-auth", str(require_auth)]
    )
