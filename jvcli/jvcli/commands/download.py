"""Download commands for the Jivas Package Repository CLI."""

import io
import os
import tarfile

import click
import requests
from pyaml import yaml

from jvcli.api import RegistryAPI
from jvcli.auth import load_token


@click.group()
def download() -> None:
    """Group for downloading resources like actions."""
    pass  # pragma: no cover


@download.command(name="action")
@click.argument("name")
@click.argument("version", required=False)
@click.option(
    "--path",
    required=False,
    help="Directory to download the action.",
)
def download_action(name: str, version: str, path: str) -> None:
    """Download a JIVAS action package."""
    _download_package(name, version, path, "action")


@download.command(name="agent")
@click.argument("name")
@click.argument("version", required=False)
@click.option(
    "--path",
    required=False,
    help="Directory to download the agent.",
)
def download_agent(name: str, version: str, path: str) -> None:
    """Download a JIVAS agent package."""
    _download_package(name, version, path, "agent")


def _download_package(name: str, version: str, path: str, pkg_type: str) -> None:
    token = load_token().get("token")

    if not version:
        version = "latest"

    click.echo(f"Downloading {name} version {version}...")

    try:
        package_data = RegistryAPI.download_package(name, version, token=token)
        if not package_data:
            click.secho("Failed to download the package.", fg="red")
            return

        package_file = requests.get(package_data["file"])
        info_file = None
        target_dir = None

        with tarfile.open(
            fileobj=io.BytesIO(package_file.content), mode="r:gz"
        ) as tar_file:
            for member in tar_file.getmembers():

                if "__MACOSX" in member.name:
                    continue

                if member.name in [
                    "info.yaml",
                    "info.yml",
                    "./info.yaml",
                    "./info.yml",
                ]:
                    info_file = tar_file.extractfile(member)
                    break

            if info_file:
                info_content = yaml.safe_load(info_file)
                package_type = (
                    info_content.get("package", {}).get("meta", {}).get("type")
                )

                # checking for both daf and agent to maintain backward compatibility
                if pkg_type == "agent" and package_type in ["agent", "daf"]:
                    base_dir = "daf"
                elif pkg_type == "action" and package_type.endswith("action"):
                    base_dir = "actions"
                else:
                    click.secho(
                        f"Invalid package type for {pkg_type} download", fg="red"
                    )
                    return

                target_dir = os.path.join(path if path else f"./{base_dir}", name)
                os.makedirs(target_dir, exist_ok=True)
                tar_file.extractall(target_dir)
            else:
                click.echo("No info.yaml file found in the package.")

            if target_dir:
                click.secho(
                    f"Package '{name}' (version: {version}) downloaded to {target_dir}!",
                    fg="green",
                )
    except Exception as e:
        click.secho(f"Error downloading the package: {e}", fg="red")
