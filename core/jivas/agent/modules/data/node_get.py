"""node_get paginating node collections in Jivas."""

from jac_cloud.core.archetype import NodeAnchor


def node_get(query_filter: dict | None = None) -> list:
    """Retrieve a list of nodes from the 'node' collection based on the query filter."""

    if query_filter is None:
        return []

    # Execute the query
    cursor = NodeAnchor.Collection.find(query_filter)

    if cursor:
        nodes = [n.archetype for n in cursor]
        return nodes

    return []
