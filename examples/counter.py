#!/usr/bin/env python3
"""Counter example demonstrating state and events.

Run with: poetry run python examples/counter.py
Press Escape or Ctrl+C to quit.
"""

from rawgui import ui


# Simple state
class State:
    count = 0


def increment():
    State.count += 1
    ui.navigate.to("/")  # Re-render


def decrement():
    State.count -= 1
    ui.navigate.to("/")


def reset():
    State.count = 0
    ui.navigate.to("/")


@ui.page("/")
def index():
    with ui.column().classes("gap-2 p-2"):
        ui.label("Counter Demo").classes("text-bold text-cyan")

        with ui.card():
            ui.label(f"Count: {State.count}").classes("text-bold")

            with ui.row().classes("gap-2"):
                ui.button("- Decrement", on_click=decrement)
                ui.button("Reset", on_click=reset).classes("text-yellow")
                ui.button("+ Increment", on_click=increment).classes("text-green")

        ui.label("").classes("")
        ui.label("Tab between buttons, Enter to activate").classes("text-bright_black")
        ui.label("Press Escape or Ctrl+C to quit").classes("text-bright_black")


if __name__ == "__main__":
    ui.run(title="Counter", reload=False)
