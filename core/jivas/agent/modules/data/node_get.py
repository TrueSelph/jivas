"""node_get paginating node collections in Jivas."""

from jac_cloud.core.archetype import BaseCollection, NodeAnchor
from jac_cloud.plugin.jaseci import JacPlugin as Jac


def node_get(query_filter: dict | None = None) -> list:
    """Retrieve a list of nodes from the 'node' collection based on the query filter."""

    if query_filter is None:
        return []

    # Execute the query
    node_refs = [
        NodeAnchor.ref(f"n::{str(nd.get("_id"))}")
        for nd in BaseCollection.get_collection("node").find(query_filter)
    ]

    if node_refs:
        nodes = [n.archetype for n in Jac.get_context().mem.find(node_refs)]
        return nodes

    return []
