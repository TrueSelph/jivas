"""Jivas Agent Utils Module"""

import ast
import json
import logging
import mimetypes
import os
import re
import subprocess
import unicodedata
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, DefaultDict, Dict, List, Optional
from uuid import UUID

import ftfy
import pytz  # To handle timezones
import requests
import yaml
from jvserve.lib.file_interface import (
    FILE_INTERFACE,
    file_interface,
    get_file_interface,
)

import jivas

logger = logging.getLogger(__name__)

# ensure .jvdata is the root as it contains sensitive data which we don't
# want served by jvcli jvfileserve
jvdata_file_interface = (
    get_file_interface("") if FILE_INTERFACE == "local" else file_interface
)
# for serving publically accessible files
public_file_interface = file_interface


class LongStringDumper(yaml.SafeDumper):
    """Custom YAML dumper to handle long strings."""

    def represent_scalar(
        self, tag: str, value: str, style: str | None = None
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


class Utils:
    """Utility class for various helper methods."""

    @staticmethod
    def get_jivas_version() -> str:
        """Returns the current JIVAS version."""
        return jivas.__version__

    @staticmethod
    def jac_clean_actions() -> None:
        """Performs jac clean on actions root folder."""

        actions_root_path = os.environ.get("JIVAS_ACTIONS_ROOT_PATH", "actions")
        if os.path.isdir(actions_root_path):
            logger.info("Running jac clean on actions directory")
            subprocess.run(["jac", "clean"], cwd=actions_root_path, check=True)

    @staticmethod
    def get_descriptor_root() -> str:
        """Get the root path for descriptors."""

        descriptor_path = os.environ.get("JIVAS_DESCRIPTOR_ROOT_PATH", ".jvdata")

        return descriptor_path

    @staticmethod
    def get_actions_root() -> str:
        """Get the root path for actions."""

        actions_root_path = os.environ.get("JIVAS_ACTIONS_ROOT_PATH", "actions")

        if not os.path.exists(actions_root_path):
            os.makedirs(actions_root_path)

        return actions_root_path

    @staticmethod
    def get_daf_root() -> str:
        """Get the root path for DAF."""

        daf_root_path = os.environ.get("JIVAS_DAF_ROOT_PATH", "daf")

        if not os.path.exists(daf_root_path):
            os.makedirs(daf_root_path)

        return daf_root_path

    @staticmethod
    def make_serializable(obj: Any) -> Any:
        """Recursively convert non-serializable objects in a dict/list to strings."""
        if isinstance(obj, dict):
            return {
                Utils.make_serializable(key): Utils.make_serializable(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [Utils.make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # For sets, tuples, custom types, etc.
            return str(obj)

    @staticmethod
    def yaml_dumps(data: Optional[dict[Any, Any]]) -> str | None:
        """Converts and formats nested dict to YAML string, handling PyYAML errors."""
        if not data:
            return "None"

        try:
            safe_data = Utils.make_serializable(data)
            yaml_output = yaml.dump(
                safe_data,
                # Use your custom dumper if needed, else SafeDumper
                Dumper=globals().get("LongStringDumper", yaml.SafeDumper),
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

    @staticmethod
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

    @staticmethod
    def find_package_folder(
        rootdir: str, name: str, required_files: set | None = None
    ) -> str | None:
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

    @staticmethod
    def list_to_phrase(lst: list) -> str:
        """Formats a list as a phrased list, e.g. ['one', 'two', 'three'] becomes 'one, two, and three'."""
        if not lst:
            return ""

        # Convert all elements to strings
        lst = list(map(str, lst))

        if len(lst) == 1:
            return lst[0]

        return ", ".join(lst[:-1]) + f", and {lst[-1]}"

    @staticmethod
    def replace_placeholders(
        string_or_collection: str | list, placeholders: dict
    ) -> str | list | None:
        """
        Replaces placeholders delimited by {{ and }} in a string or collection of strings with their corresponding values
        from a dictionary of key-value pairs. If a value in the dictionary is a list, it is formatted as a phrased list.
        Returns only items that have no remaining placeholders.

        Parameters:
        - string_or_collection (str or list): A string or collection of strings containing placeholders delimited by {{ and }}.
        - placeholders (dict): A dictionary of key-value pairs where the keys correspond to the placeholder names inside the {{ and }}
                                and the values will replace the entire placeholder in the string or collection of strings. If a
                                value in the dictionary is a list, it will be formatted as a phrased list.

        Returns:
        - str or list: The input string or collection of strings with the placeholders replaced by their corresponding values.
                    Returns only items that have no remaining placeholders.
        """

        def replace_in_string(s: str, placeholders: dict) -> str | None:
            # Replace placeholders in a single string
            for key, value in placeholders.items():
                if isinstance(value, list):
                    value = Utils.list_to_phrase(value)
                s = s.replace(f"{{{{{key}}}}}", str(value))
            return s if not re.search(r"{{.*?}}", s) else None

        if isinstance(string_or_collection, str):
            return replace_in_string(string_or_collection, placeholders)

        elif isinstance(string_or_collection, list):
            # Process each string in the list and return those with no placeholders left
            return [
                result
                for string in string_or_collection
                if (result := replace_in_string(string, placeholders)) is not None
            ]

        else:
            raise TypeError("Input must be a string or a list of strings.")

    @staticmethod
    def chunk_long_message(
        message: str, max_length: int = 1024, chunk_length: int = 1024
    ) -> list:
        """
        Splits a long message into smaller chunks of no more than chunk_length characters,
        ensuring no single chunk exceeds max_length.
        """
        if len(message) <= max_length:
            return [message]

        # Initialize variables
        final_chunks = []
        current_chunk = ""
        current_chunk_length = 0

        # Split the message into words while preserving newline characters
        words = re.findall(r"\S+\n*|\n+", message)
        words = [word for word in words if word.strip()]  # Filter out empty strings

        for word in words:
            word_length = len(word)

            if current_chunk_length + word_length + 1 <= chunk_length:
                # Add the word to the current chunk
                if current_chunk:
                    current_chunk += " "
                current_chunk += word
                current_chunk_length += word_length + 1
            else:
                # If the current chunk is full, add it to the list of chunks
                final_chunks.append(current_chunk)
                current_chunk = word  # Start a new chunk with the current word
                current_chunk_length = word_length

        if current_chunk:
            # Add the last chunk if it's non-empty
            final_chunks.append(current_chunk)

        return final_chunks

    @staticmethod
    def escape_string(input_string: str) -> str:
        """
        Escapes curly braces in the input string by converting them to double curly braces.

        Args:
        - input_string (str): The string to be escaped.

        Returns:
        - str: The escaped string with all curly braces doubled.
        """
        if not isinstance(input_string, (str)):
            logger.error(f"Error expect string: {input_string}")
            return ""
        else:
            return input_string.replace("{", "{{").replace("}", "}}")

    @staticmethod
    def export_to_dict(data: object | dict, ignore_keys: list | None = None) -> dict:
        """Export an object to a dictionary, ignoring specified keys."""
        if ignore_keys is None:
            ignore_keys = ["__jac__"]

        def stringify_value(value: object) -> object:
            # Recursive handling of dictionaries and lists
            if isinstance(value, dict):
                return {
                    k: stringify_value(v)
                    for k, v in value.items()
                    if k not in ignore_keys
                }
            elif isinstance(value, list):
                return [stringify_value(item) for item in value]
            elif isinstance(value, (str, int, float, bool, type(None))):
                return value
            else:
                # Stringify any other complex objects
                return str(value)

        # Convert top-level object to dictionary if possible
        if hasattr(data, "__dict__"):
            data = data.__dict__

        if isinstance(data, dict):
            return {
                k: stringify_value(v) for k, v in data.items() if k not in ignore_keys
            }
        else:
            return {}

    @staticmethod
    def safe_json_dump(data: dict) -> str | None:
        """Safely convert a dictionary with mixed types to a JSON string for logs."""

        def serialize(obj: dict) -> dict:
            """Recursively convert strings within complex objects."""

            def wrap_content(value: object) -> object:
                # Return value wrapped in a dictionary with key 'content' if it's a str, int or float
                return (
                    {"content": value}
                    if isinstance(value, (str, int, float))
                    else value
                )

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

    @staticmethod
    def date_now(
        timezone: str = "US/Eastern", date_format: str = "%Y-%m-%d"
    ) -> str | None:
        """Get the current date and time in the specified timezone and format."""
        try:
            # If a timezone is specified, apply it
            tz = pytz.timezone(timezone)
            # Get the current datetime
            dt = datetime.now(tz)
            # Format the datetime according to the provided format
            formatted_datetime = dt.strftime(date_format)

            return formatted_datetime
        except Exception:
            return None

    @staticmethod
    def is_valid_uuid(uuid_to_test: str, version: int = 4) -> bool:
        """
        Check if uuid_to_test is a valid UUID.

        Parameters
        ----------
        uuid_to_test : str
        version : {1, 2, 3, 4}

        Returns
        -------
        `True` if uuid_to_test is a valid UUID, otherwise `False`.

        Examples
        --------
        >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
        True
        >>> is_valid_uuid('c9bf9e58')
        False
        """

        try:
            uuid_obj = UUID(uuid_to_test, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == uuid_to_test

    @staticmethod
    def node_obj(node_list: list) -> object | None:
        """Return the first object in the list or None if the list is empty."""
        return node_list[0] if node_list else None

    @staticmethod
    def order_interact_actions(
        actions_data: List[Dict[str, Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        """Order interact actions based on their dependencies and weights."""
        if not actions_data:
            return None

        other_actions = [
            action
            for action in actions_data
            if action.get("context", {}).get("_package", {}).get("meta", {}).get("type")
            != "interact_action"
        ]
        interact_actions = [
            action
            for action in actions_data
            if action.get("context", {}).get("_package", {}).get("meta", {}).get("type")
            == "interact_action"
        ]

        action_lookup = {
            action["context"]["_package"]["name"]: action for action in interact_actions
        }

        graph: DefaultDict[str, List[str]] = defaultdict(list)
        in_degree: DefaultDict[str, int] = defaultdict(int)

        action_weights = {
            name: action["context"]["_package"]["config"]
            .get("order", {})
            .get("weight", 0)
            for name, action in action_lookup.items()
        }

        # First handle explicit before/after constraints (excluding "all")
        for action in interact_actions:
            action_name = action["context"]["_package"]["name"]
            config_order = action["context"]["_package"]["config"].get("order", {})

            before = config_order.get("before")
            after = config_order.get("after")

            if before and before != "all" and before in action_lookup:
                graph[action_name].append(before)
                in_degree[before] += 1

            if after and after != "all" and after in action_lookup:
                graph[after].append(action_name)
                in_degree[action_name] += 1

        # Handle "before": "all" and "after": "all" constraints separately without creating cycles
        before_all_actions = [
            action["context"]["_package"]["name"]
            for action in interact_actions
            if action["context"]["_package"]["config"].get("order", {}).get("before")
            == "all"
        ]
        after_all_actions = [
            action["context"]["_package"]["name"]
            for action in interact_actions
            if action["context"]["_package"]["config"].get("order", {}).get("after")
            == "all"
        ]

        for action_name in before_all_actions:
            for other_name in action_lookup:
                if other_name not in before_all_actions and other_name != action_name:
                    graph[action_name].append(other_name)
                    in_degree[other_name] += 1

        for action_name in after_all_actions:
            for other_name in action_lookup:
                if other_name not in after_all_actions and other_name != action_name:
                    graph[other_name].append(action_name)
                    in_degree[action_name] += 1

        # Kahn's algorithm with weights as tie-breaker
        queue = deque(
            sorted(
                [name for name in action_lookup if in_degree[name] == 0],
                key=lambda x: action_weights[x],
            )
        )

        sorted_actions_names = []
        while queue:
            current = queue.popleft()
            sorted_actions_names.append(current)
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            queue = deque(sorted(queue, key=lambda x: action_weights[x]))

        if len(sorted_actions_names) != len(interact_actions):
            raise ValueError("Circular dependency detected!")

        # Map sorted names back to actions and add others
        sorted_actions = [
            action_lookup[name] for name in sorted_actions_names
        ] + other_actions

        # Assign final weights according to sorted order
        for idx, action in enumerate(sorted_actions):
            if action["context"]["_package"]["meta"]["type"] == "interact_action":
                action["context"]["weight"] = idx

        return sorted_actions

    @staticmethod
    def get_mime_type(
        file_path: str | None = None,
        url: str | None = None,
        mime_type: str | None = None,
    ) -> dict | None:
        """Determines the MIME type of a file or URL and categorizes it into common file types (image, document, audio, video)."""
        detected_mime_type = None

        if file_path:
            # Use mimetypes to guess MIME type based on file extension
            detected_mime_type, _ = mimetypes.guess_type(file_path)
        elif url:
            # Make a HEAD request to get the Content-Type header
            try:
                response = requests.head(url, allow_redirects=True)
                detected_mime_type = response.headers.get("Content-Type")
            except requests.RequestException as e:
                logger.error(f"Error making HEAD request: {e}")
                return None
        else:
            # Fallback to initial MIME type if provided
            detected_mime_type = mime_type

        # MIME type categories
        image_mime_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/webp",
            "image/tiff",
            "image/svg+xml",
            "image/x-icon",
            "image/heic",
            "image/heif",
            "image/x-raw",
        ]
        document_mime_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "text/csv",
            "text/html",
            "application/rtf",
            "application/x-tex",
            "application/vnd.oasis.opendocument.text",
            "application/vnd.oasis.opendocument.spreadsheet",
            "application/epub+zip",
            "application/x-mobipocket-ebook",
            "application/x-fictionbook+xml",
            "application/x-abiword",
            "application/vnd.apple.pages",
            "application/vnd.google-apps.document",
        ]
        audio_mime_types = [
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/flac",
            "audio/aac",
            "audio/mp3",
            "audio/webm",
            "audio/amr",
            "audio/midi",
            "audio/x-m4a",
            "audio/x-realaudio",
            "audio/x-aiff",
            "audio/x-wav",
            "audio/x-matroska",
        ]
        video_mime_types = [
            "video/mp4",
            "video/mpeg",
            "video/ogg",
            "video/webm",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-matroska",
            "video/x-flv",
            "video/x-ms-wmv",
            "video/3gpp",
            "video/3gpp2",
            "video/h264",
            "video/h265",
            "video/x-f4v",
            "video/avi",
        ]

        # Handle cases where MIME type cannot be detected
        if detected_mime_type is None or detected_mime_type == "binary/octet-stream":
            if file_path:
                _, file_extension = os.path.splitext(file_path)
            elif url:
                _, file_extension = os.path.splitext(url)
            else:
                file_extension = ""

            detected_mime_type = mimetypes.types_map.get(file_extension.lower())

        # Categorize MIME type
        if detected_mime_type in image_mime_types:
            return {"file_type": "image", "mime": detected_mime_type}
        elif detected_mime_type in document_mime_types:
            return {"file_type": "document", "mime": detected_mime_type}
        elif detected_mime_type in audio_mime_types:
            return {"file_type": "audio", "mime": detected_mime_type}
        elif detected_mime_type in video_mime_types:
            return {"file_type": "video", "mime": detected_mime_type}
        else:
            logger.error(f"Unsupported MIME Type: {detected_mime_type}")
            return None

    @staticmethod
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

    @staticmethod
    def extract_first_name(full_name: str) -> str:
        """Extract the first name from a full name."""
        # List of common titles to be removed
        titles = ["Mr.", "Mrs.", "Ms.", "Miss", "Dr.", "Prof.", "Sir", "Madam", "Mx."]

        # Split the full name into parts
        name_parts = full_name.split()

        # Remove any titles from the list of name parts
        name_parts = [part for part in name_parts if part not in titles]

        # Return the first element as the first name if it's available
        if name_parts:
            return name_parts[0]
        else:
            return ""

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalizes a string by:
        - Stripping whitespace.
        - Fixing text encoding.
        - Removing non-word characters.

        :param text: Input string.
        :return: Normalized string.
        """
        text = text.strip().replace("\\n", "\n")
        text = ftfy.fix_text(text)
        return re.sub(r"\W+", "", text)

    @staticmethod
    def clean_context(
        node_context: dict, architype_context: dict, ignore_keys: list
    ) -> dict:
        """
        Cleans and sanitizes node_context by:
        - Removing keys that match in node_context and architype_context.
        - Removing empty values except boolean `False`.
        - Removing keys listed in ignore_keys.

        :param node_context: Dictionary containing existing snapshot of spawned node.
        :param architype_context: Dictionary containing original architype context variables and values.
        :param ignore_keys: List of keys to remove.
        :return: Sanitized dictionary.
        """

        # Check for matching keys and remove them if they match
        for key in list(architype_context.keys()):
            if key in node_context:
                if isinstance(node_context[key], str):
                    str1 = Utils.normalize_text(node_context[key])
                    str2 = Utils.normalize_text(architype_context[key])

                    if str1 == str2:
                        del node_context[key]

                else:
                    if node_context[key] == architype_context[key]:
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

    @staticmethod
    def to_snake_case(title: str, ascii_only: bool = True) -> str:
        """
        Converts a string to a safe, lowercase snake_case suitable for machine names.
        Args:
            title: The input string/title.
            ascii_only: If True, strips out non-ascii characters.
        Returns:
            A clean, lowercase, snake_case string.
        """
        s = title.strip()
        if ascii_only:
            # Normalize unicode
            s = unicodedata.normalize("NFKD", s)
            s = s.encode("ascii", "ignore").decode("ascii")
        else:
            # Remove combining marks but keep unicode letters
            s = unicodedata.normalize("NFKC", s)
        # Replace non-alphanumeric with underscores
        s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
        # Lowercase it
        s = s.lower()
        # Remove leading/trailing and consecutive underscores
        s = re.sub(r"_{2,}", "_", s)
        s = s.strip("_")
        return s
