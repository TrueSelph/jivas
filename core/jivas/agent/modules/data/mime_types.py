"""MIME types package"""

import logging
import mimetypes
import os
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


def get_mime_type(
    file_path: Optional[str] = None,
    url: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Determines the MIME type and categorizes it into common file types."""
    detected_mime_type = None

    if file_path:
        detected_mime_type, _ = mimetypes.guess_type(file_path)
    elif url:
        try:
            response = requests.head(url, allow_redirects=True)
            detected_mime_type = response.headers.get("Content-Type")
        except requests.RequestException as e:
            logger.error(f"Error making HEAD request: {e}")
            return None
    else:
        detected_mime_type = mime_type

    # MIME type categories
    image_mime_types = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
        "image/tiff",
        "image/svg+xml",
        "image/x-icon",
        "image/heic",
        "image/heif",
        "image/x-raw",
    ]
    document_mime_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
        "text/html",
        "application/rtf",
    ]
    audio_mime_types = [
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "audio/flac",
        "audio/aac",
        "audio/mp3",
        "audio/webm",
        "audio/amr",
        "audio/midi",
    ]
    video_mime_types = [
        "video/mp4",
        "video/mpeg",
        "video/ogg",
        "video/webm",
        "video/quicktime",
        "video/x-msvideo",
        "video/x-matroska",
    ]

    if detected_mime_type is None or detected_mime_type == "binary/octet-stream":
        if file_path:
            _, file_extension = os.path.splitext(file_path)
        elif url:
            _, file_extension = os.path.splitext(url)
        else:
            file_extension = ""
        detected_mime_type = mimetypes.types_map.get(file_extension.lower())

    # Categorize MIME type
    if detected_mime_type in image_mime_types:
        return {"file_type": "image", "mime": detected_mime_type}
    elif detected_mime_type in document_mime_types:
        return {"file_type": "document", "mime": detected_mime_type}
    elif detected_mime_type in audio_mime_types:
        return {"file_type": "audio", "mime": detected_mime_type}
    elif detected_mime_type in video_mime_types:
        return {"file_type": "video", "mime": detected_mime_type}
    else:
        logger.error(f"Unsupported MIME Type: {detected_mime_type}")
        return None
