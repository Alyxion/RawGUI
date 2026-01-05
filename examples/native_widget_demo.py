#!/usr/bin/env python3
"""Demo showing native Tkinter widgets embedded in RawGUI.

This demonstrates the native_widget feature which allows embedding
real Tkinter widgets within RawGUI layouts. This is for exceptional
cases only - 99% of UI should use standard RawGUI elements.

Run with: RAWGUI_RENDERER=tkinter poetry run python examples/native_widget_demo.py
"""

from rawgui import ui


# State for the demo
class State:
    slider_value: int = 50
    text_content: str = "Edit this text in the native Tkinter Text widget!"
    scale_value: int = 0


# ============================================================================
# Native widget factory functions
# These receive a parent Frame and return a Tkinter widget
# ============================================================================

def create_scale_widget(parent):
    """Create a native Tkinter Scale (slider) widget."""
    import tkinter as tk

    def on_change(value):
        State.scale_value = int(float(value))
        # Note: In a real app you'd trigger a re-render here

    scale = tk.Scale(
        parent,
        from_=0,
        to=100,
        orient=tk.HORIZONTAL,
        label="Native Scale",
        command=on_change,
        bg="#2d2d2d",
        fg="#ffffff",
        troughcolor="#404040",
        highlightthickness=0,
        length=250,
    )
    scale.set(State.slider_value)
    return scale


def create_text_widget(parent):
    """Create a native Tkinter Text widget."""
    import tkinter as tk

    text = tk.Text(
        parent,
        height=6,
        width=40,
        bg="#1e1e1e",
        fg="#e0e0e0",
        insertbackground="#00bcd4",
        selectbackground="#00bcd4",
        selectforeground="#000000",
        font=("Roboto", 11),
        wrap=tk.WORD,
        padx=8,
        pady=8,
    )
    text.insert("1.0", State.text_content)
    return text


def create_listbox_widget(parent):
    """Create a native Tkinter Listbox widget."""
    import tkinter as tk

    # Create frame with scrollbar
    frame = tk.Frame(parent, bg="#2d2d2d")

    scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(
        frame,
        yscrollcommand=scrollbar.set,
        bg="#1e1e1e",
        fg="#e0e0e0",
        selectbackground="#00bcd4",
        selectforeground="#000000",
        font=("Roboto", 11),
        height=5,
        highlightthickness=0,
    )

    # Add sample items
    items = [
        "Item 1 - Native Listbox",
        "Item 2 - Scrollable",
        "Item 3 - Selectable",
        "Item 4 - Tkinter Widget",
        "Item 5 - In RawGUI Layout",
        "Item 6 - More items...",
        "Item 7 - Keep scrolling",
        "Item 8 - Almost there",
        "Item 9 - Last one",
        "Item 10 - The end!",
    ]
    for item in items:
        listbox.insert(tk.END, item)

    scrollbar.config(command=listbox.yview)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    return frame


def create_canvas_widget(parent):
    """Create a native Tkinter Canvas with some drawings."""
    import tkinter as tk

    canvas = tk.Canvas(
        parent,
        bg="#1e1e1e",
        highlightthickness=0,
    )

    # Draw some shapes
    canvas.create_rectangle(20, 20, 80, 80, fill="#4caf50", outline="#81c784")
    canvas.create_oval(100, 20, 160, 80, fill="#2196f3", outline="#64b5f6")
    canvas.create_polygon(200, 80, 230, 20, 260, 80, fill="#ff9800", outline="#ffb74d")

    # Add text
    canvas.create_text(140, 100, text="Native Canvas", fill="#ffffff", font=("Roboto", 10))

    return canvas


# ============================================================================
# Page definition using standard RawGUI API
# ============================================================================

@ui.page("/")
def index():
    with ui.column().classes("gap-4 p-4"):
        ui.label("RawGUI + Native Tkinter Widgets Demo").classes("text-bold text-cyan")
        ui.label("Demonstrating embedded native widgets within RawGUI layout")

        # First row: RawGUI card with native Scale
        with ui.card():
            ui.label("Native Scale Widget").classes("text-bold")
            ui.label("A real Tkinter Scale embedded in RawGUI:")
            ui.native_widget(create_scale_widget, width=280, height=60)

        # Second row: Two cards side by side
        with ui.row().classes("gap-4"):
            # Left card: Native Text widget
            with ui.card():
                ui.label("Native Text Editor").classes("text-bold")
                ui.native_widget(create_text_widget, width=320, height=150)

            # Right card: Native Listbox
            with ui.card():
                ui.label("Native Listbox").classes("text-bold")
                ui.native_widget(create_listbox_widget, width=200, height=150)

        # Third row: Native Canvas
        with ui.card():
            ui.label("Native Canvas Drawing").classes("text-bold")
            ui.native_widget(create_canvas_widget, width=300, height=120)

        # Standard RawGUI elements below
        with ui.card():
            ui.label("Standard RawGUI Elements").classes("text-bold")
            with ui.row().classes("gap-2"):
                ui.button("RawGUI Button 1")
                ui.button("RawGUI Button 2")
            ui.input(label="RawGUI Input", placeholder="Type here...")
            ui.checkbox("RawGUI Checkbox")

        ui.label("Native widgets are the exception - use RawGUI elements when possible").classes("text-bright_black")


if __name__ == "__main__":
    ui.run(title="Native Widget Demo", reload=False)
