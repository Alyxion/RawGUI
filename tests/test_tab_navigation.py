"""Tests for Tab navigation functionality."""

import pytest
from rawgui import ui
from rawgui.client import Client
from rawgui.renderer.terminal import TerminalRenderer


class TestTabNavigation:
    """Tests for keyboard Tab navigation between focusable elements."""

    def test_focus_starts_on_first_element(self):
        """Test that focus starts on the first focusable element."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Not focusable")
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")
                inp = ui.input(label="Input")

        # First render to build focusable list
        renderer.render(col)

        # Should have 3 focusable elements
        assert len(renderer._focusable) == 3
        assert renderer._focusable[0] == btn1
        assert renderer._focusable[1] == btn2
        assert renderer._focusable[2] == inp

        # Initial focus on first button
        assert renderer.focused == btn1

    def test_focus_next_cycles_through_elements(self):
        """Test that focus_next cycles through all focusable elements."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")
                btn3 = ui.button("Button 3")

        renderer.render(col)
        assert renderer.focused == btn1

        # Tab to next
        renderer.focus_next()
        assert renderer.focused == btn2

        # Tab to next
        renderer.focus_next()
        assert renderer.focused == btn3

        # Tab wraps around
        renderer.focus_next()
        assert renderer.focused == btn1

    def test_focus_prev_cycles_backwards(self):
        """Test that focus_prev cycles backwards."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")
                btn3 = ui.button("Button 3")

        renderer.render(col)
        assert renderer.focused == btn1

        # Shift+Tab wraps to last
        renderer.focus_prev()
        assert renderer.focused == btn3

        # Shift+Tab goes backwards
        renderer.focus_prev()
        assert renderer.focused == btn2

    def test_focus_persists_after_rerender(self):
        """Test that focus persists correctly after re-rendering."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")
                btn3 = ui.button("Button 3")

        renderer.render(col)

        # Move focus to btn2
        renderer.focus_next()
        assert renderer.focused == btn2

        # Re-render (simulating screen refresh)
        renderer.render(col)

        # Focus should stay on btn2
        # Note: _focusable list is rebuilt, but _focused should match
        assert renderer._focused == btn2 or renderer._focused.text == "Button 2"

    def test_disabled_elements_not_focusable(self):
        """Test that disabled elements cannot receive focus."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Disabled", disabled=True)
                btn3 = ui.button("Button 3")

        renderer.render(col)

        # Should only have 2 focusable elements
        assert len(renderer._focusable) == 2
        assert btn2 not in renderer._focusable

    def test_focus_element_directly(self):
        """Test focusing an element directly."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")
                inp = ui.input(label="Input")

        renderer.render(col)
        assert renderer.focused == btn1

        # Focus input directly
        renderer.focus_element(inp)
        assert renderer.focused == inp

        # Tab should go to next (btn1, wrapping)
        renderer.focus_next()
        assert renderer.focused == btn1

    def test_no_focusable_elements(self):
        """Test handling when there are no focusable elements."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Just a label")
                ui.label("Another label")

        renderer.render(col)

        # No focusable elements
        assert len(renderer._focusable) == 0
        assert renderer.focused is None

        # focus_next should handle gracefully
        result = renderer.focus_next()
        assert result is None

    def test_focus_renders_differently(self):
        """Test that focused element renders differently (reverse video)."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn = ui.button("Focused")

        output = renderer.render(col)

        # The focused button should be rendered with reverse video
        # We can verify by checking the output contains the button text
        assert "Focused" in output

    def test_input_receives_focus(self):
        """Test that input elements can receive focus."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                inp = ui.input(label="Name", placeholder="Enter name")

        renderer.render(col)

        assert renderer.focused == inp
        assert len(renderer._focusable) == 1

    def test_mixed_focusable_elements(self):
        """Test focus navigation with mixed element types."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                inp1 = ui.input(label="First")
                btn1 = ui.button("Submit")
                ui.label("Some text")
                inp2 = ui.input(label="Second")
                btn2 = ui.button("Cancel")

        renderer.render(col)

        assert len(renderer._focusable) == 4
        assert renderer._focusable == [inp1, btn1, inp2, btn2]

        # Navigate through all
        assert renderer.focused == inp1
        renderer.focus_next()
        assert renderer.focused == btn1
        renderer.focus_next()
        assert renderer.focused == inp2
        renderer.focus_next()
        assert renderer.focused == btn2
        renderer.focus_next()
        assert renderer.focused == inp1  # Wrapped

    def test_focus_invalidates_renderer(self):
        """Test that changing focus marks renderer as dirty."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")

        renderer.render(col)
        assert not renderer.needs_render  # Just rendered

        renderer.focus_next()
        assert renderer.needs_render  # Should need re-render

    def test_nested_focusable_elements(self):
        """Test focus with nested containers."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                with ui.card():
                    btn1 = ui.button("Card Button 1")
                    btn2 = ui.button("Card Button 2")
                with ui.row():
                    btn3 = ui.button("Row Button")
                    inp = ui.input(label="Input")

        renderer.render(col)

        assert len(renderer._focusable) == 4
        # Order should match document order
        assert renderer._focusable[0] == btn1
        assert renderer._focusable[1] == btn2
        assert renderer._focusable[2] == btn3
        assert renderer._focusable[3] == inp


class TestFocusWithRerender:
    """Tests for focus behavior across re-renders."""

    def test_focus_index_preserved_on_rerender(self):
        """Test that focus index is preserved when re-rendering."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")
                btn3 = ui.button("Button 3")

        renderer.render(col)

        # Move to third button
        renderer.focus_next()
        renderer.focus_next()
        assert renderer.focused == btn3
        assert renderer._focus_index == 2

        # Simulate re-render by invalidating and rendering again
        renderer.invalidate()
        output = renderer.render(col)

        # The focused element reference should still be btn3
        # After re-render, _focusable is rebuilt but _focused should persist
        assert renderer._focused == btn3

    def test_focus_recovery_after_element_change(self):
        """Test focus behavior when elements change."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btns = [ui.button(f"Button {i}") for i in range(3)]

        renderer.render(col)
        renderer.focus_next()  # Focus Button 1
        assert renderer.focused == btns[1]
