"""Tests for text parsing utilities."""

import unittest

from jivas.agent.modules.text.parsing import extract_first_name


class TestParsing(unittest.TestCase):
    """Test cases for text parsing utilities."""

    def test_extract_first_name_simple(self) -> None:
        """Test extracting the first name from a simple full name."""
        self.assertEqual(extract_first_name("John Doe"), "John")

    def test_extract_first_name_with_title(self) -> None:
        """Test extracting the first name when a title is present."""
        self.assertEqual(extract_first_name("Mr. John Doe"), "John")
        self.assertEqual(extract_first_name("Dr. Jane Smith"), "Jane")

    def test_extract_first_name_with_middle_name(self) -> None:
        """Test extracting the first name from a name with a middle name."""
        self.assertEqual(extract_first_name("John Fitzgerald Kennedy"), "John")

    def test_extract_first_name_single_name(self) -> None:
        """Test with a single name."""
        self.assertEqual(extract_first_name("Cher"), "Cher")

    def test_extract_first_name_empty_string(self) -> None:
        """Test with an empty string."""
        self.assertEqual(extract_first_name(""), "")

    def test_extract_first_name_whitespace_string(self) -> None:
        """Test with a string containing only whitespace."""
        self.assertEqual(extract_first_name("   "), "")

    def test_extract_first_name_multiple_titles(self) -> None:
        """Test with multiple titles."""
        self.assertEqual(extract_first_name("Prof. Dr. John Doe"), "John")

    def test_extract_first_name_with_various_titles(self) -> None:
        """Test with a variety of titles."""
        self.assertEqual(extract_first_name("Mrs. Jane Doe"), "Jane")
        self.assertEqual(extract_first_name("Ms. Emily White"), "Emily")
        self.assertEqual(extract_first_name("Miss Elizabeth Brown"), "Elizabeth")
        self.assertEqual(extract_first_name("Sir Elton John"), "Elton")
        self.assertEqual(extract_first_name("Madam Curie"), "Curie")
        self.assertEqual(extract_first_name("Mx. Sam Jones"), "Sam")


if __name__ == "__main__":
    unittest.main()
