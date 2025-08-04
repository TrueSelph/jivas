"""Serialization utility operations"""

import ast
import json
import logging
from enum import Enum
from typing import Any, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


class LongStringDumper(yaml.SafeDumper):
    """Custom YAML dumper to handle long strings."""

    def represent_scalar(
        self,
        tag: str,
        value: str,
        style: Optional[str] = None,
    ) -> yaml.nodes.ScalarNode:
        """Represent scalar values in YAML."""
        # Replace any escape sequences to format the output as desired
        if (
            len(value) > 150 or "\n" in value
        ):  # Adjust the threshold for long strings as needed
            style = "|"
            # converts all newline escapes to actual representations
            value = "\n".join([line.rstrip() for line in value.split("\n")])
        else:
            # converts all newline escapes to actual representations
            value = "\n".join([line.rstrip() for line in value.split("\n")]).rstrip()

        return super().represent_scalar(tag, value, style)


def make_serializable(obj: Any) -> Any:
    """Recursively convert non-serializable objects in a dict/list to strings."""
    if isinstance(obj, dict):
        return {
            make_serializable(key): make_serializable(value)
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # For sets, tuples, custom types, etc.
        return str(obj)


def export_to_dict(
    data: object | dict,
    ignore_keys: Optional[List[str]] = None,
) -> dict:
    """Export an object to a dictionary, ignoring specified keys and handling cycles.

    Args:
        data: The object or dictionary to serialize.
        ignore_keys: Keys to exclude from serialization (default: ["__jac__"])

    Returns:
        A dictionary representation of the input.
    """
    if ignore_keys is None:
        ignore_keys = ["__jac__"]

    memo: Set[int] = set()  # Track object IDs for cycle detection

    def _convert(obj: object) -> object:
        # Handle cycles
        obj_id = id(obj)
        if obj_id in memo:
            return "<cycle detected>"
        memo.add(obj_id)
        try:
            # 1. Basic immutable types
            if obj is None or isinstance(obj, (bool, int, float, str)):
                return obj

            # 2. Handle enums by their value
            if Enum is not None and isinstance(obj, Enum):
                return _convert(obj.value)  # Serialize enum value

            # 3. Handle namedtuples
            if hasattr(obj, "_asdict") and callable(obj._asdict):
                return _convert(obj._asdict())

            # 4. Dictionaries: apply ignore_keys and recurse
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items() if k not in ignore_keys}

            # 5. Lists, tuples, sets: convert to list and recurse
            if isinstance(obj, (list, tuple, set, frozenset)):
                return [_convert(item) for item in obj]

            # 6. Generic objects with __dict__
            if hasattr(obj, "__dict__"):
                return _convert(obj.__dict__)

            # 7. Fallback: string representation
            return str(obj)

        finally:
            memo.discard(obj_id)  # Clean up after processing

    result = _convert(data)
    # Ensure top-level output is a dictionary
    return result if isinstance(result, dict) else {"value": result}


def safe_json_dump(data: dict) -> Optional[str]:
    """Safely convert a dictionary with mixed types to a JSON string for logs."""
    if not isinstance(data, dict):
        logger.error("Input to safe_json_dump must be a dictionary.")
        return None

    def serialize(obj: dict) -> dict:
        """Recursively convert strings within complex objects."""

        def wrap_content(value: object) -> object:
            # Return value wrapped in a dictionary with key 'content' if it's a str, int or float
            return {"content": value} if isinstance(value, (str, int, float)) else value

        def process_dict(d: dict) -> dict:
            for key, value in d.items():
                if isinstance(value, dict):
                    d[key] = process_dict(value)
                elif isinstance(value, list):
                    # If the list contains dictionaries, recursively process each
                    d[key] = [
                        process_dict(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    d[key] = wrap_content(value)
            return d

        # Create a deep copy of the original dict to avoid mutation
        import copy

        result = copy.deepcopy(obj)

        return process_dict(result)

    try:
        # Attempt to serialize the dictionary
        return json.dumps(serialize(data))
    except (TypeError, ValueError) as e:
        # Handle serialization errors
        logger.error(f"Serialization error: {str(e)}")
        return None


def convert_str_to_json(text: str) -> dict | None:
    """Convert a string to a JSON object."""
    if isinstance(text, str):
        text = text.replace("```json", "")
        text = text.replace("```", "")
    try:
        if isinstance(text, (dict, list)):
            return text
        else:
            return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError) as e:
            if "'{' was never closed" in str(e):
                text = text + "}"
                return json.loads(text)
            else:
                logger.error(e)
                return None


def yaml_dumps(data: Optional[dict]) -> Optional[str]:
    """Converts and formats nested dict to YAML string, handling PyYAML errors."""
    if not data:
        return None

    try:
        safe_data = make_serializable(data)
        yaml_output = yaml.dump(
            safe_data,
            Dumper=LongStringDumper,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        if not yaml_output or yaml_output.strip() in ("", "---"):
            return None
        return yaml_output

    except Exception as e:
        logger.error(f"Error dumping YAML: {e}")
        return None
