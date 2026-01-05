"""RawGUI testing utilities.

Provides tools for testing TUI applications including:
- SubprocessTerminal: PTY-based testing similar to Selenium
- Screenshot capture for all renderers (TUI, PIL, NiceGUI)
- User: Selenium-like API for simulating user interactions
"""

from .subprocess_terminal import SubprocessTerminal, run_terminal_test
from .screenshots import capture_tui, capture_pil, capture_nicegui, capture_all_renderers
from .user import User, TUIUser, TkinterUser, ElementInfo, compare_images

__all__ = [
    "SubprocessTerminal",
    "run_terminal_test",
    "capture_tui",
    "capture_pil",
    "capture_nicegui",
    "capture_all_renderers",
    "User",
    "TUIUser",
    "TkinterUser",
    "ElementInfo",
    "compare_images",
]
