"""Test for the JVCLI client analytics page."""

import datetime

from pytest_mock import MockerFixture

from jvcli.client.lib.utils import JIVAS_BASE_URL
from jvcli.client.pages.analytics_page import (
    channels_chart,
    interactions_chart,
    render,
    users_chart,
)


class TestClientAnalyticsPage:
    """Test the JVCLI client analytics page."""

    def test_render_analytics_with_valid_inputs(self, mocker: MockerFixture) -> None:
        """Test rendering analytics with valid inputs."""
        # Mock get_user_info to return a valid token
        mocker.patch(
            "jvcli.client.pages.analytics_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock session state
        mocker.patch(
            "streamlit.session_state", {"selected_agent": {"id": "test_agent_id"}}
        )

        # Mock streamlit widgets
        mocker.patch("streamlit.header")
        mock_date_input = mocker.patch("streamlit.date_input")
        mock_date_input.return_value = (
            datetime.date(2024, 1, 1),
            datetime.date(2024, 1, 31),
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st.columns", return_value=(1, 2, 3)
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st_javascript",
            return_value="test_timezone",
        )

        # Mock chart functions
        mock_interactions = mocker.patch(
            "jvcli.client.pages.analytics_page.interactions_chart"
        )
        mock_users = mocker.patch("jvcli.client.pages.analytics_page.users_chart")
        mock_channels = mocker.patch("jvcli.client.pages.analytics_page.channels_chart")

        # Mock router
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify chart functions were called with correct params
        mock_interactions.assert_called_once()
        mock_users.assert_called_once()
        mock_channels.assert_called_once()

    def test_render_with_no_selected_agent(self, mocker: MockerFixture) -> None:
        """Test rendering analytics page when no agent is selected."""
        # Mock session state
        mocker.patch("streamlit.session_state", {})

        # Mock streamlit widgets
        mock_header = mocker.patch("streamlit.header")
        mock_text = mocker.patch("streamlit.text")

        # Mock router
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify header and text were called
        mock_header.assert_called_once_with("Analytics", divider=True)
        mock_text.assert_called_once_with("Invalid date range")

    def test_render_with_recheck_health_clicked(self, mocker: MockerFixture) -> None:
        """Test rendering analytics when recheck_health_clicked is True."""
        # Create a mutable dict to track session state changes
        mock_session_state = {
            "selected_agent": {"id": "test_agent_id"},
            "recheck_health_clicked": True,
        }

        # Mock session state with our mutable dictionary
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit widgets
        mocker.patch("streamlit.header")
        mocker.patch(
            "streamlit.date_input",
            return_value=(
                datetime.date(2024, 1, 1),
                datetime.date(2024, 1, 31),
            ),
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st.columns", return_value=(1, 2, 3)
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st_javascript",
            return_value="test_timezone",
        )
        mocker.patch("streamlit.expander")

        # Mock get_user_info
        mocker.patch(
            "jvcli.client.pages.analytics_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock cache_data.clear() method
        mock_cache_data = mocker.patch(
            "jvcli.client.pages.analytics_page.st.cache_data"
        )
        mock_cache_instance = mock_cache_data.return_value
        mock_cache_instance.clear = mocker.Mock()

        # Mock call_healthcheck to return data directly
        mock_call_healthcheck = mocker.patch(
            "jvcli.client.pages.analytics_page.call_healthcheck",
            return_value={"trace": {}},
        )

        # Mock chart functions
        mocker.patch("jvcli.client.pages.analytics_page.interactions_chart")
        mocker.patch("jvcli.client.pages.analytics_page.users_chart")
        mocker.patch("jvcli.client.pages.analytics_page.channels_chart")

        # Mock router
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify that call_healthcheck was called directly with the agent id
        mock_call_healthcheck.assert_called_once_with("test_agent_id")

        # Verify recheck_health_clicked was set back to False
        assert mock_session_state["recheck_health_clicked"] is False

    def test_render_with_invalid_date_range(self, mocker: MockerFixture) -> None:
        """Test rendering analytics page with an invalid date range."""
        # Mock session state
        mocker.patch(
            "streamlit.session_state",
            {"selected_agent": {"id": "test_agent_id"}},
        )

        # Mock streamlit widgets
        mock_header = mocker.patch("streamlit.header")
        mock_date_input = mocker.patch("streamlit.date_input")
        mock_date_input.return_value = (
            datetime.date(2024, 1, 31),
            datetime.date(2024, 1, 1),
        )
        mock_text = mocker.patch("streamlit.text")

        # Mock router
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify header and text were called
        mock_header.assert_called_once_with("Analytics", divider=True)
        mock_text.assert_called_once_with("Invalid date range")

    def test_interactions_chart_successful_api_call(
        self, mocker: MockerFixture
    ) -> None:
        """Test interactions chart with a successful API call."""
        # Mock dependencies
        mock_container = mocker.patch("streamlit.container")
        mock_subheader = mocker.patch("streamlit.subheader")
        mock_line_chart = mocker.patch("streamlit.line_chart")
        mock_metric = mocker.Mock()
        mock_requests = mocker.patch("requests.post")

        # Setup test data
        test_date = datetime.date(2024, 1, 1)
        test_response_data = {
            "reports": [{"data": [{"date": "2024-01-01", "count": 10}], "total": 100}]
        }
        mock_requests.return_value.status_code = 200
        mock_requests.return_value.json.return_value = test_response_data

        # Call function
        interactions_chart(
            start_date=test_date,
            end_date=test_date,
            agent_id="test_agent",
            token="test_token",
            metric_col=mock_metric,
            timezone="UTC",
        )

        # Verify API call
        mock_requests.assert_called_once_with(
            url=f"{JIVAS_BASE_URL}/walker/get_interactions_by_date",
            json={
                "agent_id": "test_agent",
                "reporting": True,
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
                "timezone": "UTC",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Verify chart rendering
        mock_container.assert_called_once()
        mock_subheader.assert_called_once_with("Interactions by Date")
        mock_line_chart.assert_called_once()
        mock_metric.metric.assert_called_once_with("Interactions", 100)

    def test_users_chart_successful_api_call(self, mocker: MockerFixture) -> None:
        """Test users chart with a successful API call."""
        # Mock streamlit widgets
        mock_container = mocker.patch("streamlit.container")
        mock_subheader = mocker.patch("streamlit.subheader")
        mock_line_chart = mocker.patch("streamlit.line_chart")
        mock_metric = mocker.Mock()
        mock_metric_col = mocker.Mock()
        mock_metric_col.metric = mock_metric

        # Mock requests.post response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reports": [
                {
                    "data": [
                        {"date": "2024-01-01", "count": 10},
                        {"date": "2024-01-02", "count": 20},
                    ],
                    "total": 30,
                }
            ]
        }
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        # Test inputs
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 1, 31)
        agent_id = "test_agent_id"
        token = "test_token"
        timezone = "UTC"

        # Call function
        users_chart(start_date, end_date, agent_id, token, mock_metric_col, timezone)

        # Verify API call
        mock_post.assert_called_once_with(
            url=f"{JIVAS_BASE_URL}/walker/get_users_by_date",
            json={
                "agent_id": agent_id,
                "reporting": True,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": timezone,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Verify streamlit widgets were called
        mock_container.assert_called_once()
        mock_subheader.assert_called_once_with("Users by Date")
        mock_line_chart.assert_called_once()
        mock_metric.assert_called_once_with("Users", 30)

    def test_channels_chart_successful_api_call(self, mocker: MockerFixture) -> None:
        """Test channels chart with a successful API call."""
        # Mock streamlit components
        mock_container = mocker.patch("streamlit.container")
        mock_subheader = mocker.patch("streamlit.subheader")
        mock_line_chart = mocker.patch("streamlit.line_chart")
        mock_metric = mocker.Mock()

        # Mock requests post call
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reports": [
                {
                    "data": [
                        {"date": "2024-01-01", "count": 5},
                        {"date": "2024-01-02", "count": 10},
                    ],
                    "total": 15,
                }
            ]
        }
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        # Test inputs
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 1, 2)
        agent_id = "test_agent"
        token = "test_token"
        timezone = "UTC"

        # Call function
        channels_chart(start_date, end_date, agent_id, token, mock_metric, timezone)

        # Verify API call
        mock_post.assert_called_once_with(
            url=f"{JIVAS_BASE_URL}/walker/get_channels_by_date",
            json={
                "agent_id": agent_id,
                "reporting": True,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": timezone,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Verify streamlit components called
        mock_container.assert_called_once()
        mock_subheader.assert_called_once_with("Channels by Date")
        mock_line_chart.assert_called_once()
        mock_metric.metric.assert_called_once_with("Channels", 15)

    def test_render_with_health_errors(self, mocker: MockerFixture) -> None:
        """Test rendering analytics when health data contains errors."""
        # Create a mock session state
        mock_session_state = {
            "selected_agent": {"id": "test_agent_id"},
            "recheck_health_clicked": False,
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit widgets
        mocker.patch("streamlit.header")
        mock_date_input = mocker.patch("streamlit.date_input")
        mock_date_input.return_value = (
            datetime.date(2024, 1, 1),
            datetime.date(2024, 1, 31),
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st.columns", return_value=(1, 2, 3)
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st_javascript",
            return_value="test_timezone",
        )

        # Mock the expander and its returned context
        mock_expander = mocker.patch("streamlit.expander")
        mock_expander_context = mocker.MagicMock()
        mock_expander.return_value.__enter__.return_value = mock_expander_context

        # Mock error and text functions
        mock_error = mocker.patch("streamlit.error")
        mock_text = mocker.patch("streamlit.text")
        mock_button = mocker.patch("streamlit.button")
        mock_button.return_value = False  # Don't trigger recheck

        # Mock get_user_info
        mocker.patch(
            "jvcli.client.pages.analytics_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock health data with errors
        mock_health_data = {
            "trace": {
                "error1": {"severity": "error", "message": "This is a critical error"},
                "error2": {"severity": "error", "message": "Another critical error"},
                "warning1": {
                    "severity": "warning",
                    "message": "This is just a warning",
                },
            }
        }

        # Mock call_healthcheck to return health data with errors
        # We're mocking the underlying function that fetch_healthcheck calls
        mocker.patch(
            "jvcli.client.pages.analytics_page.call_healthcheck",
            return_value=mock_health_data,
        )

        # Create a mock for st.cache_data that returns a function that returns our mock data
        mock_cache_data = mocker.patch(
            "jvcli.client.pages.analytics_page.st.cache_data"
        )
        mock_cache_data.return_value = lambda func: lambda agent_id: mock_health_data

        # Mock chart functions
        mock_interactions = mocker.patch(
            "jvcli.client.pages.analytics_page.interactions_chart"
        )
        mock_users = mocker.patch("jvcli.client.pages.analytics_page.users_chart")
        mock_channels = mocker.patch("jvcli.client.pages.analytics_page.channels_chart")

        # Mock router
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify expander was created with the correct parameters
        mock_expander.assert_called_once_with(
            ":red[Agent health needs ATTENTION!]", expanded=True
        )

        # Verify error section was created
        mock_error.assert_called_once_with("Errors")

        # Verify error messages were displayed
        mock_text.assert_any_call("- error1: This is a critical error")
        mock_text.assert_any_call("- error2: Another critical error")

        # Verify chart functions were called
        mock_interactions.assert_called_once()
        mock_users.assert_called_once()
        mock_channels.assert_called_once()

    def test_render_with_health_warnings(self, mocker: MockerFixture) -> None:
        """Test rendering analytics when health data contains warnings but no errors."""
        # Create a mock session state
        mock_session_state = {
            "selected_agent": {"id": "test_agent_id"},
            "recheck_health_clicked": False,
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit widgets
        mocker.patch("streamlit.header")
        mocker.patch(
            "streamlit.date_input",
            return_value=(
                datetime.date(2024, 1, 1),
                datetime.date(2024, 1, 31),
            ),
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st.columns", return_value=(1, 2, 3)
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st_javascript",
            return_value="test_timezone",
        )

        # Mock the expander and its returned context
        mock_expander = mocker.patch("streamlit.expander")
        mock_expander_context = mocker.MagicMock()
        mock_expander.return_value.__enter__.return_value = mock_expander_context

        # Mock warning and text functions
        mock_warning = mocker.patch("streamlit.warning")
        mock_text = mocker.patch("streamlit.text")
        mock_button = mocker.patch("streamlit.button")
        mock_button.return_value = False  # Don't trigger recheck

        # Mock get_user_info
        mocker.patch(
            "jvcli.client.pages.analytics_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock health data with warnings only (no errors)
        mock_health_data = {
            "trace": {
                "warning1": {"severity": "warning", "message": "This is a warning"},
                "warning2": {"severity": "warning", "message": "Another warning"},
            }
        }

        # Mock call_healthcheck to return health data with warnings
        mocker.patch(
            "jvcli.client.pages.analytics_page.call_healthcheck",
            return_value=mock_health_data,
        )

        # Create a mock for st.cache_data that returns a function that returns our mock data
        mock_cache_data = mocker.patch(
            "jvcli.client.pages.analytics_page.st.cache_data"
        )
        mock_cache_data.return_value = lambda func: lambda agent_id: mock_health_data

        # Mock chart functions
        mock_interactions = mocker.patch(
            "jvcli.client.pages.analytics_page.interactions_chart"
        )
        mock_users = mocker.patch("jvcli.client.pages.analytics_page.users_chart")
        mock_channels = mocker.patch("jvcli.client.pages.analytics_page.channels_chart")

        # Mock router
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify expander was created with the correct parameters (orange for warnings)
        mock_expander.assert_called_once_with(
            ":orange[Agent health is OK (with warnings)]", expanded=True
        )

        # Verify warnings section was created
        mock_warning.assert_called_once_with("Warnings")

        # Verify warning messages were displayed
        mock_text.assert_any_call("- warning1: This is a warning")
        mock_text.assert_any_call("- warning2: Another warning")

        # Verify chart functions were called
        mock_interactions.assert_called_once()
        mock_users.assert_called_once()
        mock_channels.assert_called_once()

    def test_recheck_health_button_inside_expander(self, mocker: MockerFixture) -> None:
        """Test clicking the Recheck Health button inside the expander."""
        # Create a mock session state
        mock_session_state = {
            "selected_agent": {"id": "test_agent_id"},
            "recheck_health_clicked": False,
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit widgets
        mocker.patch("streamlit.header")
        mocker.patch(
            "streamlit.date_input",
            return_value=(
                datetime.date(2024, 1, 1),
                datetime.date(2024, 1, 31),
            ),
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st.columns", return_value=(1, 2, 3)
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st_javascript",
            return_value="test_timezone",
        )

        # Mock the expander and its returned context
        mock_expander = mocker.patch("streamlit.expander")
        mock_expander_context = mocker.MagicMock()
        mock_expander.return_value.__enter__.return_value = mock_expander_context

        # Mock text and warning functions
        mocker.patch("streamlit.text")
        mocker.patch("streamlit.warning")

        # Set button to return True (simulating a click)
        mock_button = mocker.patch("streamlit.button")
        mock_button.return_value = True

        # Mock get_user_info
        mocker.patch(
            "jvcli.client.pages.analytics_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Mock health data with warnings only
        mock_health_data = {
            "trace": {
                "warning1": {"severity": "warning", "message": "This is a warning"}
            }
        }

        # Mock call_healthcheck
        mocker.patch(
            "jvcli.client.pages.analytics_page.call_healthcheck",
            return_value=mock_health_data,
        )

        # Create a mock for st.cache_data
        mock_cache_data = mocker.patch(
            "jvcli.client.pages.analytics_page.st.cache_data"
        )
        mock_cache_data.return_value = lambda func: lambda agent_id: mock_health_data

        # Mock chart functions
        mocker.patch("jvcli.client.pages.analytics_page.interactions_chart")
        mocker.patch("jvcli.client.pages.analytics_page.users_chart")
        mocker.patch("jvcli.client.pages.analytics_page.channels_chart")

        # Mock router
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify button was called with the correct parameters
        mock_button.assert_called_once_with(
            "Recheck Health", key="recheck_inside_expander"
        )

        # Verify recheck_health_clicked was set to True after button click
        assert mock_session_state["recheck_health_clicked"] is True

    def test_render_with_healthcheck_exception(self, mocker: MockerFixture) -> None:
        """Test rendering analytics when an exception occurs in healthcheck processing."""
        # Create a mock session state
        mock_session_state = {
            "selected_agent": {"id": "test_agent_id"},
            "recheck_health_clicked": False,
        }
        mocker.patch("streamlit.session_state", mock_session_state)

        # Mock streamlit widgets
        mocker.patch("streamlit.header")
        mocker.patch(
            "streamlit.date_input",
            return_value=(
                datetime.date(2024, 1, 1),
                datetime.date(2024, 1, 31),
            ),
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st.columns", return_value=(1, 2, 3)
        )
        mocker.patch(
            "jvcli.client.pages.analytics_page.st_javascript",
            return_value="test_timezone",
        )

        # Mock error function
        mock_error = mocker.patch("streamlit.error")

        # Mock get_user_info
        mocker.patch(
            "jvcli.client.pages.analytics_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )

        # Create a malformed health data that will cause an exception
        mock_health_data = {
            "trace": None
        }  # This will cause an exception when trying to iterate over trace.items()

        # Mock call_healthcheck to return malformed data
        mocker.patch(
            "jvcli.client.pages.analytics_page.call_healthcheck",
            return_value=mock_health_data,
        )

        # Create a mock for st.cache_data that returns our malformed data
        mock_cache_data = mocker.patch(
            "jvcli.client.pages.analytics_page.st.cache_data"
        )
        mock_cache_data.return_value = lambda func: lambda agent_id: mock_health_data

        # Mock print to avoid printing to console during test
        mock_print = mocker.patch("builtins.print")

        # Mock chart functions - store the mocks for later assertions
        mock_interactions = mocker.patch(
            "jvcli.client.pages.analytics_page.interactions_chart"
        )
        mock_users = mocker.patch("jvcli.client.pages.analytics_page.users_chart")
        mock_channels = mocker.patch("jvcli.client.pages.analytics_page.channels_chart")

        # Mock router
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify error message was displayed
        mock_error.assert_any_call("An error occurred while fetching healthcheck data.")

        # Verify exception was printed (or at least print was called)
        mock_print.assert_called_once()

        # Verify chart functions were still called - use the mock objects created earlier
        mock_interactions.assert_called_once()
        mock_users.assert_called_once()
        mock_channels.assert_called_once()
