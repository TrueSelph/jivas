"""Common system utilities"""

from datetime import datetime
from uuid import UUID

import pytz

import jivas


def get_jivas_version() -> str:
    """Returns the current JIVAS version."""
    return jivas.__version__


def node_obj(node_list: list) -> object | None:
    """Return the first object in the list or None if the list is empty."""
    return node_list[0] if node_list else None


def is_valid_uuid(uuid_to_test: str, version: int = 4) -> bool:
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """

    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def date_now(timezone: str = "US/Eastern", date_format: str = "%Y-%m-%d") -> str | None:
    """Get the current date and time in the specified timezone and format."""
    try:
        # If a timezone is specified, apply it
        tz = pytz.timezone(timezone)
        # Get the current datetime
        dt = datetime.now(tz)
        # Format the datetime according to the provided format
        formatted_datetime = dt.strftime(date_format)

        return formatted_datetime
    except Exception:
        return None
