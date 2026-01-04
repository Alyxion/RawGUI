"""Input element for text entry."""

from __future__ import annotations

from typing import Callable, Optional

from ..element import Element
from ..mixins import DisableableElement, ValueElement


class Input(DisableableElement, ValueElement[str], Element):
    """A text input element.

    Supports single-line text entry with optional placeholder,
    validation, and change handlers.

    Example:
        ui.input(label='Name', placeholder='Enter your name')
        ui.input(value='default').on_change(lambda e: print(e.value))
    """

    def __init__(
        self,
        label: str = "",
        *,
        placeholder: str = "",
        value: str = "",
        password: bool = False,
        on_change: Optional[Callable] = None,
    ) -> None:
        """Initialize the input.

        Args:
            label: The input label
            placeholder: Placeholder text when empty
            value: Initial value
            password: Whether to mask input as password
            on_change: Change handler callback
        """
        super().__init__(value=value, tag="input")

        self.label = label
        self.placeholder = placeholder
        self.password = password

        if on_change:
            self.on_change(on_change)

    def on_change(self, handler: Callable) -> "Input":
        """Register a change handler.

        Note: In NiceGUI the method is on_value_change, but the
        constructor uses on_change. We support both.

        Args:
            handler: The change callback

        Returns:
            Self for method chaining
        """
        return self.on("change", handler)

    def on_value_change(self, handler: Callable) -> "Input":
        """Register a value change handler (alias for on_change).

        Args:
            handler: The change callback

        Returns:
            Self for method chaining
        """
        return self.on_change(handler)

    def __repr__(self) -> str:
        return f"Input(id={self.id}, label={self.label!r}, value={self.value!r})"
