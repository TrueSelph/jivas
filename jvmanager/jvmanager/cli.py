"""Jivas Graph CLI tool."""

from jvmanager.group import jvmanager
from jvmanager.commands.launch import launch


# Register command groups
jvmanager.add_command(launch)


if __name__ == "__main__":
    jvmanager()  # pragma: no cover
