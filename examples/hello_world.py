#!/usr/bin/env python3
"""Simple RawGUI example - Hello World.

Run with: poetry run python examples/hello_world.py
Press Escape or Ctrl+C to quit.
"""

from rawgui import ui


@ui.page("/")
def index():
    """Simple hello world page."""
    with ui.column().classes("gap-2 p-2"):
        ui.label("Hello, RawGUI!").classes("text-bold text-cyan")
        ui.label("This is a fully functional TUI built with blessed.")

        with ui.card():
            ui.label("Features:").classes("text-bold")
            ui.label("  • Tab to navigate between elements")
            ui.label("  • Enter to activate buttons")
            ui.label("  • Type in input fields")
            ui.label("  • Styled text and borders")

        with ui.row().classes("gap-2"):
            ui.button("Button 1", on_click=lambda: print("Button 1!"))
            ui.button("Button 2", on_click=lambda: print("Button 2!"))

        ui.input(label="Your name", placeholder="Type here...")

        ui.label("").classes("")
        ui.label("Press Escape or Ctrl+C to quit").classes("text-bright_black")


if __name__ == "__main__":
    ui.run(title="Hello RawGUI", reload=False)
