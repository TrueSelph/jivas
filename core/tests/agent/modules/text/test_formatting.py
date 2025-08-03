"""Tests for text formatting utilities."""

import unittest
from unittest.mock import patch

from jivas.agent.modules.text.formatting import (
    clean_text,
    escape_string,
    list_to_phrase,
    normalize_text,
    replace_placeholders,
    to_snake_case,
)


class TestFormatting(unittest.TestCase):
    """Test cases for text formatting utilities."""

    def test_list_to_phrase(self) -> None:
        """Test list_to_phrase with various inputs."""
        self.assertEqual(list_to_phrase([]), "")
        self.assertEqual(list_to_phrase(["one"]), "one")
        self.assertEqual(list_to_phrase(["one", "two"]), "one, and two")
        self.assertEqual(
            list_to_phrase(["one", "two", "three"]), "one, two, and three")
        self.assertEqual(list_to_phrase([1, "two", True]), "1, two, and True")

    def test_replace_placeholders(self) -> None:
        """Test replace_placeholders with various inputs."""
        placeholders = {"name": "John", "items": ["apples", "oranges"]}
        # Test with a single string
        self.assertEqual(
            replace_placeholders("Hello, {{name}}!", placeholders), "Hello, John!")
        # Test with a list of strings
        self.assertEqual(
            replace_placeholders(
                ["Hello, {{name}}!", "You have {{items}}."], placeholders
            ),
            ["Hello, John!", "You have apples, and oranges."],
        )
        # Test with unresolvable placeholders
        self.assertIsNone(
            replace_placeholders("Hello, {{unresolvable}}!", placeholders)
        )
        self.assertEqual(
            replace_placeholders(
                ["Hello, {{name}}!", "Hello, {{unresolvable}}!"], placeholders
            ),
            ["Hello, John!"],
        )
        # Test with invalid input type
        with self.assertRaises(TypeError):
            replace_placeholders(123, placeholders)  # type: ignore

    def test_escape_string(self) -> None:
        """Test escape_string with various inputs."""
        self.assertEqual(escape_string("Hello {world}"), "Hello {{world}}")
        self.assertEqual(escape_string("{{}}"), "{{{{}}}}")
        self.assertEqual(escape_string("no braces"), "no braces")
        with patch("jivas.agent.modules.text.formatting.logger.error") as mock_log:
            self.assertEqual(escape_string(123), "")  # type: ignore
            mock_log.assert_called_once()

    def test_normalize_text(self) -> None:
        """Test normalize_text with various inputs."""
        self.assertEqual(normalize_text("  Hello, world!  "), "Helloworld")
        self.assertEqual(normalize_text("some\ntext"), "sometext")
        self.assertEqual(normalize_text("weirdâ€”text"), "weirdtext")

    def test_to_snake_case(self) -> None:
        """Test to_snake_case with various inputs."""
        self.assertEqual(to_snake_case("Some Title"), "some_title")
        self.assertEqual(
            to_snake_case("  leading and trailing  "), "leading_and_trailing"
        )
        self.assertEqual(
            to_snake_case("multiple__underscores"), "multiple_underscores"
        )
        self.assertEqual(to_snake_case("non-ascii: éàç"), "non_ascii_eac")
        self.assertEqual(
            to_snake_case("non-ascii: éàç", ascii_only=False), "non_ascii")

    def test_clean_text(self) -> None:
        """Test clean_text with various inputs."""
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text("  some text  "), "some text")
        self.assertEqual(clean_text("line1\u2028line2"), "line1 line2")
        self.assertEqual(clean_text("hello éàç", force_ascii=True), "hello ???")


if __name__ == "__main__":
    unittest.main()