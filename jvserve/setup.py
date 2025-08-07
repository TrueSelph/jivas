"""Setup script for jvserve."""

import os

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


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


setup(
    name="jvserve",
    version=get_version(),
    description="FastAPI webserver for loading and interaction with JIVAS agents.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TrueSelph Inc.",
    author_email="admin@trueselph.com",
    url="https://github.com/TrueSelph/jvserve",
    keywords=["jivas"],
    packages=find_packages(
        include=[
            "jvserve",
            "jvserve.*",
        ]
    ),
    include_package_data=True,
    package_data={"jvserve": []},
    python_requires=">=3.12.0",
    install_requires=[
        "jac-cloud",
        "psutil>=7.0.0",
        "jaclang==0.8.4",
        "pyaml>=25.1.0",
        "requests>=2.32.3",
        "aiohttp>=3.10.10",
        "schedule>=1.2.2",
        "boto3>=1.37.10",
    ],
    extras_require={
        "dev": [
            "pre-commit",
            "pytest",
            "pytest-mock",
            "pytest-cov",
            "coverage",
        ]
    },
    entry_points={
        "jac": [
            "jvserve = jvserve.cli:JacCmd",
        ],
    },
)
