"""Tests for the CLI module."""

import click.testing

from jvcli.cli import jvcli


class TestCli:
    """Test cases for the CLI module."""

    def test_cli_initialization_registers_all_commands(self) -> None:
        """Test that CLI initializes with all commands registered correctly."""
        # Act
        runner = click.testing.CliRunner()
        result = runner.invoke(jvcli, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "create" in result.output
        assert "update" in result.output
        assert "download" in result.output
        assert "publish" in result.output
        assert "info" in result.output
        assert "server" in result.output
        assert "signup" in result.output
        assert "login" in result.output
        assert "logout" in result.output

    def test_cli_version(self) -> None:
        """Test that CLI version command works correctly."""
        # Act
        runner = click.testing.CliRunner()
        result = runner.invoke(jvcli, ["--version"])

        # Assert
        assert result.exit_code == 0
        assert "jvcli, version" in result.output

    def test_cli_no_command(self) -> None:
        """Test that CLI displays usage information when no command is provided."""
        runner = click.testing.CliRunner()
        result = runner.invoke(jvcli)
        assert "Usage:" in result.output
        assert "Commands:" in result.output
