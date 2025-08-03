"""Tests for FileInterface classes"""

import os
import unittest
from unittest.mock import MagicMock, patch

from jvserve.lib.file_interface import (
    FileInterface,
    LocalFileInterface,
    S3FileInterface,
)


class TestFileInterface(unittest.TestCase):
    """Test cases for FileInterface implementations"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.test_filename = "test_file.txt"
        self.test_content = b"test content"
        self.test_root = ".test_files"

    def tearDown(self) -> None:
        """Clean up test environment"""
        if os.path.exists(self.test_root):
            for file in os.listdir(self.test_root):
                os.remove(os.path.join(self.test_root, file))
            os.rmdir(self.test_root)

    def test_local_file_interface(self) -> None:
        """Test LocalFileInterface implementation"""
        interface = LocalFileInterface(self.test_root)

        # Test save_file
        self.assertTrue(interface.save_file(self.test_filename, self.test_content))

        # Test get_file
        self.assertEqual(interface.get_file(self.test_filename), self.test_content)
        self.assertIsNone(interface.get_file("nonexistent.txt"))

        # Test get_file_url
        expected_url = f"http://localhost:8000/files/{self.test_filename}"
        self.assertEqual(interface.get_file_url(self.test_filename), expected_url)
        self.assertIsNone(interface.get_file_url("nonexistent.txt"))

        # Test delete_file
        self.assertTrue(interface.delete_file(self.test_filename))
        self.assertFalse(interface.delete_file("nonexistent.txt"))

    @patch("boto3.client")
    def test_s3_file_interface(self, mock_boto3_client: MagicMock) -> None:
        """Test S3FileInterface implementation"""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        interface = S3FileInterface(
            bucket_name="test-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",  # pragma: allowlist secret
            region_name="test-region",
        )

        # Test get_file
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: self.test_content)
        }
        self.assertEqual(interface.get_file(self.test_filename), self.test_content)

        mock_s3.get_object.side_effect = Exception()
        self.assertIsNone(interface.get_file(self.test_filename))

        # Test save_file
        mock_s3.put_object.return_value = True
        self.assertTrue(interface.save_file(self.test_filename, self.test_content))

        mock_s3.put_object.side_effect = Exception()
        self.assertFalse(interface.save_file(self.test_filename, self.test_content))

        # Test delete_file
        mock_s3.delete_object.return_value = True
        self.assertTrue(interface.delete_file(self.test_filename))

        mock_s3.delete_object.side_effect = Exception()
        self.assertFalse(interface.delete_file(self.test_filename))

        # Test get_file_url
        mock_s3.generate_presigned_url.return_value = "https://test-url.com"
        self.assertEqual(
            interface.get_file_url(self.test_filename), "https://test-url.com"
        )

        mock_s3.generate_presigned_url.side_effect = Exception()
        self.assertIsNone(interface.get_file_url(self.test_filename))

    @patch("boto3.client")
    def test_s3_file_interface_missing_credentials(
        self, mock_boto3_client: MagicMock
    ) -> None:
        """Test S3FileInterface with missing credentials"""
        # Mock logger before creating interface
        mock_logger = MagicMock()
        FileInterface.LOGGER = mock_logger

        S3FileInterface(
            bucket_name="test-bucket",
            aws_access_key_id="",
            aws_secret_access_key="",
            region_name="",
        )

        mock_logger.warn.assert_called_once_with(
            "Missing AWS credentials - S3 operations may fail"
        )


if __name__ == "__main__":
    unittest.main()
