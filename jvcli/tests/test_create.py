"""Tests for the create module."""

import os

from click.testing import CliRunner
from pytest_mock import MockerFixture

from jvcli import __supported__jivas__versions__  # type: ignore[attr-defined]
from jvcli.commands.create import create_action, create_agent, create_namespace
from jvcli.utils import TEMPLATES_DIR


class TestCreateCommand:
    """Test cases for the create command."""

    def test_create_action_with_valid_name_and_defaults(
        self, mocker: MockerFixture
    ) -> None:
        """Test creating an action with valid name and default values."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mock_makedirs = mocker.patch("os.makedirs")
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(
            create_action,
            [
                "--name",
                "test_action",
                "--jivas_version",
                __supported__jivas__versions__[0],
            ],
        )

        assert result.exit_code == 0
        mock_makedirs.assert_has_calls(
            [
                mocker.call("./actions/testuser/test_action", exist_ok=True),
                mocker.call("./actions/testuser/test_action/app", exist_ok=True),
            ],
            any_order=True,
        )

        mock_open.assert_any_call("./actions/testuser/test_action/info.yaml", "w")
        mock_open.assert_any_call("./actions/testuser/test_action/app/app.py", "w")

        mock_click.assert_called_with(
            "Action 'test_action' created successfully in ./actions/testuser/test_action!",
            fg="green",
            bold=True,
        )

    def test_create_action_generates_correct_file_structure(
        self, mocker: MockerFixture
    ) -> None:
        """Test that create_action generates the correct file structure."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mock_makedirs = mocker.patch("os.makedirs")
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(create_action, ["--name", "test_action"])

        assert result.exit_code == 0
        mock_makedirs.assert_has_calls(
            [
                mocker.call("./actions/testuser/test_action", exist_ok=True),
                mocker.call("./actions/testuser/test_action/app", exist_ok=True),
            ],
            any_order=True,
        )

        mock_open.assert_any_call("./actions/testuser/test_action/info.yaml", "w")
        mock_open.assert_any_call("./actions/testuser/test_action/lib.jac", "w")
        mock_open.assert_any_call("./actions/testuser/test_action/test_action.jac", "w")
        mock_open.assert_any_call("./actions/testuser/test_action/app/app.py", "w")

        mock_click.assert_called_with(
            "Action 'test_action' created successfully in ./actions/testuser/test_action!",
            fg="green",
            bold=True,
        )

    def test_appends_correct_suffix_based_on_action_type(
        self, mocker: MockerFixture
    ) -> None:
        """Test that the correct suffix is appended based on action type."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mock_makedirs = mocker.patch("os.makedirs")
        mocker.patch("builtins.open", mocker.mock_open())
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(
            create_action, ["--name", "test", "--type", "interact_action"]
        )

        assert result.exit_code == 0
        expected_name = "test_interact_action"
        mock_makedirs.assert_any_call(
            f"./actions/testuser/{expected_name}", exist_ok=True
        )
        mock_click.assert_called_with(
            f"Action '{expected_name}' created successfully in ./actions/testuser/{expected_name}!",
            fg="green",
            bold=True,
        )

    def test_create_action_creates_documentation_files(
        self, mocker: MockerFixture
    ) -> None:
        """Test that documentation files are created with substituted values."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mocker.patch("os.makedirs")
        mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("click.secho")
        mock_create_docs = mocker.patch("jvcli.commands.create.create_docs")

        runner = CliRunner()
        result = runner.invoke(create_action, ["--name", "test_action"])

        assert result.exit_code == 0
        mock_create_docs.assert_called_once_with(
            "./actions/testuser/test_action",
            "Test Action",
            "0.0.1",
            "action",
            max(__supported__jivas__versions__),
            "No description provided.",
        )

    def test_create_action_with_invalid_jivas_version(
        self, mocker: MockerFixture
    ) -> None:
        """Test handling of invalid Jivas version."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mock_click = mocker.patch("click.secho")
        runner = CliRunner()
        result = runner.invoke(
            create_action, ["--name", "test_action", "--jivas_version", "1.0.0"]
        )
        assert result.exit_code == 0
        mock_click.assert_called_with(
            "Jivas version 1.0.0 is not supported. Supported versions are: {}.".format(
                str(__supported__jivas__versions__)
            ),
            fg="red",
        )

    def test_create_action_appends_suffix_when_missing(
        self, mocker: MockerFixture
    ) -> None:
        """Test that the suffix is appended to the name if it does not already have it."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mock_makedirs = mocker.patch("os.makedirs")
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(
            create_action, ["--name", "testaction"]  # Name without suffix
        )

        assert result.exit_code == 0
        expected_name_with_suffix = "testaction_action"
        mock_makedirs.assert_has_calls(
            [
                mocker.call(
                    f"./actions/testuser/{expected_name_with_suffix}", exist_ok=True
                ),
                mocker.call(
                    f"./actions/testuser/{expected_name_with_suffix}/app", exist_ok=True
                ),
            ],
            any_order=True,
        )

        mock_open.assert_any_call(
            f"./actions/testuser/{expected_name_with_suffix}/info.yaml", "w"
        )
        mock_open.assert_any_call(
            f"./actions/testuser/{expected_name_with_suffix}/app/app.py", "w"
        )

        mock_click.assert_called_with(
            f"Action '{expected_name_with_suffix}' created successfully in ./actions/testuser/{expected_name_with_suffix}!",
            fg="green",
            bold=True,
        )

    def test_create_action_template_not_found(self, mocker: MockerFixture) -> None:
        """Test behavior when the template file is not found for the specified version."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mocker.patch("os.makedirs")
        mocker.patch("builtins.open", mocker.mock_open())
        mock_click = mocker.patch("click.secho")
        mocker.patch("os.path.exists", return_value=False)

        runner = CliRunner()
        result = runner.invoke(
            create_action,
            [
                "--name",
                "test_action",
                "--jivas_version",
                __supported__jivas__versions__[0],
            ],
        )

        assert result.exit_code == 0
        mock_click.assert_called_with(
            f"Template for version {__supported__jivas__versions__[0]} not found in {TEMPLATES_DIR}.",
            fg="red",
        )

    def test_create_namespace_success_with_valid_input(
        self, mocker: MockerFixture
    ) -> None:
        """Test creating a namespace successfully when user is logged in and provides valid name."""
        # Mock dependencies
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "token": "test_token",
            "email": "test@example.com",
            "namespaces": {"default": "anonymous", "groups": []},
        }

        mock_registry_api = mocker.patch(
            "jvcli.commands.create.RegistryAPI.create_namespace"
        )
        mock_registry_api.return_value = {"status": "success"}

        mock_save_token = mocker.patch("jvcli.commands.create.save_token")
        mock_click = mocker.patch("click.secho")

        # Run command
        runner = CliRunner()
        result = runner.invoke(create_namespace, ["--name", "testnamespace"])

        # Verify results
        assert result.exit_code == 0
        mock_registry_api.assert_called_once_with("testnamespace", "test_token")
        mock_save_token.assert_called_once_with(
            "test_token",
            {"default": "anonymous", "groups": ["testnamespace"]},
            "test@example.com",
        )
        mock_click.assert_called_with(
            "Namespace 'testnamespace' created successfully!", fg="green", bold=True
        )

    def test_create_namespace_user_not_logged_in(self, mocker: MockerFixture) -> None:
        """Test creating a namespace when the user is not logged in."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {}
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(create_namespace, ["--name", "testnamespace"])

        print(result.output)
        assert result.exit_code == 0
        mock_click.assert_called_with(
            "You are not logged in. Please log in before creating a namespace.",
            fg="red",
        )

    def test_create_namespace_empty_token_value(self, mocker: MockerFixture) -> None:
        """Test handling of empty token value in local configuration."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {"token": ""}
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(create_namespace, ["--name", "testnamespace"])

        assert result.exit_code == 0
        mock_click.assert_called_with(
            "Token missing from the local configuration. Please log in again.", fg="red"
        )

    def test_create_agent_with_valid_name_and_defaults(
        self, mocker: MockerFixture
    ) -> None:
        """Test creating an agent with valid name and default values."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "token": "test_token",
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mock_makedirs = mocker.patch("os.makedirs")
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(create_agent, ["--name", "test_agent"])

        assert result.exit_code == 0
        mock_makedirs.assert_called_with("./daf/testuser/test_agent", exist_ok=True)

        version = __supported__jivas__versions__[0]

        mock_open.assert_any_call(
            os.path.join(TEMPLATES_DIR, version, "sourcefiles", "agent_info.yaml"), "r"
        )
        mock_open.assert_any_call(
            os.path.join(TEMPLATES_DIR, version, "sourcefiles", "agent_knowledge.yaml"),
            "r",
        )
        mock_open.assert_any_call(
            os.path.join(
                TEMPLATES_DIR, version, "sourcefiles", "agent_descriptor.yaml"
            ),
            "r",
        )
        mock_open.assert_any_call(
            os.path.join(TEMPLATES_DIR, version, "sourcefiles", "agent_memory.yaml"),
            "r",
        )
        mock_open.assert_any_call("./daf/testuser/test_agent/info.yaml", "w")
        mock_open.assert_any_call("./daf/testuser/test_agent/descriptor.yaml", "w")
        mock_open.assert_any_call("./daf/testuser/test_agent/knowledge.yaml", "w")
        mock_open.assert_any_call("./daf/testuser/test_agent/memory.yaml", "w")

        mock_click.assert_called_with(
            "Agent 'test_agent' created successfully in ./daf/testuser/test_agent!",
            fg="green",
            bold=True,
        )

    def test_create_agent_with_unsupported_jivas_version(
        self, mocker: MockerFixture
    ) -> None:
        """Test creating an agent with an unsupported Jivas version."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(
            create_agent, ["--name", "test_agent", "--jivas_version", "1.0.0"]
        )

        assert result.exit_code == 0
        mock_click.assert_called_with(
            f"Jivas version 1.0.0 is not supported. Supported versions are: ['{__supported__jivas__versions__[0]}'].",
            fg="red",
        )

    def test_create_agent_missing_template(self, mocker: MockerFixture) -> None:
        """Test create_agent when a template is missing."""
        mock_load_token = mocker.patch("jvcli.commands.create.load_token")
        mock_load_token.return_value = {
            "email": "test@example.com",
            "namespaces": {"default": "testuser"},
        }
        mocker.patch("os.makedirs")
        mock_click = mocker.patch("click.secho")
        mocker.patch(
            "os.path.exists",
            side_effect=lambda path: "agent_info.yaml" not in path,
        )

        runner = CliRunner()
        result = runner.invoke(create_agent, ["--name", "test_agent"])

        assert result.exit_code == 0
        mock_click.assert_called_with(
            "Template info.yaml not found in TEMPLATES_DIR.", fg="red"
        )
