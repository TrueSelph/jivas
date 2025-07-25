"""Renders the analytics page of the JVCLI client."""

import calendar
import datetime
import os
from typing import Optional

import pandas as pd
import requests
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit_javascript import st_javascript
from streamlit_router import StreamlitRouter

from jvcli.client.lib.utils import call_healthcheck, get_user_info

JIVAS_BASE_URL = os.environ.get("JIVAS_BASE_URL", "http://localhost:8000")


def render(router: StreamlitRouter) -> None:
    """Render the analytics page."""

    selected_agent = st.session_state.get("selected_agent")

    # Call the healthcheck endpoint and render the collapsible section
    @st.cache_data(show_spinner=True)
    def fetch_healthcheck(agent_id: str) -> Optional[dict]:
        return call_healthcheck(agent_id)

    health_data = None

    if selected_agent:
        # Clear the cache and fetch fresh data if the button is clicked
        if st.session_state.get("recheck_health_clicked", False):
            fetch_healthcheck.clear()
            health_data = call_healthcheck(selected_agent["id"])
            st.session_state["recheck_health_clicked"] = False
        else:
            # Use cached data
            health_data = fetch_healthcheck(selected_agent["id"])

        try:
            if health_data:
                trace = health_data.get("trace", {})
                errors = [
                    f"{key}: {value['message']}"
                    for key, value in trace.items()
                    if value.get("severity") == "error"
                ]
                warnings = [
                    f"{key}: {value['message']}"
                    for key, value in trace.items()
                    if value.get("severity") == "warning"
                ]

                if errors:
                    section_label = "Agent health needs ATTENTION!"
                    section_color = "red"
                    expanded = True
                elif warnings:
                    section_label = "Agent health is OK (with warnings)"
                    section_color = "orange"
                    expanded = True
                else:
                    section_label = "Agent health is OK"
                    section_color = "green"
                    expanded = False

                with st.expander(
                    f":{section_color}[{section_label}]", expanded=expanded
                ):
                    if errors:
                        st.error("Errors")
                        for error in errors:
                            st.text(f"- {error}")
                    if warnings:
                        st.warning("Warnings")
                        for warning in warnings:
                            st.text(f"- {warning}")
                    if st.button("Recheck Health", key="recheck_inside_expander"):
                        st.session_state["recheck_health_clicked"] = True
                        st.rerun()

            else:
                st.error("Failed to fetch healthcheck data.")
        except Exception as e:
            st.error("An error occurred while fetching healthcheck data.")
            print(e)

    st.header("Analytics", divider=True)
    today = datetime.date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]

    date_range = st.date_input(
        "Period",
        (
            datetime.date(today.year, today.month, 1),
            datetime.date(today.year, today.month, last_day),
        ),
    )

    (start_date, end_date) = date_range

    # rerender_metrics = render_metrics()
    col1, col2, col3 = st.columns(3)
    timezone = st_javascript(
        """await (async () => {
                const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                console.log(userTimezone)
                return userTimezone
    })().then(returnValue => returnValue)"""
    )

    try:
        ctx = get_user_info()
        if selected_agent and end_date > start_date:
            interactions_chart(
                token=ctx["token"],
                agent_id=selected_agent["id"],
                start_date=start_date,
                end_date=end_date,
                metric_col=col1,
                timezone=timezone,
            )
            users_chart(
                token=ctx["token"],
                agent_id=selected_agent["id"],
                start_date=start_date,
                end_date=end_date,
                metric_col=col2,
                timezone=timezone,
            )
            channels_chart(
                token=ctx["token"],
                agent_id=selected_agent["id"],
                start_date=start_date,
                end_date=end_date,
                metric_col=col3,
                timezone=timezone,
            )
        else:
            st.text("Invalid date range")
    except Exception as e:
        st.text("Unable to render charts")
        print(e)


def interactions_chart(
    start_date: datetime.date,
    end_date: datetime.date,
    agent_id: str,
    token: str,
    metric_col: DeltaGenerator,
    timezone: str,
) -> None:
    """Render the interactions chart."""
    url = f"{JIVAS_BASE_URL}/walker/get_interactions_by_date"

    with st.container(border=True):
        st.subheader("Interactions by Date")
        response = requests.post(
            url=url,
            json={
                "agent_id": agent_id,
                "reporting": True,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": timezone,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            if response_data := response.json():
                chart_data = pd.DataFrame(
                    data=response_data["reports"][0]["data"],
                )
                st.line_chart(chart_data, x="date", y="count")
                total = response_data["reports"][0]["total"]
                metric_col.metric("Interactions", total)


def users_chart(
    start_date: datetime.date,
    end_date: datetime.date,
    agent_id: str,
    token: str,
    metric_col: DeltaGenerator,
    timezone: str,
) -> None:
    """Render the users chart."""
    url = f"{JIVAS_BASE_URL}/walker/get_users_by_date"
    with st.container(border=True):
        st.subheader("Users by Date")
        response = requests.post(
            url=url,
            json={
                "agent_id": agent_id,
                "reporting": True,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": timezone,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            if response_data := response.json():
                chart_data = pd.DataFrame(
                    data=response_data["reports"][0]["data"],
                )
                st.line_chart(chart_data, x="date", y="count")
                total = response_data["reports"][0]["total"]
                metric_col.metric("Users", total)


def channels_chart(
    start_date: datetime.date,
    end_date: datetime.date,
    agent_id: str,
    token: str,
    metric_col: DeltaGenerator,
    timezone: str,
) -> None:
    """Render the channels chart."""
    url = f"{JIVAS_BASE_URL}/walker/get_channels_by_date"
    with st.container(border=True):
        st.subheader("Channels by Date")
        response = requests.post(
            url=url,
            json={
                "agent_id": agent_id,
                "reporting": True,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": timezone,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            if response_data := response.json():
                chart_data = pd.DataFrame(
                    data=response_data["reports"][0]["data"],
                )
                st.line_chart(chart_data, x="date", y="count")
                total = response_data["reports"][0]["total"]
                metric_col.metric("Channels", total)
