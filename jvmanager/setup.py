"""setup.py for jvmanager package"""

import os

from setuptools import find_packages, setup


def get_version() -> str:
    """Get the package version from the __init__ file."""
    version_file = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "__init__.py")
    )
    with open(version_file) as f:
        for line in f:
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Version not found.")


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jvmanager",
    version=get_version(),
    packages=find_packages(),
    long_description=long_description,
    install_requires=[
        "click",
        "fastapi",
        "uvicorn",
        "python-multipart",
    ],
    package_data={
        "jvmanager": ["manager/client/**"],
    },
    entry_points={
        "console_scripts": [
            "jvmanager = jvmanager.cli:jvmanager",
        ],
    },
)
