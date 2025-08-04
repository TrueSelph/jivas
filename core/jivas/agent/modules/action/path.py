"""Path utilities relating to actions"""

import logging
import os
from typing import Optional, Set

logger = logging.getLogger(__name__)


def path_to_module(path: str) -> str:
    """
    Converts a file path into a module path.

    Parameters:
        path (str): The file path to convert. Example: '/a/b/c'

    Returns:
        str: The module path. Example: 'a.b.c'
    """
    # Strip leading and trailing slashes and split the path by slashes
    parts = path.strip("/").split("/")

    # Join the parts with dots to form the module path
    module_path = ".".join(parts)

    return module_path


def find_package_folder(
    rootdir: str, name: str, required_files: Optional[Set[str]] = None
) -> Optional[str]:
    """Find a package folder within a namespace."""
    if required_files is None:
        required_files = {"info.yaml"}
    try:
        # Split the provided name into namespace and package_folder
        namespace, package_folder = name.split("/")

        # Build the path for the namespace
        namespace_path = os.path.join(rootdir, namespace)

        # Check if the namespace directory exists
        if not os.path.isdir(namespace_path):
            return None

        # Traverse the namespace directory for the package_folder
        for root, dirs, _files in os.walk(namespace_path):
            if package_folder in dirs:
                package_path = os.path.join(root, package_folder)

                # Check for the presence of the required files
                folder_files = set(os.listdir(package_path))

                if required_files.issubset(folder_files):
                    # Return the full path of the package_folder if all checks out
                    return package_path

        # If package_folder is not found, return None
        return None

    except ValueError:
        logger.error("Invalid format. Please use 'namespace/package_folder'.")
        return None


def action_walker_path(module: str) -> str:
    """Accepts the module string of an action walker and returns a walker path string"""
    if not module:
        return ""

    module_parts = module.split(".")
    return f"/action/walker/{module_parts[-2]}/{module_parts[-1]}"


def action_webhook_path(module: str) -> str:
    """Accepts the module string of an action webhook walker and returns a walker path string"""
    if not module:
        return ""

    module_parts = module.split(".")
    return f"/action/webhook/{module_parts[-2]}/{module_parts[-1]}/{{agent_id}}/{{key}}"
