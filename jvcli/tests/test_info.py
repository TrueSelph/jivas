"""Tests for the info command."""

from click.testing import CliRunner
from pytest_mock import MockerFixture

from jvcli.commands.info import get_action_info, get_agent_info


class TestInfoCommand:
    """Test cases for the info command."""

    def test_get_action_info_success(self, mocker: MockerFixture) -> None:
        """Test getting action info successfully."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch("jvcli.commands.info.RegistryAPI")
        mock_package_info = {"name": "test_action", "version": "1.0.0"}
        mock_registry_api.get_package_info.return_value = mock_package_info

        mock_yaml = mocker.patch("jvcli.commands.info.yaml")
        mock_click = mocker.patch("jvcli.commands.info.click")

        runner = CliRunner()
        result = runner.invoke(get_action_info, ["test_action", "1.0.0"])

        assert result.exit_code == 0
        mock_registry_api.get_package_info.assert_called_once_with(
            "test_action", "1.0.0", token="test-token"
        )
        assert mock_yaml.safe_dump.call_count == 1
        assert mock_click.secho.call_count == 2

    def test_get_action_info_non_existent_package(self, mocker: MockerFixture) -> None:
        """Test handling non-existent action package."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "fake-token"}

        mock_registry_api = mocker.patch("jvcli.api.RegistryAPI.get_package_info")
        mock_registry_api.return_value = {}

        mock_click_secho = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(get_action_info, ["non_existent_package", "1.0.0"])

        assert result.exit_code == 0
        mock_registry_api.assert_called_once_with(
            "non_existent_package", "1.0.0", token="fake-token"
        )
        mock_click_secho.assert_called_with(
            "Failed to locate the action package.", fg="red"
        )

    def test_get_action_info_invalid_version(self, mocker: MockerFixture) -> None:
        """Test handling invalid action package version."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch(
            "jvcli.commands.info.RegistryAPI.get_package_info"
        )
        mock_registry_api.return_value = {}

        mock_click_secho = mocker.patch("jvcli.commands.info.click.secho")

        runner = CliRunner()
        result = runner.invoke(get_action_info, ["invalid_action", "invalid_version"])

        assert result.exit_code == 0
        mock_registry_api.assert_called_once_with(
            "invalid_action", "invalid_version", token="test-token"
        )
        mock_click_secho.assert_called_with(
            "Failed to locate the action package.", fg="red"
        )

    def test_get_action_info_fetches_latest_version(
        self, mocker: MockerFixture
    ) -> None:
        """Test fetching the latest version when version parameter is not provided."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "fake-token"}

        mock_registry_api = mocker.patch("jvcli.api.RegistryAPI.get_package_info")
        mock_registry_api.return_value = {"name": "test_action", "version": "latest"}

        mock_click_echo = mocker.patch("click.echo")
        mock_yaml_dump = mocker.patch("yaml.safe_dump")

        runner = CliRunner()
        result = runner.invoke(get_action_info, ["test_action"])

        assert result.exit_code == 0
        mock_registry_api.assert_called_once_with(
            "test_action", "latest", token="fake-token"
        )
        mock_click_echo.assert_called_once_with(
            "Checking the latest version of the action..."
        )
        mock_yaml_dump.assert_called_once()

    def test_get_action_info_exception_handling(self, mocker: MockerFixture) -> None:
        """Test handling exceptions when fetching action info."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch(
            "jvcli.commands.info.RegistryAPI.get_package_info"
        )
        mock_registry_api.side_effect = Exception("Test exception")

        mock_click_secho = mocker.patch("jvcli.commands.info.click.secho")

        runner = CliRunner()
        result = runner.invoke(get_action_info, ["test_action", "1.0.0"])

        assert result.exit_code == 0
        mock_click_secho.assert_called_with(
            "Error retrieving the action info: Test exception", fg="red"
        )

    def test_get_agent_info_success(self, mocker: MockerFixture) -> None:
        """Test getting agent info successfully."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch("jvcli.commands.info.RegistryAPI")
        mock_package_info = {"name": "test_agent", "version": "1.0.0"}
        mock_registry_api.get_package_info.return_value = mock_package_info

        mock_yaml = mocker.patch("jvcli.commands.info.yaml")
        mock_click = mocker.patch("jvcli.commands.info.click")

        runner = CliRunner()
        result = runner.invoke(get_agent_info, ["test_agent", "1.0.0"])

        assert result.exit_code == 0
        mock_registry_api.get_package_info.assert_called_once_with(
            "test_agent", "1.0.0", token="test-token"
        )
        assert mock_yaml.safe_dump.call_count == 1
        assert mock_click.secho.call_count == 2

    def test_get_agent_info_non_existent_package(self, mocker: MockerFixture) -> None:
        """Test handling non-existent agent package."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "fake-token"}

        mock_registry_api = mocker.patch("jvcli.api.RegistryAPI.get_package_info")
        mock_registry_api.return_value = {}

        mock_click_secho = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(get_agent_info, ["non_existent_agent", "1.0.0"])

        assert result.exit_code == 0
        mock_registry_api.assert_called_once_with(
            "non_existent_agent", "1.0.0", token="fake-token"
        )
        mock_click_secho.assert_called_with(
            "Failed to locate the agent package.", fg="red"
        )

    def test_get_agent_info_invalid_version(self, mocker: MockerFixture) -> None:
        """Test handling invalid agent package version."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch(
            "jvcli.commands.info.RegistryAPI.get_package_info"
        )
        mock_registry_api.return_value = {}

        mock_click_secho = mocker.patch("jvcli.commands.info.click.secho")

        runner = CliRunner()
        result = runner.invoke(get_agent_info, ["invalid_agent", "invalid_version"])

        assert result.exit_code == 0
        mock_registry_api.assert_called_once_with(
            "invalid_agent", "invalid_version", token="test-token"
        )
        mock_click_secho.assert_called_with(
            "Failed to locate the agent package.", fg="red"
        )

    def test_get_agent_info_fetches_latest_version(self, mocker: MockerFixture) -> None:
        """Test fetching the latest version when version parameter is not provided."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "fake-token"}

        mock_registry_api = mocker.patch("jvcli.api.RegistryAPI.get_package_info")
        mock_registry_api.return_value = {"name": "test_agent", "version": "latest"}

        mock_click_echo = mocker.patch("click.echo")
        mock_yaml_dump = mocker.patch("yaml.safe_dump")

        runner = CliRunner()
        result = runner.invoke(get_agent_info, ["test_agent"])

        assert result.exit_code == 0
        mock_registry_api.assert_called_once_with(
            "test_agent", "latest", token="fake-token"
        )
        mock_click_echo.assert_called_once_with(
            "Checking the latest version of the agent package..."
        )
        mock_yaml_dump.assert_called_once()

    def test_get_agent_info_exception_handling(self, mocker: MockerFixture) -> None:
        """Test handling exceptions when fetching agent info."""
        mock_load_token = mocker.patch("jvcli.commands.info.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch(
            "jvcli.commands.info.RegistryAPI.get_package_info"
        )
        mock_registry_api.side_effect = Exception("Test exception")

        mock_click_secho = mocker.patch("jvcli.commands.info.click.secho")

        runner = CliRunner()
        result = runner.invoke(get_agent_info, ["test_agent", "1.0.0"])

        assert result.exit_code == 0
        mock_click_secho.assert_called_with(
            "Error retrieving the agent package info: Test exception", fg="red"
        )
