"""RawGUI - A TUI version of NiceGUI.

RawGUI provides a terminal user interface framework that is 100% API compatible
with NiceGUI, allowing you to run NiceGUI applications in the terminal.

Usage:
    from rawgui import ui

    @ui.page('/')
    def index():
        ui.label('Hello from RawGUI!')
        ui.button('Click me', on_click=lambda: print('clicked'))

    ui.run()
"""

__version__ = "0.1.0"

# Import ui module for convenient access
from . import ui

# Re-export key components
from .app import app, App
from .client import Client
from .context import context
from .element import Element
from .page import page, navigate

__all__ = [
    "__version__",
    "ui",
    "app",
    "App",
    "Client",
    "context",
    "Element",
    "page",
    "navigate",
]
