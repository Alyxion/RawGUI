"""Layout engine for terminal rendering.

Implements flexbox-like layout for rows and columns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from ..element import Element


class Direction(Enum):
    """Layout direction."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Alignment(Enum):
    """Cross-axis alignment."""
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


class Justification(Enum):
    """Main-axis justification."""
    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"


@dataclass
class LayoutBox:
    """A calculated layout box for an element."""

    element: Optional["Element"] = None

    # Position (absolute, in terminal coordinates)
    x: int = 0
    y: int = 0

    # Size
    width: int = 0
    height: int = 0

    # Content area (inside padding/border)
    content_x: int = 0
    content_y: int = 0
    content_width: int = 0
    content_height: int = 0

    # Computed style properties
    padding: Tuple[int, int, int, int] = (0, 0, 0, 0)  # top, right, bottom, left
    margin: Tuple[int, int, int, int] = (0, 0, 0, 0)
    border: bool = False

    # Children layout boxes
    children: List["LayoutBox"] = field(default_factory=list)

    # Intrinsic size (content-based)
    intrinsic_width: int = 0
    intrinsic_height: int = 0

    def compute_content_area(self) -> None:
        """Compute the content area based on padding and border."""
        border_offset = 1 if self.border else 0

        self.content_x = self.x + self.margin[3] + border_offset + self.padding[3]
        self.content_y = self.y + self.margin[0] + border_offset + self.padding[0]

        self.content_width = (
            self.width
            - self.margin[1] - self.margin[3]
            - (border_offset * 2)
            - self.padding[1] - self.padding[3]
        )
        self.content_height = (
            self.height
            - self.margin[0] - self.margin[2]
            - (border_offset * 2)
            - self.padding[0] - self.padding[2]
        )

        # Clamp to minimum
        self.content_width = max(0, self.content_width)
        self.content_height = max(0, self.content_height)


class LayoutEngine:
    """Calculates layout for the element tree."""

    def __init__(self, screen_width: int, screen_height: int) -> None:
        """Initialize the layout engine.

        Args:
            screen_width: Available terminal width
            screen_height: Available terminal height
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

    def calculate(self, root: "Element") -> LayoutBox:
        """Calculate layout for the element tree.

        Args:
            root: The root element

        Returns:
            Root LayoutBox with all children calculated
        """
        root_box = LayoutBox(
            element=root,
            x=0,
            y=0,
            width=self.screen_width,
            height=self.screen_height,
        )

        # First pass: calculate intrinsic sizes (bottom-up)
        self._calculate_intrinsic_sizes(root, root_box)

        # Second pass: calculate positions (top-down)
        root_box.compute_content_area()
        self._layout_children(root, root_box)

        return root_box

    def _calculate_intrinsic_sizes(
        self, element: "Element", box: LayoutBox
    ) -> None:
        """Calculate intrinsic sizes bottom-up.

        Args:
            element: The element
            box: The layout box
        """
        from .styles import StyleMapper

        mapper = StyleMapper()

        # Get element's style
        style = mapper.map_classes(element._classes)
        inline_style = mapper.map_inline_style(element._style)

        # Merge styles (inline takes precedence)
        box.border = style.border or inline_style.border
        box.padding = (
            style.padding_top or inline_style.padding_top,
            style.padding_right or inline_style.padding_right,
            style.padding_bottom or inline_style.padding_bottom,
            style.padding_left or inline_style.padding_left,
        )
        box.margin = (
            style.margin_top or inline_style.margin_top,
            style.margin_right or inline_style.margin_right,
            style.margin_bottom or inline_style.margin_bottom,
            style.margin_left or inline_style.margin_left,
        )

        # Calculate children first
        for child in element.children:
            if not child.visible:
                continue

            child_box = LayoutBox(element=child)
            self._calculate_intrinsic_sizes(child, child_box)
            box.children.append(child_box)

        # Calculate this element's intrinsic size
        box.intrinsic_width, box.intrinsic_height = self._get_intrinsic_size(
            element, box, style, inline_style
        )

        # Apply explicit size if set
        if style.width is not None and style.width > 0:
            box.intrinsic_width = style.width
        if inline_style.width is not None and inline_style.width > 0:
            box.intrinsic_width = inline_style.width

        if style.height is not None and style.height > 0:
            box.intrinsic_height = style.height
        if inline_style.height is not None and inline_style.height > 0:
            box.intrinsic_height = inline_style.height

    def _get_intrinsic_size(
        self,
        element: "Element",
        box: LayoutBox,
        style,
        inline_style,
    ) -> Tuple[int, int]:
        """Get the intrinsic content size of an element.

        Args:
            element: The element
            box: The layout box
            style: Computed class style
            inline_style: Inline style

        Returns:
            Tuple of (width, height)
        """
        # Base size from content
        width = 0
        height = 0

        # Text-based elements
        if hasattr(element, "text") and element.text:
            lines = str(element.text).split("\n")
            width = max(len(line) for line in lines)
            height = len(lines)

        # Input elements
        if hasattr(element, "label") and element.label:
            label_width = len(element.label) + 2  # Label + ": "
            if hasattr(element, "placeholder"):
                input_width = max(len(element.placeholder or ""), 20)
            else:
                input_width = 20
            width = label_width + input_width
            height = 1

        # Layout containers - size based on children
        if element.tag in ("row", "column", "card"):
            direction = Direction.HORIZONTAL if element.tag == "row" else Direction.VERTICAL
            gap = style.gap or inline_style.gap or 0

            if direction == Direction.HORIZONTAL:
                # Row: sum widths, max height
                for child_box in box.children:
                    width += child_box.intrinsic_width
                    height = max(height, child_box.intrinsic_height)
                width += gap * max(0, len(box.children) - 1)
            else:
                # Column: max width, sum heights
                for child_box in box.children:
                    width = max(width, child_box.intrinsic_width)
                    height += child_box.intrinsic_height
                height += gap * max(0, len(box.children) - 1)

        # Add padding and border
        border_size = 2 if box.border else 0
        width += box.padding[1] + box.padding[3] + border_size
        height += box.padding[0] + box.padding[2] + border_size

        # Add margin
        width += box.margin[1] + box.margin[3]
        height += box.margin[0] + box.margin[2]

        return width, height

    def _layout_children(self, element: "Element", box: LayoutBox) -> None:
        """Layout children within a box.

        Args:
            element: The parent element
            box: The parent's layout box
        """
        if not box.children:
            return

        from .styles import StyleMapper

        mapper = StyleMapper()
        style = mapper.map_classes(element._classes)
        inline_style = mapper.map_inline_style(element._style)

        # Determine direction
        direction = Direction.HORIZONTAL if element.tag == "row" else Direction.VERTICAL
        gap = style.gap or inline_style.gap or 0

        # Get alignment
        align_str = style.align_items or inline_style.align_items or "start"
        justify_str = style.justify_content or inline_style.justify_content or "start"

        align = Alignment(align_str)
        justify = Justification(justify_str)

        # Calculate positions
        if direction == Direction.HORIZONTAL:
            self._layout_horizontal(box, gap, align, justify)
        else:
            self._layout_vertical(box, gap, align, justify)

        # Recursively layout grandchildren
        for child_box in box.children:
            if child_box.element:
                child_box.compute_content_area()
                self._layout_children(child_box.element, child_box)

    def _layout_horizontal(
        self,
        box: LayoutBox,
        gap: int,
        align: Alignment,
        justify: Justification,
    ) -> None:
        """Layout children horizontally.

        Args:
            box: Parent box
            gap: Gap between children
            align: Cross-axis alignment
            justify: Main-axis justification
        """
        # Calculate total children width
        total_width = sum(c.intrinsic_width for c in box.children)
        total_width += gap * max(0, len(box.children) - 1)

        available_width = box.content_width
        remaining = available_width - total_width

        # Calculate starting x based on justification
        if justify == Justification.CENTER:
            x = box.content_x + remaining // 2
        elif justify == Justification.END:
            x = box.content_x + remaining
        elif justify == Justification.SPACE_BETWEEN:
            x = box.content_x
            if len(box.children) > 1:
                gap = remaining // (len(box.children) - 1)
        elif justify == Justification.SPACE_AROUND:
            if len(box.children) > 0:
                space = remaining // (len(box.children) * 2)
                x = box.content_x + space
                gap = space * 2
        else:  # START
            x = box.content_x

        # Position each child
        for child_box in box.children:
            child_box.x = x
            child_box.width = child_box.intrinsic_width

            # Cross-axis alignment
            if align == Alignment.CENTER:
                child_box.y = box.content_y + (box.content_height - child_box.intrinsic_height) // 2
            elif align == Alignment.END:
                child_box.y = box.content_y + box.content_height - child_box.intrinsic_height
            elif align == Alignment.STRETCH:
                child_box.y = box.content_y
                child_box.height = box.content_height
            else:  # START
                child_box.y = box.content_y

            if child_box.height == 0:
                child_box.height = child_box.intrinsic_height

            x += child_box.width + gap

    def _layout_vertical(
        self,
        box: LayoutBox,
        gap: int,
        align: Alignment,
        justify: Justification,
    ) -> None:
        """Layout children vertically.

        Args:
            box: Parent box
            gap: Gap between children
            align: Cross-axis alignment
            justify: Main-axis justification
        """
        # Calculate total children height
        total_height = sum(c.intrinsic_height for c in box.children)
        total_height += gap * max(0, len(box.children) - 1)

        available_height = box.content_height
        remaining = available_height - total_height

        # Calculate starting y based on justification
        if justify == Justification.CENTER:
            y = box.content_y + remaining // 2
        elif justify == Justification.END:
            y = box.content_y + remaining
        elif justify == Justification.SPACE_BETWEEN:
            y = box.content_y
            if len(box.children) > 1:
                gap = remaining // (len(box.children) - 1)
        elif justify == Justification.SPACE_AROUND:
            if len(box.children) > 0:
                space = remaining // (len(box.children) * 2)
                y = box.content_y + space
                gap = space * 2
        else:  # START
            y = box.content_y

        # Position each child
        for child_box in box.children:
            child_box.y = y
            child_box.height = child_box.intrinsic_height

            # Cross-axis alignment
            if align == Alignment.CENTER:
                child_box.x = box.content_x + (box.content_width - child_box.intrinsic_width) // 2
            elif align == Alignment.END:
                child_box.x = box.content_x + box.content_width - child_box.intrinsic_width
            elif align == Alignment.STRETCH:
                child_box.x = box.content_x
                child_box.width = box.content_width
            else:  # START
                child_box.x = box.content_x

            if child_box.width == 0:
                child_box.width = child_box.intrinsic_width

            y += child_box.height + gap
