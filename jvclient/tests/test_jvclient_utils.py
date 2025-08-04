"""Test utilities for jvclient."""

from pathlib import Path

import pytest

from jvclient.lib.utils import get_reports_payload


def test_load_function_success(tmp_path: Path) -> None:
    """Test successful loading of a function from a Python file."""
    from jvclient.lib.utils import load_function

    # Create a temporary Python file
    test_file = tmp_path / "test_module.py"
    test_file.write_text(
        """
def test_func(x, y=10):
    return x + y
"""
    )

    # Load the function
    func = load_function(str(test_file), "test_func")

    # Test the function works
    assert func(5) == 15
    assert func(5, y=20) == 25


def test_load_function_file_not_found() -> None:
    """Test FileNotFoundError when file doesn't exist."""
    from jvclient.lib.utils import load_function

    with pytest.raises(FileNotFoundError, match="No file found at"):
        load_function("nonexistent.py", "test_func")


def test_decode_base64_image() -> None:
    """Test decoding a base64 string into an image."""
    import base64
    from io import BytesIO

    from PIL import Image

    from jvclient.lib.utils import decode_base64_image

    # Create a simple test image
    test_image = Image.new("RGB", (10, 10), color="red")
    buffer = BytesIO()
    test_image.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode to base64
    base64_string = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Test decoding
    decoded_image = decode_base64_image(base64_string)
    assert isinstance(decoded_image, Image.Image)
    assert decoded_image.size == (10, 10)


def test_jac_yaml_dumper() -> None:
    """Test YAML dumper with long strings."""
    from jvclient.lib.utils import jac_yaml_dumper

    # Test with short string
    short_data = {"key": "short value"}
    result = jac_yaml_dumper(short_data)
    assert "key: short value" in result

    # Test with long string
    long_string = "a" * 200
    long_data = {"key": long_string}
    result = jac_yaml_dumper(long_data)
    assert "|" in result  # Should use block style for long strings


def test_get_user_info() -> None:
    """Test getting user info from session state."""
    import streamlit as st

    from jvclient.lib.utils import get_user_info

    # Mock session state
    st.session_state.ROOT_ID = "test_root"
    st.session_state.TOKEN = "test_token"
    st.session_state.EXPIRATION = "test_expiration"

    user_info = get_user_info()
    assert user_info["root_id"] == "test_root"
    assert user_info["token"] == "test_token"
    assert user_info["expiration"] == "test_expiration"

    def make_response_with_json(json_data: object) -> object:
        """Helper to mock requests.Response with .json() method."""

        class MockResponse:
            def json(self) -> object:
                return json_data

        return MockResponse()

    def make_response_with_json_raises(exc: Exception) -> object:
        """Helper to mock requests.Response whose .json() raises an exception."""

        class MockResponse:
            def json(self) -> object:
                raise exc

        return MockResponse()

    def test_get_reports_payload_single_item() -> None:
        """Should return first item when expect_single=True."""
        resp = make_response_with_json({"reports": ["a", "b", "c"]})
        assert get_reports_payload(resp) == "a"

    def test_get_reports_payload_full_list() -> None:
        """Should return full list when expect_single=False."""
        resp = make_response_with_json({"reports": ["x", "y"]})
        assert get_reports_payload(resp, expect_single=False) == ["x", "y"]

    def test_get_reports_payload_empty_reports() -> None:
        """Should return None for empty reports list."""
        resp = make_response_with_json({"reports": []})
        assert get_reports_payload(resp) is None
        assert get_reports_payload(resp, expect_single=False) is None

    def test_get_reports_payload_missing_reports() -> None:
        """Should return None if 'reports' key missing."""
        resp = make_response_with_json({"other": 123})
        assert get_reports_payload(resp) is None
        assert get_reports_payload(resp, expect_single=False) is None

    def test_get_reports_payload_reports_not_list() -> None:
        """Should return None if 'reports' is not a list."""
        resp = make_response_with_json({"reports": "notalist"})
        assert get_reports_payload(resp) is None

    def test_get_reports_payload_json_not_dict() -> None:
        """Should return None if .json() returns non-dict."""
        resp = make_response_with_json(["not", "a", "dict"])
        assert get_reports_payload(resp) is None

    def test_get_reports_payload_json_raises_valueerror() -> None:
        """Should return None if .json() raises ValueError."""
        resp = make_response_with_json_raises(ValueError("bad json"))
        assert get_reports_payload(resp) is None

    def test_get_reports_payload_json_raises_attributeerror() -> None:
        """Should return None if .json() raises AttributeError."""
        resp = make_response_with_json_raises(AttributeError("no json"))
        assert get_reports_payload(resp) is None

    def test_get_reports_payload_json_raises_keyerror() -> None:
        """Should return None if .json() raises KeyError."""
        resp = make_response_with_json_raises(KeyError("key error"))
        assert get_reports_payload(resp) is None
