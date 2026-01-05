"""Application singleton for RawGUI.

Manages global application state, storage, and lifecycle hooks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class AppConfig:
    """Application configuration."""

    title: str = "RawGUI"
    dark: Optional[bool] = None
    reload: bool = True
    binding_refresh_interval: float = 0.1


@dataclass
class Storage:
    """Multi-level storage system mimicking NiceGUI's storage."""

    # Per-client storage (session-based)
    client: Dict[str, Any] = field(default_factory=dict)

    # Per-user storage (would be persistent in real implementation)
    user: Dict[str, Any] = field(default_factory=dict)

    # Application-wide storage
    general: Dict[str, Any] = field(default_factory=dict)

    # Browser-like storage (terminal session)
    browser: Dict[str, Any] = field(default_factory=dict)


class App:
    """Application singleton managing global state.

    Provides:
    - Configuration
    - Storage (client, user, general, browser scopes)
    - Lifecycle hooks (startup, shutdown, connect, disconnect)
    - Auto-index client for implicit root page
    """

    _instance: Optional["App"] = None

    def __init__(self) -> None:
        """Initialize the application."""
        self.config = AppConfig()
        self.storage = Storage()

        # Lifecycle hooks
        self._startup_handlers: List[Callable] = []
        self._shutdown_handlers: List[Callable] = []
        self._connect_handlers: List[Callable] = []
        self._disconnect_handlers: List[Callable] = []
        self._exception_handlers: List[Callable] = []

        # Running state
        self._running = False

        # Auto-index client for elements created at module scope
        # (NiceGUI's implicit root page behavior)
        self._auto_index_client: Optional[Any] = None

        # Pending navigation path (set by ui.navigate.to, consumed by run loop)
        self._pending_navigation: Optional[str] = None

    @classmethod
    def instance(cls) -> "App":
        """Get the singleton application instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the application singleton (for testing)."""
        cls._instance = None

    # -------------------------------------------------------------------------
    # Lifecycle decorators
    # -------------------------------------------------------------------------

    def on_startup(self, func: Callable) -> Callable:
        """Register a startup handler.

        Args:
            func: The handler function

        Returns:
            The handler function (for decorator use)
        """
        self._startup_handlers.append(func)
        return func

    def on_shutdown(self, func: Callable) -> Callable:
        """Register a shutdown handler.

        Args:
            func: The handler function

        Returns:
            The handler function (for decorator use)
        """
        self._shutdown_handlers.append(func)
        return func

    def on_connect(self, func: Callable) -> Callable:
        """Register a connect handler.

        Args:
            func: The handler function

        Returns:
            The handler function (for decorator use)
        """
        self._connect_handlers.append(func)
        return func

    def on_disconnect(self, func: Callable) -> Callable:
        """Register a disconnect handler.

        Args:
            func: The handler function

        Returns:
            The handler function (for decorator use)
        """
        self._disconnect_handlers.append(func)
        return func

    def on_exception(self, func: Callable) -> Callable:
        """Register an exception handler.

        Args:
            func: The handler function

        Returns:
            The handler function (for decorator use)
        """
        self._exception_handlers.append(func)
        return func

    # -------------------------------------------------------------------------
    # Lifecycle execution
    # -------------------------------------------------------------------------

    async def _run_startup(self) -> None:
        """Run all startup handlers."""
        for handler in self._startup_handlers:
            result = handler()
            if hasattr(result, "__await__"):
                await result

    async def _run_shutdown(self) -> None:
        """Run all shutdown handlers."""
        for handler in self._shutdown_handlers:
            result = handler()
            if hasattr(result, "__await__"):
                await result

    def _run_connect(self, client) -> None:
        """Run all connect handlers for a client."""
        for handler in self._connect_handlers:
            handler(client)

    def _run_disconnect(self, client) -> None:
        """Run all disconnect handlers for a client."""
        for handler in self._disconnect_handlers:
            handler(client)

    def _run_exception(self, exception: Exception) -> bool:
        """Run exception handlers.

        Returns:
            True if the exception was handled
        """
        handled = False
        for handler in self._exception_handlers:
            try:
                handler(exception)
                handled = True
            except Exception:
                pass
        return handled

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def title(self) -> str:
        """Get the application title."""
        return self.config.title

    @title.setter
    def title(self, value: str) -> None:
        """Set the application title."""
        self.config.title = value

    @property
    def is_running(self) -> bool:
        """Check if the application is running."""
        return self._running

    def __repr__(self) -> str:
        return f"App(title={self.config.title!r}, running={self._running})"


# Global app instance shortcut
app = App.instance()
