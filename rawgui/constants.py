"""Global constants for RawGUI layout system.

NOTE: These are DEFAULT values only. Actual values should come from
SessionConfig for proper multi-session support.

See config.py for the session-based configuration system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import SessionConfig

# =============================================================================
# DEFAULT PIXEL-TO-ASCII SCALING CONSTANTS
# These are defaults - actual values come from SessionConfig per session
# =============================================================================

# Default: 1 ASCII character = this many "pixels"
DEFAULT_CHAR_WIDTH_PX = 12   # 1 column = 12 pixels wide
DEFAULT_CHAR_HEIGHT_PX = 24  # 1 row = 24 pixels tall

# Legacy aliases (for backwards compatibility during refactoring)
# TODO: Remove these once all code uses SessionConfig
CHAR_WIDTH_PX = DEFAULT_CHAR_WIDTH_PX
CHAR_HEIGHT_PX = DEFAULT_CHAR_HEIGHT_PX


# =============================================================================
# HELPER FUNCTIONS (use defaults when no session context available)
# =============================================================================

def px_to_cols(pixels: int, config: "SessionConfig" = None) -> int:
    """Convert pixel width to ASCII columns.

    Args:
        pixels: Width in pixels
        config: Optional session config (uses default if None)

    Returns:
        Number of ASCII columns
    """
    width = config.char_width_px if config else DEFAULT_CHAR_WIDTH_PX
    return pixels // width


def px_to_rows(pixels: int, config: "SessionConfig" = None) -> int:
    """Convert pixel height to ASCII rows.

    Args:
        pixels: Height in pixels
        config: Optional session config (uses default if None)

    Returns:
        Number of ASCII rows
    """
    height = config.char_height_px if config else DEFAULT_CHAR_HEIGHT_PX
    return pixels // height


def cols_to_px(cols: int, config: "SessionConfig" = None) -> int:
    """Convert ASCII columns to pixel width.

    Args:
        cols: Number of columns
        config: Optional session config (uses default if None)

    Returns:
        Width in pixels
    """
    width = config.char_width_px if config else DEFAULT_CHAR_WIDTH_PX
    return cols * width


def rows_to_px(rows: int, config: "SessionConfig" = None) -> int:
    """Convert ASCII rows to pixel height.

    Args:
        rows: Number of rows
        config: Optional session config (uses default if None)

    Returns:
        Height in pixels
    """
    height = config.char_height_px if config else DEFAULT_CHAR_HEIGHT_PX
    return rows * height


# =============================================================================
# STANDARD COMPONENT HEIGHTS (in rows, using defaults)
# =============================================================================

HEIGHT_LABEL = DEFAULT_CHAR_HEIGHT_PX           # 1 row
HEIGHT_BUTTON = DEFAULT_CHAR_HEIGHT_PX          # 1 row (content only, border adds 2 more)
HEIGHT_BUTTON_COMPACT = DEFAULT_CHAR_HEIGHT_PX  # 1 row total (no border)
HEIGHT_INPUT = DEFAULT_CHAR_HEIGHT_PX           # 1 row (content only)
HEIGHT_ROW_SINGLE = DEFAULT_CHAR_HEIGHT_PX      # 1 row

# Padding defaults
PADDING_XS = DEFAULT_CHAR_WIDTH_PX      # 1 char
PADDING_SM = DEFAULT_CHAR_WIDTH_PX * 2  # 2 chars
PADDING_MD = DEFAULT_CHAR_WIDTH_PX * 3  # 3 chars
PADDING_LG = DEFAULT_CHAR_WIDTH_PX * 4  # 4 chars
