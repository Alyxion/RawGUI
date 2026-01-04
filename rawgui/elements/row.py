"""Row layout element for horizontal arrangement."""

from __future__ import annotations

from ..element import Element


class Row(Element):
    """A horizontal layout container.

    Children are arranged horizontally from left to right.
    Supports flexbox-like properties for alignment and spacing.

    Example:
        with ui.row():
            ui.button('Left')
            ui.button('Right')

        with ui.row().classes('gap-4 items-center'):
            ui.label('Name:')
            ui.input()
    """

    _default_classes = ["row"]

    def __init__(self, *, wrap: bool = True) -> None:
        """Initialize the row.

        Args:
            wrap: Whether to wrap children to next line if needed
        """
        super().__init__(tag="row")
        self.wrap = wrap

        if not wrap:
            self.classes("no-wrap")

    def __repr__(self) -> str:
        return f"Row(id={self.id}, children={len(self.children)})"
