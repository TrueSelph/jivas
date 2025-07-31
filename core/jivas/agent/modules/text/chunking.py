"""Utils to chunk text"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


def chunk_long_message(
    message: str, max_length: int = 1024, chunk_length: int = 1024
) -> List[str]:
    """
    Splits a long message into smaller chunks of no more than chunk_length characters,
    ensuring no single chunk exceeds max_length.

    Args:
        message: The text to chunk
        max_length: Maximum allowed length for any chunk
        chunk_length: Target length for chunks

    Returns:
        List of message chunks
    """
    if len(message) <= max_length:
        return [message]

    # Initialize variables
    final_chunks = []
    current_chunk = ""
    current_chunk_length = 0

    # Split the message into words while preserving newline characters
    words = re.findall(r"\S+\n*|\n+", message)
    words = [word for word in words if word.strip()]  # Filter out empty strings

    for word in words:
        word_length = len(word)

        if current_chunk_length + word_length + 1 <= chunk_length:
            # Add the word to the current chunk
            if current_chunk:
                current_chunk += " "
            current_chunk += word
            current_chunk_length += word_length + 1
        else:
            # If the current chunk is full, add it to the list of chunks
            final_chunks.append(current_chunk)
            current_chunk = word  # Start a new chunk with the current word
            current_chunk_length = word_length

    if current_chunk:
        # Add the last chunk if it's non-empty
        final_chunks.append(current_chunk)

    return final_chunks
