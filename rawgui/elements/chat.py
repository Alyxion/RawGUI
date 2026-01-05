"""Chat components.

NiceGUI-compatible chat message component.
"""

from __future__ import annotations

from typing import Optional, List

from ..element import Element


class ChatMessage(Element):
    """Chat message bubble.

    Displays a chat message with optional avatar, timestamp, and styling.

    Example:
        ui.chat_message(text='Hello!', avatar='https://...', sent=True)
    """

    def __init__(
        self,
        text: str = "",
        *,
        name: Optional[str] = None,
        stamp: Optional[str] = None,
        avatar: Optional[str] = None,
        sent: bool = False,
        text_html: bool = False,
    ) -> None:
        """Create a chat message.

        Args:
            text: Message text
            name: Sender name
            stamp: Timestamp string
            avatar: Avatar URL or text
            sent: True if message was sent by user (right-aligned)
            text_html: Whether text contains HTML
        """
        super().__init__()
        self.tag = "chat_message"
        self._text = text
        self.name = name
        self.stamp = stamp
        self.avatar = avatar
        self.sent = sent
        self.text_html = text_html

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value


class Log(Element):
    """Log/console output display.

    Shows a scrollable log of messages.

    Example:
        log = ui.log(max_lines=100)
        log.push('Server started')
    """

    def __init__(self, max_lines: Optional[int] = None) -> None:
        """Create a log display.

        Args:
            max_lines: Maximum lines to keep (None = unlimited)
        """
        super().__init__()
        self.tag = "log"
        self.max_lines = max_lines
        self._lines: List[str] = []

    @property
    def lines(self) -> List[str]:
        return self._lines.copy()

    def push(self, line: str) -> None:
        """Add a line to the log.

        Args:
            line: Text to add
        """
        self._lines.append(line)
        if self.max_lines and len(self._lines) > self.max_lines:
            self._lines = self._lines[-self.max_lines:]

    def clear(self) -> None:
        """Clear all log lines."""
        self._lines.clear()
