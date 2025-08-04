"""Test cases for the download command."""

import io

from click.testing import CliRunner
from pytest_mock import MockerFixture

from jvcli.commands.download import download_action, download_agent


class TestDownload:
    """Test cases for the download command."""

    def test_download_action_with_name_and_version(self, mocker: MockerFixture) -> None:
        """Test downloading an action with name and version."""
        mock_load_token = mocker.patch("jvcli.commands.download.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch("jvcli.commands.download.RegistryAPI")
        mock_registry_api.download_package.return_value = {
            "file": "http://test.com/package.tar.gz"
        }

        mock_requests = mocker.patch("jvcli.commands.download.requests")
        mock_response = mocker.Mock()
        mock_response.content = b"test content"
        mock_requests.get.return_value = mock_response

        mock_tarfile = mocker.patch("jvcli.commands.download.tarfile")
        mock_tar = mocker.MagicMock()
        mock_member = mocker.Mock()
        mock_member.name = "info.yaml"
        mock_tar.getmembers.return_value = [mock_member]
        mock_info_file = mocker.Mock()
        mock_tar.extractfile.return_value = mock_info_file
        mock_tarfile.open.return_value.__enter__.return_value = mock_tar
        mock_make_dirs = mocker.patch("jvcli.commands.download.os.makedirs")

        mock_yaml = mocker.patch("jvcli.commands.download.yaml")
        mock_yaml.safe_load.return_value = {
            "package": {"meta": {"type": "test_action"}}
        }

        mock_click = mocker.patch("jvcli.commands.download.click")

        runner = CliRunner()
        result = runner.invoke(download_action, ["test_action", "1.0.0"])

        assert result.exit_code == 0
        mock_registry_api.download_package.assert_called_once_with(
            "test_action", "1.0.0", token="test-token"
        )
        mock_requests.get.assert_called_once_with("http://test.com/package.tar.gz")
        mock_make_dirs.assert_called_once_with("./actions/test_action", exist_ok=True)
        mock_click.secho.assert_called_with(
            "Package 'test_action' (version: 1.0.0) downloaded to ./actions/test_action!",
            fg="green",
        )

    def test_download_latest_version_when_version_not_provided(
        self, mocker: MockerFixture
    ) -> None:
        """Test downloading the latest version when version parameter is not provided."""
        mock_load_token = mocker.patch("jvcli.commands.download.load_token")
        mock_load_token.return_value = {"token": "fake-token"}
        mock_registry_api = mocker.patch("jvcli.api.RegistryAPI.download_package")
        mock_registry_api.return_value = {"file": "http://example.com/package.tar.gz"}
        mock_requests_get = mocker.patch("requests.get")
        mock_requests_get.return_value.content = b"fake-content"
        mock_tarfile_open = mocker.patch("tarfile.open")
        mock_tarfile_open.return_value.__enter__.return_value.getmembers.return_value = (
            []
        )
        mock_click_echo = mocker.patch("click.echo")

        runner = CliRunner()
        result = runner.invoke(download_action, ["test_action"])

        assert result.exit_code == 0
        mock_registry_api.assert_called_once_with(
            "test_action", "latest", token="fake-token"
        )
        mock_click_echo.assert_any_call("Downloading test_action version latest...")

    def test_download_action_failed_to_download_package(
        self, mocker: MockerFixture
    ) -> None:
        """Test failed to download a package."""
        mock_load_token = mocker.patch("jvcli.commands.download.load_token")
        mock_load_token.return_value = {"token": "fake-token"}
        mock_registry_api = mocker.patch(
            "jvcli.commands.download.RegistryAPI.download_package"
        )
        mock_registry_api.return_value = None
        mock_click_secho = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(download_action, ["test_package", "1.0.0"])

        assert result.exit_code == 0
        mock_click_secho.assert_called_with("Failed to download the package.", fg="red")

    def test_download_action_ignores_macosx(self, mocker: MockerFixture) -> None:
        """Test that the download action ignores __MACOSX directories."""
        mock_load_token = mocker.patch("jvcli.commands.download.load_token")
        mock_load_token.return_value = {"token": "fake-token"}

        mock_registry_api = mocker.patch("jvcli.api.RegistryAPI.download_package")
        mock_registry_api.return_value = {"file": "http://example.com/package.tar.gz"}

        mock_requests_get = mocker.patch("requests.get")
        mock_requests_get.return_value.content = b"fake-content"

        mock_tarfile_open = mocker.patch("tarfile.open")
        mock_tarfile = mocker.Mock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tarfile

        mock_member_macosx = mocker.Mock()
        mock_member_macosx.name = "__MACOSX/somefile"

        mock_member_info_yaml = mocker.Mock()
        mock_member_info_yaml.name = "info.yaml"

        mock_tarfile.getmembers.return_value = [
            mock_member_macosx,
            mock_member_info_yaml,
        ]

        mock_tarfile.extractfile.return_value = io.BytesIO(
            b"package:\n  meta:\n    type: action"
        )

        mock_makedirs = mocker.patch("jvcli.commands.download.os.makedirs")

        mock_click_secho = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(download_action, ["test_package", "1.0.0"])

        assert result.exit_code == 0
        print(result.output)
        assert mock_makedirs.called

        mock_makedirs.assert_called_once_with("./actions/test_package", exist_ok=True)

        mock_tarfile.extractall.assert_called_once_with("./actions/test_package")

        mock_click_secho.assert_called_with(
            "Package 'test_package' (version: 1.0.0) downloaded to ./actions/test_package!",
            fg="green",
        )

    def test_invalid_package_type(self, mocker: MockerFixture) -> None:
        """Test invalid package type handling."""
        mock_load_token = mocker.patch("jvcli.commands.download.load_token")
        mock_load_token.return_value = {"token": "fake-token"}

        mock_registry_api = mocker.patch(
            "jvcli.commands.download.RegistryAPI.download_package"
        )
        mock_registry_api.return_value = {"file": "http://example.com/package.tar.gz"}

        mock_requests_get = mocker.patch("requests.get")
        mock_requests_get.return_value.content = b"fake-content"

        mock_tarfile_open = mocker.patch("tarfile.open")
        mock_tarfile = mocker.Mock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tarfile

        mock_member_info_yaml = mocker.Mock()
        mock_member_info_yaml.name = "info.yaml"
        mock_tarfile.getmembers.return_value = [mock_member_info_yaml]

        # Simulate an invalid package type
        mock_tarfile.extractfile.return_value = io.BytesIO(
            b"package:\n  meta:\n    type: invalid_type"
        )

        mock_click_secho = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(download_action, ["test_package", "1.0.0"])

        assert result.exit_code == 0
        mock_click_secho.assert_called_with(
            "Invalid package type for action download", fg="red"
        )

    def test_download_action_handles_exception(self, mocker: MockerFixture) -> None:
        """Test that download_action handles exceptions gracefully."""
        mock_load_token = mocker.patch("jvcli.commands.download.load_token")
        mock_load_token.return_value = {"token": "fake-token"}

        mock_registry_api = mocker.patch(
            "jvcli.commands.download.RegistryAPI.download_package"
        )
        mock_registry_api.side_effect = Exception("Test exception")

        mock_click_secho = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(download_action, ["test_package", "1.0.0"])

        assert result.exit_code == 0
        mock_click_secho.assert_called_with(
            "Error downloading the package: Test exception", fg="red"
        )

    def test_download_agent_with_name_version_and_path(
        self, mocker: MockerFixture
    ) -> None:
        """Test downloading an agent package with name, version, and path."""
        mock_load_token = mocker.patch("jvcli.commands.download.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_registry_api = mocker.patch("jvcli.commands.download.RegistryAPI")
        mock_registry_api.download_package.return_value = {
            "file": "http://test.com/package.tar.gz"
        }

        mock_requests = mocker.patch("jvcli.commands.download.requests")
        mock_response = mocker.Mock()
        mock_response.content = b"test content"
        mock_requests.get.return_value = mock_response

        mock_tarfile = mocker.patch("jvcli.commands.download.tarfile")
        mock_tar = mocker.MagicMock()
        mock_member = mocker.Mock()
        mock_member.name = "info.yaml"
        mock_tar.getmembers.return_value = [mock_member]
        mock_info_file = mocker.Mock()
        mock_tar.extractfile.return_value = mock_info_file
        mock_tarfile.open.return_value.__enter__.return_value = mock_tar
        mock_make_dirs = mocker.patch("jvcli.commands.download.os.makedirs")

        mock_yaml = mocker.patch("jvcli.commands.download.yaml")
        mock_yaml.safe_load.return_value = {"package": {"meta": {"type": "agent"}}}

        mock_click = mocker.patch("jvcli.commands.download.click")

        runner = CliRunner()
        result = runner.invoke(
            download_agent, ["test_agent", "1.0.0", "--path", "/custom/path"]
        )

        assert result.exit_code == 0
        mock_registry_api.download_package.assert_called_once_with(
            "test_agent", "1.0.0", token="test-token"
        )
        mock_requests.get.assert_called_once_with("http://test.com/package.tar.gz")
        mock_make_dirs.assert_called_once_with("/custom/path/test_agent", exist_ok=True)
        mock_click.secho.assert_called_with(
            "Package 'test_agent' (version: 1.0.0) downloaded to /custom/path/test_agent!",
            fg="green",
        )
