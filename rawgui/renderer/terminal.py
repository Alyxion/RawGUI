"""Terminal renderer using blessed with pixel-first layout.

Uses a DOM-like structure with pixel-based coordinates that convert
cleanly to ASCII character positions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from blessed import Terminal

from ..constants import (
    CHAR_WIDTH_PX,
    CHAR_HEIGHT_PX,
    px_to_cols,
    px_to_rows,
    cols_to_px,
    rows_to_px,
)
from .styles import BORDER_CHARS, StyleMapper, TerminalStyle
from .dom import DOMNode, DOMBuilder, BoxModel
from .layers import Cell, Layer, LayerCompositor

if TYPE_CHECKING:
    from ..element import Element


class TerminalRenderer:
    """Renders UI elements to the terminal with pixel-first layout.

    Features:
    - Pixel-based layout calculations
    - Clean ASCII conversion (no fractional positions)
    - Mouse click, hover, and drag support
    - Keyboard navigation (Tab, Shift+Tab, arrows)
    - Focus management for interactive elements
    - Scrolling support
    - Layered rendering with shadows for dialogs/overlays
    """

    # Tags that render as overlays with shadows
    OVERLAY_TAGS = ("dialog", "menu", "context_menu", "notification")

    def __init__(self) -> None:
        """Initialize the renderer."""
        self.term = Terminal()
        self.style_mapper = StyleMapper()
        self.dom_builder = DOMBuilder()

        # Screen state (in pixels)
        self._screen_width_px = 0
        self._screen_height_px = 0

        # DOM tree
        self._root_node: Optional[DOMNode] = None

        # Element tracking
        self._node_map: Dict[int, DOMNode] = {}  # element.id -> DOMNode
        self._focusable: List["Element"] = []
        self._focus_index: int = -1
        self._focused: Optional["Element"] = None
        self._hovered: Optional["Element"] = None

        # Edit mode - when True, element has full keyboard focus (e.g., typing in input)
        self._edit_mode: bool = False

        # Pending focus restore - applied after next render
        self._pending_focus_index: Optional[int] = None

        # Scroll state (in pixels)
        self._scroll_x = 0
        self._scroll_y = 0
        self._content_height = 0
        self._content_width = 0

        # Layer compositor for overlay rendering
        self._compositor: Optional[LayerCompositor] = None

        # Running state
        self._dirty = True

    @property
    def width(self) -> int:
        """Screen width in ASCII columns."""
        return self.term.width

    @property
    def height(self) -> int:
        """Screen height in ASCII rows."""
        return self.term.height

    @property
    def width_px(self) -> int:
        """Screen width in pixels."""
        return self.width * CHAR_WIDTH_PX

    @property
    def height_px(self) -> int:
        """Screen height in pixels."""
        return self.height * CHAR_HEIGHT_PX

    def render(self, root: "Element") -> str:
        """Render element tree and return the output string.

        Args:
            root: Root element to render

        Returns:
            Rendered terminal output as string
        """
        self._screen_width_px = self.width_px
        self._screen_height_px = self.height_px
        self._node_map.clear()
        self._focusable.clear()

        # Build DOM tree with pixel-based layout
        self._root_node = self.dom_builder.build(
            root,
            self._screen_width_px,
            self._screen_height_px,
        )

        # Index nodes and find focusable elements
        self._index_nodes(self._root_node)

        # Restore pending focus BEFORE rendering (so node.focused is correct)
        if self._pending_focus_index is not None and self._focusable:
            idx = max(0, min(self._pending_focus_index, len(self._focusable) - 1))
            self._focus_index = idx
            self._focused = self._focusable[idx]
            self._pending_focus_index = None
            # Mark the node as focused
            if self._focused and self._focused.id in self._node_map:
                self._node_map[self._focused.id].focused = True

        # Track content size
        self._content_width = self._root_node.box.border_box_width
        self._content_height = self._root_node.box.border_box_height

        # Find overlay elements (dialogs, menus, etc.)
        overlays = self._find_overlays(root)
        visible_overlays = [o for o in overlays if o.visible and getattr(o, '_is_open', True)]

        # Initialize or resize compositor
        if self._compositor is None or self._compositor.width != self.width or self._compositor.height != self.height:
            self._compositor = LayerCompositor(self.width, self.height)

        # Clear compositor layers (except base)
        for name in list(self._compositor._layers.keys()):
            if name != "base":
                self._compositor.remove_layer(name)
        self._compositor.invalidate()

        # Build base buffer
        base_buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        base_style_buffer = [[None for _ in range(self.width)] for _ in range(self.height)]

        # Render DOM to base buffer (excluding overlays)
        self._render_node(self._root_node, 0, 0, base_buffer, base_style_buffer, skip_overlays=True)

        # Copy base buffer to compositor base layer
        base_layer = self._compositor.get_layer("base")
        for y in range(self.height):
            for x in range(self.width):
                base_layer.set_cell(x, y, base_buffer[y][x], base_style_buffer[y][x])

        # Render each visible overlay to its own layer with shadow
        for i, overlay in enumerate(visible_overlays):
            overlay_node = self._node_map.get(overlay.id)
            if not overlay_node:
                continue

            # Calculate overlay position (centered if not specified)
            overlay_x = getattr(overlay, '_center_x', None)
            overlay_y = getattr(overlay, '_center_y', None)

            if overlay_x is None:
                overlay_x = (self.width - overlay_node.ascii_width) // 2
            if overlay_y is None:
                overlay_y = (self.height - overlay_node.ascii_height) // 2

            overlay_x = max(0, overlay_x)
            overlay_y = max(0, overlay_y)

            # Create layer for this overlay
            layer = self._compositor.add_layer(
                f"overlay_{overlay.id}",
                z_index=100 + i,
                has_shadow=True,
                x=overlay_x,
                y=overlay_y,
                width=overlay_node.ascii_width + 3,  # Extra for shadow
                height=overlay_node.ascii_height + 2,
            )

            # Render overlay content to a temp buffer
            overlay_buffer = [['\x00' for _ in range(layer.width)] for _ in range(layer.height)]
            overlay_style_buffer = [[None for _ in range(layer.width)] for _ in range(layer.height)]

            # Render the overlay node
            self._render_overlay_node(overlay_node, 0, 0, overlay_buffer, overlay_style_buffer)

            # Copy to layer
            for y in range(min(layer.height, len(overlay_buffer))):
                for x in range(min(layer.width, len(overlay_buffer[0]))):
                    char = overlay_buffer[y][x]
                    style = overlay_style_buffer[y][x]
                    if char != '\x00':
                        layer.set_cell(x, y, char, style)

        # Composite all layers
        composite = self._compositor.composite()

        # Convert composite to string with styles
        output = self.term.home + self.term.clear
        lines = []

        for y in range(self.height):
            line = ""
            current_style = None
            for x in range(self.width):
                cell = composite[y][x]
                char = cell.char if cell.char else " "
                style = cell.style

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

        # Update focus if needed (initial focus)
        if self._focusable and self._focus_index < 0:
            self._focus_index = 0
            self._focused = self._focusable[0]

        self._dirty = False
        return output

    def _find_overlays(self, element: "Element") -> List["Element"]:
        """Find all overlay elements (dialogs, menus, etc.) in the tree."""
        overlays = []

        if element.tag in self.OVERLAY_TAGS:
            overlays.append(element)

        for child in element.children:
            overlays.extend(self._find_overlays(child))

        return overlays

    def _render_overlay_node(
        self,
        node: DOMNode,
        offset_x: int,
        offset_y: int,
        buffer: List[List[str]],
        style_buffer: List[List[Optional[TerminalStyle]]],
    ) -> None:
        """Render an overlay node (dialog, menu) to a buffer."""
        if not node.visible:
            return

        # Get style
        style = node.style or TerminalStyle()
        if node.focused and self._is_focusable(node.element):
            style = TerminalStyle(
                bold=style.bold,
                underline=style.underline,
                reverse=True,
                fg_color=style.fg_color,
                bg_color=style.bg_color,
            )

        # Calculate positions
        render_x = offset_x
        render_y = offset_y

        # Draw border if needed
        if node.has_border:
            width_cols = node.ascii_width
            height_rows = node.ascii_height
            self._draw_border(
                buffer, style_buffer,
                render_x, render_y,
                width_cols, height_rows,
                node.border_style, style
            )

        # Fill background for dialog
        if node.element and node.element.tag == "dialog":
            bg_style = TerminalStyle(bg_color="blue", fg_color="white")
            for row in range(render_y + 1, render_y + node.ascii_height - 1):
                for col in range(render_x + 1, render_x + node.ascii_width - 1):
                    if 0 <= row < len(buffer) and 0 <= col < len(buffer[0]):
                        buffer[row][col] = " "
                        style_buffer[row][col] = bg_style

        # Draw content
        content_x = render_x + px_to_cols(node.box.border_left + node.box.padding_left)
        content_y = render_y + px_to_rows(node.box.border_top + node.box.padding_top)

        if node.element:
            self._render_element_content(node, content_x, content_y, buffer, style_buffer, style)

        # Render children
        child_offset_x = render_x + px_to_cols(node.box.border_left + node.box.padding_left)
        child_offset_y = render_y + px_to_rows(node.box.border_top + node.box.padding_top)

        for child in node.children:
            child_x = child_offset_x + child.ascii_x
            child_y = child_offset_y + child.ascii_y
            self._render_overlay_node(child, child_x, child_y, buffer, style_buffer)

    def _index_nodes(self, node: DOMNode) -> None:
        """Index DOM nodes and find focusable elements."""
        if node.element:
            self._node_map[node.element.id] = node

            # Track focusable elements
            if self._is_focusable(node.element):
                self._focusable.append(node.element)

                # Update focus state
                if node.element == self._focused:
                    node.focused = True

            # Update hover state
            if node.element == self._hovered:
                node.hovered = True

        for child in node.children:
            self._index_nodes(child)

    def _render_node(
        self,
        node: DOMNode,
        parent_x: int,
        parent_y: int,
        buffer: List[List[str]],
        style_buffer: List[List[Optional[TerminalStyle]]],
        skip_overlays: bool = False,
    ) -> None:
        """Render a DOM node to the buffer.

        Args:
            node: Node to render
            parent_x: Parent's content area X in pixels
            parent_y: Parent's content area Y in pixels
            buffer: Character buffer
            style_buffer: Style buffer
            skip_overlays: Skip overlay elements (they're rendered separately)
        """
        if not node.visible:
            return

        # Skip overlays if requested (they're rendered on separate layers)
        if skip_overlays and node.element and node.element.tag in self.OVERLAY_TAGS:
            return

        # Calculate absolute position in pixels
        abs_x = parent_x + node.x
        abs_y = parent_y + node.y

        # Apply scroll offset
        render_x_px = abs_x - self._scroll_x
        render_y_px = abs_y - self._scroll_y

        # Convert to ASCII coordinates
        render_x = px_to_cols(render_x_px)
        render_y = px_to_rows(render_y_px)

        # Get style (with focus/hover modifications)
        style = node.style or TerminalStyle()
        if node.focused and self._is_focusable(node.element):
            style = TerminalStyle(
                bold=style.bold,
                underline=style.underline,
                reverse=True,
                fg_color=style.fg_color,
                bg_color=style.bg_color,
            )
        elif node.hovered and self._is_focusable(node.element):
            style = TerminalStyle(
                bold=True,
                underline=style.underline,
                fg_color=style.fg_color,
                bg_color=style.bg_color,
            )

        # Draw border if needed
        if node.has_border:
            width_cols = node.ascii_width
            height_rows = node.ascii_height
            self._draw_border(
                buffer, style_buffer,
                render_x, render_y,
                width_cols, height_rows,
                node.border_style, style
            )

        # Draw content based on element type
        content_x = px_to_cols(render_x_px + node.box.border_left + node.box.padding_left)
        content_y = px_to_rows(render_y_px + node.box.border_top + node.box.padding_top)

        if node.element:
            self._render_element_content(node, content_x, content_y, buffer, style_buffer, style)

        # Render children
        child_parent_x = abs_x + node.box.border_left + node.box.padding_left
        child_parent_y = abs_y + node.box.border_top + node.box.padding_top

        for child in node.children:
            self._render_node(child, child_parent_x, child_parent_y, buffer, style_buffer, skip_overlays)

    def _render_element_content(
        self,
        node: DOMNode,
        content_x: int,
        content_y: int,
        buffer: List[List[str]],
        style_buffer: List[List[Optional[TerminalStyle]]],
        style: TerminalStyle,
    ) -> None:
        """Render element-specific content."""
        element = node.element
        if not element:
            return

        if element.tag == "label":
            text = getattr(element, "text", "") or ""
            lines = text.split("\n")
            for i, line in enumerate(lines):
                self._draw_text(buffer, style_buffer, content_x, content_y + i, line, style)

        elif element.tag == "button":
            text = getattr(element, "text", "") or ""
            enabled = getattr(element, "enabled", True)

            # Style based on state:
            # - Disabled: dim
            # - Highlighted (nav focus): cyan bg (buttons don't have edit mode)
            # - Normal: default
            if not enabled:
                btn_style = TerminalStyle(fg_color="bright_black")
            elif node.focused:
                btn_style = TerminalStyle(fg_color="black", bg_color="cyan", bold=True)
            else:
                btn_style = style

            # Button: draw after spacing row (0.5 top + 0.5 bottom effect)
            btn_y = content_y + 1
            btn_text = f"[ {text} ]"
            self._draw_text(buffer, style_buffer, content_x, btn_y, btn_text, btn_style)

        elif element.tag == "input":
            label = getattr(element, "label", "") or ""
            value = getattr(element, "value", "") or ""
            placeholder = getattr(element, "placeholder", "") or ""
            password = getattr(element, "password", False)
            enabled = getattr(element, "enabled", True)
            cursor_pos = getattr(element, "_cursor_pos", len(value))

            # Start after spacing row
            y = content_y + 1

            # Draw label above input (Material Design style)
            if label:
                label_style = TerminalStyle(fg_color="bright_black")
                if node.focused:
                    label_style = TerminalStyle(fg_color="cyan", bold=True)
                self._draw_text(buffer, style_buffer, content_x, y, label, label_style)
                y += 1

            # Draw input field (indented by 1 char for visual hierarchy)
            field_x = content_x + 1
            display = value if not password else "*" * len(value)
            is_placeholder = False
            if not display and placeholder:
                display = placeholder
                is_placeholder = True
                cursor_pos = 0  # Cursor at start for placeholder

            field_width = 20

            # Style based on state:
            # - Disabled: dim
            # - Edit mode (full focus): white bg, show cursor
            # - Highlighted (nav focus): cyan bg
            # - Normal: default
            if not enabled:
                input_style = TerminalStyle(fg_color="bright_black")
                show_cursor = False
            elif node.focused and self._edit_mode:
                # Edit mode: white background with cursor
                input_style = TerminalStyle(fg_color="black", bg_color="white", bold=True)
                show_cursor = True
            elif node.focused:
                # Highlighted but not editing: cyan background
                input_style = TerminalStyle(fg_color="black", bg_color="cyan")
                show_cursor = False
            elif is_placeholder:
                input_style = TerminalStyle(fg_color="bright_black")
                show_cursor = False
            else:
                input_style = TerminalStyle()
                show_cursor = False

            # Truncate/pad display to field width
            display_text = display[:field_width].ljust(field_width)
            self._draw_text(buffer, style_buffer, field_x, y, f"[{display_text}]", input_style)

            # Draw cursor overlay in edit mode (doesn't shift text)
            if show_cursor and not is_placeholder:
                # Position cursor within the field (after the opening bracket)
                cursor_x = field_x + 1 + min(cursor_pos, field_width - 1)
                # Use underscore cursor that doesn't displace text
                cursor_style = TerminalStyle(fg_color="black", bg_color="white", bold=True, underline=True)
                # Get character at cursor position (or space if at end)
                char_at_cursor = display[cursor_pos] if cursor_pos < len(display) else " "
                self._draw_text(buffer, style_buffer, cursor_x, y, char_at_cursor, cursor_style)

        elif element.tag == "checkbox":
            text = getattr(element, "text", "") or ""
            value = getattr(element, "value", False)
            enabled = getattr(element, "enabled", True)

            # Checkbox: [x] text or [ ] text
            check_char = "x" if value else " "

            # Style based on state:
            # - Disabled: dim
            # - Highlighted (nav focus): cyan bg (checkboxes don't have edit mode)
            # - Normal: default
            if not enabled:
                checkbox_style = TerminalStyle(fg_color="bright_black")
            elif node.focused:
                checkbox_style = TerminalStyle(fg_color="black", bg_color="cyan", bold=True)
            else:
                checkbox_style = style

            # Draw after spacing row (0.5 top + 0.5 bottom effect)
            cb_y = content_y + 1
            checkbox_text = f"[{check_char}] {text}"
            self._draw_text(buffer, style_buffer, content_x, cb_y, checkbox_text, checkbox_style)

        elif element.tag == "toggle":
            text = getattr(element, "text", "") or ""
            value = getattr(element, "value", False)
            enabled = getattr(element, "enabled", True)

            # Toggle: ( ) OFF or (*) ON
            toggle_char = "*" if value else " "
            toggle_style = style
            if not enabled:
                toggle_style = TerminalStyle(fg_color="bright_black")

            # Draw after spacing row
            toggle_y = content_y + 1
            state_text = "ON" if value else "OFF"
            toggle_text = f"({toggle_char}) {text}" if text else f"({toggle_char}) {state_text}"
            self._draw_text(buffer, style_buffer, content_x, toggle_y, toggle_text, toggle_style)

        elif element.tag == "radio":
            options = getattr(element, "_options", [])
            value = getattr(element, "_value", None)
            enabled = getattr(element, "enabled", True)

            radio_style = style
            if not enabled:
                radio_style = TerminalStyle(fg_color="bright_black")

            y_offset = 0
            for opt in options:
                selected = opt.get("value") == value
                marker = "(*)" if selected else "( )"
                label = opt.get("label", str(opt.get("value", "")))
                self._draw_text(buffer, style_buffer, content_x, content_y + y_offset, f"{marker} {label}", radio_style)
                y_offset += 1

        elif element.tag == "select":
            label = getattr(element, "label", "") or ""
            display = getattr(element, "display_value", "") or ""
            enabled = getattr(element, "enabled", True)
            is_open = getattr(element, "_is_open", False)

            select_style = style
            if not enabled:
                select_style = TerminalStyle(fg_color="bright_black")

            x = content_x
            if label:
                self._draw_text(buffer, style_buffer, x, content_y, f"{label}: ", TerminalStyle(bold=True))
                x += len(label) + 2

            # Draw dropdown indicator
            arrow = "v" if not is_open else "^"
            dropdown_text = f"[{display:15}] {arrow}"
            self._draw_text(buffer, style_buffer, x, content_y, dropdown_text, select_style)

        elif element.tag == "progress":
            value = getattr(element, "_value", 0.0) or 0.0
            show_value = getattr(element, "show_value", False)

            # Progress bar: [=====>    ] or [=====>    ] 50%
            bar_width = 20
            filled = int(value * bar_width)
            bar = "=" * filled + ">" + " " * (bar_width - filled - 1) if filled < bar_width else "=" * bar_width
            progress_text = f"[{bar}]"
            if show_value:
                progress_text += f" {int(value * 100)}%"
            self._draw_text(buffer, style_buffer, content_x, content_y, progress_text, style)

        elif element.tag == "spinner":
            value = getattr(element, "_value", None)
            current_frame = getattr(element, "current_frame", "|")

            if value is not None:
                # Show progress arc
                progress_text = f"[{int(value * 100):3}%]"
            else:
                # Show spinning animation
                progress_text = f"[{current_frame}]"
            self._draw_text(buffer, style_buffer, content_x, content_y, progress_text, style)

        elif element.tag == "slider":
            value = getattr(element, "_value", 0.0) or 0.0
            min_val = getattr(element, "min", 0.0)
            max_val = getattr(element, "max", 1.0)
            enabled = getattr(element, "enabled", True)

            slider_style = style
            if not enabled:
                slider_style = TerminalStyle(fg_color="bright_black")

            # Calculate position
            if max_val > min_val:
                pct = (value - min_val) / (max_val - min_val)
            else:
                pct = 0.0

            track_width = 20
            handle_pos = int(pct * (track_width - 1))

            track = "-" * track_width
            track = track[:handle_pos] + "O" + track[handle_pos + 1:]
            slider_text = f"[{track}] {value:.2f}"
            self._draw_text(buffer, style_buffer, content_x, content_y, slider_text, slider_style)

        elif element.tag == "separator":
            vertical = getattr(element, "vertical", False)
            char = getattr(element, "char", "-" if not vertical else "|")
            width_cols = node.box.content_cols if not vertical else 1
            height_rows = node.box.content_rows if vertical else 1

            for row_off in range(height_rows):
                for col_off in range(width_cols):
                    self._draw_text(buffer, style_buffer, content_x + col_off, content_y + row_off, char, style)

        elif element.tag == "link":
            text = getattr(element, "text", "") or ""
            link_style = TerminalStyle(underline=True, fg_color="blue")
            self._draw_text(buffer, style_buffer, content_x, content_y, text, link_style)

        elif element.tag == "badge":
            text = getattr(element, "text", "") or ""
            badge_style = TerminalStyle(reverse=True)
            self._draw_text(buffer, style_buffer, content_x, content_y, f" {text} ", badge_style)

        elif element.tag == "icon":
            icon_text = getattr(element, "text", "[?]") or "[?]"
            self._draw_text(buffer, style_buffer, content_x, content_y, icon_text, style)

        elif element.tag == "textarea":
            label = getattr(element, "label", "") or ""
            value = getattr(element, "_value", "") or ""
            placeholder = getattr(element, "placeholder", "") or ""
            enabled = getattr(element, "enabled", True)

            y = content_y
            if label:
                self._draw_text(buffer, style_buffer, content_x, y, f"{label}:", TerminalStyle(bold=True))
                y += 1

            # Draw textarea box
            display = value if value else placeholder
            lines = display.split("\n")[:5]  # Show max 5 lines
            ta_style = style if value else TerminalStyle(fg_color="bright_black")
            if not enabled:
                ta_style = TerminalStyle(fg_color="bright_black")

            for i, line in enumerate(lines):
                self._draw_text(buffer, style_buffer, content_x, y + i, f"|{line[:30]:30}|", ta_style)

        elif element.tag == "number":
            label = getattr(element, "label", "") or ""
            display = getattr(element, "display_value", "") or ""
            enabled = getattr(element, "enabled", True)

            x = content_x
            if label:
                self._draw_text(buffer, style_buffer, x, content_y, f"{label}: ", TerminalStyle(bold=True))
                x += len(label) + 2

            num_style = style
            if not enabled:
                num_style = TerminalStyle(fg_color="bright_black")

            self._draw_text(buffer, style_buffer, x, content_y, f"[{display:10}]", num_style)

        elif element.tag == "tabs":
            # Render tab headers
            x = content_x
            for child in element.children:
                if child.tag == "tab":
                    name = getattr(child, "name", "")
                    tab_label = getattr(child, "label", name) or name
                    parent_value = getattr(element, "_value", None)
                    is_selected = name == parent_value
                    tab_style = TerminalStyle(reverse=True) if is_selected else style
                    self._draw_text(buffer, style_buffer, x, content_y, f" {tab_label} ", tab_style)
                    x += len(tab_label) + 3

        elif element.tag == "table":
            columns = getattr(element, "_columns", [])
            visible_rows = getattr(element, "visible_rows", [])
            title = getattr(element, "title", None)

            y = content_y
            # Draw title
            if title:
                self._draw_text(buffer, style_buffer, content_x, y, title, TerminalStyle(bold=True))
                y += 1

            # Draw header
            header_style = TerminalStyle(reverse=True)
            x = content_x
            for col in columns:
                col_label = col.get("label", col.get("name", ""))
                col_width = col.get("width", 12)
                self._draw_text(buffer, style_buffer, x, y, f"{col_label:{col_width}}", header_style)
                x += col_width + 1
            y += 1

            # Draw rows
            for row_data in visible_rows[:10]:  # Max 10 rows
                x = content_x
                for col in columns:
                    field = col.get("field", col.get("name", ""))
                    col_width = col.get("width", 12)
                    cell_value = str(row_data.get(field, ""))[:col_width]
                    self._draw_text(buffer, style_buffer, x, y, f"{cell_value:{col_width}}", style)
                    x += col_width + 1
                y += 1

        elif element.tag == "tree":
            nodes = getattr(element, "_nodes", [])
            expanded = getattr(element, "_expanded", set())
            selected = getattr(element, "_selected", None)
            node_key = getattr(element, "node_key", "id")
            label_key = getattr(element, "label_key", "label")
            children_key = getattr(element, "children_key", "children")

            def render_tree_nodes(tree_nodes, depth, y_offset):
                for tree_node in tree_nodes:
                    node_id = tree_node.get(node_key)
                    label_text = tree_node.get(label_key, "")
                    children = tree_node.get(children_key, [])

                    indent = "  " * depth
                    has_children = bool(children)
                    is_expanded = node_id in expanded
                    is_selected = node_id == selected

                    prefix = "[+]" if has_children and not is_expanded else "[-]" if has_children else " * "
                    line = f"{indent}{prefix} {label_text}"

                    line_style = TerminalStyle(reverse=True) if is_selected else style
                    self._draw_text(buffer, style_buffer, content_x, content_y + y_offset, line, line_style)
                    y_offset += 1

                    if is_expanded and children:
                        y_offset = render_tree_nodes(children, depth + 1, y_offset)
                return y_offset

            render_tree_nodes(nodes, 0, 0)

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
        """Draw text to buffer at ASCII coordinates."""
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
        """Draw border around a box at ASCII coordinates."""
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

    def _is_focusable(self, element: Optional["Element"]) -> bool:
        """Check if element can receive focus."""
        if not element:
            return False
        focusable_tags = ("button", "input", "checkbox", "select", "radio", "slider", "toggle", "textarea", "number")
        if element.tag in focusable_tags:
            return getattr(element, "enabled", True) and element.visible
        return False

    def get_element_at(self, x: int, y: int) -> Optional["Element"]:
        """Get element at screen coordinates (ASCII)."""
        # Convert to pixels and adjust for scroll
        abs_x_px = x * CHAR_WIDTH_PX + self._scroll_x
        abs_y_px = y * CHAR_HEIGHT_PX + self._scroll_y

        return self._find_element_at(self._root_node, abs_x_px, abs_y_px, 0, 0)

    def _find_element_at(
        self,
        node: Optional[DOMNode],
        x_px: int,
        y_px: int,
        parent_x: int,
        parent_y: int,
    ) -> Optional["Element"]:
        """Find deepest element containing point."""
        if not node or not node.visible:
            return None

        abs_x = parent_x + node.x
        abs_y = parent_y + node.y
        width = node.box.border_box_width
        height = node.box.border_box_height

        # Check if point is inside this node
        if not (abs_x <= x_px < abs_x + width and abs_y <= y_px < abs_y + height):
            return None

        # Check children first (they're on top)
        child_parent_x = abs_x + node.box.border_left + node.box.padding_left
        child_parent_y = abs_y + node.box.border_top + node.box.padding_top

        for child in reversed(node.children):
            result = self._find_element_at(child, x_px, y_px, child_parent_x, child_parent_y)
            if result:
                return result

        return node.element

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

    @property
    def focus_index(self) -> int:
        """Get current focus index."""
        return self._focus_index

    def restore_focus_index(self, index: int) -> None:
        """Restore focus to a specific index after re-render.

        Clamps to valid range if focusable list changed size.
        """
        if not self._focusable:
            self._focus_index = -1
            self._focused = None
            return

        # Clamp to valid range
        self._focus_index = max(0, min(index, len(self._focusable) - 1))
        self._focused = self._focusable[self._focus_index]
        self._dirty = True

    def schedule_focus_restore(self, index: int) -> None:
        """Schedule focus restoration after next render.

        Use this when navigating - the focusable list will be rebuilt
        during render, and this index will be applied after.
        """
        self._pending_focus_index = index

    def set_hover(self, element: Optional["Element"]) -> None:
        """Set hovered element."""
        if self._hovered != element:
            self._hovered = element
            self._dirty = True

    def scroll(self, dx: int = 0, dy: int = 0) -> None:
        """Scroll the view (in ASCII units)."""
        # Convert to pixels
        dx_px = dx * CHAR_WIDTH_PX
        dy_px = dy * CHAR_HEIGHT_PX

        max_scroll_x = max(0, self._content_width - self._screen_width_px)
        max_scroll_y = max(0, self._content_height - self._screen_height_px)

        self._scroll_x = max(0, min(self._scroll_x + dx_px, max_scroll_x))
        self._scroll_y = max(0, min(self._scroll_y + dy_px, max_scroll_y))
        self._dirty = True

    @property
    def focused(self) -> Optional["Element"]:
        return self._focused

    @property
    def edit_mode(self) -> bool:
        """True when focused element has full keyboard capture."""
        return self._edit_mode

    def enter_edit_mode(self) -> None:
        """Enter edit mode for current focused element."""
        if self._focused and self._focused.tag in ("input", "textarea", "select"):
            self._edit_mode = True
            self._dirty = True

    def exit_edit_mode(self) -> None:
        """Exit edit mode, return to navigation."""
        self._edit_mode = False
        self._dirty = True

    @property
    def needs_render(self) -> bool:
        return self._dirty

    def invalidate(self) -> None:
        """Mark renderer as needing re-render."""
        self._dirty = True
