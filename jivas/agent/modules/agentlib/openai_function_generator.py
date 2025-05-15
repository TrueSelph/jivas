"""Module for generating OpenAI tool functions from structured question indices.

This module provides the OpenAIFunctionGenerator class which converts structured
interview questions with metadata into OpenAI-compatible function definitions
with proper validation and type handling.
"""

from typing import Any, Dict, List, TypedDict


class ExtractionGuidance(TypedDict, total=False):
    """Type definition for extraction guidance metadata"""

    description: str
    type: str
    examples: List[str]
    validation: Dict[str, Any]
    required: bool
    fallback_phrases: List[str]
    response_rules: str
    edge_cases: List[Dict[str, str]]


class QuestionData(TypedDict, total=False):
    """Type definition for question data structure"""

    question: str
    extraction_guidance: ExtractionGuidance


class OpenAIFunctionGenerator:
    """
    Generates OpenAI tool functions from a structured question index
    with enhanced validation and metadata support.

    Attributes:
        question_index (Dict[str, QuestionData]): Structured interview questions with extraction metadata
        allowed_types (Dict): Type validation rules and coercion handlers
    """

    ALLOWED_TYPES: dict = {
        "string": {
            "coerce": str,
            "validation": {"maxLength": 255},
            "description_add": "Text response",
        },
        "integer": {
            "coerce": int,
            "validation": {"minimum": 0, "maximum": 150},
            "description_add": "Numeric value",
        },
        "date": {
            "coerce": "iso8601",
            "validation": {"pattern": r"^\d{4}-\d{2}-\d{2}$"},
            "description_add": "ISO 8601 date (YYYY-MM-DD)",
        },
    }

    def __init__(self, question_index: Dict[str, QuestionData]) -> None:
        """Initialize the OpenAIFunctionGenerator with a question index.

        Args:
            question_index: Dictionary containing structured interview questions
                          with extraction metadata
        """
        self.question_index = question_index
        self._validate_structure()

    def _validate_structure(self) -> None:
        """Ensures question index contains required metadata"""
        for key, data in self.question_index.items():
            if "extraction_guidance" not in data:
                continue

            eg = data["extraction_guidance"]
            if eg.get("type", "string") not in self.ALLOWED_TYPES:
                raise ValueError(f"Invalid type {eg['type']} for {key}")

    def _build_description(self, question_data: QuestionData) -> str:
        """Constructs a high-quality function description optimized for LLM function calling.

        Follows these principles:
        1. Starts with a clear action verb and scope
        2. Explicitly defines trigger conditions
        3. Includes examples and edge cases
        4. Uses natural language keywords
        5. Avoids ambiguity

        Args:
            question_data: Contains question metadata and extraction rules

        Returns:
            str: Description optimized for OpenAI function calling
        """
        q = question_data
        eg = q["extraction_guidance"]

        # Core description components
        description_parts = [
            # Primary action and scope
            f"Extract {eg['description']} from user responses. ",
            f"Pay attention to responses to: '{q['question']}'. ",
            # Input handling
            f"Processes: {self._format_phrases(eg.get('fallback_phrases', ['explicit answers']))}. ",
            # Output specification
            "Returns structured data matching the expected format. ",
        ]

        # Add examples if provided
        if "examples" in eg:
            formatted_examples = self._format_examples(eg["examples"])
            description_parts.append(f"Example conversions: {formatted_examples}. ")

        # Add rules if provided
        if "response_rules" in eg:
            description_parts.append(
                f"Strict rules: {self._format_rules(eg['response_rules'])}. "
            )

        # Add edge case handling
        if "edge_cases" in eg:
            description_parts.append(
                f"Ignores: {self._format_edge_cases(eg['edge_cases'])}. "
            )

        # Compose final description
        return "".join(description_parts).strip()

    # Helper functions for clean formatting
    def _format_phrases(self, phrases: list) -> str:
        """Formats recognition phrases for natural reading"""
        if len(phrases) == 1:
            return phrases[0]
        return f"{', '.join(phrases[:-1])}, and {phrases[-1]}"

    def _format_examples(self, examples: list) -> str:
        """Formats examples with clear before/after structure"""
        return "; ".join(f"'{ex['input']}' → {ex['output']}" for ex in examples)

    def _format_rules(self, rules: str) -> str:
        """Simplifies complex rules for description"""
        return rules.replace("\n", "; ").replace("  ", " ")

    def _format_edge_cases(self, cases: list) -> str:
        """Formats edge cases with explanations"""
        return ", ".join(f"'{case['example']}' ({case['reason']})" for case in cases)

    def _build_response_property(self, field_data: QuestionData) -> Dict[str, Any]:
        """Constructs the response property schema with validation

        Args:
            field_data: Dictionary containing field metadata

        Returns:
            Dict: Schema definition for the response property
        """
        eg = field_data["extraction_guidance"]
        prop: Dict[str, Any] = {
            "type": eg["type"],
            "description": (
                f"{eg['description']}. "
                f"{self.ALLOWED_TYPES[eg['type']]['description_add']}"
            ),
        }

        # Add type-specific validation
        validation = eg.get("validation", {})
        prop.update(self.ALLOWED_TYPES[eg["type"]]["validation"])
        prop.update(validation)

        # Add examples if provided
        if "examples" in eg:
            prop["examples"] = eg["examples"]

        return prop

    def generate_openai_functions(self) -> List[Dict[str, Any]]:
        """Generates OpenAI-compatible function definitions

        Returns:
            List[Dict]: List of OpenAI function definitions
        """
        functions: List[Dict[str, Any]] = []

        for field_key, field_data in self.question_index.items():
            if("extraction_guidance" in field_data):
                eg = field_data["extraction_guidance"]

                function_def = {
                    "type": "function",
                    "function": {
                        "name": field_key,
                        "description": self._build_description(field_data),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "response": self._build_response_property(field_data),
                                "confidence": {
                                    "type": "number",
                                    "description": "Extraction confidence score 0-1",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                            },
                            "required": (
                                ["response", "confidence"]
                                if eg.get("required", False)
                                else ["confidence"]
                            ),
                        },
                    },
                }

                functions.append(function_def)

        return functions


"""

        # Question index items can be specified as show below:

        {
            "full_name": {
                "question": "What is your full name?",
                "extraction_guidance": {
                    "description": "User's complete legal name with optional middle name",
                    "type": "string",
                    "format": "First Middle Last",
                    "examples": ["John Michael Doe", "Jane A. Smith"],
                    "validation": {
                        "min_words": 2,
                        "max_words": 4,
                        "allowed_characters": "a-zA-Z-' ."
                    },
                    "required": True,
                    "fallback_phrases": ["My name is", "I'm called", "People know me as"]
                }
            },
            "age": {
                "question": "How old are you?",
                "extraction_guidance": {
                    "description": "Current age in whole years since birth",
                    "type": "integer",
                    "range": {"min": 0, "max": 120},
                    "response_rules": "Convert verbal approximations ('early 30s') to specific numbers",
                    "required": True
                }
            }
        }

"""
