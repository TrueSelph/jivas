"""Test cases for the publish command."""

from click.testing import CliRunner
from pytest_mock import MockerFixture

from jvcli.commands.publish import _prepare_package, publish_action, publish_agent


class TestPublishCommand:
    """Test cases for the publish command."""

    def test_publish_action_with_default_visibility(
        self, mocker: MockerFixture
    ) -> None:
        """Test publishing an action with default visibility."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")

        mock_os_path.isdir.return_value = True
        mock_os_path.exists.return_value = True
        mock_os_path.join.return_value = "test/path/info.yaml"

        mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data=b"package:\n  name: test/test_action\n  dependencies: {}"
            ),
        )

        mock_yaml = mocker.patch("jvcli.commands.publish.yaml")
        mock_yaml.safe_load.return_value = {
            "package": {
                "name": "test/test_action",
                "dependencies": {},
            }
        }
        mock_validate_yaml_format = mocker.patch(
            "jvcli.commands.publish.validate_yaml_format"
        )
        mock_validate_yaml_format.return_value = True
        mocker.patch("jvcli.commands.publish.validate_package_name")
        mock_prepare_package = mocker.patch("jvcli.commands.publish._prepare_package")
        mock_prepare_package.return_value = "test.tar.gz"

        mock_registry_api = mocker.patch("jvcli.commands.publish.RegistryAPI")
        mock_registry_api.publish_action.return_value = True

        runner = CliRunner()
        result = runner.invoke(publish_action, ["--path", "test/path"])

        assert result.exit_code == 0
        mock_registry_api.publish_action.assert_called_once_with(
            "test.tar.gz", "public", "test-token", "test"
        )

    def test_publish_action_user_not_logged_in(self, mocker: MockerFixture) -> None:
        """Test publishing an action when the user is not logged in."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": None}

        runner = CliRunner()
        result = runner.invoke(publish_action, ["--path", "test/path"])

        assert result.exit_code == 0
        assert "You need to login first." in result.output

    def test_publish_action_missing_info_yaml(self, mocker: MockerFixture) -> None:
        """Test publishing an action when 'info.yaml' is missing."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")

        mock_os_path.isdir.return_value = True
        mock_os_path.exists.return_value = False  # Simulate missing info.yaml

        runner = CliRunner()
        result = runner.invoke(publish_action, ["--path", "test/path"])

        assert result.exit_code == 0
        assert (
            "Error: 'info.yaml' not found in the directory 'test/path'."
            in result.output
        )

    def test_publish_action_invalid_yaml_format(self, mocker: MockerFixture) -> None:
        """Test handling of invalid YAML format in info.yaml."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = True
        mock_os_path.exists.return_value = True
        mock_os_path.join.return_value = "test/path/info.yaml"

        # Simulate invalid YAML content
        mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data=b"package:\n  name: test/test_action\n  dependencies: {}"
            ),
        )

        mock_yaml = mocker.patch("jvcli.commands.publish.yaml")
        mock_yaml.safe_load.return_value = {
            "package": {"name": "test/test_action", "invalid_key": "value"}
        }

        mock_validate_yaml_format = mocker.patch(
            "jvcli.commands.publish.validate_yaml_format"
        )
        mock_validate_yaml_format.return_value = False

        runner = CliRunner()
        result = runner.invoke(publish_action, ["--path", "test/path"])

        assert result.exit_code == 0
        assert "Error validating 'info.yaml' for action." in result.output

    def test_invalid_action_package_name(self, mocker: MockerFixture) -> None:
        """Test handling of invalid action package name."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = True
        mock_os_path.exists.return_value = True
        mock_os_path.join.return_value = "test/path/info.yaml"

        mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data=b"package:\n  name: invalid_name\n  dependencies: {}"
            ),
        )

        mock_yaml = mocker.patch("jvcli.commands.publish.yaml")
        mock_yaml.safe_load.return_value = {
            "package": {"name": "invalid_name", "dependencies": {}}
        }

        mock_validate_yaml_format = mocker.patch(
            "jvcli.commands.publish.validate_yaml_format"
        )
        mock_validate_yaml_format.return_value = True

        mock_validate_package_name = mocker.patch(
            "jvcli.commands.publish.validate_package_name"
        )
        mock_validate_package_name.side_effect = ValueError("Invalid package name.")

        runner = CliRunner()
        result = runner.invoke(publish_action, ["--path", "test/path"])

        assert result.exit_code == 0
        assert "Error validating package name: Invalid package name." in result.output

    def test_invalid_action_dependencies(self, mocker: MockerFixture) -> None:
        """Test handling of invalid action dependencies."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")

        mock_os_path.isdir.return_value = True
        mock_os_path.exists.return_value = True
        mock_os_path.join.return_value = "test/path/info.yaml"

        mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data=b"package:\n  name: test/test_action\n  dependencies: {}"
            ),
        )

        mock_yaml = mocker.patch("jvcli.commands.publish.yaml")
        mock_yaml.safe_load.return_value = {
            "package": {"name": "test/test_action", "dependencies": {}}
        }

        mock_validate_yaml_format = mocker.patch(
            "jvcli.commands.publish.validate_yaml_format"
        )
        mock_validate_yaml_format.return_value = True

        mock_validate_package_name = mocker.patch(
            "jvcli.commands.publish.validate_package_name"
        )
        mock_validate_package_name.return_value = None

        mock_validate_dependencies = mocker.patch(
            "jvcli.commands.publish.validate_dependencies"
        )
        mock_validate_dependencies.side_effect = ValueError("Invalid dependencies.")

        runner = CliRunner()
        result = runner.invoke(publish_action, ["--path", "test/path"])

        assert result.exit_code == 0
        assert "Error validating dependencies: Invalid dependencies." in result.output

    def test_publish_action_package_only(self, mocker: MockerFixture) -> None:
        """Test publishing an action package only."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = True
        mock_os_path.exists.return_value = True
        mock_os_path.join.return_value = "test/path/info.yaml"

        mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data=b"package:\n  name: test/test_action\n  dependencies: {}"
            ),
        )

        mock_yaml = mocker.patch("jvcli.commands.publish.yaml")
        mock_yaml.safe_load.return_value = {
            "package": {"name": "test/test_action", "dependencies": {}}
        }

        mock_validate_yaml_format = mocker.patch(
            "jvcli.commands.publish.validate_yaml_format"
        )
        mock_validate_yaml_format.return_value = True
        mocker.patch("jvcli.commands.publish.validate_package_name")

        mock_validate_dependencies = mocker.patch(
            "jvcli.commands.publish.validate_dependencies"
        )
        mock_validate_dependencies.return_value = None

        mock_prepare_package = mocker.patch("jvcli.commands.publish._prepare_package")
        mock_prepare_package.return_value = "test.tar.gz"

        mock_registry_api = mocker.patch("jvcli.commands.publish.RegistryAPI")
        mock_registry_api.publish_action.return_value = True

        runner = CliRunner()
        result = runner.invoke(
            publish_action, ["--path", "test/path", "--package-only"]
        )

        assert result.exit_code == 0
        mock_registry_api.publish_action.assert_not_called()
        assert "Compressed action to: test.tar.gz" in result.output

    def test_publish_action_with_tarball(self, mocker: MockerFixture) -> None:
        """Test publishing an action with a tarball."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = False
        mock_os_path.exists.return_value = True

        mock_registry_api = mocker.patch("jvcli.commands.publish.RegistryAPI")
        mock_registry_api.publish_action.return_value = True

        runner = CliRunner()
        result = runner.invoke(
            publish_action, ["--path", "test.tar.gz", "--namespace", "test"]
        )

        assert result.exit_code == 0
        mock_registry_api.publish_action.assert_called_once_with(
            "test.tar.gz", "public", "test-token", "test"
        )
        assert "Preparing action from tgz file: test.tar.gz" in result.output
        assert "Compressed action to: test.tar.gz" not in result.output

    def test_publish_action_missing_namespace_for_tarball(
        self, mocker: MockerFixture
    ) -> None:
        """Test that publishing with a tarball fails if --namespace is missing."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = False
        mock_os_path.exists.return_value = True

        runner = CliRunner()
        result = runner.invoke(publish_action, ["--path", "test.tar.gz"], input="")

        assert result.exit_code != 0
        assert isinstance(result.exception, ValueError)

    def test_publish_action_invalid_path(self, mocker: MockerFixture) -> None:
        """Test handling of invalid path."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = False
        mock_os_path.exists.return_value = False

        runner = CliRunner()
        result = runner.invoke(publish_action, ["--path", "invalid/path"])

        assert result.exit_code == 0
        assert (
            "Unable to publish action from the path: invalid/path, unsupported file format"
            in result.output
        )

    def test_publish_agent_with_default_visibility(self, mocker: MockerFixture) -> None:
        """Test publishing an agent with default visibility."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = True
        mock_os_path.exists.return_value = True
        mock_os_path.join.return_value = "test/path/info.yaml"

        mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data=b"package:\n  name: test/test_agent\n  dependencies: {}"
            ),
        )

        mock_yaml = mocker.patch("jvcli.commands.publish.yaml")
        mock_validate_yaml_format = mocker.patch(
            "jvcli.commands.publish.validate_yaml_format"
        )
        mock_validate_yaml_format.return_value = True
        mocker.patch("jvcli.commands.publish.validate_package_name")
        mock_prepare_package = mocker.patch("jvcli.commands.publish._prepare_package")
        mock_prepare_package.return_value = "test.tar.gz"

        mock_yaml.safe_load.return_value = {
            "package": {
                "name": "test/test_agent",
                "dependencies": {},
            }
        }

        mock_registry_api = mocker.patch("jvcli.commands.publish.RegistryAPI")
        mock_registry_api.publish_action.return_value = True

        runner = CliRunner()
        result = runner.invoke(publish_agent, ["--path", "test/path"])

        assert result.exit_code == 0
        mock_registry_api.publish_action.assert_called_once_with(
            "test.tar.gz", "public", "test-token", "test"
        )

    def test_publish_agent_missing_namespace_for_tarball(
        self, mocker: MockerFixture
    ) -> None:
        """Test that publishing with a tarball fails if --namespace is missing."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = False
        mock_os_path.exists.return_value = True

        runner = CliRunner()
        result = runner.invoke(publish_agent, ["--path", "test.tar.gz"], input="")

        assert result.exit_code != 0
        assert isinstance(result.exception, ValueError)

    def test_package_with_mismatched_namespace(self, mocker: MockerFixture) -> None:
        """Test preparing a package with an output directory."""
        mock_load_token = mocker.patch("jvcli.commands.publish.load_token")
        mock_load_token.return_value = {"token": "test-token"}

        mock_os_path = mocker.patch("jvcli.commands.publish.os.path")
        mock_os_path.isdir.return_value = True
        mock_os_path.exists.return_value = True
        mock_os_path.join.return_value = "test/path/info.yaml"

        mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data="package:\n  name: test/test_action\n  dependencies: {}"
            ),
        )

        mock_yaml = mocker.patch("jvcli.commands.publish.yaml")
        mock_yaml.safe_load.return_value = {
            "package": {
                "name": "test/test_action",
                "dependencies": {},
            }
        }

        mock_validate_yaml_format = mocker.patch(
            "jvcli.commands.publish.validate_yaml_format"
        )
        mock_validate_yaml_format.return_value = True

        mocker.patch("jvcli.commands.publish.validate_package_name")

        runner = CliRunner()
        result = runner.invoke(
            publish_action, ["--path", "test/path", "--namespace", "different"]
        )

        assert result.exit_code == 0
        assert (
            "Error validating namespace: You provided 'different', but 'test' was found in the package info file."
            in result.output
        )

    def test_prepare_package_with_output_dir(self, mocker: MockerFixture) -> None:
        """Test preparing a package with an output directory."""
        mock_compress = mocker.patch("jvcli.commands.publish.compress_package_to_tgz")
        mock_compress.return_value = "/output/dir/namespace_package.tar.gz"

        mock_click = mocker.patch("jvcli.commands.publish.click.secho")

        result = _prepare_package(
            namespace="namespace",
            name="package",
            path="/source/path",
            publish_type="action",
            output="/output/dir",
        )

        mock_compress.assert_called_once_with(
            "/source/path", "/output/dir/namespace_package.tar.gz"
        )
        mock_click.assert_called_once_with(
            "Compressed action to: /output/dir/namespace_package.tar.gz", fg="yellow"
        )
        assert result == "/output/dir/namespace_package.tar.gz"
