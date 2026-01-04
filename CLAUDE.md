# RawGUI - Project Context

## Overview

RawGUI is a TUI (Terminal User Interface) version of NiceGUI built with Python and the `blessed` library.

## Tech Stack

- **Python**: 3.12 to <4.0
- **Package Manager**: Poetry
- **TUI Framework**: blessed
- **Testing**: pexpect, pyte, Pillow, Selenium (for NiceGUI comparison)

## Core Principles

### NiceGUI Compatibility

- **100% API matching** with NiceGUI (at least high-level calls)
- Drop-in replacement: `from nicegui import ui` → `from rawgui import ui`
- Context-based element creation using `with` statements
- Root elements detect which pages they are created on
- Pages defined via `@ui.page` decorators or `ui.sub_pages`

### Browser-Like Behavior

- Pages with URLs and navigation
- Main scrollview for entire content (can be forced hidden)
- Nested scrollviews supported
- Full mouse support (clicks, hover, drag)

### Auto-Reload

- File watching like NiceGUI's development mode
- Automatic refresh on Python file changes

## Architecture

```
rawgui/
├── __init__.py          # Package exports
├── ui.py                # Main ui module (NiceGUI-compatible)
├── app.py               # Application singleton, storage
├── context.py           # Task-local context (slot_stack, client)
├── client.py            # Client class (per-session state)
├── page.py              # @ui.page decorator
├── slot.py              # Slot class for element nesting
├── element.py           # Base Element class
├── elements/            # UI element implementations
├── renderer/            # Blessed rendering engine
│   ├── terminal.py      # Terminal singleton
│   ├── layout.py        # Layout calculation
│   └── styles.py        # CSS → terminal mapping
├── run.py               # ui.run() implementation
└── testing/             # Testing utilities
    └── subprocess_terminal.py  # PTY-based testing
```

## Style System

- `.classes()` maps Tailwind-like classes to terminal attributes
- `.style()` for inline CSS-style properties
- Mimic browser behavior for styles and classes

## Graphics Rendering

- Detect terminal capabilities
- Prefer RGB halfpixel / sixel graphics where supported
- Fallback to ASCII art otherwise

## Testing Approach

- SubprocessTerminal: PTY-based testing similar to Selenium
- Capture screenshots of NiceGUI samples via Selenium
- Compare TUI output to web rendering
- Goal: Make TUI samples as close as possible to NiceGUI

## Commands

```bash
poetry install          # Install dependencies
poetry run rawgui       # Run the application
poetry run pytest       # Run tests
```

## Reference

- NiceGUI documentation: https://raw.githubusercontent.com/Alyxion/nice-vibes/refs/heads/main/output/nice_vibes_extended.md
