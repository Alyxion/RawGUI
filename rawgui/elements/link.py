"""Link/anchor component.

NiceGUI-compatible hyperlink.
"""

from __future__ import annotations

from typing import Optional, Union

from ..element import Element


class Link(Element):
    """A hyperlink element.

    Features:
    - Internal page navigation
    - External URL links
    - Styled text with underline

    Example:
        ui.link('Home', '/')
        ui.link('GitHub', 'https://github.com')
    """

    def __init__(
        self,
        text: str,
        target: str = "",
        *,
        new_tab: bool = False,
    ) -> None:
        """Create a link.

        Args:
            text: Link text
            target: URL or path to navigate to
            new_tab: Open in new tab (external links only)
        """
        super().__init__()
        self.tag = "link"
        self.text = text
        self.target = target
        self.new_tab = new_tab

    @property
    def is_external(self) -> bool:
        """Whether this is an external link."""
        return self.target.startswith(("http://", "https://", "//"))


class Markdown(Element):
    """Rendered markdown content.

    Converts markdown to ASCII-styled text.

    Example:
        ui.markdown('# Heading\\n\\nSome **bold** text.')
    """

    def __init__(self, content: str = "") -> None:
        """Create markdown content.

        Args:
            content: Markdown text
        """
        super().__init__()
        self.tag = "markdown"
        self.content = content

    def set_content(self, content: str) -> None:
        """Update markdown content."""
        self.content = content


class Html(Element):
    """Raw HTML content (rendered as text in TUI).

    HTML is stripped to plain text for terminal display.

    Example:
        ui.html('<b>Bold text</b>')
    """

    def __init__(self, content: str = "") -> None:
        """Create HTML content.

        Args:
            content: HTML text
        """
        super().__init__()
        self.tag = "html"
        self.content = content

    def set_content(self, content: str) -> None:
        """Update HTML content."""
        self.content = content


class Code(Element):
    """Syntax-highlighted code block.

    Example:
        ui.code('print("Hello")', language='python')
    """

    def __init__(
        self,
        content: str = "",
        *,
        language: Optional[str] = None,
    ) -> None:
        """Create a code block.

        Args:
            content: Code text
            language: Programming language for highlighting
        """
        super().__init__()
        self.tag = "code"
        self.content = content
        self.language = language
