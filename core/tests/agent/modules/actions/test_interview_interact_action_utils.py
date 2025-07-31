"""Tests for interview interact action utils."""

from typing import Any, Dict

from jivas.agent.modules.action.interview_interact_action_utils import (
    evaluate_conditional_expression,
    evaluate_single_condition,
    parse_condition_string,
)


class TestParseConditionString:
    """Test the parse_condition_string function."""

    def test_parse_range_condition(self) -> None:
        """Test parsing range conditions."""
        result = parse_condition_string("age: [18..65]")
        assert result == ["age", "[..]", ["18", "65"]]

    def test_parse_range_condition_with_decimals(self) -> None:
        """Test parsing range conditions with decimal values."""
        result = parse_condition_string("score: [85.5..100.0]")
        assert result == ["score", "[..]", ["85.5", "100.0"]]

    def test_parse_not_in_list_condition(self) -> None:
        """Test parsing not in list conditions."""
        result = parse_condition_string("status: ![pending, rejected]")
        assert result == ["status", "![]", ["pending", "rejected"]]

    def test_parse_in_list_condition(self) -> None:
        """Test parsing in list conditions."""
        result = parse_condition_string("category: [A, B, C]")
        assert result == ["category", "[]", ["A", "B", "C"]]

    def test_parse_empty_list_condition(self) -> None:
        """Test parsing empty list conditions."""
        result = parse_condition_string("items: []")
        assert result == ["items", "[]", []]

    def test_parse_exact_not_equal_condition(self) -> None:
        """Test parsing exact not equal conditions."""
        result = parse_condition_string("name !:= John")
        assert result == ["name", "!=", "John"]

    def test_parse_not_equal_condition(self) -> None:
        """Test parsing not equal conditions."""
        result = parse_condition_string("status != active")
        assert result == ["status", "!=", "active"]

    def test_parse_exact_equal_condition(self) -> None:
        """Test parsing exact equal conditions."""
        result = parse_condition_string("type := admin")
        assert result == ["type", ":=", "admin"]

    def test_parse_comparison_operators(self) -> None:
        """Test parsing comparison operators."""
        assert parse_condition_string("age >= 18") == ["age", ">=", "18"]
        assert parse_condition_string("score <= 100") == ["score", "<=", "100"]
        assert parse_condition_string("count > 0") == ["count", ">", "0"]
        assert parse_condition_string("balance < 1000") == ["balance", "<", "1000"]

    def test_parse_partial_equal_condition(self) -> None:
        """Test parsing partial equal conditions."""
        result = parse_condition_string("description: contains_text")
        assert result == ["description", ":", "contains_text"]

    def test_parse_simple_equal_condition(self) -> None:
        """Test parsing simple equal conditions."""
        result = parse_condition_string("active = true")
        assert result == ["active", "=", True]

    def test_parse_boolean_values(self) -> None:
        """Test parsing boolean values."""
        assert parse_condition_string("enabled = true") == ["enabled", "=", True]
        assert parse_condition_string("disabled = false") == ["disabled", "=", False]
        assert parse_condition_string("valid := TRUE") == ["valid", ":=", True]
        assert parse_condition_string("invalid := FALSE") == ["invalid", ":=", False]

    def test_parse_invalid_condition_returns_none(self) -> None:
        """Test that invalid conditions return None."""
        assert parse_condition_string("invalid condition format") is None
        assert parse_condition_string("") is None
        assert parse_condition_string("   ") is None

    def test_parse_condition_with_whitespace(self) -> None:
        """Test parsing conditions with extra whitespace."""
        result = parse_condition_string("  name  :=  John  ")
        assert result == ["name", ":=", "John"]

    def test_parse_field_with_dots_and_hyphens(self) -> None:
        """Test parsing fields with dots and hyphens."""
        result = parse_condition_string("user.profile-name = test")
        assert result == ["user.profile-name", "=", "test"]


class TestEvaluateSingleCondition:
    """Test the evaluate_single_condition function."""

    def test_evaluate_exact_equal_string(self) -> None:
        """Test evaluating exact equal conditions with strings."""
        responses = {"name": "John"}
        condition = ["name", ":=", "John"]
        assert evaluate_single_condition(condition, responses) is True

        condition = ["name", ":=", "Jane"]
        assert evaluate_single_condition(condition, responses) is False

    def test_evaluate_exact_equal_boolean(self) -> None:
        """Test evaluating exact equal conditions with booleans."""
        responses = {"active": "true"}
        condition = ["active", ":=", True]
        assert evaluate_single_condition(condition, responses) is True

        condition = ["active", ":=", False]
        assert evaluate_single_condition(condition, responses) is False

    def test_evaluate_not_equal(self) -> None:
        """Test evaluating not equal conditions."""
        responses = {"status": "active"}
        condition = ["status", "!=", "inactive"]
        assert evaluate_single_condition(condition, responses) is True

        condition = ["status", "!=", "active"]
        assert evaluate_single_condition(condition, responses) is False

    def test_evaluate_numeric_comparisons(self) -> None:
        """Test evaluating numeric comparison conditions."""
        responses = {"age": "25", "score": "85.5"}

        assert evaluate_single_condition(["age", ">", "18"], responses) is True
        assert evaluate_single_condition(["age", ">", "30"], responses) is False
        assert evaluate_single_condition(["age", ">=", "25"], responses) is True
        assert evaluate_single_condition(["age", "<", "30"], responses) is True
        assert evaluate_single_condition(["age", "<=", "25"], responses) is True
        assert evaluate_single_condition(["score", ">", "85.0"], responses) is True

    def test_evaluate_range_condition(self) -> None:
        """Test evaluating range conditions."""
        responses = {"age": "25"}
        condition = ["age", "[..]", ["18", "65"]]
        assert evaluate_single_condition(condition, responses) is True

        condition = ["age", "[..]", ["30", "65"]]
        assert evaluate_single_condition(condition, responses) is False

    def test_evaluate_in_list_condition(self) -> None:
        """Test evaluating in list conditions."""
        responses = {"category": "A"}
        condition = ["category", "[]", ["A", "B", "C"]]
        assert evaluate_single_condition(condition, responses) is True

        condition = ["category", "[]", ["D", "E", "F"]]
        assert evaluate_single_condition(condition, responses) is False

    def test_evaluate_not_in_list_condition(self) -> None:
        """Test evaluating not in list conditions."""
        responses = {"status": "active"}
        condition = ["status", "![]", ["pending", "rejected"]]
        assert evaluate_single_condition(condition, responses) is True

        condition = ["status", "![]", ["active", "inactive"]]
        assert evaluate_single_condition(condition, responses) is False

    def test_evaluate_partial_match_condition(self) -> None:
        """Test evaluating partial match conditions."""
        responses = {"description": "This is a test description"}
        condition = ["description", ":", "test"]
        assert evaluate_single_condition(condition, responses) is True

        condition = ["description", ":", "missing"]
        assert evaluate_single_condition(condition, responses) is False

    def test_evaluate_missing_field(self) -> None:
        """Test evaluating conditions with missing fields."""
        responses: Dict[str, Any] = {}
        condition = ["missing_field", "=", "value"]
        assert evaluate_single_condition(condition, responses) is False

        # Special case: != operator returns True for missing fields
        condition = ["missing_field", "!=", "value"]
        assert evaluate_single_condition(condition, responses) is True

    def test_evaluate_invalid_condition_structure(self) -> None:
        """Test evaluating invalid condition structures."""
        responses = {"field": "value"}

        # Empty condition
        assert evaluate_single_condition([], responses) is False

        # Incomplete condition
        assert evaluate_single_condition(["field"], responses) is False
        assert evaluate_single_condition(["field", "="], responses) is False

    def test_evaluate_numeric_conversion_error(self) -> None:
        """Test handling numeric conversion errors."""
        responses = {"field": "not_a_number"}
        condition = ["field", ">", "10"]
        assert evaluate_single_condition(condition, responses) is False

    def test_evaluate_invalid_range_value(self) -> None:
        """Test handling invalid range values."""
        responses = {"field": "25"}
        condition = ["field", "[..]", ["invalid"]]  # Wrong list length
        assert evaluate_single_condition(condition, responses) is False

        condition = ["field", "[..]", "not_a_list"]  # Not a list
        assert evaluate_single_condition(condition, responses) is False


class TestEvaluateConditionalExpression:
    """Test the evaluate_conditional_expression function."""

    def test_evaluate_empty_expression(self) -> None:
        """Test evaluating empty expressions."""
        responses = {"field": "value"}
        assert evaluate_conditional_expression("", responses) is True
        assert evaluate_conditional_expression("   ", responses) is True

    def test_evaluate_boolean_literals(self) -> None:
        """Test evaluating boolean literal expressions."""
        responses: Dict[str, Any] = {}
        assert evaluate_conditional_expression("true", responses) is True
        assert evaluate_conditional_expression("false", responses) is False

    def test_evaluate_simple_condition(self) -> None:
        """Test evaluating simple conditions."""
        responses = {"name": "John", "age": "25"}
        assert evaluate_conditional_expression("name = John", responses) is True
        assert evaluate_conditional_expression("age > 20", responses) is True
        assert evaluate_conditional_expression("name = Jane", responses) is False

    def test_evaluate_and_conditions(self) -> None:
        """Test evaluating AND conditions."""
        responses = {"name": "John", "age": "25", "active": "true"}

        # All true
        expr = "name = John && age > 20 && active = true"
        assert evaluate_conditional_expression(expr, responses) is True

        # One false
        expr = "name = John && age > 30 && active = true"
        assert evaluate_conditional_expression(expr, responses) is False

    def test_evaluate_or_conditions(self) -> None:
        """Test evaluating OR conditions."""
        responses = {"name": "John", "age": "15", "vip": "true"}

        # One true (age condition false, but vip true)
        expr = "age >= 18 || vip = true"
        assert evaluate_conditional_expression(expr, responses) is True

        # All false
        expr = "age >= 18 || name = Jane"
        assert evaluate_conditional_expression(expr, responses) is False

    def test_evaluate_mixed_and_or_conditions(self) -> None:
        """Test evaluating mixed AND/OR conditions."""
        responses = {"name": "John", "age": "25", "vip": "false", "admin": "true"}

        # OR has lower precedence than AND
        expr = "name = John && age >= 18 || vip = true && admin = false"
        assert evaluate_conditional_expression(expr, responses) is True

    def test_evaluate_parentheses(self) -> None:
        """Test evaluating conditions with parentheses."""
        responses = {"a": "1", "b": "2", "c": "3", "d": "4"}

        # Without parentheses: a=1 && b=2 || c=5 && d=4 -> (a=1 && b=2) || (c=5 && d=4) -> True || False -> True
        expr1 = "a = 1 && b = 2 || c = 5 && d = 4"
        assert evaluate_conditional_expression(expr1, responses) is True

        # With parentheses: a=1 && (b=2 || c=5) && d=4 -> a=1 && True && d=4 -> True
        expr2 = "a = 1 && (b = 2 || c = 5) && d = 4"
        assert evaluate_conditional_expression(expr2, responses) is True

        # Different grouping: (a=1 && b=5) || (c=3 && d=4) -> False || True -> True
        expr3 = "(a = 1 && b = 5) || (c = 3 && d = 4)"
        assert evaluate_conditional_expression(expr3, responses) is True

    def test_evaluate_nested_parentheses(self) -> None:
        """Test evaluating conditions with nested parentheses."""
        responses = {"a": "1", "b": "2", "c": "3"}

        expr = "a = 1 && (b = 2 || (c = 3 && a = 2))"
        assert evaluate_conditional_expression(expr, responses) is True

        expr = "a = 1 && (b = 5 || (c = 3 && a = 2))"
        assert evaluate_conditional_expression(expr, responses) is False

    def test_evaluate_complex_conditions(self) -> None:
        """Test evaluating complex conditional expressions."""
        responses = {
            "user_type": "premium",
            "age": "25",
            "country": "US",
            "score": "85",
            "active": "true",
        }

        expr = (
            "user_type = premium && age >= 18 && "
            "(country: US || country: CA) && "
            "score > 80 && active = true"
        )
        assert evaluate_conditional_expression(expr, responses) is True

    def test_evaluate_malformed_parentheses(self) -> None:
        """Test handling malformed parentheses."""
        responses = {"a": "1"}

        # Missing closing parenthesis
        expr = "a = 1 && (b = 2"
        assert evaluate_conditional_expression(expr, responses) is False

    def test_evaluate_invalid_simple_condition(self) -> None:
        """Test handling invalid simple conditions."""
        responses = {"field": "value"}

        expr = "invalid condition format"
        assert evaluate_conditional_expression(expr, responses) is False

    def test_evaluate_whitespace_handling(self) -> None:
        """Test proper whitespace handling in expressions."""
        responses = {"name": "John", "age": "25"}

        expr = "  name = John  &&  age > 20  "
        assert evaluate_conditional_expression(expr, responses) is True
