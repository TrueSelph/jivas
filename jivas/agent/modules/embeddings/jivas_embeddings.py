from typing import List
from openai import OpenAI
from langchain_core.embeddings import Embeddings
import json

# NOTE: IF WE REQUIRE OVERFLOW HANDLING, WE NEED TO INSTALL PYTORCH AND SET HANDLE_OVERFLOW TO TRUE
class JivasEmbeddings(Embeddings):
    def __init__(self, base_url: str, api_key: str, model: str = "intfloat-multilingual-e5-large-instruct"):
        # init args
        self.model = model
        self.base_url = base_url
        self.api_key = api_key

        # create client
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # Load the tokenizer
        self.tokenizer = None # AutoTokenizer.from_pretrained('intfloat/multilingual-e5-large-instruct')

    def trim_text_if_needed(self, text: str):
        tokenized = self.tokenizer(text, return_tensors="pt")
        num_tokens = len(tokenized["input_ids"][0])

        if num_tokens > 512:
            truncated_tokens = tokenized["input_ids"][0][:512]
            return self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
        
        return False  # Indicates text is within the limit

    def embed_documents(self, texts: List[str], handle_overflow: bool = False) -> List[List[float]]:
        """Embed search docs."""
        # grab embeddings
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )

        # set response to json
        response = json.loads(response.json())

        # handle overflow
        if handle_overflow:
            # use list comprehension to set trimmed text
            trimmed_texts = [trimmed if trimmed else text for text in texts if (trimmed := self.trim_text_if_needed(text)) is not False]

        # return embeddings
        return [embd["embedding"] for embd in response["data"]]

    def embed_query(self, text: str, handle_overflow: bool = False) -> List[float]:
        """Embed query text."""
        # grab embeddings
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        
        # handle overflow
        if handle_overflow:
            # trim text if needed
            trimmed_text = self.trim_text_if_needed(text)

            # check if trimmed text
            if trimmed_text:
                # set text since we trimmed it
                text = trimmed_text

        # set response to json
        response = json.loads(response.json())

        # return embeddings
        return response["data"][0]["embedding"]
