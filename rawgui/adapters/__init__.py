"""Rendering adapters for RawGUI.

Supports multiple rendering backends:
- TUI (Terminal) - Primary, uses blessed
- Tkinter - GUI fallback, uses Pillow for rendering
"""

from .base import BaseAdapter
from .tkinter_adapter import TkinterAdapter

__all__ = ["BaseAdapter", "TkinterAdapter"]
