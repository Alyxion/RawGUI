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
- **Implicit root page**: Elements created at module scope (without `@ui.page`) are automatically assigned to the `/` route. This is NiceGUI's minimalistic approach for simple apps.

### Browser-Like Behavior

- Pages with URLs and navigation
- Main scrollview for entire content (can be forced hidden)
- Nested scrollviews supported
- Full mouse support (clicks, hover, drag)

### Auto-Reload

- File watching like NiceGUI's development mode
- Automatic refresh on Python file changes

## Pixel-First Layout Architecture

**CRITICAL: All layout calculations MUST think in pixels first, then convert to ASCII.**

### Multi-Session Support

- The system MUST support multiple concurrent sessions
- Each session can have different terminal dimensions and scaling factors
- **NEVER use global variables for session-specific state**
- Store all configuration in a per-session context (e.g., `SessionConfig`)

### Session Configuration

Each session has its own configuration lookup dictionary:

```python
class SessionConfig:
    """Per-session configuration - NOT global."""

    # Scaling factors (can vary per terminal)
    char_width_px: int = 12   # Default: 1 column = 12px
    char_height_px: int = 24  # Default: 1 row = 24px

    # CSS-like properties lookup
    sizes: Dict[str, int] = {}
    colors: Dict[str, str] = {}
    spacing: Dict[str, int] = {}
```

### Minimalistic DOM

Implement a lightweight HTML DOM-like structure where:
- Each element has pixel-based position (x, y) and size (width, height)
- Layout is calculated in pixel coordinates
- Final rendering converts pixels → ASCII characters
- All scaling uses session-specific config, not global constants

### Pixel-Perfect Alignment Rules

1. **All sizes and paddings MUST be multiples of the scaling constants**
   - Padding: multiples of 12px (width) or 24px (height)
   - Element widths: multiples of 12px
   - Element heights: multiples of 24px

2. **When converting pixel → ASCII:**
   ```python
   ascii_col = pixel_x // CHAR_WIDTH_PX   # Always clean division
   ascii_row = pixel_y // CHAR_HEIGHT_PX  # No remainder
   ```

3. **Nested elements must align cleanly**
   - Cards, rows, columns calculate child positions in pixels
   - Final coordinates always divide evenly by scaling constants
   - No fractional character positions

### Benefits

- Perfect alignment at all nesting levels
- Consistent spacing regardless of container depth
- Easy comparison with browser-based NiceGUI rendering
- Predictable layout behavior

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
│   ├── layout.py        # Layout calculation (pixel-first)
│   └── styles.py        # CSS → terminal mapping
├── run.py               # ui.run() implementation
└── testing/             # Testing utilities
    └── subprocess_terminal.py  # PTY-based testing
```

## Keyboard Navigation

### Focus Navigation

- **Tab / Shift+Tab**: Move between focusable elements (standard)
- **Arrow keys (Up/Down/Left/Right)**: Navigate between components spatially (intuitive)
- **Space**: Activate buttons, toggle checkboxes (standard)
- **Enter**: Activate buttons, submit forms

### Full Keyboard Focus Mode

Some elements capture keyboard input ("full focus mode"):

- **Input fields**:
  - Enter: Toggle edit mode (enter/exit)
  - Left/Right: Move cursor within text (in edit mode)
  - Up/Down: Exit to previous/next component (inputs don't use vertical arrows)
  - Escape: Exit edit mode, return to navigation
  - Typing: Enters edit mode and types characters
  - Home/End: Jump to start/end of text

- **Dropdowns/Select**:
  - Up/Down: Navigate options (captured)
  - Left/Right: Exit to adjacent component
  - Escape: Close dropdown, exit focus mode
  - Enter/Space: Select option

- **Other focusable elements** (buttons, checkboxes):
  - Arrow keys: Navigate to adjacent components
  - No "edit mode" - just navigation focus

### Visual Focus States

Elements have two distinct visual states:

1. **Highlighted (Navigation Focus)**: Cyan background
   - Element is selected for navigation
   - Arrow keys move to other elements
   - Space/Enter activates the element
   - Applies to: buttons, checkboxes, inputs (before typing)

2. **Edit Mode (Full Focus)**: White background + cursor
   - Element is capturing all keyboard input
   - Typing enters characters
   - Escape exits back to highlighted state
   - Applies to: inputs, textareas, selects

### Design Principle

Elements should only capture keys they actually use. If an element doesn't need Up/Down (like a text input), those keys should navigate to other components. Escape always exits any focus/edit mode.

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
