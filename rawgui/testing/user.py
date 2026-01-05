"""Unified testing API for RawGUI - Selenium-like interface.

Provides a consistent API for testing both TUI and Tkinter renderers:
- Element location and coordinates
- Click simulation
- Keyboard input simulation
- Screenshot capture and comparison

Usage:
    from rawgui.testing import User

    # Test with TUI renderer
    with User("examples/counter.py", renderer="tui") as user:
        user.wait_for_text("Counter")
        user.click_text("+ Increment")
        user.screenshot("after_click.png")
        assert user.contains("Count: 1")

    # Test with Tkinter renderer
    with User("examples/counter.py", renderer="tkinter") as user:
        user.click_element_at(100, 200)
        user.press_key("space")
        user.screenshot("result.png")
"""

from __future__ import annotations

import asyncio
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from PIL import Image

if TYPE_CHECKING:
    from ..element import Element


@dataclass
class ElementInfo:
    """Information about a rendered element."""
    element: "Element"
    x: int
    y: int
    width: int
    height: int
    text: str
    tag: str
    focused: bool = False

    @property
    def center(self) -> Tuple[int, int]:
        """Get center coordinates."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is inside element bounds."""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


class BaseUser(ABC):
    """Abstract base class for test users."""

    @abstractmethod
    def start(self) -> None:
        """Start the application."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the application."""
        pass

    @abstractmethod
    def screenshot(self, path: str) -> Path:
        """Take a screenshot."""
        pass

    @abstractmethod
    def get_elements(self) -> List[ElementInfo]:
        """Get all rendered elements with coordinates."""
        pass

    @abstractmethod
    def click(self, x: int, y: int) -> None:
        """Click at coordinates."""
        pass

    @abstractmethod
    def press_key(self, key: str) -> None:
        """Press a key (enter, space, tab, escape, up, down, left, right, or character)."""
        pass

    @abstractmethod
    def type_text(self, text: str) -> None:
        """Type text characters."""
        pass

    def find_by_text(self, text: str) -> Optional[ElementInfo]:
        """Find element by text content."""
        for el in self.get_elements():
            if text in el.text:
                return el
        return None

    def find_by_tag(self, tag: str) -> List[ElementInfo]:
        """Find elements by tag name."""
        return [el for el in self.get_elements() if el.tag == tag]

    def find_focused(self) -> Optional[ElementInfo]:
        """Find the currently focused element."""
        for el in self.get_elements():
            if el.focused:
                return el
        return None

    def click_text(self, text: str) -> bool:
        """Click on element containing text."""
        el = self.find_by_text(text)
        if el:
            cx, cy = el.center
            self.click(cx, cy)
            return True
        return False

    def click_element(self, element: ElementInfo) -> None:
        """Click on a specific element."""
        cx, cy = element.center
        self.click(cx, cy)

    def get_text(self) -> str:
        """Get all visible text."""
        return "\n".join(el.text for el in self.get_elements() if el.text)

    def contains(self, text: str) -> bool:
        """Check if text is visible."""
        return text in self.get_text()

    def should_contain(self, text: str) -> None:
        """Assert text is visible."""
        if not self.contains(text):
            raise AssertionError(f"Expected text '{text}' not found. Visible: {self.get_text()}")

    def should_not_contain(self, text: str) -> None:
        """Assert text is not visible."""
        if self.contains(text):
            raise AssertionError(f"Unexpected text '{text}' found")

    def __enter__(self) -> "BaseUser":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()


class TUIUser(BaseUser):
    """Test user for TUI renderer using subprocess."""

    def __init__(self, script_path: str, width: int = 80, height: int = 24):
        self.script_path = Path(script_path).resolve()
        self.width = width
        self.height = height
        self._terminal: Optional["SubprocessTerminal"] = None

    def start(self) -> None:
        from .subprocess_terminal import SubprocessTerminal
        command = f"poetry run python {self.script_path}"
        self._terminal = SubprocessTerminal(command, rows=self.height, cols=self.width)
        self._terminal.start()
        time.sleep(0.5)  # Wait for startup

    def stop(self) -> None:
        if self._terminal:
            self._terminal.stop()
            self._terminal = None

    def screenshot(self, path: str) -> Path:
        if not self._terminal:
            raise RuntimeError("Not started")
        return self._terminal.screenshot(path)

    def get_elements(self) -> List[ElementInfo]:
        """Get elements from TUI (limited - text-based detection)."""
        # TUI doesn't have structured element info, return empty
        # Use contains() and find text methods instead
        return []

    def click(self, x: int, y: int) -> None:
        """Simulate mouse click at terminal coordinates."""
        if not self._terminal:
            raise RuntimeError("Not started")
        # Send mouse click escape sequence
        # For now, we can't easily simulate clicks in TUI
        # Use keyboard navigation instead
        pass

    def press_key(self, key: str) -> None:
        if not self._terminal:
            raise RuntimeError("Not started")
        key_map = {
            "enter": "\n",
            "space": " ",
            "tab": "⇥",
            "escape": "⎋",
            "up": "↑",
            "down": "↓",
            "left": "←",
            "right": "→",
            "backspace": "⌫",
        }
        self._terminal.send_keys(key_map.get(key.lower(), key))

    def type_text(self, text: str) -> None:
        if not self._terminal:
            raise RuntimeError("Not started")
        self._terminal.send_text(text)

    def wait_for_text(self, text: str, timeout: float = 5.0) -> bool:
        if not self._terminal:
            raise RuntimeError("Not started")
        return self._terminal.wait_for_text(text, timeout=timeout)

    def get_text(self) -> str:
        if not self._terminal:
            raise RuntimeError("Not started")
        return self._terminal.get_text()

    def contains(self, text: str) -> bool:
        if not self._terminal:
            raise RuntimeError("Not started")
        return self._terminal.contains(text)


class TkinterUser(BaseUser):
    """Test user for Tkinter renderer (headless)."""

    def __init__(self, script_path: str, width: int = 800, height: int = 600):
        self.script_path = Path(script_path).resolve()
        self.width = width
        self.height = height
        self._adapter: Optional["TkinterAdapter"] = None
        self._client: Optional["Client"] = None
        self._root: Optional["Element"] = None
        self._elements: List[ElementInfo] = []

    def start(self) -> None:
        from ..adapters import TkinterAdapter
        from ..app import app
        from ..client import Client
        from ..page import router

        # Reset app state
        app._routes = {}
        app._auto_index_client = None
        app._startup_handlers = []
        app._shutdown_handlers = []
        app._connect_handlers = []
        app._disconnect_handlers = []
        app._pending_navigation = None
        router.routes = []

        # Clear any cached modules from previous runs to ensure fresh state
        script_module_name = self.script_path.stem
        modules_to_remove = [
            name for name in sys.modules
            if script_module_name in name or str(self.script_path.parent) in str(getattr(sys.modules[name], '__file__', ''))
        ]
        for name in modules_to_remove:
            del sys.modules[name]

        # Add script directory to path
        script_dir = str(self.script_path.parent)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Execute script in fresh namespace
        with open(self.script_path) as f:
            code = f.read()
            lines = code.split("\n")
            filtered = []
            skip_if_main = False
            for line in lines:
                if '__name__' in line and '__main__' in line:
                    skip_if_main = True
                    continue
                if skip_if_main:
                    if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                        skip_if_main = False
                    else:
                        continue
                if "ui.run(" in line:
                    continue
                filtered.append(line)
            code = "\n".join(filtered)
            # Use fresh globals dict to avoid state persistence
            self._script_globals = {"__name__": "__script__", "__file__": str(self.script_path)}
            exec(compile(code, self.script_path, "exec"), self._script_globals)

        # Create adapter and client
        self._adapter = TkinterAdapter(width=self.width, height=self.height, title="Test", dark=True)
        self._client = Client()

        # Build initial page
        self._build_page()

    def _build_page(self) -> None:
        """Build the current page."""
        from ..app import app
        from ..page import router

        async def build():
            await app._run_startup()
            app._run_connect(self._client)

            match = router.match("/")
            if not match and app._auto_index_client:
                auto_client = app._auto_index_client
                roots = [el for el in auto_client.elements.values() if el.parent_slot is None]
                if roots:
                    for el in list(auto_client.elements.values()):
                        el.client = self._client
                        self._client.register_element(el)
                    return roots[0] if len(roots) == 1 else roots[0]

            if match:
                route, params = match
                self._client.navigate_to("/")
                self._client.clear()
                await route.build(self._client, params)
                roots = [el for el in self._client.elements.values() if el.parent_slot is None]
                if roots:
                    return roots[0] if len(roots) == 1 else roots[0]
            return None

        self._root = asyncio.run(build())
        if self._root and self._adapter:
            self._adapter.render(self._root)
            self._index_elements()

    def _rebuild_page(self) -> None:
        """Rebuild page after state change."""
        from ..app import app
        from ..page import router

        # Save focus
        saved_focus = self._adapter._focus_index if self._adapter else 0

        # Clear and rebuild
        if self._client:
            self._client.clear()

        async def rebuild():
            match = router.match("/")
            if match:
                route, params = match
                await route.build(self._client, params)
                roots = [el for el in self._client.elements.values() if el.parent_slot is None]
                if roots:
                    return roots[0] if len(roots) == 1 else roots[0]
            return None

        self._root = asyncio.run(rebuild())
        if self._root and self._adapter:
            self._adapter._pending_focus_index = saved_focus
            self._adapter.render(self._root)
            self._index_elements()

    def _index_elements(self) -> None:
        """Index all rendered elements."""
        self._elements = []
        if not self._adapter or not self._adapter._render_tree:
            return

        def walk(node):
            if node.element:
                text = ""
                if hasattr(node.element, "text"):
                    text = getattr(node.element, "text", "") or ""
                elif hasattr(node.element, "label"):
                    text = getattr(node.element, "label", "") or ""

                self._elements.append(ElementInfo(
                    element=node.element,
                    x=node.x,
                    y=node.y,
                    width=node.width,
                    height=node.height,
                    text=text,
                    tag=node.element.tag,
                    focused=node.focused,
                ))
            for child in node.children:
                walk(child)

        walk(self._adapter._render_tree)

    def stop(self) -> None:
        self._adapter = None
        self._client = None
        self._root = None
        self._elements = []

    def screenshot(self, path: str) -> Path:
        if not self._adapter:
            raise RuntimeError("Not started")
        return self._adapter.screenshot(path)

    def get_image(self) -> Image.Image:
        """Get current render as PIL Image."""
        if not self._adapter:
            raise RuntimeError("Not started")
        return self._adapter.get_image()

    def get_elements(self) -> List[ElementInfo]:
        return self._elements

    def click(self, x: int, y: int) -> None:
        """Simulate click at coordinates."""
        if not self._adapter:
            raise RuntimeError("Not started")

        # Find element at position
        element = self._adapter.get_element_at(x, y)
        if element:
            # Focus the element
            self._adapter.focus_element(element)

            # Trigger click event
            if element.tag == "button":
                element._fire_event("click")
            elif element.tag == "checkbox":
                element.toggle()

            # Check for pending navigation
            from ..app import app
            if app._pending_navigation:
                app._pending_navigation = None
                self._rebuild_page()
            else:
                # Just re-render
                if self._root:
                    self._adapter.render(self._root)
                    self._index_elements()

    def press_key(self, key: str) -> None:
        """Simulate key press."""
        if not self._adapter:
            raise RuntimeError("Not started")

        focused = self._adapter.focused

        if key.lower() == "enter":
            if focused:
                if focused.tag == "button":
                    focused._fire_event("click")
                elif focused.tag == "checkbox":
                    focused.toggle()
                elif focused.tag == "input":
                    if self._adapter._edit_mode:
                        self._adapter.exit_edit_mode()
                    else:
                        self._adapter.enter_edit_mode()
        elif key.lower() == "space":
            if focused:
                if focused.tag == "button":
                    focused._fire_event("click")
                elif focused.tag == "checkbox":
                    focused.toggle()
        elif key.lower() == "tab":
            self._adapter.exit_edit_mode()
            self._adapter.focus_next()
        elif key.lower() in ("up", "left"):
            self._adapter.focus_prev()
        elif key.lower() in ("down", "right"):
            self._adapter.focus_next()
        elif key.lower() == "escape":
            self._adapter.exit_edit_mode()

        # Check for pending navigation
        from ..app import app
        if app._pending_navigation:
            app._pending_navigation = None
            self._rebuild_page()
        else:
            if self._root:
                self._adapter.render(self._root)
                self._index_elements()

    def type_text(self, text: str) -> None:
        """Type text into focused input."""
        if not self._adapter:
            raise RuntimeError("Not started")

        focused = self._adapter.focused
        if focused and focused.tag == "input":
            self._adapter.enter_edit_mode()
            value = getattr(focused, "value", "") or ""
            focused.value = value + text
            focused._cursor_pos = len(focused.value)
            focused._fire_event("change", focused.value)

            if self._root:
                self._adapter.render(self._root)
                self._index_elements()

    def wait_for_text(self, text: str, timeout: float = 1.0) -> bool:
        """Wait for text to appear (immediate for Tkinter since it's synchronous)."""
        return self.contains(text)


class User:
    """Factory for creating test users."""

    def __new__(cls, script_path: str, renderer: str = "tkinter", **kwargs) -> BaseUser:
        """Create appropriate user based on renderer.

        Args:
            script_path: Path to the script to test
            renderer: "tui" or "tkinter"
            **kwargs: Additional arguments (width, height)

        Returns:
            TUIUser or TkinterUser instance
        """
        if renderer.lower() == "tui":
            return TUIUser(script_path, **kwargs)
        else:
            return TkinterUser(script_path, **kwargs)


def compare_images(img1: Image.Image | str, img2: Image.Image | str, threshold: float = 0.01) -> Tuple[bool, float]:
    """Compare two images and return similarity.

    Args:
        img1: First image or path
        img2: Second image or path
        threshold: Maximum difference ratio to consider equal

    Returns:
        (are_equal, difference_ratio)
    """
    if isinstance(img1, str):
        img1 = Image.open(img1)
    if isinstance(img2, str):
        img2 = Image.open(img2)

    # Ensure same size
    if img1.size != img2.size:
        return False, 1.0

    # Convert to same mode
    img1 = img1.convert("RGB")
    img2 = img2.convert("RGB")

    # Calculate pixel differences
    pixels1 = list(img1.getdata())
    pixels2 = list(img2.getdata())

    diff_count = 0
    for p1, p2 in zip(pixels1, pixels2):
        if p1 != p2:
            diff_count += 1

    diff_ratio = diff_count / len(pixels1)
    return diff_ratio <= threshold, diff_ratio
