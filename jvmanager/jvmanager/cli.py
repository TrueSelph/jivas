"""Jivas Graph CLI tool."""

from jvmanager.commands.launch import launch
from jvmanager.group import jvmanager

# Register command groups
jvmanager.add_command(launch)


if __name__ == "__main__":
    jvmanager()  # pragma: no cover
