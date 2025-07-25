"""Tests for the basic functionality of the `render` function."""

from typing import Any
from unittest.mock import Mock, patch

from fixtures.app.app import render  # import your render


def test_render_basic() -> None:
    """Test that render calls expected dependencies with correct arguments."""
    router = Mock()
    agent_id = "A"
    action_id = "B"
    info: dict[str, Any] = {}

    with patch("fixtures.app.app.app_header") as m_header, patch(
        "fixtures.app.app.app_controls"
    ) as m_controls, patch("fixtures.app.app.app_update_action") as m_update:
        m_header.return_value = ("model", "module")
        render(router, agent_id, action_id, info)
        m_header.assert_called_once_with(agent_id, action_id, info)
        m_controls.assert_called_once_with(agent_id, action_id)
        m_update.assert_called_once_with(agent_id, action_id)
