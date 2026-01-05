"""Checkbox element for boolean input."""

from __future__ import annotations

from typing import Callable, Optional

from ..element import Element
from ..mixins import DisableableElement


class Checkbox(DisableableElement, Element):
    """A checkbox for boolean input.

    Can be checked or unchecked. Supports text labels and change handlers.

    Example:
        ui.checkbox("Accept terms", on_change=lambda v: print(f"Accepted: {v}"))
        ui.checkbox("Remember me", value=True)
    """

    def __init__(
        self,
        text: str = "",
        *,
        value: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """Initialize the checkbox.

        Args:
            text: Label text displayed next to the checkbox
            value: Initial checked state
            on_change: Callback when value changes
        """
        super().__init__(tag="checkbox")

        self.text = text
        self._value = value

        if on_change:
            self.on("change", on_change)

    @property
    def value(self) -> bool:
        """Get the checked state."""
        return self._value

    @value.setter
    def value(self, new_value: bool) -> None:
        """Set the checked state."""
        if self._value != new_value:
            self._value = new_value
            self._fire_event("change", new_value)

    def toggle(self) -> None:
        """Toggle the checkbox state."""
        if self.enabled:
            self.value = not self.value

    def on_change(self, handler: Callable[[bool], None]) -> "Checkbox":
        """Register a change handler.

        Args:
            handler: Callback receiving the new value

        Returns:
            Self for method chaining
        """
        return self.on("change", handler)

    def __repr__(self) -> str:
        return f"Checkbox(id={self.id}, text={self.text!r}, value={self.value})"
