"""Base adapter interface for RawGUI renderers.

All rendering adapters must implement this interface to ensure
consistent behavior across different backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, List, Callable

if TYPE_CHECKING:
    from ..element import Element


class BaseAdapter(ABC):
    """Abstract base class for rendering adapters.

    Provides a common interface for:
    - Rendering element trees
    - Focus management
    - Mouse/keyboard input handling
    - Hit testing
    """

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._focusable: List["Element"] = []
        self._focus_index: int = -1
        self._focused: Optional["Element"] = None
        self._hovered: Optional["Element"] = None
        self._edit_mode: bool = False
        self._dirty: bool = True

    @abstractmethod
    def render(self, root: "Element") -> None:
        """Render the element tree.

        Args:
            root: Root element of the tree to render
        """
        pass

    @abstractmethod
    def run(self, on_close: Optional[Callable] = None) -> None:
        """Run the main event loop.

        Args:
            on_close: Callback when window/app closes
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the main event loop."""
        pass

    def invalidate(self) -> None:
        """Mark the display as needing re-render."""
        self._dirty = True

    @property
    def needs_render(self) -> bool:
        """Check if re-render is needed."""
        return self._dirty

    @property
    def focused(self) -> Optional["Element"]:
        """Get currently focused element."""
        return self._focused

    @property
    def focus_index(self) -> int:
        """Get current focus index."""
        return self._focus_index

    @property
    def edit_mode(self) -> bool:
        """Check if in edit mode (full keyboard capture)."""
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

    def schedule_focus_restore(self, index: int) -> None:
        """Schedule focus restoration after next render."""
        self._pending_focus_index = index

    def set_hover(self, element: Optional["Element"]) -> None:
        """Set hovered element."""
        if self._hovered != element:
            self._hovered = element
            self._dirty = True

    @abstractmethod
    def get_element_at(self, x: int, y: int) -> Optional["Element"]:
        """Get element at screen coordinates.

        Args:
            x: X coordinate (pixels)
            y: Y coordinate (pixels)

        Returns:
            Element at position or None
        """
        pass

    def _is_focusable(self, element: "Element") -> bool:
        """Check if element can receive focus."""
        focusable_tags = ("button", "input", "checkbox", "select", "textarea", "toggle", "slider")
        if element.tag not in focusable_tags:
            return False
        if not getattr(element, "enabled", True):
            return False
        if not getattr(element, "visible", True):
            return False
        return True
