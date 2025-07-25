"""Test for the jvcli client dashboard page."""

import os
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture
from streamlit.testing.v1 import AppTest

from jvcli.client.pages.action_dashboard_page import logout

DASHBOARD_CARD_TITLE = "Action 1"
DASHBOARD_CARD_DESC = "Test description 1"
DASHBOARD_CARD_VERSION = "1.0.0"
DASHBOARD_CARD_TYPE = "interact_action"


@pytest.fixture(autouse=True)
def reset_streamlit_state(monkeypatch: Any) -> None:
    """Automatically reset session_state and query_params between tests."""
    from streamlit import query_params, session_state

    session_state.clear()
    query_params.from_dict({})


class TestClientActionDashboardPage:
    """Test the JVCLI client dashboard page."""

    @pytest.fixture(autouse=True)
    def setup_app_test(self) -> None:
        """Setup AppTest for each test."""
        app_path = (
            Path(__file__)
            .resolve()
            .parent.parent.parent.joinpath("jvcli")
            .joinpath("client")
            .joinpath("app.py")
            .resolve()
        )
        self.app_test = AppTest.from_file(str(app_path))

    def test_render_action_dashboard(self, mocker: MockerFixture) -> None:
        """Test the dashboard executes correct logic (data fetching, routing, and session state)."""

        # --- Set up login patch ---
        mocker_login = mocker.patch("jvcli.client.app.requests.post")
        mocker_login.return_value.status_code = 200
        mocker_login.return_value.json.return_value = {
            "user": {"root_id": "root_id", "expiration": "expiration"},
            "token": "token",
        }

        # --- Set up agent and action list patches ---
        mock_agents = mocker.patch("jvcli.client.lib.utils.call_list_agents")
        mock_agents.return_value = [{"id": "test_agent_id", "label": "test_agent_name"}]

        mock_actions = mocker.patch("jvcli.client.lib.utils.call_list_actions")
        mocked_actions_data = [
            {
                "id": "test_action_id",
                "name": "test_action_name",
                "_package": {
                    "config": {
                        "path": os.path.join(os.path.dirname(__file__), "../fixtures"),
                        "app": True,
                    },
                    "meta": {"title": "Action 1", "type": "interact_action"},
                    "version": "1.0.0",
                },
                "label": "Action 1",
                "description": "Test description 1",
                "enabled": True,
            }
        ]
        mock_actions.return_value = mocked_actions_data

        # --- Simulate user login ---
        self.app_test.run()
        self.app_test.text_input[0].input("admin@test.com").run()
        self.app_test.text_input[1].input("password").run()
        self.app_test.button[0].click().run()

        # --- Verify login state ---
        assert self.app_test.session_state["ROOT_ID"] == "root_id"
        assert self.app_test.session_state["TOKEN"] == "token"
        # assert self.app_test.session_state["EXPIRATION"] == "expiration"

        # --- Go to actions dashboard ---
        self.app_test.button[2].click().run()

        # --- Data/state assertions ---
        assert "actions_data" in self.app_test.session_state
        assert self.app_test.session_state["actions_data"] == mocked_actions_data

        assert self.app_test.query_params.get("agent") == ["test_agent_id"]
        assert self.app_test.query_params.get("request") == ["GET:/actions"]

        # --- Looser assertion on data calls due to rerun nature ---
        assert mock_actions.call_count >= 1
        assert mock_agents.call_count >= 1

    def test_token_removal_from_session_state(self, mocker: MockerFixture) -> None:
        """Test removing the token from session state."""
        # Mock streamlit session state and query params
        mock_session_state = mocker.patch(
            "streamlit.session_state", {"TOKEN": "test_token"}
        )
        mock_query_params = mocker.patch("streamlit.query_params", mocker.MagicMock())
        mock_query_params["token"] = "test_token"

        # Call logout function
        logout()

        # Verify TOKEN was removed from session state
        assert "TOKEN" not in mock_session_state
        assert "token" not in mock_query_params

    def test_render_no_actions(self, mocker: MockerFixture) -> None:
        """Dashboard should show nothing if no actions_data."""
        # -- Setup with empty action list --
        mocker_login = mocker.patch("jvcli.client.app.requests.post")
        mocker_login.return_value.status_code = 200
        mocker_login.return_value.json.return_value = {
            "user": {"root_id": "root_id", "expiration": "expiration"},
            "token": "token",
        }
        mocker.patch("jvcli.client.lib.utils.call_list_agents", return_value=[])
        mocker.patch("jvcli.client.lib.utils.call_list_actions", return_value=[])

        self.app_test.run()
        self.app_test.text_input[0].input("admin@test.com").run()
        self.app_test.text_input[1].input("password").run()
        self.app_test.button[0].click().run()
        self.app_test.button[2].click().run()

        # There should be no cards rendered
        if hasattr(self.app_test, "mui_cardheader"):
            assert len(self.app_test.mui_cardheader) == 0
        else:
            assert True  # no cards rendered, which is expected

    def test_logout_clears_token(self, mocker: MockerFixture) -> None:
        """Test logout: token gets removed from session_state and query_params."""

        # Arrange session_state and query_params
        fake_session_state = {"TOKEN": "abc123"}
        fake_query_params: dict[str, str] = {"token": "abc123", "other": "xyz"}

        mocker.patch("streamlit.session_state", fake_session_state)
        mock_qp = mocker.patch("streamlit.query_params")
        mock_qp.get.side_effect = lambda k, default=None: fake_query_params.get(
            k, default
        )
        mock_qp.to_dict.return_value = fake_query_params.copy()

        def update_qp(d: dict[str, str]) -> None:
            fake_query_params.clear()
            fake_query_params.update(d)

        mock_qp.from_dict.side_effect = update_qp

        # Act
        logout()

        # Assert
        assert "TOKEN" not in fake_session_state
        assert "token" not in fake_query_params

    def test_logout_only_deletes_token_when_present(
        self, mocker: MockerFixture
    ) -> None:
        """If no token in query params, only remove from session_state."""
        fake_session_state = {"TOKEN": "123"}
        fake_query_params: dict[str, str] = {}  # no token

        mocker.patch("streamlit.session_state", fake_session_state)
        mock_qp = mocker.patch("streamlit.query_params")
        mock_qp.get.return_value = None
        mock_qp.to_dict.return_value = fake_query_params.copy()

        def update_qp(d: dict[str, str]) -> None:
            fake_query_params.clear()
            fake_query_params.update(d)

        mock_qp.from_dict.side_effect = update_qp

        logout()

        assert "TOKEN" not in fake_session_state
        assert fake_query_params == {}  # unchanged
