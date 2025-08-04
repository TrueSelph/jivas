"""This module contains the API class for interacting with the Jivas Package Repository."""

from typing import Optional

import click
import requests


class RegistryAPI:
    """Class for interacting with the Jivas Package Repository API."""

    url = "https://api-jpr.trueselph.com/"

    @staticmethod
    def signup(username: str, email: str, password: str) -> dict:
        """Sign up for a Jivas Package Repository account."""
        endpoint = "signup"

        try:
            data = {"username": username, "email": email, "password": password}
            response = requests.post(RegistryAPI.url + endpoint, json=data)

            # Check if the response is successful
            if response.status_code == 200:
                # Include email in the response
                response_data = response.json()
                response_data["email"] = email
                return response_data
            else:
                click.secho(f"Error signing up: {response.json()['error']}", fg="red")
                return {}
        except Exception as e:
            click.secho(f"Error signing up: {e}", fg="red")
            return {}

    @staticmethod
    def login(email: str, password: str) -> dict:
        """Log in to your Jivas Package Repository account."""
        endpoint = "login"

        try:
            data = {"emailOrUsername": email, "password": password}
            response = requests.post(RegistryAPI.url + endpoint, json=data)

            # Check if the response is successful
            if response.status_code == 200:
                # Include email in the response
                response_data = response.json()
                response_data["email"] = email
                return response_data
            else:
                click.secho(f"Error logging in: {response.json()['error']}", fg="red")
                return {}
        except Exception as e:
            click.secho(f"Error logging in: {e}", fg="red")
            return {}

    @staticmethod
    def get_package_info(
        name: str,
        version: str = "",
        token: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Get package info.yaml content as json"""
        endpoint = "info"

        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}

            if api_key:
                headers["x-api-key"] = api_key

            data = {
                "name": name,
                "version": "" if version == "latest" else version,
            }
            response = requests.get(
                RegistryAPI.url + endpoint, params=data, headers=headers
            )
            # Check if the response is successful
            if response.status_code == 200:
                return response.json()
            else:
                click.secho(
                    f"Error retrieving package: {response.json()['error']}",
                    fg="red",
                )
                return {}
        except Exception as e:
            click.secho(f"Error retrieving package: {e}", fg="red")
            return {}

    @staticmethod
    def download_package(
        name: str,
        version: str = "",
        info: bool = False,
        suppress_error: bool = False,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Download a Jivas Package."""
        endpoint = "download"

        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}

            if api_key:
                headers["x-api-key"] = api_key

            data = {
                "name": name,
                "info": "true" if info else "false",
                "version": "" if version == "latest" else version,
            }
            response = requests.get(
                RegistryAPI.url + endpoint,
                params=data,
                headers=headers,
            )
            # Check if the response is successful
            if response.status_code == 200:
                return response.json()
            else:
                if not suppress_error:
                    click.secho(
                        f"Error downloading package: {response.json()['error']}",
                        fg="red",
                    )
                return {}
        except Exception as e:
            click.secho(f"Error downloading package: {e}", fg="red")
            return {}

    @staticmethod
    def create_namespace(name: str, token: str) -> dict:
        """Create a namespace."""
        endpoint = "namespace"

        try:
            headers = {"Authorization": f"Bearer {token}"}

            data = {"name": name}

            response = requests.post(
                RegistryAPI.url + endpoint, headers=headers, json=data
            )
            # Check if the response is successful
            if response.status_code == 200:
                return response.json()
            else:
                click.secho(
                    f"Error creating namespace: {response.json()['message']}", fg="red"
                )
                return {}
        except Exception as e:
            click.secho(f"Error creating namespace: {e}", fg="red")
            return {}

    @staticmethod
    def invite_user_to_namespace(
        namespace_name: str, user_email: str, token: str
    ) -> dict:
        """Invite a user to a namespace."""
        endpoint = f"namespace/{namespace_name}/invite"

        try:
            headers = {"Authorization": f"Bearer {token}"}

            data = {"emailOrUsername": user_email}

            response = requests.post(
                RegistryAPI.url + endpoint, headers=headers, json=data
            )
            # Check if the response is successful
            if response.status_code == 200:
                return response.json()
            else:
                click.secho(
                    f"Error inviting user to namespace: {response.json()['message']}",
                    fg="red",
                )
                return {}
        except Exception as e:
            click.secho(f"Error inviting user to namespace: {e}", fg="red")
            return {}

    @staticmethod
    def transfer_namespace_ownership(
        namespace_name: str, new_owner_email: str, token: str
    ) -> dict:
        """Transfer ownership of a namespace."""
        endpoint = f"namespace/{namespace_name}/transfer-ownership​"

        try:
            headers = {"Authorization": f"Bearer {token}"}

            data = {"emailOrUsername": new_owner_email}

            response = requests.post(
                RegistryAPI.url + endpoint, headers=headers, json=data
            )
            # Check if the response is successful
            if response.status_code == 200:
                return response.json()
            else:
                click.secho(
                    f"Error transferring ownership of namespace: {response.json()['message']}",
                    fg="red",
                )
                return {}
        except Exception as e:
            click.secho(f"Error transferring ownership of namespace: {e}", fg="red")
            return {}

    @staticmethod
    def package_search(
        query: str,
        version: Optional[str] = None,
        operator: Optional[str] = None,
        limit: int = 15,
        offset: int = 0,
    ) -> dict:
        """Search for packages in the Jivas Package Repository."""
        endpoint = "packages/search"

        try:
            data = {
                "q": query,
                # "version": version, # TODO: Implement version filtering
                # "operator": operator, # TODO: Implement operator filtering
                "limit": limit,
                "offset": offset,
            }
            response = requests.post(RegistryAPI.url + endpoint, json=data)
            # Check if the response is successful
            if response.status_code == 200:
                return response.json()
            else:
                click.secho(
                    f"Error searching for packages: {response.json()['error']}",
                    fg="red",
                )
                return {}
        except Exception as e:
            click.secho(f"Error searching for packages: {e}", fg="red")
            return {}

    @staticmethod
    def publish_action(
        tgz_file_path: str, visibility: str, token: str, namespace: str
    ) -> dict:
        """Publish a Jivas Action to the repository."""
        endpoint = "publish"

        try:
            headers = {
                "Authorization": f"Bearer {token}",
            }

            # Open the .tgz file using a context manager to ensure it's closed after use
            with open(tgz_file_path, "rb") as tgz_file:
                files = {"file": tgz_file}
                data = {
                    "visibility": visibility.capitalize(),  # Ensure correct capitalization
                    "namespace": namespace,
                }

                # Send POST request
                response = requests.post(
                    RegistryAPI.url + endpoint, headers=headers, files=files, data=data
                )

                if response.status_code == 401:
                    click.secho(
                        "Error publishing package: Invalid token. Please login again.",
                        fg="red",
                    )
                    return {}

                # Check if the response is successful
                if response.status_code == 200:
                    return response.json()  # Return the response data if successful
                else:
                    if response.json()["error"] == "VERSION_CONFLICT":
                        click.secho(
                            f"Error publishing package: {response.json()['message']}",
                            fg="red",
                        )
                        return {}
                    else:
                        # Print and show error message
                        click.secho(
                            f"Error publishing package: {response.json()}", fg="red"
                        )
                        return {}
        except Exception as e:
            click.secho(f"Error publishing package: {e}", fg="red")
            return {}
