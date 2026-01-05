"""Comprehensive Tailwind CSS parser and utilities for RawGUI.

This module provides complete Tailwind CSS support for both TUI and Tkinter renderers,
with proper unit conversion and responsive design capabilities.

Design principles:
- All calculations done in pixels (base unit)
- TUI converts pixels to character cells (12px width, 24px height)
- Tailwind values follow standard spacing scale (4px units)
- Responsive classes (@media queries) are handled at render time
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

# Tailwind default spacing scale (in pixels)
# All spacing values are multiples of 4px (the base unit)
SPACING_SCALE = {
    '0': 0,
    '1': 4,
    '2': 8,
    '3': 12,
    '4': 16,
    '6': 24,
    '8': 32,
    '10': 40,
    '12': 48,
    '16': 64,
    '20': 80,
    '24': 96,
    '28': 112,
    '32': 128,
    '36': 144,
    '40': 160,
    '44': 176,
    '48': 192,
    '52': 208,
    '56': 224,
    '60': 240,
    '64': 256,
    '80': 320,
    '96': 384,
}

# Tailwind width/height scale
SIZE_SCALE = {
    **SPACING_SCALE,
    '1/2': None,  # Special: 50%
    '1/3': None,  # Special: 33.333%
    '2/3': None,  # Special: 66.666%
    '1/4': None,  # Special: 25%
    '3/4': None,  # Special: 75%
    '1/5': None,  # Special: 20%
    '2/5': None,  # Special: 40%
    '3/5': None,  # Special: 60%
    '4/5': None,  # Special: 80%
    '1/6': None,  # Special: 16.666%
    '5/6': None,  # Special: 83.333%
    'full': None,  # Special: 100%
    'screen': None,  # Special: 100vw/100vh
}

# Breakpoints for responsive design
BREAKPOINTS = {
    'sm': 640,
    'md': 768,
    'lg': 1024,
    'xl': 1280,
    '2xl': 1536,
}

# Font sizes (in pixels)
FONT_SIZES = {
    'xs': 12,
    'sm': 14,
    'base': 16,
    'lg': 18,
    'xl': 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
    '5xl': 48,
    '6xl': 60,
    '7xl': 72,
    '8xl': 96,
    '9xl': 128,
}

# Line heights (as multipliers of font-size)
LINE_HEIGHTS = {
    '3': 0.75,
    '4': 1,
    '5': 1.25,
    '6': 1.5,
    '7': 1.75,
    '8': 2,
    '9': 2.25,
    '10': 2.5,
}

# Border radius (in pixels)
BORDER_RADIUS = {
    'none': 0,
    'sm': 2,
    'base': 4,
    'md': 6,
    'lg': 8,
    'xl': 12,
    '2xl': 16,
    '3xl': 24,
    'full': 9999,
}

# Colors - Tailwind default palette
COLORS = {
    'transparent': 'transparent',
    'black': '#000000',
    'white': '#ffffff',
    'slate-50': '#f8fafc',
    'slate-100': '#f1f5f9',
    'slate-200': '#e2e8f0',
    'slate-300': '#cbd5e1',
    'slate-400': '#94a3b8',
    'slate-500': '#64748b',
    'slate-600': '#475569',
    'slate-700': '#334155',
    'slate-800': '#1e293b',
    'slate-900': '#0f172a',
    'gray-50': '#f9fafb',
    'gray-100': '#f3f4f6',
    'gray-200': '#e5e7eb',
    'gray-300': '#d1d5db',
    'gray-400': '#9ca3af',
    'gray-500': '#6b7280',
    'gray-600': '#4b5563',
    'gray-700': '#374151',
    'gray-800': '#1f2937',
    'gray-900': '#111827',
    'red-50': '#fef2f2',
    'red-100': '#fee2e2',
    'red-200': '#fecaca',
    'red-300': '#fca5a5',
    'red-400': '#f87171',
    'red-500': '#ef4444',
    'red-600': '#dc2626',
    'red-700': '#b91c1c',
    'red-800': '#991b1b',
    'red-900': '#7f1d1d',
    # Add more colors as needed...
}


@dataclass
class CSSProperties:
    """Represents computed CSS properties in pixels."""
    
    # Dimensions
    width: Optional[int] = None
    height: Optional[int] = None
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    
    # Padding (all in pixels)
    padding_top: int = 0
    padding_right: int = 0
    padding_bottom: int = 0
    padding_left: int = 0
    
    # Margin (all in pixels)
    margin_top: int = 0
    margin_right: int = 0
    margin_bottom: int = 0
    margin_left: int = 0
    
    # Border
    border_width: int = 0
    border_radius: int = 0
    
    # Flexbox
    display: str = 'block'  # block, flex, grid, inline, hidden
    flex_direction: str = 'row'  # row, column, row-reverse, column-reverse
    justify_content: str = 'flex-start'
    align_items: str = 'stretch'
    align_content: str = 'stretch'
    flex_wrap: str = 'nowrap'
    gap: int = 0
    
    # Flex item properties
    flex_grow: float = 0
    flex_shrink: float = 1
    flex_basis: Union[int, str] = 'auto'
    
    # Text
    font_size: int = 16
    line_height: float = 1.5
    text_align: str = 'left'  # left, center, right, justify
    text_color: str = '#000000'
    
    # Background
    background_color: str = 'transparent'
    
    # Position
    position: str = 'static'  # static, relative, absolute, fixed
    top: Optional[int] = None
    right: Optional[int] = None
    bottom: Optional[int] = None
    left: Optional[int] = None
    z_index: int = 0
    
    # Overflow
    overflow: str = 'visible'  # visible, hidden, scroll, auto
    overflow_x: str = 'visible'
    overflow_y: str = 'visible'
    
    @property
    def padding_x(self) -> int:
        """Horizontal padding."""
        return self.padding_left + self.padding_right
    
    @property
    def padding_y(self) -> int:
        """Vertical padding."""
        return self.padding_top + self.padding_bottom
    
    @property
    def margin_x(self) -> int:
        """Horizontal margin."""
        return self.margin_left + self.margin_right
    
    @property
    def margin_y(self) -> int:
        """Vertical margin."""
        return self.margin_top + self.margin_bottom


class TailwindParser:
    """Parse Tailwind CSS classes and convert to CSSProperties."""
    
    def __init__(self):
        self.properties = CSSProperties()
        self.responsive_properties: Dict[str, CSSProperties] = {}
    
    def parse_classes(self, classes: str) -> CSSProperties:
        """Parse a string of Tailwind classes.
        
        Args:
            classes: Space-separated Tailwind class names
            
        Returns:
            CSSProperties object with computed values
        """
        self.properties = CSSProperties()
        
        if not classes:
            return self.properties
        
        class_list = classes.split()
        
        for cls in class_list:
            self._parse_single_class(cls)
        
        return self.properties
    
    def _parse_single_class(self, cls: str) -> None:
        """Parse and apply a single Tailwind class."""
        
        # Handle responsive prefixes (sm:, md:, lg:, xl:, 2xl:)
        responsive = None
        for breakpoint in BREAKPOINTS.keys():
            if cls.startswith(f'{breakpoint}:'):
                responsive = breakpoint
                cls = cls[len(breakpoint) + 1:]
                break
        
        # Handle dark mode prefix (dark:)
        dark = False
        if cls.startswith('dark:'):
            dark = True
            cls = cls[5:]
        
        # Width utilities (w-*)
        if cls.startswith('w-'):
            self._parse_width(cls[2:])
        
        # Height utilities (h-*)
        elif cls.startswith('h-'):
            self._parse_height(cls[2:])
        
        # Min/Max width
        elif cls.startswith('min-w-'):
            self._parse_min_width(cls[6:])
        elif cls.startswith('max-w-'):
            self._parse_max_width(cls[6:])
        
        # Min/Max height
        elif cls.startswith('min-h-'):
            self._parse_min_height(cls[6:])
        elif cls.startswith('max-h-'):
            self._parse_max_height(cls[6:])
        
        # Padding (p-, pt-, pr-, pb-, pl-, px-, py-)
        elif cls.startswith('p-'):
            value = cls[2:]
            if value in SPACING_SCALE:
                px = SPACING_SCALE[value]
                self.properties.padding_top = px
                self.properties.padding_right = px
                self.properties.padding_bottom = px
                self.properties.padding_left = px
        elif cls.startswith('pt-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                self.properties.padding_top = SPACING_SCALE[value]
        elif cls.startswith('pr-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                self.properties.padding_right = SPACING_SCALE[value]
        elif cls.startswith('pb-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                self.properties.padding_bottom = SPACING_SCALE[value]
        elif cls.startswith('pl-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                self.properties.padding_left = SPACING_SCALE[value]
        elif cls.startswith('px-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                px = SPACING_SCALE[value]
                self.properties.padding_left = px
                self.properties.padding_right = px
        elif cls.startswith('py-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                px = SPACING_SCALE[value]
                self.properties.padding_top = px
                self.properties.padding_bottom = px
        
        # Margin (m-, mt-, mr-, mb-, ml-, mx-, my-)
        elif cls.startswith('m-'):
            value = cls[2:]
            if value in SPACING_SCALE:
                mx = SPACING_SCALE[value]
                self.properties.margin_top = mx
                self.properties.margin_right = mx
                self.properties.margin_bottom = mx
                self.properties.margin_left = mx
        elif cls.startswith('mt-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                self.properties.margin_top = SPACING_SCALE[value]
        elif cls.startswith('mr-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                self.properties.margin_right = SPACING_SCALE[value]
        elif cls.startswith('mb-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                self.properties.margin_bottom = SPACING_SCALE[value]
        elif cls.startswith('ml-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                self.properties.margin_left = SPACING_SCALE[value]
        elif cls.startswith('mx-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                mx = SPACING_SCALE[value]
                self.properties.margin_left = mx
                self.properties.margin_right = mx
        elif cls.startswith('my-'):
            value = cls[3:]
            if value in SPACING_SCALE:
                mx = SPACING_SCALE[value]
                self.properties.margin_top = mx
                self.properties.margin_bottom = mx
        
        # Flexbox
        elif cls == 'flex':
            self.properties.display = 'flex'
        elif cls == 'flex-row':
            self.properties.flex_direction = 'row'
        elif cls == 'flex-col':
            self.properties.flex_direction = 'column'
        elif cls == 'flex-row-reverse':
            self.properties.flex_direction = 'row-reverse'
        elif cls == 'flex-col-reverse':
            self.properties.flex_direction = 'column-reverse'
        elif cls == 'flex-wrap':
            self.properties.flex_wrap = 'wrap'
        elif cls == 'flex-nowrap':
            self.properties.flex_wrap = 'nowrap'
        elif cls == 'flex-grow':
            self.properties.flex_grow = 1
        elif cls.startswith('flex-grow-'):
            value = cls[10:]
            try:
                self.properties.flex_grow = float(value)
            except ValueError:
                pass
        elif cls == 'flex-shrink':
            self.properties.flex_shrink = 1
        elif cls.startswith('flex-shrink-'):
            value = cls[12:]
            try:
                self.properties.flex_shrink = float(value)
            except ValueError:
                pass
        
        # Justify content
        elif cls == 'justify-start':
            self.properties.justify_content = 'flex-start'
        elif cls == 'justify-end':
            self.properties.justify_content = 'flex-end'
        elif cls == 'justify-center':
            self.properties.justify_content = 'center'
        elif cls == 'justify-between':
            self.properties.justify_content = 'space-between'
        elif cls == 'justify-around':
            self.properties.justify_content = 'space-around'
        elif cls == 'justify-evenly':
            self.properties.justify_content = 'space-evenly'
        
        # Align items
        elif cls == 'items-start':
            self.properties.align_items = 'flex-start'
        elif cls == 'items-end':
            self.properties.align_items = 'flex-end'
        elif cls == 'items-center':
            self.properties.align_items = 'center'
        elif cls == 'items-baseline':
            self.properties.align_items = 'baseline'
        elif cls == 'items-stretch':
            self.properties.align_items = 'stretch'
        
        # Gap
        elif cls.startswith('gap-'):
            value = cls[4:]
            if value in SPACING_SCALE:
                self.properties.gap = SPACING_SCALE[value]
        elif cls.startswith('gap-x-'):
            # Note: gap-x and gap-y not fully implemented yet
            pass
        elif cls.startswith('gap-y-'):
            pass
        
        # Text utilities
        elif cls.startswith('text-'):
            self._parse_text_class(cls[5:])
        
        # Background color
        elif cls.startswith('bg-'):
            color_name = cls[3:]
            if color_name in COLORS:
                self.properties.background_color = COLORS[color_name]
        
        # Border radius
        elif cls.startswith('rounded'):
            self._parse_rounded(cls[7:])
        
        # Display
        elif cls == 'hidden':
            self.properties.display = 'none'
        elif cls == 'block':
            self.properties.display = 'block'
        elif cls == 'inline':
            self.properties.display = 'inline'
        elif cls == 'inline-block':
            self.properties.display = 'inline-block'
        
        # Overflow
        elif cls == 'overflow-hidden':
            self.properties.overflow = 'hidden'
        elif cls == 'overflow-auto':
            self.properties.overflow = 'auto'
        elif cls == 'overflow-scroll':
            self.properties.overflow = 'scroll'
    
    def _parse_width(self, value: str) -> None:
        """Parse w-* class."""
        if value == 'full':
            self.properties.width = None  # 100%, computed at render time
        elif value == 'screen':
            self.properties.width = None  # 100vw
        elif value in SPACING_SCALE:
            self.properties.width = SPACING_SCALE[value]
        elif '/' in value:  # Fractions like 1/2, 2/3, etc.
            parts = value.split('/')
            if len(parts) == 2:
                try:
                    num, denom = int(parts[0]), int(parts[1])
                    # Store as fraction, compute at render time
                    self.properties.width = None
                except ValueError:
                    pass
    
    def _parse_height(self, value: str) -> None:
        """Parse h-* class."""
        if value == 'full':
            self.properties.height = None
        elif value == 'screen':
            self.properties.height = None
        elif value in SPACING_SCALE:
            self.properties.height = SPACING_SCALE[value]
    
    def _parse_min_width(self, value: str) -> None:
        """Parse min-w-* class."""
        if value == 'full':
            self.properties.min_width = None
        elif value in SPACING_SCALE:
            self.properties.min_width = SPACING_SCALE[value]
    
    def _parse_max_width(self, value: str) -> None:
        """Parse max-w-* class."""
        max_widths = {
            'xs': 320,
            'sm': 384,
            'md': 448,
            'lg': 512,
            'xl': 576,
            '2xl': 672,
            '3xl': 768,
            '4xl': 896,
            '5xl': 1024,
            '6xl': 1152,
            '7xl': 1280,
            'full': None,
            'screen': None,
        }
        if value in max_widths:
            self.properties.max_width = max_widths[value]
    
    def _parse_min_height(self, value: str) -> None:
        """Parse min-h-* class."""
        if value == 'full':
            self.properties.min_height = None
        elif value in SPACING_SCALE:
            self.properties.min_height = SPACING_SCALE[value]
    
    def _parse_max_height(self, value: str) -> None:
        """Parse max-h-* class."""
        if value == 'full':
            self.properties.max_height = None
        elif value in SPACING_SCALE:
            self.properties.max_height = SPACING_SCALE[value]
    
    def _parse_text_class(self, value: str) -> None:
        """Parse text-* class (size, color, etc.)."""
        if value in FONT_SIZES:
            self.properties.font_size = FONT_SIZES[value]
        elif value in COLORS:
            self.properties.text_color = COLORS[value]
        elif value == 'left':
            self.properties.text_align = 'left'
        elif value == 'center':
            self.properties.text_align = 'center'
        elif value == 'right':
            self.properties.text_align = 'right'
        elif value == 'justify':
            self.properties.text_align = 'justify'
        elif value == 'bold':
            # Font weight - would need separate handling
            pass
    
    def _parse_rounded(self, value: str) -> None:
        """Parse rounded-* class."""
        if not value or value == '':
            self.properties.border_radius = BORDER_RADIUS.get('base', 4)
        elif value in BORDER_RADIUS:
            self.properties.border_radius = BORDER_RADIUS[value]


# Global parser instance
_parser = TailwindParser()


def parse_tailwind_classes(classes: str) -> CSSProperties:
    """Parse Tailwind classes and return computed CSS properties."""
    return _parser.parse_classes(classes)
