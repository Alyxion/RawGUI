#!/usr/bin/env python3
"""Demo of dialog shadow rendering - Norton Commander style.

This shows how the layered rendering system creates shadows
under floating dialogs.
"""

from rawgui.renderer.layers import Cell, Layer, LayerCompositor
from rawgui.renderer.styles import TerminalStyle

# Create a compositor with 80x24 terminal size
compositor = LayerCompositor(80, 24)

# Get the base layer and fill it with content
base = compositor.get_layer("base")

# Draw a "desktop" background with some text
desktop_style = TerminalStyle(fg_color="cyan")
for y in range(base.height):
    for x in range(base.width):
        # Checkerboard pattern
        char = "." if (x + y) % 2 == 0 else " "
        base.set_cell(x, y, char, desktop_style)

# Draw some "files" on the desktop
file_style = TerminalStyle(fg_color="white", bold=True)
files = [
    (5, 3, "[ README.txt ]"),
    (5, 5, "[ config.py  ]"),
    (5, 7, "[ main.py    ]"),
    (25, 3, "[ data/      ]"),
    (25, 5, "[ tests/     ]"),
]
for x, y, text in files:
    for i, char in enumerate(text):
        base.set_cell(x + i, y, char, file_style)

# Draw title bar
title_style = TerminalStyle(fg_color="black", bg_color="cyan", bold=True)
title = " Norton Commander Clone - RawGUI Demo "
title = title.center(80)
for x, char in enumerate(title):
    base.set_cell(x, 0, char, title_style)

# Add a dialog layer with shadow
dialog_width = 40
dialog_height = 10
dialog_x = 20
dialog_y = 7

dialog = compositor.add_layer(
    "dialog",
    z_index=10,
    has_shadow=True,
    x=dialog_x,
    y=dialog_y,
    width=dialog_width,
    height=dialog_height,
)

# Draw dialog border and content
dialog_border_style = TerminalStyle(fg_color="white", bg_color="blue")
dialog_content_style = TerminalStyle(fg_color="white", bg_color="blue")
dialog_title_style = TerminalStyle(fg_color="yellow", bg_color="blue", bold=True)
dialog_button_style = TerminalStyle(fg_color="black", bg_color="cyan")

# Fill dialog background
for y in range(dialog_height):
    for x in range(dialog_width):
        dialog.set_cell(x, y, " ", dialog_content_style)

# Draw border
border_chars = {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"}

# Corners
dialog.set_cell(0, 0, border_chars["tl"], dialog_border_style)
dialog.set_cell(dialog_width - 1, 0, border_chars["tr"], dialog_border_style)
dialog.set_cell(0, dialog_height - 1, border_chars["bl"], dialog_border_style)
dialog.set_cell(dialog_width - 1, dialog_height - 1, border_chars["br"], dialog_border_style)

# Horizontal borders
for x in range(1, dialog_width - 1):
    dialog.set_cell(x, 0, border_chars["h"], dialog_border_style)
    dialog.set_cell(x, dialog_height - 1, border_chars["h"], dialog_border_style)

# Vertical borders
for y in range(1, dialog_height - 1):
    dialog.set_cell(0, y, border_chars["v"], dialog_border_style)
    dialog.set_cell(dialog_width - 1, y, border_chars["v"], dialog_border_style)

# Dialog title
title = " Confirm Delete "
title_x = (dialog_width - len(title)) // 2
for i, char in enumerate(title):
    dialog.set_cell(title_x + i, 0, char, dialog_title_style)

# Dialog content
message = "Are you sure you want to delete"
file_name = "README.txt"
question = "this file?"

msg_x = (dialog_width - len(message)) // 2
dialog_set_text = lambda x, y, text, style: [dialog.set_cell(x + i, y, c, style) for i, c in enumerate(text)]

for i, char in enumerate(message):
    dialog.set_cell(msg_x + i, 3, char, dialog_content_style)

file_x = (dialog_width - len(file_name)) // 2
file_style = TerminalStyle(fg_color="yellow", bg_color="blue", bold=True)
for i, char in enumerate(file_name):
    dialog.set_cell(file_x + i, 5, char, file_style)

q_x = (dialog_width - len(question)) // 2
for i, char in enumerate(question):
    dialog.set_cell(q_x + i, 4, char, dialog_content_style)

# Buttons
yes_btn = "[ Yes ]"
no_btn = "[ No ]"
btn_y = dialog_height - 2
yes_x = dialog_width // 2 - len(yes_btn) - 2
no_x = dialog_width // 2 + 2

for i, char in enumerate(yes_btn):
    dialog.set_cell(yes_x + i, btn_y, char, dialog_button_style)

for i, char in enumerate(no_btn):
    dialog.set_cell(no_x + i, btn_y, char, dialog_button_style)

# Composite and render
composite = compositor.composite()

# Print the result with ANSI colors
def get_ansi_color(color_name):
    """Convert color name to ANSI code."""
    colors = {
        "black": 30, "red": 31, "green": 32, "yellow": 33,
        "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
        "bright_black": 90, "bright_red": 91, "bright_green": 92,
        "bright_yellow": 93, "bright_blue": 94, "bright_magenta": 95,
        "bright_cyan": 96, "bright_white": 97,
    }
    return colors.get(color_name, 37)

def get_ansi_bg_color(color_name):
    """Convert color name to ANSI background code."""
    return get_ansi_color(color_name) + 10

print("\033[2J\033[H")  # Clear screen
print("=" * 80)
print("Dialog Shadow Demo - Norton Commander Style")
print("=" * 80)
print()

for y, row in enumerate(composite):
    line = ""
    for x, cell in enumerate(row):
        char = cell.char if cell.char else " "
        style = cell.style

        if style:
            codes = []
            if style.bold:
                codes.append("1")
            if style.fg_color:
                codes.append(str(get_ansi_color(style.fg_color)))
            if style.bg_color:
                codes.append(str(get_ansi_bg_color(style.bg_color)))

            if codes:
                line += f"\033[{';'.join(codes)}m{char}\033[0m"
            else:
                line += char
        else:
            line += char

    print(line)

print()
print("=" * 80)
print("Notice the shadow (darker area) to the right and below the dialog!")
print("This is the Norton Commander-style shadow effect from LayerCompositor.")
print("=" * 80)
