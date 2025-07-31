"""Setup script for jvmanager."""

import os

from setuptools import find_packages, setup
from jvmanager import __version__

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name="jvmanager",
    version=__version__,
    description="CLI tool for Jivas Graph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TrueSelph Inc.",
    author_email="admin@trueselph.com",
    url="https://github.com/TrueSelph/jvmanager",
    packages=find_packages(
        include=["jvmanager", "jvmanager.*"],
    ),
    include_package_data=True,
    package_data={
        "jvmanager": ["manager/**/*"],
    },
    install_requires=[
        "click>=8.1.8",
        "requests>=2.32.3",
        "packaging>=24.2",
        "pyaml>=25.1.0",
        "python-dotenv>=1.0.0",
        "semver>=3.0.4",
        "node-semver>=0.9.0",
        "fastapi",
        "uvicorn",
    ],
    extras_require={
        "dev": [
            "pre-commit",
            "pytest",
            "pytest-mock",
            "pytest-cov",
        ],
    },
    entry_points={
        "console_scripts": [
            "jvmanager = jvmanager.cli:jvmanager",
        ],
    },
    python_requires=">=3.12",
)
