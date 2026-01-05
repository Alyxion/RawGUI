#!/usr/bin/env python3
"""Debug runner to test keyboard input."""
import sys
sys.path.insert(0, '/projects/RawGUI')

from blessed import Terminal

term = Terminal()

def debug_keys():
    """Debug key input - shows what blessed receives."""
    print("Debug Key Tester")
    print("================")
    print("Press any key to see its properties.")
    print("Press 'q', Ctrl+C, or Escape to quit.")
    print()

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        # Enable mouse tracking
        print(term.enter_mouse_tracking, end="", flush=True)

        try:
            line = 0
            while True:
                key = term.inkey(timeout=0.1)
                if key:
                    # Display key info
                    info_lines = [
                        f"Key received:",
                        f"  str(key) = {repr(str(key))}",
                        f"  key.name = {key.name}",
                        f"  key.code = {key.code}",
                        f"  key.is_sequence = {key.is_sequence}",
                        f"  len(key) = {len(key)}",
                    ]

                    # Check specific key values
                    key_str = str(key)
                    if key_str == '\x03':
                        info_lines.append("  -> Ctrl+C detected! Exiting...")
                        print(term.clear())
                        for i, line_text in enumerate(info_lines):
                            print(term.move_xy(0, i) + line_text)
                        break
                    elif key_str == '\x1b' or key.name == "KEY_ESCAPE":
                        info_lines.append("  -> Escape detected! Exiting...")
                        print(term.clear())
                        for i, line_text in enumerate(info_lines):
                            print(term.move_xy(0, i) + line_text)
                        break
                    elif key_str == 'q':
                        info_lines.append("  -> 'q' detected! Exiting...")
                        print(term.clear())
                        for i, line_text in enumerate(info_lines):
                            print(term.move_xy(0, i) + line_text)
                        break
                    elif key.name == "KEY_TAB":
                        info_lines.append("  -> Tab detected!")
                    elif "MOUSE" in str(key.name or ""):
                        info_lines.append("  -> Mouse event detected!")

                    # Print info
                    print(term.clear())
                    for i, line_text in enumerate(info_lines):
                        print(term.move_xy(0, i) + line_text)

        finally:
            print(term.exit_mouse_tracking, end="", flush=True)

    print("\n\nExited debug mode.")

if __name__ == "__main__":
    debug_keys()
