"""RawGUI testing utilities.

Provides tools for testing TUI applications including:
- SubprocessTerminal: PTY-based testing similar to Selenium
- Screenshot capture for all renderers (TUI, PIL, NiceGUI, Tkinter with Xvfb)
- User: Selenium-like API for simulating user interactions
"""

from .subprocess_terminal import SubprocessTerminal, run_terminal_test
from .screenshots import capture_tui, capture_pil, capture_nicegui, capture_all_renderers
from .screenshot_xvfb import capture_tkinter_xvfb
from .user import User, TUIUser, TkinterUser, ElementInfo, compare_images

__all__ = [
    "SubprocessTerminal",
    "run_terminal_test",
    "capture_tui",
    "capture_pil",
    "capture_nicegui",
    "capture_all_renderers",
    "capture_tkinter_xvfb",
    "User",
    "TUIUser",
    "TkinterUser",
    "ElementInfo",
    "compare_images",
]
