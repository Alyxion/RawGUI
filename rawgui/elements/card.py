"""Card container element with border and optional sections."""

from __future__ import annotations

from typing import Optional

from ..element import Element


class Card(Element):
    """A card container with border and padding.

    Cards provide a visually distinct container for grouping
    related content. In terminal mode, rendered with box-drawing characters.

    Example:
        with ui.card():
            ui.label('Card Title')
            ui.button('Action')

        with ui.card().classes('w-64'):
            ui.label('Fixed width card')
    """

    _default_classes = ["card"]

    def __init__(self) -> None:
        """Initialize the card."""
        super().__init__(tag="card")

        # Card can have header, content, and actions sections
        self._header_slot = self.add_slot("header")
        self._actions_slot = self.add_slot("actions")

    @property
    def header(self):
        """Access the header slot."""
        return self._header_slot

    @property
    def actions(self):
        """Access the actions slot."""
        return self._actions_slot

    def tight(self) -> "Card":
        """Remove default padding.

        Returns:
            Self for method chaining
        """
        return self.classes("tight")

    def flat(self) -> "Card":
        """Remove shadow/border emphasis.

        Returns:
            Self for method chaining
        """
        return self.classes("flat")

    def bordered(self) -> "Card":
        """Add a visible border.

        Returns:
            Self for method chaining
        """
        return self.classes("bordered")

    def __repr__(self) -> str:
        return f"Card(id={self.id}, children={len(self.children)})"


class CardSection(Element):
    """A section within a card for content grouping."""

    _default_classes = ["card-section"]

    def __init__(self) -> None:
        """Initialize the card section."""
        super().__init__(tag="card-section")


class CardActions(Element):
    """An actions section at the bottom of a card."""

    _default_classes = ["card-actions"]

    def __init__(self, *, align: str = "right") -> None:
        """Initialize the card actions.

        Args:
            align: Alignment of actions ('left', 'center', 'right')
        """
        super().__init__(tag="card-actions")
        self.align = align
        self.classes(f"align-{align}")
