"""Ordering utils package"""

import logging
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def order_interact_actions(
    actions_data: List[Dict[str, Any]],
) -> Optional[List[Dict[str, Any]]]:
    """Order interact actions based on dependencies, weights, and original order, respecting pre-existing weight values in context."""
    if not actions_data:
        return None

    # Track original positions for tie-breaking
    original_order: Dict[str, int] = {}
    interact_actions = []
    other_actions = []
    fixed_action_names = set()  # Track names of actions with fixed weights

    # Separate interact actions and record original positions
    for idx, action in enumerate(actions_data):
        if (
            action.get("context", {}).get("_package", {}).get("meta", {}).get("type")
            == "interact_action"
        ):
            name = action["context"]["_package"]["name"]
            original_order[name] = idx
            interact_actions.append(action)
            # Check if weight exists in context
            if "weight" in action.get("context", {}):
                fixed_action_names.add(name)
        else:
            other_actions.append(action)

    if not interact_actions:
        return None

    action_lookup = {a["context"]["_package"]["name"]: a for a in interact_actions}
    graph: defaultdict[str, list[str]] = defaultdict(list)
    in_degree: defaultdict[str, int] = defaultdict(int)
    has_constraint: Dict[str, bool] = {}

    # Extract weights and check for constraints
    action_weights = {}
    for action in interact_actions:
        name = action["context"]["_package"]["name"]
        config_order = action["context"]["_package"]["config"].get("order", {})
        has_before = "before" in config_order
        has_after = "after" in config_order
        has_constraint[name] = has_before or has_after
        action_weights[name] = config_order.get("weight", 0)

    # Process BOTH constraints first to ensure full dependency graph
    for action in interact_actions:
        action_name = action["context"]["_package"]["name"]
        config_order = action["context"]["_package"]["config"].get("order", {})
        namespace = action_name.split("/")[0]

        # Handle AFTER constraints
        if (after := config_order.get("after")) and after != "all":
            normalized_after = f"{namespace}/{after}" if "/" not in after else after
            if normalized_after in action_lookup:
                graph[normalized_after].append(action_name)
                in_degree[action_name] += 1

        # Handle BEFORE constraints
        if (before := config_order.get("before")) and before != "all":
            normalized_before = f"{namespace}/{before}" if "/" not in before else before
            if normalized_before in action_lookup:
                graph[action_name].append(normalized_before)
                in_degree[normalized_before] += 1

    # Handle global constraints
    # Process before:all
    before_all = [
        name
        for name, a in action_lookup.items()
        if a["context"]["_package"]["config"].get("order", {}).get("before") == "all"
    ]
    for name in before_all:
        for other in action_lookup:
            if other != name and other not in before_all:
                graph[name].append(other)
                in_degree[other] += 1

    # Process after:all
    after_all = [
        name
        for name, a in action_lookup.items()
        if a["context"]["_package"]["config"].get("order", {}).get("after") == "all"
    ]
    for name in after_all:
        for other in action_lookup:
            if other != name and other not in after_all:
                graph[other].append(name)
                in_degree[name] += 1

    # Add ordering constraints for fixed-weight actions
    fixed_actions = [
        action
        for action in interact_actions
        if action["context"]["_package"]["name"] in fixed_action_names
    ]
    # Sort by existing weight and original order
    fixed_actions.sort(
        key=lambda a: (
            a["context"]["weight"],
            original_order[a["context"]["_package"]["name"]],
        )
    )
    # Add dependency edges between consecutive fixed actions
    for i in range(len(fixed_actions) - 1):
        a1_name = fixed_actions[i]["context"]["_package"]["name"]
        a2_name = fixed_actions[i + 1]["context"]["_package"]["name"]
        graph[a1_name].append(a2_name)
        in_degree[a2_name] += 1

    # Kahn's algorithm with adjusted sorting key
    queue = deque(
        sorted(
            [n for n in action_lookup if in_degree[n] == 0],
            key=lambda x: (
                action_weights[x] if has_constraint[x] else float("inf"),
                original_order[x],
            ),
        )
    )

    sorted_names = []
    while queue:
        current = queue.popleft()
        sorted_names.append(current)
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
        # Re-sort remaining nodes considering updated dependencies and constraints
        queue = deque(
            sorted(
                queue,
                key=lambda x: (
                    action_weights[x] if has_constraint[x] else float("inf"),
                    original_order[x],
                ),
            )
        )

    # Validate dependencies
    if len(sorted_names) != len(interact_actions):
        raise ValueError("Circular dependency detected in interact actions")

    # Rebuild final ordered list
    ordered = [action_lookup[n] for n in sorted_names] + other_actions

    # Update weight values only for non-fixed actions
    for idx, action in enumerate(ordered):
        if action["context"]["_package"]["meta"]["type"] == "interact_action":
            name = action["context"]["_package"]["name"]
            if name not in fixed_action_names:
                action["context"]["weight"] = idx

    return ordered
