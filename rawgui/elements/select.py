"""Select/Dropdown component.

NiceGUI-compatible dropdown selection component.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from ..element import Element
from ..mixins import DisableableElement


class Select(DisableableElement, Element):
    """A dropdown select component.

    Features:
    - Single or multiple selection
    - Keyboard navigation
    - Search/filter support
    - Options as list or dict

    Example:
        ui.select(['Option 1', 'Option 2', 'Option 3'], value='Option 1')
        ui.select({1: 'One', 2: 'Two', 3: 'Three'}, value=1)
    """

    def __init__(
        self,
        options: Union[List[Any], Dict[Any, str]],
        *,
        label: Optional[str] = None,
        value: Any = None,
        on_change: Optional[Callable[[Any], None]] = None,
        with_input: bool = False,
        multiple: bool = False,
        clearable: bool = False,
    ) -> None:
        """Create a select component.

        Args:
            options: List of options or dict mapping values to labels
            label: Label text above the select
            value: Initially selected value(s)
            on_change: Callback when selection changes
            with_input: Allow typing to filter options
            multiple: Allow multiple selections
            clearable: Show clear button
        """
        super().__init__()
        self.tag = "select"
        self.label = label
        self._options = self._normalize_options(options)
        self._value = value if value is not None else ([] if multiple else None)
        self._on_change = on_change
        self.with_input = with_input
        self.multiple = multiple
        self.clearable = clearable

        # UI state
        self._is_open = False
        self._filter_text = ""
        self._highlighted_index = 0

    def _normalize_options(
        self, options: Union[List[Any], Dict[Any, str]]
    ) -> List[Dict[str, Any]]:
        """Convert options to normalized format."""
        if isinstance(options, dict):
            return [{"value": k, "label": str(v)} for k, v in options.items()]
        else:
            return [{"value": o, "label": str(o)} for o in options]

    @property
    def options(self) -> List[Dict[str, Any]]:
        """Get normalized options."""
        return self._options

    @options.setter
    def options(self, value: Union[List[Any], Dict[Any, str]]) -> None:
        """Set options."""
        self._options = self._normalize_options(value)

    @property
    def value(self) -> Any:
        """Get selected value(s)."""
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        """Set selected value(s)."""
        old_value = self._value
        self._value = val
        if old_value != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)

    @property
    def display_value(self) -> str:
        """Get display text for current value."""
        if self._value is None:
            return ""

        if self.multiple:
            values = self._value if isinstance(self._value, list) else [self._value]
            labels = []
            for v in values:
                for opt in self._options:
                    if opt["value"] == v:
                        labels.append(opt["label"])
                        break
            return ", ".join(labels)
        else:
            for opt in self._options:
                if opt["value"] == self._value:
                    return opt["label"]
            return str(self._value)

    def open(self) -> None:
        """Open the dropdown."""
        if self.enabled:
            self._is_open = True

    def close(self) -> None:
        """Close the dropdown."""
        self._is_open = False
        self._filter_text = ""

    def toggle(self) -> None:
        """Toggle dropdown open/closed."""
        if self._is_open:
            self.close()
        else:
            self.open()

    def select(self, value: Any) -> None:
        """Select a value."""
        if self.multiple:
            if not isinstance(self._value, list):
                self._value = []
            if value in self._value:
                self._value.remove(value)
            else:
                self._value.append(value)
            self._fire_event("change", self._value)
            if self._on_change:
                self._on_change(self._value)
        else:
            self.value = value
            self.close()

    def clear(self) -> None:
        """Clear selection."""
        self.value = [] if self.multiple else None

    def set_options(
        self,
        options: Union[List[Any], Dict[Any, str]],
        *,
        value: Any = None,
    ) -> None:
        """Update options and optionally set value."""
        self._options = self._normalize_options(options)
        if value is not None:
            self.value = value
