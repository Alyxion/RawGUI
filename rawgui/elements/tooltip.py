"""Tooltip component.

NiceGUI-compatible tooltip and popup text.
"""

from __future__ import annotations

from typing import Optional

from ..element import Element


class Tooltip(Element):
    """A tooltip that appears on hover.

    Features:
    - Hover-triggered display
    - Auto-positioning
    - Configurable delay

    Example:
        with ui.button('Hover me'):
            ui.tooltip('This is a tooltip')
    """

    def __init__(
        self,
        text: str,
        *,
        delay: float = 0.5,
    ) -> None:
        """Create a tooltip.

        Args:
            text: Tooltip text
            delay: Delay before showing (seconds)
        """
        super().__init__()
        self.tag = "tooltip"
        self.text = text
        self.delay = delay
        self._z_index = 150

        # Start hidden
        self.visible = False


class Badge(Element):
    """A small badge/tag indicator.

    Features:
    - Compact display
    - Color variants
    - Can overlay other elements

    Example:
        with ui.button('Messages'):
            ui.badge('5')
    """

    def __init__(
        self,
        text: str = "",
        *,
        color: Optional[str] = None,
        text_color: Optional[str] = None,
        outline: bool = False,
    ) -> None:
        """Create a badge.

        Args:
            text: Badge text/number
            color: Background color
            text_color: Text color
            outline: Outline style instead of filled
        """
        super().__init__()
        self.tag = "badge"
        self.text = text
        self.color = color
        self.text_color = text_color
        self.outline = outline


class Chip(Element):
    """A compact element representing a tag or choice.

    Features:
    - Removable option
    - Icon support
    - Selectable

    Example:
        ui.chip('Python', removable=True)
    """

    def __init__(
        self,
        text: str,
        *,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        removable: bool = False,
        on_click: Optional[callable] = None,
    ) -> None:
        """Create a chip.

        Args:
            text: Chip text
            icon: Optional icon name
            color: Background color
            removable: Show remove button
            on_click: Click handler
        """
        super().__init__()
        self.tag = "chip"
        self.text = text
        self.icon = icon
        self.color = color
        self.removable = removable

        if on_click:
            self.on("click", on_click)

    def remove(self) -> None:
        """Remove the chip."""
        self._fire_event("remove")
        self.delete()
