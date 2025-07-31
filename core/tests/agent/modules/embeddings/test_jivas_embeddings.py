"""Tests for jivas.agent.modules.embeddings.jivas_embeddings."""

import json

from pytest_mock import MockerFixture

from jivas.agent.modules.embeddings.jivas_embeddings import JivasEmbeddings


class TestJivasEmbeddings:
    """Test class for JivasEmbeddings."""

    # Initialization with default model creates a valid JivasEmbeddings instance
    def test_init_with_default_model(self, mocker: MockerFixture) -> None:
        """Test that initialization with default model creates a valid JivasEmbeddings instance."""
        # Arrange
        base_url = "https://api.example.com"
        api_key = "test_api_key"  # pragma: allowlist secret

        # Act
        embeddings = JivasEmbeddings(base_url=base_url, api_key=api_key)

        # Assert
        assert embeddings.model == "intfloat/multilingual-e5-large-instruct"
        assert embeddings.model_name == "intfloat-multilingual-e5-large-instruct"
        assert embeddings.base_url == base_url
        assert embeddings.api_key == api_key
        assert embeddings.client is not None
        assert embeddings.tokenizer is not None
        assert embeddings.token_limit > 0

    def test_trim_text_if_needed_trims_exceeding_text(
        self, mocker: MockerFixture
    ) -> None:
        """Test that trim_text_if_needed correctly trims text exceeding token limit."""
        # Arrange
        mock_tokenizer = mocker.patch("transformers.AutoTokenizer.from_pretrained")
        mock_tokenizer_instance = mock_tokenizer.return_value
        mock_tokenizer_instance.model_max_length = 5
        mock_tokenizer_instance.return_tensors = "pt"
        mock_tokenizer_instance.side_effect = lambda text, return_tensors: {
            "input_ids": [[1, 2, 3, 4, 5, 6, 7]]
        }
        mock_tokenizer_instance.decode.return_value = "trimmed text"

        jivas_embeddings = JivasEmbeddings(
            base_url="http://example.com",
            api_key="dummy_key",  # pragma: allowlist secret
        )

        # Act
        result = jivas_embeddings.trim_text_if_needed(
            "This is a long text that needs trimming"
        )

        # Assert
        assert result == "trimmed text"

    def test_trim_text_if_needed_does_not_trim(self, mocker: MockerFixture) -> None:
        """Test that trim_text_if_needed does not trim text within token limit."""
        # Arrange
        mock_tokenizer = mocker.patch("transformers.AutoTokenizer.from_pretrained")
        mock_tokenizer_instance = mock_tokenizer.return_value
        mock_tokenizer_instance.model_max_length = 10
        mock_tokenizer_instance.return_tensors = "pt"
        mock_tokenizer_instance.side_effect = lambda text, return_tensors: {
            "input_ids": [[1, 2, 3, 4, 5]]
        }
        mock_tokenizer_instance.decode.return_value = "This is a long text"

        jivas_embeddings = JivasEmbeddings(
            base_url="http://example.com",
            api_key="dummy_key",  # pragma: allowlist secret
        )

        # Act
        result = jivas_embeddings.trim_text_if_needed("This is a long text")

        # Assert
        assert result == "This is a long text"

    def test_embed_documents_success(self, mocker: MockerFixture) -> None:
        """Test that embed_documents successfully embeds documents and returns embeddings."""

        # Arrange
        mock_client = mocker.patch(
            "jivas.agent.modules.embeddings.jivas_embeddings.OpenAI"
        )
        mock_instance = mock_client.return_value
        mock_response = mocker.Mock()
        mock_response.json.return_value = json.dumps(
            {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        )
        mock_instance.embeddings.create.return_value = mock_response

        jivas_embeddings = JivasEmbeddings(
            base_url="http://example.com",
            api_key="dummy_key",  # pragma: allowlist secret
        )

        # Act
        result = jivas_embeddings.embed_documents(["text1", "text2"])

        # Assert
        assert result == [[0.1, 0.2, 0.3]]

    def test_embed_documents_handle_overflow(self, mocker: MockerFixture) -> None:
        """Test that embed_documents handles overflow by trimming text."""
        # Arrange
        mock_client = mocker.patch(
            "jivas.agent.modules.embeddings.jivas_embeddings.OpenAI"
        )
        mock_instance = mock_client.return_value
        mock_response = mocker.Mock()
        mock_response.json.return_value = json.dumps(
            {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        )
        mock_instance.embeddings.create.return_value = mock_response

        mock_tokenizer = mocker.patch("transformers.AutoTokenizer.from_pretrained")
        mock_tokenizer_instance = mock_tokenizer.return_value
        mock_tokenizer_instance.return_tensors = "pt"
        mock_tokenizer_instance.side_effect = lambda text, return_tensors: {
            "input_ids": [[1, 2, 3, 4, 5, 6, 7]]
        }
        mock_tokenizer_instance.model_max_length = 5
        mock_tokenizer_instance.decode.return_value = "trimmed text"

        jivas_embeddings = JivasEmbeddings(
            base_url="http://example.com",
            api_key="dummy_key",  # pragma: allowlist secret
        )

        # Act
        result = jivas_embeddings.embed_documents(
            ["This is a long text that needs trimming"], handle_overflow=True
        )

        # Assert
        assert result == [[0.1, 0.2, 0.3]]

    def test_embed_documents_handles_exception(self, mocker: MockerFixture) -> None:
        """Test that embed_documents handles exceptions and returns an empty list."""
        # Arrange
        mock_client = mocker.patch(
            "jivas.agent.modules.embeddings.jivas_embeddings.OpenAI"
        )
        mock_instance = mock_client.return_value
        mock_instance.embeddings.create.side_effect = Exception("API error")

        jivas_embeddings = JivasEmbeddings(
            base_url="http://example.com",
            api_key="dummy_key",  # pragma: allowlist secret
        )

        # Act
        result = jivas_embeddings.embed_documents(["text1", "text2"])

        # Assert
        assert result == []

    def test_embed_query_success(self, mocker: MockerFixture) -> None:
        """Test that embed_query successfully embeds query text and returns embedding vector."""
        # Arrange
        mock_client = mocker.patch(
            "jivas.agent.modules.embeddings.jivas_embeddings.OpenAI"
        )
        mock_instance = mock_client.return_value
        mock_response = mocker.Mock()
        mock_response.json.return_value = json.dumps(
            {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        )
        mock_instance.embeddings.create.return_value = mock_response

        jivas_embeddings = JivasEmbeddings(
            base_url="http://example.com",
            api_key="dummy_key",  # pragma: allowlist secret
        )

        # Act
        result = jivas_embeddings.embed_query("test query")

        # Assert
        assert result == [0.1, 0.2, 0.3]
        mock_instance.embeddings.create.assert_called_once_with(
            input="test query", model=jivas_embeddings.model_name
        )

    def test_embed_query_handles_overflow(self, mocker: MockerFixture) -> None:
        """Test that embed_query handles text overflow correctly."""
        # Arrange
        mock_client = mocker.patch(
            "jivas.agent.modules.embeddings.jivas_embeddings.OpenAI"
        )
        mock_instance = mock_client.return_value
        mock_response = mocker.Mock()
        mock_response.json.return_value = json.dumps(
            {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        )
        mock_instance.embeddings.create.return_value = mock_response

        mock_tokenizer = mocker.patch("transformers.AutoTokenizer.from_pretrained")
        mock_tokenizer_instance = mock_tokenizer.return_value
        mock_tokenizer_instance.return_tensors = "pt"
        mock_tokenizer_instance.side_effect = lambda text, return_tensors: {
            "input_ids": [[1, 2, 3, 4, 5, 6, 7]]
        }
        mock_tokenizer_instance.decode.return_value = "trimmed text"

        jivas_embeddings = JivasEmbeddings(
            base_url="http://example.com",
            api_key="dummy_key",  # pragma: allowlist secret
        )
        jivas_embeddings.token_limit = 5

        # Act
        result = jivas_embeddings.embed_query(
            "This is a long text that needs trimming", handle_overflow=True
        )

        # Assert
        assert result == [0.1, 0.2, 0.3]

    def test_embed_query_handles_exception(self, mocker: MockerFixture) -> None:
        """Test that embed_query handles exceptions and returns an empty list."""
        # Arrange
        mock_client = mocker.patch(
            "jivas.agent.modules.embeddings.jivas_embeddings.OpenAI"
        )
        mock_instance = mock_client.return_value
        mock_instance.embeddings.create.side_effect = Exception("API error")

        jivas_embeddings = JivasEmbeddings(
            base_url="http://example.com",
            api_key="dummy_key",  # pragma: allowlist secret
        )

        # Act
        result = jivas_embeddings.embed_query("test text")

        # Assert
        assert result == []
