"""Tests for jivas.agent.modules.agentlib.utils."""

import os
import types
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

import pytest
import pytz
import requests
import yaml
from pytest_mock import MockerFixture

from jivas.agent.modules.agentlib.utils import (
    LongStringDumper,
    Utils,
)


class Dummy:
    """A dummy class for testing custom object serialization."""

    def __str__(self) -> str:
        """Returns the dummy instance."""
        return "DummyInstance"


class TestUtils:
    """Tests for the Utils class."""

    def test_short_string_without_newlines(self) -> None:
        """Test that short strings without newlines are not modified."""
        # Arrange
        dumper = LongStringDumper
        test_str = "This is a short string without newlines"

        # Act
        yaml_str = yaml.dump(test_str, Dumper=dumper)

        # Assert
        assert "|" not in yaml_str
        assert test_str in yaml_str

    def test_long_string_or_newline_handling(self) -> None:
        """Test that long strings or strings with newlines are handled correctly."""
        # Arrange
        dumper = LongStringDumper(None)  # type: ignore
        long_string = "a" * 151  # String longer than 150 characters
        string_with_newline = "This is a string\nwith a newline"

        # Act
        long_string_node = dumper.represent_scalar("tag:yaml.org,2002:str", long_string)
        newline_string_node = dumper.represent_scalar(
            "tag:yaml.org,2002:str", string_with_newline
        )

        # Assert
        assert long_string_node.style == "|"
        assert long_string_node.value == long_string
        assert newline_string_node.style == "|"
        assert newline_string_node.value == "This is a string\nwith a newline"

    def test_default_path_when_env_var_not_set(self, mocker: MockerFixture) -> None:
        """Test that the default path is returned when the env var is not set."""
        # Mock os.environ.get to return None for unset env var
        mocker.patch.dict("os.environ", {}, clear=True)

        # Call the method
        result = Utils.get_descriptor_root()

        # Verify results
        assert result == ".jvdata"

    def test_default_actions_path_when_env_var_not_set(
        self, mocker: MockerFixture
    ) -> None:
        """Test that the default path is returned when the env var is not set."""
        # Mock os.environ.get to return None for unset env var
        mocker.patch.dict("os.environ", {})

        # Mock os.path.exists and os.makedirs
        mocker.patch("os.path.exists", return_value=False)
        mock_makedirs = mocker.patch("os.makedirs")

        # Call the method
        result = Utils.get_actions_root()

        # Verify default path is returned
        assert result == "actions"

        # Verify directory was created
        mock_makedirs.assert_called_once_with("actions")

    def test_empty_string_env_var_handled(self, mocker: MockerFixture) -> None:
        """Test that an empty string env var is handled correctly."""
        # Mock os.environ.get to return empty string
        mocker.patch.dict("os.environ", {"JIVAS_ACTIONS_ROOT_PATH": ""})

        # Mock os.path.exists and os.makedirs
        mocker.patch("os.path.exists", return_value=False)
        mock_makedirs = mocker.patch("os.makedirs")

        # Call the method
        result = Utils.get_actions_root()

        # Verify empty string is returned
        assert result == ""

        # Verify directory was created
        mock_makedirs.assert_called_once_with("")

    def test_default_daf_path_when_env_var_not_set(self, mocker: MockerFixture) -> None:
        """Test that the default path is returned when the env var is not set."""
        # Arrange
        mocker.patch.dict("os.environ", {}, clear=True)
        mocker.patch("os.path.exists", return_value=False)
        mock_makedirs = mocker.patch("os.makedirs")

        # Act
        result = Utils.get_daf_root()

        # Assert
        assert result == "daf"
        mock_makedirs.assert_called_once_with("daf")

    def test_empty_string_env_var_handled_daf(self, mocker: MockerFixture) -> None:
        """Test that an empty string env var is handled correctly for DAF."""
        # Arrange
        mocker.patch.dict("os.environ", {"JIVAS_DAF_ROOT_PATH": ""})
        mocker.patch("os.path.exists", return_value=False)
        mock_makedirs = mocker.patch("os.makedirs")

        # Act
        result = Utils.get_daf_root()

        # Assert
        assert result == ""
        mock_makedirs.assert_called_once_with("")

    def test_convert_path_with_multiple_segments(self) -> None:
        """Test converting a path with multiple segments to module path."""
        # Arrange
        test_path = "/a/b/c/d"

        # Act
        result = Utils.path_to_module(test_path)

        # Assert
        assert result == "a.b.c.d"

    def test_returns_path_for_valid_package(self, tmp_path: Any) -> None:
        """Test that the path is returned for a valid package."""
        # Arrange
        rootdir = str(tmp_path)
        namespace = "test_namespace"
        package = "test_package"
        package_path = os.path.join(rootdir, namespace, package)
        os.makedirs(package_path)

        # Create required file
        with open(os.path.join(package_path, "info.yaml"), "w") as f:
            f.write("")

        # Act
        result = Utils.find_package_folder(rootdir, f"{namespace}/{package}")

        # Assert
        assert result == package_path

    def test_namespace_path_does_not_exist(self, mocker: MockerFixture) -> None:
        """Test that None is returned when the namespace path does not exist."""
        # Arrange
        rootdir = "/fake/rootdir"
        name = "nonexistent_namespace/package_folder"

        # Mock os.path.isdir to return False
        mocker.patch("os.path.isdir", return_value=False)

        # Act
        result = Utils.find_package_folder(rootdir, name)

        # Assert
        assert result is None

    def test_invalid_format_raises_value_error(self, mocker: MockerFixture) -> None:
        """Test that ValueError is logged when name format is invalid."""
        # Arrange
        mock_logger = mocker.patch("jivas.agent.modules.agentlib.utils.logger")
        invalid_name = "invalidformat"

        # Act
        result = Utils.find_package_folder("/some/rootdir", invalid_name)

        # Assert
        assert result is None
        mock_logger.error.assert_called_once_with(
            "Invalid format. Please use 'namespace/package_folder'."
        )

    def test_package_folder_not_found(self, mocker: MockerFixture) -> None:
        """Test that None is returned when the package folder is not found."""
        # Arrange
        rootdir = "/fake/rootdir"
        name = "namespace/nonexistent_package"
        required_files = {"info.yaml"}

        # Mock os.path.isdir to return True for namespace path
        mocker.patch("os.path.isdir", return_value=True)

        # Mock os.walk to simulate directory structure without the package folder
        mocker.patch("os.walk", return_value=[(rootdir + "/namespace", [], [])])

        # Act
        result = Utils.find_package_folder(rootdir, name, required_files)

        # Assert
        assert result is None

    def test_list_to_phrase_with_multiple_items(self) -> None:
        """Test that list of strings is converted to comma-separated phrase with 'and'."""
        # Arrange
        test_list: list[str] = ["one", "two", "three"]

        # Act
        result = Utils.list_to_phrase(test_list)

        # Assert
        assert result == "one, two, and three"

    def test_list_to_phrase_with_empty_list(self) -> None:
        """Test that empty list returns empty string."""
        # Arrange
        test_list: list[str] = []

        # Act
        result = Utils.list_to_phrase(test_list)

        # Assert
        assert result == ""

    def test_single_element_list(self) -> None:
        """Test that a single element list returns the element itself."""
        # Arrange
        lst = ["one"]

        # Act
        result = Utils.list_to_phrase(lst)

        # Assert
        assert result == "one"

    def test_replace_single_placeholder(self) -> None:
        """Test replacing a single placeholder in a string with value from dictionary."""
        # Arrange
        test_string = "Hello {{name}}!"
        placeholders = {"name": "World"}

        # Act
        result = Utils.replace_placeholders(test_string, placeholders)

        # Assert
        assert result == "Hello World!"

    def test_string_without_placeholders(self) -> None:
        """Test that a string without placeholders is returned unchanged."""
        # Arrange
        test_string = "Hello World!"
        placeholders = {"name": "John"}

        # Act
        result = Utils.replace_placeholders(test_string, placeholders)

        # Assert
        assert result == "Hello World!"

    def test_replace_placeholders_with_list_value(self) -> None:
        """Test that placeholders with list values are replaced correctly."""
        # Arrange
        placeholders = {"items": ["apple", "banana", "cherry"]}
        input_string = "I have {{items}}."
        expected_output = "I have apple, banana, and cherry."

        # Act
        result = Utils.replace_placeholders(input_string, placeholders)

        # Assert
        assert result == expected_output

    def test_replace_placeholders_with_list_input(self) -> None:
        """Test that replace_placeholders correctly processes a list input."""
        # Arrange
        input_list = ["Hello, {{name}}!", "Welcome to {{place}}."]
        placeholders = {"name": "Alice", "place": "Wonderland"}

        # Act
        result = Utils.replace_placeholders(input_list, placeholders)

        # Assert
        assert result == ["Hello, Alice!", "Welcome to Wonderland."]

    def test_type_error_on_invalid_input(self) -> None:
        """Test that TypeError is raised when input is neither a string nor a list."""
        # Arrange
        invalid_input = 123  # An integer, which is not a valid input type
        placeholders = {"key": "value"}

        # Act & Assert
        with pytest.raises(
            TypeError, match="Input must be a string or a list of strings."
        ):
            Utils.replace_placeholders(invalid_input, placeholders)  # type: ignore

    def test_short_message_returns_single_chunk(self) -> None:
        """Test that a short message is returned as a single chunk."""
        # Arrange
        message = "This is a short message"
        max_length = 1024
        chunk_length = 1024

        # Act
        result = Utils.chunk_long_message(message, max_length, chunk_length)

        # Assert
        assert len(result) == 1
        assert result[0] == message

    def test_empty_string_returns_empty_list(self) -> None:
        """Test that an empty string returns an empty list."""
        # Arrange
        message = ""
        max_length = 1024
        chunk_length = 1024

        # Act
        result = Utils.chunk_long_message(message, max_length, chunk_length)

        # Assert
        assert len(result) == 1
        assert result[0] == ""

    def test_message_exceeding_chunk_length(self) -> None:
        """Test message that exceeds chunk_length is split correctly."""
        message = "This is a test " + "word " * 250  # Long message
        result = Utils.chunk_long_message(message, max_length=1000, chunk_length=100)

        # Ensure multiple chunks
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 100

    def test_escape_single_curly_braces(self) -> None:
        """Test that single curly braces are converted to double curly braces."""
        # Arrange
        input_str = "Hello {name}, welcome to {place}!"
        expected = "Hello {{name}}, welcome to {{place}}!"

        # Act
        result = Utils.escape_string(input_str)

        # Assert
        assert result == expected

    def test_list_input_returns_empty_with_error(self, caplog: Any) -> None:
        """Test that list input returns empty string and logs error."""
        # Arrange
        input_list: list[str] = ["test", "list"]

        # Act
        result = Utils.escape_string(input_list)  # type: ignore

        # Assert
        assert result == ""
        assert "Error expect string" in caplog.text
        assert input_list.__str__() in caplog.text

    def test_nested_dict_and_list_conversion(self) -> None:
        """Test that nested dictionaries and lists are properly converted."""
        # Arrange
        test_data: Dict[str, Any] = {
            "str_key": "string_value",
            "int_key": 42,
            "nested_dict": {
                "inner_key": "inner_value",
                "inner_list": [1, 2, {"key": "value"}],
            },
            "__jac__": "should_be_ignored",
        }

        # Act
        result = Utils.export_to_dict(test_data)

        # Assert
        expected = {
            "str_key": "string_value",
            "int_key": 42,
            "nested_dict": {
                "inner_key": "inner_value",
                "inner_list": [1, 2, {"key": "value"}],
            },
        }
        assert result == expected

    def test_empty_dict_input(self) -> None:
        """Test that empty dictionary input returns empty dictionary."""
        # Arrange
        test_data: dict = {}

        # Act
        result = Utils.export_to_dict(test_data)

        # Assert
        assert result == {}

    def test_stringify_complex_objects(self) -> None:
        """Test that complex objects are stringified correctly."""
        # Arrange
        complex_object = {
            "simple_key": "simple_value",
            "complex_key": datetime(2023, 10, 5, 12, 0, 0),
            "nested_dict": {
                "another_complex_key": UUID("12345678123456781234567812345678")
            },
            "list_of_objects": [
                datetime(2023, 10, 5, 12, 0, 0),
                UUID("87654321876543218765432187654321"),
            ],
        }
        expected_output = {
            "simple_key": "simple_value",
            "complex_key": "2023-10-05 12:00:00",
            "nested_dict": {
                "another_complex_key": "12345678-1234-5678-1234-567812345678"
            },
            "list_of_objects": [
                "2023-10-05 12:00:00",
                "87654321-8765-4321-8765-432187654321",
            ],
        }

        # Act
        result = Utils.export_to_dict(complex_object)

        # Assert
        assert result == expected_output

    def test_export_to_dict_with_object_having_dict(self) -> None:
        """Test export_to_dict with an object having a __dict__ attribute."""

        # Arrange
        class SampleObject:
            def __init__(self) -> None:
                self.attr1 = "value1"
                self.attr2 = 42

        sample_obj = SampleObject()

        # Act
        result = Utils.export_to_dict(sample_obj)

        # Assert
        assert result == {"attr1": "value1", "attr2": 42}

    def test_non_dict_input_returns_empty_dict(self) -> None:
        """Test that non-dict input returns an empty dictionary."""
        # Arrange
        non_dict_input: Any = "This is a string, not a dict"

        # Act
        result = Utils.export_to_dict(non_dict_input)

        # Assert
        assert result == {}

    def test_simple_types_conversion(self) -> None:
        """Test that dictionary with simple types is converted to JSON string correctly."""
        # Arrange
        test_dict = {"string": "test", "integer": 42, "float": 3.14}
        expected = '{"string": {"content": "test"}, "integer": {"content": 42}, "float": {"content": 3.14}}'

        # Act
        result = Utils.safe_json_dump(test_dict)

        # Assert
        assert result == expected

    def test_nonserializable_types_return_none(self) -> None:
        """Test that None is returned for non-serializable types."""
        # Arrange
        test_dict = {"function": lambda x: x, "valid": "test"}

        # Act
        result = Utils.safe_json_dump(test_dict)

        # Assert
        assert result is None

    def test_safe_json_dump_with_nested_dict(self) -> None:
        """Test safe_json_dump with a nested dictionary."""
        # Arrange
        data = {
            "key1": "value1",
            "key2": 123,
            "key3": {
                "nested_key1": "nested_value1",
                "nested_key2": 456,
                "nested_key3": {"deeply_nested_key": "deeply_nested_value"},
            },
        }

        # Act
        result = Utils.safe_json_dump(data)

        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert '"key1": {"content": "value1"}' in result
        assert '"key2": {"content": 123}' in result
        assert '"nested_key1": {"content": "nested_value1"}' in result
        assert '"nested_key2": {"content": 456}' in result
        assert '"deeply_nested_key": {"content": "deeply_nested_value"}' in result

    def test_list_serialization(self) -> None:
        """Test that lists within the dictionary are processed correctly."""
        # Arrange
        data = {
            "key1": "value1",
            "key2": [1, 2, 3],
            "key3": [{"nested_key": "nested_value"}],
        }
        expected_output = '{"key1": {"content": "value1"}, "key2": [1, 2, 3], "key3": [{"nested_key": {"content": "nested_value"}}]}'

        # Act
        result = Utils.safe_json_dump(data)

        # Assert
        assert result == expected_output

    def test_date_now_default_timezone_and_format(self, mocker: MockerFixture) -> None:
        """Test date_now returns correctly formatted string for default timezone and format."""
        # Arrange
        mock_dt = datetime(2023, 1, 1, 12, 0, tzinfo=pytz.timezone("US/Eastern"))
        mocker.patch("pytz.timezone", return_value=pytz.timezone("US/Eastern"))
        mocker.patch(
            "jivas.agent.modules.agentlib.utils.datetime", return_value=mock_dt
        )
        mocker.patch(
            "jivas.agent.modules.agentlib.utils.datetime", return_value=mock_dt
        )

        # Act
        result = Utils.date_now()

        # Assert
        assert result

    def test_date_now_invalid_timezone(self) -> None:
        """Test date_now returns None when invalid timezone is provided."""
        # Act
        result = Utils.date_now(timezone="Invalid/Timezone")

        # Assert
        assert result is None

    def test_valid_uuid_v4_returns_true(self) -> None:
        """Test that a valid UUID v4 string returns True."""
        # Arrange
        valid_uuid = "c9bf9e57-1685-4c89-bafb-ff5af830be8a"

        # Act
        result = Utils.is_valid_uuid(valid_uuid)

        # Assert
        assert result is True

    def test_empty_string_returns_false(self) -> None:
        """Test that an empty string returns False."""
        # Arrange
        empty_uuid = ""

        # Act
        result = Utils.is_valid_uuid(empty_uuid)

        # Assert
        assert result is False

    def test_returns_first_element_from_nonempty_list(self) -> None:
        """Test that the first element is returned from a nonempty list."""
        # Arrange
        test_list: list[int] = [1, 2, 3]

        # Act
        result = Utils.node_obj(test_list)

        # Assert
        assert result == 1

    def test_returns_none_for_empty_list(self) -> None:
        """Test that None is returned for an empty list."""
        # Arrange
        test_list: list[Any] = []

        # Act
        result = Utils.node_obj(test_list)

        # Assert
        assert result is None

    def test_empty_actions_data_returns_none(self) -> None:
        """Test that None is returned when actions data is empty."""
        # Arrange
        actions_data: list[Dict[str, Any]] = []

        # Act
        result = Utils.order_interact_actions(actions_data)

        # Assert
        assert result is None

    @staticmethod
    def create_action(
        name: str,
        before: str | None = None,
        after: str | None = None,
        weight: int | None = None,
        action_type: str = "interact_action",
    ) -> Dict[str, Any]:
        """Helper function to create a structured action dictionary."""
        order: Dict[str, Any] = {}
        if before:
            order["before"] = before
        if after:
            order["after"] = after
        if weight is not None:
            order["weight"] = weight

        return {
            "context": {
                "_package": {
                    "meta": {"type": action_type},
                    "name": name,
                    "config": {"order": order} if order else {},
                }
            }
        }

    def test_basic_ordering(self) -> None:
        """Test that actions are ordered correctly based on 'before' and 'after' constraints."""
        # Arrange
        actions_data: list[Dict[str, Any]] = [
            self.create_action("A"),
            self.create_action("B", before="A"),
        ]

        # Act
        result = Utils.order_interact_actions(actions_data)

        if result is None:
            raise ValueError("result is None")
        sorted_names = [action["context"]["_package"]["name"] for action in result]

        # Assert
        assert sorted_names == ["B", "A"]

    def test_before_all(self) -> None:
        """Test that 'before: all' places the action first."""
        # Arrange
        actions_data: list[Dict[str, Any]] = [
            self.create_action("A"),
            self.create_action("B", before="all"),
            self.create_action("C"),
        ]

        # Act
        result = Utils.order_interact_actions(actions_data)

        if result is None:
            raise ValueError("result is None")

        sorted_names = [action["context"]["_package"]["name"] for action in result]

        # Assert
        assert sorted_names == ["B", "A", "C"]

    def test_after_all(self) -> None:
        """Test that 'after: all' places the action last."""
        # Arrange
        actions_data: list[Dict[str, Any]] = [
            self.create_action("A"),
            self.create_action("B", after="all"),
            self.create_action("C"),
        ]

        # Act
        result = Utils.order_interact_actions(actions_data)

        if result is None:
            raise ValueError("result is None")

        sorted_names = [action["context"]["_package"]["name"] for action in result]

        # Assert
        assert sorted_names == ["A", "C", "B"]

    def test_complex_dependencies(self) -> None:
        """Test complex dependencies where multiple actions have before/after constraints."""
        # Arrange
        actions_data: list[Dict[str, Any]] = [
            self.create_action("A"),
            self.create_action("B", before="A"),
            self.create_action("C", after="B"),
            self.create_action("D", before="C"),
        ]

        # Act
        result = Utils.order_interact_actions(actions_data)

        if result is None:
            raise ValueError("result is None")

        sorted_names = [action["context"]["_package"]["name"] for action in result]

        # Assert
        assert (
            sorted_names == ["B", "C", "D", "A"]
            or sorted_names == ["B", "D", "C", "A"]
            or sorted_names == ["B", "D", "A", "C"]
            or sorted_names == ["B", "A", "D", "C"]
        )

    def test_no_dependencies(self) -> None:
        """Test that when no dependencies are provided, order remains unchanged."""
        # Arrange
        actions_data: list[Dict[str, Any]] = [
            self.create_action("A"),
            self.create_action("B"),
            self.create_action("C"),
        ]

        # Act
        result = Utils.order_interact_actions(actions_data)

        if result is None:
            raise ValueError("result is None")

        sorted_names = [action["context"]["_package"]["name"] for action in result]

        # Assert
        assert sorted_names == ["A", "B", "C"]

    def test_circular_dependency(self) -> None:
        """Test that circular dependencies raise an exception."""
        # Arrange
        actions_data: list[Dict[str, Any]] = [
            self.create_action("A", before="B"),
            self.create_action("B", before="A"),
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="Circular dependency detected!"):
            Utils.order_interact_actions(actions_data)

    def test_mixed_interact_and_other_actions(self) -> None:
        """Test that non-interact actions remain at the end of the ordered list."""
        # Arrange
        actions_data: list[Dict[str, Any]] = [
            self.create_action("A", action_type="other"),
            self.create_action("B", before="all"),
            self.create_action("C"),
        ]

        # Act
        result = Utils.order_interact_actions(actions_data)

        if result is None:
            raise ValueError("result is None")

        sorted_names = [action["context"]["_package"]["name"] for action in result]

        # Assert
        assert sorted_names == ["B", "C", "A"]

    def test_empty_list_returns_none(self) -> None:
        """Test that an empty input list returns None."""
        # Act
        result = Utils.order_interact_actions([])

        # Assert
        assert result is None

    def test_detect_mime_type_from_file_path(self, mocker: MockerFixture) -> None:
        """Test that MIME type is correctly detected from file path."""
        # Arrange
        test_file_path = "test.jpg"
        expected_mime_type = "image/jpeg"
        expected_result = {"file_type": "image", "mime": expected_mime_type}

        # Mock mimetypes.guess_type to return expected MIME type
        with mocker.patch(
            "mimetypes.guess_type", return_value=(expected_mime_type, None)
        ):
            # Act
            result = Utils.get_mime_type(file_path=test_file_path)

            # Assert
            assert result == expected_result

    def test_handle_undetected_mime_type_with_unknown_extension(
        self, mocker: MockerFixture
    ) -> None:
        """Test handling of undetected MIME type with unknown file extension."""
        # Arrange
        test_file_path = "test.unknown"

        # Mock mimetypes.guess_type to return None
        with mocker.patch("mimetypes.guess_type", return_value=(None, None)):
            # Act
            result = Utils.get_mime_type(file_path=test_file_path)

            # Assert
            assert result is None

    def test_detect_mime_type_from_url(self, mocker: MockerFixture) -> None:
        """Test that MIME type is correctly detected from URL."""
        # Arrange
        test_url = "http://example.com/test.jpg"
        expected_mime_type = "image/jpeg"
        expected_result = {"file_type": "image", "mime": expected_mime_type}

        # Mock requests.head to return a response with the expected MIME type
        mock_response = mocker.Mock()
        mock_response.headers = {"Content-Type": expected_mime_type}
        mocker.patch("requests.head", return_value=mock_response)

        # Act
        result = Utils.get_mime_type(url=test_url)

        # Assert
        assert result == expected_result

    def test_request_exception_handling(self, mocker: MockerFixture) -> None:
        """Test that requests.RequestException is handled correctly."""
        # Arrange
        test_url = "http://example.com/test"
        mocker.patch(
            "requests.head", side_effect=requests.RequestException("Connection error")
        )
        mock_logger_error = mocker.patch(
            "jivas.agent.modules.agentlib.utils.logger.error"
        )

        # Act
        result = Utils.get_mime_type(url=test_url)

        # Assert
        assert result is None
        mock_logger_error.assert_called_once_with(
            "Error making HEAD request: Connection error"
        )

    def test_fallback_to_initial_mime_type(self) -> None:
        """Test that the function falls back to the initial MIME type when file_path and url are not provided."""
        # Arrange
        initial_mime_type = "application/pdf"
        expected_result = {"file_type": "document", "mime": initial_mime_type}

        # Act
        result = Utils.get_mime_type(mime_type=initial_mime_type)

        # Assert
        assert result == expected_result

    def test_handle_undetected_mime_type_from_url(self, mocker: MockerFixture) -> None:
        """Test handling of undetected MIME type from URL."""
        # Arrange
        test_url = "http://example.com/file.unknown"
        mock_response = mocker.Mock()
        mock_response.headers.get.return_value = "binary/octet-stream"

        # Mock requests.head to return a response with Content-Type as "binary/octet-stream"
        mocker.patch("requests.head", return_value=mock_response)

        # Act
        result = Utils.get_mime_type(url=test_url)

        # Assert
        assert result is None

    def test_handle_undetected_mime_type_without_url_or_file_type(
        self, mocker: MockerFixture
    ) -> None:
        """Test handling of undetected MIME type when neither URL nor file type is provided."""
        # Arrange
        test_file_path = None
        test_url = None
        test_mime_type = None

        # Mock logger to capture error messages
        mock_logger_error = mocker.patch(
            "jivas.agent.modules.agentlib.utils.logger.error"
        )

        # Act
        result = Utils.get_mime_type(
            file_path=test_file_path, url=test_url, mime_type=test_mime_type
        )

        # Assert
        assert result is None
        mock_logger_error.assert_called_once_with("Unsupported MIME Type: None")

    def test_detect_mime_type_from_audio_file_path(self, mocker: MockerFixture) -> None:
        """Test that MIME type is correctly detected as audio from file path."""
        # Arrange
        test_file_path = "test.mp3"
        expected_mime_type = "audio/mpeg"
        expected_result = {"file_type": "audio", "mime": expected_mime_type}

        # Mock mimetypes.guess_type to return expected MIME type
        with mocker.patch(
            "mimetypes.guess_type", return_value=(expected_mime_type, None)
        ):
            # Act
            result = Utils.get_mime_type(file_path=test_file_path)

            # Assert
            assert result == expected_result

    def test_detect_mime_type_from_url_as_video(self, mocker: MockerFixture) -> None:
        """Test that MIME type is correctly detected as video from URL."""
        # Arrange
        test_url = "http://example.com/video.mp4"
        expected_mime_type = "video/mp4"
        expected_result = {"file_type": "video", "mime": expected_mime_type}

        # Mock requests.head to return a response with the expected MIME type
        mock_response = mocker.Mock()
        mock_response.headers = {"Content-Type": expected_mime_type}
        mocker.patch("requests.head", return_value=mock_response)

        # Act
        result = Utils.get_mime_type(url=test_url)

        # Assert
        assert result == expected_result

    def test_valid_json_string_conversion(self) -> None:
        """Test that valid JSON string is converted to dictionary."""
        # Arrange
        test_json = '{"key": "value", "number": 42}'

        # Act
        result = Utils.convert_str_to_json(test_json)

        # Assert
        assert result == {"key": "value", "number": 42}

    def test_input_is_dict_or_list(self) -> None:
        """Test that input which is already a dict or list is returned as is."""
        # Arrange
        input_dict: str = '{"key": "value"}'
        input_list: str = '["item1", "item2"]'

        # Act
        result_dict = Utils.convert_str_to_json(input_dict)
        result_list = Utils.convert_str_to_json(input_list)

        # Assert
        assert result_dict == {"key": "value"}
        assert result_list == ["item1", "item2"]

    def test_json_decode_error_handling(self) -> None:
        """Test that JSONDecodeError is handled correctly."""
        # Arrange
        invalid_json_str = '{"key": "value"'

        # Act
        result = Utils.convert_str_to_json(invalid_json_str)

        # Assert
        assert result == {"key": "value"}

    def test_unexpected_exception_handling(self, mocker: MockerFixture) -> None:
        """Test that unexpected exceptions are logged and None is returned."""
        # Arrange
        invalid_json = (
            "{invalid: json}"  # This will cause a KeyError in ast.literal_eval
        )
        mock_logger_error = mocker.patch(
            "jivas.agent.modules.agentlib.utils.logger.error"
        )

        # Act
        result = Utils.convert_str_to_json(invalid_json)

        # Assert
        assert result is None
        mock_logger_error.assert_called_once()

    def test_convert_str_to_json_with_dict_input(self) -> None:
        """Test that convert_str_to_json returns the input when it is already a dict."""
        # Arrange
        input_data = {"key": "value"}

        # Act
        result = Utils.convert_str_to_json(input_data)  # type: ignore

        # Assert
        assert result == input_data

    def test_extract_first_name_from_full_name(self) -> None:
        """Test extracting first name from full name."""
        # Arrange
        full_name = "John Smith"

        # Act
        result = Utils.extract_first_name(full_name)

        # Assert
        assert result == "John"

    def test_extract_first_name_empty_string(self) -> None:
        """Test extracting first name from empty string."""
        # Arrange
        full_name = ""

        # Act
        result = Utils.extract_first_name(full_name)

        # Assert
        assert result == ""

    def test_make_serializable_primitives(self) -> None:
        """Test make_serializable handles primitive types as-is."""
        assert Utils.make_serializable(1) == 1
        assert Utils.make_serializable(3.14) == 3.14
        assert Utils.make_serializable("hi") == "hi"
        assert Utils.make_serializable(True) is True
        assert Utils.make_serializable(None) is None

    def test_make_serializable_nested_dict_and_list(self) -> None:
        """Test make_serializable handles nested dicts and lists."""
        data = {"int": 1, "list": [1, 2, {"a": 3}], "dict": {"nested": "val"}}
        result = Utils.make_serializable(data)
        assert result == {"int": 1, "list": [1, 2, {"a": 3}], "dict": {"nested": "val"}}

    def test_make_serializable_non_serializable(self) -> None:
        """Test make_serializable converts non-serializable objects to strings."""
        dt = types.SimpleNamespace(x=10)
        myset = {1, 2, 3}
        mytuple = (4, 5)

        class MyClass:
            def __str__(self) -> str:
                return "MyClassInstance"

        d = {
            "obj": dt,
            "set": myset,
            "tuple": mytuple,
            "custom": MyClass(),
        }
        result = Utils.make_serializable(d)
        assert result["obj"].startswith("namespace") and "x=10" in result["obj"]
        assert result["set"].startswith("{1") or result["set"].startswith(
            "{2"
        )  # As str
        assert result["tuple"] == str(mytuple)
        assert result["custom"] == "MyClassInstance"

    def test_make_serializable_empty_collections(self) -> None:
        """Test make_serializable returns empty collections as is or stringifies empty sets."""
        assert Utils.make_serializable({}) == {}
        assert Utils.make_serializable([]) == []
        assert Utils.make_serializable(set()) == "set()"  # As str

    def test_make_serializable_mixed(self) -> None:
        """Test make_serializable with a mixed list including sets and objects."""
        data = [{"num": 1}, (2, 3), {4, 5}, Dummy()]
        result = Utils.make_serializable(data)
        assert result[0] == {"num": 1}
        assert result[1] == str((2, 3))
        # Result[2] as str({'4, 5'}) - order is arbitrary
        assert result[2] == "{4, 5}" or result[2] == "{5, 4}"
        assert result[3] == "DummyInstance"

    def test_yaml_dumps_basic(self) -> None:
        """Test yaml_dumps correctly serializes a basic dict."""
        d = {"a": 1, "b": "string", "c": True}
        yml = Utils.yaml_dumps(d)
        assert yml is not None
        assert "a: 1" in yml
        assert "b: string" in yml
        assert "c: true" in yml

    def test_yaml_dumps_nested(self) -> None:
        """Test yaml_dumps handles nested structures and tuples."""
        d = {"a": [1, 2, {"b": (1, 2)}]}
        yml = Utils.yaml_dumps(d)
        assert yml is not None
        assert "a:" in yml
        assert "- 1" in yml
        assert "- 2" in yml
        assert "b: (1, 2)" in yml

    def test_yaml_dumps_non_serializable(self) -> None:
        """Test yaml_dumps serializes dicts with custom object values."""
        d = {"foo": Dummy()}
        yml = Utils.yaml_dumps(d)
        assert yml is not None
        assert "foo: DummyInstance" in yml

    def test_yaml_dumps_serialization_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test yaml_dumps returns None if yaml.dump raises an exception."""
        # Patch yaml.dump to simulate an exception
        monkeypatch.setattr(
            "yaml.dump", lambda *a, **kw: (_ for _ in ()).throw(Exception("fail"))
        )
        d = {"a": 1}
        assert Utils.yaml_dumps(d) is None

    def test_normalize_text_basic(self) -> None:
        """Test that normalize_text handles basic cases."""
        # Arrange
        input_text = "  This is a   test.   "
        expected_output = "Thisisatest"

        # Act
        result = Utils.normalize_text(input_text)

        # Assert
        assert result == expected_output

    def test_clean_context_match_and_remove(self) -> None:
        """Test that matching keys/values are removed."""
        # Arrange
        node_context = {"key1": "value", "key2": "another"}
        architype_context = {"key1": "value", "key2": "different"}
        ignore_keys: list[str] = []

        # Act
        result = Utils.clean_context(node_context, architype_context, ignore_keys)

        # Assert
        assert result == {"key2": "another"}

    def test_clean_context_remove_empty_values(self) -> None:
        """Test that empty values are removed."""
        # Arrange
        node_context: dict = {"key1": "", "key2": None, "key3": [], "key4": False}
        architype_context: dict = {}
        ignore_keys: list[str] = []

        # Act
        result = Utils.clean_context(node_context, architype_context, ignore_keys)

        # Assert
        assert result == {"key4": False}

    def test_clean_context_ignore_keys(self) -> None:
        """Test that keys in ignore_keys are removed."""
        # Arrange
        node_context = {"key1": "value", "key2": "another"}
        architype_context = {"key1": "different"}
        ignore_keys: list[str] = ["key1"]

        # Act
        result = Utils.clean_context(node_context, architype_context, ignore_keys)

        # Assert
        assert result == {"key2": "another"}

    def test_to_snake_case_basic(self) -> None:
        """Test that to_snake_case converts a title to snake case."""
        # Arrange
        input_title = "Test Title for Conversion"
        expected_output = "test_title_for_conversion"

        # Act
        result = Utils.to_snake_case(input_title)

        # Assert
        assert result == expected_output

    def test_to_snake_case_strip_non_ascii(self) -> None:
        """Test that to_snake_case strips non-ASCII characters when ascii_only is True."""
        # Arrange
        input_title = "Tést Tïtle wîth âccêntš"
        expected_output = "test_title_with_accents"

        # Act
        result = Utils.to_snake_case(input_title)

        # Assert
        assert result == expected_output
