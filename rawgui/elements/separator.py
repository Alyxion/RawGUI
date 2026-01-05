"""Separator component.

NiceGUI-compatible visual separator/divider.
"""

from __future__ import annotations

from typing import Optional

from ..element import Element


class Separator(Element):
    """A horizontal or vertical separator line.

    Features:
    - Horizontal or vertical orientation
    - Configurable character
    - Optional margins

    Example:
        ui.separator()
        ui.separator(vertical=True)
    """

    def __init__(
        self,
        *,
        vertical: bool = False,
        char: Optional[str] = None,
    ) -> None:
        """Create a separator.

        Args:
            vertical: Vertical orientation (default horizontal)
            char: Character to use (default: '-' or '|')
        """
        super().__init__()
        self.tag = "separator"
        self.vertical = vertical
        self.char = char or ("|" if vertical else "-")


class Space(Element):
    """Empty space element.

    Used to add fixed spacing between elements.

    Example:
        ui.button('A')
        ui.space()
        ui.button('B')
    """

    def __init__(self, *, width: int = 1, height: int = 1) -> None:
        """Create a space.

        Args:
            width: Width in characters
            height: Height in rows
        """
        super().__init__()
        self.tag = "space"
        self.width = width
        self.height = height


class Divider(Separator):
    """Alias for Separator (alternative naming)."""

    pass
