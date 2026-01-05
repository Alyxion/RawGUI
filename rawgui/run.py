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

                    # Check for pending navigation (from ui.navigate.to)
                    if app._pending_navigation is not None:
                        path = app._pending_navigation
                        app._pending_navigation = None
                        await self._navigate(path)

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
        """Read a key with timeout (non-blocking).

        Uses a short timeout with inkey() which is designed to be non-blocking.
        The blessed inkey() with timeout uses select/poll internally.
        """
        # Use very short timeout to stay responsive
        key = self.term.inkey(timeout=timeout)

        # Yield to event loop to keep things responsive
        await asyncio.sleep(0)

        if key:
            return key
        return None

    async def _handle_input(self, key) -> None:
        """Handle keyboard and mouse input."""
        key_str = str(key)
        focused = self.renderer.focused
        in_edit_mode = self.renderer.edit_mode

        # Check for quit - Ctrl+C (chr(3)), Ctrl+Q (chr(17))
        if key_str == '\x03' or key_str == '\x11':  # Ctrl+C or Ctrl+Q
            self._running = False
            return

        # Escape - exit edit mode first, or quit if not in edit mode
        if key_str == '\x1b' or key.name == "KEY_ESCAPE":
            if in_edit_mode:
                self.renderer.exit_edit_mode()
                return
            self._running = False
            return

        # 'q' to quit (only if not focused on an input/textarea)
        if key_str == 'q' and (not focused or focused.tag not in ("input", "textarea")):
            self._running = False
            return

        # Mouse events - blessed uses names like KEY_MOUSE, MOUSE_RELEASE, etc.
        if key.name and "MOUSE" in str(key.name).upper():
            await self._handle_mouse(key)
            return

        # Tab navigation - always works
        if key.name == "KEY_TAB":
            self.renderer.exit_edit_mode()
            self.renderer.focus_next()
            self.renderer.invalidate()
            return

        if key.name == "KEY_BTAB":  # Shift+Tab
            self.renderer.exit_edit_mode()
            self.renderer.focus_prev()
            self.renderer.invalidate()
            return

        # Arrow key navigation
        if key.name == "KEY_UP":
            # Inputs don't capture Up/Down, so navigate to prev element
            if not focused or focused.tag in ("input", "button", "checkbox"):
                self.renderer.exit_edit_mode()
                self.renderer.focus_prev()
                self.renderer.invalidate()
            elif focused.tag in ("select", "textarea"):
                # These capture Up/Down for internal navigation
                pass  # TODO: handle select/textarea navigation
            return

        if key.name == "KEY_DOWN":
            # Inputs don't capture Up/Down, so navigate to next element
            if not focused or focused.tag in ("input", "button", "checkbox"):
                self.renderer.exit_edit_mode()
                self.renderer.focus_next()
                self.renderer.invalidate()
            elif focused.tag in ("select", "textarea"):
                # These capture Up/Down for internal navigation
                pass  # TODO: handle select/textarea navigation
            return

        if key.name == "KEY_LEFT":
            if in_edit_mode and focused and focused.tag == "input":
                # Move cursor left within input
                cursor_pos = getattr(focused, "_cursor_pos", 0)
                if cursor_pos > 0:
                    focused._cursor_pos = cursor_pos - 1
                    self.renderer.invalidate()
            else:
                # Navigate to previous element
                self.renderer.focus_prev()
                self.renderer.invalidate()
            return

        if key.name == "KEY_RIGHT":
            if in_edit_mode and focused and focused.tag == "input":
                # Move cursor right within input
                value = getattr(focused, "value", "") or ""
                cursor_pos = getattr(focused, "_cursor_pos", len(value))
                if cursor_pos < len(value):
                    focused._cursor_pos = cursor_pos + 1
                    self.renderer.invalidate()
            else:
                # Navigate to next element
                self.renderer.focus_next()
                self.renderer.invalidate()
            return

        if key.name == "KEY_PGUP":
            self.renderer.scroll(dy=-self.term.height // 2)
            return

        if key.name == "KEY_PGDN":
            self.renderer.scroll(dy=self.term.height // 2)
            return

        # Browser-like navigation hotkeys
        # Alt+Left = Back, Alt+Right = Forward
        if key.name == "kLFT5" or (hasattr(key, 'code') and key.code == 554):  # Alt+Left
            await self._navigate_back()
            return

        if key.name == "kRIT5" or (hasattr(key, 'code') and key.code == 569):  # Alt+Right
            await self._navigate_forward()
            return

        # Backspace at top level navigates back (like browser)
        if key.name == "KEY_BACKSPACE" and not focused:
            await self._navigate_back()
            return

        # Enter key - activate focused element or enter edit mode
        if key.name == "KEY_ENTER" or key_str == "\n" or key_str == "\r":
            if focused:
                if focused.tag == "button":
                    focused._fire_event("click")
                    self.renderer.invalidate()
                elif focused.tag == "checkbox":
                    focused.toggle()
                    self.renderer.invalidate()
                elif focused.tag == "input":
                    # Enter toggles edit mode for inputs
                    if in_edit_mode:
                        self.renderer.exit_edit_mode()
                    else:
                        self.renderer.enter_edit_mode()
                    self.renderer.invalidate()
            return

        # Space key - activate buttons and toggle checkboxes
        if key_str == " ":
            if focused:
                if focused.tag == "button":
                    focused._fire_event("click")
                    self.renderer.invalidate()
                elif focused.tag == "checkbox":
                    focused.toggle()
                    self.renderer.invalidate()
                elif focused.tag == "input":
                    # Space in input enters text
                    self.renderer.enter_edit_mode()
                    value = getattr(focused, "value", "") or ""
                    focused.value = value + " "
                    focused._fire_event("change", focused.value)
                    self.renderer.invalidate()
            return

        # Handle text input for focused input elements
        if focused and focused.tag == "input":
            enabled = getattr(focused, "enabled", True)
            if not enabled:
                return

            value = getattr(focused, "value", "") or ""
            cursor_pos = getattr(focused, "_cursor_pos", len(value))

            if key.name == "KEY_BACKSPACE" or key.code == 127:
                # Delete character before cursor
                if cursor_pos > 0:
                    focused.value = value[:cursor_pos - 1] + value[cursor_pos:]
                    focused._cursor_pos = cursor_pos - 1
                    focused._fire_event("change", focused.value)
                    self.renderer.invalidate()
                return

            if key.name == "KEY_DELETE":
                # Delete character after cursor
                if cursor_pos < len(value):
                    focused.value = value[:cursor_pos] + value[cursor_pos + 1:]
                    focused._fire_event("change", focused.value)
                    self.renderer.invalidate()
                return

            # Home key - move cursor to start
            if key.name == "KEY_HOME":
                focused._cursor_pos = 0
                self.renderer.invalidate()
                return

            # End key - move cursor to end
            if key.name == "KEY_END":
                focused._cursor_pos = len(value)
                self.renderer.invalidate()
                return

            # Regular character input - enter edit mode, insert at cursor
            if not key.is_sequence and key.isprintable():
                self.renderer.enter_edit_mode()
                focused.value = value[:cursor_pos] + str(key) + value[cursor_pos:]
                focused._cursor_pos = cursor_pos + 1
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
        old_hover = getattr(self.renderer, '_hovered', None)
        self.renderer.set_hover(element)
        if old_hover != element:
            self.renderer.invalidate()

        # Handle click - only on button press (not release)
        key_name = str(key.name) if key.name else ""
        is_press = "MOUSE" in key_name and "RELEASE" not in key_name

        if is_press and element:
            if element.tag == "button":
                self.renderer.focus_element(element)
                element._fire_event("click")
                self.renderer.invalidate()
            elif element.tag == "input":
                self.renderer.focus_element(element)
                self.renderer.invalidate()
            elif element.tag == "checkbox":
                self.renderer.focus_element(element)
                element.toggle()
                self.renderer.invalidate()

    async def _navigate(self, path: str) -> None:
        """Navigate to a page."""
        if not self.client:
            return

        # Preserve focus index for restoration after page rebuild
        saved_focus_index = self.renderer.focus_index

        # Find matching route
        match = router.match(path)

        # Check for implicit root page (NiceGUI compatibility)
        if not match and path == "/" and app._auto_index_client:
            # Use elements from auto-index client as implicit root page
            auto_client = app._auto_index_client
            roots = [el for el in auto_client.elements.values() if el.parent_slot is None]
            if roots:
                self.client.navigate_to(path)
                # Transfer elements to the actual client
                for el in list(auto_client.elements.values()):
                    el.client = self.client
                    self.client.register_element(el)
                auto_client.elements.clear()

                if len(roots) == 1:
                    self._root_element = roots[0]
                else:
                    from .elements import Column
                    wrapper = Column()
                    for root in roots:
                        root.move(wrapper)
                    self._root_element = wrapper
                self.renderer.schedule_focus_restore(saved_focus_index)
                self.renderer.invalidate()
                return

        if not match:
            # 404 - create error page
            self.client.clear()
            with self.client:
                from .elements import Label, Column
                with Column() as col:
                    Label(f"404 - Page not found: {path}")
                self._root_element = col
            self.renderer.schedule_focus_restore(saved_focus_index)
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

        self.renderer.schedule_focus_restore(saved_focus_index)
        self.renderer.invalidate()

    async def _navigate_back(self) -> None:
        """Navigate back in history."""
        if not self.client:
            return

        prev_path = self.client.navigate_back()
        if prev_path:
            await self._navigate(prev_path)

    async def _navigate_forward(self) -> None:
        """Navigate forward in history."""
        if not self.client:
            return

        next_path = self.client.navigate_forward()
        if next_path:
            await self._navigate(next_path)

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
    host: str = "0.0.0.0",  # Ignored for TUI
    port: int = 8080,  # Ignored for TUI
    title: str = "RawGUI",
    reload: bool = True,
    show: bool = True,  # Ignored for TUI
    dark: Optional[bool] = None,
    storage_secret: Optional[str] = None,
    native: bool = False,  # Ignored for TUI
    renderer: Optional[str] = None,  # "tui", "tkinter", "nicegui"
    **kwargs,
) -> None:
    """Run the RawGUI application.

    NiceGUI-compatible signature. The renderer can be selected via:
    1. Environment variable RAWGUI_RENDERER (recommended)
    2. The 'renderer' parameter (for testing)

    Args:
        title: Application title
        reload: Enable auto-reload on file changes
        dark: Dark mode (None = auto)
        renderer: Renderer backend ("tui", "tkinter", "nicegui")
        Other args are for NiceGUI compatibility and may be ignored
    """
    global _app

    # Determine renderer: env var takes precedence, then parameter, then default
    selected_renderer = os.environ.get("RAWGUI_RENDERER", renderer or "tui").lower()

    if selected_renderer == "nicegui":
        # Use actual NiceGUI
        try:
            from nicegui import ui as nicegui_ui
            nicegui_ui.run(
                host=host,
                port=port,
                title=title,
                reload=reload,
                show=show,
                dark=dark,
                storage_secret=storage_secret,
                native=native,
                **kwargs,
            )
        except ImportError:
            print("Error: nicegui not installed. Install with: pip install nicegui")
            sys.exit(1)

    elif selected_renderer == "tkinter":
        # Use Tkinter adapter with Pillow rendering
        _run_tkinter(title=title, dark=dark, reload=reload)

    else:
        # Default: TUI mode
        _app = RawGUIApp(title=title, reload=reload, dark=dark)
        _app.run()


def _run_tkinter(
    title: str = "RawGUI",
    dark: bool = True,
    reload: bool = False,
    width: int = 800,
    height: int = 600,
) -> None:
    """Run with Tkinter adapter."""
    from .adapters import TkinterAdapter
    from .client import Client

    # Configure app
    app.config.title = title
    app._running = True

    # Create client
    client = Client()

    # Create adapter
    adapter = TkinterAdapter(
        width=width,
        height=height,
        title=title,
        dark=dark if dark is not None else True,
    )

    # Store client reference for rebuilding
    adapter._client = client

    def rebuild_page():
        """Rebuild the current page (called after navigation)."""
        import asyncio

        async def _rebuild():
            # Clear client elements
            client.clear()

            # Find matching route
            match = router.match("/")
            if match:
                route, params = match
                await route.build(client, params)

                # Get root elements
                roots = [el for el in client.elements.values() if el.parent_slot is None]
                if roots:
                    return roots[0] if len(roots) == 1 else roots[0]
            return None

        # Run async rebuild in a new event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an existing loop - use nest_asyncio or run in thread
            # For simplicity, create a new loop in a thread-safe way
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _rebuild())
                return future.result()
        else:
            return asyncio.run(_rebuild())

    # Set rebuild callback
    adapter._rebuild_callback = rebuild_page

    async def build_page():
        """Build the page without rendering (rendering happens after window is created)."""
        # Run startup handlers
        await app._run_startup()
        app._run_connect(client)

        # Find matching route for root
        match = router.match("/")

        # Check for implicit root page
        if not match and app._auto_index_client:
            auto_client = app._auto_index_client
            roots = [el for el in auto_client.elements.values() if el.parent_slot is None]
            if roots:
                for el in list(auto_client.elements.values()):
                    el.client = client
                    client.register_element(el)
                auto_client.elements.clear()
                return roots[0] if len(roots) == 1 else roots[0]

        if match:
            route, params = match
            client.navigate_to("/")
            await route.build(client, params)

            # Get root elements
            roots = [el for el in client.elements.values() if el.parent_slot is None]
            if roots:
                return roots[0] if len(roots) == 1 else roots[0]

        return None

    import asyncio
    root_element = asyncio.run(build_page())

    # Set root element for rendering after window is created
    adapter._root_element = root_element

    # Run the adapter main loop (creates window and renders)
    adapter.run()
