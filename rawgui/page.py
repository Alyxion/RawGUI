"""Page decorator and routing for RawGUI.

Implements the @ui.page decorator for defining routes.
"""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Pattern

from .client import Client


@dataclass
class PageConfig:
    """Configuration for a page."""

    path: str
    title: Optional[str] = None
    dark: Optional[bool] = None
    viewport: Optional[str] = None
    favicon: Optional[str] = None
    response_timeout: float = 3.0


class PageRoute:
    """Represents a registered page route."""

    def __init__(
        self,
        path: str,
        builder: Callable,
        config: PageConfig,
    ) -> None:
        """Initialize a page route.

        Args:
            path: The URL path pattern (e.g., '/user/{user_id}')
            builder: The page builder function
            config: Page configuration
        """
        self.path = path
        self.builder = builder
        self.config = config

        # Parse path parameters
        self.param_names: List[str] = re.findall(r"\{(\w+)\}", path)

        # Create regex pattern for matching
        pattern = path
        for name in self.param_names:
            pattern = pattern.replace(f"{{{name}}}", f"(?P<{name}>[^/]+)")
        self._pattern: Pattern = re.compile(f"^{pattern}$")

    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Try to match a path against this route.

        Args:
            path: The path to match

        Returns:
            Dictionary of path parameters if matched, None otherwise
        """
        match = self._pattern.match(path)
        if match:
            return match.groupdict()
        return None

    async def build(self, client: Client, params: Dict[str, str]) -> None:
        """Build the page for a client.

        Args:
            client: The client to build for
            params: Path parameters
        """
        # Get the builder's signature
        sig = inspect.signature(self.builder)
        kwargs = {}

        # Add path parameters
        for name in self.param_names:
            if name in sig.parameters:
                kwargs[name] = params.get(name, "")

        # Add client if requested
        if "client" in sig.parameters:
            kwargs["client"] = client

        # Build the page within the client context
        with client:
            result = self.builder(**kwargs)
            if inspect.iscoroutine(result):
                await result


class Router:
    """URL router for page navigation."""

    def __init__(self) -> None:
        """Initialize the router."""
        self.routes: List[PageRoute] = []
        self._default_route: Optional[PageRoute] = None

    def add_route(self, route: PageRoute) -> None:
        """Add a route to the router.

        Args:
            route: The route to add
        """
        self.routes.append(route)

        # Set default route for root path
        if route.path == "/":
            self._default_route = route

    def match(self, path: str) -> Optional[tuple[PageRoute, Dict[str, str]]]:
        """Find a route matching the given path.

        Args:
            path: The path to match

        Returns:
            Tuple of (route, params) if matched, None otherwise
        """
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                return route, params
        return None

    def get_route(self, path: str) -> Optional[PageRoute]:
        """Get the route for a path (without params).

        Args:
            path: The path pattern

        Returns:
            The route or None
        """
        for route in self.routes:
            if route.path == path:
                return route
        return None


# Global router instance
router = Router()


class page:
    """Decorator for defining page routes.

    Usage:
        @ui.page('/')
        def index():
            ui.label('Welcome!')

        @ui.page('/user/{user_id}')
        def user_page(user_id: str):
            ui.label(f'User: {user_id}')
    """

    def __init__(
        self,
        path: str,
        *,
        title: Optional[str] = None,
        dark: Optional[bool] = None,
        viewport: Optional[str] = None,
        favicon: Optional[str] = None,
        response_timeout: float = 3.0,
    ) -> None:
        """Initialize the page decorator.

        Args:
            path: The URL path (must start with '/')
            title: Page title (defaults to app title)
            dark: Dark mode setting
            viewport: Viewport meta tag
            favicon: Favicon path
            response_timeout: Max time to build page
        """
        if not path.startswith("/"):
            raise ValueError(f"Page path must start with '/': {path}")

        self.config = PageConfig(
            path=path,
            title=title,
            dark=dark,
            viewport=viewport,
            favicon=favicon,
            response_timeout=response_timeout,
        )

    def __call__(self, func: Callable) -> Callable:
        """Decorate a function as a page builder.

        Args:
            func: The page builder function

        Returns:
            The decorated function
        """
        # Create and register the route
        route = PageRoute(self.config.path, func, self.config)
        router.add_route(route)

        # Register with Client class for lookup
        Client.page_routes[func] = self.config.path
        Client.page_configs[func] = self.config

        return func


class Navigate:
    """Navigation helper for page navigation."""

    def to(self, path: str) -> None:
        """Navigate to a path.

        Args:
            path: The path to navigate to
        """
        from .app import app

        # Set pending navigation - the run loop will pick this up
        app._pending_navigation = path

    def back(self) -> None:
        """Navigate back in history."""
        from .context import context

        client = context.client
        if client:
            client.navigate_back()

    def forward(self) -> None:
        """Navigate forward in history."""
        from .context import context

        client = context.client
        if client:
            client.navigate_forward()


# Global navigation helper
navigate = Navigate()
