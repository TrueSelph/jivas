"""Module for Jivas Embeddings."""

import json
from typing import List

from langchain_core.embeddings import Embeddings
from openai import OpenAI
from transformers import AutoTokenizer


class JivasEmbeddings(Embeddings):
    """Class for handling Jivas Embeddings."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "intfloat/multilingual-e5-large-instruct",
    ) -> None:
        """Initialize the JivasEmbeddings class."""
        # init args
        self.model = model
        self.model_name = "-".join(model.split("/"))
        self.base_url = base_url
        self.api_key = api_key

        # create client
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # Load the tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.token_limit = self.tokenizer.model_max_length

    def trim_text_if_needed(self, text: str) -> str:
        """Trim text if it exceeds the token limit."""
        tokenized = self.tokenizer(text, return_tensors="pt")
        num_tokens = len(tokenized["input_ids"][0])

        if num_tokens > self.token_limit:
            truncated_tokens = tokenized["input_ids"][0][: self.token_limit]
            return self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)

        return text

    def embed_documents(
        self, texts: List[str], handle_overflow: bool = False
    ) -> List[List[float]]:
        """Embed search documents."""
        if handle_overflow:
            texts = [self.trim_text_if_needed(text) for text in texts]

        try:
            # grab embeddings
            response = self.client.embeddings.create(input=texts, model=self.model_name)
            # set response to json
            response = json.loads(response.json())
            # return embeddings
            return [embd["embedding"] for embd in response["data"]]
        except Exception as e:
            # Handle potential errors
            print(f"Error embedding documents: {e}")
            return []

    def embed_query(self, text: str, handle_overflow: bool = False) -> List[float]:
        """Embed query text."""
        if handle_overflow:
            text = self.trim_text_if_needed(text)

        try:
            # grab embeddings
            response = self.client.embeddings.create(input=text, model=self.model_name)
            # set response to json
            response = json.loads(response.json())
            # return embeddings
            return response["data"][0]["embedding"]
        except Exception as e:
            # Handle potential errors
            print(f"Error embedding query: {e}")
            return []
