"""Tests for RawGUI UI elements."""

import pytest
from rawgui import ui
from rawgui.context import context
from rawgui.client import Client


class TestLabel:
    """Tests for Label element."""

    def test_create_label(self):
        """Test creating a label with text."""
        label = ui.label("Hello World")
        assert label.text == "Hello World"
        assert label.tag == "label"

    def test_label_classes(self):
        """Test adding classes to a label."""
        label = ui.label("Test").classes("text-bold text-red-500")
        assert "text-bold" in label._classes
        assert "text-red-500" in label._classes

    def test_label_style(self):
        """Test adding inline styles."""
        label = ui.label("Test").style("color: red; font-size: 14px")
        assert label._style["color"] == "red"
        assert label._style["font-size"] == "14px"


class TestButton:
    """Tests for Button element."""

    def test_create_button(self):
        """Test creating a button."""
        button = ui.button("Click me")
        assert button.text == "Click me"
        assert button.tag == "button"
        assert button.enabled is True

    def test_button_click_handler(self):
        """Test button click handler."""
        clicked = []
        button = ui.button("Click", on_click=lambda: clicked.append(True))
        button.click()
        assert clicked == [True]

    def test_button_disabled(self):
        """Test disabled button doesn't fire events."""
        clicked = []
        button = ui.button("Click", on_click=lambda: clicked.append(True))
        button.disable()
        button.click()
        assert clicked == []  # No click when disabled


class TestInput:
    """Tests for Input element."""

    def test_create_input(self):
        """Test creating an input."""
        inp = ui.input(label="Name", placeholder="Enter name")
        assert inp.label == "Name"
        assert inp.placeholder == "Enter name"
        assert inp.value == ""

    def test_input_with_value(self):
        """Test input with initial value."""
        inp = ui.input(value="initial")
        assert inp.value == "initial"

    def test_password_input(self):
        """Test password input."""
        inp = ui.input(password=True)
        assert inp.password is True


class TestRow:
    """Tests for Row layout element."""

    def test_create_row(self):
        """Test creating a row."""
        row = ui.row()
        assert row.tag == "row"
        assert "row" in row._classes


class TestColumn:
    """Tests for Column layout element."""

    def test_create_column(self):
        """Test creating a column."""
        col = ui.column()
        assert col.tag == "column"
        assert "column" in col._classes


class TestCard:
    """Tests for Card element."""

    def test_create_card(self):
        """Test creating a card."""
        card = ui.card()
        assert card.tag == "card"
        assert "card" in card._classes

    def test_card_slots(self):
        """Test card has header and actions slots."""
        card = ui.card()
        assert "header" in card.slots
        assert "actions" in card.slots


class TestContextManager:
    """Tests for context manager nesting."""

    def test_nesting_elements(self):
        """Test that elements nest correctly with context managers."""
        with Client() as client:
            with ui.column() as col:
                label = ui.label("Child")

            assert label.parent_slot is not None
            assert label.parent_slot.parent == col
            assert label in col.children

    def test_multiple_children(self):
        """Test multiple children in a container."""
        with Client() as client:
            with ui.row() as row:
                label1 = ui.label("First")
                label2 = ui.label("Second")
                button = ui.button("Action")

            assert len(row.children) == 3
            assert label1 in row.children
            assert label2 in row.children
            assert button in row.children

    def test_nested_containers(self):
        """Test nested containers."""
        with Client() as client:
            with ui.column() as outer:
                with ui.row() as inner:
                    label = ui.label("Deep")

            assert inner in outer.children
            assert label in inner.children
            assert label.parent == inner
            assert inner.parent == outer


class TestPage:
    """Tests for page decorator."""

    def test_page_decorator(self):
        """Test page decorator registers route."""
        @ui.page('/test')
        def test_page():
            ui.label("Test Page")

        from rawgui.page import router
        route = router.get_route('/test')
        assert route is not None
        assert route.path == '/test'

    def test_page_with_params(self):
        """Test page with path parameters."""
        @ui.page('/user/{user_id}')
        def user_page(user_id: str):
            ui.label(f"User: {user_id}")

        from rawgui.page import router
        match = router.match('/user/123')
        assert match is not None
        route, params = match
        assert params['user_id'] == '123'
