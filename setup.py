"""Setup script for jivas"""

import os

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def get_version() -> str:
    """Get the package version from the __init__ file."""
    version_file = os.path.join(os.path.dirname(__file__), "jivas", "__init__.py")
    with open(version_file) as f:
        for line in f:
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Version not found.")


setup(
    name="jivas",
    version=get_version(),
    description="JIVAS is an Agentic Framework for rapidly prototyping and deploying graph-based, AI solutions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TrueSelph Inc.",
    author_email="admin@trueselph.com",
    url="https://github.com/TrueSelph/jivas",
    keywords=["jivas"],
    packages=find_packages(
        include=[
            "jivas",
            "jivas.*",
        ]
    ),
    include_package_data=True,
    package_data={"jivas": []},
    python_requires=">=3.12.0",
    install_requires=[
        "jvcli>=2.0.10",
        "jvserve>=2.0.6",
        "pytz>=2024.2",
        "types-pytz>=2024.2.0.20241003",
        "schedule>=1.2.2",
        "openai>=1.68.2",
        "langchain>=0.3.21",
        "langchain-community>=0.3.20",
        "langchain-core>=0.3.47",
        "langchain-experimental>=0.3.4",
        "langchain-openai>=0.3.9",
        "setuptools>=75.8.1",
        "transformers>=4.49.0",
        "spacy>=3.8.4",
        "ftfy>=6.2.3",
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
