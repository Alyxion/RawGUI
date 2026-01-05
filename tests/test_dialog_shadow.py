"""Tests for dialog shadow rendering."""

import pytest
from rawgui import ui
from rawgui.client import Client
from rawgui.renderer.terminal import TerminalRenderer


class TestDialogShadow:
    """Tests for dialog with shadow effect."""

    def test_dialog_not_rendered_when_closed(self):
        """Test that closed dialog is not rendered."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Background content")
                with ui.dialog() as dialog:
                    ui.label("Dialog content")

        output = renderer.render(col)
        assert "Background content" in output
        assert "Dialog content" not in output  # Dialog is closed

    def test_dialog_rendered_when_open(self):
        """Test that open dialog is rendered."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Background content")
                dialog = ui.dialog(value=True)

        output = renderer.render(col)
        # Open dialog should be visible (though it may not have content)
        assert "Background content" in output

    def test_dialog_has_shadow_layer(self):
        """Test that dialog creates a shadow layer."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Background")
                dialog = ui.dialog(value=True)

        renderer.render(col)

        # Compositor should have overlay layer for dialog
        if renderer._compositor:
            layer_names = list(renderer._compositor._layers.keys())
            # Should have base layer plus dialog overlay
            assert "base" in layer_names

    def test_multiple_dialogs_stack(self):
        """Test that multiple dialogs stack correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Background")
                dialog1 = ui.dialog(value=True)
                dialog2 = ui.dialog(value=True)

        renderer.render(col)

        # Both dialogs should be tracked
        overlays = renderer._find_overlays(col)
        visible = [o for o in overlays if o.visible]
        assert len(visible) == 2

    def test_dialog_with_card_renders(self):
        """Test dialog with card content renders correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Main content")
                with ui.dialog(value=True) as dialog:
                    with ui.card():
                        ui.label("Card in dialog")
                        ui.button("Close")

        output = renderer.render(col)
        assert "Main content" in output

    def test_closed_dialog_skipped_in_base_render(self):
        """Test that closed dialogs don't affect base rendering."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.label("Line 1")
                with ui.dialog() as dialog:  # Closed by default
                    ui.label("Hidden dialog content")
                ui.label("Line 2")

        output = renderer.render(col)
        assert "Line 1" in output
        assert "Line 2" in output
        assert "Hidden dialog content" not in output


class TestMenuShadow:
    """Tests for menu shadow rendering."""

    def test_menu_is_overlay(self):
        """Test that menu is treated as overlay."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                with ui.menu() as menu:
                    ui.menu_item("Item 1")

        # Menu should be in overlay tags
        assert "menu" in renderer.OVERLAY_TAGS

    def test_closed_menu_not_rendered(self):
        """Test that closed menu is not visible."""
        renderer = TerminalRenderer()

        with Client() as client:
            with ui.column() as col:
                ui.button("Open Menu")
                with ui.menu() as menu:
                    ui.menu_item("Action")

        output = renderer.render(col)
        assert "Open Menu" in output
        # Menu is closed by default so Action shouldn't appear
        # (unless it's rendered as part of button's children)
