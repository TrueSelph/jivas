"""Test Streamlit app."""

from streamlit_router import StreamlitRouter

from jvcli.client.lib.widgets import app_controls, app_header, app_update_action


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """Render the streamlit app."""
    (model_key, action) = app_header(agent_id, action_id, info)
    app_controls(agent_id, action_id)
    app_update_action(agent_id, action_id)
