"""Operations to clean up actions"""

import logging
import os
import shutil
from typing import Dict, List

from ..text.formatting import normalize_text

logger = logging.getLogger(__name__)


def clean_action(namespace_package_name: str) -> bool:
    """Completely removes a specific action folder.

    Args:
        namespace_package_name: The namespace and package name in format 'namespace_folder/action_folder'

    Returns:
        bool: True if the action folder was successfully removed, False otherwise
    """
    actions_root_path = os.environ.get("JIVAS_ACTIONS_ROOT_PATH", "actions")
    if os.path.isdir(actions_root_path):
        logger.info(f"Running clean on action {namespace_package_name}")

        # Construct full path to the action folder
        action_path = os.path.join(actions_root_path, namespace_package_name)

        try:
            if os.path.exists(action_path):
                # Remove the entire action folder and its contents
                shutil.rmtree(action_path)
                logger.info(f"Successfully removed action folder: {action_path}")
                return True
            else:
                logger.warning(f"Action folder not found: {action_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to remove action folder {action_path}: {str(e)}")
            return False
    else:
        logger.error(f"Actions root directory not found: {actions_root_path}")
        return False


def clean_context(
    node_context: Dict, archetype_context: Dict, ignore_keys: List[str]
) -> Dict:
    """
    Cleans and sanitizes node_context by:
    - Removing keys that match in node_context and archetype_context
    - Removing empty values except boolean `False`
    - Removing keys listed in ignore_keys.

    Args:
        node_context: Existing snapshot of spawned node
        archetype_context: Original archetype context variables
        ignore_keys: List of keys to remove

    Returns:
        Sanitized dictionary
    """
    # Check for matching keys and remove them if they match
    for key in list(archetype_context.keys()):
        if key in node_context:
            if isinstance(node_context[key], str):
                str1 = normalize_text(node_context[key])
                str2 = normalize_text(archetype_context[key])

                if str1 == str2:
                    del node_context[key]
            else:
                if node_context[key] == archetype_context[key]:
                    del node_context[key]

    # Prepare keys to remove
    to_remove_key = list(ignore_keys)

    # Remove empty values (except boolean False)
    for key in list(node_context.keys()):
        if not node_context[key] and not isinstance(node_context[key], bool):
            to_remove_key.append(key)

    # Remove specified keys
    for key in to_remove_key:
        node_context.pop(key, None)

    return node_context
