"""Tests for newly added components."""

import pytest
from rawgui import ui
from rawgui.client import Client
from rawgui.renderer.terminal import TerminalRenderer


class TestDialog:
    """Tests for dialog component."""

    def test_create_dialog(self):
        """Test creating a dialog."""
        with Client() as client:
            dialog = ui.dialog()

        assert dialog.tag == "dialog"
        assert dialog.is_open is False
        assert dialog.visible is False

    def test_dialog_open_close(self):
        """Test opening and closing dialog."""
        with Client() as client:
            dialog = ui.dialog()

        dialog.open()
        assert dialog.is_open is True
        assert dialog.visible is True

        dialog.close()
        assert dialog.is_open is False
        assert dialog.visible is False

    def test_dialog_with_content(self):
        """Test dialog with content inside."""
        with Client() as client:
            with ui.dialog() as dialog:
                card = ui.card()

        # Dialog has content (card is inside the dialog's slot)
        assert dialog.tag == "dialog"
        # The card was created within the dialog context
        assert card.tag == "card"


class TestSelect:
    """Tests for select/dropdown component."""

    def test_create_select_with_list(self):
        """Test creating select with list options."""
        with Client() as client:
            sel = ui.select(['Option 1', 'Option 2', 'Option 3'])

        assert sel.tag == "select"
        assert len(sel.options) == 3
        assert sel.options[0]["value"] == "Option 1"

    def test_create_select_with_dict(self):
        """Test creating select with dict options."""
        with Client() as client:
            sel = ui.select({1: 'One', 2: 'Two', 3: 'Three'})

        assert len(sel.options) == 3
        assert sel.options[0]["value"] == 1
        assert sel.options[0]["label"] == "One"

    def test_select_value(self):
        """Test select value setting."""
        with Client() as client:
            sel = ui.select(['A', 'B', 'C'], value='B')

        assert sel.value == 'B'
        assert sel.display_value == 'B'

    def test_select_change_callback(self):
        """Test select change callback."""
        values = []
        with Client() as client:
            sel = ui.select(['A', 'B', 'C'], on_change=lambda v: values.append(v))

        sel.value = 'C'
        assert values == ['C']


class TestRadio:
    """Tests for radio button component."""

    def test_create_radio(self):
        """Test creating radio group."""
        with Client() as client:
            radio = ui.radio(['Small', 'Medium', 'Large'])

        assert radio.tag == "radio"
        assert len(radio.options) == 3

    def test_radio_value(self):
        """Test radio value."""
        with Client() as client:
            radio = ui.radio(['A', 'B', 'C'], value='B')

        assert radio.value == 'B'

    def test_radio_navigation(self):
        """Test radio next/prev navigation."""
        with Client() as client:
            radio = ui.radio(['A', 'B', 'C'], value='A')

        radio.next()
        assert radio.value == 'B'

        radio.prev()
        assert radio.value == 'A'


class TestProgress:
    """Tests for progress bar component."""

    def test_create_progress(self):
        """Test creating progress bar."""
        with Client() as client:
            prog = ui.progress(0.5)

        assert prog.tag == "progress"
        assert prog.value == 0.5
        assert prog.percentage == 50

    def test_progress_bounds(self):
        """Test progress value bounds."""
        with Client() as client:
            prog = ui.progress(1.5)

        assert prog.value == 1.0  # Clamped to max

        prog.value = -0.5
        assert prog.value == 0.0  # Clamped to min


class TestSlider:
    """Tests for slider component."""

    def test_create_slider(self):
        """Test creating slider."""
        with Client() as client:
            slider = ui.slider(min=0, max=100, value=50)

        assert slider.tag == "slider"
        assert slider.value == 50
        assert slider.min == 0
        assert slider.max == 100

    def test_slider_increment_decrement(self):
        """Test slider increment/decrement."""
        with Client() as client:
            slider = ui.slider(min=0, max=10, step=1, value=5)

        slider.increment()
        assert slider.value == 6

        slider.decrement()
        assert slider.value == 5


class TestToggle:
    """Tests for toggle/switch component."""

    def test_create_toggle(self):
        """Test creating toggle."""
        with Client() as client:
            toggle = ui.toggle("Dark mode", value=False)

        assert toggle.tag == "toggle"
        assert toggle.value is False
        assert toggle.text == "Dark mode"

    def test_toggle_switch(self):
        """Test toggling."""
        with Client() as client:
            toggle = ui.toggle("Test")

        assert toggle.value is False
        toggle.toggle()
        assert toggle.value is True
        toggle.toggle()
        assert toggle.value is False


class TestTabs:
    """Tests for tabs component."""

    def test_create_tabs(self):
        """Test creating tabs."""
        with Client() as client:
            with ui.tabs() as tabs:
                tab1 = ui.tab('Home')
                tab2 = ui.tab('Settings')

        assert tabs.tag == "tabs"
        # Verify tabs were created
        assert tab1.tag == "tab"
        assert tab2.tag == "tab"
        assert tab1.name == "Home"
        assert tab2.name == "Settings"

    def test_tabs_value(self):
        """Test tabs value (selected tab)."""
        with Client() as client:
            with ui.tabs(value='Settings') as tabs:
                ui.tab('Home')
                ui.tab('Settings')

        assert tabs.value == 'Settings'


class TestTable:
    """Tests for table component."""

    def test_create_table(self):
        """Test creating table."""
        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name'},
            {'name': 'age', 'label': 'Age', 'field': 'age'},
        ]
        rows = [
            {'name': 'Alice', 'age': 30},
            {'name': 'Bob', 'age': 25},
        ]

        with Client() as client:
            table = ui.table(columns=columns, rows=rows, row_key='name')

        assert table.tag == "table"
        assert len(table.rows) == 2
        assert len(table.columns) == 2

    def test_table_selection(self):
        """Test table row selection."""
        columns = [{'name': 'id', 'label': 'ID', 'field': 'id'}]
        rows = [{'id': 1}, {'id': 2}, {'id': 3}]

        with Client() as client:
            table = ui.table(columns=columns, rows=rows, row_key='id', selection='single')

        table.select(2)
        assert len(table.selected) == 1
        assert table.selected[0]['id'] == 2


class TestSeparator:
    """Tests for separator component."""

    def test_create_separator(self):
        """Test creating separator."""
        with Client() as client:
            sep = ui.separator()

        assert sep.tag == "separator"
        assert sep.vertical is False

    def test_vertical_separator(self):
        """Test vertical separator."""
        with Client() as client:
            sep = ui.separator(vertical=True)

        assert sep.vertical is True


class TestNumber:
    """Tests for number input component."""

    def test_create_number(self):
        """Test creating number input."""
        with Client() as client:
            num = ui.number(label="Age", value=25, min=0, max=120)

        assert num.tag == "number"
        assert num.value == 25

    def test_number_bounds(self):
        """Test number value bounds."""
        with Client() as client:
            num = ui.number(min=0, max=100, value=50)

        num.value = 150
        assert num.value == 100  # Clamped

        num.value = -50
        assert num.value == 0  # Clamped


class TestTextarea:
    """Tests for textarea component."""

    def test_create_textarea(self):
        """Test creating textarea."""
        with Client() as client:
            ta = ui.textarea(label="Description", value="Initial text")

        assert ta.tag == "textarea"
        assert ta.value == "Initial text"
        assert ta.line_count == 1

    def test_textarea_multiline(self):
        """Test textarea with multiline content."""
        with Client() as client:
            ta = ui.textarea(value="Line 1\nLine 2\nLine 3")

        assert ta.line_count == 3


class TestTree:
    """Tests for tree component."""

    def test_create_tree(self):
        """Test creating tree."""
        nodes = [
            {'id': '1', 'label': 'Root'},
        ]

        with Client() as client:
            tree = ui.tree(nodes)

        assert tree.tag == "tree"
        assert len(tree.nodes) == 1

    def test_tree_expand_collapse(self):
        """Test tree expand/collapse."""
        nodes = [
            {'id': '1', 'label': 'Root', 'children': [
                {'id': '1.1', 'label': 'Child'}
            ]},
        ]

        with Client() as client:
            tree = ui.tree(nodes)

        tree.expand('1')
        assert '1' in tree._expanded

        tree.collapse('1')
        assert '1' not in tree._expanded


class TestRendering:
    """Tests for rendering new components."""

    def test_render_toggle(self):
        """Test toggle renders correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            toggle = ui.toggle("Dark mode", value=True)

        output = renderer.render(toggle)
        assert "Dark mode" in output
        assert "(*)" in output  # ON indicator

    def test_render_progress(self):
        """Test progress bar renders correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            prog = ui.progress(0.5, show_value=True)

        output = renderer.render(prog)
        assert "50%" in output
        assert "=" in output  # Progress bar fill

    def test_render_slider(self):
        """Test slider renders correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            slider = ui.slider(min=0, max=1, value=0.5)

        output = renderer.render(slider)
        assert "O" in output  # Handle
        assert "-" in output  # Track

    def test_render_select(self):
        """Test select renders correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            sel = ui.select(['A', 'B', 'C'], value='B')

        output = renderer.render(sel)
        assert "B" in output
        assert "v" in output or "^" in output  # Dropdown indicator

    def test_render_radio(self):
        """Test radio renders correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            radio = ui.radio(['A', 'B', 'C'], value='B')

        output = renderer.render(radio)
        assert "A" in output
        assert "B" in output
        assert "C" in output
        assert "(*)" in output  # Selected marker

    def test_render_badge(self):
        """Test badge renders correctly."""
        renderer = TerminalRenderer()

        with Client() as client:
            badge = ui.badge("NEW")

        output = renderer.render(badge)
        assert "NEW" in output
