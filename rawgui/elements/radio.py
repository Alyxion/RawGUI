"""Radio button component.

NiceGUI-compatible radio button group.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from ..element import Element
from ..mixins import DisableableElement


class Radio(DisableableElement, Element):
    """A radio button group for single selection.

    Features:
    - Single selection from multiple options
    - Keyboard navigation (arrows)
    - Horizontal or vertical layout

    Example:
        ui.radio(['Option A', 'Option B', 'Option C'], value='Option A')
        ui.radio({1: 'Small', 2: 'Medium', 3: 'Large'}, value=2)
    """

    def __init__(
        self,
        options: Union[List[Any], Dict[Any, str]],
        *,
        value: Any = None,
        on_change: Optional[Callable[[Any], None]] = None,
    ) -> None:
        """Create a radio button group.

        Args:
            options: List of options or dict mapping values to labels
            value: Initially selected value
            on_change: Callback when selection changes
        """
        super().__init__()
        self.tag = "radio"
        self._options = self._normalize_options(options)
        self._value = value
        self._on_change = on_change

        # UI state
        self._focused_index = 0

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
        """Get selected value."""
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        """Set selected value."""
        old_value = self._value
        self._value = val
        if old_value != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)

    def select(self, value: Any) -> None:
        """Select a value."""
        self.value = value

    def next(self) -> None:
        """Select next option."""
        if not self._options:
            return

        current_idx = -1
        for i, opt in enumerate(self._options):
            if opt["value"] == self._value:
                current_idx = i
                break

        next_idx = (current_idx + 1) % len(self._options)
        self.value = self._options[next_idx]["value"]

    def prev(self) -> None:
        """Select previous option."""
        if not self._options:
            return

        current_idx = 0
        for i, opt in enumerate(self._options):
            if opt["value"] == self._value:
                current_idx = i
                break

        prev_idx = (current_idx - 1) % len(self._options)
        self.value = self._options[prev_idx]["value"]
