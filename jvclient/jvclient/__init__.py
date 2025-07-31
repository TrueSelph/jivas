"""
jvclient package initialization.

This package provides a library of utils and components for action ui development.
"""

import os


def get_version() -> str:
    """Get the package version from the __init__ file."""
    version_file = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "__init__.py")
    )
    with open(version_file) as f:
        for line in f:
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Version not found.")


__version__ = get_version()
