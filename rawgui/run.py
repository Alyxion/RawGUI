"""Main run loop for RawGUI applications.

Fully functional terminal application with:
- Keyboard input handling
- Mouse support (clicks, hover)
- Focus management
- Auto-reload on file changes
"""

from __future__ import annotations

import asyncio
import sys
import os
import traceback
from pathlib import Path
from typing import Callable, List, Optional, TYPE_CHECKING

from blessed import Terminal

from .app import App, app
from .client import Client
from .context import context
from .element import Element
from .page import router
from .renderer.terminal import TerminalRenderer

if TYPE_CHECKING:
    pass


class RawGUIApp:
    """Main application runner with full interactivity.

    Handles:
    - Terminal rendering with blessed
    - Keyboard input (Tab, arrows, Enter, typing)
    - Mouse clicks and hover
    - Page routing
    - Auto-reload on file changes
    """

    def __init__(
        self,
        title: str = "RawGUI",
        reload: bool = True,
        dark: Optional[bool] = None,
    ) -> None:
        self.title = title
        self.reload = reload
        self.dark = dark

        self.term = Terminal()
        self.renderer = TerminalRenderer()
        self.client: Optional[Client] = None

        self._running = False
        self._root_element: Optional[Element] = None

        # Input state
        self._last_mouse_pos = (0, 0)

    def run(self) -> None:
        """Run the application (blocking)."""
        try:
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    async def _async_run(self) -> None:
        """Async main loop."""
        self._running = True

        # Configure app
        app.config.title = self.title
        app.config.reload = self.reload
        app._running = True

        # Create client
        self.client = Client()

        # Run startup handlers
        await app._run_startup()
        app._run_connect(self.client)

        # Build initial page
        await self._navigate("/")

        # Main loop with fullscreen and input handling
        with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
            # Enable mouse reporting
            print(self.term.enter_mouse_tracking, end="", flush=True)

            try:
                # Start file watcher if reload enabled
                reload_task = None
                if self.reload:
                    reload_task = asyncio.create_task(self._watch_files())

                # Main input loop
                while self._running:
                    # Render if needed
                    if self.renderer.needs_render and self._root_element:
                        output = self.renderer.render(self._root_element)
                        print(output, end="", flush=True)

                    # Handle input with timeout
                    key = await self._read_key(timeout=0.05)
                    if key:
                        await self._handle_input(key)

                if reload_task:
                    reload_task.cancel()
                    try:
                        await reload_task
                    except asyncio.CancelledError:
                        pass

            finally:
                # Disable mouse tracking
                print(self.term.exit_mouse_tracking, end="", flush=True)

        # Cleanup
        await app._run_shutdown()
        if self.client:
            app._run_disconnect(self.client)
            self.client.close()

    async def _read_key(self, timeout: float = 0.1):
        """Read a key with timeout (non-blocking)."""
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self.term.inkey(timeout=timeout)),
                timeout=timeout + 0.1
            )
        except asyncio.TimeoutError:
            return None

    async def _handle_input(self, key) -> None:
        """Handle keyboard and mouse input."""
        # Check for quit
        if key == chr(3) or key == chr(17):  # Ctrl+C or Ctrl+Q
            self._running = False
            return

        if key == chr(27):  # Escape
            self._running = False
            return

        # Mouse events
        if hasattr(key, 'is_mouse') or (hasattr(key, 'code') and key.code and 'mouse' in str(key.code).lower()):
            await self._handle_mouse(key)
            return

        # Tab navigation
        if key.name == "KEY_TAB":
            self.renderer.focus_next()
            return

        if key.name == "KEY_BTAB":  # Shift+Tab
            self.renderer.focus_prev()
            return

        # Arrow keys for scrolling
        if key.name == "KEY_UP":
            focused = self.renderer.focused
            if not focused or focused.tag != "input":
                self.renderer.scroll(dy=-1)
            return

        if key.name == "KEY_DOWN":
            focused = self.renderer.focused
            if not focused or focused.tag != "input":
                self.renderer.scroll(dy=1)
            return

        if key.name == "KEY_PGUP":
            self.renderer.scroll(dy=-self.term.height // 2)
            return

        if key.name == "KEY_PGDN":
            self.renderer.scroll(dy=self.term.height // 2)
            return

        # Enter key - activate focused element
        if key.name == "KEY_ENTER" or key == "\n" or key == "\r":
            focused = self.renderer.focused
            if focused:
                if focused.tag == "button":
                    focused._fire_event("click")
                    self.renderer.invalidate()
            return

        # Handle text input for focused input elements
        focused = self.renderer.focused
        if focused and focused.tag == "input":
            enabled = getattr(focused, "enabled", True)
            if not enabled:
                return

            if key.name == "KEY_BACKSPACE" or key.code == 127:
                value = getattr(focused, "value", "") or ""
                if value:
                    focused.value = value[:-1]
                    focused._fire_event("change", focused.value)
                    self.renderer.invalidate()
                return

            if key.name == "KEY_DELETE":
                focused.value = ""
                focused._fire_event("change", "")
                self.renderer.invalidate()
                return

            # Regular character input
            if not key.is_sequence and key.isprintable():
                value = getattr(focused, "value", "") or ""
                focused.value = value + str(key)
                focused._fire_event("change", focused.value)
                self.renderer.invalidate()

    async def _handle_mouse(self, key) -> None:
        """Handle mouse events."""
        # Parse mouse position from key if available
        # Blessed provides mouse info via key attributes
        if hasattr(key, 'x') and hasattr(key, 'y'):
            x, y = key.x, key.y
        else:
            # Try to extract from key code
            return

        element = self.renderer.get_element_at(x, y)

        # Handle hover
        self.renderer.set_hover(element)

        # Handle click
        if hasattr(key, 'name') and 'MOUSE' in str(key.name):
            if 'RELEASE' not in str(key.name) and element:
                # Click
                if element.tag == "button":
                    self.renderer.focus_element(element)
                    element._fire_event("click")
                    self.renderer.invalidate()
                elif element.tag == "input":
                    self.renderer.focus_element(element)
                    self.renderer.invalidate()

    async def _navigate(self, path: str) -> None:
        """Navigate to a page."""
        if not self.client:
            return

        # Find matching route
        match = router.match(path)
        if not match:
            # 404 - create error page
            self.client.clear()
            with self.client:
                from .elements import Label, Column
                with Column() as col:
                    Label(f"404 - Page not found: {path}")
                self._root_element = col
            self.renderer.invalidate()
            return

        route, params = match
        self.client.navigate_to(path)
        self.client.clear()

        # Build page
        await route.build(self.client, params)

        # Find root element(s) - elements without parent
        roots = [el for el in self.client.elements.values() if el.parent_slot is None]
        if roots:
            if len(roots) == 1:
                self._root_element = roots[0]
            else:
                # Wrap multiple roots in a column
                from .elements import Column
                wrapper = Column()
                for root in roots:
                    root.move(wrapper)
                self._root_element = wrapper

        self.renderer.invalidate()

    async def _watch_files(self) -> None:
        """Watch for file changes and reload."""
        try:
            from watchfiles import awatch

            async for changes in awatch(Path.cwd()):
                py_changes = [(ct, p) for ct, p in changes if p.endswith('.py')]
                if py_changes and self._running:
                    # Reload current page
                    if self.client:
                        current = self.client.current_path
                        await self._navigate(current)
        except ImportError:
            pass
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def _cleanup(self) -> None:
        """Cleanup on exit."""
        app._running = False


# Global app instance
_app: Optional[RawGUIApp] = None


def run(
    *,
    host: str = "0.0.0.0",  # Ignored
    port: int = 8080,  # Ignored
    title: str = "RawGUI",
    reload: bool = True,
    show: bool = True,  # Ignored
    dark: Optional[bool] = None,
    storage_secret: Optional[str] = None,
    native: bool = False,  # Ignored
    **kwargs,
) -> None:
    """Run the RawGUI application.

    NiceGUI-compatible signature.

    Args:
        title: Application title
        reload: Enable auto-reload on file changes
        dark: Dark mode (None = auto)
        Other args are for NiceGUI compatibility and ignored
    """
    global _app
    _app = RawGUIApp(title=title, reload=reload, dark=dark)
    _app.run()
