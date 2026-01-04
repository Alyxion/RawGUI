"""Slot implementation for element nesting.

Slots are containers that hold child elements and manage the context
stack for the `with` statement pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .context import context

if TYPE_CHECKING:
    from .element import Element


class Slot:
    """A slot that can contain child elements.

    Slots are used to implement the context manager pattern for element nesting.
    When entering a slot with `with`, all elements created inside become children
    of that slot's parent element.

    Example:
        with ui.row() as row:  # Enters row's default slot
            ui.label('Hello')  # Added as child of row
            ui.button('Click') # Added as child of row
    """

    def __init__(self, parent: "Element", name: str = "default") -> None:
        """Initialize a slot.

        Args:
            parent: The element that owns this slot
            name: The slot name (default is "default")
        """
        self.parent = parent
        self.name = name
        self.children: List["Element"] = []

    def __enter__(self) -> "Slot":
        """Enter the slot context, pushing onto the stack."""
        context.push_slot(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the slot context, popping from the stack."""
        context.pop_slot()

    def add_child(self, element: "Element") -> None:
        """Add an element as a child of this slot.

        Args:
            element: The element to add
        """
        self.children.append(element)
        element.parent_slot = self

    def remove_child(self, element: "Element") -> None:
        """Remove an element from this slot.

        Args:
            element: The element to remove
        """
        if element in self.children:
            self.children.remove(element)
            element.parent_slot = None

    def clear(self) -> None:
        """Remove all children from this slot."""
        for child in self.children[:]:
            child.delete()
        self.children.clear()

    def __repr__(self) -> str:
        return f"Slot({self.name!r}, parent={self.parent.__class__.__name__}, children={len(self.children)})"
