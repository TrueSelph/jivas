"""Simple test for client launch command."""

from unittest.mock import patch

from click.testing import CliRunner

from jvcli.commands.client import launch


def test_client_launch_runs() -> None:
    """Test that client launch command runs without errors."""
    runner = CliRunner()

    with patch("subprocess.call") as mock_subprocess:
        mock_subprocess.return_value = 0

        result = runner.invoke(launch)

        assert result.exit_code == 0
        mock_subprocess.assert_called_once_with(["jvmanager", "launch"])


def test_client_launch_file_not_found() -> None:
    """Test that client launch handles jvmanager not found."""
    runner = CliRunner()

    with patch("subprocess.call") as mock_subprocess:
        mock_subprocess.side_effect = FileNotFoundError()

        result = runner.invoke(launch)

        assert result.exit_code == 0
        assert "jvmanager' command not found" in result.output


def test_client_launch_general_error() -> None:
    """Test that client launch handles general errors."""
    runner = CliRunner()

    with patch("subprocess.call") as mock_subprocess:
        mock_subprocess.side_effect = Exception("Test error")

        result = runner.invoke(launch)

        assert result.exit_code == 0
        assert "An error occurred: Test error" in result.output
