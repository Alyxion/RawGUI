"""Layout components for page structure.

NiceGUI-compatible header, footer, and drawer components.
"""

from __future__ import annotations

from typing import Optional, Callable

from ..element import Element


class Header(Element):
    """Page header component.

    Renders at the top of the terminal window.

    Example:
        with ui.header():
            ui.label('My App')
    """

    def __init__(self, *, value: bool = True, fixed: bool = True) -> None:
        """Create a header.

        Args:
            value: Whether header is visible
            fixed: Whether header stays at top when scrolling
        """
        super().__init__()
        self.tag = "header"
        self._visible = value
        self.fixed = fixed

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, val: bool) -> None:
        self._visible = val

    def show(self) -> None:
        """Show the header."""
        self._visible = True

    def hide(self) -> None:
        """Hide the header."""
        self._visible = False

    def toggle(self) -> None:
        """Toggle header visibility."""
        self._visible = not self._visible


class Footer(Element):
    """Page footer component.

    Renders at the bottom of the terminal window.

    Example:
        with ui.footer():
            ui.label('Status: Ready')
    """

    def __init__(self, *, value: bool = True, fixed: bool = True) -> None:
        """Create a footer.

        Args:
            value: Whether footer is visible
            fixed: Whether footer stays at bottom when scrolling
        """
        super().__init__()
        self.tag = "footer"
        self._visible = value
        self.fixed = fixed

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, val: bool) -> None:
        self._visible = val

    def show(self) -> None:
        """Show the footer."""
        self._visible = True

    def hide(self) -> None:
        """Hide the footer."""
        self._visible = False

    def toggle(self) -> None:
        """Toggle footer visibility."""
        self._visible = not self._visible


class Drawer(Element):
    """Side drawer component.

    Renders as a slide-out panel from the side of the screen.

    Example:
        with ui.left_drawer() as drawer:
            ui.label('Menu')
    """

    def __init__(
        self,
        side: str = "left",
        *,
        value: bool = False,
        fixed: bool = True,
        top_corner: bool = False,
        bottom_corner: bool = False,
    ) -> None:
        """Create a drawer.

        Args:
            side: 'left' or 'right'
            value: Whether drawer is open
            fixed: Whether drawer overlays content
            top_corner: Extend into header area
            bottom_corner: Extend into footer area
        """
        super().__init__()
        self.tag = "drawer"
        self.side = side
        self._is_open = value
        self.fixed = fixed
        self.top_corner = top_corner
        self.bottom_corner = bottom_corner
        if not value:
            self.visible = False

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        """Open the drawer."""
        self._is_open = True
        self.visible = True

    def close(self) -> None:
        """Close the drawer."""
        self._is_open = False
        self.visible = False

    def toggle(self) -> None:
        """Toggle drawer open/close."""
        if self._is_open:
            self.close()
        else:
            self.open()


class LeftDrawer(Drawer):
    """Left-side drawer."""

    def __init__(self, **kwargs) -> None:
        super().__init__(side="left", **kwargs)


class RightDrawer(Drawer):
    """Right-side drawer."""

    def __init__(self, **kwargs) -> None:
        super().__init__(side="right", **kwargs)


class PageSticky(Element):
    """Sticky positioned element.

    Stays fixed at a specific position on screen.

    Example:
        with ui.page_sticky(position='bottom-right'):
            ui.button('Help')
    """

    POSITIONS = {
        "top-left": (0, 0),
        "top-right": (1, 0),
        "bottom-left": (0, 1),
        "bottom-right": (1, 1),
        "top": (0.5, 0),
        "bottom": (0.5, 1),
        "left": (0, 0.5),
        "right": (1, 0.5),
    }

    def __init__(
        self,
        position: str = "bottom-right",
        *,
        x_offset: int = 0,
        y_offset: int = 0,
    ) -> None:
        """Create a sticky element.

        Args:
            position: Position name ('top-left', 'bottom-right', etc.)
            x_offset: Horizontal offset from position
            y_offset: Vertical offset from position
        """
        super().__init__()
        self.tag = "page_sticky"
        self.position = position
        self.x_offset = x_offset
        self.y_offset = y_offset


class Grid(Element):
    """Grid layout container.

    Creates a CSS-style grid layout.

    Example:
        with ui.grid(columns=3):
            ui.label('A')
            ui.label('B')
            ui.label('C')
    """

    def __init__(
        self,
        columns: int = 2,
        *,
        rows: Optional[int] = None,
    ) -> None:
        """Create a grid.

        Args:
            columns: Number of columns
            rows: Number of rows (auto if None)
        """
        super().__init__()
        self.tag = "grid"
        self.columns = columns
        self.rows = rows


class Splitter(Element):
    """Resizable split pane.

    Divides content into two resizable sections.

    Example:
        with ui.splitter() as splitter:
            with splitter.before:
                ui.label('Left')
            with splitter.after:
                ui.label('Right')
    """

    def __init__(
        self,
        *,
        horizontal: bool = False,
        value: int = 50,
    ) -> None:
        """Create a splitter.

        Args:
            horizontal: Split horizontally instead of vertically
            value: Initial split position (percentage)
        """
        super().__init__()
        self.tag = "splitter"
        self.horizontal = horizontal
        self._value = value
        # Create before/after slots
        from ..slot import Slot
        self.before = Slot(self, "before")
        self.after = Slot(self, "after")

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        self._value = max(0, min(100, val))
