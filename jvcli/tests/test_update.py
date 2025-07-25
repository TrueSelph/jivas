"""Tests for the update command."""

from click.testing import CliRunner
from pytest_mock import MockerFixture

from jvcli.commands.update import namespace


class TestUpdate:
    """Tests for the update command."""

    # Successfully invite a user to a namespace when valid token and email are provided
    def test_namespace_invite_user_success(self, mocker: MockerFixture) -> None:
        """Test successfully inviting a user to a namespace."""
        mock_load_token = mocker.patch("jvcli.commands.update.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch("jvcli.commands.update.RegistryAPI")
        mock_registry_api.invite_user_to_namespace.return_value = {"success": True}

        runner = CliRunner()
        result = runner.invoke(
            namespace, ["test-namespace", "--invite", "test@example.com"]
        )

        assert result.exit_code == 0
        mock_registry_api.invite_user_to_namespace.assert_called_once_with(
            namespace_name="test-namespace",
            user_email="test@example.com",
            token="test-token",
        )
        assert (
            "Operation on namespace 'test-namespace' completed successfully"
            in result.output
        )

    def test_namespace_not_logged_in(self, mocker: MockerFixture) -> None:
        """Test namespace command when not logged in."""
        mock_load_token = mocker.patch("jvcli.commands.update.load_token")
        mock_load_token.return_value = {}

        runner = CliRunner()
        result = runner.invoke(
            namespace, ["test-namespace", "--invite", "user@example.com"]
        )

        assert result.exit_code == 1
        assert "You need to login first." in result.output

        # Ensure that using both --invite and --transfer options at the same time results in an error

    def test_namespace_invite_and_transfer_mutually_exclusive(
        self, mocker: MockerFixture
    ) -> None:
        """Test namespace command with both invite and transfer options simultaneously."""
        mock_load_token = mocker.patch("jvcli.commands.update.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        runner = CliRunner()

        # Test both invite and transfer options at the same time
        result = runner.invoke(
            namespace,
            [
                "test-namespace",
                "--invite",
                "user@example.com",
                "--transfer",
                "newowner@example.com",
            ],
        )
        assert result.exit_code != 0
        assert (
            "You can only use one of --invite or --transfer at a time." in result.output
        )

    def test_namespace_transfer_success(self, mocker: MockerFixture) -> None:
        """Test successfully transferring ownership of a namespace."""
        # Mock user authentication
        mock_load_token = mocker.patch("jvcli.commands.update.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        # Mock RegistryAPI transfer method
        mock_registry_api = mocker.patch("jvcli.commands.update.RegistryAPI")
        mock_registry_api.transfer_namespace_ownership.return_value = {"success": True}

        runner = CliRunner()
        result = runner.invoke(
            namespace, ["test-namespace", "--transfer", "newowner@example.com"]
        )

        assert result.exit_code == 0

        mock_registry_api.transfer_namespace_ownership.assert_called_once_with(
            namespace_name="test-namespace",
            new_owner_email="newowner@example.com",
            token="test-token",
        )

        assert (
            "Operation on namespace 'test-namespace' completed successfully"
            in result.output
        )
