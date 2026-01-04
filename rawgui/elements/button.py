"""Button element for user interaction."""

from __future__ import annotations

from typing import Callable, Optional

from ..element import Element
from ..mixins import DisableableElement, TextElement


class Button(DisableableElement, TextElement, Element):
    """A clickable button element.

    Supports text labels, icons, and click handlers.

    Example:
        ui.button('Click me', on_click=lambda: print('clicked'))
        ui.button('Submit').props('color=primary')
    """

    def __init__(
        self,
        text: str = "",
        *,
        on_click: Optional[Callable] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
    ) -> None:
        """Initialize the button.

        Args:
            text: The button text
            on_click: Click handler callback
            icon: Optional icon name
            color: Optional color
        """
        super().__init__(text=text, tag="button")

        self.icon = icon
        self.color = color

        if on_click:
            self.on_click(on_click)

    def on_click(self, handler: Callable) -> "Button":
        """Register a click handler.

        Args:
            handler: The click callback

        Returns:
            Self for method chaining
        """
        return self.on("click", handler)

    def click(self) -> None:
        """Programmatically trigger a click event."""
        if self.enabled:
            self._fire_event("click")

    def __repr__(self) -> str:
        return f"Button(id={self.id}, text={self.text!r}, enabled={self.enabled})"
