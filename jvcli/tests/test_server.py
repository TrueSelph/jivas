"""Tests for the server command group."""

import json
import os
from unittest.mock import MagicMock

import requests
from click.testing import CliRunner
from pytest_mock import MockerFixture

from jvcli.commands.server import server


class TestImportAgentCommand:
    """Test cases for the importagent command."""

    def test_successful_agent_import(self, mocker: MockerFixture) -> None:
        """Test importing an agent successfully."""
        # Mock dependencies
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mock_requests = mocker.patch("jvcli.commands.server.requests.post")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test_agent_id"}
        mock_requests.return_value = mock_response
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mocker.patch("jvcli.commands.server.sys.exit")

        # Set environment variables
        mocker.patch.dict(os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"})

        # Run command
        runner = CliRunner()
        result = runner.invoke(server, ["importagent", "test_agent_name"])

        # Verify behavior
        assert result.exit_code == 0
        mock_requests.assert_called_once_with(
            "http://localhost:8000/walker/import_agent",
            json={"daf_name": "test_agent_name", "daf_version": "latest"},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer test_token",
            },
        )
        mock_click.assert_any_call("Logged in to Jivas successfully.", fg="green")
        mock_click.assert_any_call(
            "Successfully imported agent. Agent ID: test_agent_id", fg="green"
        )

    def test_server_not_running(self, mocker: MockerFixture) -> None:
        """Test behavior when server is not running."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=False)
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mock_exit = mocker.patch("jvcli.commands.server.sys.exit")

        # Mock environment variables needed for login
        mocker.patch.dict(
            os.environ,
            {
                "JIVAS_USER": "test_user",
                "JIVAS_PASSWORD": "test_password",  # pragma: allowlist secret
            },
        )

        runner = CliRunner()
        runner.invoke(server, ["importagent", "test_agent_name"])

        # Since sys.exit is mocked, the exit_code is 0
        assert mock_exit.called
        mock_click.assert_called_with(
            "Server is not running. Please start the server first.", fg="red"
        )

    def test_failed_login(self, mocker: MockerFixture) -> None:
        """Test behavior when login fails."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value=None)
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mock_exit = mocker.patch("jvcli.commands.server.sys.exit")
        # Prevent actual API calls
        mocker.patch("jvcli.commands.server.requests.post")

        # Mock environment variables
        mocker.patch.dict(
            os.environ,
            {
                "JIVAS_USER": "test_user",
                "JIVAS_PASSWORD": "test_password",  # pragma: allowlist secret
            },
        )

        runner = CliRunner()
        runner.invoke(server, ["importagent", "test_agent_name"])

        # Verify exit was called
        assert mock_exit.called
        # Check if the specific message was called with the right parameters
        mock_click.assert_any_call("Failed to login to Jivas.", fg="red")

    def test_failed_api_request(self, mocker: MockerFixture) -> None:
        """Test behavior when API request fails."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mocker.patch(
            "jvcli.commands.server.requests.post",
            side_effect=requests.RequestException("Network error"),
        )
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mocker.patch("jvcli.commands.server.sys.exit")

        runner = CliRunner()
        result = runner.invoke(server, ["importagent", "test_agent_name"])

        assert result.exit_code == 0
        mock_click.assert_any_call("Request failed: Network error", fg="red")

    def test_invalid_json_response(self, mocker: MockerFixture) -> None:
        """Test behavior when server returns invalid JSON."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mocker.patch("jvcli.commands.server.requests.post", return_value=mock_response)
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mocker.patch("jvcli.commands.server.sys.exit")

        runner = CliRunner()
        result = runner.invoke(server, ["importagent", "test_agent_name"])

        assert result.exit_code == 0
        mock_click.assert_any_call("Invalid JSON response from server", fg="red")

    def test_error_response(self, mocker: MockerFixture) -> None:
        """Test behavior when server returns error status code."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error message"
        mocker.patch("jvcli.commands.server.requests.post", return_value=mock_response)
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mock_echo = mocker.patch("jvcli.commands.server.click.echo")
        mocker.patch("jvcli.commands.server.sys.exit")

        runner = CliRunner()
        result = runner.invoke(server, ["importagent", "test_agent_name"])

        assert result.exit_code == 0
        mock_click.assert_any_call("Failed to import agent. Status: 400", fg="red")
        mock_echo.assert_called_once_with("Error message")

    def test_agent_import_with_specified_version(self, mocker: MockerFixture) -> None:
        """Test importing an agent with a specific version."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test_agent_id"}
        mock_requests = mocker.patch(
            "jvcli.commands.server.requests.post", return_value=mock_response
        )
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mocker.patch.dict(os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"})

        runner = CliRunner()
        result = runner.invoke(server, ["importagent", "test_agent_name", "1.0.0"])

        assert result.exit_code == 0
        mock_requests.assert_called_once_with(
            "http://localhost:8000/walker/import_agent",
            json={"daf_name": "test_agent_name", "daf_version": "1.0.0"},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer test_token",
            },
        )
        mock_click.assert_any_call(
            "Successfully imported agent. Agent ID: test_agent_id", fg="green"
        )

    def test_missing_agent_id_in_response(self, mocker: MockerFixture) -> None:
        """Test handling of response without agent ID."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Success but no ID"}
        mocker.patch("jvcli.commands.server.requests.post", return_value=mock_response)
        mock_click = mocker.patch("jvcli.commands.server.click.secho")

        runner = CliRunner()
        result = runner.invoke(server, ["importagent", "test_agent_name"])

        assert result.exit_code == 0
        mock_click.assert_any_call(
            "Agent imported but no ID was returned in the response", fg="yellow"
        )


class TestInitAgentsCommand:
    """Test cases for the initagents command."""

    def test_successful_initialization(self, mocker: MockerFixture) -> None:
        """Test initializing agents successfully."""
        # Mock dependencies
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mock_requests = mocker.patch("jvcli.commands.server.requests.post")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["agent_1", "agent_2"]
        mock_requests.return_value = mock_response
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mocker.patch("jvcli.commands.server.sys.exit")

        # Set environment variables
        mocker.patch.dict(os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"})

        # Run command
        runner = CliRunner()
        result = runner.invoke(server, ["initagents"])

        # Verify behavior
        assert result.exit_code == 0
        mock_requests.assert_called_once_with(
            "http://localhost:8000/walker/init_agents",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer test_token",
            },
            json={},
        )
        mock_click.assert_any_call("Logged in to Jivas successfully.", fg="green")
        mock_click.assert_any_call(
            "Successfully initialized agents: ['agent_1', 'agent_2']", fg="green"
        )

    def test_server_not_running(self, mocker: MockerFixture) -> None:
        """Test behavior when server is not running."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=False)
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mock_exit = mocker.patch("jvcli.commands.server.sys.exit")

        # Mock environment variables needed for login
        mocker.patch.dict(
            os.environ,
            {
                "JIVAS_USER": "test_user",
                "JIVAS_PASSWORD": "test_password",  # pragma: allowlist secret
            },
        )

        runner = CliRunner()
        runner.invoke(server, ["initagents"])

        # Since sys.exit is mocked, the exit_code is 0
        assert mock_exit.called
        mock_click.assert_called_with(
            "Server is not running. Please start the server first.", fg="red"
        )

    def test_failed_login(self, mocker: MockerFixture) -> None:
        """Test behavior when login fails."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value=None)
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mock_exit = mocker.patch("jvcli.commands.server.sys.exit")
        # Prevent actual API calls
        mocker.patch("jvcli.commands.server.requests.post")

        # Mock environment variables
        mocker.patch.dict(
            os.environ,
            {
                "JIVAS_USER": "test_user",
                "JIVAS_PASSWORD": "test_password",  # pragma: allowlist secret
            },
        )

        runner = CliRunner()
        runner.invoke(server, ["initagents"])

        # Verify exit was called
        assert mock_exit.called
        # Check if the specific message was called with the right parameters
        mock_click.assert_any_call("Failed to login to Jivas.", fg="red")

    def test_failed_api_request(self, mocker: MockerFixture) -> None:
        """Test behavior when API request fails."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mocker.patch(
            "jvcli.commands.server.requests.post",
            side_effect=requests.RequestException("Network error"),
        )
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mocker.patch("jvcli.commands.server.sys.exit")

        runner = CliRunner()
        result = runner.invoke(server, ["initagents"])

        assert result.exit_code == 0
        mock_click.assert_any_call("Error during request: Network error", fg="red")

    def test_error_response(self, mocker: MockerFixture) -> None:
        """Test behavior when server returns error status code."""
        mocker.patch("jvcli.commands.server.is_server_running", return_value=True)
        mocker.patch("jvcli.commands.server.login_jivas", return_value="test_token")
        mock_response = MagicMock()
        mock_response.status_code = 400
        mocker.patch("jvcli.commands.server.requests.post", return_value=mock_response)
        mock_click = mocker.patch("jvcli.commands.server.click.secho")
        mocker.patch("jvcli.commands.server.sys.exit")

        runner = CliRunner()
        result = runner.invoke(server, ["initagents"])

        assert result.exit_code == 0
        mock_click.assert_any_call("Failed to initialize agents", fg="red")


class TestLaunchCommand:
    """Test cases for the launch command."""

    def test_launch_default_file(self, mocker: MockerFixture) -> None:
        """Test launching the server with the default JAC file."""
        # Mock subprocess.call
        mock_subprocess = mocker.patch("jvcli.commands.server.subprocess.call")

        # Run command
        runner = CliRunner()
        result = runner.invoke(server, ["launch"])

        # Verify behavior
        assert result.exit_code == 0
        assert "Launching Jivas Server with JAC file: main.jac" in result.output
        mock_subprocess.assert_called_once_with(["jac", "jvserve", "main.jac"])

    def test_launch_custom_file(self, mocker: MockerFixture) -> None:
        """Test launching the server with a custom JAC file."""
        # Mock subprocess.call
        mock_subprocess = mocker.patch("jvcli.commands.server.subprocess.call")

        # Run command
        runner = CliRunner()
        result = runner.invoke(server, ["launch", "--jac-file", "custom.jac"])

        # Verify behavior
        assert result.exit_code == 0
        assert "Launching Jivas Server with JAC file: custom.jac" in result.output
        mock_subprocess.assert_called_once_with(["jac", "jvserve", "custom.jac"])


class TestLoginCommand:
    """Test cases for the login command."""

    def test_successful_login_with_args(self, mocker: MockerFixture) -> None:
        """Test login with provided email and password arguments."""
        # Mock the requests.post call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "test_token_123"}
        mock_post = mocker.patch(
            "jvcli.commands.server.requests.post", return_value=mock_response
        )

        # Mock environment variables
        mocker.patch.dict(os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"})

        # Run command with arguments
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["login", "--email", "test@example.com", "--password", "password123"],
        )

        # Verify behavior
        assert result.exit_code == 0
        assert "Login successful!" in result.output
        assert "Token: test_token_123" in result.output

        # Verify API call
        mock_post.assert_called_once_with(
            "http://localhost:8000/user/login",
            json={
                "email": "test@example.com",
                "password": "password123",  # pragma: allowlist secret
            },
        )

        # Verify token stored in environment
        assert os.environ.get("JIVAS_TOKEN") == "test_token_123"

    def test_successful_login_with_env_vars(self, mocker: MockerFixture) -> None:
        """Test login with credentials from environment variables."""
        # Mock the requests.post call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "test_token_123"}
        mock_post = mocker.patch(
            "jvcli.commands.server.requests.post", return_value=mock_response
        )

        # Mock environment variables
        mocker.patch.dict(
            os.environ,
            {
                "JIVAS_BASE_URL": "http://localhost:8000",
                "JIVAS_USER": "env_user@example.com",
                "JIVAS_PASSWORD": "env_password",  # pragma: allowlist secret
            },
        )

        # Run command without arguments
        runner = CliRunner()
        result = runner.invoke(server, ["login"])

        # Verify behavior
        assert result.exit_code == 0
        assert "Login successful!" in result.output

        # Verify API call used env var credentials
        mock_post.assert_called_once_with(
            "http://localhost:8000/user/login",
            json={
                "email": "env_user@example.com",
                "password": "env_password",  # pragma: allowlist secret
            },
        )

    def test_failed_login_api_error(self, mocker: MockerFixture) -> None:
        """Test behavior when login API returns an error."""
        # Mock the requests.post call
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"
        mocker.patch("jvcli.commands.server.requests.post", return_value=mock_response)

        # Run command
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["login", "--email", "test@example.com", "--password", "wrong_password"],
        )

        # Verify behavior
        assert (
            result.exit_code == 0
        )  # Exit code is 0 because we handle the error in the code
        assert "Login failed: Invalid credentials" in result.output

    def test_login_connection_error(self, mocker: MockerFixture) -> None:
        """Test behavior when connection to server fails."""
        # Mock requests.post to raise an exception
        mocker.patch(
            "jvcli.commands.server.requests.post",
            side_effect=requests.RequestException("Connection refused"),
        )

        # Run command
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["login", "--email", "test@example.com", "--password", "password123"],
        )

        # Verify behavior
        assert (
            result.exit_code == 0
        )  # Exit code is 0 because we handle the error in the code
        assert "Error connecting to Jivas Server: Connection refused" in result.output

    def test_login_with_prompts_for_both(self, mocker: MockerFixture) -> None:
        """Test login with interactive prompts for both email and password."""
        # Mock click.prompt to simulate user input
        mock_prompt = mocker.patch("jvcli.commands.server.click.prompt")
        mock_prompt.side_effect = ["prompted_email@example.com", "prompted_password"]

        # Mock requests response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "test_token_123"}
        mock_post = mocker.patch(
            "jvcli.commands.server.requests.post", return_value=mock_response
        )

        # Clear environment variables to force prompting
        mocker.patch.dict(
            os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"}, clear=True
        )

        # Run command without arguments
        runner = CliRunner()
        result = runner.invoke(server, ["login"])

        # Verify behavior
        assert result.exit_code == 0
        assert "Login successful!" in result.output

        # Verify prompt calls
        assert mock_prompt.call_count == 2
        mock_prompt.assert_any_call("Email")
        mock_prompt.assert_any_call("Password", hide_input=True)

        # Verify API call used prompted credentials
        mock_post.assert_called_once_with(
            "http://localhost:8000/user/login",
            json={
                "email": "prompted_email@example.com",
                "password": "prompted_password",  # pragma: allowlist secret
            },
        )

    def test_login_with_prompt_for_password_only(self, mocker: MockerFixture) -> None:
        """Test login with email provided but password prompted."""
        # Mock click.prompt for password only
        mock_prompt = mocker.patch("jvcli.commands.server.click.prompt")
        mock_prompt.return_value = "prompted_password"

        # Mock requests response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "test_token_123"}
        mock_post = mocker.patch(
            "jvcli.commands.server.requests.post", return_value=mock_response
        )

        # Clear environment variables to force prompting
        mocker.patch.dict(
            os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"}, clear=True
        )

        # Run command with email only
        runner = CliRunner()
        result = runner.invoke(server, ["login", "--email", "email_arg@example.com"])

        # Verify behavior
        assert result.exit_code == 0
        assert "Login successful!" in result.output

        # Verify prompt was called once for password
        mock_prompt.assert_called_once_with("Password", hide_input=True)

        # Verify API call used provided email and prompted password
        mock_post.assert_called_once_with(
            "http://localhost:8000/user/login",
            json={
                "email": "email_arg@example.com",
                "password": "prompted_password",  # pragma: allowlist secret
            },
        )


class TestCreateAdminCommand:
    """Test cases for the createadmin command."""

    def test_createadmin_using_signup_endpoint(self, mocker: MockerFixture) -> None:
        """Test creating admin user using the signup endpoint."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "new_admin_id"}
        mock_post = mocker.patch(
            "jvcli.commands.server.requests.post", return_value=mock_response
        )

        # Environment without DATABASE_HOST
        mocker.patch.dict(
            os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"}, clear=True
        )

        # Run command
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["createadmin", "--email", "admin@example.com", "--password", "admin123"],
        )

        # Verify behavior
        assert result.exit_code == 0
        assert "Admin user created successfully!" in result.output

        # Verify API endpoint was called
        mock_post.assert_called_once_with(
            "http://localhost:8000/user/register",
            json={
                "email": "admin@example.com",
                "password": "admin123",  # pragma: allowlist secret
            },
        )

    def test_createadmin_using_jac_command(self, mocker: MockerFixture) -> None:
        """Test creating admin user using the jac command."""
        # Mock subprocess.call successful return
        mock_subprocess = mocker.patch(
            "jvcli.commands.server.subprocess.call", return_value=0
        )

        # Environment with DATABASE_HOST
        mocker.patch.dict(
            os.environ,
            {
                "DATABASE_HOST": "postgres:5432",
                "JIVAS_BASE_URL": "http://localhost:8000",
            },
        )

        # Run command
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["createadmin", "--email", "admin@example.com", "--password", "admin123"],
        )

        # Verify behavior
        assert result.exit_code == 0
        assert "Creating system admin..." in result.output
        assert "Admin user created successfully!" in result.output

        # Verify jac command was called
        mock_subprocess.assert_called_once_with(
            [
                "jac",
                "create_system_admin",
                "main.jac",
                "--email",
                "admin@example.com",
                "--password",
                "admin123",
            ]
        )

    def test_failed_signup_endpoint(self, mocker: MockerFixture) -> None:
        """Test behavior when signup endpoint returns an error."""
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Email already exists"
        mocker.patch("jvcli.commands.server.requests.post", return_value=mock_response)

        # Environment without DATABASE_HOST
        mocker.patch.dict(
            os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"}, clear=True
        )

        # Run command
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["createadmin", "--email", "admin@example.com", "--password", "admin123"],
        )

        # Verify behavior
        assert result.exit_code == 0
        assert "Failed to create admin: Email already exists" in result.output

    def test_failed_jac_command(self, mocker: MockerFixture) -> None:
        """Test behavior when jac command fails."""
        # Mock subprocess.call failure
        mocker.patch("jvcli.commands.server.subprocess.call", return_value=1)

        # Environment with DATABASE_HOST
        mocker.patch.dict(os.environ, {"DATABASE_HOST": "postgres:5432"})

        # Run command
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["createadmin", "--email", "admin@example.com", "--password", "admin123"],
        )

        # Verify behavior
        assert result.exit_code == 0
        assert "Failed to create admin user" in result.output

    def test_createadmin_with_prompts(self, mocker: MockerFixture) -> None:
        """Test creating admin with interactive prompts for credentials."""
        # Mock prompts
        mock_prompt = mocker.patch("jvcli.commands.server.click.prompt")
        mock_prompt.side_effect = ["prompted_admin@example.com", "prompted_password"]

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "new_admin_id"}
        mock_post = mocker.patch(
            "jvcli.commands.server.requests.post", return_value=mock_response
        )

        # Environment with no credentials
        mocker.patch.dict(
            os.environ, {"JIVAS_BASE_URL": "http://localhost:8000"}, clear=True
        )

        # Run command without args
        runner = CliRunner()
        result = runner.invoke(server, ["createadmin"])

        # Verify behavior
        assert result.exit_code == 0
        assert "Admin user created successfully!" in result.output

        # Verify prompts were called
        assert mock_prompt.call_count == 2
        mock_prompt.assert_any_call("Email")
        mock_prompt.assert_any_call("Password", hide_input=True)

        # Verify API call used prompted credentials
        mock_post.assert_called_once_with(
            "http://localhost:8000/user/register",
            json={
                "email": "prompted_admin@example.com",
                "password": "prompted_password",  # pragma: allowlist secret
            },
        )

    def test_createadmin_connection_error(self, mocker: MockerFixture) -> None:
        """Test behavior when connection to server fails."""
        # Mock request exception
        mocker.patch(
            "jvcli.commands.server.requests.post",
            side_effect=requests.RequestException("Connection refused"),
        )

        # Run command
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["createadmin", "--email", "admin@example.com", "--password", "admin123"],
        )

        # Verify behavior
        assert result.exit_code == 0
        assert "Error connecting to Jivas Server: Connection refused" in result.output

    def test_createadmin_jac_command_exception(self, mocker: MockerFixture) -> None:
        """Test behavior when jac command raises an exception."""
        # Mock subprocess to raise an exception
        mocker.patch(
            "jvcli.commands.server.subprocess.call",
            side_effect=Exception("Command not found"),
        )

        # Environment with DATABASE_HOST
        mocker.patch.dict(os.environ, {"DATABASE_HOST": "postgres:5432"})

        # Run command
        runner = CliRunner()
        result = runner.invoke(
            server,
            ["createadmin", "--email", "admin@example.com", "--password", "admin123"],
        )

        # Verify behavior
        assert result.exit_code == 0
        assert "Error running jac command: Command not found" in result.output
