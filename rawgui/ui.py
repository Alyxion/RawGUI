"""Main UI module for RawGUI.

This module provides a NiceGUI-compatible API for building terminal user interfaces.
All UI elements and functions are exported from here.

Usage:
    from rawgui import ui

    @ui.page('/')
    def index():
        with ui.column():
            ui.label('Hello World')
            ui.button('Click me', on_click=lambda: print('clicked'))

    ui.run()
"""

from __future__ import annotations

# Core classes
from .app import app, App
from .client import Client
from .context import context
from .element import Element

# Page and routing
from .page import page, navigate, router

# Elements - import classes and create lowercase factory functions
from .elements.label import Label
from .elements.button import Button
from .elements.input import Input
from .elements.row import Row
from .elements.column import Column
from .elements.card import Card, CardSection, CardActions

# Run function
from .run import run


# Element factory functions (NiceGUI style - lowercase)
def label(text: str = "") -> Label:
    """Create a text label.

    Args:
        text: The text to display

    Returns:
        Label element
    """
    return Label(text)


def button(
    text: str = "",
    *,
    on_click=None,
    icon: str = None,
    color: str = None,
) -> Button:
    """Create a clickable button.

    Args:
        text: Button text
        on_click: Click handler callback
        icon: Optional icon name
        color: Optional color

    Returns:
        Button element
    """
    return Button(text, on_click=on_click, icon=icon, color=color)


def input(
    label: str = "",
    *,
    placeholder: str = "",
    value: str = "",
    password: bool = False,
    on_change=None,
) -> Input:
    """Create a text input field.

    Args:
        label: Input label
        placeholder: Placeholder text
        value: Initial value
        password: Whether to mask input
        on_change: Change handler callback

    Returns:
        Input element
    """
    return Input(
        label=label,
        placeholder=placeholder,
        value=value,
        password=password,
        on_change=on_change,
    )


def row(*, wrap: bool = True) -> Row:
    """Create a horizontal layout container.

    Args:
        wrap: Whether to wrap children

    Returns:
        Row element
    """
    return Row(wrap=wrap)


def column(*, wrap: bool = False) -> Column:
    """Create a vertical layout container.

    Args:
        wrap: Whether to wrap children

    Returns:
        Column element
    """
    return Column(wrap=wrap)


def card() -> Card:
    """Create a card container.

    Returns:
        Card element
    """
    return Card()


def card_section() -> CardSection:
    """Create a card section.

    Returns:
        CardSection element
    """
    return CardSection()


def card_actions(*, align: str = "right") -> CardActions:
    """Create a card actions section.

    Args:
        align: Action alignment ('left', 'center', 'right')

    Returns:
        CardActions element
    """
    return CardActions(align=align)


# Export all for `from rawgui.ui import *`
__all__ = [
    # Core
    "app",
    "App",
    "Client",
    "context",
    "Element",
    # Page/routing
    "page",
    "navigate",
    "router",
    # Run
    "run",
    # Elements (lowercase factory functions)
    "label",
    "button",
    "input",
    "row",
    "column",
    "card",
    "card_section",
    "card_actions",
    # Element classes (PascalCase)
    "Label",
    "Button",
    "Input",
    "Row",
    "Column",
    "Card",
    "CardSection",
    "CardActions",
]
