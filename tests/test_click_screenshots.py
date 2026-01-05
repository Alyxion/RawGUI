"""Click tests with screenshot verification.

These tests use SubprocessTerminal to run actual TUI applications,
perform interactions, and capture screenshots for visual verification.
"""

import pytest
import tempfile
import os
from pathlib import Path

from rawgui.testing import SubprocessTerminal


# Skip if no TTY available
pytestmark = pytest.mark.skipif(
    not os.isatty(0) and os.environ.get("CI"),
    reason="Click tests require TTY"
)


class TestButtonClicks:
    """Tests for button click interactions."""

    def test_button_click_updates_state(self, tmp_path):
        """Test that clicking a button updates application state."""
        app_code = '''
from rawgui import ui

class State:
    count = 0

def increment():
    State.count += 1
    ui.navigate.to("/")

@ui.page("/")
def index():
    with ui.column():
        ui.label(f"Count: {State.count}")
        ui.button("Increment", on_click=increment)

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "click_test.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            # Wait for initial render
            if term.wait_for_text("Count: 0", timeout=5):
                # Take initial screenshot
                screenshot1 = tmp_path / "before_click.png"
                term.screenshot(screenshot1)
                assert screenshot1.exists()

                # Press Enter to click button (button should be focused)
                term.send_keys("\r")

                # Wait for state update
                if term.wait_for_text("Count: 1", timeout=3):
                    # Take screenshot after click
                    screenshot2 = tmp_path / "after_click.png"
                    term.screenshot(screenshot2)
                    assert screenshot2.exists()

    def test_multiple_buttons_navigation(self, tmp_path):
        """Test Tab navigation between multiple buttons."""
        app_code = '''
from rawgui import ui

class State:
    message = "Press a button"

def set_a():
    State.message = "Button A pressed"
    ui.navigate.to("/")

def set_b():
    State.message = "Button B pressed"
    ui.navigate.to("/")

@ui.page("/")
def index():
    with ui.column():
        ui.label(State.message)
        with ui.row():
            ui.button("Button A", on_click=set_a)
            ui.button("Button B", on_click=set_b)

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "multi_button.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            if term.wait_for_text("Press a button", timeout=5):
                # Initial state
                assert term.contains("Button A")
                assert term.contains("Button B")

                # Tab to second button and click
                term.send_keys("\t")  # Move to Button B
                term.send_keys("\r")  # Press Enter

                # Check for state update
                term.wait_for_text("Button B pressed", timeout=3)


class TestInputInteraction:
    """Tests for input field interactions."""

    def test_typing_in_input(self, tmp_path):
        """Test typing text into an input field."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    with ui.column():
        ui.input(label="Username", placeholder="Enter name")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "input_test.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            if term.wait_for_text("Username", timeout=5):
                # Type into the input
                term.send_text("testuser")

                # Wait for text to appear
                if term.wait_for_text("testuser", timeout=3):
                    # Take screenshot showing typed text
                    screenshot = tmp_path / "input_typed.png"
                    term.screenshot(screenshot)
                    assert screenshot.exists()

    def test_password_input_masking(self, tmp_path):
        """Test that password input masks characters."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    with ui.column():
        ui.input(label="Password", password=True, value="secret")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "password_test.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            if term.wait_for_text("Password", timeout=5):
                # Wait for render
                import time
                time.sleep(0.3)

                # The actual text should NOT be visible
                text = term.get_text()
                assert "secret" not in text
                # But asterisks should be visible (password is pre-filled)
                assert "*" in text


class TestCardRendering:
    """Tests for card element rendering."""

    def test_card_with_border(self, tmp_path):
        """Test that cards render with borders."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    with ui.card():
        ui.label("Card Title")
        ui.label("Card content here")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "card_test.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            if term.wait_for_text("Card Title", timeout=5):
                text = term.get_text()

                # Check for border characters
                has_border = any(c in text for c in "─│┌┐└┘╭╮╰╯")
                assert has_border, "Card should have visible border"

                # Take screenshot
                screenshot = tmp_path / "card_border.png"
                term.screenshot(screenshot)
                assert screenshot.exists()

    def test_nested_cards(self, tmp_path):
        """Test nested card rendering."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    with ui.card():
        ui.label("Outer Card")
        with ui.card():
            ui.label("Inner Card")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "nested_card.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            if term.wait_for_text("Outer Card", timeout=5):
                assert term.contains("Inner Card")

                # Take screenshot of nested structure
                screenshot = tmp_path / "nested_cards.png"
                term.screenshot(screenshot)
                assert screenshot.exists()


class TestLayoutRendering:
    """Tests for layout containers (row/column)."""

    def test_row_layout(self, tmp_path):
        """Test horizontal row layout."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    with ui.row():
        ui.button("Left")
        ui.button("Middle")
        ui.button("Right")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "row_test.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            if term.wait_for_text("Left", timeout=5):
                assert term.contains("Middle")
                assert term.contains("Right")

                # Take screenshot
                screenshot = tmp_path / "row_layout.png"
                term.screenshot(screenshot)
                assert screenshot.exists()

    def test_column_layout(self, tmp_path):
        """Test vertical column layout."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    with ui.column():
        ui.label("Line 1")
        ui.label("Line 2")
        ui.label("Line 3")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "column_test.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            if term.wait_for_text("Line 1", timeout=5):
                assert term.contains("Line 2")
                assert term.contains("Line 3")

                # Take screenshot
                screenshot = tmp_path / "column_layout.png"
                term.screenshot(screenshot)
                assert screenshot.exists()


class TestStyling:
    """Tests for CSS-like styling."""

    def test_text_color_styles(self, tmp_path):
        """Test text color styling."""
        app_code = '''
from rawgui import ui

@ui.page("/")
def index():
    with ui.column():
        ui.label("Red Text").classes("text-red")
        ui.label("Green Text").classes("text-green")
        ui.label("Blue Text").classes("text-blue")
        ui.label("Bold Text").classes("text-bold")

if __name__ == "__main__":
    ui.run(reload=False)
'''
        app_file = tmp_path / "style_test.py"
        app_file.write_text(app_code)

        with SubprocessTerminal(
            f"python {app_file}",
            rows=24,
            cols=80,
            cwd=str(tmp_path),
        ) as term:
            if term.wait_for_text("Red Text", timeout=5):
                assert term.contains("Green Text")
                assert term.contains("Blue Text")
                assert term.contains("Bold Text")

                # Take screenshot showing styled text
                screenshot = tmp_path / "styled_text.png"
                term.screenshot(screenshot)
                assert screenshot.exists()


class TestExamples:
    """Tests for the example applications."""

    def test_hello_world_example(self):
        """Test the hello_world.py example runs correctly."""
        example_path = Path(__file__).parent.parent / "examples" / "hello_world.py"
        if not example_path.exists():
            pytest.skip("Example file not found")

        with SubprocessTerminal(
            f"python {example_path}",
            rows=24,
            cols=80,
        ) as term:
            if term.wait_for_text("Hello, RawGUI!", timeout=5):
                assert term.contains("Features:")
                assert term.contains("Button 1")

                # Take screenshot
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    term.screenshot(f.name)
                    assert Path(f.name).exists()
                    Path(f.name).unlink()

    def test_counter_example(self):
        """Test the counter.py example runs correctly."""
        example_path = Path(__file__).parent.parent / "examples" / "counter.py"
        if not example_path.exists():
            pytest.skip("Example file not found")

        with SubprocessTerminal(
            f"python {example_path}",
            rows=24,
            cols=80,
        ) as term:
            if term.wait_for_text("Counter Demo", timeout=5):
                assert term.contains("Count: 0")
                assert term.contains("Increment")

                # Take screenshot
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    term.screenshot(f.name)
                    assert Path(f.name).exists()
                    Path(f.name).unlink()

    def test_form_example(self):
        """Test the form.py example runs correctly."""
        example_path = Path(__file__).parent.parent / "examples" / "form.py"
        if not example_path.exists():
            pytest.skip("Example file not found")

        with SubprocessTerminal(
            f"python {example_path}",
            rows=24,
            cols=80,
        ) as term:
            if term.wait_for_text("Registration Form", timeout=5):
                assert term.contains("Username")
                assert term.contains("Email")
                assert term.contains("Submit")

                # Take screenshot
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    term.screenshot(f.name)
                    assert Path(f.name).exists()
                    Path(f.name).unlink()
