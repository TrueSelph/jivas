"""
Test module for action ordering operations.

This module contains comprehensive tests for the ordering functionality
including dependency resolution, weight handling, and topological sorting
of interact actions.
"""

import unittest
from typing import Any, Dict

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

    def test_basic_ordering(self) -> None:
        """Test basic ordering functionality"""
        actions = [
            self.create_action("test/action1"),
            self.create_action("test/action2"),
            self.create_action("test/action3", action_type="other"),
        ]
        result = order_interact_actions(actions)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
        # Interact actions should be first, others at end
        interact_names = [
            a["context"]["_package"]["name"]
            for a in result
            if a["context"]["_package"]["meta"]["type"] == "interact_action"
        ]
        self.assertEqual(interact_names, ["test/action1", "test/action2"])

    def test_before_all(self) -> None:
        """Test before:all constraint"""
        actions = [
            self.create_action("test/action1"),
            self.create_action("test/action2", order_config={"before": "all"}),
            self.create_action("test/action3"),
        ]
        result = order_interact_actions(actions)

        self.assertIsNotNone(result)
        names = [a["context"]["_package"]["name"] for a in result[:3]]
        self.assertEqual(names[0], "test/action2")

    def test_after_all(self) -> None:
        """Test after:all constraint"""
        actions = [
            self.create_action("test/action1"),
            self.create_action("test/action2", order_config={"after": "all"}),
            self.create_action("test/action3"),
        ]
        result = order_interact_actions(actions)

        self.assertIsNotNone(result)
        interact_actions = [
            a
            for a in result
            if a["context"]["_package"]["meta"]["type"] == "interact_action"
        ]
        names = [a["context"]["_package"]["name"] for a in interact_actions]
        self.assertEqual(names[-1], "test/action2")

    def test_complex_dependencies(self) -> None:
        """Test complex dependency resolution"""
        actions = [
            self.create_action("test/action1", order_config={"after": "action2"}),
            self.create_action("test/action2"),
            self.create_action("test/action3", order_config={"before": "action1"}),
        ]
        result = order_interact_actions(actions)

        self.assertIsNotNone(result)
        names = [a["context"]["_package"]["name"] for a in result[:3]]

        # action2 should come before action1
        # action3 should come before action1
        action1_idx = names.index("test/action1")
        action2_idx = names.index("test/action2")
        action3_idx = names.index("test/action3")

        self.assertLess(action2_idx, action1_idx)
        self.assertLess(action3_idx, action1_idx)

    def test_no_dependencies(self) -> None:
        """Test ordering with no dependencies"""
        actions = [
            self.create_action("test/action1"),
            self.create_action("test/action2"),
            self.create_action("test/action3"),
        ]
        result = order_interact_actions(actions)

        self.assertIsNotNone(result)
        # Should maintain original order
        names = [a["context"]["_package"]["name"] for a in result[:3]]
        self.assertEqual(names, ["test/action1", "test/action2", "test/action3"])

    def test_mixed_namespaces_and_types(self) -> None:
        """Test mixed action types and namespaces"""
        actions = [
            self.create_action("ns1/action1"),
            self.create_action("ns2/action2"),
            self.create_action("ns1/other", action_type="other"),
        ]
        result = order_interact_actions(actions)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)

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
        # Other actions should be at the end
        other_action = result[-1]
        self.assertEqual(other_action["context"]["_package"]["meta"]["type"], "other")

    def test_empty_list_returns_none(self) -> None:
        """Test that empty list returns None"""
        result = order_interact_actions([])
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
