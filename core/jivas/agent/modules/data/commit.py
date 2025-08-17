"""Commit utilities for Jac memory."""

from jac_cloud.core.archetype import BaseAnchor, BulkWrite
from jac_cloud.jaseci.datasources import Collection
from jac_cloud.plugin.jaseci import JacPlugin as Jac
from jaclang.runtimelib.constructs import Archetype


def commit(anchor: BaseAnchor | None = None) -> None:
    """Commit all data from memory to datasource."""
    if anchor:
        if isinstance(anchor, Archetype):
            anchor = anchor.__jac__
        anchor.build_query(bulk_write := BulkWrite())
    else:
        bulk_write = Jac.get_context().mem.get_bulk_write()

    if bulk_write.has_operations:
        if session := Jac.get_context().mem.__session__:
            bulk_write.execute(session)
        else:
            with Collection.get_session() as session, session.start_transaction():
                bulk_write.execute(session)
