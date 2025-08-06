"""Tests for jvcli startproject command."""

import os

from click.testing import CliRunner
from pytest_mock import MockerFixture

from jvcli import __supported__jivas__versions__  # type: ignore[attr-defined]
from jvcli.commands.startproject import startproject


class TestStartProjectCommand:
    """Test cases for the startproject command."""

    def test_create_project_with_default_version(self, mocker: MockerFixture) -> None:
        """Create project with default version and verify structure."""

        # Mock file system operations
        mock_makedirs = mocker.patch("os.makedirs")
        mocker.patch("os.path.exists", side_effect=lambda path: path != "test_project")

        # Mock open with support for both text and binary modes
        mock_file = mocker.mock_open(read_data=b"template content")
        mock_open = mocker.patch("builtins.open", mock_file)

        # Mock click.secho to prevent actual console output
        mock_click = mocker.patch("click.secho")

        # Run command
        runner = CliRunner()
        result = runner.invoke(startproject, ["test_project"])

        # Verify project directory creation
        mock_makedirs.assert_any_call("test_project", exist_ok=True)

        # Verify subdirectories creation
        expected_dirs = ["tests", "actions", "daf"]
        for dir_name in expected_dirs:
            mock_makedirs.assert_any_call(
                os.path.join("test_project", dir_name), exist_ok=True
            )

        # Verify template files creation
        expected_files = [
            "main.jac",
            "globals.jac",
            ".env",
            "env.example",
            ".gitignore",
            "gitignore.example",
            "README.md",
            "actions/README.md",
            "daf/README.md",
            "tests/README.md",
        ]

        mock_calls = mock_open.mock_calls
        written_files = {
            os.path.normpath(call.args[0])
            for call in mock_calls
            if "test_project" in str(call)
        }
        normalized_expected_files = [
            os.path.normpath(os.path.join("test_project", file))
            for file in expected_files
        ]
        assert set(written_files) == set(normalized_expected_files)

        # Verify success message
        mock_click.assert_called_with(
            f"Successfully created Jivas project: test_project (Version: {max(__supported__jivas__versions__)})",
            fg="green",
        )

        assert result.exit_code == 0

    def test_template_path_does_not_exist(self, mocker: MockerFixture) -> None:
        """Test behavior when the template path does not exist."""
        mocker.patch("os.path.exists", return_value=False)
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(startproject, ["test_project"])

        assert result.exit_code == 0
        mock_click.assert_called_once_with(
            f"Template for Jivas version {__supported__jivas__versions__[0]} not found.",
            fg="red",
        )

    def test_exception_handling_during_project_creation(
        self, mocker: MockerFixture
    ) -> None:
        """Test exception handling during project creation."""
        mocker.patch("os.makedirs", side_effect=Exception("Mocked exception"))
        mock_click = mocker.patch("click.secho")

        runner = CliRunner()
        result = runner.invoke(
            startproject,
            ["test_project", "--version", __supported__jivas__versions__[0]],
        )

        assert result.exit_code == 0
        mock_click.assert_called_once_with(
            "Error creating project: Mocked exception", fg="red"
        )
