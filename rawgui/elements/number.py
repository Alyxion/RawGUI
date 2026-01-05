"""Number input component.

NiceGUI-compatible numeric input with min/max/step.
"""

from __future__ import annotations

from typing import Callable, Optional, Union

from ..element import Element
from ..mixins import DisableableElement


class Number(DisableableElement, Element):
    """A numeric input field.

    Features:
    - Min/max validation
    - Step increment
    - Keyboard adjustment
    - Optional prefix/suffix

    Example:
        ui.number(label='Age', min=0, max=120, value=25)
        ui.number(label='Price', prefix='$', step=0.01)
    """

    def __init__(
        self,
        label: Optional[str] = None,
        *,
        placeholder: str = "",
        value: Optional[float] = None,
        min: Optional[float] = None,
        max: Optional[float] = None,
        step: float = 1.0,
        precision: Optional[int] = None,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        on_change: Optional[Callable[[Optional[float]], None]] = None,
    ) -> None:
        """Create a number input.

        Args:
            label: Field label
            placeholder: Placeholder text
            value: Initial value
            min: Minimum allowed value
            max: Maximum allowed value
            step: Step increment
            precision: Decimal precision
            prefix: Text before value
            suffix: Text after value
            on_change: Callback when value changes
        """
        super().__init__()
        self.tag = "number"
        self.label = label
        self.placeholder = placeholder
        self._value = value
        self.min = min
        self.max = max
        self.step = step
        self.precision = precision
        self.prefix = prefix
        self.suffix = suffix
        self._on_change = on_change

    @property
    def value(self) -> Optional[float]:
        """Get numeric value."""
        return self._value

    @value.setter
    def value(self, val: Optional[float]) -> None:
        """Set value (validated)."""
        old = self._value

        if val is not None:
            # Apply bounds
            if self.min is not None:
                val = max(self.min, val)
            if self.max is not None:
                val = min(self.max, val)
            # Apply precision
            if self.precision is not None:
                val = round(val, self.precision)

        self._value = val

        if old != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)

    @property
    def display_value(self) -> str:
        """Get formatted display string."""
        if self._value is None:
            return ""

        text = str(self._value)
        if self.precision is not None:
            text = f"{self._value:.{self.precision}f}"

        parts = []
        if self.prefix:
            parts.append(self.prefix)
        parts.append(text)
        if self.suffix:
            parts.append(self.suffix)

        return "".join(parts)

    def increment(self) -> None:
        """Increase value by step."""
        if self.enabled:
            current = self._value or 0
            self.value = current + self.step

    def decrement(self) -> None:
        """Decrease value by step."""
        if self.enabled:
            current = self._value or 0
            self.value = current - self.step

    def clear(self) -> None:
        """Clear the value."""
        self.value = None


class ColorPicker(Element):
    """A color selection input.

    In TUI, displays hex value with colored preview.

    Example:
        ui.color_picker(value='#ff0000')
    """

    def __init__(
        self,
        label: Optional[str] = None,
        *,
        value: str = "#000000",
        on_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Create a color picker.

        Args:
            label: Field label
            value: Initial hex color
            on_change: Callback when color changes
        """
        super().__init__()
        self.tag = "color_picker"
        self.label = label
        self._value = value
        self._on_change = on_change

    @property
    def value(self) -> str:
        """Get hex color value."""
        return self._value

    @value.setter
    def value(self, val: str) -> None:
        """Set hex color value."""
        old = self._value
        self._value = val
        if old != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)


class DatePicker(Element):
    """A date selection input.

    Example:
        ui.date(label='Birthday', value='2000-01-01')
    """

    def __init__(
        self,
        label: Optional[str] = None,
        *,
        value: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Create a date picker.

        Args:
            label: Field label
            value: Initial date (YYYY-MM-DD format)
            on_change: Callback when date changes
        """
        super().__init__()
        self.tag = "date"
        self.label = label
        self._value = value
        self._on_change = on_change

    @property
    def value(self) -> Optional[str]:
        """Get date string."""
        return self._value

    @value.setter
    def value(self, val: Optional[str]) -> None:
        """Set date string."""
        old = self._value
        self._value = val
        if old != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)


class TimePicker(Element):
    """A time selection input.

    Example:
        ui.time(label='Meeting', value='14:30')
    """

    def __init__(
        self,
        label: Optional[str] = None,
        *,
        value: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Create a time picker.

        Args:
            label: Field label
            value: Initial time (HH:MM format)
            on_change: Callback when time changes
        """
        super().__init__()
        self.tag = "time"
        self.label = label
        self._value = value
        self._on_change = on_change

    @property
    def value(self) -> Optional[str]:
        """Get time string."""
        return self._value

    @value.setter
    def value(self, val: Optional[str]) -> None:
        """Set time string."""
        old = self._value
        self._value = val
        if old != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)
