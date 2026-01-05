#!/usr/bin/env python3
"""Debug input handling - run this to see what keys blessed receives.

This is useful for debugging keyboard/mouse issues.
"""
from nicegui import ui

# Store debug info
debug_info = {"last_key": "None", "count": 0}

@ui.page("/")
def index():
    ui.label("Input Debug Mode")
    ui.label("Press keys to see them logged.")
    ui.label("Press q, Escape, or Ctrl+C to quit.")
    ui.label("")

    with ui.row():
        ui.button("Button 1")
        ui.button("Button 2")

    ui.checkbox("Test Checkbox")
    ui.input("Test Input")

ui.run(reload=False)
