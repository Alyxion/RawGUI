"""Column layout element for vertical arrangement."""

from __future__ import annotations

from ..element import Element


class Column(Element):
    """A vertical layout container.

    Children are arranged vertically from top to bottom.
    Supports flexbox-like properties for alignment and spacing.

    Example:
        with ui.column():
            ui.label('Title')
            ui.button('Action')

        with ui.column().classes('gap-4 items-center'):
            ui.label('Centered content')
            ui.button('Submit')
    """

    _default_classes = ["column"]

    def __init__(self, *, wrap: bool = False) -> None:
        """Initialize the column.

        Args:
            wrap: Whether to wrap children (typically False for columns)
        """
        super().__init__(tag="column")
        self.wrap = wrap

    def __repr__(self) -> str:
        return f"Column(id={self.id}, children={len(self.children)})"
