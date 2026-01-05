"""Native widget element for embedding Tkinter widgets in RawGUI.

This element allows embedding real Tkinter widgets within RawGUI layouts.
It is intended for exceptional cases where RawGUI doesn't provide an
equivalent widget (e.g., browser, video player, complex canvas).

NOTE: Native widgets are the exception, not the norm. 99% of UI should
use standard RawGUI elements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from ..element import Element

if TYPE_CHECKING:
    import tkinter as tk


class NativeWidget(Element):
    """A placeholder for embedding native Tkinter widgets.

    This element creates a "hole" in the RawGUI rendering where a real
    Tkinter widget will be placed. The widget is created lazily when
    the Tkinter adapter runs.

    Example:
        # Create a native Tkinter Scale widget
        def create_scale(parent):
            import tkinter as tk
            scale = tk.Scale(parent, from_=0, to=100, orient=tk.HORIZONTAL)
            return scale

        ui.native_widget(create_scale, width=200, height=50)

        # Or with a Text widget
        def create_text(parent):
            import tkinter as tk
            text = tk.Text(parent, height=10, width=40)
            text.insert('1.0', 'Hello from native Tkinter!')
            return text

        ui.native_widget(create_text, width=400, height=200)

    Note:
        - Only works with the Tkinter renderer
        - In TUI mode, displays a placeholder
        - Native widgets handle their own events
    """

    def __init__(
        self,
        widget_factory: Callable[["tk.Frame"], Optional["tk.Widget"]],
        *,
        width: int = 200,
        height: int = 100,
    ) -> None:
        """Initialize the native widget placeholder.

        Args:
            widget_factory: A callable that receives a parent Frame and returns
                           a Tkinter widget. The widget will be packed into the frame.
            width: Width in pixels
            height: Height in pixels
        """
        super().__init__(tag="native_widget")

        self.widget_factory = widget_factory
        self.width = width
        self.height = height

        # Store reference to the created widget (set by adapter)
        self._native_widget: Optional[Any] = None

    def __repr__(self) -> str:
        return f"NativeWidget(id={self.id}, size={self.width}x{self.height})"
