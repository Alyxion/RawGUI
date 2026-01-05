#!/usr/bin/env python3
"""Test blessed input in same context as run.py."""
import sys
sys.path.insert(0, '/projects/RawGUI')

from blessed import Terminal

term = Terminal()

print("Testing blessed input with fullscreen context...")
print("Press keys to see their codes. Ctrl+C or 'q' to quit.")
print()

with term.fullscreen(), term.cbreak(), term.hidden_cursor():
    # Enable mouse tracking like run.py does
    print(term.enter_mouse_tracking, end="", flush=True)

    try:
        running = True
        while running:
            key = term.inkey(timeout=0.05)
            if key:
                # Print key info
                info = f"Key: repr={repr(key)}, name={key.name}, code={key.code}, is_sequence={key.is_sequence}"
                print(term.move_xy(0, 5) + term.clear_eol + info)

                # Check quit conditions
                if key.code == 3:  # Ctrl+C
                    print(term.move_xy(0, 7) + "Ctrl+C detected!")
                    running = False
                elif key.code == 27 or key.name == "KEY_ESCAPE":
                    print(term.move_xy(0, 7) + "Escape detected!")
                    running = False
                elif str(key) == 'q':
                    print(term.move_xy(0, 7) + "'q' detected!")
                    running = False
    finally:
        print(term.exit_mouse_tracking, end="", flush=True)

print("\nDone!")
