"""Image and media components.

NiceGUI-compatible image/icon display using ASCII art.
"""

from __future__ import annotations

from typing import Optional

from ..element import Element


class Image(Element):
    """An image displayed as ASCII art.

    In terminals that support it, may use sixel graphics.
    Otherwise falls back to ASCII/block character art.

    Example:
        ui.image('logo.png')
        ui.image(source='https://example.com/image.png')
    """

    def __init__(
        self,
        source: str = "",
        *,
        alt: str = "",
    ) -> None:
        """Create an image.

        Args:
            source: Image path or URL
            alt: Alternative text
        """
        super().__init__()
        self.tag = "image"
        self.source = source
        self.alt = alt

    def set_source(self, source: str) -> None:
        """Change the image source."""
        self.source = source


class Icon(Element):
    """An icon from a symbol set.

    Uses ASCII/Unicode character representations.

    Example:
        ui.icon('home')
        ui.icon('settings', size='lg')
    """

    # Simple ASCII icon mappings
    ICONS = {
        "home": "[H]",
        "settings": "[*]",
        "user": "[@]",
        "search": "[?]",
        "menu": "[=]",
        "close": "[X]",
        "check": "[v]",
        "arrow_left": "<-",
        "arrow_right": "->",
        "arrow_up": "^",
        "arrow_down": "v",
        "plus": "[+]",
        "minus": "[-]",
        "edit": "[/]",
        "delete": "[x]",
        "save": "[S]",
        "file": "[F]",
        "folder": "[D]",
        "star": "[*]",
        "heart": "<3",
        "info": "(i)",
        "warning": "/!\\",
        "error": "(X)",
        "help": "(?)",
    }

    def __init__(
        self,
        name: str,
        *,
        size: Optional[str] = None,
        color: Optional[str] = None,
    ) -> None:
        """Create an icon.

        Args:
            name: Icon name
            size: Icon size ('sm', 'md', 'lg', 'xl')
            color: Icon color
        """
        super().__init__()
        self.tag = "icon"
        self.name = name
        self.size = size or "md"
        self.color = color

    @property
    def text(self) -> str:
        """Get ASCII representation of icon."""
        return self.ICONS.get(self.name, f"[{self.name[:1]}]")


class Avatar(Element):
    """A user avatar display.

    Shows initials or image in circular frame.

    Example:
        ui.avatar('JD')  # John Doe initials
        ui.avatar(icon='user')
    """

    def __init__(
        self,
        text: Optional[str] = None,
        *,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
    ) -> None:
        """Create an avatar.

        Args:
            text: Avatar text (usually initials)
            icon: Icon name instead of text
            color: Background color
            size: Size ('sm', 'md', 'lg', 'xl')
        """
        super().__init__()
        self.tag = "avatar"
        self.text = text
        self.icon = icon
        self.color = color
        self.size = size or "md"
