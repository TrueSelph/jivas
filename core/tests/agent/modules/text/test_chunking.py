"""Test for text chunking utilities."""

from jivas.agent.modules.text.chunking import chunk_long_message


class TestTextChunking:
    """Test cases for text chunking utilities."""

    def test_chunk_long_message_short_message(self) -> None:
        """Test that a short message is not chunked."""
        message = "This is a short message."
        chunks = chunk_long_message(message, max_length=100, chunk_length=50)
        assert chunks == [message]

    def test_chunk_long_message_long_message(self) -> None:
        """Test that a long message is chunked correctly."""
        message = "This is a long message that should be split into multiple chunks."
        chunks = chunk_long_message(message, max_length=50, chunk_length=30)
        assert len(chunks) == 3
        assert chunks[0] == "This is a long message that"
        assert chunks[1] == "should be split into multiple"
        assert chunks[2] == "chunks."

    def test_chunk_long_message_with_newlines(self) -> None:
        """Test chunking with newlines."""
        message = "First line.\nSecond line.\nThird line."
        chunks = chunk_long_message(message, max_length=20, chunk_length=15)
        assert len(chunks) == 3
        assert chunks[0] == "First line.\n"
        assert chunks[1] == "Second line.\n"
        assert chunks[2] == "Third line."

    def test_chunk_long_message_empty_message(self) -> None:
        """Test that an empty message returns a list with an empty string."""
        message = ""
        chunks = chunk_long_message(message)
        assert chunks == [""]

    def test_chunk_long_message_whitespace_message(self) -> None:
        """Test that a message with only whitespace returns an empty list."""
        message = "   \n   "
        chunks = chunk_long_message(message)
        assert chunks == [message]

    def test_chunk_long_message_single_word_longer_than_chunk(self) -> None:
        """Test a single word longer than the chunk length."""
        message = "ThisIsAVeryLongWordThatExceedsTheChunkLength"
        chunks = chunk_long_message(message, max_length=50, chunk_length=20)
        assert chunks == [message]

    def test_chunk_long_message_exact_chunk_length(self) -> None:
        """Test a message that fits exactly into chunks."""
        message = "word " * 4  # 20 chars
        chunks = chunk_long_message(message.strip(), max_length=100, chunk_length=20)
        assert len(chunks) == 1
        assert chunks[0] == "word word word word"

    def test_chunk_long_message_with_multiple_spaces(self) -> None:
        """Test that multiple spaces are handled correctly."""
        message = "word  word    word"
        chunks = chunk_long_message(message, max_length=100, chunk_length=10)
        assert len(chunks) == 1
        assert chunks[0] == "word  word    word"
