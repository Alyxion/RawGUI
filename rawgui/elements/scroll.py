"""Scroll area component.

NiceGUI-compatible scrollable container.
"""

from __future__ import annotations

from typing import Optional

from ..element import Element
from ..slot import Slot


class ScrollArea(Element):
    """A scrollable container area.

    Features:
    - Vertical and horizontal scrolling
    - Scroll position tracking
    - Keyboard navigation

    Example:
        with ui.scroll_area():
            for i in range(100):
                ui.label(f'Line {i}')
    """

    def __init__(self) -> None:
        """Create a scroll area."""
        super().__init__()
        self.tag = "scroll_area"

        # Scroll state
        self._scroll_x = 0
        self._scroll_y = 0

        # Content slot
        self._content_slot = Slot(self)

    @property
    def scroll_x(self) -> int:
        """Get horizontal scroll position."""
        return self._scroll_x

    @scroll_x.setter
    def scroll_x(self, val: int) -> None:
        """Set horizontal scroll position."""
        self._scroll_x = max(0, val)

    @property
    def scroll_y(self) -> int:
        """Get vertical scroll position."""
        return self._scroll_y

    @scroll_y.setter
    def scroll_y(self, val: int) -> None:
        """Set vertical scroll position."""
        self._scroll_y = max(0, val)

    def scroll_to(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Scroll to position."""
        if x is not None:
            self.scroll_x = x
        if y is not None:
            self.scroll_y = y

    def scroll_by(self, dx: int = 0, dy: int = 0) -> None:
        """Scroll by delta."""
        self.scroll_x += dx
        self.scroll_y += dy

    def scroll_to_top(self) -> None:
        """Scroll to top."""
        self.scroll_y = 0

    def scroll_to_bottom(self) -> None:
        """Scroll to bottom (requires content height calculation)."""
        # Will be calculated during render
        self._scroll_y = 999999

    def __enter__(self) -> "ScrollArea":
        """Enter context."""
        self._content_slot.__enter__()
        return self

    def __exit__(self, *args) -> None:
        """Exit context."""
        self._content_slot.__exit__(*args)


class Expansion(Element):
    """An expandable/collapsible section.

    Features:
    - Click to expand/collapse
    - Animated transition (in GUI terminals)
    - Icon indicator

    Example:
        with ui.expansion('Advanced Options'):
            ui.checkbox('Option 1')
            ui.checkbox('Option 2')
    """

    def __init__(
        self,
        text: str = "",
        *,
        value: bool = False,
        icon: Optional[str] = None,
    ) -> None:
        """Create an expansion panel.

        Args:
            text: Header text
            value: Initially expanded
            icon: Optional icon name
        """
        super().__init__()
        self.tag = "expansion"
        self.text = text
        self._value = value
        self.icon = icon

        # Content slot
        self._content_slot = Slot(self)

    @property
    def value(self) -> bool:
        """Whether expanded."""
        return self._value

    @value.setter
    def value(self, val: bool) -> None:
        """Set expanded state."""
        old = self._value
        self._value = val
        if old != val:
            self._fire_event("change", val)

    def open(self) -> None:
        """Expand the panel."""
        self.value = True

    def close(self) -> None:
        """Collapse the panel."""
        self.value = False

    def toggle(self) -> None:
        """Toggle expanded state."""
        self.value = not self._value

    def __enter__(self) -> "Expansion":
        """Enter context."""
        self._content_slot.__enter__()
        return self

    def __exit__(self, *args) -> None:
        """Exit context."""
        self._content_slot.__exit__(*args)
