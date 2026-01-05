"""NiceGUI compatibility injection.

Call inject() before importing nicegui to redirect imports to RawGUI.

Usage:
    from rawgui.compat import inject
    inject()

    # Now this uses RawGUI:
    from nicegui import ui
"""

import sys
from types import ModuleType


_injected = False


def inject():
    """Inject RawGUI as the nicegui module.

    After calling this, `from nicegui import ui` will use rawgui.
    """
    global _injected
    if _injected:
        return

    # Create nicegui module that proxies to rawgui
    nicegui = ModuleType('nicegui')
    nicegui.__path__ = []
    nicegui.__package__ = 'nicegui'

    # Import rawgui components
    from rawgui import ui
    from rawgui.app import app
    from rawgui.client import Client
    from rawgui.context import context
    from rawgui.element import Element

    # Set up nicegui module attributes
    nicegui.ui = ui
    nicegui.app = app
    nicegui.Client = Client
    nicegui.context = context
    nicegui.Element = Element
    nicegui.__version__ = "0.1.0"

    # Stubs for NiceGUI-specific items
    class APIRouter:
        def __init__(self, prefix="", tags=None):
            self.prefix = prefix
            self.tags = tags or []

    class Event:
        def __init__(self, sender=None, args=None):
            self.sender = sender
            self.args = args or {}

    class ElementFilter:
        def __init__(self, **kwargs):
            self.filters = kwargs

    class PageArguments:
        pass

    nicegui.APIRouter = APIRouter
    nicegui.Event = Event
    nicegui.ElementFilter = ElementFilter
    nicegui.PageArguments = PageArguments

    # Create run submodule
    run_module = ModuleType('nicegui.run')

    async def cpu_bound(func, *args, **kwargs):
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def io_bound(func, *args, **kwargs):
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    run_module.cpu_bound = cpu_bound
    run_module.io_bound = io_bound
    nicegui.run = run_module

    # Create other submodules as empty
    nicegui.binding = ModuleType('nicegui.binding')
    nicegui.storage = ModuleType('nicegui.storage')
    nicegui.storage.user = {}
    nicegui.storage.browser = {}
    nicegui.storage.general = {}
    nicegui.storage.tab = {}
    nicegui.storage.client = {}
    nicegui.html = ModuleType('nicegui.html')
    nicegui.elements = ModuleType('nicegui.elements')

    # Install in sys.modules
    sys.modules['nicegui'] = nicegui
    sys.modules['nicegui.ui'] = ui
    sys.modules['nicegui.run'] = run_module
    sys.modules['nicegui.binding'] = nicegui.binding
    sys.modules['nicegui.storage'] = nicegui.storage
    sys.modules['nicegui.html'] = nicegui.html
    sys.modules['nicegui.elements'] = nicegui.elements

    _injected = True


def eject():
    """Remove RawGUI injection, restoring original nicegui if present."""
    global _injected

    modules_to_remove = [
        'nicegui',
        'nicegui.ui',
        'nicegui.run',
        'nicegui.binding',
        'nicegui.storage',
        'nicegui.html',
        'nicegui.elements',
    ]

    for mod in modules_to_remove:
        sys.modules.pop(mod, None)

    _injected = False


def is_injected() -> bool:
    """Check if RawGUI is currently injected as nicegui."""
    return _injected
