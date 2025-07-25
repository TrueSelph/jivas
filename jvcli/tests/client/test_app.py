"""Test cases for the client app.py module."""

import os
from pathlib import Path

from click.testing import CliRunner
from pytest_mock import MockerFixture
from streamlit.testing.v1 import AppTest

from jvcli.client.lib.page import Page
from jvcli.commands.client import launch


class TestClientApp:
    """Test cases for the client command app.py."""

    def test_launch_client_default_port(self, mocker: MockerFixture) -> None:
        """Test launching client with default port."""
        # Mock subprocess.call
        mock_call = mocker.patch("subprocess.call")

        # Create CLI runner
        runner = CliRunner()

        # Run the command
        result = runner.invoke(launch)

        # Verify the command executed successfully
        assert result.exit_code == 0

        mock_call.assert_called_once()

    def test_client_init_login_form(self, mocker: MockerFixture) -> None:
        """Test init render of client app with login form."""

        app_test = AppTest.from_file(
            Path(__file__)
            .resolve()
            .parent.parent.parent.joinpath("jvcli")
            .joinpath("client")
            .joinpath("app.py")
            .resolve()
            .__str__()
        )

        app_test.run()

        assert app_test.header[0].body == "Login"

    def test_client_login(self, mocker: MockerFixture) -> None:
        """Test login form submission and redirection to dashboard."""

        app_test = AppTest.from_file(
            Path(__file__)
            .resolve()
            .parent.parent.parent.joinpath("jvcli")
            .joinpath("client")
            .joinpath("app.py")
            .resolve()
            .__str__()
        )

        # Mock post request
        mocker_login = mocker.patch("jvcli.client.app.requests.post")
        mocker_login.return_value.status_code = 200
        mocker_login.return_value.json.return_value = {
            "user": {"root_id": "root_id", "expiration": "expiration"},
            "token": "token",
        }

        # Mock list agents
        mock_agents = mocker.patch("jvcli.client.lib.utils.call_list_agents")
        mock_agents.return_value = [{"id": "test_agent_id", "label": "test_agent_name"}]

        # Mock list actions
        mock_actions = mocker.patch("jvcli.client.lib.utils.call_list_actions")
        mock_actions.return_value = [
            {
                "id": "test_action_id",
                "name": "test_action_name",
                "_package": {
                    "config": {
                        "path": os.path.join(os.path.dirname(__file__), "../fixtures")
                    }
                },
            }
        ]

        # Mock query params
        query_params = {"agent": "test_agent_id"}
        mocker.patch("jvcli.client.app.st.query_params", query_params)

        app_test.run()

        app_test.text_input[0].input("admin@test.com").run()
        app_test.text_input[1].input("password").run()
        app_test.button[0].click().run()

        assert app_test.session_state["ROOT_ID"] == "root_id"
        assert app_test.session_state["TOKEN"] == "token"
        assert app_test.session_state["EXPIRATION"] == "expiration"
        assert app_test.session_state["streamlit-router-endpoint"] == "dashboard"

    def test_client_login_form_development_env(self, mocker: MockerFixture) -> None:
        """Test login form submission in development environment."""

        # Set environment variables for development
        os.environ["JIVAS_ENVIRONMENT"] = "development"

        mock_post = mocker.patch("jvcli.client.app.requests.post")
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "user": {"root_id": "root_id", "expiration": "expiration"},
            "token": "token",
        }

        app_test = AppTest.from_file(
            Path(__file__)
            .resolve()
            .parent.parent.parent.joinpath("jvcli")
            .joinpath("client")
            .joinpath("app.py")
            .resolve()
            .__str__()
        )
        app_test.run()

        assert app_test.session_state["ROOT_ID"] == "root_id"
        assert app_test.session_state["TOKEN"] == "token"
        assert app_test.session_state["streamlit-router-endpoint"] == "dashboard"

        # Clean up
        del os.environ["JIVAS_ENVIRONMENT"]

    def test_client_login_key_error_exception(self, mocker: MockerFixture) -> None:
        """Test login form submission with KeyError exception."""

        app_test = AppTest.from_file(
            Path(__file__)
            .resolve()
            .parent.parent.parent.joinpath("jvcli")
            .joinpath("client")
            .joinpath("app.py")
            .resolve()
            .__str__()
        )

        # Mock post request
        mocker_login = mocker.patch("jvcli.client.app.requests.post")
        mocker_login.return_value.status_code = 200
        mocker_login.return_value.json.return_value = {
            "user": {"root_id": "root_id", "expiration": "expiration"},
            "token": "token",
        }

        # Mock list agents
        mock_agents = mocker.patch("jvcli.client.lib.utils.call_list_agents")
        mock_agents.return_value = [{"id": "test_agent_id", "label": "test_agent_name"}]

        # Mock list actions
        mock_actions = mocker.patch("jvcli.client.lib.utils.call_list_actions")
        mock_actions.return_value = [
            {
                "id": "test_action_id",
                "name": "test_action_name",
                "_package": {
                    "config": {
                        "path": os.path.join(os.path.dirname(__file__), "../fixtures"),
                    }
                },
            }
        ]

        # Mock query params
        mock_query_params = mocker.patch("jvcli.client.app.st.query_params", {})

        app_test.run()

        app_test.text_input[0].input("admin@test.com").run()
        app_test.text_input[1].input("password").run()
        app_test.button[0].click().run()

        assert mock_query_params.get("agent") == "test_agent_id"

    def test_client_handle_agent_selection(self, mocker: MockerFixture) -> None:
        """Test handle agent selection function."""

        app_test = AppTest.from_file(
            Path(__file__)
            .resolve()
            .parent.parent.parent.joinpath("jvcli")
            .joinpath("client")
            .joinpath("app.py")
            .resolve()
            .__str__()
        )

        # Mock post request
        mocker_login = mocker.patch("jvcli.client.app.requests.post")
        mocker_login.return_value.status_code = 200
        mocker_login.return_value.json.return_value = {
            "user": {"root_id": "root_id", "expiration": "expiration"},
            "token": "token",
        }

        # Mock list agents
        mock_agents = mocker.patch("jvcli.client.lib.utils.call_list_agents")
        mock_agents.return_value = [
            {"id": "test_agent_1_id", "label": "test_agent_1_name"},
            {"id": "test_agent_2_id", "label": "test_agent_2_name"},
        ]

        # Mock list actions
        mock_actions = mocker.patch("jvcli.client.lib.utils.call_list_actions")
        mock_actions.return_value = [
            {
                "id": "test_action_id",
                "name": "test_action_name",
                "_package": {
                    "meta": {"title": "Test App"},
                    "config": {
                        "path": os.path.join(os.path.dirname(__file__), "../fixtures"),
                        "app": True,
                    },
                },
            }
        ]

        # Mock query params
        mocker.patch("jvcli.client.app.st.query_params", {})

        app_test.run()

        app_test.text_input[0].input("admin@test.com").run()
        app_test.text_input[1].input("password").run()
        app_test.button[0].click().run()
        app_test.selectbox[0].select_index(1).run()

        assert app_test.selectbox[0].value["id"] == "test_agent_2_id"

    def test_client_hide_sidebar(self, mocker: MockerFixture) -> None:
        """Test client with hidden sidebar."""

        app_test = AppTest.from_file(
            Path(__file__)
            .resolve()
            .parent.parent.parent.joinpath("jvcli")
            .joinpath("client")
            .joinpath("app.py")
            .resolve()
            .__str__()
        )

        # Mock post request
        mocker_login = mocker.patch("jvcli.client.app.requests.post")
        mocker_login.return_value.status_code = 200
        mocker_login.return_value.json.return_value = {
            "user": {"root_id": "root_id", "expiration": "expiration"},
            "token": "token",
        }

        # Mock query params
        mock_query_params = mocker.patch(
            "jvcli.client.app.st.query_params", {"hide_sidebar": "true"}
        )

        # Mock markdown
        mock_md = mocker.patch("jvcli.client.app.st.markdown", mocker.MagicMock())

        app_test.run()

        app_test.text_input[0].input("admin@test.com").run()
        app_test.text_input[1].input("password").run()
        app_test.button[0].click().run()

        print(mock_query_params)
        mock_md.assert_called_once()

    def test_client_already_logged_in(self, mocker: MockerFixture) -> None:
        """Test client with already logged in session."""

        app_test = AppTest.from_file(
            Path(__file__)
            .resolve()
            .parent.parent.parent.joinpath("jvcli")
            .joinpath("client")
            .joinpath("app.py")
            .resolve()
            .__str__()
        )

        # Mock query params
        mock_query_params = mocker.patch(
            "jvcli.client.app.st.query_params", {"token": "test_token"}
        )

        app_test.run()

        assert mock_query_params.get("token") == "test_token"
        assert app_test.header[0].body == "Analytics"

    def test_button_click_triggers_redirect(self, mocker: MockerFixture) -> None:
        """Test button click triggers redirect method."""

        # Mock streamlit button
        mock_button = mocker.patch("streamlit.button")
        mock_button.return_value = True

        # Mock router
        mock_router = mocker.Mock()
        mock_router.build.return_value = ("test_path", {"test": "args"})

        # Initialize page with mocked router
        page = Page(mock_router)
        page._label = "Test Label"
        page._key = "test_key"
        page._args = {"test": "args"}

        # Call method
        page.st_button()

        # Verify button was called correctly
        mock_button.assert_called_once_with(
            "Test Label", key="test_key", use_container_width=True
        )

        # Verify router methods were called correctly
        mock_router.build.assert_called_once_with("test_key", {"test": "args"})
        mock_router.redirect.assert_called_once_with("test_path", {"test": "args"})
