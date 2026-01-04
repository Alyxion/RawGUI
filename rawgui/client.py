"""Client management for RawGUI.

Each terminal session has a Client that manages the element tree,
navigation state, and event handling.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from .context import context

if TYPE_CHECKING:
    from .element import Element
    from .page import PageConfig


class Client:
    """Represents a terminal session/client.

    The Client manages:
    - The element tree for the current view
    - Navigation history
    - Element registry for quick lookup
    - Storage (session-based)
    """

    # Class-level registry of all clients
    instances: Dict[str, "Client"] = {}

    # Page route registry (decorated functions -> paths)
    page_routes: Dict[Callable, str] = {}
    page_configs: Dict[Callable, "PageConfig"] = {}

    def __init__(self, client_id: Optional[str] = None) -> None:
        """Initialize a new client.

        Args:
            client_id: Optional explicit client ID
        """
        self.id = client_id or str(uuid.uuid4())

        # Element registry
        self._elements: Dict[int, "Element"] = {}

        # Root content element (set during page build)
        self.content: Optional["Element"] = None

        # Navigation state
        self.current_path: str = "/"
        self.history: List[str] = []
        self.history_index: int = -1

        # Session storage
        self.storage: Dict[str, any] = {}

        # Event handlers
        self.connect_handlers: List[Callable] = []
        self.disconnect_handlers: List[Callable] = []

        # Register this client
        Client.instances[self.id] = self

    def __enter__(self) -> "Client":
        """Enter the client context for building UI."""
        context.client = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the client context."""
        context.client = None

    def register_element(self, element: "Element") -> None:
        """Register an element with this client.

        Args:
            element: The element to register
        """
        self._elements[element.id] = element

    def unregister_element(self, element: "Element") -> None:
        """Unregister an element from this client.

        Args:
            element: The element to unregister
        """
        self._elements.pop(element.id, None)

    def get_element(self, element_id: int) -> Optional["Element"]:
        """Get an element by ID.

        Args:
            element_id: The element ID

        Returns:
            The element or None if not found
        """
        return self._elements.get(element_id)

    @property
    def elements(self) -> Dict[int, "Element"]:
        """Get all registered elements."""
        return self._elements

    def navigate_to(self, path: str) -> None:
        """Navigate to a new path.

        Args:
            path: The path to navigate to
        """
        # Add current path to history
        if self.current_path != path:
            # Truncate forward history if we navigated back
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]

            self.history.append(self.current_path)
            self.history_index = len(self.history) - 1
            self.current_path = path

    def navigate_back(self) -> Optional[str]:
        """Navigate back in history.

        Returns:
            The previous path or None if at the beginning
        """
        if self.history_index > 0:
            self.history_index -= 1
            self.current_path = self.history[self.history_index]
            return self.current_path
        return None

    def navigate_forward(self) -> Optional[str]:
        """Navigate forward in history.

        Returns:
            The next path or None if at the end
        """
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_path = self.history[self.history_index]
            return self.current_path
        return None

    def clear(self) -> None:
        """Clear all elements from this client."""
        for element in list(self._elements.values()):
            element.delete()
        self._elements.clear()
        self.content = None

    def close(self) -> None:
        """Close and cleanup this client."""
        self.clear()
        Client.instances.pop(self.id, None)

        # Fire disconnect handlers
        for handler in self.disconnect_handlers:
            handler()

    def __repr__(self) -> str:
        return f"Client(id={self.id!r}, path={self.current_path!r}, elements={len(self._elements)})"
