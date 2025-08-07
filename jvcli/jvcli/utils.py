"""Utility functions for the Jivas Package Repository CLI tool."""

import os
import re
import tarfile
from typing import Optional

import click
import nodesemver
import requests
import semver
import yaml

from jvcli import __supported__jivas__versions__  # type: ignore[attr-defined]
from jvcli.api import RegistryAPI
from jvcli.auth import load_token

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def validate_snake_case(ctx: click.Context, param: click.Parameter, value: str) -> str:
    """Validate that the input is in snake_case."""
    if not re.match(r"^[a-z0-9_]+$", value):
        raise click.BadParameter(
            "must be snake_case (lowercase letters, numbers, and underscores only)."
        )
    return value


def validate_name(ctx: click.Context, param: click.Parameter, value: str) -> str:
    """Validate that the input only contains lowercase letters and numbers. Used for validating names."""
    if not re.match(r"^[a-z0-9]+$", value):
        raise click.BadParameter("must be lowercase letters and numbers only.")
    return value


def validate_yaml_format(info_data: dict, type: str, version: str = "latest") -> bool:
    """Validate if the info.yaml data matches the corresponding version template."""
    if version == "latest":
        version = max(__supported__jivas__versions__)

    if type == "action" or type.endswith("action"):
        template_path = os.path.join(
            TEMPLATES_DIR, version, "sourcefiles", "action_info.yaml"
        )

    if type == "daf" or type == "agent":
        template_path = os.path.join(
            TEMPLATES_DIR, version, "sourcefiles", "agent_info.yaml"
        )

    if not os.path.exists(template_path):
        click.secho(f"Template for version {version} not found.", fg="red")
        return False

    # Load template
    with open(template_path, "r") as template_file:
        # Fill placeholders to avoid YAML error
        template_content = template_file.read().format(
            dict.fromkeys(info_data.keys(), "")
        )
        template_data = yaml.safe_load(template_content)

    # Compare keys
    if set(info_data.keys()) != set(template_data.keys()):
        missing_keys = set(template_data.keys()) - set(info_data.keys())
        extra_keys = set(info_data.keys()) - set(template_data.keys())

        if extra_keys:
            click.secho(
                f"Warning: Extra keys: {extra_keys} found in info.yaml, the jivas package repository may ignore them.",
                fg="yellow",
            )

        if missing_keys:
            click.secho(
                f"info.yaml validation failed. Missing keys: {missing_keys}",
                fg="red",
            )
            return False
    return True


def validate_package_name(name: str) -> None:
    """Ensure the package name includes a namespace and matches user access."""
    if "/" not in name:
        raise ValueError(
            f"Package name '{name}' must include a namespace (e.g., 'namespace/action_name')."
        )

    namespace, _ = name.split("/", 1)
    namespaces = load_token().get("namespaces", {}).get("groups", [])
    if namespace not in namespaces:
        raise ValueError(
            f"Namespace '{namespace}' is not accessible to the current user."
        )


def is_version_compatible(
    version: str, specifiers: str, allow_prerelease: bool = True
) -> bool:
    """
    Determines if the provided version satisfies the given specifiers, with strict
    prerelease checks when `allow_prerelease` is True.
    """
    if not version or not specifiers:
        return False

    # Normalize specifiers to Node.js format
    specifiers = re.sub(r"\s*,\s*", " ", specifiers.strip())

    try:
        # Check using nodesemver
        result = nodesemver.satisfies(
            version, specifiers, include_prerelease=allow_prerelease
        )
    except ImportError:
        try:
            # Fallback to python-semver
            result = semver.satisfies(
                version, specifiers, allow_prerelease=allow_prerelease
            )
        except Exception:
            return False
    except Exception:
        return False

    # Additional scrutiny for prerelease logic
    if allow_prerelease and result:
        try:
            version_info = semver.VersionInfo.parse(version)
            # Extract base version from specifier (e.g., "^2.0.0-alpha.44" → "2.0.0-alpha.44")
            base_version_match = re.search(
                r"[\^~>=<]*(?P<version>\d+\.\d+\.\d+(-[a-zA-Z0-9\.]+)?)", specifiers
            )
            if base_version_match:
                base_version_str = base_version_match.group("version")
                base_version_info = semver.VersionInfo.parse(base_version_str)

                # Case 1: Specifier is a prerelease
                if base_version_info.prerelease:
                    # Reject stable versions or prereleases lower than the base prerelease
                    if (not version_info.prerelease) or (
                        version_info < base_version_info
                    ):
                        return False

        except (ValueError, TypeError):
            pass  # Fallback to original result if parsing fails

    return result


def validate_dependencies(dependencies: dict, token: Optional[str] = None) -> None:
    """Ensure all dependencies exist in the registry."""

    missing_dependencies = []

    for dep, specifier in dependencies.items():
        if dep == "jivas":
            # Check if the version is in list of supported versions
            def supported(spec: str) -> bool:
                return any(
                    is_version_compatible(
                        version, spec, False
                    )  # ignore prerelase specs for this validation
                    for version in __supported__jivas__versions__
                )

            if not supported(specifier):
                missing_dependencies.append(f"{dep} {specifier}")
        elif dep == "actions":
            # Check if action exists in the registry
            for name, spec in specifier.items():

                package = RegistryAPI.download_package(
                    name=name, version=spec, token=token, suppress_error=True
                )

                if not package:
                    missing_dependencies.append(f"{dep} {specifier}")
        elif dep == "pip":
            # TODO: Add support for pip dependencies
            continue
        else:
            raise ValueError(f"Unknown dependency type: {dep}")

    if missing_dependencies:
        raise ValueError(f"Dependencies not found in registry: {missing_dependencies}")


def compress_package_to_tgz(source_path: str, output_filename: str) -> str:
    """
    Compress the action folder into a .tgz file with the required structure,
    excluding the __jac_gen__ folder.

    Args:
        source_path (str): Path to the action directory.
        output_filename (str): Desired name of the output .tgz file.

    Returns:
        str: Path to the .tgz file.
    """
    with tarfile.open(output_filename, "w:gz") as tar:
        for root, dirs, files in os.walk(source_path):
            # Exclude the __jac_gen__ folder
            if "__jac_gen__" in dirs:
                dirs.remove("__jac_gen__")
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=source_path)
                tar.add(file_path, arcname=arcname)
    return output_filename


def load_env_if_present() -> None:
    """Load environment variables from .env file if present."""
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        try:
            import dotenv

            dotenv.load_dotenv(env_path)
        except ImportError:
            click.echo(
                "dotenv package not installed. Environment variables will not be loaded from .env file."
            )


def is_server_running() -> bool:
    """Check if the server is running by sending a request to the API."""
    try:
        base_url = os.environ.get("JIVAS_BASE_URL", "http://localhost:8000")
        healthz_url = f"{base_url}/healthz"
        response = requests.get(healthz_url)
        return response.status_code == 200
    except requests.ConnectionError:
        return False
