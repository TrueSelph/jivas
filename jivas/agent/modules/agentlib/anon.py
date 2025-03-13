"""This module provides functionality to anonymize sensitive information in text."""

import logging
import re
import subprocess

import spacy


class Anon:
    """Class to handle anonymization of sensitive information in text."""

    def __init__(self) -> None:
        """Initialize the Anon class and load the spaCy model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logging.error(f"Error loading spacy model: {e}")
            subprocess.call("python -m spacy download en_core_web_sm", shell=True)
            self.nlp = spacy.load("en_core_web_sm")

        # Precompile regular expressions for better performance
        self.email_regex = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        self.credit_card_regex = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

        # Default mapping of Spacy NER tags to custom sensitive information types
        self.info_type_mapping = {
            "PERSON": "PERSON",
            "CARDINAL": "NUMBER",  # Compromise for phone numbers
            "QUANTITY": "NUMBER",  # Compromise for phone numbers
            "GPE": "LOCATION",
        }
