"""Utils to handle parsing"""


def extract_first_name(full_name: str) -> str:
    """
    Extract the first name from a full name.

    Args:
        full_name: The complete name string

    Returns:
        The extracted first name
    """
    # List of common titles to be removed
    titles = ["Mr.", "Mrs.", "Ms.", "Miss", "Dr.", "Prof.", "Sir", "Madam", "Mx."]

    # Split the full name into parts
    name_parts = full_name.split()

    # Remove any titles from the list of name parts
    name_parts = [part for part in name_parts if part not in titles]

    # Return the first element as the first name if it's available
    return name_parts[0] if name_parts else ""
