"""Streamlit widgets for JVCLI client app."""

from typing import Any, Optional

import streamlit as st
import yaml

from jvclient.lib.utils import call_get_action, call_update_action


def app_header(agent_id: str, action_id: str, info: dict) -> tuple:
    """Render the app header and return model key and module root."""

    # Create a dynamic key for the session state using the action_id
    model_key = f"model_{agent_id}_{action_id}"
    module_root = info.get("config", {}).get("module_root")

    # Initialize session state if not already
    if model_key not in st.session_state:
        # Copy original data to prevent modification of original_data
        st.session_state[model_key] = call_get_action(
            agent_id=agent_id, action_id=action_id
        )

    # add standard action app header
    st.header(
        st.session_state[model_key]
        .get("_package", {})
        .get("meta", {})
        .get("title", "Action"),
        divider=True,
    )

    # Display the description from the model
    if description := st.session_state[model_key].get("description", False):
        st.text(description)

    def update_action() -> None:
        st.session_state[model_key]
        call_update_action(
            agent_id=agent_id,
            action_id=action_id,
            action_data=st.session_state[model_key],
        )

    current_state = st.session_state[model_key]["enabled"]
    new_state = st.checkbox(
        "Enabled",
        key="enabled",
        value=current_state,
    )

    if new_state != current_state:
        st.session_state[model_key]["enabled"] = new_state
        update_action()
        st.rerun()

    return model_key, module_root


def snake_to_title(snake_str: str) -> str:
    """Convert a snake_case string to Title Case."""
    return snake_str.replace("_", " ").title()


def app_controls(
    agent_id: str,
    action_id: str,
    hidden: Optional[list] = None,
    masked: Optional[list] = None,
) -> None:
    """Render the app controls for a given agent and action."""
    if hidden is None:
        hidden = []
    if masked is None:
        masked = []

    # Generate a dynamic key for the session state using the action_id
    model_key = f"model_{agent_id}_{action_id}"

    default_hidden_keys = ["data"]

    # Combine default masked keys with additional keys specified in 'masked'
    default_masked_keys = [
        "password",
        "token",
        "api_key",
        "key",
        "secret",
        "secret_key",
    ]
    all_masked_keys = set(default_masked_keys + masked)
    all_hidden_keys = set(default_hidden_keys + hidden)

    # Recursive function to handle nested dictionaries
    def render_fields(item_key: str, value: Any, parent_key: str = "") -> None:
        """Render fields based on their type."""

        # Skip rendering if the field is in the hidden list
        if item_key.lower() in all_hidden_keys:
            return

        field_type = type(value)
        label = snake_to_title(item_key)  # Convert item_key to Title Case

        # Special case for masked fields to render as a password field
        if item_key.lower() in all_masked_keys:
            st.session_state[model_key][item_key] = st.text_input(
                label, value=value, type="password", key=item_key
            )

        elif field_type == int:
            st.session_state[model_key][item_key] = st.number_input(
                label, value=value, step=1, key=item_key
            )

        elif field_type == float:
            st.session_state[model_key][item_key] = st.number_input(
                label, value=value, step=0.01, key=item_key
            )

        elif field_type == bool:
            st.session_state[model_key][item_key] = st.checkbox(
                label, value=value, key=item_key
            )

        elif field_type == list:
            yaml_str = st.text_area(
                label + " (YAML format)",
                value=yaml.dump(value, sort_keys=False),
                key=item_key,
            )
            try:
                # Update the list with the user-defined YAML
                loaded_value = yaml.safe_load(yaml_str)
                if not isinstance(loaded_value, list):
                    raise ValueError("The provided YAML does not produce a list.")
                st.session_state[model_key][item_key] = loaded_value
            except (yaml.YAMLError, ValueError) as e:
                st.error(f"Error parsing YAML for {item_key}: {e}")

        elif field_type == str:
            if len(value) > 100:
                st.session_state[model_key][item_key] = st.text_area(
                    label, value=value, key=item_key
                )
            else:
                st.session_state[model_key][item_key] = st.text_input(
                    label, value=value, key=item_key
                )

        elif field_type == dict:
            yaml_str = st.text_area(
                label + " (YAML format)",
                value=yaml.dump(value, sort_keys=False),
                key=item_key,
            )
            try:
                # Update the dictionary with the user-defined YAML
                st.session_state[model_key][item_key] = yaml.safe_load(yaml_str) or {}
            except yaml.YAMLError as e:
                st.error(f"Error parsing YAML for {item_key}: {e}")

        else:
            st.write(f"Unsupported type for {item_key}: {field_type}")

    # Iterate over keys of context except specific keys
    keys_to_iterate = [
        key
        for key in (st.session_state[model_key]).keys()
        if key not in ["id", "version", "label", "description", "enabled", "_package"]
    ]

    for item_key in keys_to_iterate:
        render_fields(item_key, st.session_state[model_key][item_key])


def app_update_action(agent_id: str, action_id: str) -> None:
    """Add a standard update button to apply changes."""

    model_key = f"model_{agent_id}_{action_id}"

    st.divider()

    if st.button("Update"):
        result = call_update_action(
            agent_id=agent_id,
            action_id=action_id,
            action_data=st.session_state[model_key],
        )
        if result and result.get("id", "") == action_id:
            st.success("Changes saved")
        else:
            st.error("Unable to save changes")


def dynamic_form(
    field_definitions: list,
    initial_data: Optional[list] = None,
    session_key: str = "dynamic_form",
) -> list:
    """
    Create a dynamic form widget with add/remove functionality.

    Parameters:
    - field_definitions: A list of dictionaries where each dictionary defines a field
                         with 'name', 'type', and any specific 'options' if needed.
    - initial_data: A list of dictionaries to initialize the form with predefined values.
    - session_key: A unique key to store and manage session state of the form.

    Returns:
    - list: The current value of the dynamic form.
    """
    if session_key not in st.session_state:
        if initial_data is not None:
            st.session_state[session_key] = []
            for idx, row_data in enumerate(initial_data):
                fields = {
                    field["name"]: row_data.get(field["name"], "")
                    for field in field_definitions
                }
                st.session_state[session_key].append({"id": idx, "fields": fields})
        else:
            st.session_state[session_key] = [
                {"id": 0, "fields": {field["name"]: "" for field in field_definitions}}
            ]

    def add_row() -> None:  # pragma: no cover, don't know how to test this yet 😅
        """Add a new row to the dynamic form."""
        new_id = (
            max((item["id"] for item in st.session_state[session_key]), default=-1) + 1
        )
        new_row = {
            "id": new_id,
            "fields": {field["name"]: "" for field in field_definitions},
        }
        st.session_state[session_key].append(new_row)

    def remove_row(
        id_to_remove: int,
    ) -> None:  # pragma: no cover, don't know how to test this yet 😅
        """Remove a row from the dynamic form."""
        st.session_state[session_key] = [
            item for item in st.session_state[session_key] if item["id"] != id_to_remove
        ]

    for item in st.session_state[session_key]:
        # Display fields in a row
        row_cols = st.columns(len(field_definitions))
        for i, field in enumerate(field_definitions):
            field_name = field["name"]
            field_type = field.get("type", "text")
            options = field.get("options", [])

            if field_type == "text":
                item["fields"][field_name] = row_cols[i].text_input(
                    field_name,
                    value=item["fields"][field_name],
                    key=f"{session_key}_{item['id']}_{field_name}",
                )
            elif field_type == "number":
                field_value = item["fields"][field_name]
                if field_value == "":
                    field_value = 0
                item["fields"][field_name] = row_cols[i].number_input(
                    field_name,
                    value=int(field_value),
                    key=f"{session_key}_{item['id']}_{field_name}",
                )
            elif field_type == "select":
                item["fields"][field_name] = row_cols[i].selectbox(
                    field_name,
                    options,
                    index=(
                        options.index(item["fields"][field_name])
                        if item["fields"][field_name] in options
                        else 0
                    ),
                    key=f"{session_key}_{item['id']}_{field_name}",
                )

        # Add a remove button in a new row beneath the fields, aligned to the left
        with st.container():
            if st.button(
                "Remove",
                key=f"remove_{item['id']}",
                on_click=lambda id=item["id"]: remove_row(id),
            ):
                pass

    # Add a divider above the "Add Row" button
    st.divider()

    # Button to add a new row
    st.button("Add Row", on_click=add_row)

    # Return the current value of the dynamic form
    return [item["fields"] for item in st.session_state[session_key]]
