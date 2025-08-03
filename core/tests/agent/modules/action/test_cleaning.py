"""
Test module for action cleaning operations.

This module contains comprehensive tests for the cleaning functionality
including action folder removal and context sanitization operations.
"""

import os
import shutil
import tempfile
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from jivas.agent.modules.action.cleaning import clean_action, clean_context


class TestCleanAction(unittest.TestCase):
    """Test cases for the clean_action function."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.actions_root = os.path.join(self.test_dir, "actions")
        os.makedirs(self.actions_root)

    def tearDown(self) -> None:
        """Clean up test fixtures after each test method."""
        # Remove the temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": ""})
    def test_clean_action_success(self) -> None:
        """Test successful removal of an action folder."""
        # Set the environment variable to our test directory
        os.environ["JIVAS_ACTIONS_ROOT_PATH"] = self.actions_root

        # Create test action folder structure
        namespace_package = "test_namespace/test_action"
        action_path = os.path.join(self.actions_root, namespace_package)
        os.makedirs(action_path)

        # Create some test files in the action folder
        test_file = os.path.join(action_path, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        # Test the clean_action function
        result = clean_action(namespace_package)

        # Assertions
        self.assertTrue(result)
        self.assertFalse(os.path.exists(action_path))

    @patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": ""})
    def test_clean_action_folder_not_found(self) -> None:
        """Test clean_action when the action folder doesn't exist."""
        os.environ["JIVAS_ACTIONS_ROOT_PATH"] = self.actions_root

        namespace_package = "nonexistent_namespace/nonexistent_action"

        result = clean_action(namespace_package)

        self.assertFalse(result)

    @patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": ""})
    def test_clean_action_removal_failure(self) -> None:
        """Test clean_action when removal fails due to permission error."""
        os.environ["JIVAS_ACTIONS_ROOT_PATH"] = self.actions_root

        # Create test action folder structure
        namespace_package = "test_namespace/test_action"
        action_path = os.path.join(self.actions_root, namespace_package)
        os.makedirs(action_path)

        with patch("shutil.rmtree", side_effect=PermissionError("Permission denied")):
            result = clean_action(namespace_package)
            self.assertFalse(result)

    def test_clean_action_root_dir_not_found(self) -> None:
        """Test clean_action when root directory doesn't exist."""
        with patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": "/nonexistent/path"}):
            result = clean_action("test_namespace/test_action")
            self.assertFalse(result)

    @patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": ""})
    def test_clean_action_custom_root_path(self) -> None:
        """Test clean_action with custom root path."""
        custom_root = os.path.join(self.test_dir, "custom_actions")
        os.makedirs(custom_root)
        os.environ["JIVAS_ACTIONS_ROOT_PATH"] = custom_root

        namespace_package = "test_namespace/test_action"
        action_path = os.path.join(custom_root, namespace_package)
        os.makedirs(action_path)

        result = clean_action(namespace_package)
        self.assertTrue(result)
        self.assertFalse(os.path.exists(action_path))

    def test_clean_action_invalid_namespace_format(self) -> None:
        """Test clean_action with invalid namespace format."""
        with patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": self.actions_root}):
            result = clean_action("invalid_format")
            self.assertFalse(result)

    def test_clean_action_with_nested_path(self) -> None:
        """Test clean_action with nested directory structure."""
        with patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": self.actions_root}):
            namespace_package = "namespace/subdir/action"
            action_path = os.path.join(self.actions_root, namespace_package)
            os.makedirs(action_path)

            result = clean_action(namespace_package)
            self.assertTrue(result)
            self.assertFalse(os.path.exists(action_path))

    def test_clean_action_root_not_found(self) -> None:
        """Test clean_action when the actions root directory doesn't exist."""
        with patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": "/nonexistent/path"}):
            result = clean_action("test_namespace/test_action")
            self.assertFalse(result)

    @patch.dict(os.environ, {"JIVAS_ACTIONS_ROOT_PATH": ""})
    @patch("shutil.rmtree")
    def test_clean_action_permission_error(self, mock_rmtree: MagicMock) -> None:
        """Test clean_action when there's a permission error during removal."""
        os.environ["JIVAS_ACTIONS_ROOT_PATH"] = self.actions_root

        # Create test action folder
        namespace_package = "test_namespace/test_action"
        action_path = os.path.join(self.actions_root, namespace_package)
        os.makedirs(action_path)

        # Mock rmtree to raise an exception
        mock_rmtree.side_effect = PermissionError("Permission denied")

        result = clean_action(namespace_package)

        self.assertFalse(result)


class TestCleanContext(unittest.TestCase):
    """Test cases for the clean_context function."""

    def test_clean_context_match_and_remove(self) -> None:
        """Test removal of matching values between contexts."""
        node_context = {
            "name": "test_name",
            "count": 42,
            "description": "test description",
        }
        archetype_context = {
            "name": "test_name",
            "count": 42,
        }
        ignore_keys: List[str] = []

        result = clean_context(node_context, archetype_context, ignore_keys)

        expected = {"description": "test description"}
        self.assertEqual(result, expected)

    def test_clean_context_remove_empty_values(self) -> None:
        """Test removal of empty values while preserving boolean False."""
        node_context = {
            "empty_string": "",
            "empty_list": [],
            "none_value": None,
            "false_value": False,
            "valid_string": "not empty",
        }
        archetype_context: Dict[str, Any] = {}
        ignore_keys: List[str] = []

        result = clean_context(node_context, archetype_context, ignore_keys)

        expected = {"false_value": False, "valid_string": "not empty"}
        self.assertEqual(result, expected)

    def test_clean_context_ignore_keys(self) -> None:
        """Test removal of keys specified in ignore_keys list."""
        node_context = {
            "keep_this": "valuable_data",
            "remove_this": "unwanted_data",
            "also_remove": "also_unwanted",
        }
        archetype_context: Dict[str, Any] = {}
        ignore_keys = ["remove_this", "also_remove"]

        result = clean_context(node_context, archetype_context, ignore_keys)

        expected = {"keep_this": "valuable_data"}
        self.assertEqual(result, expected)

    def test_clean_context_remove_matching_strings(self) -> None:
        """Test removal of matching string values between contexts."""
        node_context = {
            "name": "test_name",
            "description": "test description",
            "unique_field": "unique_value",
        }
        archetype_context = {
            "name": "test_name",
            "description": "different description",
        }
        ignore_keys: List[str] = []

        result = clean_context(node_context, archetype_context, ignore_keys)

        expected = {"description": "test description", "unique_field": "unique_value"}
        self.assertEqual(result, expected)

    def test_clean_context_remove_matching_non_strings(self) -> None:
        """Test removal of matching non-string values between contexts."""
        node_context = {
            "count": 42,
            "enabled": True,
            "items": [1, 2, 3],
            "different_count": 100,
        }
        archetype_context = {"count": 42, "enabled": False, "items": [1, 2, 3]}
        ignore_keys: List[str] = []

        result = clean_context(node_context, archetype_context, ignore_keys)

        expected = {"enabled": True, "different_count": 100}
        self.assertEqual(result, expected)

    def test_clean_context_comprehensive(self) -> None:
        """Test comprehensive cleaning with all conditions."""
        node_context = {
            "matching_string": "same_value",
            "matching_number": 42,
            "different_value": "different",
            "empty_field": "",
            "ignore_me": "should_be_removed",
            "false_bool": False,
            "none_field": None,
            "keep_this": "important_data",
        }
        archetype_context = {
            "matching_string": "same_value",
            "matching_number": 42,
            "different_value": "original_value",
        }
        ignore_keys = ["ignore_me"]

        result = clean_context(node_context, archetype_context, ignore_keys)

        expected = {
            "different_value": "different",
            "false_bool": False,
            "keep_this": "important_data",
        }
        self.assertEqual(result, expected)

    @patch("jivas.agent.modules.action.cleaning.normalize_text")
    def test_clean_context_with_text_normalization(
        self, mock_normalize: MagicMock
    ) -> None:
        """Test that text normalization is called for string comparisons."""
        node_context = {"text_field": "  Test Text  "}
        archetype_context = {"text_field": "test text"}
        ignore_keys: List[str] = []

        # Mock normalize_text to return the same normalized value
        mock_normalize.return_value = "test text"

        result = clean_context(node_context, archetype_context, ignore_keys)

        # Verify normalize_text was called twice (once for each string)
        self.assertEqual(mock_normalize.call_count, 2)
        # The field should be removed because normalized strings match
        self.assertNotIn("text_field", result)


if __name__ == "__main__":
    unittest.main()
