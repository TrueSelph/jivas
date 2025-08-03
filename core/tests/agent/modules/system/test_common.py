"""Test for common system utilities."""

from unittest.mock import patch

from jivas.agent.modules.system.common import (
    date_now,
    get_jivas_version,
    is_valid_uuid,
    node_obj,
)


class TestCommonSystemUtils:
    """Test cases for common system utilities."""

    def test_get_jivas_version(self) -> None:
        """Test that get_jivas_version returns the correct version."""
        with patch("jivas.agent.modules.system.common.jivas.__version__", "1.0.0"):
            assert get_jivas_version() == "1.0.0"

    def test_node_obj(self) -> None:
        """Test node_obj returns the first element or None."""
        assert node_obj([1, 2, 3]) == 1
        assert node_obj([]) is None
        assert node_obj(["a", "b"]) == "a"

    def test_is_valid_uuid(self) -> None:
        """Test is_valid_uuid with various inputs."""
        # Valid v4 UUID
        assert (
            is_valid_uuid("c9bf9e57-1685-4c89-bafb-ff5af830be8a") is True
        )  # pragma: allowlist secret
        # Invalid UUID
        assert is_valid_uuid("not-a-uuid") is False
        # Valid v1 UUID, but fails with default v4 check
        assert (
            is_valid_uuid("a8098c1a-f86e-11da-bd1a-00112444be1e", version=4) is False
        )  # pragma: allowlist secret
        # Valid v1 UUID with correct version check
        assert (
            is_valid_uuid("a8098c1a-f86e-11da-bd1a-00112444be1e", version=1) is True
        )  # pragma: allowlist secret

    def test_date_now(self) -> None:
        """Test date_now with different timezones and formats."""
        # Test with default timezone and format
        assert date_now() is not None
        # Test with a different timezone
        assert date_now(timezone="UTC") is not None
        # Test with a different format
        assert date_now(date_format="%Y/%m/%d %H:%M:%S") is not None
        # Test with an invalid timezone
        assert date_now(timezone="Invalid/Timezone") is None
