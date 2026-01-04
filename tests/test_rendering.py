"""Tests for terminal rendering functionality."""

import pytest
from rawgui import ui
from rawgui.client import Client
from rawgui.renderer.terminal import TerminalRenderer
from rawgui.renderer.styles import StyleMapper, TerminalStyle


class TestStyleMapper:
    """Tests for style mapping."""

    def test_text_bold_class(self):
        """Test text-bold class is recognized."""
        mapper = StyleMapper()
        style = mapper.map_classes(["text-bold"])
        assert style.bold is True

    def test_font_bold_class(self):
        """Test font-bold class is recognized."""
        mapper = StyleMapper()
        style = mapper.map_classes(["font-bold"])
        assert style.bold is True

    def test_padding_all_sides(self):
        """Test p-2 applies padding to all sides."""
        mapper = StyleMapper()
        style = mapper.map_classes(["p-2"])
        assert style.padding_top == 2
        assert style.padding_right == 2
        assert style.padding_bottom == 2
        assert style.padding_left == 2

    def test_padding_x(self):
        """Test px-4 applies horizontal padding."""
        mapper = StyleMapper()
        style = mapper.map_classes(["px-4"])
        assert style.padding_left == 4
        assert style.padding_right == 4
        assert style.padding_top == 0
        assert style.padding_bottom == 0

    def test_gap_class(self):
        """Test gap-2 is parsed correctly."""
        mapper = StyleMapper()
        style = mapper.map_classes(["gap-2"])
        assert style.gap == 2

    def test_text_color_simple(self):
        """Test text-red sets foreground color."""
        mapper = StyleMapper()
        style = mapper.map_classes(["text-red"])
        assert style.fg_color == "red"

    def test_text_color_with_shade(self):
        """Test text-red-500 sets foreground color."""
        mapper = StyleMapper()
        style = mapper.map_classes(["text-red-500"])
        assert style.fg_color == "red"

    def test_bg_color(self):
        """Test bg-blue sets background color."""
        mapper = StyleMapper()
        style = mapper.map_classes(["bg-blue"])
        assert style.bg_color == "blue"

    def test_border_class(self):
        """Test border class."""
        mapper = StyleMapper()
        style = mapper.map_classes(["border"])
        assert style.border is True

    def test_multiple_classes(self):
        """Test multiple classes combined."""
        mapper = StyleMapper()
        style = mapper.map_classes(["text-bold", "text-red", "p-2", "gap-1"])
        assert style.bold is True
        assert style.fg_color == "red"
        assert style.padding_top == 2
        assert style.gap == 1


class TestTerminalRenderer:
    """Tests for terminal renderer."""

    def test_render_label(self):
        """Test rendering a simple label."""
        renderer = TerminalRenderer()

        with Client() as client:
            label = ui.label("Hello World")

        output = renderer.render(label)
        assert "Hello World" in output

    def test_render_button(self):
        """Test rendering a button."""
        renderer = TerminalRenderer()

        with Client() as client:
            btn = ui.button("Click Me")

        output = renderer.render(btn)
        assert "Click Me" in output
        assert "[" in output  # Button brackets

    def test_render_column_with_children(self):
        """Test rendering a column with children."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Line 1")
                ui.label("Line 2")

        output = renderer.render(col)
        assert "Line 1" in output
        assert "Line 2" in output

    def test_render_row_with_children(self):
        """Test rendering a row with children."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.row() as row:
                ui.label("Left")
                ui.label("Right")

        output = renderer.render(row)
        assert "Left" in output
        assert "Right" in output

    def test_render_card(self):
        """Test rendering a card with border."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.card() as card:
                ui.label("Card Content")

        output = renderer.render(card)
        assert "Card Content" in output
        # Check for border characters
        assert "─" in output or "│" in output  # Border chars

    def test_focus_tracking(self):
        """Test that focusable elements are tracked."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")
                inp = ui.input(label="Input")

        renderer.render(col)

        # Should have 3 focusable elements
        assert len(renderer._focusable) == 3
        assert btn1 in renderer._focusable
        assert btn2 in renderer._focusable
        assert inp in renderer._focusable

    def test_focus_navigation(self):
        """Test Tab navigation between elements."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                btn1 = ui.button("Button 1")
                btn2 = ui.button("Button 2")

        renderer.render(col)

        # Initial focus should be on first element
        assert renderer.focused == btn1

        # Tab to next
        renderer.focus_next()
        assert renderer.focused == btn2

        # Tab wraps around
        renderer.focus_next()
        assert renderer.focused == btn1

        # Shift+Tab goes back
        renderer.focus_prev()
        assert renderer.focused == btn2


class TestInputElement:
    """Tests for input element rendering and interaction."""

    def test_input_with_label(self):
        """Test input renders with label."""
        renderer = TerminalRenderer()

        with Client() as client:
            inp = ui.input(label="Name")

        output = renderer.render(inp)
        assert "Name" in output

    def test_input_with_value(self):
        """Test input displays value."""
        renderer = TerminalRenderer()

        with Client() as client:
            inp = ui.input(value="test value")

        output = renderer.render(inp)
        assert "test value" in output

    def test_input_with_placeholder(self):
        """Test input shows placeholder when empty."""
        renderer = TerminalRenderer()

        with Client() as client:
            inp = ui.input(placeholder="Enter text...")

        output = renderer.render(inp)
        assert "Enter text..." in output

    def test_password_input_masks_value(self):
        """Test password input masks the value."""
        renderer = TerminalRenderer()

        with Client() as client:
            inp = ui.input(value="secret", password=True)

        output = renderer.render(inp)
        assert "secret" not in output
        assert "******" in output  # Should be masked


class TestElementInteraction:
    """Tests for element event handling."""

    def test_button_click_fires_event(self):
        """Test button click triggers handler."""
        clicked = []

        with Client() as client:
            btn = ui.button("Click", on_click=lambda: clicked.append(True))

        btn._fire_event("click")
        assert clicked == [True]

    def test_input_change_fires_event(self):
        """Test input change triggers handler."""
        values = []

        with Client() as client:
            inp = ui.input(on_change=lambda v: values.append(v))

        inp.value = "new value"
        inp._fire_event("change", "new value")
        assert values == ["new value"]

    def test_disabled_button_styling(self):
        """Test disabled button has different style."""
        renderer = TerminalRenderer()

        with Client() as client:
            btn = ui.button("Disabled")
            btn.disable()

        output = renderer.render(btn)
        assert "Disabled" in output
        # Note: Visual styling test - disabled should look different
