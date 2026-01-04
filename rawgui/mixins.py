"""Element mixins for common functionality.

Provides reusable mixins like TextElement, ValueElement, etc.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Optional, Self, TypeVar

T = TypeVar("T")


class BindableProperty(Generic[T]):
    """Descriptor for properties that can be bound to other objects.

    Supports reactive binding where changes to this property automatically
    update bound targets.
    """

    def __init__(
        self,
        default: Optional[T] = None,
        on_change: Optional[Callable[[Any, T], None]] = None,
    ) -> None:
        """Initialize the bindable property.

        Args:
            default: Default value
            on_change: Callback when value changes
        """
        self.default = default
        self.on_change = on_change
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        """Store the property name."""
        self.name = f"_bindable_{name}"

    def __get__(self, obj: Any, objtype: Optional[type] = None) -> T:
        """Get the property value."""
        if obj is None:
            return self  # type: ignore
        return getattr(obj, self.name, self.default)

    def __set__(self, obj: Any, value: T) -> None:
        """Set the property value and trigger callbacks."""
        old_value = getattr(obj, self.name, self.default)
        setattr(obj, self.name, value)

        if old_value != value and self.on_change:
            self.on_change(obj, value)


class TextElement:
    """Mixin for elements with text content."""

    text: str = BindableProperty(default="")

    def __init__(self, text: str = "", **kwargs) -> None:
        """Initialize with text.

        Args:
            text: The text content
            **kwargs: Additional arguments for parent class
        """
        super().__init__(**kwargs)
        self.text = text

    def set_text(self, text: str) -> Self:
        """Set the text content.

        Args:
            text: The new text

        Returns:
            Self for method chaining
        """
        self.text = text
        return self

    def bind_text_to(
        self,
        target_object: Any,
        target_name: str,
        forward: Callable[[str], Any] = lambda x: x,
    ) -> Self:
        """Bind this element's text to a target property.

        Args:
            target_object: The object to bind to
            target_name: The property name on the target
            forward: Transform function

        Returns:
            Self for method chaining
        """
        # Store binding info for the binding refresh loop
        if not hasattr(self, "_bindings"):
            self._bindings = []
        self._bindings.append(
            ("text", target_object, target_name, forward)
        )
        return self

    def bind_text_from(
        self,
        source_object: Any,
        source_name: str,
        backward: Callable[[Any], str] = lambda x: str(x),
    ) -> Self:
        """Bind this element's text from a source property.

        Args:
            source_object: The object to bind from
            source_name: The property name on the source
            backward: Transform function

        Returns:
            Self for method chaining
        """
        if not hasattr(self, "_bindings"):
            self._bindings = []
        self._bindings.append(
            (source_object, source_name, "text", backward)
        )
        return self


class ValueElement(Generic[T]):
    """Mixin for elements with a value (inputs, selects, etc.)."""

    value: T = BindableProperty(default=None)

    def __init__(self, value: Optional[T] = None, **kwargs) -> None:
        """Initialize with value.

        Args:
            value: The initial value
            **kwargs: Additional arguments for parent class
        """
        super().__init__(**kwargs)
        if value is not None:
            self.value = value

    def set_value(self, value: T) -> Self:
        """Set the value.

        Args:
            value: The new value

        Returns:
            Self for method chaining
        """
        self.value = value
        self._fire_event("change", value)
        return self

    def bind_value(
        self,
        target_object: Any,
        target_name: str,
        forward: Callable[[T], Any] = lambda x: x,
        backward: Callable[[Any], T] = lambda x: x,
    ) -> Self:
        """Two-way bind this element's value to a target property.

        Args:
            target_object: The object to bind to
            target_name: The property name on the target
            forward: Transform from element to target
            backward: Transform from target to element

        Returns:
            Self for method chaining
        """
        if not hasattr(self, "_bindings"):
            self._bindings = []
        self._bindings.append(
            ("value", target_object, target_name, forward, backward)
        )
        return self

    def bind_value_to(
        self,
        target_object: Any,
        target_name: str,
        forward: Callable[[T], Any] = lambda x: x,
    ) -> Self:
        """One-way bind from this element to target.

        Args:
            target_object: The object to bind to
            target_name: The property name on the target
            forward: Transform function

        Returns:
            Self for method chaining
        """
        if not hasattr(self, "_bindings"):
            self._bindings = []
        self._bindings.append(
            ("value", target_object, target_name, forward)
        )
        return self

    def bind_value_from(
        self,
        source_object: Any,
        source_name: str,
        backward: Callable[[Any], T] = lambda x: x,
    ) -> Self:
        """One-way bind from source to this element.

        Args:
            source_object: The object to bind from
            source_name: The property name on the source
            backward: Transform function

        Returns:
            Self for method chaining
        """
        if not hasattr(self, "_bindings"):
            self._bindings = []
        self._bindings.append(
            (source_object, source_name, "value", backward)
        )
        return self


class DisableableElement:
    """Mixin for elements that can be disabled."""

    def __init__(self, **kwargs) -> None:
        """Initialize the disableable element."""
        super().__init__(**kwargs)
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Check if the element is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set the enabled state."""
        self._enabled = value

    def enable(self) -> Self:
        """Enable the element.

        Returns:
            Self for method chaining
        """
        self._enabled = True
        return self

    def disable(self) -> Self:
        """Disable the element.

        Returns:
            Self for method chaining
        """
        self._enabled = False
        return self

    def set_enabled(self, enabled: bool) -> Self:
        """Set the enabled state.

        Args:
            enabled: Whether to enable the element

        Returns:
            Self for method chaining
        """
        self._enabled = enabled
        return self
