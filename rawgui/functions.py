"""NiceGUI-compatible functions.

This module provides decorators and functions like @refreshable, notify, timer.
"""

from __future__ import annotations

import time
import threading
from functools import wraps
from typing import Any, Callable, Optional, List, Dict, TypeVar
from weakref import WeakSet

F = TypeVar("F", bound=Callable)


class RefreshableContainer:
    """Container that can be refreshed to rebuild its contents."""

    _instances: WeakSet["RefreshableContainer"] = WeakSet()

    def __init__(self, func: Callable) -> None:
        self._func = func
        self._element = None
        self._args = ()
        self._kwargs = {}
        RefreshableContainer._instances.add(self)

    def __call__(self, *args, **kwargs) -> Any:
        """Call the wrapped function and store args for refresh."""
        self._args = args
        self._kwargs = kwargs
        return self._func(*args, **kwargs)

    def refresh(self) -> None:
        """Rebuild the container with stored arguments."""
        if self._element:
            # Clear existing children
            self._element.children.clear()
        # Re-call with same arguments
        self._func(*self._args, **self._kwargs)


def refreshable(func: F) -> F:
    """Decorator to make a function refreshable.

    The decorated function gets a .refresh() method that rebuilds its UI.

    Example:
        @ui.refreshable
        def user_list():
            for user in users:
                ui.label(user.name)

        user_list()  # Initial render
        user_list.refresh()  # Re-render with updated data
    """
    container = RefreshableContainer(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return container(*args, **kwargs)

    wrapper.refresh = container.refresh
    wrapper._container = container
    return wrapper


def refreshable_method(method: F) -> F:
    """Decorator for refreshable methods on classes."""
    container = RefreshableContainer(method)

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        return container(self, *args, **kwargs)

    wrapper.refresh = container.refresh
    wrapper._container = container
    return wrapper


class State:
    """Reactive state container.

    Changes to state trigger UI refreshes.

    Example:
        count = ui.state(0)
        ui.label().bind_text_from(count)
        count.value += 1  # UI updates automatically
    """

    def __init__(self, value: Any = None) -> None:
        self._value = value
        self._listeners: List[Callable] = []

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        old = self._value
        self._value = val
        if old != val:
            self._notify()

    def _notify(self) -> None:
        for listener in self._listeners:
            listener(self._value)

    def on_change(self, callback: Callable) -> None:
        self._listeners.append(callback)


def state(initial_value: Any = None) -> State:
    """Create a reactive state container.

    Args:
        initial_value: Initial state value

    Returns:
        State object with .value property
    """
    return State(initial_value)


class Timer:
    """Periodic timer that calls a callback.

    Example:
        ui.timer(1.0, lambda: print('tick'))
    """

    _active_timers: List["Timer"] = []

    def __init__(
        self,
        interval: float,
        callback: Callable,
        *,
        active: bool = True,
        once: bool = False,
    ) -> None:
        """Create a timer.

        Args:
            interval: Seconds between calls
            callback: Function to call
            active: Whether timer is running
            once: Fire only once then deactivate
        """
        self.interval = interval
        self.callback = callback
        self._active = active
        self.once = once
        self._thread: Optional[threading.Thread] = None
        if active:
            self._start()
        Timer._active_timers.append(self)

    @property
    def active(self) -> bool:
        return self._active

    def activate(self) -> None:
        """Start the timer."""
        if not self._active:
            self._active = True
            self._start()

    def deactivate(self) -> None:
        """Stop the timer."""
        self._active = False

    def _start(self) -> None:
        """Start the timer thread."""
        def run():
            while self._active:
                time.sleep(self.interval)
                if self._active:
                    try:
                        self.callback()
                    except Exception:
                        pass
                    if self.once:
                        self._active = False
                        break

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()


def timer(
    interval: float,
    callback: Callable,
    *,
    active: bool = True,
    once: bool = False,
) -> Timer:
    """Create a periodic timer.

    Args:
        interval: Seconds between callback invocations
        callback: Function to call
        active: Whether timer starts immediately
        once: Fire only once

    Returns:
        Timer object
    """
    return Timer(interval, callback, active=active, once=once)


# Notification storage
_notifications: List[Dict[str, Any]] = []


def notify(
    message: str,
    *,
    type: str = "info",
    position: str = "bottom-right",
    close_button: bool = False,
    timeout: float = 3.0,
    **kwargs,
) -> None:
    """Show a notification message.

    Args:
        message: Notification text
        type: 'positive', 'negative', 'warning', 'info'
        position: Where to show notification
        close_button: Show close button
        timeout: Auto-close after seconds (0 = no auto-close)
    """
    from .elements.dialog import Notification
    notif = Notification(
        message,
        position=position,
        type=type,
        timeout=timeout,
        close_button=close_button,
    )
    _notifications.append({
        "message": message,
        "type": type,
        "notification": notif,
    })


def navigate_to(target: str, new_tab: bool = False) -> None:
    """Navigate to a URL or page.

    Args:
        target: URL or page path
        new_tab: Open in new tab (ignored in terminal)
    """
    from .page import navigate
    navigate.to(target)


class Navigate:
    """Navigation helper object."""

    def to(self, target: str, new_tab: bool = False) -> None:
        """Navigate to target."""
        navigate_to(target, new_tab)

    def back(self) -> None:
        """Navigate back in history."""
        from .page import router
        if router:
            router.back()

    def forward(self) -> None:
        """Navigate forward in history."""
        from .page import router
        if router:
            router.forward()

    def reload(self) -> None:
        """Reload current page."""
        from .page import router
        if router:
            router.reload()


navigate = Navigate()


def run_javascript(code: str) -> None:
    """Execute JavaScript (no-op in terminal).

    This is a no-op since terminals don't run JavaScript,
    but it's provided for API compatibility.

    Args:
        code: JavaScript code (ignored)
    """
    pass


def add_css(css: str) -> None:
    """Add CSS styles (stored for reference).

    Terminal doesn't use CSS, but we store it for compatibility
    and potential style mapping.

    Args:
        css: CSS code
    """
    pass


def add_head_html(html: str) -> None:
    """Add HTML to head (no-op in terminal).

    Args:
        html: HTML code (ignored)
    """
    pass


def add_body_html(html: str) -> None:
    """Add HTML to body (no-op in terminal).

    Args:
        html: HTML code (ignored)
    """
    pass


def download(data: bytes, filename: str = "download", media_type: str = "application/octet-stream") -> None:
    """Trigger a file download (no-op in terminal).

    Args:
        data: File contents
        filename: Download filename
        media_type: MIME type
    """
    pass


def page_title(title: str) -> None:
    """Set the page title.

    In terminal, this updates the terminal window title if supported.

    Args:
        title: Page title
    """
    # Set terminal title using ANSI escape
    print(f"\033]0;{title}\007", end="", flush=True)


def update(*elements) -> None:
    """Update elements immediately.

    Forces a re-render of specified elements.

    Args:
        elements: Elements to update (or all if none specified)
    """
    pass  # Terminal re-renders on next frame automatically
