"""Tests for checkbox component."""

import pytest
from rawgui import ui
from rawgui.client import Client
from rawgui.renderer.terminal import TerminalRenderer


class TestCheckbox:
    """Tests for checkbox element."""

    def test_create_checkbox(self):
        """Test creating a basic checkbox."""
        with Client() as client:
            cb = ui.checkbox("Accept terms")

        assert cb.text == "Accept terms"
        assert cb.value is False
        assert cb.tag == "checkbox"

    def test_checkbox_with_value(self):
        """Test checkbox with initial value."""
        with Client() as client:
            cb = ui.checkbox("Remember me", value=True)

        assert cb.value is True

    def test_checkbox_toggle(self):
        """Test toggling checkbox."""
        with Client() as client:
            cb = ui.checkbox("Toggle me")

        assert cb.value is False
        cb.toggle()
        assert cb.value is True
        cb.toggle()
        assert cb.value is False

    def test_checkbox_change_handler(self):
        """Test checkbox change callback."""
        values = []

        with Client() as client:
            cb = ui.checkbox("Track", on_change=lambda v: values.append(v))

        cb.toggle()
        assert values == [True]

        cb.toggle()
        assert values == [True, False]

    def test_checkbox_renders(self):
        """Test checkbox renders correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            cb = ui.checkbox("My Option", value=False)

        output = renderer.render(cb)
        assert "My Option" in output
        assert "[ ]" in output  # Unchecked

    def test_checkbox_checked_renders(self):
        """Test checked checkbox renders with x."""
        renderer = TerminalRenderer()

        with Client() as client:
            cb = ui.checkbox("Checked", value=True)

        output = renderer.render(cb)
        assert "Checked" in output
        assert "[x]" in output  # Checked

    def test_checkbox_focusable(self):
        """Test checkbox can receive focus."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn = ui.button("Button")
                cb = ui.checkbox("Checkbox")

        renderer.render(col)

        assert cb in renderer._focusable
        assert renderer.focused == btn  # First element

        renderer.focus_next()
        assert renderer.focused == cb

    def test_disabled_checkbox(self):
        """Test disabled checkbox behavior."""
        with Client() as client:
            cb = ui.checkbox("Disabled")
            cb.disable()

        assert cb.enabled is False

        # Toggle should not work when disabled
        cb.toggle()
        assert cb.value is False  # Still false

    def test_checkbox_in_form(self):
        """Test checkbox in a form layout."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Settings")
                ui.checkbox("Enable notifications", value=True)
                ui.checkbox("Dark mode", value=False)
                ui.checkbox("Remember login", value=True)

        output = renderer.render(col)
        assert "Enable notifications" in output
        assert "Dark mode" in output
        assert "Remember login" in output
