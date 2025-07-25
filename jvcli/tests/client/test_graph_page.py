"""Test for the JVCLI client graph page."""

import os
from pathlib import Path

from pytest_mock import MockerFixture
from streamlit.testing.v1 import AppTest

from jvcli.client.pages.graph_page import JIVAS_STUDIO_URL


class TestClientGraphPage:
    """Test the JVCLI client graph page."""

    def test_render_graph(self, mocker: MockerFixture) -> None:
        """Test rendering the graph page."""
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
                        "app": True,
                    },
                    "meta": {"title": "Action 1", "type": "interact_action"},
                },
                "label": "Action 1",
                "description": "Test description 1",
                "version": "1.0.0",
                "enabled": True,
            }
        ]

        # Mock graph page
        mock_graph_iframe = mocker.patch("streamlit.components.v1.iframe")

        app_test.run()

        app_test.text_input[0].input("admin@test.com").run()
        app_test.text_input[1].input("password").run()
        app_test.button[0].click().run()

        # assert logged in
        assert app_test.session_state["ROOT_ID"] == "root_id"
        assert app_test.session_state["TOKEN"] == "token"
        assert app_test.session_state["EXPIRATION"] == "expiration"

        # trigger graph page
        app_test.button[3].click().run()

        # assert on graph page
        assert app_test.query_params["request"] == ["GET:/graph"]
        mock_graph_iframe.assert_called_once_with(
            JIVAS_STUDIO_URL, width=None, height=800, scrolling=False
        )
