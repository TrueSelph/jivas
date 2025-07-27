"""Tests for conditional expression evaluation functionality."""

from typing import Any, Dict, List, Union

import pytest
from jivas.agent.modules.interview_interact_action.utils import (
    evaluate_conditional_expression,
    evaluate_single_condition,
    parse_condition_string,
)


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("country=USA", ["country", "=", "USA"]),
        ("age = 30", ["age", "=", "30"]),
        ("is_valid = true", ["is_valid", "=", True]),
        ("name= John Doe", ["name", "=", "John Doe"]),
        ("category:=Shoe", ["category", ":=", "Shoe"]),
        ("description:Urgent", ["description", ":", "Urgent"]),
        ("status!=inactive", ["status", "!=", "inactive"]),
        ("count != 0", ["count", "!=", "0"]),
        ("is_ready != false", ["is_ready", "!=", False]),
        ("price>100", ["price", ">", "100"]),
        ("stock < 50", ["stock", "<", "50"]),
        ("rating >= 4.5", ["rating", ">=", "4.5"]),
        ("attempts <= 3", ["attempts", "<=", "3"]),
        ("country:[USA,UK,Canada]", ["country", "[]", ["USA", "UK", "Canada"]]),
        ("ids : [ 1, 2 ,3 ]", ["ids", "[]", ["1", "2", "3"]]),
        ("tags:[]", ["tags", "[]", []]),
        ("state:![pending,failed]", ["state", "![]", ["pending", "failed"]]),
        ("category : ![ A , B ]", ["category", "![]", ["A", "B"]]),
        ("score:[70..90]", ["score", "[..]", ["70", "90"]]),
        ("value : [ -10.5 .. 0.5 ]", ["value", "[..]", ["-10.5", "0.5"]]),
    ],
)
def test_parse_condition_string_valid(
    input_str: str, expected: List[Union[str, List[str]]]
) -> None:
    """Test that valid condition strings are parsed correctly."""
    assert parse_condition_string(input_str) == expected


@pytest.mark.parametrize(
    "input_str",
    [
        "field_no_operator",
        "field <> value",
    ],
)
def test_parse_condition_string_invalid(input_str: str) -> None:
    """Test that invalid condition strings return None."""
    assert parse_condition_string(input_str) is None


@pytest.fixture
def responses() -> Dict[str, Any]:
    """Fixture providing sample response data for testing."""
    return {
        "country": "USA",
        "age": "30",
        "score": "85.5",
        "status": "active",
        "is_member": "true",
        "is_flagged": "false",
        "tags": "alpha",
        "codes": ["A", "C"],
        "empty_field": None,
        "description": "This is an urgent item",
    }


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["country", "=", "USA"], True),
        (["country", "=", "Canada"], False),
        (["age", "=", "30"], True),
        (["is_member", "=", True], True),
        (["is_member", "=", False], False),
        (["is_flagged", "=", False], True),
    ],
)
def test_evaluate_single_condition_equal(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of equality conditions."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["status", ":=", "active"], True),
        (["status", ":=", "Active"], False),
    ],
)
def test_evaluate_single_condition_exact_equal(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of exact equality conditions."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["description", ":", "urgent"], True),
        (["description", ":", "item"], True),
        (["description", ":", "missing"], False),
    ],
)
def test_evaluate_single_condition_partial_equal(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of partial string match conditions."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["country", "!=", "Canada"], True),
        (["country", "!=", "USA"], False),
        (["age", "!=", "25"], True),
        (["is_member", "!=", False], True),
    ],
)
def test_evaluate_single_condition_not_equal(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of inequality conditions."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["age", ">", "25"], True),
        (["age", "<", "30"], False),
        (["score", ">=", "85.5"], True),
        (["score", "<=", "85.5"], True),
        (["score", ">", "90"], False),
    ],
)
def test_evaluate_single_condition_numeric_ops(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of numeric comparison conditions."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["country", "[]", ["USA", "UK"]], True),
        (["country", "[]", ["Canada", "Mexico"]], False),
        (["tags", "[]", ["alpha", "beta"]], True),
        (["age", "[]", ["29", "30", "31"]], True),
    ],
)
def test_evaluate_single_condition_in_list(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of list membership conditions."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["country", "![]", ["Canada", "Mexico"]], True),
        (["country", "![]", ["USA", "UK"]], False),
        (["tags", "![]", ["gamma", "delta"]], True),
    ],
)
def test_evaluate_single_condition_not_in_list(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of list non-membership conditions."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["score", "[..]", ["80", "90"]], True),
        (["score", "[..]", ["70", "80"]], False),
        (["age", "[..]", ["25", "35"]], True),
    ],
)
def test_evaluate_single_condition_range(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of range conditions."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        (["non_existent_field", "=", "value"], False),
        (["non_existent_field", "!=", "value"], True),
        (["non_existent_field", "![]", ["A", "B"]], True),
        (["non_existent_field", "[]", ["A", "B"]], False),
    ],
)
def test_evaluate_single_condition_missing_field(
    condition: List[Union[str, List[str]]], expected: bool, responses: Dict[str, Any]
) -> None:
    """Test evaluation of conditions with missing fields."""
    assert evaluate_single_condition(condition, responses) == expected


@pytest.fixture
def complex_responses() -> Dict[str, Any]:
    """Fixture providing more complex response data for testing."""
    return {
        "country": "USA",
        "age": "30",
        "status": "active",
        "plan": "premium",
    }


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("country=USA && age>25", True),
        ("country=USA && age<25", False),
        ("country=Canada && age>25", False),
        ("country=Canada || age>25", True),
        ("plan:gold || status:active", True),
        ("country=Canada || age<25", False),
        ("status:active && (country=USA || country=Canada)", True),
        ("status:inactive && (country=USA || country=Canada)", False),
        ("(status:active && country=USA) || plan=basic", True),
        ("plan=basic || (status:active && country=USA)", True),
        ("country=USA && (age>20 && (status:active || plan:basic))", True),
        ("(country=USA && age>20) && status:active", True),
        ("", True),
        ("   ", True),
        ("age>25", True),
        ("age<25", False),
    ],
)
def test_evaluate_conditional_expression(
    expr: str, expected: bool, complex_responses: Dict[str, Any]
) -> None:
    """Test evaluation of complex conditional expressions."""
    assert evaluate_conditional_expression(expr, complex_responses) == expected
