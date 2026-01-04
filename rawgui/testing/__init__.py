"""RawGUI testing utilities.

Provides tools for testing TUI applications including:
- SubprocessTerminal: PTY-based testing similar to Selenium
- Screenshot capture and comparison
"""

from .subprocess_terminal import SubprocessTerminal, run_terminal_test

__all__ = [
    "SubprocessTerminal",
    "run_terminal_test",
]
