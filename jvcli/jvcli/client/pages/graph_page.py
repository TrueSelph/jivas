"""Render the Jivas Studio page in an iframe."""

import os

import streamlit as st
from streamlit_router import StreamlitRouter

JIVAS_STUDIO_URL = os.environ.get("JIVAS_STUDIO_URL", "http://localhost:8989")


def render(router: StreamlitRouter) -> None:
    """
    Render the Jivas Studio page in an iframe.

    args:
        router: StreamlitRouter
            The StreamlitRouter instance
    """

    st.components.v1.iframe(JIVAS_STUDIO_URL, width=None, height=800, scrolling=False)
