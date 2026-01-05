"""Session-based configuration for RawGUI.

Each session has its own configuration to support:
- Multiple concurrent terminal sessions
- Different terminal dimensions and scaling factors
- Per-session CSS-like property lookups

NEVER use global variables for session-specific state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class SessionConfig:
    """Per-session configuration.

    Stores scaling factors, CSS property lookups, and terminal-specific settings.
    Each Client/Session should have its own SessionConfig instance.
    """

    # ==========================================================================
    # PIXEL-TO-ASCII SCALING (can vary per terminal)
    # ==========================================================================

    # Default scaling: 1 ASCII character = these pixel dimensions
    char_width_px: int = 12   # 1 column = 12 pixels wide
    char_height_px: int = 24  # 1 row = 24 pixels tall

    # ==========================================================================
    # CSS-LIKE PROPERTY LOOKUPS
    # ==========================================================================

    # Named sizes (like Tailwind spacing scale)
    sizes: Dict[str, int] = field(default_factory=lambda: {
        "none": 0,
        "xs": 1,
        "sm": 2,
        "md": 4,
        "lg": 6,
        "xl": 8,
        "2xl": 12,
        "3xl": 16,
    })

    # Named colors mapping (CSS/Tailwind -> terminal)
    colors: Dict[str, str] = field(default_factory=lambda: {
        "red": "red",
        "green": "green",
        "blue": "blue",
        "yellow": "yellow",
        "cyan": "cyan",
        "magenta": "magenta",
        "white": "white",
        "black": "black",
        "gray": "bright_black",
        "grey": "bright_black",
        "orange": "yellow",
        "purple": "magenta",
        "pink": "bright_magenta",
    })

    # Standard spacing values (in char units)
    spacing: Dict[str, int] = field(default_factory=lambda: {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "8": 8,
        "10": 10,
        "12": 12,
    })

    # Component heights (in rows)
    component_heights: Dict[str, int] = field(default_factory=lambda: {
        "label": 1,
        "button": 3,  # Norton Commander style
        "input": 3,
        "checkbox": 1,
        "select": 3,
    })

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def px_to_cols(self, pixels: int) -> int:
        """Convert pixel width to ASCII columns."""
        return pixels // self.char_width_px

    def px_to_rows(self, pixels: int) -> int:
        """Convert pixel height to ASCII rows."""
        return pixels // self.char_height_px

    def cols_to_px(self, cols: int) -> int:
        """Convert ASCII columns to pixel width."""
        return cols * self.char_width_px

    def rows_to_px(self, rows: int) -> int:
        """Convert ASCII rows to pixel height."""
        return rows * self.char_height_px

    def snap_to_grid_x(self, pixels: int) -> int:
        """Snap pixel x-coordinate to nearest grid position."""
        return (pixels // self.char_width_px) * self.char_width_px

    def snap_to_grid_y(self, pixels: int) -> int:
        """Snap pixel y-coordinate to nearest grid position."""
        return (pixels // self.char_height_px) * self.char_height_px

    def get_size(self, name: str) -> int:
        """Get a named size value."""
        return self.sizes.get(name, 0)

    def get_color(self, name: str) -> Optional[str]:
        """Get a terminal color for a CSS color name."""
        return self.colors.get(name)

    def get_spacing(self, value: str) -> int:
        """Get a spacing value."""
        return self.spacing.get(value, int(value) if value.isdigit() else 0)

    def get_component_height(self, component: str) -> int:
        """Get standard height for a component type (in rows)."""
        return self.component_heights.get(component, 1)

    def tailwind_spacing_to_px(self, value: int, horizontal: bool = True) -> int:
        """Convert Tailwind spacing value to pixels.

        Tailwind: 1 unit = 4px (0.25rem)
        We round to nearest grid position.
        """
        raw_px = value * 4

        if horizontal:
            return max(self.char_width_px,
                      ((raw_px + self.char_width_px // 2) // self.char_width_px) * self.char_width_px)
        else:
            return max(self.char_height_px,
                      ((raw_px + self.char_height_px // 2) // self.char_height_px) * self.char_height_px)


# Default configuration (used when no session context is available)
# This should only be used for testing or initialization
_default_config = SessionConfig()


def get_default_config() -> SessionConfig:
    """Get a copy of the default configuration.

    Use this to create new session configs with default values.
    """
    return SessionConfig()
