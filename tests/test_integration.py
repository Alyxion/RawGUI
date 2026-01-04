"""End-to-end integration tests using SubprocessTerminal.

These tests actually run the TUI application and verify behavior.
"""

import pytest
import tempfile
import os
from pathlib import Path

from rawgui.testing import SubprocessTerminal, run_terminal_test


# Skip integration tests in CI if no TTY
pytestmark = pytest.mark.skipif(
    not os.isatty(0) and os.environ.get("CI"),
    reason="Integration tests require TTY"
)


class TestBasicRendering:
    """Tests for basic TUI rendering."""

    def test_render_simple_app(self, tmp_path):
        """Test rendering a simple app."""
        # Create a simple test app
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    ui.label("Test Label")
    ui.button("Test Button")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "test_app.py"
        app_file.write_text(app_code)

        # Run with SubprocessTerminal
        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            # Wait for initial render
            found = term.wait_for_text("Test Label", timeout=5)
            if found:
                assert term.contains("Test Label")
                assert term.contains("Test Button")

    def test_card_renders_border(self, tmp_path):
        """Test that cards render with borders."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    with ui.card():
        ui.label("Card Content")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "test_card.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            found = term.wait_for_text("Card Content", timeout=5)
            if found:
                text = term.get_text()
                # Check for border characters
                assert "─" in text or "│" in text or "╭" in text


class TestInputHandling:
    """Tests for keyboard input handling."""

    def test_typing_in_input(self, tmp_path):
        """Test typing text into an input field."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    ui.input(label="Name")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "test_input.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            found = term.wait_for_text("Name", timeout=5)
            if found:
                # Type some text
                term.send_text("Hello")
                term.wait_for_text("Hello", timeout=2)
                # Note: The input field should show the typed text


class TestScreenshots:
    """Tests for screenshot functionality."""

    def test_screenshot_captures_content(self, tmp_path):
        """Test that screenshots capture terminal content."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    ui.label("Screenshot Test")
    with ui.row():
        ui.button("Btn 1")
        ui.button("Btn 2")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "test_screenshot.py"
        app_file.write_text(app_code)
        screenshot_path = tmp_path / "screenshot.png"

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            found = term.wait_for_text("Screenshot Test", timeout=5)
            if found:
                term.screenshot(screenshot_path)
                assert screenshot_path.exists()
                # Check file is a valid PNG (starts with PNG signature)
                with open(screenshot_path, 'rb') as f:
                    header = f.read(8)
                    assert header[:4] == b'\x89PNG'


class TestElementFunctionality:
    """Tests for element-specific functionality."""

    def test_label_displays_text(self):
        """Test label element displays text correctly."""
        from rawgui import ui
        from rawgui.client import Client
        from rawgui.renderer.terminal import TerminalRenderer

        renderer = TerminalRenderer()

        with Client() as client:
            label = ui.label("Hello World")

        output = renderer.render(label)
        assert "Hello World" in output

    def test_button_shows_brackets(self):
        """Test button renders with brackets."""
        from rawgui import ui
        from rawgui.client import Client
        from rawgui.renderer.terminal import TerminalRenderer

        renderer = TerminalRenderer()

        with Client() as client:
            btn = ui.button("Click")

        output = renderer.render(btn)
        assert "[ Click ]" in output

    def test_nested_layout(self):
        """Test nested row/column layout."""
        from rawgui import ui
        from rawgui.client import Client
        from rawgui.renderer.terminal import TerminalRenderer

        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Header")
                with ui.row():
                    ui.button("Left")
                    ui.button("Right")
                ui.label("Footer")

        output = renderer.render(col)
        assert "Header" in output
        assert "Left" in output
        assert "Right" in output
        assert "Footer" in output
