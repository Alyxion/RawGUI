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

from typing import Any, Callable, Dict, List, Optional, Union

# Core classes
from .app import app, App
from .client import Client
from .context import context
from .element import Element

# Page and routing
from .page import page, router

# Import all element classes
from .elements.label import Label
from .elements.button import Button
from .elements.input import Input
from .elements.row import Row
from .elements.column import Column
from .elements.card import Card, CardSection, CardActions
from .elements.checkbox import Checkbox
from .elements.navbar import NavigationBar
from .elements.dialog import Dialog, Notification
from .elements.select import Select
from .elements.radio import Radio
from .elements.tabs import Tabs, Tab, TabPanels, TabPanel
from .elements.table import Table
from .elements.progress import ProgressBar, CircularProgress, LinearProgress
from .elements.slider import Slider, Knob
from .elements.toggle import Toggle, Switch
from .elements.separator import Separator, Space, Divider
from .elements.menu import Menu, MenuItem, MenuSeparator, ContextMenu
from .elements.textarea import Textarea, Editor
from .elements.tooltip import Tooltip, Badge, Chip
from .elements.image import Image, Icon, Avatar
from .elements.link import Link, Markdown, Html, Code
from .elements.number import Number, ColorPicker, DatePicker, TimePicker
from .elements.scroll import ScrollArea, Expansion
from .elements.tree import Tree
from .elements.layout import Header, Footer, Drawer, LeftDrawer, RightDrawer, PageSticky, Grid, Splitter
from .elements.chat import ChatMessage, Log
from .elements.native_widget import NativeWidget

# Functions (decorators, timers, etc.)
from .functions import (
    refreshable,
    refreshable_method,
    state,
    timer,
    notify,
    navigate,
    run_javascript,
    add_css,
    add_head_html,
    add_body_html,
    download,
    page_title,
    update,
    Timer,
    State,
)

# Run function
from .run import run


# ============================================================================
# Element factory functions (NiceGUI style - lowercase)
# ============================================================================

def label(text: str = "") -> Label:
    """Create a text label."""
    return Label(text)


def button(
    text: str = "",
    *,
    on_click: Optional[Callable] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
    disabled: bool = False,
) -> Button:
    """Create a clickable button."""
    return Button(text, on_click=on_click, icon=icon, color=color, disabled=disabled)


def input(
    label: Optional[str] = "",
    *,
    placeholder: str = "",
    value: str = "",
    password: bool = False,
    on_change: Optional[Callable] = None,
) -> Input:
    """Create a text input field."""
    return Input(
        label=label,
        placeholder=placeholder,
        value=value,
        password=password,
        on_change=on_change,
    )


def row(*, wrap: bool = True) -> Row:
    """Create a horizontal layout container."""
    return Row(wrap=wrap)


def column(*, wrap: bool = False) -> Column:
    """Create a vertical layout container."""
    return Column(wrap=wrap)


def card() -> Card:
    """Create a card container."""
    return Card()


def card_section() -> CardSection:
    """Create a card section."""
    return CardSection()


def card_actions(*, align: str = "right") -> CardActions:
    """Create a card actions section."""
    return CardActions(align=align)


def navigation_bar(*, show_url: bool = True) -> NavigationBar:
    """Create a browser-like navigation bar."""
    return NavigationBar(show_url=show_url)


def checkbox(
    text: str = "",
    *,
    value: bool = False,
    on_change: Optional[Callable[[bool], None]] = None,
) -> Checkbox:
    """Create a checkbox for boolean input."""
    return Checkbox(text, value=value, on_change=on_change)


def dialog(
    *,
    value: bool = False,
    on_close: Optional[Callable] = None,
) -> Dialog:
    """Create a modal dialog."""
    return Dialog(value=value, on_close=on_close)


def notification(
    message: str,
    *,
    position: str = "bottom-right",
    type: str = "info",
    timeout: float = 3.0,
    close_button: bool = False,
) -> Notification:
    """Create a temporary notification message."""
    return Notification(
        message,
        position=position,
        type=type,
        timeout=timeout,
        close_button=close_button,
    )


def select(
    options: Union[List[Any], Dict[Any, str]],
    *,
    label: Optional[str] = None,
    value: Any = None,
    on_change: Optional[Callable[[Any], None]] = None,
    with_input: bool = False,
    multiple: bool = False,
    clearable: bool = False,
) -> Select:
    """Create a dropdown select."""
    return Select(
        options,
        label=label,
        value=value,
        on_change=on_change,
        with_input=with_input,
        multiple=multiple,
        clearable=clearable,
    )


def radio(
    options: Union[List[Any], Dict[Any, str]],
    *,
    value: Any = None,
    on_change: Optional[Callable[[Any], None]] = None,
) -> Radio:
    """Create a radio button group."""
    return Radio(options, value=value, on_change=on_change)


def tabs(
    *,
    value: Optional[str] = None,
    on_change: Optional[Callable[[str], None]] = None,
) -> Tabs:
    """Create a tabs container."""
    return Tabs(value=value, on_change=on_change)


def tab(
    name: str,
    label: Optional[str] = None,
    icon: Optional[str] = None,
) -> Tab:
    """Create a tab."""
    return Tab(name, label=label, icon=icon)


def tab_panels(
    tabs_element: Tabs,
    *,
    value: Optional[str] = None,
) -> TabPanels:
    """Create a tab panels container."""
    return TabPanels(tabs_element, value=value)


def tab_panel(name: str) -> TabPanel:
    """Create a tab panel."""
    return TabPanel(name)


def table(
    *,
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    row_key: str = "id",
    title: Optional[str] = None,
    selection: Optional[str] = None,
    pagination: Optional[int] = None,
    on_select: Optional[Callable[[List[Dict]], None]] = None,
) -> Table:
    """Create a data table."""
    return Table(
        columns=columns,
        rows=rows,
        row_key=row_key,
        title=title,
        selection=selection,
        pagination=pagination,
        on_select=on_select,
    )


def progress(
    value: float = 0.0,
    *,
    show_value: bool = False,
    size: Optional[str] = None,
) -> ProgressBar:
    """Create a progress bar."""
    return ProgressBar(value, show_value=show_value, size=size)


def linear_progress(
    value: float = 0.0,
    *,
    show_value: bool = False,
    size: Optional[str] = None,
) -> LinearProgress:
    """Create a linear progress bar (alias for progress)."""
    return LinearProgress(value, show_value=show_value, size=size)


def spinner(
    value: Optional[float] = None,
    *,
    size: Optional[str] = None,
) -> CircularProgress:
    """Create a spinner/circular progress."""
    return CircularProgress(value=value, size=size)


def slider(
    *,
    min: float = 0.0,
    max: float = 1.0,
    step: float = 0.01,
    value: Optional[float] = None,
    on_change: Optional[Callable[[float], None]] = None,
) -> Slider:
    """Create a slider."""
    return Slider(min=min, max=max, step=step, value=value, on_change=on_change)


def knob(
    *,
    min: float = 0.0,
    max: float = 1.0,
    step: float = 0.01,
    value: Optional[float] = None,
    show_value: bool = True,
    on_change: Optional[Callable[[float], None]] = None,
) -> Knob:
    """Create a knob."""
    return Knob(
        min=min,
        max=max,
        step=step,
        value=value,
        show_value=show_value,
        on_change=on_change,
    )


def toggle(
    text: str = "",
    *,
    value: bool = False,
    on_change: Optional[Callable[[bool], None]] = None,
) -> Toggle:
    """Create a toggle switch."""
    return Toggle(text, value=value, on_change=on_change)


def switch(
    text: str = "",
    *,
    value: bool = False,
    on_change: Optional[Callable[[bool], None]] = None,
) -> Switch:
    """Create a switch (alias for toggle)."""
    return Switch(text, value=value, on_change=on_change)


def separator(*, vertical: bool = False, char: Optional[str] = None) -> Separator:
    """Create a separator line."""
    return Separator(vertical=vertical, char=char)


def divider(*, vertical: bool = False, char: Optional[str] = None) -> Divider:
    """Create a divider (alias for separator)."""
    return Divider(vertical=vertical, char=char)


def space(*, width: int = 1, height: int = 1) -> Space:
    """Create empty space."""
    return Space(width=width, height=height)


def menu() -> Menu:
    """Create a popup menu."""
    return Menu()


def menu_item(
    text: str,
    on_click: Optional[Callable] = None,
    *,
    auto_close: bool = True,
) -> MenuItem:
    """Create a menu item."""
    return MenuItem(text, on_click=on_click, auto_close=auto_close)


def menu_separator() -> MenuSeparator:
    """Create a menu separator."""
    return MenuSeparator()


def context_menu() -> ContextMenu:
    """Create a context menu."""
    return ContextMenu()


def textarea(
    label: Optional[str] = None,
    *,
    placeholder: str = "",
    value: str = "",
    on_change: Optional[Callable[[str], None]] = None,
) -> Textarea:
    """Create a multiline text input."""
    return Textarea(
        label=label,
        placeholder=placeholder,
        value=value,
        on_change=on_change,
    )


def editor(
    label: Optional[str] = None,
    *,
    placeholder: str = "",
    value: str = "",
    language: Optional[str] = None,
    on_change: Optional[Callable[[str], None]] = None,
) -> Editor:
    """Create a code editor."""
    return Editor(
        label=label,
        placeholder=placeholder,
        value=value,
        language=language,
        on_change=on_change,
    )


def tooltip(text: str, *, delay: float = 0.5) -> Tooltip:
    """Create a tooltip."""
    return Tooltip(text, delay=delay)


def badge(
    text: str = "",
    *,
    color: Optional[str] = None,
    text_color: Optional[str] = None,
    outline: bool = False,
) -> Badge:
    """Create a badge."""
    return Badge(text, color=color, text_color=text_color, outline=outline)


def chip(
    text: str,
    *,
    icon: Optional[str] = None,
    color: Optional[str] = None,
    removable: bool = False,
    on_click: Optional[Callable] = None,
) -> Chip:
    """Create a chip."""
    return Chip(text, icon=icon, color=color, removable=removable, on_click=on_click)


def image(source: str = "", *, alt: str = "") -> Image:
    """Create an image."""
    return Image(source, alt=alt)


def icon(
    name: str,
    *,
    size: Optional[str] = None,
    color: Optional[str] = None,
) -> Icon:
    """Create an icon."""
    return Icon(name, size=size, color=color)


def avatar(
    text: Optional[str] = None,
    *,
    icon: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
) -> Avatar:
    """Create an avatar."""
    return Avatar(text, icon=icon, color=color, size=size)


def link(text: str, target: str = "", *, new_tab: bool = False) -> Link:
    """Create a hyperlink."""
    return Link(text, target, new_tab=new_tab)


def markdown(content: str = "") -> Markdown:
    """Create markdown content."""
    return Markdown(content)


def html(content: str = "") -> Html:
    """Create HTML content."""
    return Html(content)


def code(content: str = "", *, language: Optional[str] = None) -> Code:
    """Create a code block."""
    return Code(content, language=language)


def number(
    label: Optional[str] = None,
    *,
    placeholder: str = "",
    value: Optional[float] = None,
    min: Optional[float] = None,
    max: Optional[float] = None,
    step: float = 1.0,
    precision: Optional[int] = None,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    on_change: Optional[Callable[[Optional[float]], None]] = None,
) -> Number:
    """Create a number input."""
    return Number(
        label=label,
        placeholder=placeholder,
        value=value,
        min=min,
        max=max,
        step=step,
        precision=precision,
        prefix=prefix,
        suffix=suffix,
        on_change=on_change,
    )


def color_picker(
    label: Optional[str] = None,
    *,
    value: str = "#000000",
    on_change: Optional[Callable[[str], None]] = None,
) -> ColorPicker:
    """Create a color picker."""
    return ColorPicker(label=label, value=value, on_change=on_change)


def date(
    label: Optional[str] = None,
    *,
    value: Optional[str] = None,
    on_change: Optional[Callable[[str], None]] = None,
) -> DatePicker:
    """Create a date picker."""
    return DatePicker(label=label, value=value, on_change=on_change)


def time(
    label: Optional[str] = None,
    *,
    value: Optional[str] = None,
    on_change: Optional[Callable[[str], None]] = None,
) -> TimePicker:
    """Create a time picker."""
    return TimePicker(label=label, value=value, on_change=on_change)


def scroll_area() -> ScrollArea:
    """Create a scrollable area."""
    return ScrollArea()


def expansion(
    text: str = "",
    *,
    value: bool = False,
    icon: Optional[str] = None,
) -> Expansion:
    """Create an expandable panel."""
    return Expansion(text, value=value, icon=icon)


def tree(
    nodes: List[Dict[str, Any]],
    *,
    label_key: str = "label",
    children_key: str = "children",
    node_key: str = "id",
    on_select: Optional[Callable[[Dict], None]] = None,
    on_expand: Optional[Callable[[Dict], None]] = None,
    tick_strategy: Optional[str] = None,
) -> Tree:
    """Create a tree view."""
    return Tree(
        nodes,
        label_key=label_key,
        children_key=children_key,
        node_key=node_key,
        on_select=on_select,
        on_expand=on_expand,
        tick_strategy=tick_strategy,
    )


def header(*, value: bool = True, fixed: bool = True) -> Header:
    """Create a page header."""
    return Header(value=value, fixed=fixed)


def footer(*, value: bool = True, fixed: bool = True) -> Footer:
    """Create a page footer."""
    return Footer(value=value, fixed=fixed)


def drawer(
    side: str = "left",
    *,
    value: bool = False,
    fixed: bool = True,
) -> Drawer:
    """Create a side drawer."""
    return Drawer(side, value=value, fixed=fixed)


def left_drawer(*, value: bool = False, fixed: bool = True) -> LeftDrawer:
    """Create a left-side drawer."""
    return LeftDrawer(value=value, fixed=fixed)


def right_drawer(*, value: bool = False, fixed: bool = True) -> RightDrawer:
    """Create a right-side drawer."""
    return RightDrawer(value=value, fixed=fixed)


def page_sticky(
    position: str = "bottom-right",
    *,
    x_offset: int = 0,
    y_offset: int = 0,
) -> PageSticky:
    """Create a sticky positioned element."""
    return PageSticky(position, x_offset=x_offset, y_offset=y_offset)


def grid(columns: int = 2, *, rows: Optional[int] = None) -> Grid:
    """Create a grid layout."""
    return Grid(columns=columns, rows=rows)


def splitter(*, horizontal: bool = False, value: int = 50) -> Splitter:
    """Create a resizable split pane."""
    return Splitter(horizontal=horizontal, value=value)


def chat_message(
    text: str = "",
    *,
    name: Optional[str] = None,
    stamp: Optional[str] = None,
    avatar: Optional[str] = None,
    sent: bool = False,
) -> ChatMessage:
    """Create a chat message bubble."""
    return ChatMessage(text, name=name, stamp=stamp, avatar=avatar, sent=sent)


def log(max_lines: Optional[int] = None) -> Log:
    """Create a log display."""
    return Log(max_lines=max_lines)


def native_widget(
    widget_factory: Callable,
    *,
    width: int = 200,
    height: int = 100,
) -> NativeWidget:
    """Create a placeholder for a native Tkinter widget.

    This is for exceptional cases where RawGUI doesn't provide an equivalent.
    99% of UI should use standard RawGUI elements.

    Args:
        widget_factory: Callable that receives a parent Frame and returns a Tkinter widget
        width: Width in pixels
        height: Height in pixels

    Example:
        def create_scale(parent):
            import tkinter as tk
            return tk.Scale(parent, from_=0, to=100, orient=tk.HORIZONTAL)

        ui.native_widget(create_scale, width=200, height=50)
    """
    return NativeWidget(widget_factory, width=width, height=height)


def circular_progress(
    value: Optional[float] = None,
    *,
    size: Optional[str] = None,
) -> CircularProgress:
    """Create a circular progress indicator."""
    return CircularProgress(value=value, size=size)


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
    # Functions/decorators
    "refreshable",
    "refreshable_method",
    "state",
    "timer",
    "notify",
    "run_javascript",
    "add_css",
    "add_head_html",
    "add_body_html",
    "download",
    "page_title",
    "update",
    "Timer",
    "State",
    # Factory functions
    "label",
    "button",
    "input",
    "row",
    "column",
    "card",
    "card_section",
    "card_actions",
    "navigation_bar",
    "header",
    "footer",
    "drawer",
    "left_drawer",
    "right_drawer",
    "page_sticky",
    "grid",
    "splitter",
    "checkbox",
    "dialog",
    "notification",
    "select",
    "radio",
    "tabs",
    "tab",
    "tab_panels",
    "tab_panel",
    "table",
    "progress",
    "linear_progress",
    "circular_progress",
    "spinner",
    "slider",
    "knob",
    "toggle",
    "switch",
    "separator",
    "divider",
    "space",
    "menu",
    "menu_item",
    "menu_separator",
    "context_menu",
    "textarea",
    "editor",
    "tooltip",
    "badge",
    "chip",
    "image",
    "icon",
    "avatar",
    "link",
    "markdown",
    "html",
    "code",
    "number",
    "color_picker",
    "date",
    "time",
    "scroll_area",
    "expansion",
    "tree",
    "chat_message",
    "log",
    "native_widget",
    # Element classes
    "Label",
    "Button",
    "Input",
    "Row",
    "Column",
    "Card",
    "CardSection",
    "CardActions",
    "NavigationBar",
    "Header",
    "Footer",
    "Drawer",
    "LeftDrawer",
    "RightDrawer",
    "PageSticky",
    "Grid",
    "Splitter",
    "Checkbox",
    "Dialog",
    "Notification",
    "Select",
    "Radio",
    "Tabs",
    "Tab",
    "TabPanels",
    "TabPanel",
    "Table",
    "ProgressBar",
    "CircularProgress",
    "LinearProgress",
    "Slider",
    "Knob",
    "Toggle",
    "Switch",
    "Separator",
    "Divider",
    "Space",
    "Menu",
    "MenuItem",
    "MenuSeparator",
    "ContextMenu",
    "Textarea",
    "Editor",
    "Tooltip",
    "Badge",
    "Chip",
    "Image",
    "Icon",
    "Avatar",
    "Link",
    "Markdown",
    "Html",
    "Code",
    "Number",
    "ColorPicker",
    "DatePicker",
    "TimePicker",
    "ScrollArea",
    "Expansion",
    "Tree",
    "ChatMessage",
    "Log",
    "NativeWidget",
]
