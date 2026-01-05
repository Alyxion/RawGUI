"""Dialog component with modal behavior and shadow effect.

Implements NiceGUI-compatible dialog with Norton Commander-style shadows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

from ..element import Element
from ..slot import Slot

if TYPE_CHECKING:
    pass


class Dialog(Element):
    """A modal dialog that floats above other content.

    Features:
    - Modal overlay (blocks interaction with content below)
    - Norton Commander-style shadow effect
    - open() and close() methods
    - Context manager support for content

    Example:
        with ui.dialog() as dialog:
            with ui.card():
                ui.label('Hello!')
                ui.button('Close', on_click=dialog.close)

        ui.button('Open', on_click=dialog.open)
    """

    def __init__(
        self,
        *,
        value: bool = False,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        """Create a dialog.

        Args:
            value: Whether dialog is initially open
            on_close: Callback when dialog is closed
        """
        super().__init__()
        self.tag = "dialog"
        self._is_open = value
        self._on_close = on_close

        # Dialog floats above normal content
        self._z_index = 100

        # Shadow configuration (Norton Commander style)
        self._has_shadow = True
        self._shadow_offset_x = 2
        self._shadow_offset_y = 1

        # For positioning
        self._center_x: Optional[int] = None
        self._center_y: Optional[int] = None

        # Create content slot
        self._content_slot = Slot(self)

        # Start hidden if not initially open
        if not value:
            self.visible = False

    @property
    def is_open(self) -> bool:
        """Whether the dialog is currently open."""
        return self._is_open

    @property
    def value(self) -> bool:
        """Alias for is_open (NiceGUI compatibility)."""
        return self._is_open

    @value.setter
    def value(self, val: bool) -> None:
        if val:
            self.open()
        else:
            self.close()

    def open(self) -> None:
        """Open the dialog."""
        if not self._is_open:
            self._is_open = True
            self.visible = True
            self._fire_event("open")

    def close(self) -> None:
        """Close the dialog."""
        if self._is_open:
            self._is_open = False
            self.visible = False
            self._fire_event("close")
            if self._on_close:
                self._on_close()

    def toggle(self) -> None:
        """Toggle dialog open/closed state."""
        if self._is_open:
            self.close()
        else:
            self.open()

    def __enter__(self) -> "Dialog":
        """Enter context - push content slot."""
        self._content_slot.__enter__()
        return self

    def __exit__(self, *args) -> None:
        """Exit context - pop content slot."""
        self._content_slot.__exit__(*args)
        # Start hidden by default
        if not self._is_open:
            self.visible = False

    def submit(self, result=None) -> None:
        """Submit the dialog with a result and close it.

        Args:
            result: Optional result value
        """
        self._fire_event("submit", result)
        self.close()

    def props(self, add: Optional[str] = None) -> "Dialog":
        """Set dialog properties (NiceGUI compatibility)."""
        # Parse props string if provided
        return self


class Notification(Element):
    """A temporary notification/toast message.

    Appears briefly then disappears automatically.
    """

    def __init__(
        self,
        message: str,
        *,
        position: str = "bottom-right",
        type: str = "info",
        timeout: float = 3.0,
        close_button: bool = False,
    ) -> None:
        """Create a notification.

        Args:
            message: Message to display
            position: Where to show (top-left, top-right, bottom-left, bottom-right, center)
            type: Notification type (info, success, warning, error)
            timeout: Seconds until auto-dismiss (0 = no auto-dismiss)
            close_button: Show close button
        """
        super().__init__()
        self.tag = "notification"
        self.message = message
        self.position = position
        self.type = type
        self.timeout = timeout
        self.close_button = close_button
        self._z_index = 200  # Above dialogs

        # Start visible
        self.visible = True

    def dismiss(self) -> None:
        """Dismiss the notification."""
        self.visible = False
        self._fire_event("dismiss")
