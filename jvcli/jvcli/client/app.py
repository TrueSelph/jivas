"""This module contains the main application logic for the JVCLI client."""

import os

import requests
import streamlit as st
from streamlit_router import StreamlitRouter

from jvcli.client.lib.page import Page
from jvcli.client.lib.utils import call_list_actions, call_list_agents, load_function
from jvcli.client.pages import (
    action_dashboard_page,
    analytics_page,
    chat_page,
    graph_page,
)

JIVAS_BASE_URL = os.environ.get("JIVAS_BASE_URL", "http://localhost:8000")
JIVAS_STUDIO_URL = os.environ.get("JIVAS_STUDIO_URL", "http://localhost:8989")


def handle_agent_selection() -> None:
    """Handle the selection of an agent."""
    if "selected_agent" in st.session_state:
        st.query_params["agent"] = st.session_state.selected_agent["id"]
        st.session_state.messages = {}


def login_form() -> None:
    """Render the login form and handle login logic."""
    login_url = f"{JIVAS_BASE_URL}/user/login"

    if os.environ.get("JIVAS_ENVIRONMENT") == "development":
        email = os.environ.get("JIVAS_USER", "admin@jivas.com")
        password = os.environ.get("JIVAS_PASSWORD", "password")

        response = requests.post(login_url, json={"email": email, "password": password})

        if response.status_code == 200:
            st.session_state.ROOT_ID = response.json()["user"]["root_id"]
            st.session_state.TOKEN = response.json()["token"]
            st.session_state.EXPIRATION = response.json()["user"]["expiration"]
            st.rerun()

    else:

        with st.container(border=True):
            st.header("Login")

            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                response = requests.post(
                    login_url, json={"email": email, "password": password}
                )

                if response.status_code == 200:
                    st.session_state.ROOT_ID = response.json()["user"]["root_id"]
                    st.session_state.TOKEN = response.json()["token"]
                    st.session_state.EXPIRATION = response.json()["user"]["expiration"]
                    st.rerun()


def main() -> None:
    """Main function to render the Streamlit app."""
    hide_sidebar = st.query_params.get("hide_sidebar")
    router = StreamlitRouter()

    # Initialize session state
    for key in [
        "messages",
        "session_id",
        "agents",
        "actions_data",
        "TOKEN",
        "ROOT_ID",
        "EXPIRATION",
    ]:
        if key not in st.session_state:
            if key == "messages":
                st.session_state[key] = {}
            else:
                st.session_state[key] = [] if key in ["actions_data"] else ""

    if hide_sidebar == "true":
        st.markdown(
            """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
            [data-testid="stSidebarCollapsedControl"] {
                display: none;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

    # Setup the sidebar
    with st.sidebar:
        st.title("✧ JIVAS Manager")
        # retrieve agent list
        agents = call_list_agents()

        try:
            selected_agent_id = st.query_params["agent"]
        except KeyError:
            st.query_params["agent"] = agents[0]["id"] if agents else None
            selected_agent_id = st.query_params["agent"]

        selected_agent_index = next(
            (i for i, item in enumerate(agents) if item["id"] == selected_agent_id),
            len(agents) - 1 if agents else None,
        )

        # Render the ComboBox using streamlit-elements
        st.sidebar.selectbox(
            "Agent",
            agents,
            index=selected_agent_index,
            placeholder="Select agent...",
            format_func=lambda x: x["label"] if "label" in x else x,
            on_change=handle_agent_selection,
            key="selected_agent",
        )

        # Expander for the menu
        with st.expander("Menu", True):
            Page(router).item(analytics_page.render, "Dashboard", "/").st_button()
            Page(router).item(chat_page.render, "Chat", "/chat").st_button()
            Page(router).item(
                action_dashboard_page.render, "Actions", "/actions"
            ).st_button()
            Page(router).item(graph_page.render, "Graph", "/graph").st_button()
            st.button(
                "Logout",
                on_click=action_dashboard_page.logout,
                use_container_width=True,
            )

        with st.expander("Action Apps", False):
            if selected_agent_id and (
                actions_data := call_list_actions(agent_id=selected_agent_id)
            ):
                st.session_state.actions_data = actions_data

                # Sort actions_data alphabetically by the action's title
                actions_data.sort(
                    key=lambda action: action.get("_package", {})
                    .get("meta", {})
                    .get("title", "")
                )

                for action in actions_data:
                    package = action.get("_package", {})

                    if package.get("config", {}).get("app", False):
                        func = load_function(
                            f"{package['config']['path']}/app/app.py",
                            "render",
                            router=router,
                            agent_id=selected_agent_id,
                            action_id=action["id"],
                            info=package,
                        )
                        # register the route to the app
                        Page(router).item(
                            callback=func,
                            label=package["meta"]["title"],
                            path=f'/{Page.normalize_label(package["meta"]["title"])}',
                        ).st_button()
    router.serve()


# Initialize Streamlit app config
if __name__ == "__main__":
    token_query = st.query_params.get("token")
    if token_query:
        st.session_state.TOKEN = token_query

    if "TOKEN" not in st.session_state:
        st.set_page_config(page_title="JIVAS Manager", page_icon="💠")
        login_form()
    else:
        st.set_page_config(page_title="JIVAS Manager", page_icon="💠", layout="wide")
        main()
