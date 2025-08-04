"""setup.py for jvmanager package"""

from setuptools import find_packages, setup

setup(
    name="jvmanager",
    version="2.1.0",
    packages=find_packages(),
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
