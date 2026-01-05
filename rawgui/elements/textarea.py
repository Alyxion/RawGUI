"""Textarea component.

NiceGUI-compatible multiline text input.
"""

from __future__ import annotations

from typing import Callable, Optional

from ..element import Element
from ..mixins import DisableableElement


class Textarea(DisableableElement, Element):
    """A multiline text input.

    Features:
    - Multiple lines of text
    - Scrolling for long content
    - Keyboard navigation
    - Line numbers (optional)

    Example:
        textarea = ui.textarea(label='Description', value='Initial text')
        textarea = ui.textarea(placeholder='Enter code...')
    """

    def __init__(
        self,
        label: Optional[str] = None,
        *,
        placeholder: str = "",
        value: str = "",
        on_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Create a textarea.

        Args:
            label: Label text
            placeholder: Placeholder text when empty
            value: Initial value
            on_change: Callback when text changes
        """
        super().__init__()
        self.tag = "textarea"
        self.label = label
        self.placeholder = placeholder
        self._value = value
        self._on_change = on_change

        # Editing state
        self._cursor_line = 0
        self._cursor_col = 0
        self._scroll_y = 0

    @property
    def value(self) -> str:
        """Get text content."""
        return self._value

    @value.setter
    def value(self, val: str) -> None:
        """Set text content."""
        old_value = self._value
        self._value = val
        if old_value != val:
            self._fire_event("change", val)
            if self._on_change:
                self._on_change(val)

    @property
    def lines(self) -> list[str]:
        """Get text as list of lines."""
        return self._value.split("\n")

    @property
    def line_count(self) -> int:
        """Get number of lines."""
        return len(self.lines)

    def set_value(self, text: str) -> None:
        """Set the text value."""
        self.value = text

    def clear(self) -> None:
        """Clear all text."""
        self.value = ""

    def append(self, text: str) -> None:
        """Append text."""
        self.value = self._value + text

    def insert_line(self, line: str, index: Optional[int] = None) -> None:
        """Insert a line at index (or end if None)."""
        lines = self.lines
        if index is None:
            lines.append(line)
        else:
            lines.insert(index, line)
        self.value = "\n".join(lines)


class Editor(Textarea):
    """A code/markdown editor with syntax highlighting.

    Like Textarea but with:
    - Syntax highlighting
    - Line numbers
    - Keyboard shortcuts

    Example:
        editor = ui.editor(language='python')
    """

    def __init__(
        self,
        label: Optional[str] = None,
        *,
        placeholder: str = "",
        value: str = "",
        language: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Create an editor.

        Args:
            label: Label text
            placeholder: Placeholder text
            value: Initial content
            language: Language for syntax highlighting
            on_change: Callback when content changes
        """
        super().__init__(
            label=label,
            placeholder=placeholder,
            value=value,
            on_change=on_change,
        )
        self.tag = "editor"
        self.language = language
