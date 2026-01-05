"""Main entry point for RawGUI CLI runner.

Supports running any RawGUI/NiceGUI app with different renderers:
  rawgui my_app.py                    # TUI mode (default)
  rawgui --renderer=tkinter my_app.py # Tkinter mode
  rawgui --renderer=nicegui my_app.py # NiceGUI mode

If no script is provided, runs the built-in demo.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def run_demo():
    """Run the built-in RawGUI demo."""
    from . import ui

    # State for the demo
    class DemoState:
        counter: int = 0
        name: str = ""
        password: str = ""
        messages: list = []

    state = DemoState()

    def increment():
        state.counter += 1
        state.messages.append(f"Counter: {state.counter}")
        ui.navigate.to("/")

    def decrement():
        state.counter -= 1
        state.messages.append(f"Counter: {state.counter}")
        ui.navigate.to("/")

    def on_name_change(value):
        state.name = value

    def on_password_change(value):
        state.password = value

    def submit_form():
        state.messages.append(f"Submitted: {state.name}")
        ui.navigate.to("/")

    @ui.page("/")
    def index():
        with ui.column().classes("gap-2 p-2"):
            ui.label("RawGUI Demo").classes("text-bold text-cyan")
            ui.label("A TUI version of NiceGUI").classes("text-bright_black")

            with ui.card():
                ui.label(f"Counter: {state.counter}").classes("text-bold")
                with ui.row().classes("gap-2"):
                    ui.button("- Decrement", on_click=decrement)
                    ui.button("+ Increment", on_click=increment).classes("text-green")

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

            if state.messages:
                with ui.card():
                    ui.label("Activity Log").classes("text-bold")
                    for msg in state.messages[-5:]:
                        ui.label(f"  {msg}").classes("text-bright_black")

            ui.label("").classes("")
            ui.label("Controls:").classes("text-bold")
            ui.label("  Tab/Shift+Tab: Navigate between elements")
            ui.label("  Arrow keys: Navigate between components")
            ui.label("  Enter: Activate / Toggle edit mode")
            ui.label("  Escape: Exit edit mode / Quit")

    ui.run(title="RawGUI Demo", reload=False)


def run_script(script_path: str):
    """Run a RawGUI/NiceGUI script.

    The script should import from rawgui (or nicegui - we'll intercept).
    """
    script = Path(script_path).resolve()
    if not script.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    # Add script's directory to Python path
    script_dir = str(script.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Execute the script
    with open(script) as f:
        code = compile(f.read(), script, "exec")
        exec(code, {"__name__": "__main__", "__file__": str(script)})


def main() -> None:
    """RawGUI CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="rawgui",
        description="Run RawGUI/NiceGUI applications with different renderers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rawgui                               Run built-in demo (TUI mode)
  rawgui my_app.py                     Run script in TUI mode
  rawgui --renderer=tkinter my_app.py  Run script with Tkinter GUI
  rawgui --renderer=nicegui my_app.py  Run script with actual NiceGUI

Environment variable RAWGUI_RENDERER can also be used:
  RAWGUI_RENDERER=tkinter rawgui my_app.py
""",
    )

    parser.add_argument(
        "script",
        nargs="?",
        help="Python script to run (if omitted, runs built-in demo)",
    )

    parser.add_argument(
        "--renderer",
        "-r",
        choices=["tui", "tkinter", "nicegui"],
        default=None,
        help="Rendering backend: tui (default), tkinter, or nicegui",
    )

    args = parser.parse_args()

    # Set renderer via environment variable (takes precedence in run())
    if args.renderer:
        os.environ["RAWGUI_RENDERER"] = args.renderer

    if args.script:
        run_script(args.script)
    else:
        run_demo()


if __name__ == "__main__":
    main()
