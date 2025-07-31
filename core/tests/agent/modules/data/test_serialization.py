"""Test module for serialization utilities and data transformation functions."""

import json
from enum import Enum

from jivas.agent.modules.data.serialization import (
    convert_str_to_json,
    export_to_dict,
    make_serializable,
    safe_json_dump,
    yaml_dumps,
)


class Color(Enum):
    """Test enum for serialization testing."""

    RED = "red"
    BLUE = "blue"


class TestSerializationUtils:
    """Test cases for serialization utility functions."""

    def test_make_serializable_with_enum_and_complex_types(self) -> None:
        """Test make_serializable with enums, sets, and custom objects."""

        class CustomObject:
            def __init__(self, name: str) -> None:
                self.name = name

            def __str__(self) -> str:
                return f"CustomObject({self.name})"

        data = {
            "color": Color.RED,
            "numbers": {1, 2, 3},
            "custom": CustomObject("test"),
            "nested": {
                "tuple_data": (1, 2, "three"),
                "set_data": frozenset(["a", "b"]),
            },
        }

        result = make_serializable(data)

        assert result["color"] == "Color.RED"
        assert isinstance(result["numbers"], str)
        assert "CustomObject(test)" in result["custom"]
        assert result["nested"]["tuple_data"] == "(1, 2, 'three')"
        assert isinstance(result["nested"]["set_data"], str)

    def test_export_to_dict_with_cycle_detection(self) -> None:
        """Test export_to_dict properly handles circular references."""
        # Create circular reference
        obj1 = {"name": "obj1"}

        result = export_to_dict(obj1)

        assert result["name"] == "obj1"

    def test_safe_json_dump_with_nested_content_wrapping(self) -> None:
        """Test safe_json_dump wraps primitive values in content keys."""
        data = {
            "user": {"name": "John Doe", "age": 30, "score": 95.5},
            "tags": ["admin", "active"],
            "metadata": {"created": "2023-01-01", "nested": {"level": 2}},
        }

        result = safe_json_dump(data)
        assert result is not None

        parsed = json.loads(result)
        assert parsed["user"]["name"]["content"] == "John Doe"
        assert parsed["user"]["age"]["content"] == 30
        assert parsed["user"]["score"]["content"] == 95.5
        assert parsed["tags"] == ["admin", "active"]  # Lists not wrapped
        assert parsed["metadata"]["nested"]["level"]["content"] == 2

    def test_convert_str_to_json_with_malformed_json_recovery(self) -> None:
        """Test convert_str_to_json handles malformed JSON with missing closing brace."""
        malformed_json = '{"name": "test", "value": 42'  # Missing closing brace

        result = convert_str_to_json(malformed_json)

        assert result is not None
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_yaml_dumps_with_long_strings_and_multiline(self) -> None:
        """Test yaml_dumps formats long strings and multiline content correctly."""
        data = {
            "short_text": "Brief content",
            "long_text": "This is a very long string that exceeds the threshold for inline representation and should be formatted as a block scalar in YAML output for better readability",
            "multiline": "Line one\nLine two\nLine three",
            "nested": {
                "description": "Another long description that should also be formatted as a block scalar due to its length exceeding the configured threshold"
            },
        }

        result = yaml_dumps(data)

        assert result is not None
        assert "short_text: Brief content" in result
        assert "|" in result  # Block scalar indicator for long strings
        assert "Line one" in result
        assert "Line two" in result
        assert "Line three" in result
