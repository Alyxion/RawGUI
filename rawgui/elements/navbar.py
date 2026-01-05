"""Navigation bar element for browser-like navigation."""

from __future__ import annotations

from typing import Callable, Optional

from ..element import Element


class NavigationBar(Element):
    """A browser-like navigation bar with back/forward buttons.

    Provides navigation controls and displays current URL.

    Example:
        ui.navigation_bar()  # Shows at top of page
    """

    _default_classes = ["navbar", "border", "p-1"]

    def __init__(
        self,
        *,
        show_url: bool = True,
        on_back: Optional[Callable] = None,
        on_forward: Optional[Callable] = None,
    ) -> None:
        """Initialize the navigation bar.

        Args:
            show_url: Whether to show the current URL
            on_back: Callback for back navigation
            on_forward: Callback for forward navigation
        """
        super().__init__(tag="navbar")

        self.show_url = show_url
        self._on_back = on_back
        self._on_forward = on_forward

        # Navigation state (updated by renderer)
        self.can_go_back = False
        self.can_go_forward = False
        self.current_url = "/"

    def on_back(self, handler: Callable) -> "NavigationBar":
        """Register a back navigation handler.

        Args:
            handler: The callback

        Returns:
            Self for method chaining
        """
        self._on_back = handler
        return self

    def on_forward(self, handler: Callable) -> "NavigationBar":
        """Register a forward navigation handler.

        Args:
            handler: The callback

        Returns:
            Self for method chaining
        """
        self._on_forward = handler
        return self

    def go_back(self) -> None:
        """Trigger back navigation."""
        if self._on_back and self.can_go_back:
            self._on_back()

    def go_forward(self) -> None:
        """Trigger forward navigation."""
        if self._on_forward and self.can_go_forward:
            self._on_forward()

    def __repr__(self) -> str:
        return f"NavigationBar(id={self.id}, url={self.current_url!r})"
