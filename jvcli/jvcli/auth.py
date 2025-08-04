"""Authentication module for the CLI."""

import json
import os

import requests

TOKEN_FILE = os.path.expanduser("~/.jvcli_token")


def save_token(token: str, namespaces: dict, email: str) -> None:
    """Save the token to a file."""
    data = {"token": token, "namespaces": clean_namespaces(namespaces), "email": email}
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)


def load_token() -> dict:
    """Load the token from a file."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data
    return {}


def delete_token() -> None:
    """Delete the token file."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)


def clean_namespaces(namespaces: dict) -> dict:
    """Clean up the namespaces dict."""
    for k, v in namespaces.items():
        if k == "default":
            namespaces[k] = v.replace("@", "")
        if k == "groups":
            v = [group.replace("@", "") for group in v]
            namespaces[k] = v
    return namespaces


def load_namespaces() -> str:
    """Load the namespaces from the token."""
    token = load_token()
    return token.get("namespaces", {}).get("default", "anonymous")


def login_jivas() -> str:
    """Login to Jivas and return the token."""
    email = os.environ.get("JIVAS_USER")
    password = os.environ.get("JIVAS_PASSWORD")
    if not email or not password:
        raise ValueError(
            "JIVAS_USER and JIVAS_PASSWORD environment variables are required."
        )

    login_url = (
        f"{os.environ.get('JIVAS_BASE_URL', 'http://localhost:8000')}/user/login"
    )
    response = requests.post(login_url, json={"email": email, "password": password})
    if response.status_code == 200:
        data = response.json()
        os.environ["JIVAS_TOKEN"] = data["token"]
        return data["token"]
    else:
        raise ValueError(f"Login failed: {response.text}")
