"""Toggle/Switch component.

NiceGUI-compatible toggle switch.
"""

from __future__ import annotations

from typing import Callable, Optional

from ..element import Element
from ..mixins import DisableableElement


class Toggle(DisableableElement, Element):
    """A toggle switch (on/off).

    Features:
    - Binary on/off state
    - Optional text label
    - Keyboard activation (Space/Enter)
    - ASCII switch visualization

    Example:
        toggle = ui.toggle('Dark mode', value=False)
        toggle.value = True
    """

    def __init__(
        self,
        text: str = "",
        *,
        value: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """Create a toggle switch.

        Args:
            text: Label text
            value: Initial state (on/off)
            on_change: Callback when toggled
        """
        super().__init__()
        self.tag = "toggle"
        self.text = text
        self._value = value
        self._on_change = on_change

    @property
    def value(self) -> bool:
        """Get toggle state."""
        return self._value

    @value.setter
    def value(self, val: bool) -> None:
        """Set toggle state."""
        old_value = self._value
        self._value = val
        if old_value != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)

    def toggle(self) -> None:
        """Toggle the switch."""
        if self.enabled:
            self.value = not self._value

    def on(self) -> None:
        """Turn on."""
        if self.enabled:
            self.value = True

    def off(self) -> None:
        """Turn off."""
        if self.enabled:
            self.value = False


class Switch(Toggle):
    """Alias for Toggle (NiceGUI compatibility)."""

    pass
