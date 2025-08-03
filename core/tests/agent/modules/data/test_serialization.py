"""Test module for serialization utilities and data transformation functions."""

import json
from collections import namedtuple
from enum import Enum
from typing import Any, Dict

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
    GREEN = 3


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

    def test_make_serializable_with_none_values(self) -> None:
        """Test make_serializable handles None values correctly."""
        data = {
            "valid": "value",
            "none_value": None,
            "nested": {"empty": None, "list": [1, None, 3]},
        }

        result = make_serializable(data)
        assert result["valid"] == "value"
        assert result["none_value"] is None
        assert result["nested"]["empty"] is None
        assert result["nested"]["list"] == [1, None, 3]

    def test_export_to_dict_with_cycle_detection(self) -> None:
        """Test export_to_dict properly handles circular references."""
        # Create circular reference
        obj1: Dict[str, Any] = {"name": "obj1"}
        obj2 = {"name": "obj2", "ref": obj1}
        obj1["ref"] = obj2

        result = export_to_dict(obj1)
        assert result["name"] == "obj1"
        assert result["ref"]["name"] == "obj2"
        assert result["ref"]["ref"] == "<cycle detected>"

    def test_export_to_dict_with_namedtuple(self) -> None:
        """Test export_to_dict handles namedtuples correctly."""
        Point = namedtuple("Point", ["x", "y"])
        p = Point(10, 20)

        result = export_to_dict(p)
        assert result == {"x": 10, "y": 20}

    def test_export_to_dict_with_enum_values(self) -> None:
        """Test export_to_dict serializes enum values correctly."""
        data = {
            "colors": [Color.RED, Color.BLUE, Color.GREEN],
            "primary": Color.RED,
        }

        result = export_to_dict(data)
        assert result["colors"] == ["red", "blue", 3]
        assert result["primary"] == "red"

    def test_export_to_dict_with_ignore_keys(self) -> None:
        """Test export_to_dict properly ignores specified keys."""
        data = {
            "public": "data",
            "__jac__": "internal",
            "nested": {"__jac__": "secret", "visible": True},
        }

        result = export_to_dict(data, ignore_keys=["__jac__"])
        assert "__jac__" not in result
        assert result["public"] == "data"
        assert "__jac__" not in result["nested"]
        assert result["nested"]["visible"] is True

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

    def test_safe_json_dump_with_non_serializable_objects(self) -> None:
        """Test safe_json_dump handles non-serializable objects gracefully."""

        class Unserializable:
            def __str__(self) -> str:
                return "unserializable"

        data = {
            "valid": "data",
            "problem": Unserializable(),
        }

        result = safe_json_dump(data)
        assert result is None  # Should fail and return None

    def test_convert_str_to_json_with_malformed_json_recovery(self) -> None:
        """Test convert_str_to_json handles malformed JSON with missing closing brace."""
        malformed_json = '{"name": "test", "value": 42'  # Missing closing brace

        result = convert_str_to_json(malformed_json)
        assert result is not None
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_convert_str_to_json_with_json_wrapped_in_markdown(self) -> None:
        """Test convert_str_to_json handles JSON wrapped in markdown code blocks."""
        wrapped_json = """```json
        {"key": "value"}
        ```"""

        result = convert_str_to_json(wrapped_json)
        assert result == {"key": "value"}

    def test_convert_str_to_json_with_invalid_input(self) -> None:
        """Test convert_str_to_json returns None for completely invalid input."""
        result = convert_str_to_json("this is not json")
        assert result is None

    def test_convert_str_to_json_with_list_input(self) -> None:
        """Test convert_str_to_json handles list input correctly."""
        result = convert_str_to_json([1, 2, 3])
        assert result == {"list": [1, 2, 3]}

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

    def test_yaml_dumps_with_empty_data(self) -> None:
        """Test yaml_dumps returns None for empty input."""
        assert yaml_dumps(None) is None
        assert yaml_dumps({}) is None

    def test_yaml_dumps_with_non_serializable_objects(self) -> None:
        """Test yaml_dumps handles non-serializable objects gracefully."""

        class Unserializable:
            pass

        data = {
            "valid": "data",
            "problem": Unserializable(),
        }

        result = yaml_dumps(data)
        assert result is not None
        assert "problem" in result
