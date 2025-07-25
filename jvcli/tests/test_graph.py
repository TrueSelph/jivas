"""Tests for the graph command."""

from click.testing import CliRunner
from pytest_mock import MockerFixture

from jvcli.commands.graph import launch


class TestGraph:
    """Test cases for the graph command."""

    def test_launch_graph_default_port(self, mocker: MockerFixture) -> None:
        """Test launching graph with default port."""
        # Mock subprocess.run
        mock_subprocess_run = mocker.patch("jvcli.commands.graph.subprocess.run")

        # Create CLI runner
        runner = CliRunner()

        # Run the command
        result = runner.invoke(launch)

        # Verify the command executed successfully
        assert result.exit_code == 0

        # Verify subprocess.run was called with correct arguments
        mock_subprocess_run.assert_called_once_with(
            ["jvgraph", "launch", "--port", "8989", "--require-auth", "False"]
        )

    def test_launch_graph_custom_port(self, mocker: MockerFixture) -> None:
        """Test launching graph with custom port."""
        # Mock subprocess.run
        mock_subprocess_run = mocker.patch("jvcli.commands.graph.subprocess.run")

        # Create CLI runner
        runner = CliRunner()

        # Run the command with custom port
        result = runner.invoke(launch, ["--port", "9000"])

        # Verify the command executed successfully
        assert result.exit_code == 0

        # Verify subprocess.run was called with correct arguments
        mock_subprocess_run.assert_called_once_with(
            ["jvgraph", "launch", "--port", "9000", "--require-auth", "False"]
        )

    def test_launch_graph_with_auth(self, mocker: MockerFixture) -> None:
        """Test launching graph with authentication required."""
        # Mock subprocess.run
        mock_subprocess_run = mocker.patch("jvcli.commands.graph.subprocess.run")

        # Create CLI runner
        runner = CliRunner()

        # Run the command with auth enabled
        result = runner.invoke(launch, ["--require-auth", "True"])

        # Verify the command executed successfully
        assert result.exit_code == 0

        # Verify subprocess.run was called with correct arguments
        mock_subprocess_run.assert_called_once_with(
            ["jvgraph", "launch", "--port", "8989", "--require-auth", "True"]
        )

    def test_launch_graph_custom_port_and_auth(self, mocker: MockerFixture) -> None:
        """Test launching graph with custom port and authentication."""
        # Mock subprocess.run
        mock_subprocess_run = mocker.patch("jvcli.commands.graph.subprocess.run")

        # Create CLI runner
        runner = CliRunner()

        # Run the command with custom port and auth
        result = runner.invoke(launch, ["--port", "9001", "--require-auth", "True"])

        # Verify the command executed successfully
        assert result.exit_code == 0

        # Verify subprocess.run was called with correct arguments
        mock_subprocess_run.assert_called_once_with(
            ["jvgraph", "launch", "--port", "9001", "--require-auth", "True"]
        )
