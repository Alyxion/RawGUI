"""Task-local context management for RawGUI.

Provides context variables for tracking the current client and slot stack,
similar to NiceGUI's context management system.
"""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .client import Client
    from .slot import Slot

# Task-local context variables
_current_client: ContextVar[Optional["Client"]] = ContextVar("current_client", default=None)
_slot_stack: ContextVar[list["Slot"]] = ContextVar("slot_stack", default=[])


class Context:
    """Context accessor for current client and slot stack.

    This mimics NiceGUI's context system where elements automatically
    detect which client and slot they belong to based on the current
    execution context.
    """

    @property
    def client(self) -> Optional["Client"]:
        """Get the current client for this context."""
        return _current_client.get()

    @client.setter
    def client(self, value: Optional["Client"]) -> None:
        """Set the current client for this context."""
        _current_client.set(value)

    @property
    def slot_stack(self) -> list["Slot"]:
        """Get the current slot stack for element nesting."""
        stack = _slot_stack.get()
        if stack is None:
            stack = []
            _slot_stack.set(stack)
        return stack

    @property
    def slot(self) -> Optional["Slot"]:
        """Get the current (topmost) slot from the stack."""
        stack = self.slot_stack
        return stack[-1] if stack else None

    def push_slot(self, slot: "Slot") -> None:
        """Push a slot onto the stack."""
        self.slot_stack.append(slot)

    def pop_slot(self) -> Optional["Slot"]:
        """Pop and return the topmost slot from the stack."""
        stack = self.slot_stack
        return stack.pop() if stack else None

    def get_task_id(self) -> int:
        """Get the current asyncio task ID or thread ID."""
        try:
            task = asyncio.current_task()
            return id(task) if task else id(asyncio.get_event_loop())
        except RuntimeError:
            import threading
            return threading.current_thread().ident or 0


# Global context instance
context = Context()
