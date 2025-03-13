"""Unit tests for the Anon class in the agentlib module."""

from pytest_mock import MockerFixture

from jivas.agent.modules.agentlib.anon import Anon


class TestAnon:
    """Unit tests for the Anon class."""

    def test_init_loads_spacy_model_successfully(self, mocker: MockerFixture) -> None:
        """Test that Anon successfully initializes with spaCy model loaded on first attempt."""
        # Arrange
        mock_spacy_load = mocker.patch("spacy.load")
        mock_nlp = mocker.MagicMock()
        mock_spacy_load.return_value = mock_nlp

        # Act
        anon = Anon()

        # Assert
        mock_spacy_load.assert_called_once_with("en_core_web_sm")
        assert anon.nlp == mock_nlp
        assert anon.email_regex is not None
        assert anon.credit_card_regex is not None
        assert "PERSON" in anon.info_type_mapping
        assert anon.info_type_mapping["PERSON"] == "PERSON"

    def test_init_handles_spacy_model_load_failure(self, mocker: MockerFixture) -> None:
        """Test that Anon handles case when spaCy model fails to load on first attempt."""
        # Arrange
        mock_spacy_load = mocker.patch("spacy.load")
        mock_subprocess_call = mocker.patch("subprocess.call")
        mock_logging = mocker.patch("logging.error")

        # Configure mock to fail on first call, succeed on second
        mock_nlp = mocker.MagicMock()
        mock_spacy_load.side_effect = [Exception("Model not found"), mock_nlp]

        # Act
        anon = Anon()

        # Assert
        assert mock_spacy_load.call_count == 2
        mock_logging.assert_called_once()
        mock_subprocess_call.assert_called_once_with(
            "python -m spacy download en_core_web_sm", shell=True
        )
        assert anon.nlp == mock_nlp
        assert anon.email_regex is not None
        assert anon.credit_card_regex is not None
