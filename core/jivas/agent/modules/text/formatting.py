"""Text formatting utilities"""

import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional, Union

import ftfy

logger = logging.getLogger(__name__)


def list_to_phrase(lst: List[Any]) -> str:
    """Formats a list as a phrased list, e.g. ['one', 'two', 'three'] becomes 'one, two, and three'."""
    if not lst:
        return ""

    # Convert all elements to strings
    lst = list(map(str, lst))

    if len(lst) == 1:
        return lst[0]

    return ", ".join(lst[:-1]) + f", and {lst[-1]}"


def replace_placeholders(
    string_or_collection: Union[str, List[str]], placeholders: Dict[str, Any]
) -> Union[str, List[str], None]:
    """
    Replaces placeholders delimited by {{ and }} in a string or collection of strings with their corresponding values
    from a dictionary of key-value pairs. If a value in the dictionary is a list, it is formatted as a phrased list.
    Returns only items that have no remaining placeholders.
    """

    def replace_in_string(s: str, ph: Dict[str, Any]) -> Optional[str]:
        # Replace placeholders in a single string
        for key, value in ph.items():
            if isinstance(value, list):
                value = list_to_phrase(value)
            s = s.replace(f"{{{{{key}}}}}", str(value))
        return s if not re.search(r"{{.*?}}", s) else None

    if isinstance(string_or_collection, str):
        return replace_in_string(string_or_collection, placeholders)
    elif isinstance(string_or_collection, list):
        # Process each string in the list and return those with no placeholders left
        return [
            result
            for string in string_or_collection
            if (result := replace_in_string(string, placeholders)) is not None
        ]
    else:
        raise TypeError("Input must be a string or a list of strings.")


def escape_string(input_string: str) -> str:
    """
    Escapes curly braces in the input string by converting them to double curly braces.

    Args:
        input_string: The string to be escaped.

    Returns:
        The escaped string with all curly braces doubled.
    """
    if not isinstance(input_string, str):
        logger.error(f"Error expect string: {input_string}")
        return ""
    return input_string.replace("{", "{{").replace("}", "}}")


def normalize_text(text: str) -> str:
    """
    Normalizes a string by:
    - Stripping whitespace
    - Fixing text encoding
    - Removing non-word characters

    Args:
        text: Input string
    Returns:
        Normalized string
    """
    text = text.strip().replace("\\n", "\n")
    text = ftfy.fix_text(text)
    return re.sub(r"\W+", "", text)


def to_snake_case(title: str, ascii_only: bool = True) -> str:
    """
    Converts a string to a safe, lowercase snake_case suitable for machine names.

    Args:
        title: The input string/title
        ascii_only: If True, strips out non-ascii characters

    Returns:
        A clean, lowercase, snake_case string
    """
    s = title.strip()
    if ascii_only:
        # Normalize unicode
        s = unicodedata.normalize("NFKD", s)
        s = s.encode("ascii", "ignore").decode("ascii")
    else:
        # Remove combining marks but keep unicode letters
        s = unicodedata.normalize("NFKC", s)
    # Replace non-alphanumeric with underscores
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    # Lowercase it
    s = s.lower()
    # Remove leading/trailing and consecutive underscores
    s = re.sub(r"_{2,}", "_", s)
    s = s.strip("_")
    return s


def clean_text(text: Optional[str], force_ascii: bool = False) -> str:
    """
    Sanitizes text to prevent encoding issues (e.g., UnicodeEncodeError).

    Args:
        text: Input string (or None)
        force_ascii: If True, replaces non-ASCII chars with '?'

    Returns:
        Cleaned string, or empty string if input is None
    """
    if text is None:
        return ""

    # Remove Unicode line/paragraph separators
    text = re.sub(r"[\u2028\u2029]", " ", text)

    if force_ascii:
        # Encode to ASCII, replacing non-ASCII chars with '?'
        text = text.encode("ascii", errors="replace").decode("ascii")

    return text.strip()
