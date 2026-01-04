"""Label element for displaying text."""

from __future__ import annotations

from ..element import Element
from ..mixins import TextElement


class Label(TextElement, Element):
    """A text label element.

    Displays text content that can be styled with classes and inline styles.

    Example:
        ui.label('Hello World').classes('text-xl font-bold')
    """

    def __init__(self, text: str = "") -> None:
        """Initialize the label.

        Args:
            text: The text to display
        """
        super().__init__(text=text, tag="label")

    def __repr__(self) -> str:
        return f"Label(id={self.id}, text={self.text!r})"
