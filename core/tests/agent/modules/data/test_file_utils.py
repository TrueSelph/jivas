"""Tests for file_utils module."""

import sys
import unittest
from unittest.mock import MagicMock, patch


class TestFileUtils(unittest.TestCase):
    """Test cases for file_utils module."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Ensure the module is reloaded for each test to check initialization logic
        if "jivas.agent.modules.data.file_utils" in sys.modules:
            del sys.modules["jivas.agent.modules.data.file_utils"]
        if "jvserve.lib.file_interface" in sys.modules:
            del sys.modules["jvserve.lib.file_interface"]

    @patch("jvserve.lib.file_interface.get_file_interface")
    @patch("jvserve.lib.file_interface.FILE_INTERFACE", "local")
    def test_file_interface_local(self, mock_get_file_interface: MagicMock) -> None:
        """Test that local file interface is used when FILE_INTERFACE is 'local'."""
        from jivas.agent.modules.data.file_utils import jvdata_file_interface

        mock_get_file_interface.assert_called_with("")
        self.assertEqual(jvdata_file_interface, mock_get_file_interface.return_value)

    @patch("jvserve.lib.file_interface.file_interface")
    @patch("jvserve.lib.file_interface.FILE_INTERFACE", "remote")
    def test_file_interface_remote(self, mock_file_interface: MagicMock) -> None:
        """Test that remote file interface is used when FILE_INTERFACE is not 'local'."""
        from jivas.agent.modules.data.file_utils import jvdata_file_interface

        self.assertEqual(jvdata_file_interface, mock_file_interface)

    @patch("jvserve.lib.file_interface.file_interface")
    @patch("jvserve.lib.file_interface.FILE_INTERFACE", "default")
    def test_file_interface_default(self, mock_file_interface: MagicMock) -> None:
        """Test that remote file interface is used by default."""
        from jivas.agent.modules.data.file_utils import jvdata_file_interface

        self.assertEqual(jvdata_file_interface, mock_file_interface)


if __name__ == "__main__":
    unittest.main()
