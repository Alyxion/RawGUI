"""Main entry point for RawGUI demo application.

Demonstrates all Tier 1 elements with full interactivity.
"""

from __future__ import annotations

from . import ui


# State for the demo
class DemoState:
    counter: int = 0
    name: str = ""
    password: str = ""
    messages: list = []


state = DemoState()


def increment():
    """Increment counter and update display."""
    state.counter += 1
    state.messages.append(f"Counter: {state.counter}")
    # Force re-render by navigating to same page
    ui.navigate.to("/")


def decrement():
    """Decrement counter."""
    state.counter -= 1
    state.messages.append(f"Counter: {state.counter}")
    ui.navigate.to("/")


def on_name_change(value):
    """Handle name input change."""
    state.name = value


def on_password_change(value):
    """Handle password input change."""
    state.password = value


def submit_form():
    """Handle form submission."""
    state.messages.append(f"Submitted: {state.name}")
    ui.navigate.to("/")


@ui.page("/")
def index():
    """Demo index page showcasing all Tier 1 elements."""
    with ui.column().classes("gap-2 p-2"):
        # Title
        ui.label("RawGUI Demo").classes("text-bold text-cyan")
        ui.label("A TUI version of NiceGUI").classes("text-bright_black")

        # Counter section in a card
        with ui.card():
            ui.label(f"Counter: {state.counter}").classes("text-bold")

            with ui.row().classes("gap-2"):
                ui.button("- Decrement", on_click=decrement)
                ui.button("+ Increment", on_click=increment).classes("text-green")

        # Form section
        with ui.card():
            ui.label("Form Demo").classes("text-bold")

            ui.input(
                label="Name",
                placeholder="Enter your name",
                value=state.name,
                on_change=on_name_change,
            )

            ui.input(
                label="Password",
                placeholder="Enter password",
                password=True,
                value=state.password,
                on_change=on_password_change,
            )

            ui.button("Submit", on_click=submit_form).classes("text-blue")

        # Messages log
        if state.messages:
            with ui.card():
                ui.label("Activity Log").classes("text-bold")
                # Show last 5 messages
                for msg in state.messages[-5:]:
                    ui.label(f"  {msg}").classes("text-bright_black")

        # Instructions
        ui.label("").classes("")  # spacer
        ui.label("Controls:").classes("text-bold")
        ui.label("  Tab/Shift+Tab: Navigate between elements")
        ui.label("  Enter: Activate button / Submit")
        ui.label("  Type: Enter text in focused input")
        ui.label("  Backspace: Delete character")
        ui.label("  Escape/Ctrl+C: Quit")


def main() -> None:
    """Run the RawGUI demo."""
    ui.run(title="RawGUI Demo", reload=False)


if __name__ == "__main__":
    main()
