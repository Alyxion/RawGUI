"""Menu components.

NiceGUI-compatible context menu and menu items.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from ..element import Element
from ..slot import Slot


class MenuItem(Element):
    """A single menu item.

    Example:
        with ui.menu():
            ui.menu_item('Open', on_click=handle_open)
            ui.menu_item('Save', on_click=handle_save)
            ui.menu_item('Exit', on_click=handle_exit)
    """

    def __init__(
        self,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        *,
        auto_close: bool = True,
    ) -> None:
        """Create a menu item.

        Args:
            text: Item text
            on_click: Click handler
            auto_close: Auto-close menu on click
        """
        super().__init__()
        self.tag = "menu_item"
        self.text = text
        self._on_click = on_click
        self.auto_close = auto_close

        if on_click:
            self.on("click", lambda: on_click())

    def click(self) -> None:
        """Trigger click action."""
        if self._on_click:
            self._on_click()


class Menu(Element):
    """A popup/context menu.

    Features:
    - Keyboard navigation
    - Submenu support
    - Auto-positioning

    Example:
        with ui.button('Menu') as button:
            with ui.menu():
                ui.menu_item('Action 1')
                ui.menu_item('Action 2')
    """

    def __init__(self) -> None:
        """Create a menu."""
        super().__init__()
        self.tag = "menu"
        self._is_open = False
        self._z_index = 50

        # Create content slot
        self._content_slot = Slot(self)

    @property
    def is_open(self) -> bool:
        """Whether menu is open."""
        return self._is_open

    def open(self) -> None:
        """Open the menu."""
        self._is_open = True
        self.visible = True

    def close(self) -> None:
        """Close the menu."""
        self._is_open = False
        self.visible = False

    def toggle(self) -> None:
        """Toggle menu open/closed."""
        if self._is_open:
            self.close()
        else:
            self.open()

    def __enter__(self) -> "Menu":
        """Enter context."""
        self._content_slot.__enter__()
        return self

    def __exit__(self, *args) -> None:
        """Exit context."""
        self._content_slot.__exit__(*args)
        # Start hidden
        self.visible = False


class ContextMenu(Menu):
    """A right-click context menu.

    Appears at cursor position on right-click.

    Example:
        with ui.element('div'):
            with ui.context_menu():
                ui.menu_item('Copy')
                ui.menu_item('Paste')
    """

    def __init__(self) -> None:
        """Create a context menu."""
        super().__init__()
        self.tag = "context_menu"


class MenuSeparator(Element):
    """A separator line within a menu.

    Example:
        with ui.menu():
            ui.menu_item('Open')
            ui.menu_separator()
            ui.menu_item('Exit')
    """

    def __init__(self) -> None:
        """Create a menu separator."""
        super().__init__()
        self.tag = "menu_separator"
