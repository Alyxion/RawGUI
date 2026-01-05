"""Tabs component.

NiceGUI-compatible tab navigation.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from ..element import Element
from ..slot import Slot


class Tab(Element):
    """A single tab within a Tabs container.

    Example:
        with ui.tabs() as tabs:
            ui.tab('Home', icon='home')
            ui.tab('Settings', icon='settings')
    """

    def __init__(
        self,
        name: str,
        label: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> None:
        """Create a tab.

        Args:
            name: Tab identifier (used for selection)
            label: Display text (defaults to name)
            icon: Optional icon name
        """
        super().__init__()
        self.tag = "tab"
        self.name = name
        self.label = label or name
        self.icon = icon

    def select(self) -> None:
        """Select this tab."""
        if self.parent_slot and self.parent_slot.parent:
            parent = self.parent_slot.parent
            if hasattr(parent, "value"):
                parent.value = self.name


class Tabs(Element):
    """A tab bar for navigation.

    Features:
    - Horizontal tab layout
    - Keyboard navigation
    - Icon support

    Example:
        with ui.tabs() as tabs:
            ui.tab('Home')
            ui.tab('Settings')

        with ui.tab_panels(tabs, value='Home'):
            with ui.tab_panel('Home'):
                ui.label('Home content')
            with ui.tab_panel('Settings'):
                ui.label('Settings content')
    """

    def __init__(
        self,
        *,
        value: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Create a tabs container.

        Args:
            value: Initially selected tab name
            on_change: Callback when tab changes
        """
        super().__init__()
        self.tag = "tabs"
        self._value = value
        self._on_change = on_change

        # Create content slot
        self._content_slot = Slot(self)

    @property
    def value(self) -> Optional[str]:
        """Get selected tab name."""
        return self._value

    @value.setter
    def value(self, val: str) -> None:
        """Set selected tab."""
        old_value = self._value
        self._value = val
        if old_value != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)

    def __enter__(self) -> "Tabs":
        """Enter context."""
        self._content_slot.__enter__()
        return self

    def __exit__(self, *args) -> None:
        """Exit context."""
        self._content_slot.__exit__(*args)
        # Auto-select first tab if none selected
        if self._value is None and self.children:
            for child in self.children:
                if child.tag == "tab":
                    self._value = child.name
                    break


class TabPanel(Element):
    """Content panel for a specific tab.

    Only visible when the corresponding tab is selected.

    Example:
        with ui.tab_panel('Home'):
            ui.label('Home content')
    """

    def __init__(self, name: str) -> None:
        """Create a tab panel.

        Args:
            name: Must match a tab name in the parent TabPanels
        """
        super().__init__()
        self.tag = "tab_panel"
        self.name = name

        # Create content slot
        self._content_slot = Slot(self)

    def __enter__(self) -> "TabPanel":
        """Enter context."""
        self._content_slot.__enter__()
        return self

    def __exit__(self, *args) -> None:
        """Exit context."""
        self._content_slot.__exit__(*args)


class TabPanels(Element):
    """Container for tab panels, synchronized with a Tabs component.

    Example:
        with ui.tabs() as tabs:
            ui.tab('Home')
            ui.tab('Settings')

        with ui.tab_panels(tabs, value='Home'):
            with ui.tab_panel('Home'):
                ui.label('Home content')
    """

    def __init__(
        self,
        tabs: Tabs,
        *,
        value: Optional[str] = None,
    ) -> None:
        """Create tab panels container.

        Args:
            tabs: The Tabs component to sync with
            value: Initially visible panel (defaults to tabs.value)
        """
        super().__init__()
        self.tag = "tab_panels"
        self._tabs = tabs
        self._value = value or tabs.value

        # Sync with tabs
        tabs._on_change = self._on_tab_change

        # Create content slot
        self._content_slot = Slot(self)

    def _on_tab_change(self, tab_name: str) -> None:
        """Handle tab selection change."""
        self._value = tab_name
        self._update_panel_visibility()

    def _update_panel_visibility(self) -> None:
        """Update which panel is visible."""
        for child in self.children:
            if child.tag == "tab_panel":
                child.visible = child.name == self._value

    @property
    def value(self) -> Optional[str]:
        """Get visible panel name."""
        return self._value

    @value.setter
    def value(self, val: str) -> None:
        """Set visible panel and sync tabs."""
        self._value = val
        self._tabs.value = val
        self._update_panel_visibility()

    def __enter__(self) -> "TabPanels":
        """Enter context."""
        self._content_slot.__enter__()
        return self

    def __exit__(self, *args) -> None:
        """Exit context."""
        self._content_slot.__exit__(*args)
        self._update_panel_visibility()
