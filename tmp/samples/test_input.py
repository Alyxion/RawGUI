#!/usr/bin/env python3
"""Simple input test for RawGUI."""
from nicegui import ui

# Track keypresses
key_log = []

@ui.page("/")
def index():
    ui.label("RawGUI Input Test")
    ui.label("Press Tab to navigate, Enter to click, q/Esc to quit")

    with ui.row():
        ui.button("Button 1", on_click=lambda: ui.notify("Clicked 1!"))
        ui.button("Button 2", on_click=lambda: ui.notify("Clicked 2!"))
        ui.button("Button 3", on_click=lambda: ui.notify("Clicked 3!"))

    with ui.column():
        ui.checkbox("Option A")
        ui.checkbox("Option B", value=True)

    ui.input("Name", placeholder="Type here")

ui.run(reload=False)
