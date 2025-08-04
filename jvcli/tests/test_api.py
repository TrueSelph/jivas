"""Tests for the JVCLI API module."""

import io

from pytest_mock import MockerFixture

from jvcli.api import RegistryAPI


class TestRegistryAPI:
    """Test cases for the RegistryAPI class."""

    def test_signup_success_returns_response_with_email(
        self, mocker: MockerFixture
    ) -> None:
        """Successful user signup returns response data with added email."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "test_token",
            "namespaces": {"default": "testuser", "groups": ["testuser"]},
            "email": "test@example.com",
        }

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_username = "testuser"
        test_email = "test@example.com"
        test_password = "password123"  # pragma: allowlist secret

        # Act
        result = RegistryAPI.signup(test_username, test_email, test_password)

        # Assert
        mock_post.assert_called_once_with(
            RegistryAPI.url + "signup",
            json={
                "username": test_username,
                "email": test_email,
                "password": test_password,
            },
        )
        assert result == {
            "token": "test_token",
            "namespaces": {"default": "testuser", "groups": ["testuser"]},
            "email": "test@example.com",
        }

    def test_signup_unsuccessful_due_to_existing_username_or_email(
        self, mocker: MockerFixture
    ) -> None:
        """Test that covers unsuccessful signup using a username or email that is already taken."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Username or email already taken"}

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_username = "existinguser"
        test_email = "existing@example.com"
        test_password = "password123"  # pragma: allowlist secret

        # Act
        result = RegistryAPI.signup(test_username, test_email, test_password)

        # Assert
        mock_post.assert_called_once_with(
            RegistryAPI.url + "signup",
            json={
                "username": test_username,
                "email": test_email,
                "password": test_password,
            },
        )
        assert result == {}

    def test_signup_handles_exception(self, mocker: MockerFixture) -> None:
        """Test that covers handling exceptions during signup."""
        mocker.patch("requests.post", side_effect=Exception("Network error"))
        mock_secho = mocker.patch("click.secho")

        result = RegistryAPI.signup("testuser", "test@example.com", "password123")

        mock_secho.assert_called_once_with("Error signing up: Network error", fg="red")
        assert result == {}

    def test_login_success_returns_response_with_email(
        self, mocker: MockerFixture
    ) -> None:
        """Successful login returns response data with added email."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "test_token",
            "namespaces": {"default": "testuser", "groups": ["testuser"]},
            "email": "test@example.com",
        }

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_email = "test@example.com"
        test_password = "password123"  # pragma: allowlist secret

        # Act
        result = RegistryAPI.login(test_email, test_password)

        # Assert
        mock_post.assert_called_once_with(
            RegistryAPI.url + "login",
            json={"emailOrUsername": test_email, "password": test_password},
        )
        assert result == {
            "token": "test_token",
            "namespaces": {"default": "testuser", "groups": ["testuser"]},
            "email": "test@example.com",
        }

    def test_login_invalid_credentials_returns_empty_dict(
        self, mocker: MockerFixture
    ) -> None:
        """Invalid credentials during login returns empty dict."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid credentials"}

        mocker.patch("requests.post", return_value=mock_response)
        mocker.patch("click.secho")  # Suppress CLI output

        test_email = "test@example.com"
        test_password = "wrongpassword"  # pragma: allowlist secret

        # Act
        result = RegistryAPI.login(test_email, test_password)

        # Assert
        assert result == {}

    def test_login_handles_exception(self, mocker: MockerFixture) -> None:
        """Test that covers handling exceptions during login."""
        # Arrange
        mock_post = mocker.patch(
            "requests.post", side_effect=Exception("Network error")
        )
        test_email = "test@example.com"
        test_password = "password123"  # pragma: allowlist secret

        # Act
        result = RegistryAPI.login(test_email, test_password)

        # Assert
        mock_post.assert_called_once_with(
            f"{RegistryAPI.url}login",
            json={"emailOrUsername": test_email, "password": test_password},
        )
        assert result == {}

    def test_get_package_info_with_valid_token(self, mocker: MockerFixture) -> None:
        """Package info retrieval with valid token returns package data."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "test_package", "version": "1.0.0"}

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        test_name = "test_package"
        test_version = "1.0.0"
        test_token = "valid_token"

        # Act
        result = RegistryAPI.get_package_info(test_name, test_version, test_token)

        # Assert
        mock_get.assert_called_once_with(
            RegistryAPI.url + "info",
            params={"name": test_name, "version": test_version},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert result == {"name": "test_package", "version": "1.0.0"}

    def test_get_package_info_exception_handling(self, mocker: MockerFixture) -> None:
        """Test that covers handling exceptions during package info retrieval."""
        # Arrange
        mock_requests = mocker.patch(
            "requests.get", side_effect=Exception("Network error")
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.get_package_info(name="test-pkg", version="1.0.0")

        # Assert
        mock_requests.assert_called_once_with(
            RegistryAPI.url + "info",
            params={"name": "test-pkg", "version": "1.0.0"},
            headers={},
        )
        mock_secho.assert_called_once_with(
            "Error retrieving package: Network error", fg="red"
        )
        assert result == {}

    def test_download_package_success(self, mocker: MockerFixture) -> None:
        """Package download with valid parameters returns package content."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"package": "content"}

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        test_name = "testpackage"
        test_version = "1.0.0"
        test_info = False
        test_token = "valid_token"

        # Act
        result = RegistryAPI.download_package(
            name=test_name, version=test_version, info=test_info, token=test_token
        )

        # Assert
        mock_get.assert_called_once_with(
            RegistryAPI.url + "download",
            params={"name": test_name, "info": "false", "version": test_version},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert result == {"package": "content"}

    def test_download_package_exception_handling(self, mocker: MockerFixture) -> None:
        """Test that covers handling exceptions during package download."""
        # Arrange
        mock_requests = mocker.patch(
            "requests.get", side_effect=Exception("Network error")
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.download_package(name="test-package", version="1.0.0")

        # Assert
        mock_requests.assert_called_once_with(
            RegistryAPI.url + "download",
            params={"name": "test-package", "info": "false", "version": "1.0.0"},
            headers={},
        )
        mock_secho.assert_called_once_with(
            "Error downloading package: Network error", fg="red"
        )
        assert result == {}

    def test_create_namespace_success_returns_namespace_data(
        self, mocker: MockerFixture
    ) -> None:
        """Namespace creation with valid token returns namespace data."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"namespace": "test_namespace"}

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_name = "test_namespace"
        test_token = "valid_token"

        # Act
        result = RegistryAPI.create_namespace(test_name, test_token)

        # Assert
        mock_post.assert_called_once_with(
            RegistryAPI.url + "namespace",
            headers={"Authorization": f"Bearer {test_token}"},
            json={"name": test_name},
        )
        assert result == {"namespace": "test_namespace"}

    def test_create_namespace_unsuccessful_response(
        self, mocker: MockerFixture
    ) -> None:
        """Test that covers handling unsuccessful response during namespace creation."""
        # Arrange
        mock_post = mocker.patch(
            "requests.post",
            return_value=mocker.Mock(
                status_code=400, json=lambda: {"message": "Invalid data"}
            ),
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.create_namespace(
            name="invalid-namespace", token="fake-token"
        )

        # Assert
        mock_post.assert_called_once_with(
            f"{RegistryAPI.url}namespace",
            headers={"Authorization": "Bearer fake-token"},
            json={"name": "invalid-namespace"},
        )
        mock_secho.assert_called_once_with(
            "Error creating namespace: Invalid data", fg="red"
        )
        assert result == {}

    def test_create_namespace_exception_handling(self, mocker: MockerFixture) -> None:
        """Test that covers handling exceptions during namespace creation."""
        # Arrange
        mock_post = mocker.patch(
            "requests.post", side_effect=Exception("Network error")
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.create_namespace(
            name="test-namespace", token="dummy-token"
        )

        # Assert
        mock_post.assert_called_once_with(
            f"{RegistryAPI.url}namespace",
            headers={"Authorization": "Bearer dummy-token"},
            json={"name": "test-namespace"},
        )
        mock_secho.assert_called_once_with(
            "Error creating namespace: Network error", fg="red"
        )
        assert result == {}

    def test_invite_user_to_namespace_success(self, mocker: MockerFixture) -> None:
        """Test successful invitation of user to namespace."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "User invited successfully"}

        mock_requests = mocker.patch("requests.post", return_value=mock_response)

        namespace = "test-namespace"
        email = "test@example.com"
        token = "test-token"

        # Act
        result = RegistryAPI.invite_user_to_namespace(namespace, email, token)

        # Assert
        mock_requests.assert_called_once_with(
            f"{RegistryAPI.url}namespace/{namespace}/invite",
            headers={"Authorization": f"Bearer {token}"},
            json={"emailOrUsername": email},
        )
        assert result == {"message": "User invited successfully"}

    def test_invite_user_unsuccessful_response(self, mocker: MockerFixture) -> None:
        """Test that covers handling unsuccessful response during user invitation."""
        # Arrange
        mock_post = mocker.patch(
            "requests.post",
            return_value=mocker.Mock(
                status_code=400, json=lambda: {"message": "Invalid request"}
            ),
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.invite_user_to_namespace(
            namespace_name="test-namespace",
            user_email="user@example.com",
            token="fake-token",
        )

        # Assert
        mock_post.assert_called_once_with(
            f"{RegistryAPI.url}namespace/test-namespace/invite",
            headers={"Authorization": "Bearer fake-token"},
            json={"emailOrUsername": "user@example.com"},
        )
        mock_secho.assert_called_once_with(
            "Error inviting user to namespace: Invalid request", fg="red"
        )
        assert result == {}

    def test_invite_user_to_namespace_exception_handling(
        self, mocker: MockerFixture
    ) -> None:
        """Test that covers handling exceptions during user invitation to namespace."""
        # Arrange
        mock_requests = mocker.patch(
            "requests.post", side_effect=Exception("Network error")
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.invite_user_to_namespace(
            namespace_name="test-namespace",
            user_email="user@example.com",
            token="dummy-token",
        )

        # Assert
        mock_requests.assert_called_once_with(
            f"{RegistryAPI.url}namespace/test-namespace/invite",
            headers={"Authorization": "Bearer dummy-token"},
            json={"emailOrUsername": "user@example.com"},
        )
        mock_secho.assert_called_once_with(
            "Error inviting user to namespace: Network error", fg="red"
        )
        assert result == {}

    def test_transfer_namespace_ownership_success(self, mocker: MockerFixture) -> None:
        """Test successful namespace ownership transfer with valid inputs."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": "Ownership transferred successfully"
        }

        mock_requests = mocker.patch("requests.post", return_value=mock_response)
        mock_secho = mocker.patch("click.secho")

        namespace = "test-namespace"
        new_owner = "new.owner@email.com"
        token = "test-token"

        # Act
        result = RegistryAPI.transfer_namespace_ownership(namespace, new_owner, token)

        # Assert
        mock_requests.assert_called_once_with(
            f"{RegistryAPI.url}namespace/{namespace}/transfer-ownership​",
            headers={"Authorization": f"Bearer {token}"},
            json={"emailOrUsername": new_owner},
        )
        mock_secho.assert_not_called()
        assert result == {"message": "Ownership transferred successfully"}

    def test_transfer_namespace_ownership_unsuccessful_response(
        self, mocker: MockerFixture
    ) -> None:
        """Test handling of unsuccessful response during namespace ownership transfer."""
        # Arrange
        mock_post = mocker.patch(
            "requests.post",
            return_value=mocker.Mock(
                status_code=400, json=lambda: {"message": "Invalid email"}
            ),
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.transfer_namespace_ownership(
            namespace_name="test-namespace",
            new_owner_email="invalid-email",
            token="fake-token",
        )

        # Assert
        mock_post.assert_called_once_with(
            f"{RegistryAPI.url}namespace/test-namespace/transfer-ownership​",
            headers={"Authorization": "Bearer fake-token"},
            json={"emailOrUsername": "invalid-email"},
        )
        mock_secho.assert_called_once_with(
            "Error transferring ownership of namespace: Invalid email", fg="red"
        )
        assert result == {}

    def test_transfer_namespace_ownership_exception_handling(
        self, mocker: MockerFixture
    ) -> None:
        """Test that covers handling exceptions during namespace ownership transfer."""
        # Arrange
        mock_requests = mocker.patch(
            "requests.post", side_effect=Exception("Network error")
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.transfer_namespace_ownership(
            namespace_name="test-namespace",
            new_owner_email="newowner@example.com",
            token="dummy-token",
        )

        # Assert
        mock_requests.assert_called_once_with(
            f"{RegistryAPI.url}namespace/test-namespace/transfer-ownership​",
            headers={"Authorization": "Bearer dummy-token"},
            json={"emailOrUsername": "newowner@example.com"},
        )
        mock_secho.assert_called_once_with(
            "Error transferring ownership of namespace: Network error", fg="red"
        )
        assert result == {}

    def test_package_search_with_valid_query_returns_results(
        self, mocker: MockerFixture
    ) -> None:
        """Package search with valid query returns search results."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"packages": ["package1", "package2"]}

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_query = "test_query"
        test_limit = 15
        test_offset = 0

        # Act
        result = RegistryAPI.package_search(
            test_query, limit=test_limit, offset=test_offset
        )

        # Assert
        mock_post.assert_called_once_with(
            RegistryAPI.url + "packages/search",
            json={"q": test_query, "limit": test_limit, "offset": test_offset},
        )
        assert result == {"packages": ["package1", "package2"]}

    def test_package_search_unsuccessful_response(self, mocker: MockerFixture) -> None:
        """Test that covers handling unsuccessful responses during package search."""
        # Arrange
        mock_post = mocker.patch(
            "requests.post",
            return_value=mocker.Mock(
                status_code=400, json=lambda: {"error": "Bad Request"}
            ),
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.package_search(query="test-query")

        # Assert
        mock_post.assert_called_once_with(
            f"{RegistryAPI.url}packages/search",
            json={"q": "test-query", "limit": 15, "offset": 0},
        )
        mock_secho.assert_called_once_with(
            "Error searching for packages: Bad Request", fg="red"
        )
        assert result == {}

    def test_package_search_exception_handling(self, mocker: MockerFixture) -> None:
        """Test that covers handling exceptions during package search."""
        # Arrange
        mock_requests = mocker.patch(
            "requests.post", side_effect=Exception("Network error")
        )
        mock_secho = mocker.patch("click.secho")

        # Act
        result = RegistryAPI.package_search(query="test-query")

        # Assert
        mock_requests.assert_called_once_with(
            f"{RegistryAPI.url}packages/search",
            json={"q": "test-query", "limit": 15, "offset": 0},
        )
        mock_secho.assert_called_once_with(
            "Error searching for packages: Network error", fg="red"
        )
        assert result == {}

    def test_publish_action_successful_upload(self, mocker: MockerFixture) -> None:
        """Successful action upload returns success message."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Action published successfully"}

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_tgz_file_path = "test_action.tgz"
        test_visibility = "Public"
        test_token = "valid_token"
        test_namespace = "test_namespace"

        # Create a fake file object
        fake_file = io.BytesIO(b"Fake file content")

        # Mock `open()` to return `fake_file` within a context manager
        mock_open = mocker.mock_open()
        mock_open.return_value.__enter__.return_value = fake_file  # Keeps it open
        mocker.patch("builtins.open", mock_open)

        # Act
        result = RegistryAPI.publish_action(
            tgz_file_path=test_tgz_file_path,
            visibility=test_visibility,
            token=test_token,
            namespace=test_namespace,
        )

        # Assert
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]  # Get keyword arguments from the call

        # Check headers
        assert call_args["headers"] == {"Authorization": f"Bearer {test_token}"}

        # Check file upload (ensure `requests.post` gets a real file-like object)
        uploaded_file = call_args["files"]["file"]
        assert isinstance(
            uploaded_file, io.BytesIO
        )  # Ensures it’s a real file-like object
        assert (
            uploaded_file.getvalue() == b"Fake file content"
        )  # Ensures correct content

        # Check form data
        assert call_args["data"] == {
            "visibility": test_visibility,
            "namespace": test_namespace,
        }

        assert result == {"message": "Action published successfully"}

    def test_get_package_info_invalid_token_returns_error(
        self, mocker: MockerFixture
    ) -> None:
        """Missing or invalid auth token returns error response."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid token"}

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        test_name = "test_package"
        test_version = "1.0.0"
        invalid_token = "invalid_token"

        # Act
        result = RegistryAPI.get_package_info(test_name, test_version, invalid_token)

        # Assert
        mock_get.assert_called_once_with(
            RegistryAPI.url + "info",
            params={"name": test_name, "version": test_version},
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
        assert result == {}

    def test_download_package_non_existent_version_returns_error(
        self, mocker: MockerFixture
    ) -> None:
        """Package download with non-existent version returns error."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Version not found"}

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        test_name = "test_package"
        test_version = "non_existent_version"

        # Act
        result = RegistryAPI.download_package(test_name, test_version)

        # Assert
        mock_get.assert_called_once_with(
            RegistryAPI.url + "download",
            params={"name": test_name, "info": "false", "version": test_version},
            headers={},
        )
        assert result == {}

    def test_package_search_empty_query_returns_all_packages(
        self, mocker: MockerFixture
    ) -> None:
        """Package search with empty query string behavior."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"packages": ["package1", "package2"]}

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_query = ""
        test_limit = 15
        test_offset = 0

        # Act
        result = RegistryAPI.package_search(
            test_query, limit=test_limit, offset=test_offset
        )

        # Assert
        mock_post.assert_called_once_with(
            RegistryAPI.url + "packages/search",
            json={"q": test_query, "limit": test_limit, "offset": test_offset},
        )
        assert result == {"packages": ["package1", "package2"]}

    def test_publish_action_invalid_file_format_fails(
        self, mocker: MockerFixture
    ) -> None:
        """Publishing action with invalid file format fails."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "INVALID_FILE_FORMAT",
            "message": "Invalid file format.",
        }

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_tgz_file_path = "invalid_file.txt"
        test_visibility = "public"
        test_token = "test_token"
        test_namespace = "test_namespace"

        # Create a fake file object
        fake_file = io.BytesIO(b"Fake file content")

        # Mock `open()` to return `fake_file` within a context manager
        mock_open = mocker.mock_open()
        mock_open.return_value.__enter__.return_value = fake_file
        mocker.patch("builtins.open", mock_open)

        # Act
        result = RegistryAPI.publish_action(
            test_tgz_file_path, test_visibility, test_token, test_namespace
        )

        # Assert
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]

        # Check headers
        assert call_args["headers"] == {"Authorization": f"Bearer {test_token}"}
        uploaded_file = call_args["files"]["file"]
        assert isinstance(uploaded_file, io.BytesIO)
        assert uploaded_file.getvalue() == b"Fake file content"

        assert result == {}

    def test_publish_action_version_conflict_returns_error(
        self, mocker: MockerFixture
    ) -> None:
        """Version conflict during package publishing returns error."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "VERSION_CONFLICT",
            "message": "Version conflict error message",
        }

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_tgz_file_path = "test_path.tgz"
        test_visibility = "Public"
        test_token = "test_token"
        test_namespace = "test_namespace"

        # Create a fake file object
        fake_file = io.BytesIO(b"Fake file content")

        # Mock `open()` to return `fake_file` within a context manager
        mock_open = mocker.mock_open()
        mock_open.return_value.__enter__.return_value = fake_file
        mocker.patch("builtins.open", mock_open)

        # Act
        result = RegistryAPI.publish_action(
            tgz_file_path=test_tgz_file_path,
            visibility=test_visibility,
            token=test_token,
            namespace=test_namespace,
        )

        # Assert
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]

        # Check headers
        assert call_args["headers"] == {"Authorization": f"Bearer {test_token}"}
        uploaded_file = call_args["files"]["file"]
        assert isinstance(uploaded_file, io.BytesIO)
        assert uploaded_file.getvalue() == b"Fake file content"

        # Check form data
        assert call_args["data"] == {
            "visibility": test_visibility,
            "namespace": test_namespace,
        }

        assert result == {}

    def test_publish_action_invalid_token_returns_error(
        self, mocker: MockerFixture
    ) -> None:
        """Invalid token during package publishing returns error."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 401

        mock_post = mocker.patch("requests.post", return_value=mock_response)

        test_tgz_file_path = "test_path.tgz"
        test_visibility = "Public"
        test_token = "invalid_token"
        test_namespace = "test_namespace"

        # Create a fake file object
        fake_file = io.BytesIO(b"Fake file content")

        # Mock `open()` to return `fake_file` within a context manager
        mock_open = mocker.mock_open()
        mock_open.return_value.__enter__.return_value = fake_file
        mocker.patch("builtins.open", mock_open)

        # Act
        result = RegistryAPI.publish_action(
            tgz_file_path=test_tgz_file_path,
            visibility=test_visibility,
            token=test_token,
            namespace=test_namespace,
        )

        # Assert
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]

        # Check headers
        assert call_args["headers"] == {"Authorization": f"Bearer {test_token}"}
        uploaded_file = call_args["files"]["file"]
        assert isinstance(uploaded_file, io.BytesIO)
        assert uploaded_file.getvalue() == b"Fake file content"

        # Check form data
        assert call_args["data"] == {
            "visibility": test_visibility,
            "namespace": test_namespace,
        }

        assert result == {}

    def test_publish_action_handles_exception(self, mocker: MockerFixture) -> None:
        """Test that an exception during package publishing is handled gracefully."""
        # Arrange
        mocker.patch("requests.post", side_effect=Exception("Test exception"))

        test_tgz_file_path = "test_path.tgz"
        test_visibility = "Public"
        test_token = "test_token"
        test_namespace = "test_namespace"

        # Create a fake file object
        fake_file = io.BytesIO(b"Fake file content")

        # Mock `open()` to return `fake_file` within a context manager
        mock_open = mocker.mock_open()
        mock_open.return_value.__enter__.return_value = fake_file
        mocker.patch("builtins.open", mock_open)

        # Act
        result = RegistryAPI.publish_action(
            tgz_file_path=test_tgz_file_path,
            visibility=test_visibility,
            token=test_token,
            namespace=test_namespace,
        )

        # Assert
        assert result == {}

    def test_package_download_with_api_key(self, mocker: MockerFixture) -> None:
        """Test downloading package with API key."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"package": "content"}

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        test_name = "test-action"
        test_api_key = "test-api-key"  # pragma: allowlist secret

        # Act
        result = RegistryAPI.download_package(name=test_name, api_key=test_api_key)

        # Assert
        mock_get.assert_called_once_with(
            f"{RegistryAPI.url}download",
            params={"name": test_name, "info": "false", "version": ""},
            headers={"x-api-key": test_api_key},
        )
        assert result == {"package": "content"}

    def test_package_info_with_api_key(self, mocker: MockerFixture) -> None:
        """Test getting package info with API key."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-action",
            "version": "1.0.0",
            "description": "Test action",
        }

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        test_name = "test-action"
        test_api_key = "test-api-key"  # pragma: allowlist secret

        # Act
        result = RegistryAPI.get_package_info(name=test_name, api_key=test_api_key)

        # Assert
        mock_get.assert_called_once_with(
            f"{RegistryAPI.url}info",
            params={"name": test_name, "version": ""},
            headers={"x-api-key": test_api_key},
        )
        assert result == {
            "name": "test-action",
            "version": "1.0.0",
            "description": "Test action",
        }
