"""Module for parsing and evaluating conditional expressions."""

import contextlib
import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG) # Uncomment for detailed parsing logs


def parse_condition_string(
    condition_str: str,
) -> Optional[List[Union[str, bool, List[str]]]]:
    """Parse a single condition string into its components.

    Args:
        condition_str: The condition string to parse.

    Returns:
        A list containing [field_name, operator, value] where value can be str, bool, or List[str],
        or None if parsing fails.
    """
    condition_str = condition_str.strip()

    patterns = {
        "range": r"^([\w.-]+)\s*:\s*\[\s*([\d.-]+)\s*\.\.\s*([\d.-]+)\s*\]$",
        "not_in_list": r"^([\w.-]+)\s*:\s*!\[\s*([^\]]*?)\s*\]$",
        "in_list": r"^([\w.-]+)\s*:\s*\[\s*([^\]]*?)\s*\]$",
        "exact_not_equal": r"^([\w.-]+)\s*!:=\s*(.+)$",
        "not_equal": r"^([\w.-]+)\s*!=\s*(.+)$",
        "exact_equal": r"^([\w.-]+)\s*:=\s*(.+)$",
        "greater_equal": r"^([\w.-]+)\s*>=\s*([\d.-]+)$",
        "less_equal": r"^([\w.-]+)\s*<=\s*([\d.-]+)$",
        "greater_than": r"^([\w.-]+)\s*>\s*([\d.-]+)$",
        "less_than": r"^([\w.-]+)\s*<\s*([\d.-]+)$",
        "partial_equal": r"^([\w.-]+)\s*:\s*(.+)$",
        "simple_equal": r"^([\w.-]+)\s*=\s*(.+)$",
    }

    op_mapping = {
        "range": "[..]",
        "not_in_list": "![]",
        "in_list": "[]",
        "exact_not_equal": "!=",
        "not_equal": "!=",
        "exact_equal": ":=",
        "greater_equal": ">=",
        "less_equal": "<=",
        "greater_than": ">",
        "less_than": "<",
        "partial_equal": ":",
        "simple_equal": "=",
    }

    for op_key, pattern in patterns.items():
        match = re.fullmatch(pattern, condition_str)
        if not match:
            continue

        field = match.group(1).strip()
        operator_symbol = op_mapping[op_key]

        if op_key == "range":
            val1 = match.group(2).strip()
            val2 = match.group(3).strip()
            return [field, operator_symbol, [val1, val2]]
        if op_key in ["in_list", "not_in_list"]:
            values_str = match.group(2).strip()
            values = (
                [v.strip() for v in values_str.split(",") if v.strip()]
                if values_str
                else []
            )
            return [field, operator_symbol, values]

        value_str = match.group(2).strip()
        if value_str.lower() == "true":
            value: Union[str, bool] = True
        elif value_str.lower() == "false":
            value = False
        else:
            value = value_str
        return [field, operator_symbol, value]

    logger.warning(
        f"Could not parse condition part: '{condition_str}' with any known pattern."
    )
    return None


def evaluate_single_condition(
    parsed_condition: Sequence[Union[str, bool, List[str]]], responses: Dict[str, Any]
) -> bool:
    """Evaluate a single parsed condition against response data.

    Args:
        parsed_condition: The parsed condition as [field, operator, value] where value can be str, bool, or List[str].
        responses: Dictionary of response data to evaluate against.

    Returns:
        bool: The result of the evaluation.
    """
    if not parsed_condition or len(parsed_condition) < 3:
        logger.warning(f"Invalid parsed condition structure: {parsed_condition}")
        return False

    field_name = parsed_condition[0]
    operator = parsed_condition[1]
    expected_value = parsed_condition[2]

    if not isinstance(field_name, str):
        logger.warning(f"Field name is not a string: {field_name}")
        return False

    actual_value_from_responses = responses.get(field_name)
    if actual_value_from_responses is None:
        if operator == "!=":
            return True
        if operator == "![]":
            return True
        logger.warning(f"Field '{field_name}' not found in responses.")
        return False

    actual_value_str = str(actual_value_from_responses)

    try:
        if operator in (">", "<", ">=", "<="):
            if not isinstance(expected_value, str):
                logger.warning(f"Expected value is not a string: {expected_value}")
                return False
            actual_val_num = float(actual_value_str)
            expected_val_num = float(expected_value)
            if operator == ">":
                return actual_val_num > expected_val_num
            if operator == "<":
                return actual_val_num < expected_val_num
            if operator == ">=":
                return actual_val_num >= expected_val_num
            if operator == "<=":
                return actual_val_num <= expected_val_num

        if operator == "[..]":
            if not isinstance(expected_value, list) or len(expected_value) != 2:
                logger.warning(
                    f"Expected value for range is not a list of two: {expected_value}"
                )
                return False
            actual_val_num = float(actual_value_str)
            min_val = float(expected_value[0])
            max_val = float(expected_value[1])
            return min_val <= actual_val_num <= max_val

        if operator in ("=", ":="):
            if isinstance(expected_value, bool):
                return actual_value_str.lower() == str(expected_value).lower()
            with contextlib.suppress(ValueError):
                if (
                    isinstance(expected_value, str)
                    and expected_value.replace(".", "", 1).lstrip("-").isdigit()
                ):
                    return float(actual_value_str) == float(expected_value)
            return actual_value_str == str(expected_value)

        if operator == "!=":
            if isinstance(expected_value, bool):
                return actual_value_str.lower() != str(expected_value).lower()
            with contextlib.suppress(ValueError):
                if (
                    isinstance(expected_value, str)
                    and expected_value.replace(".", "", 1).lstrip("-").isdigit()
                ):
                    return float(actual_value_str) != float(expected_value)
            return actual_value_str != str(expected_value)

        if operator == ":":
            return str(expected_value).lower() in actual_value_str.lower()

        if operator == "[]":
            if not isinstance(expected_value, list):
                return False
            return actual_value_str in [str(v) for v in expected_value]

        if operator == "![]":
            if not isinstance(expected_value, list):
                return True
            return actual_value_str not in [str(v) for v in expected_value]

    except ValueError as e:
        logger.warning(
            f"Type error during evaluation: field='{field_name}', op='{operator}', "
            f"actual='{actual_value_str}', expected='{expected_value}'. Error: {e}"
        )
        return False

    logger.warning(f"Unhandled operator '{operator}' for field '{field_name}'")
    return False


def evaluate_conditional_expression(expression: str, responses: Dict[str, Any]) -> bool:
    """Evaluate a conditional expression with AND, OR, and parentheses.

    Args:
        expression: The conditional expression to evaluate.
        responses: Dictionary of response data to evaluate against.

    Returns:
        bool: The result of the evaluation.
    """
    expression = expression.strip()
    if not expression:
        return True

    # Check if this is just a boolean literal (from parentheses processing)
    if expression == "true":
        return True
    if expression == "false":
        return False

    # Check if this is a simple condition (no operators)
    if "&&" not in expression and "||" not in expression and "(" not in expression:
        # Simple condition - parse and evaluate directly
        parsed = parse_condition_string(expression)
        if parsed is None:
            return False
        return evaluate_single_condition(parsed, responses)

    # Handle parentheses first
    while "(" in expression:
        # Find the innermost parentheses
        start = -1
        for i, char in enumerate(expression):
            if char == "(":
                start = i
            elif char == ")" and start != -1:
                # Found a matching closing paren
                inner_expr = expression[start + 1 : i]
                inner_result = evaluate_conditional_expression(inner_expr, responses)
                # Replace the parenthesized expression with its result
                expression = (
                    expression[:start] + str(inner_result).lower() + expression[i + 1 :]
                )
                break
        else:
            # No matching closing paren found
            logger.error(f"Mismatched parentheses in: {expression}")
            return False

    # Now handle OR operations (lower precedence)
    if "||" in expression:
        or_parts = expression.split("||")
        return any(
            evaluate_conditional_expression(part.strip(), responses)
            for part in or_parts
        )

    # Handle AND operations (higher precedence)
    if "&&" in expression:
        and_parts = expression.split("&&")
        for part in and_parts:
            part = part.strip()
            # It's a condition that needs to be evaluated (boolean literals handled at top)
            if not evaluate_conditional_expression(part, responses):
                return False
        return True

    # If we get here, it should be a simple condition
    parsed = parse_condition_string(expression)
    if parsed is None:
        return False
    return evaluate_single_condition(parsed, responses)
