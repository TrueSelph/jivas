"""Test cases for mime_types module"""

import unittest
from unittest.mock import Mock, patch
from typing import Dict, Optional

from jivas.agent.modules.data.mime_types import get_mime_type


class TestMimeTypes(unittest.TestCase):
    """Test cases for MIME type detection and categorization functionality."""

    def test_get_mime_type_from_file_path_image(self) -> None:
        """Test MIME type detection for image files using file path."""
        # Test with a JPEG image file
        result: Optional[Dict[str, str]] = get_mime_type(file_path="test_image.jpg")

        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result["file_type"], "image")
            self.assertEqual(result["mime"], "image/jpeg")

    def test_get_mime_type_from_url_with_content_type(self) -> None:
        """Test MIME type detection from URL with Content-Type header."""
        with patch("requests.head") as mock_head:
            # Mock successful response with PDF content type
            mock_response = Mock()
            mock_response.headers.get.return_value = "application/pdf"
            mock_head.return_value = mock_response

            result: Optional[Dict[str, str]] = get_mime_type(
                url="https://example.com/document.pdf"
            )

            self.assertIsNotNone(result)
            if result:
                self.assertEqual(result["file_type"], "document")
                self.assertEqual(result["mime"], "application/pdf")

    def test_get_mime_type_unsupported_type_returns_none(self) -> None:
        """Test that unsupported MIME types return None."""
        # Test with an unsupported MIME type
        result: Optional[Dict[str, str]] = get_mime_type(
            mime_type="application/x-unknown-format"
        )

        self.assertIsNone(result)

    def test_get_mime_type_audio_file_detection(self) -> None:
        """Test MIME type detection for audio files."""
        result: Optional[Dict[str, str]] = get_mime_type(file_path="test_audio.mp3")

        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result["file_type"], "audio")
            self.assertEqual(result["mime"], "audio/mpeg")
