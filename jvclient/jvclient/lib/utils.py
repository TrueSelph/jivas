"""This module contains utility functions for the JVCLI client."""

import base64
import json
import os
from importlib.util import module_from_spec, spec_from_file_location
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Union

import requests
import streamlit as st
import yaml
from PIL import Image


def load_function(file_path: str, function_name: str, **kwargs: Any) -> Callable:
    """Dynamically loads and returns a function from a Python file, with optional keyword arguments."""

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No file found at {file_path}")

    # Get the module name from the file name
    module_name = os.path.splitext(os.path.basename(file_path))[0]

    # Load the module specification
    spec = spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Could not load specification for module {module_name}")

    # Create the module
    module = module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"Could not load module {module_name}")

    # Execute the module
    spec.loader.exec_module(module)

    # Get the function
    if not hasattr(module, function_name):
        raise AttributeError(f"Function '{function_name}' not found in {file_path}")

    func = getattr(module, function_name)

    # Ensure the returned callable can accept any kwargs passed to it
    def wrapped_func(*args: Any, **func_kwargs: Any) -> Any:
        return func(*args, **{**kwargs, **func_kwargs})

    return wrapped_func


def call_api(
    endpoint: str,
    method: str = "POST",
    headers: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    files: Optional[List] = None,
    data: Optional[Dict] = None,
    timeout: int = 10,
) -> Optional[requests.Response]:
    """Generic function to call an API endpoint."""

    jivas_base_url = os.environ.get("JIVAS_BASE_URL", "http://localhost:8000")
    if not endpoint.startswith("http"):
        endpoint = f"{jivas_base_url}/{endpoint}"

    ctx = get_user_info()  # Assumes a function that fetches user info

    if ctx.get("token"):
        try:
            headers = headers or {}
            headers["Authorization"] = f"Bearer {ctx['token']}"

            response = requests.request(
                method=method,
                url=endpoint,
                headers=headers,
                json=json_data,
                files=files,
                data=data,
                timeout=timeout,
            )

            if response.status_code == 401:
                st.session_state.EXPIRATION = ""
                return None

            return response

        except Exception as e:
            st.session_state.EXPIRATION = ""
            st.write(e)

    return None


def get_reports_payload(
    request: requests.Response, expect_single: bool = True
) -> Optional[Union[Any, List[Any]]]:
    """
    Safely extracts the 'reports' payload from a request's JSON response.

    Args:
        request (requests.Response): The HTTP response object (assumed to have `.json()` method).
        expect_single (bool, optional): If True, returns the first item in 'reports' (default).
                                        If False, returns the full list (or None if empty/missing).

    Returns:
        Optional[Union[Any, List[Any]]]:
            - If `expect_single=True`: Returns the first item in 'reports' or None.
            - If `expect_single=False`: Returns the full list (or None if missing/empty).
            - Returns None if JSON parsing fails or 'reports' is invalid.

    Example:
        >>> response = requests.get('https://api.example.com/data')
        >>> get_reports_payload(response)          # Returns first item (default)
        >>> get_reports_payload(response, False)   # Returns full list
    """
    try:
        payload = request.json()
        reports = payload.get("reports", []) if isinstance(payload, dict) else []

        if isinstance(reports, list):
            if expect_single:
                return reports[0] if reports else None
            return reports if reports else None
        return None
    except (ValueError, AttributeError, KeyError):
        return None


def call_action_walker_exec(
    agent_id: str,
    module_root: str,
    walker: str,
    args: Optional[Dict] = None,
    files: Optional[List] = None,
    headers: Optional[Dict] = None,
) -> list:
    """Call the API to execute a walker action for a given agent."""

    jivas_base_url = os.environ.get("JIVAS_BASE_URL", "http://localhost:8000")
    endpoint = f"{jivas_base_url}/action/walker"

    # Create form data
    data = {"agent_id": agent_id, "module_root": module_root, "walker": walker}

    if args:
        data["args"] = json.dumps(args)

    file_list = []

    if files:
        for file in files:
            file_list.append(("attachments", (file[0], file[1], file[2])))

    response = call_api(endpoint, headers=headers, data=data, files=file_list)

    if response is not None and response.status_code == 200:
        result = response.json()
        return result if result else []

    return []


def call_healthcheck(agent_id: str, headers: Optional[Dict] = None) -> Optional[dict]:
    """Call the API to check the health of an agent."""
    endpoint = "walker/healthcheck"
    json_data = {"agent_id": agent_id}
    response = call_api(endpoint, headers=headers, json_data=json_data)

    if response is not None and response.status_code in [200, 501, 503]:
        result = response.json()
        reports = result.get("reports", [])
        return reports[0] if reports else {}

    return {}


def call_list_agents(headers: Optional[Dict] = None) -> list:
    """Call the API to list agents."""
    endpoint = "walker/list_agents"
    json_data = {"reporting": True}
    response = call_api(endpoint, headers=headers, json_data=json_data)

    if response is not None and response.status_code == 200:
        result = response.json()
        reports = result.get("reports", [])
        return [
            {"id": agent.get("id", ""), "label": agent.get("name", "")}
            for agent in reports
        ]

    return []


def call_get_agent(agent_id: str, headers: Optional[Dict] = None) -> dict:
    """Call the API to get details of a specific agent."""
    endpoint = "walker/get_agent"
    json_data = {"agent_id": agent_id}
    response = call_api(endpoint, headers=headers, json_data=json_data)

    if response is not None and response.status_code == 200:
        result = response.json()
        reports = result.get("reports", [])
        return reports[0] if reports else {}

    return {}


def call_list_actions(agent_id: str, headers: Optional[Dict] = None) -> list:
    """Call the API to list actions for a given agent."""
    endpoint = "walker/list_actions"
    json_data = {"agent_id": agent_id}
    response = call_api(endpoint, headers=headers, json_data=json_data)

    if response is not None and response.status_code == 200:
        result = response.json()
        reports = result.get("reports", [])
        return reports[0] if reports else []

    return []


def call_get_action(
    agent_id: str, action_id: str, headers: Optional[Dict] = None
) -> dict:
    """Call the API to get a specific action for a given agent."""
    endpoint = "walker/get_action"
    json_data = {"agent_id": agent_id, "action_id": action_id}
    response = call_api(endpoint, headers=headers, json_data=json_data)

    if response is not None and response.status_code == 200:
        result = response.json()
        reports = result.get("reports", [])
        return reports[0] if reports else {}

    return {}


def call_update_action(
    agent_id: str, action_id: str, action_data: dict, headers: Optional[Dict] = None
) -> dict:
    """Call the API to update a specific action for a given agent."""
    endpoint = "walker/update_action"
    json_data = {
        "agent_id": agent_id,
        "action_id": action_id,
        "action_data": action_data,
    }
    response = call_api(endpoint, headers=headers, json_data=json_data)

    if response is not None and response.status_code == 200:
        result = response.json()
        reports = result.get("reports", [])
        return reports[0] if reports else {}

    return {}


def call_update_agent(
    agent_id: str, agent_data: dict, headers: Optional[Dict] = None
) -> dict:
    """Call the API to update a specific agent."""
    endpoint = "walker/update_agent"
    json_data = {"agent_id": agent_id, "agent_data": agent_data}
    response = call_api(endpoint, headers=headers, json_data=json_data)

    if response is not None and response.status_code == 200:
        result = response.json()
        reports = result.get("reports", [])
        return reports[0] if reports else {}

    return {}


def call_import_agent(descriptor: str, headers: Optional[Dict] = None) -> list:
    """Call the API to import an agent."""
    endpoint = "walker/import_agent"
    json_data = {"descriptor": descriptor}
    response = call_api(endpoint, headers=headers, json_data=json_data)

    if response is not None and response.status_code == 200:
        result = response.json()
        reports = result.get("reports", [])
        return reports[0] if reports else []

    return []


def get_user_info() -> dict:
    """Get user information from the session state."""
    return {
        "root_id": st.session_state.get("ROOT_ID", ""),
        "token": st.session_state.get("TOKEN", ""),
        "expiration": st.session_state.get("EXPIRATION", ""),
    }


def decode_base64_image(base64_string: str) -> Image:
    """Decode a base64 string into an image."""
    # Decode the base64 string
    image_data = base64.b64decode(base64_string)

    # Create a bytes buffer from the decoded bytes
    image_buffer = BytesIO(image_data)

    # Open the image using PIL
    return Image.open(image_buffer)


class LongStringDumper(yaml.SafeDumper):
    """Custom YAML dumper to handle long strings."""

    def represent_scalar(
        self, tag: str, value: str, style: Optional[str] = None
    ) -> yaml.ScalarNode:
        """Represent scalar values, using block style for long strings."""
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


def jac_yaml_dumper(
    data: Any,
    indent: int = 2,
    default_flow_style: bool = False,
    allow_unicode: bool = True,
    sort_keys: bool = False,
) -> str:
    """Dumps YAML data using LongStringDumper with customizable options."""
    return yaml.dump(
        data,
        Dumper=LongStringDumper,
        indent=indent,
        default_flow_style=default_flow_style,
        allow_unicode=allow_unicode,
        sort_keys=sort_keys,
    )
