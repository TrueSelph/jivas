"""Test module for serialization utilities and data transformation functions."""

import json
from collections import namedtuple
from enum import Enum
from typing import Any, Dict
from unittest.mock import patch

import yaml

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

    # ==========================================================================
    # Tests for make_serializable
    # ==========================================================================

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

        assert result["color"] == str(Color.RED)
        assert isinstance(result["numbers"], str)
        assert "CustomObject(test)" in result["custom"]
        assert result["nested"]["tuple_data"] == str((1, 2, "three"))
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

    def test_make_serializable_with_toplevel_set(self) -> None:
        """Test make_serializable with a set as the top-level object."""
        data = {1, 2, 3}
        result = make_serializable(data)
        assert result == str({1, 2, 3})

    def test_make_serializable_with_toplevel_list(self) -> None:
        """Test make_serializable with a list as the top-level object."""
        data = [1, "two", {3}]
        result = make_serializable(data)
        assert result == [1, "two", str({3})]

    # ==========================================================================
    # Tests for export_to_dict
    # ==========================================================================

    def test_export_to_dict_with_cycle_detection(self) -> None:
        """Test export_to_dict properly handles circular references."""
        obj1: Dict[str, Any] = {"name": "obj1"}
        obj2 = {"name": "obj2", "ref": obj1}
        obj1["ref"] = obj2

        result = export_to_dict(obj1)
        assert result["name"] == "obj1"
        assert result["ref"]["name"] == "obj2"
        assert result["ref"]["ref"] == "<cycle detected>"

    def test_export_to_dict_with_list_input(self) -> None:
        """Test export_to_dict handles a list as top-level input."""
        data = [1, {"key": "value"}]
        result = export_to_dict(data)
        assert result == {"value": [1, {"key": "value"}]}

    def test_export_to_dict_with_plain_object(self) -> None:
        """Test export_to_dict with a plain object instance."""
        obj = object()
        result = export_to_dict(obj)
        assert "value" in result
        assert isinstance(result["value"], str)
        assert "object object at" in result["value"]

    def test_export_to_dict_with_generic_object(self) -> None:
        """Test export_to_dict with a generic object with __dict__."""

        class Generic:
            def __init__(self) -> None:
                self.a = 1
                self.b = "two"

        obj = Generic()
        result = export_to_dict(obj)
        assert result == {"a": 1, "b": "two"}

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

    def test_export_to_dict_with_default_ignore_keys(self) -> None:
        """Test export_to_dict with default ignore_keys ('__jac__')."""
        data = {"a": 1, "__jac__": "ignored"}
        result = export_to_dict(data)
        assert result == {"a": 1}

    def test_export_to_dict_with_set_and_frozenset(self) -> None:
        """Test export_to_dict converts sets and frozensets to lists."""
        data = {
            "my_set": {1, 2, 3},
            "my_frozenset": frozenset(["a", "b"]),
        }
        result = export_to_dict(data)
        assert isinstance(result["my_set"], list)
        assert sorted(result["my_set"]) == [1, 2, 3]
        assert isinstance(result["my_frozenset"], list)
        assert sorted(result["my_frozenset"]) == ["a", "b"]

    def test_export_to_dict_with_primitive_input(self) -> None:
        """Test export_to_dict with a primitive (non-dict/list) input."""
        assert export_to_dict("a string") == {"value": "a string"}
        assert export_to_dict(123) == {"value": 123}
        assert export_to_dict(None) == {"value": None}

    def test_export_to_dict_with_slots(self) -> None:
        """Test export_to_dict with an object using __slots__."""

        class Slotted:
            __slots__ = ["x", "y"]

            def __init__(self, x: int, y: int) -> None:
                self.x = x
                self.y = y

            def __str__(self) -> str:
                return f"Slotted(x={self.x}, y={self.y})"

        obj = Slotted(1, 2)
        result = export_to_dict(obj)
        assert result == {"value": "Slotted(x=1, y=2)"}

    # ==========================================================================
    # Tests for safe_json_dump
    # ==========================================================================

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
        assert parsed["tags"] == ["admin", "active"]
        assert parsed["metadata"]["nested"]["level"]["content"] == 2

    def test_safe_json_dump_with_mixed_list(self) -> None:
        """Test safe_json_dump with a list of mixed dicts and primitives."""
        data = {"items": [{"id": 1}, "string", {"id": 2}]}
        result = safe_json_dump(data)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["items"][0]["id"]["content"] == 1
        assert parsed["items"][1] == "string"
        assert parsed["items"][2]["id"]["content"] == 2

    @patch("jivas.agent.modules.data.serialization.json.dumps")
    def test_safe_json_dump_exception(self, mock_dumps: Any) -> None:
        """Test that safe_json_dump handles exceptions and returns None."""
        mock_dumps.side_effect = TypeError("JSON dump error")
        result = safe_json_dump({"a": 1})
        assert result is None

    def test_safe_json_dump_with_non_serializable_objects(self) -> None:
        """Test safe_json_dump handles non-serializable objects gracefully."""

        class Unserializable:
            pass

        data = {"problem": Unserializable()}
        result = safe_json_dump(data)
        assert result is None

    def test_safe_json_dump_with_value_error(self) -> None:
        """Test safe_json_dump handles ValueError from non-compliant floats."""
        data = {"value": float("inf")}
        result = safe_json_dump(data)
        assert result is None

    def test_safe_json_dump_with_non_dict_input(self) -> None:
        """Test safe_json_dump with non-dictionary input."""
        result = safe_json_dump([1, 2, 3])  # type: ignore
        assert result is None

    def test_safe_json_dump_with_empty_dict(self) -> None:
        """Test safe_json_dump with an empty dictionary."""
        result = safe_json_dump({})
        assert result == "{}"

    # ==========================================================================
    # Tests for convert_str_to_json
    # ==========================================================================

    def test_convert_str_to_json_with_malformed_json_recovery(self) -> None:
        """Test convert_str_to_json handles malformed JSON with missing closing brace."""
        malformed_json = '{"name": "test", "value": 42}'
        result = convert_str_to_json(malformed_json)
        assert result == {"name": "test", "value": 42}

    def test_convert_str_to_json_with_failed_recovery(self) -> None:
        """Test convert_str_to_json where adding a brace does not fix it."""
        malformed = '{"key":}'
        result = convert_str_to_json(malformed)
        assert result is None

    def test_convert_str_to_json_with_unclosed_brace_and_invalid_json(self) -> None:
        """Test recovery for unclosed brace that still results in invalid JSON."""
        malformed = '{"a": {"b": 1} '  # Unclosed inner dict
        result = convert_str_to_json(malformed)
        assert result is None

    def test_convert_str_to_json_with_unrecoverable_error(self) -> None:
        """Test convert_str_to_json with an unrecoverable syntax error."""
        # This string, when appended with '}', is still invalid JSON.
        malformed = '{"key": "value",,}'
        result = convert_str_to_json(malformed)
        assert result is None

    def test_convert_str_to_json_with_other_syntax_error(self) -> None:
        """Test convert_str_to_json with a syntax error other than a missing brace."""
        malformed = "{'key': 'value',}"  # Invalid syntax for json.loads
        result = convert_str_to_json(malformed)
        assert result == {"key": "value"}

    def test_convert_str_to_json_with_python_literal(self) -> None:
        """Test convert_str_to_json with a Python literal string (e.g., tuple)."""
        py_literal_str = "{'key': (1, 2), 'valid': True}"
        result = convert_str_to_json(py_literal_str)
        assert result == {"key": (1, 2), "valid": True}

    def test_convert_str_to_json_with_python_literal_list(self) -> None:
        """Test convert_str_to_json with a Python literal string that is a list."""
        py_literal_str = "['a', 1, None]"
        result = convert_str_to_json(py_literal_str)
        assert result == {"data": ["a", 1, None]}

    def test_convert_str_to_json_with_string_list(self) -> None:
        """Test convert_str_to_json with a string that is a JSON list."""
        str_list = '[1, "a", {"b": 2}]'
        result = convert_str_to_json(str_list)
        assert result == {"data": [1, "a", {"b": 2}]}

    def test_convert_str_to_json_with_json_wrapped_in_markdown(self) -> None:
        """Test convert_str_to_json handles JSON wrapped in markdown code blocks."""
        wrapped_json = '```json\n{"key": "value"}\n```'
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

    def test_convert_str_to_json_with_dict_input(self) -> None:
        """Test convert_str_to_json with a dict as input."""
        data = {"key": "value"}
        result = convert_str_to_json(data)
        assert result == data

    def test_convert_str_to_json_with_bytes_input(self) -> None:
        """Test convert_str_to_json with bytes input returns None."""
        result = convert_str_to_json(b'{"key": "value"}')
        assert result is None

    # ==========================================================================
    # Tests for yaml_dumps and LongStringDumper
    # ==========================================================================

    def test_yaml_dumps_with_long_strings_and_multiline(self) -> None:
        """Test yaml_dumps formats long strings and multiline content correctly."""
        long_string = "a" * 160
        data = {
            "short_text": "Brief content",
            "long_text": long_string,
            "multiline": "Line one\nLine two",
        }
        result = yaml_dumps(data)
        assert result is not None
        assert "short_text: Brief content" in result
        assert f"long_text: |-\n  {long_string}" in result
        assert "multiline: |-\n  Line one\n  Line two" in result

    def test_long_string_dumper_stripping(self) -> None:
        """Test that the LongStringDumper correctly strips whitespace."""
        data = {"multiline_with_spaces": "line 1  \nline 2 \n\nline 4\t"}
        expected_yaml = """multiline_with_spaces: |-
  line 1
  line 2

  line 4"""
        result = yaml_dumps(data)
        assert result is not None
        assert result.strip() == expected_yaml.strip()

    def test_long_string_dumper_short_string_with_trailing_whitespace(self) -> None:
        """Test LongStringDumper strips trailing whitespace from short strings."""
        data = {"key": "value  "}
        expected_yaml = "key: value"
        result = yaml_dumps(data)
        assert result is not None
        assert result.strip() == expected_yaml

    def test_long_string_dumper_short_string_no_trailing_whitespace(self) -> None:
        """Test LongStringDumper with a short string without trailing whitespace."""
        data = {"key": "value"}
        expected_yaml = "key: value"
        result = yaml_dumps(data)
        assert result is not None
        assert result.strip() == expected_yaml

    def test_yaml_dumps_with_empty_data(self) -> None:
        """Test yaml_dumps returns None for empty or None input."""
        assert yaml_dumps(None) is None
        assert yaml_dumps({}) is None

    def test_yaml_dumps_with_non_serializable_objects(self) -> None:
        """Test yaml_dumps handles non-serializable objects gracefully."""

        class Unserializable:
            pass

        data = {"problem": Unserializable()}
        result = yaml_dumps(data)
        assert result is not None
        assert "problem" in result
        assert "Unserializable" in result

    @patch("jivas.agent.modules.data.serialization.yaml.dump")
    def test_yaml_dumps_exception(self, mock_dump: Any) -> None:
        """Test yaml_dumps handles exceptions during YAML conversion."""
        mock_dump.side_effect = yaml.YAMLError("YAML processing error")
        result = yaml_dumps({"a": 1})
        assert result is None

    def test_yaml_dumps_output_is_none_for_separator(self) -> None:
        """Test yaml_dumps returns None for YAML that is only a separator."""
        with patch(
            "jivas.agent.modules.data.serialization.yaml.dump", return_value="---"
        ) as mock_dump:
            result = yaml_dumps({"some": "data"})
            assert result is None
            mock_dump.assert_called_once()

    def test_yaml_dumps_with_unicode(self) -> None:
        """Test yaml_dumps handles unicode characters correctly."""
        data = {"key": "你好世界"}
        result = yaml_dumps(data)
        assert result is not None
        assert "你好世界" in result
