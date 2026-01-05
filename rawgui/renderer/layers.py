"""Layered rendering system with caching and compositing.

Supports:
- Multiple render layers (base, overlays, modals)
- Character caching for smooth updates
- Shadow effects (Norton Commander style)
- Compositing overlays onto base layer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from copy import deepcopy

from .styles import TerminalStyle


@dataclass
class Cell:
    """A single cell in the render buffer."""
    char: str = " "
    style: Optional[TerminalStyle] = None

    def copy(self) -> "Cell":
        return Cell(self.char, self.style)


@dataclass
class Layer:
    """A render layer with its own buffer."""

    name: str
    width: int
    height: int
    z_index: int = 0
    visible: bool = True

    # Position offset (for floating layers like dialogs)
    x: int = 0
    y: int = 0

    # The cell buffer
    cells: List[List[Cell]] = field(default_factory=list)

    # Whether this layer casts a shadow
    has_shadow: bool = False
    shadow_offset_x: int = 2
    shadow_offset_y: int = 1

    # Transparency - cells with this char are see-through
    transparent_char: str = "\x00"  # Null char = transparent

    def __post_init__(self):
        if not self.cells:
            self.cells = [[Cell() for _ in range(self.width)] for _ in range(self.height)]

    def clear(self):
        """Clear the layer."""
        for row in self.cells:
            for cell in row:
                cell.char = self.transparent_char
                cell.style = None

    def set_cell(self, x: int, y: int, char: str, style: Optional[TerminalStyle] = None):
        """Set a cell in the layer."""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.cells[y][x].char = char
            self.cells[y][x].style = style

    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Get a cell from the layer."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.cells[y][x]
        return None

    def fill_rect(self, x: int, y: int, width: int, height: int,
                  char: str = " ", style: Optional[TerminalStyle] = None):
        """Fill a rectangle with a character."""
        for row in range(y, min(y + height, self.height)):
            for col in range(x, min(x + width, self.width)):
                if row >= 0 and col >= 0:
                    self.set_cell(col, row, char, style)


class LayerCompositor:
    """Composites multiple layers into a final output buffer.

    Features:
    - Layer stacking by z-index
    - Transparency support
    - Shadow rendering (darken underlying cells)
    - Caching for unchanged layers
    """

    # Shadow style - makes text darker/grayer
    SHADOW_STYLE = TerminalStyle(fg_color="bright_black")

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # Layer registry
        self._layers: Dict[str, Layer] = {}

        # Cached composite buffer
        self._composite: List[List[Cell]] = []
        self._cache_valid = False

        # Base layer (always exists)
        self.add_layer("base", z_index=0)

    def add_layer(self, name: str, z_index: int = 0,
                  has_shadow: bool = False,
                  x: int = 0, y: int = 0,
                  width: Optional[int] = None,
                  height: Optional[int] = None) -> Layer:
        """Add a new layer."""
        layer = Layer(
            name=name,
            width=width or self.width,
            height=height or self.height,
            z_index=z_index,
            x=x,
            y=y,
            has_shadow=has_shadow,
        )
        self._layers[name] = layer
        self._cache_valid = False
        return layer

    def get_layer(self, name: str) -> Optional[Layer]:
        """Get a layer by name."""
        return self._layers.get(name)

    def remove_layer(self, name: str):
        """Remove a layer."""
        if name != "base" and name in self._layers:
            del self._layers[name]
            self._cache_valid = False

    def invalidate(self):
        """Invalidate the cache."""
        self._cache_valid = False

    def composite(self) -> List[List[Cell]]:
        """Composite all layers into final buffer."""
        if self._cache_valid and self._composite:
            return self._composite

        # Create fresh composite buffer
        self._composite = [[Cell() for _ in range(self.width)] for _ in range(self.height)]

        # Sort layers by z-index
        sorted_layers = sorted(self._layers.values(), key=lambda l: l.z_index)

        for layer in sorted_layers:
            if not layer.visible:
                continue

            # If layer has shadow, darken cells under it first
            if layer.has_shadow:
                self._apply_shadow(layer)

            # Composite this layer onto the buffer
            self._composite_layer(layer)

        self._cache_valid = True
        return self._composite

    def _apply_shadow(self, layer: Layer):
        """Apply shadow effect under a layer."""
        shadow_x = layer.x + layer.shadow_offset_x
        shadow_y = layer.y + layer.shadow_offset_y

        for row in range(layer.height):
            for col in range(layer.width):
                src_cell = layer.get_cell(col, row)
                if src_cell and src_cell.char != layer.transparent_char:
                    # This cell will cast a shadow
                    dst_x = shadow_x + col
                    dst_y = shadow_y + row

                    if 0 <= dst_y < self.height and 0 <= dst_x < self.width:
                        # Darken the underlying cell
                        existing = self._composite[dst_y][dst_x]
                        # Create shadow by changing style to gray
                        existing.style = self.SHADOW_STYLE

    def _composite_layer(self, layer: Layer):
        """Composite a single layer onto the buffer."""
        for row in range(layer.height):
            for col in range(layer.width):
                cell = layer.get_cell(col, row)
                if cell and cell.char != layer.transparent_char:
                    dst_x = layer.x + col
                    dst_y = layer.y + row

                    if 0 <= dst_y < self.height and 0 <= dst_x < self.width:
                        self._composite[dst_y][dst_x] = cell.copy()

    def resize(self, width: int, height: int):
        """Resize the compositor."""
        self.width = width
        self.height = height

        # Resize base layer
        base = self._layers.get("base")
        if base:
            base.width = width
            base.height = height
            base.cells = [[Cell() for _ in range(width)] for _ in range(height)]

        self._cache_valid = False


def darken_style(style: Optional[TerminalStyle]) -> TerminalStyle:
    """Create a darkened version of a style for shadow effect."""
    if style is None:
        return TerminalStyle(fg_color="bright_black")

    # Map colors to their darker variants
    dark_map = {
        "white": "bright_black",
        "bright_white": "white",
        "red": "bright_black",
        "bright_red": "red",
        "green": "bright_black",
        "bright_green": "green",
        "blue": "bright_black",
        "bright_blue": "blue",
        "yellow": "bright_black",
        "bright_yellow": "yellow",
        "cyan": "bright_black",
        "bright_cyan": "cyan",
        "magenta": "bright_black",
        "bright_magenta": "magenta",
    }

    new_fg = dark_map.get(style.fg_color, "bright_black") if style.fg_color else "bright_black"

    return TerminalStyle(
        fg_color=new_fg,
        bg_color=style.bg_color,
        bold=False,  # Remove bold for shadow
        underline=style.underline,
    )
