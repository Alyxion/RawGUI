"""Subprocess-based terminal tester.

Runs a real terminal application in a PTY subprocess and allows:
- Sending keystrokes
- Capturing terminal state
- Rendering screenshots to PNG
- Finding text (like Selenium's find_element)

Usage:
    tester = SubprocessTerminal("poetry run rawgui")
    tester.start()
    tester.wait_for_text("Welcome")
    tester.send_keys("↓↓↓\n")
    tester.screenshot("output.png")
    tester.stop()
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pexpect
import pyte
from PIL import Image, ImageDraw, ImageFont


class SubprocessTerminal:
    """Run a terminal app in a subprocess with PTY support.

    Provides methods to send keystrokes, wait for specific text,
    capture the terminal buffer, and render screenshots to PNG.
    """

    # ANSI escape code to key mapping
    KEY_MAP = {
        "↑": "\x1b[A",  # Up arrow
        "↓": "\x1b[B",  # Down arrow
        "→": "\x1b[C",  # Right arrow
        "←": "\x1b[D",  # Left arrow
        "\n": "\r",     # Enter
        "⏎": "\r",      # Enter (alternative)
        "⇥": "\t",      # Tab
        "⎋": "\x1b",    # Escape
        "⌫": "\x7f",    # Backspace
    }

    def __init__(
        self,
        command: str,
        rows: int = 24,
        cols: int = 80,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the subprocess terminal.

        Args:
            command: The command to run (e.g., "poetry run rawgui")
            rows: Terminal height in rows
            cols: Terminal width in columns
            cwd: Working directory for the process
            env: Additional environment variables
        """
        self.command = command
        self.rows = rows
        self.cols = cols
        self.cwd = cwd
        self.env = env or {}

        # PTY process
        self._process: Optional[pexpect.spawn] = None

        # Terminal emulator
        self._screen = pyte.Screen(cols, rows)
        self._stream = pyte.Stream(self._screen)

    def start(self, timeout: float = 10.0) -> None:
        """Start the terminal process.

        Args:
            timeout: Time to wait for process to start
        """
        # Build environment
        process_env = os.environ.copy()
        process_env.update(self.env)
        process_env["TERM"] = "xterm-256color"

        # Spawn the process
        self._process = pexpect.spawn(
            self.command,
            encoding="utf-8",
            timeout=timeout,
            cwd=self.cwd,
            env=process_env,
            dimensions=(self.rows, self.cols),
        )

        # Give it a moment to initialize
        time.sleep(0.5)
        self._read_output()

    def stop(self) -> None:
        """Stop the terminal process."""
        if self._process:
            self._process.close(force=True)
            self._process = None

    def send_keys(self, keys: str, delay: float = 0.1) -> None:
        """Send keystrokes to the terminal.

        Supports special keys via unicode arrows:
        - ↑↓←→ for arrow keys
        - ⏎ or \\n for Enter
        - ⇥ for Tab
        - ⎋ for Escape
        - ⌫ for Backspace

        Args:
            keys: String of keys to send
            delay: Delay after sending (for terminal to process)
        """
        if not self._process:
            raise RuntimeError("Terminal not started")

        # Convert special keys
        output = ""
        for char in keys:
            output += self.KEY_MAP.get(char, char)

        self._process.send(output)
        time.sleep(delay)
        self._read_output()

    def send_text(self, text: str, delay: float = 0.1) -> None:
        """Send plain text (no key translation).

        Args:
            text: Text to send
            delay: Delay after sending
        """
        if not self._process:
            raise RuntimeError("Terminal not started")

        self._process.send(text)
        time.sleep(delay)
        self._read_output()

    def press_enter(self, delay: float = 0.1) -> None:
        """Press Enter key."""
        self.send_keys("\n", delay)

    def press_tab(self, delay: float = 0.1) -> None:
        """Press Tab key."""
        self.send_keys("⇥", delay)

    def press_down(self, count: int = 1, delay: float = 0.1) -> None:
        """Press Down arrow key."""
        self.send_keys("↓" * count, delay)

    def press_up(self, count: int = 1, delay: float = 0.1) -> None:
        """Press Up arrow key."""
        self.send_keys("↑" * count, delay)

    def press_left(self, count: int = 1, delay: float = 0.1) -> None:
        """Press Left arrow key."""
        self.send_keys("←" * count, delay)

    def press_right(self, count: int = 1, delay: float = 0.1) -> None:
        """Press Right arrow key."""
        self.send_keys("→" * count, delay)

    def press_escape(self, delay: float = 0.1) -> None:
        """Press Escape key."""
        self.send_keys("⎋", delay)

    def press_backspace(self, count: int = 1, delay: float = 0.1) -> None:
        """Press Backspace key."""
        self.send_keys("⌫" * count, delay)

    def _read_output(self) -> None:
        """Read available output from the process and update screen."""
        if not self._process:
            return

        try:
            # Read all available output (non-blocking)
            while True:
                try:
                    data = self._process.read_nonblocking(size=4096, timeout=0.1)
                    if data:
                        self._stream.feed(data)
                    else:
                        break
                except pexpect.TIMEOUT:
                    break
                except pexpect.EOF:
                    break
        except Exception:
            pass

    def get_text(self) -> str:
        """Get the current terminal content as text.

        Returns:
            Multi-line string of terminal content
        """
        self._read_output()
        lines = []
        for row in range(self.rows):
            line = "".join(
                self._screen.buffer[row][col].data
                for col in range(self.cols)
            )
            lines.append(line.rstrip())

        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        return "\n".join(lines)

    def get_line(self, row: int) -> str:
        """Get a specific line from the terminal.

        Args:
            row: The row number (0-indexed)

        Returns:
            The line content
        """
        self._read_output()
        if 0 <= row < self.rows:
            line = "".join(
                self._screen.buffer[row][col].data
                for col in range(self.cols)
            )
            return line.rstrip()
        return ""

    def wait_for_text(
        self,
        text: str,
        timeout: float = 10.0,
        poll_interval: float = 0.2,
    ) -> bool:
        """Wait for specific text to appear on screen.

        Args:
            text: Text to wait for
            timeout: Maximum time to wait
            poll_interval: How often to check

        Returns:
            True if text found, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            content = self.get_text()
            if text in content:
                return True
            time.sleep(poll_interval)
        return False

    def find_text(self, text: str) -> List[Tuple[int, int]]:
        """Find all occurrences of text on screen.

        Args:
            text: Text to find

        Returns:
            List of (row, col) positions where text starts
        """
        self._read_output()
        positions = []

        for row in range(self.rows):
            line = "".join(
                self._screen.buffer[row][col].data
                for col in range(self.cols)
            )
            col = 0
            while True:
                idx = line.find(text, col)
                if idx == -1:
                    break
                positions.append((row, idx))
                col = idx + 1

        return positions

    def find_pattern(self, pattern: str) -> List[Tuple[int, int, str]]:
        """Find all occurrences of a regex pattern on screen.

        Args:
            pattern: Regex pattern to find

        Returns:
            List of (row, col, matched_text) tuples
        """
        self._read_output()
        matches = []
        regex = re.compile(pattern)

        for row in range(self.rows):
            line = "".join(
                self._screen.buffer[row][col].data
                for col in range(self.cols)
            )
            for match in regex.finditer(line):
                matches.append((row, match.start(), match.group()))

        return matches

    def contains(self, text: str) -> bool:
        """Check if text exists on screen.

        Args:
            text: Text to find

        Returns:
            True if text is found
        """
        return text in self.get_text()

    def should_contain(self, text: str) -> None:
        """Assert that text exists on screen.

        Args:
            text: Text that should be present

        Raises:
            AssertionError: If text is not found
        """
        content = self.get_text()
        if text not in content:
            raise AssertionError(
                f"Expected text '{text}' not found in terminal.\n"
                f"Terminal content:\n{content}"
            )

    def should_not_contain(self, text: str) -> None:
        """Assert that text does not exist on screen.

        Args:
            text: Text that should not be present

        Raises:
            AssertionError: If text is found
        """
        content = self.get_text()
        if text in content:
            raise AssertionError(
                f"Unexpected text '{text}' found in terminal.\n"
                f"Terminal content:\n{content}"
            )

    # ANSI 16 color palette (standard terminal colors)
    ANSI_COLORS = {
        "black": "#000000",
        "red": "#cd0000",
        "green": "#00cd00",
        "brown": "#cdcd00",
        "yellow": "#cdcd00",
        "blue": "#0000ee",
        "magenta": "#cd00cd",
        "cyan": "#00cdcd",
        "white": "#e5e5e5",
        "default": "#d4d4d4",
        # Bright variants
        "brightblack": "#7f7f7f",
        "brightred": "#ff0000",
        "brightgreen": "#00ff00",
        "brightyellow": "#ffff00",
        "brightblue": "#5c5cff",
        "brightmagenta": "#ff00ff",
        "brightcyan": "#00ffff",
        "brightwhite": "#ffffff",
    }

    def _color_to_rgb(self, color: str, bold: bool = False) -> str:
        """Convert pyte color to hex RGB."""
        if not color or color == "default":
            return self.ANSI_COLORS["default"]

        # Handle named colors
        color_lower = color.lower()
        if bold and color_lower in self.ANSI_COLORS:
            # Bold makes colors brighter
            bright_key = f"bright{color_lower}"
            if bright_key in self.ANSI_COLORS:
                return self.ANSI_COLORS[bright_key]

        if color_lower in self.ANSI_COLORS:
            return self.ANSI_COLORS[color_lower]

        # Handle hex colors (pyte sometimes returns these)
        if color.startswith("#"):
            return color

        # Handle 256 color codes
        try:
            code = int(color)
            if code < 16:
                # Standard colors
                names = [
                    "black", "red", "green", "yellow",
                    "blue", "magenta", "cyan", "white",
                    "brightblack", "brightred", "brightgreen", "brightyellow",
                    "brightblue", "brightmagenta", "brightcyan", "brightwhite",
                ]
                return self.ANSI_COLORS.get(names[code], self.ANSI_COLORS["default"])
            elif code < 232:
                # 216 color cube (6x6x6)
                code -= 16
                r = (code // 36) * 51
                g = ((code // 6) % 6) * 51
                b = (code % 6) * 51
                return f"#{r:02x}{g:02x}{b:02x}"
            else:
                # Grayscale (24 shades)
                gray = (code - 232) * 10 + 8
                return f"#{gray:02x}{gray:02x}{gray:02x}"
        except (ValueError, TypeError):
            pass

        return self.ANSI_COLORS["default"]

    def screenshot(
        self,
        path: str | Path,
        font_size: int = 14,
        bg_color: str = "#1a1a2e",
        fg_color: str = "#eaeaea",
    ) -> Path:
        """Render terminal content to a PNG image with colors.

        Args:
            path: Output path for the PNG file
            font_size: Font size in pixels
            bg_color: Background color (hex)
            fg_color: Default foreground/text color (hex)

        Returns:
            Path to the created image
        """
        self._read_output()
        path = Path(path)

        # Try to load a monospace font with good Unicode support
        font = None
        font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/UbuntuMono[wght].ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            # macOS
            "/System/Library/Fonts/Monaco.ttf",
            "/System/Library/Fonts/Menlo.ttc",
        ]
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except (OSError, IOError):
                continue

        if font is None:
            font = ImageFont.load_default()

        # Get actual character dimensions using the font
        bbox = font.getbbox("M")
        char_width = bbox[2] - bbox[0]
        char_height = int(font_size * 1.4)  # Line height
        padding = 12

        img_width = int(self.cols * char_width + padding * 2)
        img_height = int(self.rows * char_height + padding * 2)

        # Create image with dark background
        img = Image.new("RGB", (img_width, img_height), bg_color)
        draw = ImageDraw.Draw(img)

        # Render each character with its color
        for row in range(self.rows):
            y = padding + row * char_height
            for col in range(self.cols):
                char = self._screen.buffer[row][col]
                x = padding + col * char_width

                # Get character data
                char_data = char.data if char.data else " "

                # Get foreground color
                fg = char.fg if hasattr(char, "fg") else "default"
                bold = char.bold if hasattr(char, "bold") else False
                char_color = self._color_to_rgb(fg, bold) if fg else fg_color

                # Get background color if set
                bg = char.bg if hasattr(char, "bg") else None
                if bg and bg != "default":
                    bg_rgb = self._color_to_rgb(bg)
                    draw.rectangle(
                        [x, y, x + char_width, y + char_height],
                        fill=bg_rgb,
                    )

                # Draw character
                if char_data.strip():
                    draw.text((x, y), char_data, font=font, fill=char_color)

        # Save
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(path))
        return path

    def __enter__(self) -> "SubprocessTerminal":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def run_terminal_test(
    command: str,
    actions: List[Tuple[str, str | float]],
    screenshot_path: Optional[str] = None,
    timeout: float = 10.0,
    rows: int = 24,
    cols: int = 80,
) -> str:
    """Run a quick terminal test with a sequence of actions.

    Args:
        command: Command to run
        actions: List of (action_type, value) tuples:
            - ("wait", "text") - wait for text
            - ("keys", "↓↓\\n") - send keys
            - ("text", "hello") - send plain text
            - ("delay", 0.5) - sleep for seconds
            - ("assert", "text") - assert text is present
            - ("assert_not", "text") - assert text is not present
        screenshot_path: Optional path to save screenshot
        timeout: Timeout for starting and waiting
        rows: Terminal height
        cols: Terminal width

    Returns:
        Final terminal content as text

    Example:
        content = run_terminal_test(
            "poetry run rawgui",
            [
                ("wait", "Welcome"),
                ("keys", "↓↓↓\\n"),
                ("delay", 0.5),
                ("assert", "Selected"),
            ],
            screenshot_path="test_output.png",
        )
    """
    with SubprocessTerminal(command, rows=rows, cols=cols) as term:
        for action_type, value in actions:
            if action_type == "wait":
                if not term.wait_for_text(str(value), timeout=timeout):
                    raise TimeoutError(f"Timeout waiting for text: {value}")
            elif action_type == "keys":
                term.send_keys(str(value))
            elif action_type == "text":
                term.send_text(str(value))
            elif action_type == "delay":
                time.sleep(float(value))
            elif action_type == "assert":
                term.should_contain(str(value))
            elif action_type == "assert_not":
                term.should_not_contain(str(value))

        if screenshot_path:
            term.screenshot(screenshot_path)

        return term.get_text()
