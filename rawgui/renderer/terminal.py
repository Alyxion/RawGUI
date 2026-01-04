"""Terminal renderer using blessed.

Fully functional terminal rendering with mouse support, keyboard input,
focus management, and styling.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple, Any

from blessed import Terminal

from .styles import BORDER_CHARS, StyleMapper, TerminalStyle

if TYPE_CHECKING:
    from ..element import Element


@dataclass
class RenderBox:
    """Calculated render box for an element."""
    element: Optional["Element"] = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    # Content area (inside padding/border)
    content_x: int = 0
    content_y: int = 0
    content_width: int = 0
    content_height: int = 0
    # Style
    style: Optional[TerminalStyle] = None
    border: bool = False
    border_style: str = "single"
    # Children
    children: List["RenderBox"] = field(default_factory=list)


class TerminalRenderer:
    """Renders UI elements to the terminal with full interactivity.

    Features:
    - Fullscreen rendering with blessed
    - Mouse click, hover, and drag support
    - Keyboard navigation (Tab, Shift+Tab, arrows)
    - Focus management for interactive elements
    - Scrolling support
    - Tailwind-like styling
    """

    def __init__(self) -> None:
        """Initialize the renderer."""
        self.term = Terminal()
        self.style_mapper = StyleMapper()

        # Screen state
        self._width = 0
        self._height = 0

        # Element tracking
        self._element_boxes: Dict[int, RenderBox] = {}
        self._focusable: List["Element"] = []
        self._focus_index: int = -1
        self._focused: Optional["Element"] = None
        self._hovered: Optional["Element"] = None

        # Scroll state
        self._scroll_x = 0
        self._scroll_y = 0
        self._content_height = 0
        self._content_width = 0

        # Input state
        self._mouse_down = False
        self._mouse_pos: Tuple[int, int] = (0, 0)

        # Running state
        self._running = False
        self._dirty = True

    @property
    def width(self) -> int:
        return self.term.width

    @property
    def height(self) -> int:
        return self.term.height

    def render(self, root: "Element") -> str:
        """Render element tree and return the output string.

        Args:
            root: Root element to render

        Returns:
            Rendered terminal output as string
        """
        self._width = self.width
        self._height = self.height
        self._element_boxes.clear()
        self._focusable.clear()

        # Calculate layout
        root_box = self._calculate_layout(root, 0, 0, self._width, self._height)
        self._content_height = root_box.height
        self._content_width = root_box.width

        # Build output buffer
        lines = []
        buffer = [[' ' for _ in range(self._width)] for _ in range(self._height)]
        style_buffer = [[None for _ in range(self._width)] for _ in range(self._height)]

        # Render to buffer
        self._render_box(root_box, buffer, style_buffer)

        # Convert buffer to string with styles
        output = self.term.home + self.term.clear
        for y in range(self._height):
            line = ""
            current_style = None
            for x in range(self._width):
                char = buffer[y][x]
                style = style_buffer[y][x]

                if style != current_style:
                    if current_style is not None:
                        line += self.term.normal
                    current_style = style

                if style:
                    line += self._apply_style(char, style)
                else:
                    line += char

            if current_style:
                line += self.term.normal
            lines.append(line)

        output += "\n".join(lines)

        # Update focus if needed
        if self._focusable and self._focus_index < 0:
            self._focus_index = 0
            self._focused = self._focusable[0]

        self._dirty = False
        return output

    def _calculate_layout(
        self,
        element: "Element",
        x: int,
        y: int,
        available_width: int,
        available_height: int,
    ) -> RenderBox:
        """Calculate layout for element and children."""
        if not element.visible:
            return RenderBox(element=element, x=x, y=y, width=0, height=0)

        # Get style
        style = self.style_mapper.map_classes(element._classes)
        inline = self.style_mapper.map_inline_style(element._style)
        merged = self._merge_styles(style, inline)

        box = RenderBox(
            element=element,
            x=x,
            y=y,
            style=merged,
            border=merged.border or element.tag == "card",
            border_style=merged.border_style,
        )

        # Track focusable elements
        if self._is_focusable(element):
            self._focusable.append(element)

        # Calculate size based on element type
        padding = (
            merged.padding_top,
            merged.padding_right,
            merged.padding_bottom,
            merged.padding_left,
        )
        border_size = 1 if box.border else 0

        # Content area
        box.content_x = x + padding[3] + border_size
        box.content_y = y + padding[0] + border_size

        content_width = available_width - padding[1] - padding[3] - (border_size * 2)
        content_height = available_height - padding[0] - padding[2] - (border_size * 2)

        # Calculate based on element type
        if element.tag == "label":
            text = getattr(element, "text", "") or ""
            lines = text.split("\n")
            text_width = max((len(line) for line in lines), default=0)
            text_height = len(lines) if lines else 1
            box.content_width = min(text_width, content_width)
            box.content_height = text_height

        elif element.tag == "button":
            text = getattr(element, "text", "") or ""
            # Button: [ text ]
            box.content_width = len(text) + 4  # "[ " + text + " ]"
            box.content_height = 1

        elif element.tag == "input":
            label = getattr(element, "label", "") or ""
            # Input: label: [________]
            label_width = len(label) + 2 if label else 0
            input_width = max(20, merged.width or 20) if merged.width else 20
            box.content_width = label_width + input_width + 2  # brackets
            box.content_height = 1

        elif element.tag in ("row", "column", "card"):
            # Layout containers
            is_row = element.tag == "row"
            gap = merged.gap

            # Calculate children
            child_x = box.content_x
            child_y = box.content_y
            max_cross = 0  # max height for row, max width for column
            total_main = 0  # total width for row, total height for column

            for child in element.children:
                if not child.visible:
                    continue

                if is_row:
                    child_avail_w = content_width - total_main
                    child_avail_h = content_height
                else:
                    child_avail_w = content_width
                    child_avail_h = content_height - total_main

                child_box = self._calculate_layout(
                    child, child_x, child_y, child_avail_w, child_avail_h
                )
                box.children.append(child_box)

                if is_row:
                    child_x += child_box.width + gap
                    total_main += child_box.width + gap
                    max_cross = max(max_cross, child_box.height)
                else:
                    child_y += child_box.height + gap
                    total_main += child_box.height + gap
                    max_cross = max(max_cross, child_box.width)

            # Remove trailing gap
            if box.children:
                total_main -= gap

            if is_row:
                box.content_width = total_main or content_width
                box.content_height = max_cross or 1
            else:
                box.content_width = max_cross or content_width
                box.content_height = total_main or 1
        else:
            # Generic element
            box.content_width = content_width
            box.content_height = 1

        # Final dimensions
        box.width = box.content_width + padding[1] + padding[3] + (border_size * 2)
        box.height = box.content_height + padding[0] + padding[2] + (border_size * 2)

        # Apply explicit sizes
        if merged.width and merged.width > 0:
            box.width = merged.width
        if merged.height and merged.height > 0:
            box.height = merged.height

        # Store for hit testing
        self._element_boxes[element.id] = box

        return box

    def _render_box(
        self,
        box: RenderBox,
        buffer: List[List[str]],
        style_buffer: List[List[Optional[TerminalStyle]]],
    ) -> None:
        """Render a box to the buffer."""
        if not box.element or not box.element.visible:
            return

        element = box.element
        style = box.style or TerminalStyle()

        # Check if focused or hovered
        is_focused = element == self._focused
        is_hovered = element == self._hovered

        # Modify style for state
        if is_focused and self._is_focusable(element):
            style = TerminalStyle(
                bold=style.bold,
                underline=style.underline,
                reverse=True,  # Highlight focused
                fg_color=style.fg_color,
                bg_color=style.bg_color,
            )
        elif is_hovered and self._is_focusable(element):
            style = TerminalStyle(
                bold=True,
                underline=style.underline,
                fg_color=style.fg_color,
                bg_color=style.bg_color,
            )

        # Apply scroll offset
        render_y = box.y - self._scroll_y
        render_x = box.x - self._scroll_x

        # Draw border if needed
        if box.border:
            self._draw_border(
                buffer, style_buffer,
                render_x, render_y, box.width, box.height,
                box.border_style, style
            )

        # Draw content based on element type
        content_y = box.content_y - self._scroll_y
        content_x = box.content_x - self._scroll_x

        if element.tag == "label":
            text = getattr(element, "text", "") or ""
            self._draw_text(buffer, style_buffer, content_x, content_y, text, style, box.content_width)

        elif element.tag == "button":
            text = getattr(element, "text", "") or ""
            enabled = getattr(element, "enabled", True)
            btn_style = style
            if not enabled:
                btn_style = TerminalStyle(fg_color="bright_black")
            btn_text = f"[ {text} ]"
            self._draw_text(buffer, style_buffer, content_x, content_y, btn_text, btn_style)

        elif element.tag == "input":
            label = getattr(element, "label", "") or ""
            value = getattr(element, "value", "") or ""
            placeholder = getattr(element, "placeholder", "") or ""
            password = getattr(element, "password", False)
            enabled = getattr(element, "enabled", True)

            x = content_x

            # Draw label
            if label:
                label_style = TerminalStyle(bold=True)
                self._draw_text(buffer, style_buffer, x, content_y, f"{label}: ", label_style)
                x += len(label) + 2

            # Draw input field
            display = value if not password else "*" * len(value)
            if not display and placeholder:
                display = placeholder
                input_style = TerminalStyle(fg_color="bright_black", underline=True)
            else:
                input_style = TerminalStyle(underline=True)

            if is_focused:
                input_style.reverse = True
            if not enabled:
                input_style.fg_color = "bright_black"

            # Pad to width
            field_width = 20
            display = display[:field_width].ljust(field_width)
            self._draw_text(buffer, style_buffer, x, content_y, f"[{display}]", input_style)

        # Render children
        for child_box in box.children:
            self._render_box(child_box, buffer, style_buffer)

    def _draw_text(
        self,
        buffer: List[List[str]],
        style_buffer: List[List[Optional[TerminalStyle]]],
        x: int,
        y: int,
        text: str,
        style: TerminalStyle,
        max_width: Optional[int] = None,
    ) -> None:
        """Draw text to buffer."""
        if y < 0 or y >= len(buffer):
            return

        for i, char in enumerate(text):
            col = x + i
            if max_width and i >= max_width:
                break
            if 0 <= col < len(buffer[0]):
                buffer[y][col] = char
                style_buffer[y][col] = style

    def _draw_border(
        self,
        buffer: List[List[str]],
        style_buffer: List[List[Optional[TerminalStyle]]],
        x: int,
        y: int,
        width: int,
        height: int,
        border_style: str,
        style: TerminalStyle,
    ) -> None:
        """Draw border around a box."""
        chars = BORDER_CHARS.get(border_style, BORDER_CHARS["single"])

        x2 = x + width - 1
        y2 = y + height - 1

        # Corners
        if 0 <= y < len(buffer) and 0 <= x < len(buffer[0]):
            buffer[y][x] = chars["tl"]
            style_buffer[y][x] = style
        if 0 <= y < len(buffer) and 0 <= x2 < len(buffer[0]):
            buffer[y][x2] = chars["tr"]
            style_buffer[y][x2] = style
        if 0 <= y2 < len(buffer) and 0 <= x < len(buffer[0]):
            buffer[y2][x] = chars["bl"]
            style_buffer[y2][x] = style
        if 0 <= y2 < len(buffer) and 0 <= x2 < len(buffer[0]):
            buffer[y2][x2] = chars["br"]
            style_buffer[y2][x2] = style

        # Horizontal lines
        for col in range(x + 1, x2):
            if 0 <= col < len(buffer[0]):
                if 0 <= y < len(buffer):
                    buffer[y][col] = chars["h"]
                    style_buffer[y][col] = style
                if 0 <= y2 < len(buffer):
                    buffer[y2][col] = chars["h"]
                    style_buffer[y2][col] = style

        # Vertical lines
        for row in range(y + 1, y2):
            if 0 <= row < len(buffer):
                if 0 <= x < len(buffer[0]):
                    buffer[row][x] = chars["v"]
                    style_buffer[row][x] = style
                if 0 <= x2 < len(buffer[0]):
                    buffer[row][x2] = chars["v"]
                    style_buffer[row][x2] = style

    def _apply_style(self, char: str, style: TerminalStyle) -> str:
        """Apply terminal style to a character."""
        result = char

        if style.reverse:
            result = self.term.reverse(result)
        if style.bold:
            result = self.term.bold(result)
        if style.underline:
            result = self.term.underline(result)

        if style.fg_color:
            color_func = getattr(self.term, style.fg_color, None)
            if color_func and callable(color_func):
                result = color_func(result)

        if style.bg_color:
            color_func = getattr(self.term, f"on_{style.bg_color}", None)
            if color_func and callable(color_func):
                result = color_func(result)

        return result

    def _merge_styles(self, s1: TerminalStyle, s2: TerminalStyle) -> TerminalStyle:
        """Merge two styles (s2 takes precedence)."""
        return TerminalStyle(
            bold=s2.bold or s1.bold,
            underline=s2.underline or s1.underline,
            italic=s2.italic or s1.italic,
            reverse=s2.reverse or s1.reverse,
            fg_color=s2.fg_color or s1.fg_color,
            bg_color=s2.bg_color or s1.bg_color,
            border=s2.border or s1.border,
            border_style=s2.border_style or s1.border_style,
            padding_top=s2.padding_top or s1.padding_top,
            padding_right=s2.padding_right or s1.padding_right,
            padding_bottom=s2.padding_bottom or s1.padding_bottom,
            padding_left=s2.padding_left or s1.padding_left,
            gap=s2.gap or s1.gap,
            width=s2.width or s1.width,
            height=s2.height or s1.height,
        )

    def _is_focusable(self, element: "Element") -> bool:
        """Check if element can receive focus."""
        if element.tag in ("button", "input"):
            return getattr(element, "enabled", True) and element.visible
        return False

    def get_element_at(self, x: int, y: int) -> Optional["Element"]:
        """Get element at screen coordinates."""
        # Adjust for scroll
        abs_x = x + self._scroll_x
        abs_y = y + self._scroll_y

        # Find deepest (smallest) element containing point
        result = None
        result_area = float('inf')

        for element_id, box in self._element_boxes.items():
            if (box.x <= abs_x < box.x + box.width and
                box.y <= abs_y < box.y + box.height):
                area = box.width * box.height
                if area < result_area:
                    result = box.element
                    result_area = area

        return result

    def focus_next(self) -> Optional["Element"]:
        """Focus next focusable element."""
        if not self._focusable:
            return None
        self._focus_index = (self._focus_index + 1) % len(self._focusable)
        self._focused = self._focusable[self._focus_index]
        self._dirty = True
        return self._focused

    def focus_prev(self) -> Optional["Element"]:
        """Focus previous focusable element."""
        if not self._focusable:
            return None
        self._focus_index = (self._focus_index - 1) % len(self._focusable)
        self._focused = self._focusable[self._focus_index]
        self._dirty = True
        return self._focused

    def focus_element(self, element: "Element") -> None:
        """Focus a specific element."""
        if element in self._focusable:
            self._focus_index = self._focusable.index(element)
            self._focused = element
            self._dirty = True

    def set_hover(self, element: Optional["Element"]) -> None:
        """Set hovered element."""
        if self._hovered != element:
            self._hovered = element
            self._dirty = True

    def scroll(self, dx: int = 0, dy: int = 0) -> None:
        """Scroll the view."""
        self._scroll_x = max(0, min(self._scroll_x + dx, max(0, self._content_width - self._width)))
        self._scroll_y = max(0, min(self._scroll_y + dy, max(0, self._content_height - self._height)))
        self._dirty = True

    @property
    def focused(self) -> Optional["Element"]:
        return self._focused

    @property
    def needs_render(self) -> bool:
        return self._dirty

    def invalidate(self) -> None:
        """Mark renderer as needing re-render."""
        self._dirty = True
