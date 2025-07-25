"""Render the action_dashboard page of the jvclient with actions data."""

import streamlit as st
from streamlit_elements import dashboard, elements, mui
from streamlit_router import StreamlitRouter

from jvcli.client.lib.page import Page


def render(router: StreamlitRouter) -> None:
    """Render the dashboard page."""
    if actions_data := st.session_state.get("actions_data"):
        with elements("action_dashboard"):
            columns = 4
            layout = []

            # Compute the position of each card component in the layout
            for idx, _ in enumerate(actions_data):
                x = (idx % columns) * 3
                y = (idx // columns) * 2
                width = 3
                height = 2
                # Add an item to the action_dashboard manually without using `with` if it's not a context manager
                layout.append(
                    dashboard.Item(
                        f"card_{idx}",
                        x,
                        y,
                        width,
                        height,
                        isDraggable=False,
                        isResizable=False,
                    )
                )

            # now populate the actual cards with content
            with dashboard.Grid(layout):
                for idx, action in enumerate(actions_data):

                    package = action.get("_package", {})
                    title = package.get("meta", {}).get("title", action.get("label"))
                    description = action.get("description", "")
                    version = package.get("version", "0.0.0")
                    action_type = package.get("meta", {}).get("type", "action")
                    key = Page.normalize_label(title)
                    enabled_color = "red"
                    enabled_text = "(disabled)"
                    avatar_text = "A"

                    if action_type == "interact_action":
                        avatar_text = "I"

                    if action.get("enabled", False):
                        enabled_color = "green"
                        enabled_text = ""

                    # create the card
                    with mui.Card(
                        key=f"card_{idx}",
                        sx={
                            "display": "flex",
                            "flexDirection": "column",
                            "borderRadius": 2,
                            "overflow": "scroll",
                        },
                        elevation=2,
                    ):
                        # Card header with title
                        mui.CardHeader(
                            title=f"{title} {enabled_text}",
                            subheader=f"{version}",
                            avatar=mui.Avatar(
                                avatar_text, sx={"bgcolor": enabled_color}
                            ),
                            action=mui.IconButton(mui.icon.MoreVert),
                        )

                        # Card body
                        with mui.CardContent(sx={"flex": 1}):
                            mui.Typography(description, variant="body2")

                        # Card footer with action buttons
                        with mui.CardActions(disableSpacing=True):
                            query = st.query_params.to_dict()
                            query_str = ""
                            for k, v in query.items():
                                if k != "request":
                                    query_str += f"{k}={v}&"

                            if package.get("config", {}).get("app", False):
                                with mui.Stack(
                                    direction="row",
                                    spacing=2,
                                    alignItems="center",
                                    sx={"padding": "10px"},
                                ):
                                    mui.Button(
                                        "Configure",
                                        variant="outlined",
                                        href=(
                                            (
                                                f"/?request=GET:/{key}&${query_str.rstrip('&')}"
                                                if query_str
                                                else f"/?request=GET:/{key}"
                                            )
                                            + f"&token={st.session_state.TOKEN}"
                                        ),
                                        target="_blank",
                                    )


def logout() -> None:
    """Logout the user by clearing the session token."""
    del st.session_state["TOKEN"]
    token_query = st.query_params.get("token")

    if token_query:
        query_params = st.query_params.to_dict()
        del query_params["token"]
        st.query_params.from_dict(query_params)
