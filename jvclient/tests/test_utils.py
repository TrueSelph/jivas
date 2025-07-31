import pytest


def test_load_function_success(tmp_path):
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


def test_load_function_file_not_found():
    """Test FileNotFoundError when file doesn't exist."""
    from jvclient.lib.utils import load_function

    with pytest.raises(FileNotFoundError, match="No file found at"):
        load_function("nonexistent.py", "test_func")


def test_decode_base64_image():
    """Test decoding a base64 string into an image."""
    from jvclient.lib.utils import decode_base64_image
    import base64
    from PIL import Image
    from io import BytesIO

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


def test_jac_yaml_dumper():
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


def test_get_user_info():
    """Test getting user info from session state."""
    from jvclient.lib.utils import get_user_info
    import streamlit as st

    # Mock session state
    st.session_state.ROOT_ID = "test_root"
    st.session_state.TOKEN = "test_token"
    st.session_state.EXPIRATION = "test_expiration"

    user_info = get_user_info()
    assert user_info["root_id"] == "test_root"
    assert user_info["token"] == "test_token"
    assert user_info["expiration"] == "test_expiration"
