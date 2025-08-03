"""Test cases for mime_types module"""

import unittest
from unittest.mock import Mock, patch

import requests  # Added missing import

from jivas.agent.modules.data.mime_types import get_mime_type


class TestMimeTypes(unittest.TestCase):
    """Test cases for MIME type detection and categorization functionality."""

    def test_get_mime_type_from_file_path_image(self) -> None:
        """Test MIME type detection for image files using file path."""
        # Test with a JPEG image file
        with patch("mimetypes.guess_type") as mock_guess:
            mock_guess.return_value = ("image/jpeg", None)
            result = get_mime_type(file_path="test_image.jpg")
            self.assertIsNotNone(result)
            self.assertEqual(result["file_type"], "image")  # type: ignore[index]
            self.assertEqual(result["mime"], "image/jpeg")  # type: ignore[index]

    def test_get_mime_type_from_url_with_content_type(self) -> None:
        """Test MIME type detection from URL with Content-Type header."""
        with patch("requests.head") as mock_head:
            # Mock successful response with PDF content type
            mock_response = Mock()
            mock_response.headers.get.return_value = "application/pdf"
            mock_head.return_value = mock_response

            result = get_mime_type(url="https://example.com/document.pdf")
            self.assertIsNotNone(result)
            self.assertEqual(result["file_type"], "document")  # type: ignore[index]
            self.assertEqual(result["mime"], "application/pdf")  # type: ignore[index]

    def test_get_mime_type_unsupported_type_returns_none(self) -> None:
        """Test that unsupported MIME types return None."""
        # Test with an unsupported MIME type
        result = get_mime_type(mime_type="application/x-unknown-format")
        self.assertIsNone(result)

    def test_get_mime_type_audio_file_detection(self) -> None:
        """Test MIME type detection for audio files."""
        with patch("mimetypes.guess_type") as mock_guess:
            mock_guess.return_value = ("audio/mpeg", None)
            result = get_mime_type(file_path="test_audio.mp3")
            self.assertIsNotNone(result)
            self.assertEqual(result["file_type"], "audio")  # type: ignore[index]
            self.assertEqual(result["mime"], "audio/mpeg")  # type: ignore[index]

    def test_get_mime_type_video_file_detection(self) -> None:
        """Test MIME type detection for video files."""
        with patch("mimetypes.guess_type") as mock_guess:
            mock_guess.return_value = ("video/mp4", None)
            result = get_mime_type(file_path="test_video.mp4")
            self.assertIsNotNone(result)
            self.assertEqual(result["file_type"], "video")  # type: ignore[index]
            self.assertEqual(result["mime"], "video/mp4")  # type: ignore[index]

    def test_get_mime_type_document_file_detection(self) -> None:
        """Test MIME type detection for document files."""
        with patch("mimetypes.guess_type") as mock_guess:
            mock_guess.return_value = ("application/pdf", None)
            result = get_mime_type(file_path="test_document.pdf")
            self.assertIsNotNone(result)
            self.assertEqual(result["file_type"], "document")  # type: ignore[index]
            self.assertEqual(result["mime"], "application/pdf")  # type: ignore[index]

    def test_get_mime_type_with_direct_mime_type_input(self) -> None:
        """Test MIME type detection with direct MIME type input."""
        result = get_mime_type(mime_type="image/png")
        self.assertIsNotNone(result)
        self.assertEqual(result["file_type"], "image")  # type: ignore[index]
        self.assertEqual(result["mime"], "image/png")  # type: ignore[index]

    def test_get_mime_type_with_url_extension_fallback(self) -> None:
        """Test MIME type detection with URL extension fallback."""
        with patch("requests.head") as mock_head:
            mock_response = Mock()
            mock_response.headers.get.return_value = None
            mock_head.return_value = mock_response
            with patch.dict(
                "mimetypes.types_map", {".pdf": "application/pdf"}, clear=False
            ):
                result = get_mime_type(url="https://example.com/document.pdf")
                self.assertIsNotNone(result)
                self.assertEqual(result["mime"], "application/pdf")  # type: ignore[index]

    def test_get_mime_type_with_request_exception(self) -> None:
        """Test MIME type detection when URL request fails."""
        with patch("requests.head") as mock_head:
            mock_head.side_effect = requests.RequestException("Connection error")
            with patch("logging.Logger.error") as mock_log:
                result = get_mime_type(url="https://example.com/document.pdf")
                self.assertIsNone(result)
                mock_log.assert_called_once()

    def test_get_mime_type_with_unknown_extension(self) -> None:
        """Test MIME type detection with unknown file extension."""
        with patch("mimetypes.guess_type") as mock_guess:
            mock_guess.return_value = (None, None)
            result = get_mime_type(file_path="test_file.unknown")
            self.assertIsNone(result)

    def test_get_mime_type_with_empty_input(self) -> None:
        """Test MIME type detection with no input provided."""
        result = get_mime_type()
        self.assertIsNone(result)

    def test_get_mime_type_with_unsupported_extension_but_known_mime(self) -> None:
        """Test MIME type detection with unsupported extension but known MIME type."""
        with patch("mimetypes.guess_type") as mock_guess:
            mock_guess.return_value = ("application/x-custom", None)
            result = get_mime_type(file_path="test.custom")
            self.assertIsNone(result)

    def test_get_mime_type_with_extension_fallback_success(self) -> None:
        """Test MIME type detection with successful extension fallback."""
        with patch("mimetypes.guess_type") as mock_guess:
            mock_guess.return_value = (None, None)
            with patch.dict("mimetypes.types_map", {".html": "text/html"}, clear=False):
                result = get_mime_type(file_path="test.html")
                self.assertIsNotNone(result)
                self.assertEqual(result["mime"], "text/html")  # type: ignore[index]

    def test_get_mime_type_with_octet_stream_but_known_extension(self) -> None:
        """Test MIME type detection with octet-stream but known extension."""
        with patch("mimetypes.guess_type") as mock_guess:
            mock_guess.return_value = ("binary/octet-stream", None)
            with patch.dict("mimetypes.types_map", {".png": "image/png"}, clear=False):
                result = get_mime_type(file_path="test.png")
                self.assertIsNotNone(result)
                self.assertEqual(result["mime"], "image/png")  # type: ignore[index]

    def test_get_mime_type_with_url_octet_stream_but_known_extension(self) -> None:
        """Test MIME type detection with URL returning octet-stream but known extension."""
        with patch("requests.head") as mock_head:
            mock_response = Mock()
            mock_response.headers.get.return_value = "binary/octet-stream"
            mock_head.return_value = mock_response
            with patch.dict("mimetypes.types_map", {".png": "image/png"}, clear=False):
                result = get_mime_type(url="https://example.com/image.png")
                self.assertIsNotNone(result)
                self.assertEqual(result["mime"], "image/png")  # type: ignore[index]
