"""Renders the chat page for the JVCLI client."""

import os
from typing import Optional

import requests
import streamlit as st
from streamlit_router import StreamlitRouter

from jvcli.client.lib.utils import get_user_info

JIVAS_BASE_URL = os.environ.get("JIVAS_BASE_URL", "http://localhost:8000")


def transcribe_audio(token: str, agent_id: str, file: bytes) -> dict:
    """Transcribe audio using the walker API."""
    action_walker_url = f"{JIVAS_BASE_URL}/action/walker"

    # Create form data
    files = {"attachments": ("audio.wav", file, "audio/wav")}

    data = {
        "args": "{}",
        "module_root": "jivas.agent.action",
        "agent_id": agent_id,
        "walker": "invoke_stt_action",
    }

    headers = {"Authorization": f"Bearer {token}"}

    # Make the POST request
    response = requests.post(
        f"{action_walker_url}", headers=headers, data=data, files=files
    )

    # Parse JSON response
    result = response.json()
    return result


def render(router: StreamlitRouter) -> None:
    """Render the chat page."""
    url = f"{JIVAS_BASE_URL}/interact"
    ctx = get_user_info()

    st.header("Chat", divider=True)
    tts_on = st.toggle("TTS")

    message = ""
    # Handle audio input first
    audio_value = st.audio_input("Record a voice message")
    # Get selected agent from query params
    selected_agent = st.query_params.get("agent")

    if selected_agent:
        chat_messages = st.session_state.messages.get(selected_agent, [])

        # Display chat messages from history on app rerun
        for item in chat_messages:
            role = item.get("role", "user")
            content = item.get("content", "")
            with st.chat_message(role):
                st.markdown(content)
                if payload := item.get("payload"):
                    with st.expander("...", False):
                        st.json(payload)

    # Process audio input if available
    if audio_value and selected_agent:
        result = transcribe_audio(ctx["token"], selected_agent, audio_value)
        if result and result.get("success", False):
            message = result["transcript"]

    # Otherwise handle text input
    if input := st.chat_input("Type your message here"):
        message = input

    if message:
        send_message(message, url, ctx["token"], selected_agent, tts_on)


def send_message(
    prompt: str,
    url: str,
    token: str,
    selected_agent: Optional[str] = None,
    tts_on: bool = False,
) -> None:
    """Send a message to the walker API and display the response."""
    # Add user message to chat history
    add_agent_message(selected_agent, {"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Call walker API
        response = requests.post(
            url=url,
            json={
                "utterance": prompt,
                "session_id": st.session_state.session_id,
                "agent_id": selected_agent,
                "tts": tts_on,
                "verbose": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            if response_data := response.json():
                st.markdown(
                    response_data.get("response", {})
                    .get("message", {})
                    .get("content", "...")
                )
                if "audio_url" in response_data.get("response", {}) and tts_on:
                    audio_url = response_data.get("response", {}).get(
                        "audio_url", "..."
                    )
                    st.audio(audio_url, autoplay=True)
                with st.expander("...", False):
                    st.json(response_data)

                # Add assistant response to chat history
                add_agent_message(
                    selected_agent,
                    {
                        "role": "assistant",
                        "content": response_data.get("response", {})
                        .get("message", {})
                        .get("content", "..."),
                        "payload": response_data,
                    },
                )
            if "session_id" in response_data.get("response", {}):
                st.session_state.session_id = response_data["response"]["session_id"]


def add_agent_message(agent_id: Optional[str], message: dict) -> None:
    """Add a message to the chat history for a specific agent."""
    all_messages = st.session_state.messages
    agent_messages = all_messages.get(agent_id, [])
    agent_messages.append(message)
    st.session_state.messages[agent_id] = agent_messages


def clear_messages() -> None:
    """Clear all chat messages."""
    st.session_state.messages = {}
