"""Tests for user interaction simulation.

Tests click and keyboard interactions with the counter example
using both TUI and Tkinter renderers.
"""

import pytest
from pathlib import Path

from rawgui.testing import User, TkinterUser, TUIUser, compare_images


class TestTkinterUserInteraction:
    """Test user interactions with Tkinter renderer."""

    def test_click_increment_button(self):
        """Test clicking the increment button updates counter."""
        with User("examples/counter.py", renderer="tkinter") as user:
            # Verify initial state
            assert user.contains("Count: 0"), "Initial count should be 0"

            # Find and click the increment button
            increment_btn = user.find_by_text("+ Increment")
            assert increment_btn is not None, "Increment button should exist"

            # Click fires the action immediately
            user.click_element(increment_btn)

            # Verify counter incremented
            assert user.contains("Count: 1"), f"Count should be 1 after increment. Got: {user.get_text()}"

    def test_click_increment_twice(self):
        """Test clicking increment button twice."""
        with User("examples/counter.py", renderer="tkinter") as user:
            increment_btn = user.find_by_text("+ Increment")

            # Each click fires the event
            user.click_element(increment_btn)
            assert user.contains("Count: 1")

            user.click_element(increment_btn)
            assert user.contains("Count: 2"), f"Count should be 2. Got: {user.get_text()}"

    def test_space_key_activates_button(self):
        """Test pressing Space activates focused button."""
        with User("examples/counter.py", renderer="tkinter") as user:
            # Navigate to increment button using Tab
            # Initial focus is on first button (Decrement)
            user.press_key("tab")  # Move to Reset
            user.press_key("tab")  # Move to Increment

            # Press space to activate
            user.press_key("space")

            # Verify counter incremented
            assert user.contains("Count: 1"), f"Space should increment. Got: {user.get_text()}"

    def test_enter_key_activates_button(self):
        """Test pressing Enter activates focused button."""
        with User("examples/counter.py", renderer="tkinter") as user:
            # Navigate to increment button
            user.press_key("tab")
            user.press_key("tab")

            # Press enter to activate
            user.press_key("enter")

            assert user.contains("Count: 1"), f"Enter should increment. Got: {user.get_text()}"

    def test_decrement_button(self):
        """Test decrement button decreases counter."""
        with User("examples/counter.py", renderer="tkinter") as user:
            # First increment twice
            increment_btn = user.find_by_text("+ Increment")
            user.click_element(increment_btn)
            user.click_element(increment_btn)
            assert user.contains("Count: 2")

            # Now decrement twice
            decrement_btn = user.find_by_text("- Decrement")
            user.click_element(decrement_btn)
            user.click_element(decrement_btn)
            assert user.contains("Count: 0"), f"Should be back to 0. Got: {user.get_text()}"

    def test_reset_button(self):
        """Test reset button sets counter to 0."""
        with User("examples/counter.py", renderer="tkinter") as user:
            # Increment a few times
            increment_btn = user.find_by_text("+ Increment")
            for _ in range(3):
                user.click_element(increment_btn)

            assert user.contains("Count: 3")

            # Reset
            reset_btn = user.find_by_text("Reset")
            user.click_element(reset_btn)

            assert user.contains("Count: 0"), f"Reset should set to 0. Got: {user.get_text()}"

    def test_screenshot_after_interaction(self, tmp_path):
        """Test screenshot capture after interaction."""
        with User("examples/counter.py", renderer="tkinter") as user:
            # Take initial screenshot
            initial = tmp_path / "initial.png"
            user.screenshot(str(initial))
            assert initial.exists()

            # Increment
            increment_btn = user.find_by_text("+ Increment")
            user.click_element(increment_btn)

            # Take screenshot after increment
            after = tmp_path / "after.png"
            user.screenshot(str(after))
            assert after.exists()

            # Images should be different (diff > 0 means some pixels changed)
            are_equal, diff = compare_images(str(initial), str(after), threshold=0.0001)
            assert diff > 0, f"Screenshots should differ after increment (diff={diff})"

    def test_arrow_key_navigation(self):
        """Test arrow keys navigate between buttons."""
        with User("examples/counter.py", renderer="tkinter") as user:
            # Check we have buttons
            buttons = user.find_by_tag("button")
            assert len(buttons) >= 3, f"Expected 3 buttons, got {len(buttons)}"

            # Press right/tab to navigate between buttons
            user.press_key("right")
            user.press_key("right")

            # After navigating, pressing space should activate increment button
            user.press_key("space")

            # Check counter incremented
            assert user.contains("Count: 1"), f"Navigation + space should increment. Got: {user.get_text()}"

    def test_get_elements_returns_all(self):
        """Test get_elements returns all rendered elements."""
        with User("examples/counter.py", renderer="tkinter") as user:
            elements = user.get_elements()

            # Should have labels, buttons, etc.
            tags = [el.tag for el in elements]
            assert "label" in tags, "Should have labels"
            assert "button" in tags, "Should have buttons"

            # Find specific elements
            buttons = user.find_by_tag("button")
            assert len(buttons) == 3, f"Should have 3 buttons. Got {len(buttons)}"

    def test_element_coordinates(self):
        """Test elements have valid coordinates."""
        with User("examples/counter.py", renderer="tkinter") as user:
            elements = user.get_elements()

            for el in elements:
                assert el.x >= 0, f"Element {el.tag} has negative x"
                assert el.y >= 0, f"Element {el.tag} has negative y"
                assert el.width > 0, f"Element {el.tag} has zero width"
                assert el.height > 0, f"Element {el.tag} has zero height"


class TestTUIUserInteraction:
    """Test user interactions with TUI renderer."""

    def test_tui_contains_text(self):
        """Test TUI shows expected text."""
        with User("examples/counter.py", renderer="tui") as user:
            user.wait_for_text("Counter Demo", timeout=3.0)
            assert user.contains("Count: 0")
            assert user.contains("Decrement")
            assert user.contains("Increment")

    def test_tui_keyboard_navigation(self):
        """Test keyboard navigation in TUI."""
        with User("examples/counter.py", renderer="tui") as user:
            user.wait_for_text("Counter Demo", timeout=3.0)

            # Tab to navigate
            user.press_key("tab")
            user.press_key("tab")

            # Press space to activate (increment)
            user.press_key("space")

            # Wait for re-render
            import time
            time.sleep(0.5)

            # Check counter updated
            assert user.contains("Count: 1"), f"TUI should show Count: 1. Got: {user.get_text()}"

    def test_tui_screenshot(self, tmp_path):
        """Test TUI screenshot capture."""
        with User("examples/counter.py", renderer="tui") as user:
            user.wait_for_text("Counter Demo", timeout=3.0)

            screenshot_path = tmp_path / "tui_counter.png"
            user.screenshot(str(screenshot_path))

            assert screenshot_path.exists(), "Screenshot should be saved"


class TestCrossRendererParity:
    """Test that both renderers produce similar results."""

    def test_both_show_same_initial_content(self):
        """Test both renderers show same initial content."""
        with User("examples/counter.py", renderer="tkinter") as tk_user:
            with User("examples/counter.py", renderer="tui") as tui_user:
                tui_user.wait_for_text("Counter Demo", timeout=3.0)

                # Both should show Count: 0
                assert tk_user.contains("Count: 0")
                assert tui_user.contains("Count: 0")

                # Both should have increment/decrement text
                assert tk_user.contains("Increment")
                assert tui_user.contains("Increment")

    def test_both_increment_correctly(self):
        """Test both renderers increment counter the same way."""
        # Tkinter - click increments
        with User("examples/counter.py", renderer="tkinter") as user:
            btn = user.find_by_text("+ Increment")
            user.click_element(btn)
            assert user.contains("Count: 1"), f"Tkinter count wrong: {user.get_text()}"

        # TUI - keyboard navigation + space increments
        with User("examples/counter.py", renderer="tui") as user:
            user.wait_for_text("Counter Demo", timeout=3.0)
            user.press_key("tab")
            user.press_key("tab")
            user.press_key("space")
            import time
            time.sleep(0.5)
            assert user.contains("Count: 1"), f"TUI count wrong: {user.get_text()}"
