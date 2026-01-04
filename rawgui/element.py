"""Base Element class for all RawGUI UI elements.

Provides the foundation for context-based element creation, styling,
and the element tree structure.
"""

from __future__ import annotations

import itertools
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Self,
    Union,
)

from .context import context
from .slot import Slot

if TYPE_CHECKING:
    from .client import Client

# Global element ID counter
_element_id_counter = itertools.count(1)


def _next_element_id() -> int:
    """Generate the next unique element ID."""
    return next(_element_id_counter)


class Element:
    """Base class for all RawGUI UI elements.

    Elements are the building blocks of the UI. They can contain other elements
    through slots, and support styling via classes and inline styles.

    Example:
        with ui.column():
            ui.label('Hello').classes('text-bold')
            with ui.row():
                ui.button('Click').style('color: red')
    """

    # Class-level defaults that can be overridden by subclasses
    _default_classes: List[str] = []
    _default_style: Dict[str, str] = {}
    _default_props: Dict[str, Any] = {}

    def __init__(
        self,
        tag: Optional[str] = None,
        *,
        _client: Optional["Client"] = None,
    ) -> None:
        """Initialize an element.

        Args:
            tag: The element tag/type name (for rendering)
            _client: Optional explicit client (defaults to current context)
        """
        self.id = _next_element_id()
        self.tag = tag or self.__class__.__name__.lower()

        # Get client from context or explicit parameter
        self.client = _client or context.client

        # Slot management
        self.slots: Dict[str, Slot] = {}
        self.default_slot = self.add_slot("default")
        self.parent_slot: Optional[Slot] = None

        # Styling
        self._classes: List[str] = list(self._default_classes)
        self._style: Dict[str, str] = dict(self._default_style)
        self._props: Dict[str, Any] = dict(self._default_props)

        # Visibility
        self._visible = True

        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}

        # Register with parent slot if in a context
        current_slot = context.slot
        if current_slot is not None:
            current_slot.add_child(self)

        # Register with client
        if self.client is not None:
            self.client.register_element(self)

    def add_slot(self, name: str) -> Slot:
        """Add a named slot to this element.

        Args:
            name: The slot name

        Returns:
            The created slot
        """
        slot = Slot(self, name)
        self.slots[name] = slot
        return slot

    def __enter__(self) -> Self:
        """Enter the element's default slot context."""
        self.default_slot.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the element's default slot context."""
        self.default_slot.__exit__(exc_type, exc_val, exc_tb)

    # -------------------------------------------------------------------------
    # Styling methods (NiceGUI-compatible API)
    # -------------------------------------------------------------------------

    def classes(
        self,
        add: Optional[str] = None,
        *,
        remove: Optional[str] = None,
        replace: Optional[str] = None,
    ) -> Self:
        """Modify the element's CSS classes.

        Args:
            add: Space-separated classes to add
            remove: Space-separated classes to remove
            replace: Replace all classes with these

        Returns:
            Self for method chaining
        """
        if replace is not None:
            self._classes = replace.split() if replace else []
        if remove:
            for cls in remove.split():
                if cls in self._classes:
                    self._classes.remove(cls)
        if add:
            for cls in add.split():
                if cls not in self._classes:
                    self._classes.append(cls)
        return self

    def style(
        self,
        add: Optional[str] = None,
        *,
        remove: Optional[str] = None,
        replace: Optional[str] = None,
    ) -> Self:
        """Modify the element's inline styles.

        Args:
            add: CSS style string to add (e.g., "color: red; font-size: 14px")
            remove: Style properties to remove (e.g., "color font-size")
            replace: Replace all styles with this string

        Returns:
            Self for method chaining
        """
        if replace is not None:
            self._style = self._parse_style(replace)
        if remove:
            for prop in remove.split():
                self._style.pop(prop.rstrip(";"), None)
        if add:
            self._style.update(self._parse_style(add))
        return self

    def props(
        self,
        add: Optional[str] = None,
        *,
        remove: Optional[str] = None,
        replace: Optional[str] = None,
    ) -> Self:
        """Modify the element's properties.

        Args:
            add: Properties to add (e.g., "outlined flat" or "label=Click")
            remove: Properties to remove
            replace: Replace all properties

        Returns:
            Self for method chaining
        """
        if replace is not None:
            self._props = self._parse_props(replace)
        if remove:
            for prop in remove.split():
                self._props.pop(prop.split("=")[0], None)
        if add:
            self._props.update(self._parse_props(add))
        return self

    @staticmethod
    def _parse_style(style_str: str) -> Dict[str, str]:
        """Parse a CSS style string into a dictionary."""
        result = {}
        if not style_str:
            return result
        for part in style_str.split(";"):
            part = part.strip()
            if ":" in part:
                key, value = part.split(":", 1)
                result[key.strip()] = value.strip()
        return result

    @staticmethod
    def _parse_props(props_str: str) -> Dict[str, Any]:
        """Parse a props string into a dictionary."""
        result = {}
        if not props_str:
            return result
        for part in props_str.split():
            if "=" in part:
                key, value = part.split("=", 1)
                # Remove quotes if present
                value = value.strip("\"'")
                result[key] = value
            else:
                # Boolean property
                result[part] = True
        return result

    # -------------------------------------------------------------------------
    # Visibility
    # -------------------------------------------------------------------------

    def set_visibility(self, visible: bool) -> Self:
        """Set the element's visibility.

        Args:
            visible: Whether the element should be visible

        Returns:
            Self for method chaining
        """
        self._visible = visible
        return self

    @property
    def visible(self) -> bool:
        """Whether the element is visible."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    # -------------------------------------------------------------------------
    # Event handling
    # -------------------------------------------------------------------------

    def on(
        self,
        event: str,
        handler: Callable,
        args: Optional[List[str]] = None,
    ) -> Self:
        """Register an event handler.

        Args:
            event: The event name (e.g., 'click', 'change')
            handler: The callback function
            args: Optional list of argument names to pass

        Returns:
            Self for method chaining
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
        return self

    def _fire_event(self, event: str, *args, **kwargs) -> None:
        """Fire an event, calling all registered handlers."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            handler(*args, **kwargs)

    # -------------------------------------------------------------------------
    # Tree operations
    # -------------------------------------------------------------------------

    @property
    def parent(self) -> Optional["Element"]:
        """Get the parent element (via parent slot)."""
        return self.parent_slot.parent if self.parent_slot else None

    @property
    def children(self) -> List["Element"]:
        """Get all children from the default slot."""
        return self.default_slot.children

    def clear(self) -> None:
        """Remove all children from this element."""
        self.default_slot.clear()

    def move(self, target: Union["Element", Slot]) -> Self:
        """Move this element to a new parent.

        Args:
            target: The target element or slot

        Returns:
            Self for method chaining
        """
        # Remove from current parent
        if self.parent_slot:
            self.parent_slot.remove_child(self)

        # Add to new parent
        if isinstance(target, Slot):
            target.add_child(self)
        else:
            target.default_slot.add_child(self)

        return self

    def delete(self) -> None:
        """Delete this element and all its children."""
        # Remove from parent
        if self.parent_slot:
            self.parent_slot.remove_child(self)

        # Delete all children
        for slot in self.slots.values():
            slot.clear()

        # Unregister from client
        if self.client:
            self.client.unregister_element(self)

    def remove(self, element: "Element") -> None:
        """Remove a child element.

        Args:
            element: The element to remove
        """
        self.default_slot.remove_child(element)

    # -------------------------------------------------------------------------
    # Rendering support
    # -------------------------------------------------------------------------

    def get_classes_string(self) -> str:
        """Get classes as a space-separated string."""
        return " ".join(self._classes)

    def get_style_string(self) -> str:
        """Get styles as a CSS string."""
        return "; ".join(f"{k}: {v}" for k, v in self._style.items())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, tag={self.tag!r})"
