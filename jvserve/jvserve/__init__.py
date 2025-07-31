"""
jvserve package initialization.

This package provides the webserver for loading and interacting with JIVAS agents.
"""

from importlib.metadata import version

__version__ = version("jvserve")
__supported__jivas__versions__ = [__version__]
