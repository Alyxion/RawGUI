#!/usr/bin/env python3
"""Simple test sample for RawGUI."""
from nicegui import ui

ui.label('Hello RawGUI!')

with ui.row():
    ui.button('Button 1')
    ui.button('Button 2')
    ui.button('Button 3')

with ui.column():
    ui.checkbox('Option A')
    ui.checkbox('Option B', value=True)

ui.input('Name', placeholder='Enter your name')

ui.run()
