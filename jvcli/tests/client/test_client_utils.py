"""Test the client utility functions."""

import base64
import json
from io import BytesIO
from pathlib import Path

import pytest
import yaml
from PIL import Image
from pytest_mock import MockerFixture

from jvcli.client.lib.utils import (
    JIVAS_BASE_URL,
    LongStringDumper,
    call_action_walker_exec,
    call_api,
    call_get_action,
    call_get_agent,
    call_healthcheck,
    call_import_agent,
    call_list_actions,
    call_list_agents,
    call_update_action,
    call_update_agent,
    decode_base64_image,
    jac_yaml_dumper,
    load_function,
)


class TestClientUtils:
    """Test the client utility functions."""

    def test_load_existing_function(self, tmp_path: Path) -> None:
        """Test loading an existing function from a file."""
        # Create a temporary Python file with a test function
        file_content = """
def test_func(x, y):
    return x + y
"""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(file_content)

        # Load the function
        loaded_func = load_function(str(test_file), "test_func")

        # Test the loaded function
        result = loaded_func(1, 2)
        assert result == 3

        # Test with kwargs
        loaded_func_with_kwargs = load_function(str(test_file), "test_func", x=10)
        result_with_kwargs = loaded_func_with_kwargs(y=5)
        assert result_with_kwargs == 15

    def test_load_function_file_not_found(self, mocker: MockerFixture) -> None:
        """Test load_function raises FileNotFoundError when file path does not exist."""
        # Arrange
        non_existent_file_path = "non_existent_file.py"
        function_name = "dummy_function"

        # Act & Assert
        with pytest.raises(FileNotFoundError) as excinfo:
            load_function(non_existent_file_path, function_name)

        assert str(excinfo.value) == f"No file found at {non_existent_file_path}"

    def test_load_function_specification_not_loaded(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test load_function when module specification cannot be loaded."""
        # Create a temporary Python file with a test function
        file_content = """
def dummy_function():
    pass
"""
        test_file = tmp_path / "dummy_path.py"
        test_file.write_text(file_content)

        # Mock spec_from_file_location to return None
        mocker.patch(
            "jvcli.client.lib.utils.spec_from_file_location", return_value=None
        )

        # Attempt to load function and expect ImportError
        with pytest.raises(
            ImportError, match="Could not load specification for module dummy_path"
        ):
            load_function(str(test_file), "dummy_function")

    def test_import_error_when_loading_module(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test ImportError is raised when module cannot be loaded."""
        # Create a temporary Python file with a test function
        file_content = """
def dummy_function():
    pass
"""
        test_file = tmp_path / "dummy_path.py"
        test_file.write_text(file_content)

        # Mock spec_from_file_location to return None
        mock_spec = mocker.MagicMock()
        mock_spec.loader = None
        mocker.patch(
            "jvcli.client.lib.utils.spec_from_file_location", return_value=mock_spec
        )

        # Mock module_from_spec
        mocker.patch("jvcli.client.lib.utils.module_from_spec", return_value=None)

        # Attempt to load function and expect ImportError
        with pytest.raises(ImportError, match="Could not load module dummy_path"):
            load_function(str(test_file), "dummy_function")

    def test_load_function_not_found(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test load_function raises AttributeError when function does not exist."""
        # Create a temporary Python file with a test function
        file_content = """
def dummy_function():
    pass
"""

        test_file = tmp_path / "dummy_path.py"
        test_file.write_text(file_content)

        # Attempt to load function and expect AttributeError
        with pytest.raises(
            AttributeError,
            match=f"Function 'dummy_function2' not found in {str(test_file)}",
        ):
            load_function(str(test_file), "dummy_function2")

    def test_call_list_agents_returns_non_empty_list(
        self, mocker: MockerFixture
    ) -> None:
        """Test call_list_agents returns a non-empty list."""
        # Mock call_api to simulate API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {
            "reports": [
                {"id": "agent_1", "name": "Agent One"},
                {"id": "agent_2", "name": "Agent Two"},
            ]
        }

        # Call the function
        result = call_list_agents()

        # Assert that the result is a non-empty list with correct structure
        assert len(result) > 0
        assert result == [
            {"id": "agent_1", "label": "Agent One"},
            {"id": "agent_2", "label": "Agent Two"},
        ]

    def test_call_list_agents_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_list_agents returns empty list on 401 status code."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to simulate a 401 Unauthorized response
        mock_post = mocker.patch("requests.post")
        mock_post.return_value.status_code = 401

        # Call the function
        result = call_list_agents()

        # Assert that the result is an empty list
        assert result == []

    def test_valid_token_returns_actions(self, mocker: MockerFixture) -> None:
        """Test call_list_actions returns actions when token is valid."""

        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {
            "reports": [["action1", "action2"]]
        }

        # Call function
        result = call_list_actions(
            "test_agent", headers={"Authorization": "Bearer test_token"}
        )

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            "walker/list_actions",
            headers={"Authorization": "Bearer test_token"},
            json_data={"agent_id": "test_agent"},
        )

        # Verify result
        assert result == ["action1", "action2"]

    def test_call_list_actions_empty_result(self, mocker: MockerFixture) -> None:
        """Test call_list_actions returns empty list when no actions are found."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {"reports": []}

        # Call the function
        result = call_list_actions("test_agent")

        # Assert that the result is an empty list
        assert len(result) <= 0

    def test_call_list_actions_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_list_actions returns empty list on 401 status code."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to simulate a 401 Unauthorized response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 401

        # Call the function
        result = call_list_actions("test_agent")

        # Assert that the result is an empty list
        assert result == []

    def test_call_list_actions_exception_handling(self, mocker: MockerFixture) -> None:
        """Test call_list_actions handles exceptions and returns empty list."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to raise an exception
        mocker.patch("requests.post", side_effect=Exception("Test Exception"))

        # Call the function
        result = call_list_actions("test_agent")

        # Verify that the exception was handled and an empty list is returned
        assert result == []

    def test_valid_token_returns_action_data(self, mocker: MockerFixture) -> None:
        """Test call_get_action returns action data when token is valid."""

        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {
            "reports": [{"action": "test_action"}]
        }

        # Call function
        result = call_get_action(
            "test_agent", "test_action", headers={"Authorization": "Bearer test_token"}
        )

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            "walker/get_action",
            headers={"Authorization": "Bearer test_token"},
            json_data={"agent_id": "test_agent", "action_id": "test_action"},
        )

        # Verify result
        assert result == {"action": "test_action"}

    def test_call_get_action_empty_result(self, mocker: MockerFixture) -> None:
        """Test call_get_action returns empty list when no action is found."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to simulate API response with empty reports
        mock_post = mocker.patch("requests.post")
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"reports": []}

        # Call the function
        result = call_get_action("test_agent_id", "test_action_id")

        # Assert that the result is an empty list
        assert len(result) <= 0

    def test_call_get_action_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_get_action returns empty list on 401 status code."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to simulate a 401 Unauthorized response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 401

        # Call the function
        result = call_get_action("test_agent_id", "test_action_id")

        # Assert that the result is an empty dict
        assert result == {}

    def test_call_api_exception_handling(self, mocker: MockerFixture) -> None:
        """Test call_api handles exceptions and returns None."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.request to raise an exception
        mocker.patch("requests.request", side_effect=Exception("Test Exception"))

        # Call the function
        result = call_api(
            endpoint="test_endpoint",
            method="POST",
            headers={"Custom-Header": "test-value"},
            json_data={"key": "value"},
        )

        # Verify that the exception was handled and None is returned
        assert result is None

    def test_valid_token_returns_first_report(self, mocker: MockerFixture) -> None:
        """Test call_update_action returns first report when token is valid."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"reports": [{"result": "test_result"}]}
        mock_call_api = mocker.patch(
            "jvcli.client.lib.utils.call_api", return_value=mock_response
        )

        # Call function
        result = call_update_action(
            "test_agent",
            "test_action",
            {"test": "data"},
            headers={"Authorization": "Bearer test_token"},
        )

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            "walker/update_action",
            headers={"Authorization": "Bearer test_token"},
            json_data={
                "agent_id": "test_agent",
                "action_id": "test_action",
                "action_data": {"test": "data"},
            },
        )

        # Verify result
        assert result == {"result": "test_result"}

    def test_call_update_action_empty_result(self, mocker: MockerFixture) -> None:
        """Test call_update_action returns empty dict when no report is found."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response with empty reports
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {"reports": []}

        # Call the function
        result = call_update_action("test_agent_id", "test_action_id", {"key": "value"})

        # Assert that the result is an empty dictionary
        assert result == {}

    def test_call_update_action_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_update_action returns empty dict on 401 status code."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to simulate a 401 Unauthorized response
        mock_post = mocker.patch("requests.post")
        mock_post.return_value.status_code = 401

        # Call the function
        result = call_update_action("test_agent_id", "test_action_id", {"key": "value"})

        # Assert that the result is an empty dict
        assert result == {}

    def test_call_update_action_exception_handling(self, mocker: MockerFixture) -> None:
        """Test call_update_action handles exceptions and returns empty dict."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to raise an exception
        mocker.patch("requests.post", side_effect=Exception("Test Exception"))

        # Call the function
        result = call_update_action("test_agent_id", "test_action_id", {"key": "value"})

        # Verify that the exception was handled and an empty dictionary is returned
        assert result == {}

    def test_valid_walker_execution(self, mocker: MockerFixture) -> None:
        """Test call_action_walker_exec returns results when token is valid."""
        # Mock get_user_info to return valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock successful API response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["result1", "result2"]
        mock_call_api = mocker.patch(
            "jvcli.client.lib.utils.call_api", return_value=mock_response
        )

        # Test parameters
        agent_id = "test_agent"
        action = "test_module"
        walker = "test_walker"
        args = {"arg1": "value1"}
        files = [("file1.txt", b"content", "text/plain")]
        headers = {"Authorization": "Bearer test_token"}

        # Call function
        result = call_action_walker_exec(agent_id, action, walker, args, files, headers)

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            f"{JIVAS_BASE_URL}/action/walker",
            headers=headers,
            data={
                "agent_id": agent_id,
                "module_root": action,
                "walker": walker,
                "args": json.dumps(args),
            },
            files=[("attachments", ("file1.txt", b"content", "text/plain"))],
        )

        # Verify result
        assert result == ["result1", "result2"]

    def test_call_action_walker_exec_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_action_walker_exec returns empty list on 401 status code."""
        # Mock get_user_info to return valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate a 401 Unauthorized response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 401

        # Test parameters
        agent_id = "test_agent"
        action = "test_module"
        walker = "test_walker"
        args = {"arg1": "value1"}
        files = [("file1.txt", b"content", "text/plain")]
        headers = {"Authorization": "Bearer test_token"}

        # Call function
        result = call_action_walker_exec(agent_id, action, walker, args, files, headers)

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            f"{JIVAS_BASE_URL}/action/walker",
            headers=headers,
            data={
                "agent_id": agent_id,
                "module_root": action,
                "walker": walker,
                "args": json.dumps(args),
            },
            files=[("attachments", ("file1.txt", b"content", "text/plain"))],
        )

        # Verify result
        assert result == []

    def test_successful_import_agent_call(self, mocker: MockerFixture) -> None:
        """Test call_import_agent returns agents when API call is successful."""
        # Mock get_user_info to return valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate a successful API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {
            "reports": [["agent1", "agent2"]]
        }

        # Test parameters
        descriptor = "test_descriptor"
        headers = {"Custom-Header": "test-value"}

        # Call the function
        result = call_import_agent(descriptor, headers)

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            "walker/import_agent",
            headers=headers,
            json_data={"descriptor": descriptor},
        )

        # Verify result
        assert result == ["agent1", "agent2"]

    def test_call_import_agent_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_import_agent returns empty list on 401 status code."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to simulate a 401 Unauthorized response
        mock_post = mocker.patch("requests.post")
        mock_post.return_value.status_code = 401

        # Call the function
        result = call_import_agent("test_descriptor")

        # Assert that the result is an empty list
        assert result == []

    def test_call_import_agent_exception_handling(self, mocker: MockerFixture) -> None:
        """Test call_import_agent handles exceptions and returns empty list."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.post to raise an exception
        mocker.patch("requests.post", side_effect=Exception("Test Exception"))

        # Call the function
        result = call_import_agent("test_descriptor")

        # Verify that the exception was handled and an empty list is returned
        assert result == []

    def test_decode_valid_base64_to_image(self) -> None:
        """Test decoding a valid base64 string to an image."""
        # Arrange
        # Create a small test image and convert to base64
        test_image = Image.new("RGB", (10, 10), color="red")
        buffer = BytesIO()
        test_image.save(buffer, format="PNG")
        base64_string = base64.b64encode(buffer.getvalue()).decode()

        # Act
        result = decode_base64_image(base64_string)

        # Assert
        assert isinstance(result, Image.Image)
        assert result.size == (10, 10)
        assert result.mode == "RGB"
        # Verify pixel color
        assert result.getpixel((0, 0)) == (255, 0, 0)  # Red color in RGB

    def test_short_string_representation(self) -> None:
        """Test that short strings are represented correctly."""
        data = {"message": "Short string"}
        yaml_output = yaml.dump(data, Dumper=LongStringDumper).strip()

        expected_output = "message: Short string"
        assert yaml_output == expected_output

    def test_long_string_representation(self) -> None:
        """Test that long strings use block style (| or |-)."""
        long_text = "This is a very long string " * 10  # More than 150 chars
        data = {"message": long_text}
        yaml_output = yaml.dump(data, Dumper=LongStringDumper).strip()

        # Ensure it starts with block style and contains the text
        assert yaml_output.startswith("message: |")  # YAML block style
        assert "This is a very long string" in yaml_output  # Ensure text is present
        assert yaml_output.endswith(
            "This is a very long string"
        )  # Ensure it ends correctly

    def test_multiline_string_representation(self) -> None:
        """Test that multiline strings use block style."""
        multiline_text = "Line 1\nLine 2\nLine 3"
        data = {"message": multiline_text}
        yaml_output = yaml.dump(data, Dumper=LongStringDumper).strip()

        # Ensure block style is used
        assert yaml_output.startswith("message: |")

        # Normalize indentation and compare content
        expected_content = "\n".join(
            line.strip() for line in multiline_text.split("\n")
        )
        yaml_content = "\n".join(line.strip() for line in yaml_output.split("\n")[1:])
        assert yaml_content == expected_content

    def test_newline_escapes_are_formatted(self) -> None:
        """Test that escape sequences are properly converted."""
        text_with_escapes = "Line 1\nLine 2\nLine 3\n"
        data = {"message": text_with_escapes}
        yaml_output = yaml.dump(data, Dumper=LongStringDumper).strip()

        # Ensure block style (|) is used
        assert yaml_output.startswith("message: |")

        # Normalize indentation and compare
        expected_content = "\n".join(
            line.strip() for line in text_with_escapes.split("\n") if line
        )
        yaml_lines = yaml_output.split("\n")[1:]  # Skip "message: |"
        yaml_content = "\n".join(line.strip() for line in yaml_lines if line)

        assert yaml_content == expected_content

    def test_basic_yaml_dumping(self) -> None:
        """Test that basic data is correctly dumped to YAML."""
        data = {"key": "value"}
        yaml_output = jac_yaml_dumper(data)

        assert yaml_output.strip() == "key: value"

    def test_multiline_string_block_style(self) -> None:
        """Test that multiline strings use block style (|)."""
        multiline_text = "Line 1\nLine 2\nLine 3"
        data = {"message": multiline_text}
        yaml_output = jac_yaml_dumper(data).strip()

        assert yaml_output.startswith("message: |")

        # Normalize indentation and compare
        expected_content = "\n".join(
            line.strip() for line in multiline_text.split("\n")
        )
        yaml_lines = yaml_output.split("\n")[1:]  # Skip "message: |"
        yaml_content = "\n".join(line.strip() for line in yaml_lines)

        assert yaml_content == expected_content

    def test_long_string_block_style(self) -> None:
        """Test that long strings (over 150 characters) are dumped in block style."""
        long_text = "This is a very long string " * 10  # 240+ chars
        data = {"long_message": long_text}
        yaml_output = jac_yaml_dumper(data).strip()

        assert yaml_output.startswith("long_message: |")

    def test_unicode_handling(self) -> None:
        """Test that unicode characters are preserved."""
        unicode_text = "你好, мир, hello"
        data = {"greeting": unicode_text}
        yaml_output = jac_yaml_dumper(data, allow_unicode=True).strip()

        assert "greeting: 你好, мир, hello" in yaml_output

    def test_sort_keys_option(self) -> None:
        """Test that keys are sorted when sort_keys=True."""
        data = {"b_key": "value2", "a_key": "value1"}
        yaml_output = jac_yaml_dumper(data, sort_keys=True).strip()

        assert yaml_output.startswith("a_key: value1\nb_key: value2")

    def test_flow_style(self) -> None:
        """Test that default_flow_style=True results in inline formatting."""
        data = {"items": ["apple", "banana", "cherry"]}
        yaml_output = jac_yaml_dumper(data, default_flow_style=True).strip()

        # Adjust expectation to match PyYAML's default behavior
        assert yaml_output == "{items: [apple, banana, cherry]}"

    def test_call_healthcheck_success_with_warning(self, mocker: MockerFixture) -> None:
        """Test call_healthcheck returns payload with warning and no error."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {
            "reports": [
                {
                    "status": 200,
                    "message": "passed_message",
                    "trace": {
                        "item_label": {
                            "status": "true_value",
                            "message": "warning_message",
                            "severity": "warning",
                        }
                    },
                }
            ]
        }

        # Call the function
        result = call_healthcheck(
            "test_agent_id", headers={"Authorization": "Bearer test_token"}
        )

        # Assert the result
        assert result == {
            "status": 200,
            "message": "passed_message",
            "trace": {
                "item_label": {
                    "status": "true_value",
                    "message": "warning_message",
                    "severity": "warning",
                }
            },
        }

    def test_call_healthcheck_failure_with_error(self, mocker: MockerFixture) -> None:
        """Test call_healthcheck returns payload with error."""

        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 503
        mock_call_api.return_value.json.return_value = {
            "reports": [
                {
                    "status": 503,
                    "message": "Agent healthcheck failed.",
                    "trace": {
                        "jpr_api_key": {
                            "status": True,
                            "message": "JPR API key not set. Your agent will not be able to access private JIVAS package repo items.",
                            "severity": "warning",
                        },
                        "LangChainModelAction": {
                            "status": False,
                            "message": "Agent healthcheck failed on LangChainModelAction. Inspect configuration and try again.",
                            "severity": "error",
                        },
                    },
                }
            ]
        }

        # Call the function
        result = call_healthcheck(
            "test_agent_id", headers={"Authorization": "Bearer test_token"}
        )

        # Assert the result
        assert result == {
            "status": 503,
            "message": "Agent healthcheck failed.",
            "trace": {
                "jpr_api_key": {
                    "status": True,
                    "message": "JPR API key not set. Your agent will not be able to access private JIVAS package repo items.",
                    "severity": "warning",
                },
                "LangChainModelAction": {
                    "status": False,
                    "message": "Agent healthcheck failed on LangChainModelAction. Inspect configuration and try again.",
                    "severity": "error",
                },
            },
        }

    def test_call_healthcheck_success_no_warning_or_error(
        self, mocker: MockerFixture
    ) -> None:
        """Test call_healthcheck returns empty payload when no warnings or errors."""

        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {"reports": []}

        # Call the function
        result = call_healthcheck(
            "test_agent_id", headers={"Authorization": "Bearer test_token"}
        )

        # Assert the result
        assert result == {}

    def test_call_healthcheck_incomplete_healthcheck(
        self, mocker: MockerFixture
    ) -> None:
        """Test call_healthcheck returns incomplete healthcheck payload."""

        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 501
        mock_call_api.return_value.json.return_value = {
            "reports": [
                {
                    "status": 501,
                    "message": "Agent healthcheck incomplete.",
                    "trace": {},
                }
            ]
        }

        # Call the function
        result = call_healthcheck(
            "test_agent_id", headers={"Authorization": "Bearer test_token"}
        )

        # Assert the result
        assert result == {
            "status": 501,
            "message": "Agent healthcheck incomplete.",
            "trace": {},
        }

    def test_call_api_success(self, mocker: MockerFixture) -> None:
        """Test call_api returns response when request is successful."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock streamlit session state using patch
        mock_session_state = mocker.MagicMock()
        mocker.patch("jvcli.client.lib.utils.st.session_state", mock_session_state)

        # Mock requests.request for successful response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_request = mocker.patch("requests.request", return_value=mock_response)

        # Test parameters
        endpoint = "test_endpoint"
        method = "POST"
        headers = {"Custom-Header": "test-value"}
        json_data = {"key": "value"}
        files = [("file1.txt", b"content", "text/plain")]
        data = {"form_key": "form_value"}

        # Call function
        result = call_api(
            endpoint=endpoint,
            method=method,
            headers=headers,
            json_data=json_data,
            files=files,
            data=data,
            timeout=10,
        )

        # Verify requests.request was called with correct parameters
        mock_request.assert_called_once_with(
            method=method,
            url=f"{JIVAS_BASE_URL}/{endpoint}",
            headers={
                "Custom-Header": "test-value",
                "Authorization": "Bearer test_token",
            },
            json=json_data,
            files=files,
            data=data,
            timeout=10,
        )

        # Verify result
        assert result == mock_response
        assert result.status_code == 200
        assert result.json() == {"test": "data"}

    def test_call_api_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_api returns None when response is 401 Unauthorized."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock streamlit session state as an object with attributes, not a dictionary
        mock_session_state = mocker.MagicMock()
        mock_session_state.EXPIRATION = ""
        mocker.patch("jvcli.client.lib.utils.st.session_state", mock_session_state)

        # Mock requests.request for 401 response
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mocker.patch("requests.request", return_value=mock_response)

        # Call function
        result = call_api("test_endpoint")

        # Verify session state was updated (as an attribute, not a dict key)
        assert mock_session_state.EXPIRATION == ""

        # Verify result
        assert result is None

    def test_call_api_no_token(self, mocker: MockerFixture) -> None:
        """Test call_api returns None when no token is available."""
        # Mock get_user_info to return no token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "",
                "expiration": "",
            },
        )

        # Mock requests.request
        mock_request = mocker.patch("requests.request")

        # Call function
        result = call_api("test_endpoint")

        # Verify requests.request was not called
        mock_request.assert_not_called()

        # Verify result
        assert result is None

    def test_call_api_with_absolute_url(self, mocker: MockerFixture) -> None:
        """Test call_api handles absolute URLs correctly."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock requests.request
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_request = mocker.patch("requests.request", return_value=mock_response)

        # Use an absolute URL
        absolute_url = "https://example.com/api/resource"

        # Call function
        call_api(endpoint=absolute_url)

        # Verify the URL was not modified
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        assert call_args["url"] == absolute_url

    def test_call_get_agent_success(self, mocker: MockerFixture) -> None:
        """Test call_get_agent returns agent details when API call is successful."""
        # Mock get_user_info to return valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate a successful API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {
            "reports": [
                {
                    "id": "test_agent_id",
                    "name": "Test Agent",
                    "description": "A test agent",
                    "config": {"key": "value"},
                }
            ]
        }

        # Test parameters
        agent_id = "test_agent_id"
        headers = {"Custom-Header": "test-value"}

        # Call the function
        result = call_get_agent(agent_id, headers)

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            "walker/get_agent",
            headers=headers,
            json_data={"agent_id": agent_id},
        )

        # Verify result
        assert result == {
            "id": "test_agent_id",
            "name": "Test Agent",
            "description": "A test agent",
            "config": {"key": "value"},
        }

    def test_call_get_agent_empty_result(self, mocker: MockerFixture) -> None:
        """Test call_get_agent returns empty dict when no agent is found."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response with empty reports
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {"reports": []}

        # Call the function
        result = call_get_agent("test_agent_id")

        # Assert that the result is an empty dictionary
        assert result == {}

    def test_call_get_agent_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_get_agent returns empty dict on 401 status code."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock streamlit session state as an object with attributes
        mock_session_state = mocker.MagicMock()
        mock_session_state.EXPIRATION = ""
        mocker.patch("jvcli.client.lib.utils.st.session_state", mock_session_state)

        # Mock call_api to return None (which happens on 401)
        mocker.patch("jvcli.client.lib.utils.call_api", return_value=None)

        # Call the function
        result = call_get_agent("test_agent_id")

        # Assert that the result is an empty dict
        assert result == {}

    def test_call_update_agent_success(self, mocker: MockerFixture) -> None:
        """Test call_update_agent returns updated agent data when API call succeeds."""
        # Mock get_user_info to return valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate a successful API response
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {
            "reports": [
                {
                    "id": "test_agent_id",
                    "name": "Updated Agent",
                    "description": "An updated test agent",
                    "config": {"updated_key": "updated_value"},
                }
            ]
        }

        # Test parameters
        agent_id = "test_agent_id"
        agent_data = {
            "name": "Updated Agent",
            "description": "An updated test agent",
            "config": {"updated_key": "updated_value"},
        }
        headers = {"Custom-Header": "test-value"}

        # Call the function
        result = call_update_agent(agent_id, agent_data, headers)

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            "walker/update_agent",
            headers=headers,
            json_data={"agent_id": agent_id, "agent_data": agent_data},
        )

        # Verify result
        assert result == {
            "id": "test_agent_id",
            "name": "Updated Agent",
            "description": "An updated test agent",
            "config": {"updated_key": "updated_value"},
        }

    def test_call_update_agent_empty_result(self, mocker: MockerFixture) -> None:
        """Test call_update_agent returns empty dict when API returns empty reports."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock call_api to simulate API response with empty reports
        mock_call_api = mocker.patch("jvcli.client.lib.utils.call_api")
        mock_call_api.return_value.status_code = 200
        mock_call_api.return_value.json.return_value = {"reports": []}

        # Test parameters
        agent_id = "test_agent_id"
        agent_data = {"name": "Updated Agent"}

        # Call the function
        result = call_update_agent(agent_id, agent_data)

        # Verify call_api was called with correct parameters
        mock_call_api.assert_called_once_with(
            "walker/update_agent",
            headers=None,
            json_data={"agent_id": agent_id, "agent_data": agent_data},
        )

        # Assert that the result is an empty dictionary
        assert result == {}

    def test_call_update_agent_unauthorized(self, mocker: MockerFixture) -> None:
        """Test call_update_agent returns empty dict on 401 status code."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.lib.utils.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock streamlit session state as an object with attributes
        mock_session_state = mocker.MagicMock()
        mock_session_state.EXPIRATION = ""
        mocker.patch("jvcli.client.lib.utils.st.session_state", mock_session_state)

        # Mock call_api to return None (which happens on 401)
        mocker.patch("jvcli.client.lib.utils.call_api", return_value=None)

        # Test parameters
        agent_id = "test_agent_id"
        agent_data = {"name": "Updated Agent"}

        # Call the function
        result = call_update_agent(agent_id, agent_data)

        # Assert that the result is an empty dict
        assert result == {}
