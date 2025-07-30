"""Jivas Package Repository CLI tool."""

import click

from jivas import __version__
from jivas.plugin.commands.info import info


@click.group()
@click.version_option(__version__, prog_name="jvcli")
def jvcli() -> None:
    """Jivas Package Repository CLI tool."""
    pass  # pragma: no cover


jvcli.add_command(info)
