"""Minimalistic DOM structure for pixel-first layout.

Implements HTML-like box model with pixel-based coordinates that
convert cleanly to ASCII character positions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Any

from ..constants import (
    CHAR_WIDTH_PX,
    CHAR_HEIGHT_PX,
    px_to_cols,
    px_to_rows,
    HEIGHT_BUTTON,
    HEIGHT_LABEL,
    PADDING_XS,
)

if TYPE_CHECKING:
    from ..element import Element
    from .styles import TerminalStyle


@dataclass
class BoxModel:
    """CSS-like box model with pixel dimensions.

    All values are in pixels and should be multiples of CHAR_WIDTH_PX/CHAR_HEIGHT_PX
    for clean ASCII conversion.
    """

    # Content dimensions
    content_width: int = 0
    content_height: int = 0

    # Padding (inside border)
    padding_top: int = 0
    padding_right: int = 0
    padding_bottom: int = 0
    padding_left: int = 0

    # Border (1 char = CHAR_WIDTH_PX wide, CHAR_HEIGHT_PX tall)
    border_top: int = 0
    border_right: int = 0
    border_bottom: int = 0
    border_left: int = 0

    # Margin (outside border)
    margin_top: int = 0
    margin_right: int = 0
    margin_bottom: int = 0
    margin_left: int = 0

    @property
    def padding_box_width(self) -> int:
        """Width including content + padding."""
        return self.content_width + self.padding_left + self.padding_right

    @property
    def padding_box_height(self) -> int:
        """Height including content + padding."""
        return self.content_height + self.padding_top + self.padding_bottom

    @property
    def border_box_width(self) -> int:
        """Width including content + padding + border."""
        return self.padding_box_width + self.border_left + self.border_right

    @property
    def border_box_height(self) -> int:
        """Height including content + padding + border."""
        return self.padding_box_height + self.border_top + self.border_bottom

    @property
    def outer_width(self) -> int:
        """Total width including margin."""
        return self.border_box_width + self.margin_left + self.margin_right

    @property
    def outer_height(self) -> int:
        """Total height including margin."""
        return self.border_box_height + self.margin_top + self.margin_bottom

    # ASCII conversions
    @property
    def content_cols(self) -> int:
        return px_to_cols(self.content_width)

    @property
    def content_rows(self) -> int:
        return px_to_rows(self.content_height)

    @property
    def border_box_cols(self) -> int:
        return px_to_cols(self.border_box_width)

    @property
    def border_box_rows(self) -> int:
        return px_to_rows(self.border_box_height)


@dataclass
class DOMNode:
    """A node in the DOM tree with pixel-based layout.

    Represents a single element with position, size, and children.
    All coordinates are in pixels for calculation, then converted to
    ASCII for rendering.
    """

    element: Optional["Element"] = None
    tag: str = ""

    # Position in pixel space (relative to parent's content area)
    x: int = 0
    y: int = 0

    # Box model
    box: BoxModel = field(default_factory=BoxModel)

    # Style
    style: Optional["TerminalStyle"] = None

    # Tree structure
    parent: Optional["DOMNode"] = None
    children: List["DOMNode"] = field(default_factory=list)

    # Rendering flags
    has_border: bool = False
    border_style: str = "single"
    visible: bool = True

    # State
    focused: bool = False
    hovered: bool = False
    disabled: bool = False

    # ASCII coordinates (computed from pixel coords)
    @property
    def ascii_x(self) -> int:
        """X position in ASCII columns."""
        return px_to_cols(self.x)

    @property
    def ascii_y(self) -> int:
        """Y position in ASCII rows."""
        return px_to_rows(self.y)

    @property
    def ascii_width(self) -> int:
        """Width in ASCII columns (border box)."""
        return self.box.border_box_cols

    @property
    def ascii_height(self) -> int:
        """Height in ASCII rows (border box)."""
        return self.box.border_box_rows

    # Content area position (inside padding + border)
    @property
    def content_x(self) -> int:
        """Content area X in pixels."""
        return self.x + self.box.border_left + self.box.padding_left

    @property
    def content_y(self) -> int:
        """Content area Y in pixels."""
        return self.y + self.box.border_top + self.box.padding_top

    @property
    def content_ascii_x(self) -> int:
        """Content area X in ASCII columns."""
        return px_to_cols(self.content_x)

    @property
    def content_ascii_y(self) -> int:
        """Content area Y in ASCII rows."""
        return px_to_rows(self.content_y)

    def add_child(self, child: "DOMNode") -> None:
        """Add a child node."""
        child.parent = self
        self.children.append(child)

    def get_absolute_position(self) -> tuple[int, int]:
        """Get absolute pixel position by traversing up the tree."""
        x, y = self.x, self.y
        node = self.parent
        while node:
            x += node.content_x
            y += node.content_y
            node = node.parent
        return x, y

    def get_absolute_ascii_position(self) -> tuple[int, int]:
        """Get absolute ASCII position."""
        px_x, px_y = self.get_absolute_position()
        return px_to_cols(px_x), px_to_rows(px_y)


class DOMBuilder:
    """Builds a DOM tree from Element tree with pixel-based layout."""

    def __init__(self) -> None:
        from .styles import StyleMapper
        self.style_mapper = StyleMapper()

    def build(
        self,
        element: "Element",
        available_width: int,
        available_height: int,
    ) -> DOMNode:
        """Build DOM tree from element tree.

        Args:
            element: Root element
            available_width: Available width in pixels
            available_height: Available height in pixels

        Returns:
            Root DOMNode with complete layout
        """
        return self._build_node(element, available_width, available_height)

    def _build_node(
        self,
        element: "Element",
        available_width: int,
        available_height: int,
    ) -> DOMNode:
        """Recursively build a DOM node."""
        if not element.visible:
            return DOMNode(element=element, visible=False)

        # Get computed style
        style = self.style_mapper.map_classes(element._classes)
        inline = self.style_mapper.map_inline_style(element._style)
        style = self._merge_styles(style, inline)

        # Create node
        node = DOMNode(
            element=element,
            tag=element.tag,
            style=style,
            visible=True,
            disabled=not getattr(element, "enabled", True),
        )

        # Build box model from style
        box = self._compute_box_model(element, style, available_width, available_height)
        node.box = box

        # Handle borders
        # Cards get borders by default, buttons only if explicitly styled
        if style.border or element.tag == "card":
            node.has_border = True
            node.border_style = style.border_style or "rounded"
            # Border adds 1 char on each side
            node.box.border_top = CHAR_HEIGHT_PX
            node.box.border_bottom = CHAR_HEIGHT_PX
            node.box.border_left = CHAR_WIDTH_PX
            node.box.border_right = CHAR_WIDTH_PX

        # Build children for container elements
        container_tags = (
            "row", "column", "card", "header", "footer", "drawer",
            "tabs", "tab_panels", "tab_panel", "dialog", "menu",
            "scroll_area", "expansion", "grid", "splitter",
        )
        if element.tag in container_tags:
            self._layout_children(node, element, style)

        return node

    def _compute_box_model(
        self,
        element: "Element",
        style: "TerminalStyle",
        available_width: int,
        available_height: int,
    ) -> BoxModel:
        """Compute box model dimensions from element and style."""
        box = BoxModel()

        # Padding (convert from char units to pixels)
        box.padding_top = style.padding_top * CHAR_HEIGHT_PX
        box.padding_bottom = style.padding_bottom * CHAR_HEIGHT_PX
        box.padding_left = style.padding_left * CHAR_WIDTH_PX
        box.padding_right = style.padding_right * CHAR_WIDTH_PX

        # Margin
        box.margin_top = style.margin_top * CHAR_HEIGHT_PX
        box.margin_bottom = style.margin_bottom * CHAR_HEIGHT_PX
        box.margin_left = style.margin_left * CHAR_WIDTH_PX
        box.margin_right = style.margin_right * CHAR_WIDTH_PX

        # Default padding for cards
        if element.tag == "card" and "tight" not in element._classes:
            if box.padding_top == 0:
                box.padding_top = CHAR_HEIGHT_PX
                box.padding_bottom = CHAR_HEIGHT_PX
            if box.padding_left == 0:
                box.padding_left = CHAR_WIDTH_PX
                box.padding_right = CHAR_WIDTH_PX

        # Content size based on element type
        if element.tag == "label":
            text = getattr(element, "text", "") or ""
            lines = text.split("\n")
            text_width = max((len(line) for line in lines), default=0)
            text_height = len(lines) if lines else 1
            box.content_width = text_width * CHAR_WIDTH_PX
            box.content_height = text_height * CHAR_HEIGHT_PX

        elif element.tag == "button":
            text = getattr(element, "text", "") or ""
            # Button: 1 row content + 1 row spacing (0.5 top + 0.5 bottom effect)
            box.content_width = (len(text) + 4) * CHAR_WIDTH_PX  # "[ text ]"
            box.content_height = 2 * CHAR_HEIGHT_PX  # 2 rows total

        elif element.tag == "input":
            label = getattr(element, "label", "") or ""
            field_width = 23  # Default input width including brackets + indent
            # Label goes above input (Material Design style)
            # Add 1 row spacing above for visual separation
            label_row = 1 if label else 0
            spacing_row = 1  # Top margin for visual separation
            box.content_width = max(len(label), field_width) * CHAR_WIDTH_PX
            box.content_height = (1 + label_row + spacing_row) * CHAR_HEIGHT_PX

        elif element.tag == "checkbox":
            text = getattr(element, "text", "") or ""
            # Checkbox: [x] text or [ ] text + spacing
            box.content_width = (len(text) + 4) * CHAR_WIDTH_PX  # "[x] " + text
            box.content_height = 2 * CHAR_HEIGHT_PX  # 2 rows (content + spacing)

        elif element.tag == "toggle":
            text = getattr(element, "text", "") or ""
            # Toggle: (*) text + spacing
            box.content_width = (len(text) + 6) * CHAR_WIDTH_PX
            box.content_height = 2 * CHAR_HEIGHT_PX  # content + spacing

        elif element.tag == "radio":
            options = getattr(element, "_options", [])
            # Radio: one row per option
            max_label = max((len(opt.get("label", "")) for opt in options), default=0)
            box.content_width = (max_label + 5) * CHAR_WIDTH_PX  # "(*) " + label
            box.content_height = len(options) * CHAR_HEIGHT_PX

        elif element.tag == "select":
            label = getattr(element, "label", "") or ""
            # Select: label + dropdown box
            label_width = len(label) + 2 if label else 0
            box.content_width = (label_width + 20) * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "progress":
            # Progress bar: [=====>    ] 100%
            box.content_width = 30 * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "spinner":
            # Spinner: [|]
            box.content_width = 6 * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "slider":
            # Slider: [---O-------] 0.50
            box.content_width = 30 * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "separator":
            vertical = getattr(element, "vertical", False)
            if vertical:
                box.content_width = CHAR_WIDTH_PX
                box.content_height = 3 * CHAR_HEIGHT_PX
            else:
                box.content_width = 40 * CHAR_WIDTH_PX
                box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "link":
            text = getattr(element, "text", "") or ""
            box.content_width = len(text) * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "badge":
            text = getattr(element, "text", "") or ""
            box.content_width = (len(text) + 2) * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "icon":
            # Icon: [X]
            box.content_width = 3 * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "textarea":
            label = getattr(element, "label", "") or ""
            label_height = 1 if label else 0
            box.content_width = 32 * CHAR_WIDTH_PX
            box.content_height = (5 + label_height) * CHAR_HEIGHT_PX

        elif element.tag == "number":
            label = getattr(element, "label", "") or ""
            label_width = len(label) + 2 if label else 0
            box.content_width = (label_width + 14) * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "tabs":
            # Tabs header: calculate width of all tabs
            total_width = 0
            for child in element.children:
                if child.tag == "tab":
                    tab_label = getattr(child, "label", getattr(child, "name", ""))
                    total_width += len(tab_label) + 3
            box.content_width = max(total_width, 20) * CHAR_WIDTH_PX
            box.content_height = CHAR_HEIGHT_PX

        elif element.tag == "table":
            columns = getattr(element, "_columns", [])
            rows = getattr(element, "_rows", [])
            title = getattr(element, "title", None)
            # Calculate width from columns
            total_width = sum(col.get("width", 12) + 1 for col in columns)
            # Height: header + rows + optional title
            total_height = min(len(rows), 10) + 1 + (1 if title else 0)
            box.content_width = total_width * CHAR_WIDTH_PX
            box.content_height = total_height * CHAR_HEIGHT_PX

        elif element.tag == "tree":
            nodes = getattr(element, "_nodes", [])
            # Estimate tree size
            box.content_width = 40 * CHAR_WIDTH_PX
            box.content_height = min(len(nodes) * 3, 15) * CHAR_HEIGHT_PX

        elif element.tag == "dialog":
            # Dialog sizes to its children content
            pass

        elif element.tag in ("row", "column", "card"):
            # Containers size to content (calculated in _layout_children)
            pass

        return box

    def _layout_children(
        self,
        node: DOMNode,
        element: "Element",
        style: "TerminalStyle",
    ) -> None:
        """Layout children within a container node."""
        is_row = element.tag == "row"
        gap = style.gap * CHAR_WIDTH_PX if is_row else style.gap * CHAR_HEIGHT_PX

        # Available space for children (inside padding + border)
        content_width = node.box.content_width or 1000 * CHAR_WIDTH_PX  # Default large
        content_height = node.box.content_height or 1000 * CHAR_HEIGHT_PX

        # Position children
        current_x = 0
        current_y = 0
        max_cross = 0  # max height for row, max width for column
        total_main = 0  # total width for row, total height for column

        for child in element.children:
            if not child.visible:
                continue

            # Build child node
            if is_row:
                child_avail_w = content_width - total_main
                child_avail_h = content_height
            else:
                child_avail_w = content_width
                child_avail_h = content_height - total_main

            child_node = self._build_node(child, child_avail_w, child_avail_h)
            child_node.x = current_x
            child_node.y = current_y
            node.add_child(child_node)

            # Advance position
            child_outer_w = child_node.box.outer_width
            child_outer_h = child_node.box.outer_height

            if is_row:
                current_x += child_outer_w + gap
                total_main += child_outer_w + gap
                max_cross = max(max_cross, child_outer_h)
            else:
                current_y += child_outer_h + gap
                total_main += child_outer_h + gap
                max_cross = max(max_cross, child_outer_w)

        # Remove trailing gap
        if node.children:
            total_main -= gap

        # Set container content size based on children
        if is_row:
            node.box.content_width = max(total_main, CHAR_WIDTH_PX)
            node.box.content_height = max(max_cross, CHAR_HEIGHT_PX)
        else:
            node.box.content_width = max(max_cross, CHAR_WIDTH_PX)
            node.box.content_height = max(total_main, CHAR_HEIGHT_PX)

    def _merge_styles(self, s1: "TerminalStyle", s2: "TerminalStyle") -> "TerminalStyle":
        """Merge two styles (s2 takes precedence)."""
        from .styles import TerminalStyle
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
