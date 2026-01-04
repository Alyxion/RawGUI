"""Style mapping from CSS/Tailwind to terminal attributes.

Maps web-style classes and CSS properties to blessed terminal formatting.
Uses data-driven definitions for maintainability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from blessed import Terminal


@dataclass
class TerminalStyle:
    """Computed terminal style for an element."""

    # Text formatting
    bold: bool = False
    underline: bool = False
    italic: bool = False
    reverse: bool = False
    blink: bool = False

    # Colors (None means default)
    fg_color: Optional[str] = None
    bg_color: Optional[str] = None

    # Border style
    border: bool = False
    border_style: str = "single"  # single, double, rounded, heavy

    # Spacing (in character units)
    padding_top: int = 0
    padding_right: int = 0
    padding_bottom: int = 0
    padding_left: int = 0
    margin_top: int = 0
    margin_right: int = 0
    margin_bottom: int = 0
    margin_left: int = 0

    # Sizing
    width: Optional[int] = None
    height: Optional[int] = None
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None

    # Layout
    gap: int = 0
    align_items: str = "start"  # start, center, end, stretch
    justify_content: str = "start"  # start, center, end, space-between, space-around

    def apply(self, term: "Terminal", text: str) -> str:
        """Apply this style to text using blessed terminal."""
        result = text

        if self.bold:
            result = term.bold(result)
        if self.underline:
            result = term.underline(result)
        if self.italic and hasattr(term, "italic"):
            result = term.italic(result)
        if self.reverse:
            result = term.reverse(result)
        if self.blink and hasattr(term, "blink"):
            result = term.blink(result)

        if self.fg_color:
            color_func = getattr(term, self.fg_color, None)
            if color_func:
                result = color_func(result)
            elif self.fg_color.startswith("#"):
                r, g, b = self._hex_to_rgb(self.fg_color)
                result = term.color_rgb(r, g, b)(result)

        if self.bg_color:
            color_func = getattr(term, f"on_{self.bg_color}", None)
            if color_func:
                result = color_func(result)
            elif self.bg_color.startswith("#"):
                r, g, b = self._hex_to_rgb(self.bg_color)
                result = term.on_color_rgb(r, g, b)(result)

        return result

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# =============================================================================
# DATA-DRIVEN STYLE DEFINITIONS
# =============================================================================

# Border character sets - easily customizable
BORDER_CHARS: Dict[str, Dict[str, str]] = {
    "single": {
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "h": "─", "v": "│",
    },
    "double": {
        "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
        "h": "═", "v": "║",
    },
    "rounded": {
        "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
        "h": "─", "v": "│",
    },
    "heavy": {
        "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
        "h": "━", "v": "┃",
    },
    "none": {
        "tl": " ", "tr": " ", "bl": " ", "br": " ",
        "h": " ", "v": " ",
    },
}

# Tailwind/CSS color name to terminal color mapping
# Terminal colors: black, red, green, yellow, blue, magenta, cyan, white
# Bright variants: bright_black, bright_red, bright_green, etc.
COLOR_MAP: Dict[str, str] = {
    # CSS/Tailwind basic colors
    "red": "red",
    "green": "green",
    "blue": "blue",
    "yellow": "yellow",
    "cyan": "cyan",
    "magenta": "magenta",
    "white": "white",
    "black": "black",

    # Gray variants
    "gray": "bright_black",
    "grey": "bright_black",
    "slate": "bright_black",
    "zinc": "bright_black",
    "neutral": "bright_black",
    "stone": "bright_black",

    # Extended Tailwind colors -> closest terminal color
    "orange": "yellow",
    "amber": "yellow",
    "lime": "bright_green",
    "emerald": "green",
    "teal": "cyan",
    "sky": "bright_blue",
    "indigo": "blue",
    "violet": "magenta",
    "purple": "magenta",
    "fuchsia": "bright_magenta",
    "pink": "bright_magenta",
    "rose": "bright_red",
}

# Tailwind shade intensity mapping
# Lower shades stay normal, higher shades become bright
SHADE_BRIGHTNESS: Dict[str, bool] = {
    "50": False,
    "100": False,
    "200": False,
    "300": False,
    "400": False,
    "500": False,
    "600": False,
    "700": True,
    "800": True,
    "900": True,
    "950": True,
}

# Static class definitions - maps class name to style attributes
# Format: {"attribute": value} or {"attribute": {"sub_attr": value}}
STATIC_CLASSES: Dict[str, Dict[str, Any]] = {
    # Text formatting
    "font-bold": {"bold": True},
    "text-bold": {"bold": True},
    "bold": {"bold": True},
    "font-normal": {"bold": False},

    "underline": {"underline": True},
    "text-underline": {"underline": True},
    "no-underline": {"underline": False},

    "italic": {"italic": True},
    "text-italic": {"italic": True},
    "not-italic": {"italic": False},

    # Border styles
    "border": {"border": True},
    "border-0": {"border": False},
    "border-2": {"border": True, "border_style": "double"},
    "border-none": {"border": False},

    "rounded": {"border_style": "rounded"},
    "rounded-lg": {"border_style": "rounded"},
    "rounded-xl": {"border_style": "rounded"},
    "rounded-full": {"border_style": "rounded"},
    "rounded-none": {"border_style": "single"},

    # Flexbox alignment (items- prefix)
    "items-start": {"align_items": "start"},
    "items-center": {"align_items": "center"},
    "items-end": {"align_items": "end"},
    "items-stretch": {"align_items": "stretch"},

    # Flexbox justification (justify- prefix)
    "justify-start": {"justify_content": "start"},
    "justify-center": {"justify_content": "center"},
    "justify-end": {"justify_content": "end"},
    "justify-between": {"justify_content": "space-between"},
    "justify-around": {"justify_content": "space-around"},
    "justify-evenly": {"justify_content": "space-around"},

    # Quasar-like classes
    "q-ma-none": {"margin_top": 0, "margin_right": 0, "margin_bottom": 0, "margin_left": 0},
    "q-pa-none": {"padding_top": 0, "padding_right": 0, "padding_bottom": 0, "padding_left": 0},
    "no-wrap": {},  # Handled by element
    "wrap": {},  # Handled by element
}

# Pattern-based class definitions
# Each pattern maps to a handler function name and regex pattern
CLASS_PATTERNS: List[Dict[str, Any]] = [
    # Text colors: text-{color} or text-{color}-{shade}
    {
        "pattern": r"^text-([\w]+)(?:-(\d+))?$",
        "handler": "text_color",
        "exclude": ["bold", "underline", "italic", "left", "center", "right"],
    },
    # Background colors: bg-{color} or bg-{color}-{shade}
    {
        "pattern": r"^bg-([\w]+)(?:-(\d+))?$",
        "handler": "bg_color",
    },
    # Padding: p-{n}, px-{n}, py-{n}, pt-{n}, pr-{n}, pb-{n}, pl-{n}
    {
        "pattern": r"^p([xytrbl])?-(\d+)$",
        "handler": "padding",
    },
    # Margin: m-{n}, mx-{n}, my-{n}, mt-{n}, mr-{n}, mb-{n}, ml-{n}
    {
        "pattern": r"^m([xytrbl])?-(\d+)$",
        "handler": "margin",
    },
    # Gap: gap-{n}, gap-x-{n}, gap-y-{n}
    {
        "pattern": r"^gap(?:-([xy]))?-(\d+)$",
        "handler": "gap",
    },
    # Width: w-{n}
    {
        "pattern": r"^w-(\d+)$",
        "handler": "width",
    },
    # Height: h-{n}
    {
        "pattern": r"^h-(\d+)$",
        "handler": "height",
    },
    # Quasar padding: q-pa-{size}, q-px-{size}, q-py-{size}, etc.
    {
        "pattern": r"^q-p([axytrbl])-(\w+)$",
        "handler": "quasar_padding",
    },
    # Quasar margin: q-ma-{size}, q-mx-{size}, q-my-{size}, etc.
    {
        "pattern": r"^q-m([axytrbl])-(\w+)$",
        "handler": "quasar_margin",
    },
]

# Quasar size scale (xs, sm, md, lg, xl -> character units)
QUASAR_SIZES: Dict[str, int] = {
    "none": 0,
    "xs": 1,
    "sm": 2,
    "md": 3,
    "lg": 4,
    "xl": 5,
}

# CSS property to style attribute mapping
CSS_PROPERTIES: Dict[str, str] = {
    "color": "fg_color",
    "background-color": "bg_color",
    "background": "bg_color",
    "font-weight": "bold",  # Special handling needed
    "text-decoration": "underline",  # Special handling needed
    "font-style": "italic",  # Special handling needed
    "border": "border",  # Special handling needed
}


class StyleMapper:
    """Maps CSS classes and styles to terminal attributes.

    Uses data-driven definitions for maintainability and extensibility.
    """

    def __init__(self) -> None:
        """Initialize the style mapper with compiled patterns."""
        self._compiled_patterns = [
            {
                **p,
                "regex": re.compile(p["pattern"]),
            }
            for p in CLASS_PATTERNS
        ]

    def map_classes(self, classes: List[str]) -> TerminalStyle:
        """Map a list of CSS classes to terminal style.

        Args:
            classes: List of class names

        Returns:
            Computed TerminalStyle
        """
        style = TerminalStyle()

        for cls in classes:
            # Check static class definitions first
            if cls in STATIC_CLASSES:
                for attr, value in STATIC_CLASSES[cls].items():
                    setattr(style, attr, value)
                continue

            # Try pattern-based matching
            matched = False
            for pattern_def in self._compiled_patterns:
                match = pattern_def["regex"].match(cls)
                if match:
                    # Check exclusions
                    if "exclude" in pattern_def:
                        groups = match.groups()
                        if groups and groups[0] in pattern_def["exclude"]:
                            continue

                    handler = getattr(self, f"_handle_{pattern_def['handler']}", None)
                    if handler:
                        handler(style, match)
                        matched = True
                        break

            if matched:
                continue

        return style

    def _handle_text_color(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle text-{color}-{shade} pattern."""
        color_name = match.group(1)
        shade = match.group(2)

        if color_name not in COLOR_MAP:
            return

        terminal_color = COLOR_MAP[color_name]

        # Apply brightness based on shade
        if shade and shade in SHADE_BRIGHTNESS:
            if SHADE_BRIGHTNESS[shade] and not terminal_color.startswith("bright_"):
                terminal_color = f"bright_{terminal_color}"

        style.fg_color = terminal_color

    def _handle_bg_color(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle bg-{color}-{shade} pattern."""
        color_name = match.group(1)
        shade = match.group(2)

        if color_name not in COLOR_MAP:
            return

        terminal_color = COLOR_MAP[color_name]

        if shade and shade in SHADE_BRIGHTNESS:
            if SHADE_BRIGHTNESS[shade] and not terminal_color.startswith("bright_"):
                terminal_color = f"bright_{terminal_color}"

        style.bg_color = terminal_color

    def _handle_padding(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle p-{n}, px-{n}, py-{n}, pt-{n}, etc."""
        direction = match.group(1)  # x, y, t, r, b, l, or None
        value = int(match.group(2))

        if direction is None:
            # p-{n} - all sides
            style.padding_top = value
            style.padding_right = value
            style.padding_bottom = value
            style.padding_left = value
        elif direction == "x":
            style.padding_left = value
            style.padding_right = value
        elif direction == "y":
            style.padding_top = value
            style.padding_bottom = value
        elif direction == "t":
            style.padding_top = value
        elif direction == "r":
            style.padding_right = value
        elif direction == "b":
            style.padding_bottom = value
        elif direction == "l":
            style.padding_left = value

    def _handle_margin(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle m-{n}, mx-{n}, my-{n}, mt-{n}, etc."""
        direction = match.group(1)
        value = int(match.group(2))

        if direction is None:
            style.margin_top = value
            style.margin_right = value
            style.margin_bottom = value
            style.margin_left = value
        elif direction == "x":
            style.margin_left = value
            style.margin_right = value
        elif direction == "y":
            style.margin_top = value
            style.margin_bottom = value
        elif direction == "t":
            style.margin_top = value
        elif direction == "r":
            style.margin_right = value
        elif direction == "b":
            style.margin_bottom = value
        elif direction == "l":
            style.margin_left = value

    def _handle_gap(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle gap-{n} pattern."""
        # direction = match.group(1)  # x, y, or None (not used yet)
        value = int(match.group(2))
        style.gap = value

    def _handle_width(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle w-{n} pattern."""
        style.width = int(match.group(1))

    def _handle_height(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle h-{n} pattern."""
        style.height = int(match.group(1))

    def _handle_quasar_padding(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle q-pa-{size}, q-px-{size}, etc."""
        direction = match.group(1)  # a, x, y, t, r, b, l
        size_name = match.group(2)

        value = QUASAR_SIZES.get(size_name, 0)

        if direction == "a":  # all
            style.padding_top = value
            style.padding_right = value
            style.padding_bottom = value
            style.padding_left = value
        elif direction == "x":
            style.padding_left = value
            style.padding_right = value
        elif direction == "y":
            style.padding_top = value
            style.padding_bottom = value
        elif direction == "t":
            style.padding_top = value
        elif direction == "r":
            style.padding_right = value
        elif direction == "b":
            style.padding_bottom = value
        elif direction == "l":
            style.padding_left = value

    def _handle_quasar_margin(self, style: TerminalStyle, match: re.Match) -> None:
        """Handle q-ma-{size}, q-mx-{size}, etc."""
        direction = match.group(1)
        size_name = match.group(2)

        value = QUASAR_SIZES.get(size_name, 0)

        if direction == "a":
            style.margin_top = value
            style.margin_right = value
            style.margin_bottom = value
            style.margin_left = value
        elif direction == "x":
            style.margin_left = value
            style.margin_right = value
        elif direction == "y":
            style.margin_top = value
            style.margin_bottom = value
        elif direction == "t":
            style.margin_top = value
        elif direction == "r":
            style.margin_right = value
        elif direction == "b":
            style.margin_bottom = value
        elif direction == "l":
            style.margin_left = value

    def map_inline_style(self, style_dict: Dict[str, str]) -> TerminalStyle:
        """Map inline CSS styles to terminal style.

        Args:
            style_dict: Dictionary of CSS properties

        Returns:
            Computed TerminalStyle
        """
        style = TerminalStyle()

        for prop, value in style_dict.items():
            prop = prop.lower().replace("_", "-")

            if prop == "color":
                style.fg_color = self._css_color_to_terminal(value)
            elif prop in ("background-color", "background"):
                style.bg_color = self._css_color_to_terminal(value)
            elif prop == "font-weight":
                style.bold = value in ("bold", "700", "800", "900")
            elif prop == "text-decoration":
                style.underline = "underline" in value
            elif prop == "font-style":
                style.italic = value == "italic"
            elif prop == "padding":
                val = self._parse_css_size(value)
                if val:
                    style.padding_top = style.padding_right = val
                    style.padding_bottom = style.padding_left = val
            elif prop == "margin":
                val = self._parse_css_size(value)
                if val:
                    style.margin_top = style.margin_right = val
                    style.margin_bottom = style.margin_left = val
            elif prop == "width":
                val = self._parse_css_size(value)
                if val:
                    style.width = val
            elif prop == "height":
                val = self._parse_css_size(value)
                if val:
                    style.height = val
            elif prop == "border":
                style.border = value not in ("none", "0", "")
            elif prop == "gap":
                val = self._parse_css_size(value)
                if val:
                    style.gap = val

        return style

    def _css_color_to_terminal(self, color: str) -> Optional[str]:
        """Convert a CSS color to terminal color."""
        color = color.strip().lower()

        if color in COLOR_MAP:
            return COLOR_MAP[color]

        if color.startswith("#"):
            return color

        rgb_match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", color)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return f"#{r:02x}{g:02x}{b:02x}"

        return None

    def _parse_css_size(self, value: str) -> Optional[int]:
        """Parse a CSS size value to character units."""
        value = value.strip().lower()

        # Remove units and convert
        for unit in ("px", "rem", "em", "ch", "vw", "vh", "%"):
            if value.endswith(unit):
                value = value[:-len(unit)]
                break

        try:
            return int(float(value))
        except ValueError:
            return None
