"""Setup script for jivas"""

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
        "jvcli",
        "jvclient",
        "jvserve",
        "jac-cloud==0.2.7",
        "jaclang==0.8.7",
        "pytz==2025.2",
        "types-pytz==2025.2.0.20250809",
        "schedule==1.2.2",
        "openai==1.109.1",
        "langchain==0.3.27",
        "langchain-community==0.3.27",
        "langchain-core==0.3.79",
        "langchain-experimental==0.3.4",
        "langchain-openai==0.3.19",
        "langchain-text-splitters==0.3.11",
        "langsmith==0.4.38",
        "setuptools==80.9.0",
        "transformers==4.57.1",
        "ftfy==6.3.1",
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
