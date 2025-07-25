"""Test chat page for the JVCLI client."""

from pytest_mock import MockerFixture

from jvcli.client.lib.utils import JIVAS_BASE_URL
from jvcli.client.pages.chat_page import (
    add_agent_message,
    clear_messages,
    render,
    send_message,
    transcribe_audio,
)


class TestClientChatPage:
    """Test the JVCLI client chat page."""

    def test_transcribe_audio_success(self, mocker: MockerFixture) -> None:
        """Test transcribing audio successfully."""
        # Mock requests.post response
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"transcription": "test transcription"}
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        # Test inputs
        token = "test_token"
        agent_id = "test_agent_id"
        test_file = b"test audio bytes"

        # Call function
        result = transcribe_audio(token, agent_id, test_file)

        # Verify requests.post was called with correct params
        mock_post.assert_called_once_with(
            f"{JIVAS_BASE_URL}/action/walker",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "args": "{}",
                "module_root": "jivas.agent.action",
                "agent_id": agent_id,
                "walker": "invoke_stt_action",
            },
            files={"attachments": ("audio.wav", test_file, "audio/wav")},
        )

        # Verify response
        assert result == {"transcription": "test transcription"}

    def test_render_audio_input_and_message_sending(
        self, mocker: MockerFixture
    ) -> None:
        """Test rendering audio input and sending a message."""
        # Mock dependencies
        mocker.patch(
            "jvcli.client.pages.chat_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )
        mocker.patch("streamlit.header")
        mocker.patch("streamlit.toggle", return_value=True)
        mocker.patch("streamlit.audio_input", return_value=b"audio_data")
        mock_session_state = mocker.MagicMock()
        mock_session_state.selected_agent = {"id": "agent_1"}
        mock_session_state.messages = {"agent_1": []}
        mocker.patch("streamlit.session_state", mock_session_state)
        mocker.patch("streamlit.query_params", {"agent": "agent_1"})
        mock_transcribe_audio = mocker.patch(
            "jvcli.client.pages.chat_page.transcribe_audio",
            return_value={"success": True, "transcript": "Hello"},
        )
        mock_send_message = mocker.patch("jvcli.client.pages.chat_page.send_message")
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        # Verify transcribe_audio and send_message were called
        mock_transcribe_audio.assert_called_once_with(
            "test_token", "agent_1", b"audio_data"
        )
        mock_send_message.assert_called_once_with(
            "Hello", f"{JIVAS_BASE_URL}/interact", "test_token", "agent_1", True
        )

    def test_render_with_audio_input_and_user_input(
        self, mocker: MockerFixture
    ) -> None:
        """Test rendering with both audio input and user input."""
        # Mock dependencies
        mocker.patch(
            "jvcli.client.pages.chat_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )
        mocker.patch("streamlit.header")
        mocker.patch("streamlit.toggle", return_value=True)
        mocker.patch("streamlit.audio_input", return_value=b"audio_data")
        mocker.patch("streamlit.chat_input", return_value="Hello")
        mock_session_state = mocker.patch("streamlit.session_state", mocker.MagicMock())
        mock_session_state["selected_agent"] = "agent_1"
        mocker.patch("streamlit.session_state.messages", {"agent_1": []})
        mocker.patch("streamlit.query_params", {"agent": "agent_1"})
        mocker.patch(
            "jvcli.client.pages.chat_page.transcribe_audio",
            return_value={"success": True, "transcript": "Hello"},
        )
        mock_send_message = mocker.patch("jvcli.client.pages.chat_page.send_message")
        mock_router = mocker.Mock()

        # Call function
        render(mock_router)

        mock_send_message.assert_called_with(
            "Hello", f"{JIVAS_BASE_URL}/interact", "test_token", "agent_1", True
        )

    def test_render_with_chat_messages(self, mocker: MockerFixture) -> None:
        """Test rendering with existing chat messages."""
        # Mock dependencies
        mocker.patch(
            "jvcli.client.pages.chat_page.get_user_info",
            return_value={
                "root_id": "test_root_id",
                "token": "test_token",
                "expiration": "test_expiration",
            },
        )
        mocker.patch("streamlit.header")
        mocker.patch("streamlit.toggle", return_value=True)
        mocker.patch("streamlit.audio_input", return_value=None)
        mocker.patch("streamlit.chat_input", return_value=None)
        mock_session_state = mocker.patch("streamlit.session_state", mocker.MagicMock())
        mock_session_state.messages = {
            "agent_1": [
                {"role": "user", "content": "Hello"},
                {
                    "role": "assistant",
                    "content": "Hi there!",
                    "payload": {"key": "value"},
                },
            ]
        }
        mocker.patch("streamlit.query_params", {"agent": "agent_1"})
        mock_router = mocker.Mock()

        # Verify chat messages are displayed
        st_chat_message = mocker.patch("streamlit.chat_message")
        st_markdown = mocker.patch("streamlit.markdown")
        st_expander = mocker.patch("streamlit.expander")
        st_json = mocker.patch("streamlit.json")

        # Call function
        render(mock_router)

        st_chat_message.assert_any_call("user")
        st_markdown.assert_any_call("Hello")

        st_chat_message.assert_any_call("assistant")
        st_markdown.assert_any_call("Hi there!")

        st_expander.assert_called_once()
        st_json.assert_called_once()

    def test_send_message_success(self, mocker: MockerFixture) -> None:
        """Test sending a message successfully."""
        # Mock dependencies
        mock_add_agent_message = mocker.patch(
            "jvcli.client.pages.chat_page.add_agent_message"
        )
        mocker.patch("streamlit.chat_message")
        mock_st_markdown = mocker.patch("streamlit.markdown")
        mocker.patch("streamlit.expander")
        mocker.patch("streamlit.json")
        mock_st_audio = mocker.patch("streamlit.audio")
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_session_state.session_id = "test_session"

        # Mock requests.post response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "message": {"content": "Test response"},
                "audio_url": "http://test.audio",
                "session_id": "new_session",
            }
        }
        requests_post = mocker.patch("requests.post", return_value=mock_response)

        # Test inputs
        prompt = "Hello"
        url = "http://test.url"
        token = "test_token"
        selected_agent = "test_agent"
        tts_on = True

        # Call function
        send_message(prompt, url, token, selected_agent, tts_on)

        # Verify message was added to chat history
        mock_add_agent_message.assert_any_call(
            selected_agent, {"role": "user", "content": prompt}
        )

        # Verify API call
        requests_post.assert_called_once_with(
            url=url,
            json={
                "utterance": prompt,
                "session_id": "test_session",
                "agent_id": selected_agent,
                "tts": tts_on,
                "verbose": True,
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Verify response handling
        mock_st_markdown.assert_called_with("Test response")
        mock_st_audio.assert_called_with("http://test.audio", autoplay=True)

        # Verify assistant message was added
        mock_add_agent_message.assert_called_with(
            selected_agent,
            {
                "role": "assistant",
                "content": "Test response",
                "payload": mock_response.json(),
            },
        )

        # Verify session ID was updated
        assert mock_session_state.session_id == "new_session"

    def test_add_message_to_existing_agent(self, mocker: MockerFixture) -> None:
        """Test adding a message to an existing agent."""
        # Mock streamlit session state
        mock_session_state = mocker.patch("streamlit.session_state", mocker.MagicMock())
        mock_session_state.messages = {
            "agent_1": [{"role": "user", "content": "Hello"}]
        }

        # Test message to add
        new_message = {"role": "assistant", "content": "Hi there!"}

        # Call function
        add_agent_message("agent_1", new_message)

        # Verify message was appended to existing agent messages
        assert mock_session_state.messages["agent_1"] == [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

    def test_clear_messages_creates_empty_dict(self, mocker: MockerFixture) -> None:
        """Test clearing messages creates an empty dictionary."""
        # Mock streamlit session state
        mock_session_state = mocker.patch("streamlit.session_state", mocker.MagicMock())

        # Call function
        clear_messages()

        # Verify messages dict is empty
        assert mock_session_state.messages == {}
