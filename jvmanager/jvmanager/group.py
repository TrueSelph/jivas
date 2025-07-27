"""Jivas Manager CLI tool."""

import click
from __init__ import __version__


@click.group()
@click.version_option(__version__, prog_name="jvmanager")
def jvmanager() -> None:
    """Jivas Manager CLI tool."""
    pass  # pragma: no cover
