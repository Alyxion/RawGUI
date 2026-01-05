"""Slider component.

NiceGUI-compatible range slider.
"""

from __future__ import annotations

from typing import Callable, Optional, Union

from ..element import Element
from ..mixins import DisableableElement


class Slider(DisableableElement, Element):
    """A horizontal slider for numeric input.

    Features:
    - Keyboard navigation (arrows)
    - Min/max/step values
    - Optional value display
    - ASCII track and handle

    Example:
        slider = ui.slider(min=0, max=100, value=50)
        slider = ui.slider(min=0, max=1, step=0.1, value=0.5)
    """

    def __init__(
        self,
        *,
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        value: Optional[float] = None,
        on_change: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Create a slider.

        Args:
            min: Minimum value
            max: Maximum value
            step: Step increment
            value: Initial value (defaults to min)
            on_change: Callback when value changes
        """
        super().__init__()
        self.tag = "slider"
        self.min = min
        self.max = max
        self.step = step
        self._value = value if value is not None else min
        self._on_change = on_change

    @property
    def value(self) -> float:
        """Get current value."""
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        """Set value (clamped to min/max)."""
        old_value = self._value
        # Clamp and snap to step
        val = max(self.min, min(self.max, val))
        steps = round((val - self.min) / self.step)
        self._value = self.min + steps * self.step
        self._value = max(self.min, min(self.max, self._value))

        if old_value != self._value:
            self._fire_event("change", self._value)
            if self._on_change:
                self._on_change(self._value)

    @property
    def percentage(self) -> float:
        """Get value as percentage of range (0-1)."""
        if self.max == self.min:
            return 0.0
        return (self._value - self.min) / (self.max - self.min)

    def increment(self) -> None:
        """Increase value by one step."""
        if self.enabled:
            self.value = self._value + self.step

    def decrement(self) -> None:
        """Decrease value by one step."""
        if self.enabled:
            self.value = self._value - self.step

    def set_min(self) -> None:
        """Set to minimum value."""
        self.value = self.min

    def set_max(self) -> None:
        """Set to maximum value."""
        self.value = self.max


class Knob(Element):
    """A circular knob for numeric input.

    Like a slider but circular - useful for angle/rotation values.

    Example:
        knob = ui.knob(min=0, max=360, value=180)
    """

    def __init__(
        self,
        *,
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        value: Optional[float] = None,
        show_value: bool = True,
        on_change: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Create a knob.

        Args:
            min: Minimum value
            max: Maximum value
            step: Step increment
            value: Initial value
            show_value: Show numeric value
            on_change: Callback when value changes
        """
        super().__init__()
        self.tag = "knob"
        self.min = min
        self.max = max
        self.step = step
        self._value = value if value is not None else min
        self.show_value = show_value
        self._on_change = on_change

    @property
    def value(self) -> float:
        """Get current value."""
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        """Set value."""
        old_value = self._value
        val = max(self.min, min(self.max, val))
        self._value = val

        if old_value != self._value:
            self._fire_event("change", self._value)
            if self._on_change:
                self._on_change(self._value)
