"""Setup script for jvclient."""

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
    name="jvclient",
    version=get_version(),
    description="JIVAS client library for action development.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TrueSelph Inc.",
    author_email="admin@trueselph.com",
    url="https://github.com/TrueSelph/jvclient",
    keywords=["jivas"],
    packages=find_packages(
        include=[
            "jvclient",
            "jvclient.*",
        ]
    ),
    include_package_data=True,
    package_data={"jvclient": []},
    python_requires=">=3.12.0",
    install_requires=[
        "pyaml>=25.1.0",
        "requests>=2.32.3",
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
)
