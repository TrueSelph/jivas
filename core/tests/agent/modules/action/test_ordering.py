"""
Test module for action ordering operations.

This module contains comprehensive tests for the ordering functionality
including dependency resolution, weight handling, and topological sorting
of interact actions.
"""

import unittest
from typing import Any, Dict, List

from jivas.agent.modules.action.ordering import order_interact_actions


class TestOrderInteractActions(unittest.TestCase):
    """Test cases for the order_interact_actions function."""

    def create_action(
        self,
        name: str,
        action_type: str = "interact_action",
        order_config: Dict[str, Any] | None = None,
        weight: int | None = None,
    ) -> Dict[str, Any]:
        """Helper method to create test action data."""
        action: Dict[str, Any] = {
            "context": {
                "_package": {
                    "name": name,
                    "meta": {"type": action_type},
                    "config": {"order": order_config or {}},
                }
            }
        }
        if weight is not None:
            action["context"]["weight"] = weight
        return action

    def assert_order(self, result: List[Dict], expected_order: List[str]) -> None:
        """Assert the order of interact actions in the result."""
        self.assertIsNotNone(result)
        interact_names = [
            a["context"]["_package"]["name"]
            for a in result
            if a["context"]["_package"]["meta"]["type"] == "interact_action"
        ]
        self.assertEqual(interact_names, expected_order)

    def test_basic_ordering(self) -> None:
        """Test basic ordering functionality"""
        actions = [
            self.create_action("test/action1"),
            self.create_action("test/action2"),
            self.create_action("test/action3", action_type="other"),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/action1", "test/action2"])
        self.assertEqual(result[-1]["context"]["_package"]["name"], "test/action3")

    def test_before_all(self) -> None:
        """Test before:all constraint"""
        actions = [
            self.create_action("test/action1"),
            self.create_action("test/action2", order_config={"before": "all"}),
            self.create_action("test/action3"),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/action2", "test/action1", "test/action3"])

    def test_after_all(self) -> None:
        """Test after:all constraint"""
        actions = [
            self.create_action("test/action1"),
            self.create_action("test/action2", order_config={"after": "all"}),
            self.create_action("test/action3"),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/action1", "test/action3", "test/action2"])

    def test_complex_dependencies(self) -> None:
        """Test complex dependency resolution"""
        actions = [
            self.create_action("test/action1", order_config={"after": "action2"}),
            self.create_action("test/action2"),
            self.create_action("test/action3", order_config={"before": "action1"}),
        ]
        result = order_interact_actions(actions)
        self.assertIsNotNone(result)
        names = [
            a["context"]["_package"]["name"]
            for a in result
            if a["context"]["_package"]["meta"]["type"] == "interact_action"
        ]
        action1_idx = names.index("test/action1")
        action2_idx = names.index("test/action2")
        action3_idx = names.index("test/action3")
        self.assertLess(action2_idx, action1_idx)
        self.assertLess(action3_idx, action1_idx)

    def test_no_dependencies(self) -> None:
        """Test ordering with no dependencies, should preserve original order."""
        actions = [
            self.create_action("test/action1"),
            self.create_action("test/action2"),
            self.create_action("test/action3"),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/action1", "test/action2", "test/action3"])

    def test_mixed_interact_and_other_actions(self) -> None:
        """Test ordering with mixed interact and other action types"""
        actions = [
            self.create_action("test/interact1"),
            self.create_action("test/other1", action_type="other"),
            self.create_action("test/interact2"),
        ]
        result = order_interact_actions(actions)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
        self.assert_order(result, ["test/interact1", "test/interact2"])
        self.assertEqual(result[-1]["context"]["_package"]["meta"]["type"], "other")

    def test_empty_list_returns_none(self) -> None:
        """Test that empty list returns None"""
        self.assertIsNone(order_interact_actions([]))

    def test_no_interact_actions_returns_none(self) -> None:
        """Test that a list with no interact actions returns None."""
        actions = [
            self.create_action("test/other1", action_type="other"),
            self.create_action("test/other2", action_type="other"),
        ]
        self.assertIsNone(order_interact_actions(actions))

    def test_circular_dependency_raises_error(self) -> None:
        """Test that a circular dependency raises a ValueError."""
        actions = [
            self.create_action("test/action1", order_config={"after": "action2"}),
            self.create_action("test/action2", order_config={"after": "action1"}),
        ]
        with self.assertRaisesRegex(ValueError, "Circular dependency detected"):
            order_interact_actions(actions)

    def test_dependency_on_non_existent_action(self) -> None:
        """Test that a dependency on a non-existent action is ignored."""
        actions = [
            self.create_action("test/action1", order_config={"after": "nonexistent"}),
            self.create_action("test/action2"),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/action1", "test/action2"])

    def test_fixed_weights_are_respected(self) -> None:
        """Test that actions with pre-set weights are ordered correctly."""
        actions = [
            self.create_action("test/action1", weight=10),
            self.create_action("test/action2"),
            self.create_action("test/action3", weight=5),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/action2", "test/action3", "test/action1"])
        # Check final weights
        self.assertEqual(result[0]["context"]["weight"], 0)  # Newly assigned
        self.assertEqual(result[1]["context"]["weight"], 5)  # Fixed
        self.assertEqual(result[2]["context"]["weight"], 10)  # Fixed

    def test_complex_sorting_with_weights_and_constraints(self) -> None:
        """Test sorting based on weights for constrained actions vs unconstrained."""
        actions = [
            self.create_action("test/actionA", order_config={"weight": 100}),
            self.create_action(
                "test/actionB", order_config={"weight": 10, "before": "actionC"}
            ),
            self.create_action("test/actionC"),
        ]
        result = order_interact_actions(actions)
        # actionB has a constraint and lower weight, so it should come before actionA.
        # actionC depends on B.
        self.assert_order(result, ["test/actionB", "test/actionA", "test/actionC"])

    def test_tie_breaking_with_original_order(self) -> None:
        """Test that original order is used as a tie-breaker."""
        actions = [
            self.create_action("test/actionA", order_config={"weight": 10}),
            self.create_action("test/actionB", order_config={"weight": 5}),
            self.create_action("test/actionC", order_config={"weight": 5}),
        ]
        result = order_interact_actions(actions)
        # B and C have same weight, so their original order should be preserved.
        self.assert_order(result, ["test/actionA", "test/actionB", "test/actionC"])

    def test_final_weight_assignment(self) -> None:
        """Test that final weights are assigned correctly."""
        actions = [
            self.create_action("test/actionC", weight=100),  # Fixed high weight
            self.create_action("test/actionA"),
            self.create_action("test/actionB", order_config={"after": "actionA"}),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/actionC", "test/actionA", "test/actionB"])
        # Check final weights
        self.assertEqual(result[0]["context"]["weight"], 100)  # Fixed
        self.assertEqual(result[1]["context"]["weight"], 1)  # New
        self.assertEqual(result[2]["context"]["weight"], 2)  # New

    def test_full_namespace_in_dependency(self) -> None:
        """Test dependency using a full namespace."""
        actions = [
            self.create_action("ns1/action1", order_config={"after": "ns1/action2"}),
            self.create_action("ns1/action2"),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["ns1/action2", "ns1/action1"])

    def test_before_and_after_constraints(self) -> None:
        """Test an action with both before and after constraints."""
        actions = [
            self.create_action("test/action1"),
            self.create_action(
                "test/action2",
                order_config={"after": "action1", "before": "action3"},
            ),
            self.create_action("test/action3"),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/action1", "test/action2", "test/action3"])

    def test_multiple_before_all(self) -> None:
        """Test multiple actions with before:all constraint."""
        actions = [
            self.create_action("test/action1", order_config={"before": "all"}),
            self.create_action("test/action2"),
            self.create_action("test/action3", order_config={"before": "all"}),
        ]
        result = order_interact_actions(actions)
        # action1 and action3 should come first, in their original order.
        self.assert_order(result, ["test/action1", "test/action3", "test/action2"])

    def test_multiple_after_all(self) -> None:
        """Test multiple actions with after:all constraint."""
        actions = [
            self.create_action("test/action1", order_config={"after": "all"}),
            self.create_action("test/action2"),
            self.create_action("test/action3", order_config={"after": "all"}),
        ]
        result = order_interact_actions(actions)
        # action1 and action3 should come last, in their original order.
        self.assert_order(result, ["test/action2", "test/action1", "test/action3"])

    def test_mixed_fixed_weights_and_dependencies(self) -> None:
        """Test a mix of fixed-weight actions and dependency constraints."""
        actions = [
            self.create_action("test/action1", weight=10),
            self.create_action("test/action2", order_config={"after": "action3"}),
            self.create_action("test/action3"),
        ]
        result = order_interact_actions(actions)
        self.assert_order(result, ["test/action1", "test/action3", "test/action2"])


if __name__ == "__main__":
    unittest.main()
