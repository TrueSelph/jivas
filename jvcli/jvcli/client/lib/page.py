"""This module contains the Page class used for managing pages in the JVCLI client."""

from typing import Callable, Dict, Optional

import streamlit as st
from streamlit_router import StreamlitRouter


class Page:
    """Class to manage pages in the JVCLI client."""

    def __init__(self, router: StreamlitRouter) -> None:
        """Initialize the Page with a router."""
        self._router: StreamlitRouter = router
        self._callback: Optional[Callable] = None
        self._label: Optional[str] = None
        self._path: Optional[str] = None
        self._key: Optional[str] = None
        self._args: Optional[Dict] = None

    def item(
        self, callback: Callable, label: str, path: str, args: Optional[Dict] = None
    ) -> "Page":
        """
        Register the page callable on the given route.

        Args:
            callback (Callable): The function to call for the page.
            label (str): The label for the page.
            path (str): The path for the page.
            args (Optional[Dict], optional): Additional arguments for the page. Defaults to None.

        Returns:
            Page: The current Page instance.
        """
        if args is None:
            args = {}
        self._callback = callback
        self._label = label
        self._path = path
        self._args = args
        self._key = f"{Page.normalize_label(label)}"
        self._router.register(func=self._callback, path=self._path, endpoint=self._key)
        return self

    def st_button(self) -> None:
        """Add the Streamlit link for this page wherever it is called."""
        if st.button(self._label, key=self._key, use_container_width=True):
            self._router.redirect(*self._router.build(self._key, self._args))

    @staticmethod
    def normalize_label(label: str) -> str:
        """
        Normalize the label to be used as a key.

        Args:
            label (str): The label to normalize.

        Returns:
            str: The normalized label.
        """
        return (
            "".join(char.lower() for char in label if char.isascii())
            .strip()
            .replace(" ", "-")
            .replace("/", "-")
            .replace(":", "-")
        )
