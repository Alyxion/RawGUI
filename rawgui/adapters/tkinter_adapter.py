"""Tkinter rendering adapter for RawGUI.

Uses Pillow for all rendering, displayed on a single Tkinter canvas.
Supports multi-layer architecture for future hybrid UIs.
"""

from __future__ import annotations

import os
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union
from io import BytesIO
import urllib.request

from PIL import Image, ImageDraw, ImageFont, ImageTk

from .base import BaseAdapter

if TYPE_CHECKING:
    from ..element import Element


# Font cache directory
FONT_CACHE_DIR = Path.home() / ".cache" / "rawgui" / "fonts"

# Roboto font URLs (from Google Fonts GitHub)
ROBOTO_URLS = {
    "regular": "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf",
    "bold": "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf",
    "italic": "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Italic.ttf",
    "bold_italic": "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-BoldItalic.ttf",
    "mono": "https://github.com/googlefonts/RobotoMono/raw/main/fonts/ttf/RobotoMono-Regular.ttf",
    "mono_bold": "https://github.com/googlefonts/RobotoMono/raw/main/fonts/ttf/RobotoMono-Bold.ttf",
}


@dataclass
class RenderNode:
    """Node in the render tree with computed layout and caching."""

    element: Optional["Element"] = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    clip_rect: Optional[Tuple[int, int, int, int]] = None  # x1, y1, x2, y2
    focused: bool = False
    hovered: bool = False
    children: List["RenderNode"] = field(default_factory=list)

    # Caching support
    cached_image: Optional[Image.Image] = None
    dirty: bool = True
    is_cacheable: bool = False  # True for rows, columns, cards
    cache_key: Optional[str] = None  # For cache invalidation

    # Native widget support
    is_native_hole: bool = False  # True if this is a placeholder for native widget
    native_widget: Optional[Any] = None  # Reference to actual Tkinter widget


@dataclass
class Layer:
    """A rendering layer for compositing."""

    name: str
    image: Image.Image
    z_index: int = 0
    visible: bool = True
    dirty: bool = True


class FontManager:
    """Manages font loading and caching."""

    def __init__(self) -> None:
        self._fonts: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
        self._ensure_fonts_downloaded()

    def _ensure_fonts_downloaded(self) -> None:
        """Download Roboto fonts if not cached."""
        FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        for name, url in ROBOTO_URLS.items():
            font_path = FONT_CACHE_DIR / f"Roboto-{name}.ttf"
            if not font_path.exists():
                try:
                    print(f"Downloading Roboto {name} font...")
                    urllib.request.urlretrieve(url, font_path)
                except Exception as e:
                    print(f"Warning: Could not download font {name}: {e}")

    def get_font(
        self,
        size: int = 14,
        bold: bool = False,
        italic: bool = False,
        mono: bool = False,
    ) -> ImageFont.FreeTypeFont:
        """Get a font with specified attributes.

        Args:
            size: Font size in pixels
            bold: Use bold weight
            italic: Use italic style
            mono: Use monospace font

        Returns:
            PIL ImageFont object
        """
        # Build cache key
        key = (f"{'mono' if mono else 'regular'}_{bold}_{italic}", size)

        if key not in self._fonts:
            # Determine font file
            if mono:
                font_name = "mono_bold" if bold else "mono"
            elif bold and italic:
                font_name = "bold_italic"
            elif bold:
                font_name = "bold"
            elif italic:
                font_name = "italic"
            else:
                font_name = "regular"

            font_path = FONT_CACHE_DIR / f"Roboto-{font_name}.ttf"

            try:
                self._fonts[key] = ImageFont.truetype(str(font_path), size)
            except Exception:
                # Fallback to default font
                self._fonts[key] = ImageFont.load_default()

        return self._fonts[key]


class TkinterAdapter(BaseAdapter):
    """Tkinter rendering adapter using Pillow for painting.

    Features:
    - Single canvas rendering
    - 100% Pillow-based painting
    - Intelligent clipping for nested elements
    - Multi-layer architecture for hybrid UIs
    - Full mouse and keyboard support
    """

    # Default colors (Material Design inspired)
    COLORS = {
        "background": "#1e1e1e",
        "surface": "#2d2d2d",
        "primary": "#00bcd4",  # Cyan
        "secondary": "#ff9800",
        "text": "#ffffff",
        "text_secondary": "#b0b0b0",
        "border": "#404040",
        "focus": "#00bcd4",
        "edit": "#ffffff",
        "disabled": "#666666",
        "error": "#f44336",
        "success": "#4caf50",
    }

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "RawGUI",
        dark: bool = True,
    ) -> None:
        """Initialize the Tkinter adapter.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
            dark: Use dark theme
        """
        super().__init__()

        self.width = width
        self.height = height
        self.title = title
        self.dark = dark

        # Tkinter components (created in run())
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._photo_image: Optional[ImageTk.PhotoImage] = None

        # Rendering
        self._font_manager = FontManager()
        self._layers: Dict[str, Layer] = {}
        self._render_tree: Optional[RenderNode] = None
        self._element_map: Dict[int, RenderNode] = {}  # element.id -> node
        self._pending_focus_index: Optional[int] = None

        # State
        self._running = False
        self._root_element: Optional["Element"] = None
        self._on_close: Optional[Callable] = None

        # Client for page building (set externally)
        self._client: Optional[Any] = None

        # Page rebuild callback (set externally)
        self._rebuild_callback: Optional[Callable[[], Any]] = None

        # Native widget tracking
        self._native_widgets: Dict[int, tk.Widget] = {}  # element.id -> widget
        self._native_frames: Dict[int, tk.Frame] = {}  # element.id -> container frame

        # Render cache for incremental updates
        self._node_cache: Dict[int, RenderNode] = {}  # element.id -> cached node
        self._cache_enabled: bool = True

        # Background image ID for canvas
        self._bg_image_id: Optional[int] = None

        # Create base layer
        self._create_layer("base", z_index=0)

    def _create_layer(self, name: str, z_index: int = 0) -> Layer:
        """Create a new rendering layer."""
        image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        layer = Layer(name=name, image=image, z_index=z_index)
        self._layers[name] = layer
        return layer

    def _get_layer(self, name: str) -> Layer:
        """Get layer by name, creating if needed."""
        if name not in self._layers:
            return self._create_layer(name)
        return self._layers[name]

    def render(self, root: "Element") -> None:
        """Render the element tree to Pillow image."""
        self._root_element = root
        self._element_map.clear()
        self._focusable.clear()

        # Build render tree
        self._render_tree = self._build_render_tree(root, 0, 0, self.width, self.height)

        # Index focusable elements
        self._index_focusable(self._render_tree)

        # Restore pending focus
        if self._pending_focus_index is not None and self._focusable:
            idx = max(0, min(self._pending_focus_index, len(self._focusable) - 1))
            self._focus_index = idx
            self._focused = self._focusable[idx]
            self._pending_focus_index = None

        # Initial focus
        if self._focusable and self._focus_index < 0:
            self._focus_index = 0
            self._focused = self._focusable[0]

        # Clear base layer
        base_layer = self._get_layer("base")
        base_layer.image = Image.new("RGBA", (self.width, self.height), self.COLORS["background"])

        # Paint to base layer
        draw = ImageDraw.Draw(base_layer.image)
        self._paint_node(draw, self._render_tree, base_layer.image)

        # Composite layers and update canvas
        self._composite_and_display()

        self._dirty = False

    def _build_render_tree(
        self,
        element: "Element",
        x: int,
        y: int,
        available_width: int,
        available_height: int,
        clip_rect: Optional[Tuple[int, int, int, int]] = None,
    ) -> RenderNode:
        """Build render tree with layout calculations and caching."""
        node = RenderNode(
            element=element,
            x=x,
            y=y,
            clip_rect=clip_rect,
            focused=element == self._focused,
            hovered=element == self._hovered,
        )

        # Mark cacheable containers (major layout boundaries)
        if element.tag in ("row", "column", "card"):
            node.is_cacheable = True
            node.cache_key = f"{element.id}:{element.tag}"

        # Handle native widget elements
        if element.tag == "native_widget":
            node.is_native_hole = True
            node.dirty = True  # Always re-evaluate native widgets

        # Calculate size based on element type
        width, height = self._calculate_size(element, available_width, available_height)
        node.width = width
        node.height = height

        # Check cache for incremental updates
        if self._cache_enabled and element.id in self._node_cache:
            cached = self._node_cache[element.id]
            # Reuse cache if position/size unchanged and not dirty
            if (cached.x == x and cached.y == y and
                cached.width == width and cached.height == height and
                cached.focused == node.focused and
                cached.hovered == node.hovered and
                not cached.dirty and cached.cached_image is not None):
                # Reuse cached node
                node.cached_image = cached.cached_image
                node.dirty = False

        # Map element to node
        self._element_map[element.id] = node

        # Build children
        if hasattr(element, "children") and element.children:
            child_x, child_y = x, y
            padding = 8  # Default padding

            # Adjust for container types
            if element.tag in ("card", "dialog"):
                child_x += padding
                child_y += padding
                available_width -= padding * 2
                available_height -= padding * 2

            # Layout children based on container type
            if element.tag == "row":
                # Horizontal layout
                for child in element.children:
                    if not getattr(child, "visible", True):
                        continue
                    child_node = self._build_render_tree(
                        child, child_x, child_y, available_width, available_height, clip_rect
                    )
                    node.children.append(child_node)
                    child_x += child_node.width + 8  # gap
            else:
                # Vertical layout (column, card, etc.)
                for child in element.children:
                    if not getattr(child, "visible", True):
                        continue
                    child_node = self._build_render_tree(
                        child, child_x, child_y, available_width, available_height, clip_rect
                    )
                    node.children.append(child_node)
                    child_y += child_node.height + 4  # gap

        return node

    def _calculate_size(
        self, element: "Element", available_width: int, available_height: int
    ) -> Tuple[int, int]:
        """Calculate element size."""
        tag = element.tag
        font = self._font_manager.get_font(size=14)

        if tag == "label":
            text = getattr(element, "text", "") or ""
            if not text:
                return available_width, 8  # Empty label acts as spacer
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0] + 16, bbox[3] - bbox[1] + 16

        elif tag == "button":
            text = getattr(element, "text", "") or ""
            bbox = font.getbbox(f"[ {text} ]")
            return bbox[2] - bbox[0] + 24, 40

        elif tag == "input":
            label = getattr(element, "label", "") or ""
            height = 64 if label else 44
            return min(300, available_width), height

        elif tag == "checkbox":
            text = getattr(element, "text", "") or ""
            bbox = font.getbbox(f"[x] {text}")
            return bbox[2] - bbox[0] + 24, 40

        elif tag == "row":
            # Calculate based on children
            if hasattr(element, "children") and element.children:
                max_height = 0
                total_width = 0
                for child in element.children:
                    if not getattr(child, "visible", True):
                        continue
                    cw, ch = self._calculate_size(child, available_width, available_height)
                    total_width += cw + 8
                    max_height = max(max_height, ch)
                return min(total_width, available_width), max_height
            return available_width, 40

        elif tag == "column":
            # Calculate based on children
            if hasattr(element, "children") and element.children:
                max_width = 0
                total_height = 0
                for child in element.children:
                    if not getattr(child, "visible", True):
                        continue
                    cw, ch = self._calculate_size(child, available_width, available_height)
                    max_width = max(max_width, cw)
                    total_height += ch + 4
                return min(max_width, available_width), total_height
            return available_width, available_height

        elif tag == "card":
            # Calculate based on children + padding
            padding = 16
            if hasattr(element, "children") and element.children:
                max_width = 0
                total_height = 0
                for child in element.children:
                    if not getattr(child, "visible", True):
                        continue
                    cw, ch = self._calculate_size(child, available_width - padding * 2, available_height)
                    max_width = max(max_width, cw)
                    total_height += ch + 4
                return min(max_width + padding * 2, available_width), total_height + padding * 2
            return min(400, available_width), 100

        elif tag == "native_widget":
            # Native widgets specify their own size
            width = getattr(element, "width", 200)
            height = getattr(element, "height", 100)
            return width, height

        return 100, 32

    def _index_focusable(self, node: RenderNode) -> None:
        """Index focusable elements in render tree."""
        if node.element and self._is_focusable(node.element):
            self._focusable.append(node.element)
            node.focused = node.element == self._focused

        for child in node.children:
            self._index_focusable(child)

    def _paint_node(self, draw: ImageDraw.Draw, node: RenderNode, image: Image.Image) -> None:
        """Paint a render node and its children with caching support."""
        if not node.element:
            return

        element = node.element
        tag = element.tag

        # Handle native widget - don't paint, just reserve space
        if tag == "native_widget":
            self._paint_native_widget_placeholder(draw, node)
            self._position_native_widget(node)
            return

        # Check if we can use cached image for this node
        if node.is_cacheable and not node.dirty and node.cached_image is not None:
            # Paste cached image at node position
            image.paste(node.cached_image, (node.x, node.y), node.cached_image)
            return

        # For cacheable nodes, render to a separate image
        if node.is_cacheable:
            # Create a new image for this node's content
            node_image = Image.new("RGBA", (node.width, node.height), (0, 0, 0, 0))
            node_draw = ImageDraw.Draw(node_image)

            # Paint this node's background to node_image (offset to 0,0)
            temp_x, temp_y = node.x, node.y
            node.x, node.y = 0, 0

            if tag == "card":
                self._paint_card(node_draw, node, node_image)
            elif tag in ("row", "column"):
                pass  # Containers have no background

            # Paint children (recursively, they'll be at relative positions)
            for child in node.children:
                # Adjust child positions relative to this node
                child.x -= temp_x
                child.y -= temp_y
                self._paint_node(node_draw, child, node_image)
                child.x += temp_x
                child.y += temp_y

            node.x, node.y = temp_x, temp_y

            # Cache and paste
            node.cached_image = node_image
            node.dirty = False
            image.paste(node_image, (node.x, node.y), node_image)

            # Update cache
            self._node_cache[element.id] = node
            return

        # Standard painting for non-cacheable nodes
        if tag == "label":
            self._paint_label(draw, node)
        elif tag == "button":
            self._paint_button(draw, node)
        elif tag == "input":
            self._paint_input(draw, node)
        elif tag == "checkbox":
            self._paint_checkbox(draw, node)
        elif tag == "card":
            self._paint_card(draw, node, image)
        elif tag in ("row", "column"):
            pass  # Container, just paint children

        # Paint children
        for child in node.children:
            self._paint_node(draw, child, image)

    def _paint_label(self, draw: ImageDraw.Draw, node: RenderNode) -> None:
        """Paint a label element."""
        element = node.element
        text = getattr(element, "text", "") or ""
        font = self._font_manager.get_font(size=14)

        draw.text(
            (node.x + 8, node.y + 8),
            text,
            fill=self.COLORS["text"],
            font=font,
        )

    def _paint_button(self, draw: ImageDraw.Draw, node: RenderNode) -> None:
        """Paint a button element."""
        element = node.element
        text = getattr(element, "text", "") or ""
        enabled = getattr(element, "enabled", True)
        font = self._font_manager.get_font(size=14, bold=True)

        # Colors based on state
        if node.focused and self._edit_mode:
            bg_color = self.COLORS["edit"]
            text_color = self.COLORS["background"]
            border_color = self.COLORS["edit"]
        elif node.focused:
            bg_color = self.COLORS["focus"]
            text_color = self.COLORS["background"]
            border_color = self.COLORS["focus"]
        elif node.hovered:
            bg_color = "#3d3d3d"  # Slightly lighter on hover
            text_color = self.COLORS["text"]
            border_color = self.COLORS["focus"]
        elif not enabled:
            bg_color = self.COLORS["disabled"]
            text_color = self.COLORS["text_secondary"]
            border_color = self.COLORS["disabled"]
        else:
            bg_color = self.COLORS["surface"]
            text_color = self.COLORS["text"]
            border_color = "#505050"  # Visible border for unfocused buttons

        # Draw rounded rectangle with border
        x1, y1 = node.x + 4, node.y + 4
        x2, y2 = node.x + node.width - 4, node.y + node.height - 4
        draw.rounded_rectangle([x1, y1, x2, y2], radius=6, fill=bg_color, outline=border_color, width=2)

        # Draw text centered
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = node.x + (node.width - text_width) // 2
        text_y = node.y + (node.height - text_height) // 2 - 2
        draw.text((text_x, text_y), text, fill=text_color, font=font)

    def _paint_input(self, draw: ImageDraw.Draw, node: RenderNode) -> None:
        """Paint an input element."""
        element = node.element
        label = getattr(element, "label", "") or ""
        value = getattr(element, "value", "") or ""
        placeholder = getattr(element, "placeholder", "") or ""
        password = getattr(element, "password", False)
        enabled = getattr(element, "enabled", True)
        cursor_pos = getattr(element, "_cursor_pos", len(value))

        font = self._font_manager.get_font(size=14)
        label_font = self._font_manager.get_font(size=12)

        y = node.y + 8

        # Draw label above
        if label:
            label_color = self.COLORS["focus"] if node.focused else self.COLORS["text_secondary"]
            draw.text((node.x + 12, y), label, fill=label_color, font=label_font)
            y += 20

        # Input field background
        if node.focused and self._edit_mode:
            bg_color = self.COLORS["edit"]
            text_color = self.COLORS["background"]
            border_color = self.COLORS["focus"]
        elif node.focused:
            bg_color = self.COLORS["focus"]
            text_color = self.COLORS["background"]
            border_color = self.COLORS["focus"]
        elif not enabled:
            bg_color = self.COLORS["disabled"]
            text_color = self.COLORS["text_secondary"]
            border_color = self.COLORS["border"]
        else:
            bg_color = self.COLORS["surface"]
            text_color = self.COLORS["text"]
            border_color = self.COLORS["border"]

        # Draw field
        x1, y1 = node.x + 8, y
        x2, y2 = node.x + node.width - 8, y + 28
        draw.rounded_rectangle([x1, y1, x2, y2], radius=4, fill=bg_color, outline=border_color)

        # Draw text
        display = value if not password else "*" * len(value)
        if not display and placeholder:
            display = placeholder
            text_color = self.COLORS["text_secondary"]

        draw.text((x1 + 8, y1 + 4), display[:30], fill=text_color, font=font)

        # Draw cursor in edit mode
        if node.focused and self._edit_mode:
            cursor_text = display[:cursor_pos]
            cursor_x = x1 + 8 + font.getbbox(cursor_text)[2]
            draw.line([(cursor_x, y1 + 4), (cursor_x, y2 - 4)], fill=text_color, width=2)

    def _paint_checkbox(self, draw: ImageDraw.Draw, node: RenderNode) -> None:
        """Paint a checkbox element."""
        element = node.element
        text = getattr(element, "text", "") or ""
        value = getattr(element, "value", False)
        enabled = getattr(element, "enabled", True)
        font = self._font_manager.get_font(size=14)

        y = node.y + 12

        # Checkbox box
        box_size = 18
        x1, y1 = node.x + 8, y
        x2, y2 = x1 + box_size, y1 + box_size

        if node.focused:
            bg_color = self.COLORS["focus"]
            text_color = self.COLORS["background"]
        elif not enabled:
            bg_color = self.COLORS["disabled"]
            text_color = self.COLORS["text_secondary"]
        else:
            bg_color = self.COLORS["surface"]
            text_color = self.COLORS["text"]

        draw.rounded_rectangle([x1, y1, x2, y2], radius=2, fill=bg_color, outline=self.COLORS["border"])

        # Check mark
        if value:
            check_color = self.COLORS["background"] if node.focused else self.COLORS["focus"]
            draw.text((x1 + 3, y1 - 2), "✓", fill=check_color, font=font)

        # Label
        draw.text((x2 + 8, y1), text, fill=text_color if enabled else self.COLORS["text_secondary"], font=font)

    def _paint_card(self, draw: ImageDraw.Draw, node: RenderNode, image: Image.Image) -> None:
        """Paint a card element."""
        # Card background with shadow
        shadow_offset = 3
        card_width = node.width - shadow_offset
        card_height = node.height - shadow_offset

        # Shadow
        draw.rounded_rectangle(
            [node.x + shadow_offset, node.y + shadow_offset,
             node.x + node.width, node.y + node.height],
            radius=8,
            fill="#00000060",
        )

        # Card background
        draw.rounded_rectangle(
            [node.x, node.y, node.x + card_width, node.y + card_height],
            radius=8,
            fill=self.COLORS["surface"],
            outline=self.COLORS["border"],
        )

    def _paint_native_widget_placeholder(self, draw: ImageDraw.Draw, node: RenderNode) -> None:
        """Paint a placeholder rectangle for native widget area."""
        # Draw a subtle border to show where the native widget will be
        draw.rectangle(
            [node.x, node.y, node.x + node.width, node.y + node.height],
            fill=self.COLORS["surface"],
            outline=self.COLORS["border"],
        )

        # If no native widget is attached yet, show a label
        if node.element and node.element.id not in self._native_widgets:
            font = self._font_manager.get_font(size=12)
            text = "Native Widget"
            draw.text(
                (node.x + 8, node.y + 8),
                text,
                fill=self.COLORS["text_secondary"],
                font=font,
            )

    def _position_native_widget(self, node: RenderNode) -> None:
        """Position the native Tkinter widget at the correct location."""
        if not node.element or not self._canvas or not self._root:
            return

        element = node.element
        widget_id = element.id

        # Get or create the native widget
        if widget_id not in self._native_widgets:
            # Get the widget factory from the element
            factory = getattr(element, "widget_factory", None)
            if factory and callable(factory):
                # Create container frame as child of root window (not canvas)
                # This ensures proper rendering and event handling
                frame = tk.Frame(
                    self._root,
                    bg=self.COLORS["surface"],
                    highlightthickness=0,
                    width=node.width,
                    height=node.height,
                )
                # Prevent frame from shrinking to fit children
                frame.pack_propagate(False)
                self._native_frames[widget_id] = frame

                # Create the actual widget inside the frame
                widget = factory(frame)
                if widget:
                    widget.pack(fill=tk.BOTH, expand=True)
                    self._native_widgets[widget_id] = widget

                # Force frame to update so its geometry is calculated
                frame.update_idletasks()

                # Place on canvas using create_window (ensures it's on top)
                window_id = self._canvas.create_window(
                    node.x,
                    node.y,
                    window=frame,
                    anchor=tk.NW,
                    width=node.width,
                    height=node.height,
                )
                # Store window ID for later updates
                frame._canvas_window_id = window_id
        else:
            # Update existing widget position
            if widget_id in self._native_frames:
                frame = self._native_frames[widget_id]
                if hasattr(frame, "_canvas_window_id"):
                    self._canvas.coords(frame._canvas_window_id, node.x, node.y)
                    self._canvas.itemconfig(
                        frame._canvas_window_id,
                        width=node.width,
                        height=node.height,
                    )

    def remove_native_widget(self, element_id: int) -> None:
        """Remove a native widget by element ID."""
        if element_id in self._native_frames:
            frame = self._native_frames[element_id]
            # Delete canvas window item first
            if hasattr(frame, "_canvas_window_id") and self._canvas:
                self._canvas.delete(frame._canvas_window_id)
            frame.destroy()
            del self._native_frames[element_id]
        if element_id in self._native_widgets:
            del self._native_widgets[element_id]

    def clear_native_widgets(self) -> None:
        """Remove all native widgets."""
        for frame in self._native_frames.values():
            # Delete canvas window item first
            if hasattr(frame, "_canvas_window_id") and self._canvas:
                self._canvas.delete(frame._canvas_window_id)
            frame.destroy()
        self._native_widgets.clear()
        self._native_frames.clear()

    def _composite_and_display(self) -> None:
        """Composite all layers and update the Tkinter canvas."""
        if not self._canvas:
            return

        # Sort layers by z_index
        sorted_layers = sorted(self._layers.values(), key=lambda l: l.z_index)

        # Composite
        result = Image.new("RGBA", (self.width, self.height), self.COLORS["background"])
        for layer in sorted_layers:
            if layer.visible:
                result = Image.alpha_composite(result, layer.image)

        # Convert to PhotoImage
        self._photo_image = ImageTk.PhotoImage(result)

        # Update canvas - delete only the background image, keep native widget windows
        # Find and delete the existing background image
        if hasattr(self, "_bg_image_id") and self._bg_image_id:
            self._canvas.delete(self._bg_image_id)

        # Create new background image (behind native widgets)
        self._bg_image_id = self._canvas.create_image(0, 0, anchor=tk.NW, image=self._photo_image)

        # Lower the background image below all windows
        self._canvas.tag_lower(self._bg_image_id)

    def run(self, on_close: Optional[Callable] = None) -> None:
        """Run the Tkinter main loop."""
        self._on_close = on_close
        self._running = True

        # Create window
        self._root = tk.Tk()
        self._root.title(self.title)
        self._root.geometry(f"{self.width}x{self.height}")
        self._root.configure(bg=self.COLORS["background"])

        # Create canvas
        self._canvas = tk.Canvas(
            self._root,
            width=self.width,
            height=self.height,
            bg=self.COLORS["background"],
            highlightthickness=0,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self._canvas.bind("<Button-1>", self._on_click)
        self._canvas.bind("<Motion>", self._on_motion)
        self._root.bind("<Key>", self._on_key)
        self._root.bind("<Escape>", self._on_escape)
        self._root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Initial render
        if self._root_element:
            self.render(self._root_element)

        # Start main loop
        self._root.mainloop()

    def stop(self) -> None:
        """Stop the main loop."""
        self._running = False
        if self._root:
            self._root.quit()

    def _on_click(self, event: tk.Event) -> None:
        """Handle mouse click."""
        element = self.get_element_at(event.x, event.y)
        if element:
            self.focus_element(element)

            if element.tag == "button":
                element._fire_event("click")
            elif element.tag == "checkbox":
                element.toggle()
            elif element.tag == "input":
                self.enter_edit_mode()

            self._check_navigation_and_render()

    def _on_motion(self, event: tk.Event) -> None:
        """Handle mouse motion."""
        element = self.get_element_at(event.x, event.y)
        if element != self._hovered:
            self.set_hover(element)
            if self._root_element and self._dirty:
                self.render(self._root_element)

    def _on_key(self, event: tk.Event) -> None:
        """Handle key press."""
        key = event.keysym
        char = event.char

        # Navigation
        if key == "Tab":
            if event.state & 1:  # Shift
                self.focus_prev()
            else:
                self.focus_next()
            self.exit_edit_mode()
        elif key in ("Up", "Down", "Left", "Right"):
            if self._edit_mode and self._focused and self._focused.tag == "input":
                self._handle_input_cursor(key)
            else:
                if key in ("Up", "Left"):
                    self.focus_prev()
                else:
                    self.focus_next()
        elif key == "Return":
            self._handle_enter()
        elif key == "space" and not self._edit_mode:
            self._handle_space()
        elif self._edit_mode and self._focused and self._focused.tag == "input":
            self._handle_input_char(event)

        self._check_navigation_and_render()

    def _on_escape(self, event: tk.Event) -> None:
        """Handle Escape key."""
        if self._edit_mode:
            self.exit_edit_mode()
            self.invalidate()
            if self._root_element:
                self.render(self._root_element)
        else:
            self.stop()

    def _on_window_close(self) -> None:
        """Handle window close."""
        if self._on_close:
            self._on_close()
        self.stop()

    def _handle_enter(self) -> None:
        """Handle Enter key."""
        if self._focused:
            if self._focused.tag == "button":
                self._focused._fire_event("click")
            elif self._focused.tag == "checkbox":
                self._focused.toggle()
            elif self._focused.tag == "input":
                if self._edit_mode:
                    self.exit_edit_mode()
                else:
                    self.enter_edit_mode()

    def _handle_space(self) -> None:
        """Handle Space key (not in edit mode)."""
        if self._focused:
            if self._focused.tag == "button":
                self._focused._fire_event("click")
            elif self._focused.tag == "checkbox":
                self._focused.toggle()

    def _handle_input_cursor(self, key: str) -> None:
        """Handle cursor movement in input."""
        if not self._focused:
            return

        value = getattr(self._focused, "value", "") or ""
        cursor_pos = getattr(self._focused, "_cursor_pos", len(value))

        if key == "Left" and cursor_pos > 0:
            self._focused._cursor_pos = cursor_pos - 1
        elif key == "Right" and cursor_pos < len(value):
            self._focused._cursor_pos = cursor_pos + 1

    def _handle_input_char(self, event: tk.Event) -> None:
        """Handle character input."""
        if not self._focused:
            return

        value = getattr(self._focused, "value", "") or ""
        cursor_pos = getattr(self._focused, "_cursor_pos", len(value))

        if event.keysym == "BackSpace":
            if cursor_pos > 0:
                self._focused.value = value[:cursor_pos - 1] + value[cursor_pos:]
                self._focused._cursor_pos = cursor_pos - 1
                self._focused._fire_event("change", self._focused.value)
        elif event.keysym == "Delete":
            if cursor_pos < len(value):
                self._focused.value = value[:cursor_pos] + value[cursor_pos + 1:]
                self._focused._fire_event("change", self._focused.value)
        elif event.keysym == "Home":
            self._focused._cursor_pos = 0
        elif event.keysym == "End":
            self._focused._cursor_pos = len(value)
        elif event.char and event.char.isprintable():
            self._focused.value = value[:cursor_pos] + event.char + value[cursor_pos:]
            self._focused._cursor_pos = cursor_pos + 1
            self._focused._fire_event("change", self._focused.value)

    def _check_navigation_and_render(self) -> None:
        """Check for pending navigation and re-render."""
        from ..app import app

        # Check if there's a pending navigation (from ui.navigate.to())
        if app._pending_navigation is not None:
            app._pending_navigation = None

            # Save focus index for restoration
            self._pending_focus_index = self._focus_index

            # Use rebuild callback if available
            if self._rebuild_callback:
                new_root = self._rebuild_callback()
                if new_root:
                    self._root_element = new_root

        # Always re-render
        self.invalidate()
        if self._root_element:
            self.render(self._root_element)

    def get_element_at(self, x: int, y: int) -> Optional["Element"]:
        """Get element at screen coordinates."""
        if not self._render_tree:
            return None

        return self._hit_test(self._render_tree, x, y)

    def _hit_test(self, node: RenderNode, x: int, y: int) -> Optional["Element"]:
        """Recursive hit testing."""
        # Check children first (front to back)
        for child in reversed(node.children):
            result = self._hit_test(child, x, y)
            if result:
                return result

        # Check this node
        if node.element and self._is_focusable(node.element):
            if node.x <= x <= node.x + node.width and node.y <= y <= node.y + node.height:
                return node.element

        return None

    def get_image(self) -> Image.Image:
        """Get the current rendered image (for screenshots).

        Returns:
            PIL Image of the current render
        """
        # Composite all layers
        sorted_layers = sorted(self._layers.values(), key=lambda l: l.z_index)
        result = Image.new("RGBA", (self.width, self.height), self.COLORS["background"])
        for layer in sorted_layers:
            if layer.visible:
                result = Image.alpha_composite(result, layer.image)
        return result.convert("RGB")

    def screenshot(self, path: str | Path) -> Path:
        """Save a screenshot to file.

        Args:
            path: Output path for the PNG file

        Returns:
            Path to the created image
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img = self.get_image()
        img.save(str(path))
        return path

    def render_headless(self, root: "Element") -> Image.Image:
        """Render element tree headlessly (no Tkinter window).

        This is useful for testing and screenshot generation.

        Args:
            root: Root element to render

        Returns:
            PIL Image of the rendered content
        """
        # Just call render() - it builds the PIL image without needing Tkinter
        self.render(root)
        return self.get_image()
