"""Tests for the client widgets module."""

import yaml
from pytest_mock import MockerFixture

from jvcli.client.lib.widgets import (
    app_controls,
    app_header,
    app_update_action,
    dynamic_form,
    snake_to_title,
)


class TestClientWidgets:
    """Test the client widgets module."""

    def test_initialize_session_state_with_call_get_action(
        self, mocker: MockerFixture
    ) -> None:
        """Test initializing session state with call_get_action."""
        # Mock streamlit session state
        mock_session_state: dict = {}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit widgets
        mocker.patch("streamlit.header")
        mocker.patch("streamlit.text")
        mock_checkbox = mocker.patch("streamlit.checkbox")
        mock_checkbox.return_value = True

        # Mock call_get_action
        mock_get_action = mocker.patch("jvcli.client.lib.widgets.call_get_action")
        mock_get_action.return_value = {
            "_package": {"meta": {"title": "Test Action"}},
            "description": "Test description",
            "enabled": True,
        }

        # Test inputs
        agent_id = "test_agent"
        action_id = "test_action"
        info = {"config": {"action": "test_root"}}

        # Call function
        model_key, action = app_header(agent_id, action_id, info)

        # Verify call_get_action was called with correct params
        mock_get_action.assert_called_once_with(agent_id=agent_id, action_id=action_id)

        # Verify session state was initialized
        expected_key = f"model_{agent_id}_{action_id}"
        assert expected_key in mock_session_state
        assert mock_session_state[expected_key] == mock_get_action.return_value

    def test_basic_snake_case_conversion(self) -> None:
        """Test basic snake case conversion."""
        # Arrange
        input_str = "hello_world_test"
        expected = "Hello World Test"

        # Act
        result = snake_to_title(input_str)

        # Assert
        assert result == expected

    def test_render_short_string_input(self, mocker: MockerFixture) -> None:
        """Test rendering short string input."""
        # Mock streamlit session state
        mock_session_state = {
            "model_test_agent_test_action": {"short_string": "test value"}
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit text_input
        mock_text_input = mocker.patch("streamlit.text_input")
        mock_text_input.return_value = "test value"

        # Call function
        app_controls("test_agent", "test_action")

        # Verify text_input was called with correct params
        mock_text_input.assert_called_once_with(
            "Short String", value="test value", key="short_string"
        )

    def test_render_api_key_as_password_field(self, mocker: MockerFixture) -> None:
        """Test rendering API key as password field."""
        # Mock streamlit session state
        mock_session_state = {
            "model_test_agent_test_action": {
                "api_key": "secret_value"  # pragma: allowlist secret
            }
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit text_input
        mock_text_input = mocker.patch("streamlit.text_input")
        mock_text_input.return_value = "secret_value"

        # Call function
        app_controls("test_agent", "test_action")

        # Verify text_input was called with correct params for api_key
        mock_text_input.assert_called_once_with(
            "Api Key", value="secret_value", type="password", key="api_key"
        )

    def test_render_integer_input(self, mocker: MockerFixture) -> None:
        """Test rendering integer input."""
        # Mock streamlit session state
        mock_session_state = {"model_test_agent_test_action": {"integer_field": 42}}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit number_input
        mock_number_input = mocker.patch("streamlit.number_input")
        mock_number_input.return_value = 42

        # Call function
        app_controls("test_agent", "test_action")

        # Verify number_input was called with correct params
        mock_number_input.assert_called_once_with(
            "Integer Field", value=42, step=1, key="integer_field"
        )

    def test_render_float_input(self, mocker: MockerFixture) -> None:
        """Test rendering float input."""
        # Mock streamlit session state
        mock_session_state = {"model_test_agent_test_action": {"float_value": 3.14}}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit number_input
        mock_number_input = mocker.patch("streamlit.number_input")
        mock_number_input.return_value = 3.14

        # Call function
        app_controls("test_agent", "test_action")

        # Verify number_input was called with correct params
        mock_number_input.assert_called_once_with(
            "Float Value", value=3.14, step=0.01, key="float_value"
        )

    def test_render_boolean_checkbox(self, mocker: MockerFixture) -> None:
        """Test rendering boolean checkbox."""
        # Mock streamlit session state
        mock_session_state = {"model_test_agent_test_action": {"boolean_field": False}}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit checkbox
        mock_checkbox = mocker.patch("streamlit.checkbox")
        mock_checkbox.return_value = True

        # Call function
        app_controls("test_agent", "test_action")

        # Verify checkbox was called with correct params
        mock_checkbox.assert_called_once_with(
            "Boolean Field", value=False, key="boolean_field"
        )

    def test_render_list_input(self, mocker: MockerFixture) -> None:
        """Test rendering list input."""
        # Mock streamlit session state
        mock_session_state = {
            "model_test_agent_test_action": {"list_field": ["item1", "item2"]}
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit text_area
        mock_text_area = mocker.patch("streamlit.text_area")
        mock_text_area.return_value = yaml.dump(["item1", "item2"])

        # Call function
        app_controls("test_agent", "test_action")

        # Verify text_area was called with correct params
        mock_text_area.assert_called_once_with(
            "List Field (YAML format)",
            value=yaml.dump(["item1", "item2"]),
            key="list_field",
        )

        # Verify session state was updated correctly
        assert mock_session_state["model_test_agent_test_action"]["list_field"] == [
            "item1",
            "item2",
        ]

    def test_render_string_input(self, mocker: MockerFixture) -> None:
        """Test rendering string input."""
        # Mock streamlit session state
        mock_session_state = {
            "model_test_agent_test_action": {"string_field": "test string"}
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit text_input and text_area
        mock_text_input = mocker.patch("streamlit.text_input")
        mock_text_input.return_value = "test string"
        mock_text_area = mocker.patch("streamlit.text_area")
        mock_text_area.return_value = "test string"

        # Call function
        app_controls("test_agent", "test_action")

        # Verify text_input was called for short strings
        mock_text_input.assert_called_once_with(
            "String Field", value="test string", key="string_field"
        )

        # Update session state for a long string
        mock_session_state["model_test_agent_test_action"]["string_field"] = "a" * 101

        # Call function again
        app_controls("test_agent", "test_action")

        # Verify text_area was called for long strings
        mock_text_area.assert_called_once_with(
            "String Field", value="a" * 101, key="string_field"
        )

    def test_render_dict_input(self, mocker: MockerFixture) -> None:
        """Test rendering dictionary input."""
        # Mock streamlit session state
        mock_session_state = {
            "model_test_agent_test_action": {
                "config": {"key1": "value1", "key2": "value2"}
            }
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit text_area
        mock_text_area = mocker.patch("streamlit.text_area")
        mock_text_area.return_value = yaml.dump({"key1": "value1", "key2": "value2"})

        # Call function
        app_controls("test_agent", "test_action")

        # Verify text_area was called with correct params
        mock_text_area.assert_called_once_with(
            "Config (YAML format)",
            value=yaml.dump({"key1": "value1", "key2": "value2"}),
            key="config",
        )

        # Verify session state was updated correctly
        assert mock_session_state["model_test_agent_test_action"]["config"] == {
            "key1": "value1",
            "key2": "value2",
        }

    def test_render_unsupported_type(self, mocker: MockerFixture) -> None:
        """Test rendering unsupported type."""
        # Mock streamlit session state
        mock_session_state = {
            "model_test_agent_test_action": {
                "unsupported_field": object()  # Using an object to simulate unsupported type
            }
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit write
        mock_write = mocker.patch("streamlit.write")

        # Call function
        app_controls("test_agent", "test_action")

        # Verify write was called with correct message for unsupported type
        mock_write.assert_called_once_with(
            "Unsupported type for unsupported_field: <class 'object'>"
        )

    def test_yaml_list_value_error(self, mocker: MockerFixture) -> None:
        """Test handling YAML list value error."""
        # Mock streamlit session state
        mock_session_state = {"model_test_agent_test_action": {"list_field": [1, 2, 3]}}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit text_area and error
        mock_text_area = mocker.patch("streamlit.text_area")
        mock_text_area.return_value = "not a list"
        mock_error = mocker.patch("streamlit.error")

        # Call function
        app_controls("test_agent", "test_action")

        # Verify error was called with correct message
        mock_error.assert_called_once_with(
            "Error parsing YAML for list_field: The provided YAML does not produce a list."
        )

    def test_render_dict_field_with_yaml_error(self, mocker: MockerFixture) -> None:
        """Test rendering dictionary field with YAML error."""
        # Mock streamlit session state
        mock_session_state = {
            "model_test_agent_test_action": {
                "config": {"key1": "value1", "key2": "value2"}
            }
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit text_area and error
        mock_text_area = mocker.patch("streamlit.text_area")
        mock_text_area.return_value = "invalid_yaml: ["
        mock_error = mocker.patch("streamlit.error")

        # Call function
        app_controls("test_agent", "test_action")

        # Verify text_area was called with correct params
        mock_text_area.assert_called_once_with(
            "Config (YAML format)", value=mocker.ANY, key="config"
        )

        # Verify error was called due to YAML parsing error
        mock_error.assert_called_once()

    def test_update_button_success_message(self, mocker: MockerFixture) -> None:
        """Test displaying success message on update button click."""
        # Mock streamlit session state
        mock_session_state = {"model_test_agent_test_action": {"some_data": "test"}}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit widgets
        mock_divider = mocker.patch("streamlit.divider")
        mock_button = mocker.patch("streamlit.button")
        mock_button.return_value = True
        mock_success = mocker.patch("streamlit.success")
        mock_error = mocker.patch("streamlit.error")

        # Mock call_update_action
        mock_update_action = mocker.patch("jvcli.client.lib.widgets.call_update_action")
        mock_update_action.return_value = {"id": "test_action"}

        # Test inputs
        agent_id = "test_agent"
        action_id = "test_action"

        # Call function
        app_update_action(agent_id, action_id)

        # Verify interactions
        mock_divider.assert_called_once()
        mock_button.assert_called_once_with("Update")
        mock_update_action.assert_called_once_with(
            agent_id=agent_id,
            action_id=action_id,
            action_data=mock_session_state[f"model_{agent_id}_{action_id}"],
        )
        mock_success.assert_called_once_with("Changes saved")
        mock_error.assert_not_called()

    def test_unable_to_save_changes(self, mocker: MockerFixture) -> None:
        """Test handling unable to save changes error."""
        # Mock streamlit session state
        mock_session_state = {
            "model_test_agent_test_action": {"some_key": "some_value"}
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit button and error
        mock_button = mocker.patch("streamlit.button")
        mock_button.return_value = True
        mock_error = mocker.patch("streamlit.error")

        # Mock call_update_action to return an empty result
        mock_update_action = mocker.patch("jvcli.client.lib.widgets.call_update_action")
        mock_update_action.return_value = {}

        # Call function
        app_update_action("test_agent", "test_action")

        # Verify error was called with correct message
        mock_error.assert_called_once_with("Unable to save changes")

    def test_init_empty_form(self, mocker: MockerFixture) -> None:
        """Test initializing empty form."""
        # Mock streamlit session state
        mock_session_state: dict = {}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit widgets
        mocker.patch("streamlit.columns")
        mocker.patch("streamlit.container")
        mocker.patch("streamlit.button")
        mocker.patch("streamlit.divider")

        # Test inputs
        field_definitions = [
            {"name": "field1", "type": "text"},
            {"name": "field2", "type": "number"},
        ]

        # Call function
        result = dynamic_form(field_definitions)

        # Verify session state was initialized correctly
        assert "dynamic_form" in mock_session_state
        assert len(mock_session_state["dynamic_form"]) == 1
        assert mock_session_state["dynamic_form"][0]["id"] == 0
        assert len(result) == 1

    def test_dynamic_form_initial_data_not_none(self, mocker: MockerFixture) -> None:
        """Test dynamic form with initial data not None."""
        # Mock streamlit session state
        mock_session_state: dict = {}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Define field definitions and initial data
        field_definitions = [
            {"name": "field1", "type": "text"},
            {"name": "field2", "type": "number"},
        ]
        initial_data = [
            {"field1": "value1", "field2": 10},
            {"field1": "value2", "field2": 20},
        ]

        # Call the dynamic_form function
        result = dynamic_form(field_definitions, initial_data)

        # Verify session state was initialized with initial data
        expected_session_state = [
            {"id": 0, "fields": {"field1": "value1", "field2": 10}},
            {"id": 1, "fields": {"field1": "value2", "field2": 20}},
        ]
        assert mock_session_state["dynamic_form"] == expected_session_state

        # Verify the result matches the expected output (only fields)
        expected_result = [
            {"field1": "value1", "field2": 10},
            {"field1": "value2", "field2": 20},
        ]
        assert result == expected_result

    def test_select_field_rendering(self, mocker: MockerFixture) -> None:
        """Test rendering select field."""
        # Mock streamlit session state
        mock_session_state: dict = {}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit selectbox
        mock_selectbox = mocker.patch("jvcli.client.lib.widgets.st.selectbox")
        mock_selectbox.return_value = "option1"

        # Define field definitions and initial data
        field_definitions = [
            {
                "name": "select_field",
                "type": "select",
                "options": ["option1", "option2"],
            }
        ]
        initial_data = [{"select_field": "option1"}]

        # Call the dynamic_form function
        dynamic_form(field_definitions, initial_data)

        # Verify the session state is updated correctly
        assert (
            mock_session_state["dynamic_form"][0]["fields"]["select_field"] == "option1"
        )
