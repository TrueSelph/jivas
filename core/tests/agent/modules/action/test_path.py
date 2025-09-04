"""Test module for action path utilities.

This module contains comprehensive tests for path-related utilities used in action processing,
including path to module conversion, package folder finding, and path generation for walkers
and webhooks.
"""

from pathlib import Path
from typing import Optional, Set

import pytest

from jivas.agent.modules.action.path import (
    action_walker_path,
    action_webhook_path,
    find_package_folder,
    path_to_module,
)


class TestPath:
    """Test suite for action path utilities."""

    def test_path_to_module_basic(self) -> None:
        """Test basic path to module conversion.

        Verifies that a standard file path with multiple segments
        is correctly converted to a module path format.
        """
        result: str = path_to_module("/a/b/c")
        assert result == "a.b.c"

    def test_path_to_module_single_segment(self) -> None:
        """Test path to module with single segment.

        Verifies that a path with only one segment is handled correctly.
        """
        result: str = path_to_module("/test")
        assert result == "test"

    def test_path_to_module_no_leading_slash(self) -> None:
        """Test path to module without leading slash.

        Verifies that paths without leading slashes are processed correctly.
        """
        result: str = path_to_module("a/b/c")
        assert result == "a.b.c"

    def test_path_to_module_trailing_slash(self) -> None:
        """Test path to module with trailing slash.

        Verifies that trailing slashes are properly stripped during conversion.
        """
        result: str = path_to_module("/a/b/c/")
        assert result == "a.b.c"

    def test_path_to_module_empty_string(self) -> None:
        """Test path to module with empty string.

        Verifies that empty string input is handled gracefully.
        """
        result: str = path_to_module("")
        assert result == ""

    def test_find_package_folder_success(self, tmp_path: Path) -> None:
        """Test successful package folder finding.

        Creates a test directory structure and verifies that the package
        folder is found when it exists with required files.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        # Create test directory structure
        namespace_dir: Path = tmp_path / "test_namespace"
        namespace_dir.mkdir()
        package_dir: Path = namespace_dir / "test_package"
        package_dir.mkdir()
        info_file: Path = package_dir / "info.yaml"
        info_file.write_text("test content")

        result: Optional[str] = find_package_folder(
            str(tmp_path), "test_namespace/test_package"
        )
        assert result == str(package_dir)

    def test_find_package_folder_missing_namespace(self, tmp_path: Path) -> None:
        """Test package folder finding with missing namespace.

        Verifies that None is returned when the namespace directory doesn't exist.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        result: Optional[str] = find_package_folder(
            str(tmp_path), "nonexistent/test_package"
        )
        assert result is None

    def test_find_package_folder_missing_required_files(self, tmp_path: Path) -> None:
        """Test package folder finding with missing required files.

        Verifies that None is returned when the package folder exists but
        lacks the required files.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        namespace_dir: Path = tmp_path / "test_namespace"
        namespace_dir.mkdir()
        package_dir: Path = namespace_dir / "test_package"
        package_dir.mkdir()

        result: Optional[str] = find_package_folder(
            str(tmp_path), "test_namespace/test_package"
        )
        assert result is None

    def test_find_package_folder_invalid_format(self) -> None:
        """Test package folder finding with invalid name format.

        Verifies that None is returned when the package name doesn't follow
        the expected 'namespace/package' format.
        """
        result: Optional[str] = find_package_folder("/tmp", "invalid_format")
        assert result is None

    def test_find_package_folder_custom_required_files(self, tmp_path: Path) -> None:
        """Test package folder finding with custom required files.

        Verifies that the function works correctly when custom required files
        are specified instead of the default info.yaml.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        namespace_dir: Path = tmp_path / "test_namespace"
        namespace_dir.mkdir()
        package_dir: Path = namespace_dir / "test_package"
        package_dir.mkdir()
        custom_file: Path = package_dir / "custom.txt"
        custom_file.write_text("test")

        required_files: Set[str] = {"custom.txt"}
        result: Optional[str] = find_package_folder(
            str(tmp_path), "test_namespace/test_package", required_files
        )
        assert result == str(package_dir)

    def test_action_walker_path_basic(self) -> None:
        """Test basic action walker path generation.

        Verifies that a standard module string is correctly converted
        to an action walker path format.
        """
        result: str = action_walker_path("some.module.namespace.action")
        assert result == "/action/walker/namespace/action"

    def test_action_walker_path_empty_module(self) -> None:
        """Test action walker path with empty module.

        Verifies that empty module strings are handled gracefully.
        """
        result: str = action_walker_path("")
        assert result == ""

    def test_action_walker_path_single_part(self) -> None:
        """Test action walker path with single module part.

        Verifies that module strings with insufficient parts raise an IndexError.
        """
        with pytest.raises(IndexError):
            action_walker_path("action")

    def test_action_webhook_path_basic(self) -> None:
        """Test basic action webhook path generation.

        Verifies that a standard module string is correctly converted
        to an action webhook path format with placeholders.
        """
        result: str = action_webhook_path("some.namespace.action.walker")
        assert result == "/action/webhook/namespace/action/walker/{agent_id}/{key}"

    def test_action_webhook_path_empty_module(self) -> None:
        """Test action webhook path with empty module.

        Verifies that empty module strings are handled gracefully.
        """
        result: str = action_webhook_path("")
        assert result == ""

    def test_action_webhook_path_complex_module(self) -> None:
        """Test action webhook path with complex module name.

        Verifies that complex module names with multiple segments
        are correctly processed to extract the namespace and action parts.
        """
        result: str = action_webhook_path(
            "jivas.core.agent.modules.test.webhook_action"
        )
        assert result == "/action/webhook/modules/test/webhook_action/{agent_id}/{key}"
