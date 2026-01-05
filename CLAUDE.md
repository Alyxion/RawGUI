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

## Multi-Adapter Rendering Architecture

RawGUI supports multiple rendering backends (adapters). **The source code is 100% identical across all backends.**

### Core Principle: Unified Source Code

**CRITICAL: Application source code must remain 100% identical regardless of rendering backend.**

- Same source runs on TUI, Tkinter, and NiceGUI
- No conditional imports or adapter-specific code in apps
- Renderer selection happens EXTERNALLY via:
  1. Environment variable `RAWGUI_RENDERER`
  2. The `rawgui` runner tool
  3. Parameter to `ui.run()`

This means:
- **NO separate samples** for different adapters
- NiceGUI samples should run unmodified with RawGUI
- RawGUI samples should run unmodified with NiceGUI

### Available Adapters

1. **TUI (Terminal)** - Primary focus, default
   - Uses `blessed` library
   - ASCII/Unicode rendering
   - Full keyboard and mouse support

2. **Tkinter** - GUI fallback
   - Single canvas rendering
   - 100% Pillow-based painting
   - Uses Roboto fonts (downloaded automatically)
   - Intelligent clipping for nested elements
   - Full mouse and keyboard handling
   - Prepared for multi-layer rendering (mixing NiceGUI with native Tkinter components)

### Adapter Interface

All adapters implement a common interface:
- `render(root_element)` - Render element tree
- `invalidate()` - Mark for re-render
- `get_element_at(x, y)` - Hit testing for mouse
- `focus_next()` / `focus_prev()` - Focus navigation

### Multi-Layer Architecture

The Tkinter adapter is designed for future multi-layer support:
- Base layer: RawGUI elements rendered via Pillow
- Overlay layers: Native Tkinter widgets can be composited on top
- This enables gradual migration or hybrid UIs

### Intelligent Rendering Graph (Future Optimization)

Full re-rendering of the entire image on every update is expensive, especially with many text areas. The Tkinter adapter should implement an intelligent caching and rendering system.

**Region-Based Caching:**
- Cache rendered output at major container boundaries (rows, columns, cards)
- Each cacheable region stores its rendered PIL Image
- On state change, only invalidate and re-render affected regions
- Propagate invalidation up the tree (child change invalidates parent)

**Alpha Blending Considerations:**
- Many elements have rounded corners with alpha-blended edges
- Elements may have semi-transparent backgrounds
- Cache regions must account for alpha compositing order
- When a region is invalidated, all overlapping regions above it must also re-render

**Clipped Drawing:**
- Support clipped rendering within container bounds
- Scrollable areas only render visible content
- Use clip rectangles to avoid drawing outside bounds
- Cache visible portions separately from full content

**Dirty Rectangle Tracking:**
```
RenderNode:
  - cached_image: Optional[PIL.Image]
  - dirty: bool
  - dirty_rect: Optional[Rect]  # None = full redraw needed
  - children_dirty: bool

On update:
  1. Mark changed element as dirty
  2. Propagate dirty_rect up to nearest cacheable ancestor
  3. On render, only redraw dirty regions
  4. Composite cached + freshly rendered regions
```

**Native Component Integration (Implemented):**
- **Native widgets are the exception, not the norm** - 99% of UI should be RawGUI elements
- However, it is technically possible to mix native Tkinter widgets when needed
- Use cases: embedding a browser, complex canvas, video player, or other widgets with no RawGUI equivalent
- Example: A RawGUI app with 3 cards, one containing a native Tkinter browser widget
- Architecture:
  - RawGUI renders to canvas as usual
  - Native widgets are placed as Tkinter children at calculated coordinates
  - Render graph tracks "holes" where native widgets live
  - Native widgets handle their own rendering/events
  - On layout change, reposition native widgets to match RawGUI layout

```python
# Native widget API - use sparingly, only when necessary
def create_my_widget(parent):
    """Factory function receives a parent Frame, returns a Tkinter widget."""
    import tkinter as tk
    widget = tk.Text(parent, height=10, width=40)
    widget.insert('1.0', 'Hello from native Tkinter!')
    return widget

with ui.card():
    ui.label("Text Editor")
    ui.native_widget(create_my_widget, width=400, height=200)
```

See `examples/native_widget_demo.py` for a complete example with Scale, Text, Listbox, and Canvas widgets.

**Performance Targets:**
- Static UI: render once, cache everything
- Single element change: only re-render that element + ancestors
- Scroll: only render newly visible content
- Native widgets: zero Pillow rendering overhead for native areas

### Selecting the Renderer

**Option 1: Environment Variable (Recommended)**
```bash
# TUI mode (default)
poetry run python my_app.py

# Tkinter mode
RAWGUI_RENDERER=tkinter poetry run python my_app.py

# NiceGUI mode (uses actual NiceGUI)
RAWGUI_RENDERER=nicegui poetry run python my_app.py
```

**Option 2: Runner Tool**
```bash
# TUI mode (default)
poetry run rawgui my_app.py

# Tkinter mode
poetry run rawgui --renderer=tkinter my_app.py

# NiceGUI mode
poetry run rawgui --renderer=nicegui my_app.py
```

**Option 3: Code Parameter (least preferred)**
```python
# Only use this for development/testing
ui.run(renderer="tkinter")
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

## Screenshot Capture

RawGUI provides unified screenshot capture for all three renderers. This enables visual testing and comparison across rendering backends.

### Available Methods

1. **TUI Screenshots** (`capture_tui`)
   - Runs script in PTY subprocess with pyte terminal emulator
   - Renders to PNG with terminal colors and fonts
   - Best for testing actual terminal behavior

2. **PIL/Tkinter Screenshots** (`capture_pil`)
   - Renders headlessly using Pillow (no window needed)
   - Uses Roboto fonts (auto-downloaded)
   - Fast, deterministic, ideal for CI/CD

3. **NiceGUI Screenshots** (`capture_nicegui`)
   - Uses Selenium to capture browser rendering
   - Requires Chrome/Chromium and chromedriver
   - Reference for visual parity comparison

### Usage

```python
from rawgui.testing import capture_tui, capture_pil, capture_nicegui

# TUI screenshot (runs in PTY)
capture_tui("examples/counter.py", "screenshots/counter_tui.png")

# PIL screenshot (headless, fast)
capture_pil("examples/counter.py", "screenshots/counter_pil.png")

# NiceGUI screenshot (browser-based)
capture_nicegui("examples/counter.py", "screenshots/counter_nicegui.png")

# Capture all renderers at once
from rawgui.testing import capture_all_renderers
capture_all_renderers("examples/counter.py", "screenshots/")
```

### CLI Usage

```bash
# Capture with PIL (default)
poetry run python -m rawgui.testing.screenshots examples/counter.py -o screenshots/

# Capture with specific renderer
poetry run python -m rawgui.testing.screenshots examples/counter.py -r tui
poetry run python -m rawgui.testing.screenshots examples/counter.py -r pil
poetry run python -m rawgui.testing.screenshots examples/counter.py -r nicegui

# Capture all renderers
poetry run python -m rawgui.testing.screenshots examples/counter.py -r all
```

### Design Principle

Screenshots should always be available for development and testing. The PIL/Tkinter renderer can generate screenshots without any display server, making it ideal for:
- CI/CD pipelines
- Automated visual testing
- Documentation generation
- Comparing TUI/GUI/Web rendering

### 4. **Tkinter with Xvfb Screenshots** (`capture_tkinter_xvfb`)
   - Captures actual Tkinter window rendering using virtual X display (Xvfb)
   - **Shows native Tkinter widgets** (Scale, Text, Listbox, Canvas, etc.)
   - Requires Xvfb installed (`apt-get install xvfb`)
   - Best for visual verification and demos with native widgets
   - Ideal for CI/CD on headless systems with X11 support

### Xvfb Screenshot Usage

```python
from rawgui.testing import capture_tkinter_xvfb

# Capture native widget demo with actual Tkinter rendering
capture_tkinter_xvfb(
    "examples/native_widget_demo.py",
    "screenshots/demo_native_tkinter.png",
    width=1024,
    height=768,
    wait_seconds=2
)

# Capture with custom parameters
capture_tkinter_xvfb(
    "examples/counter.py",
    "screenshots/counter_tkinter.png",
    width=800,
    height=600,
    wait_seconds=1.5,
    display=":99"
)
```

### Xvfb CLI Usage

```bash
# Basic capture (800x600, 2 second wait)
poetry run python -m rawgui.testing.screenshot_xvfb examples/native_widget_demo.py -o screenshots/

# Custom dimensions and wait time
poetry run python -m rawgui.testing.screenshot_xvfb examples/counter.py \
  -w 1024 -H 768 -t 3 -o screenshots/counter_tkinter.png

# Use different X display
poetry run python -m rawgui.testing.screenshot_xvfb examples/form.py \
  -d ":100" -o screenshots/form_tkinter.png
```

### Comparison: All Screenshot Methods

| Feature | TUI | PIL | NiceGUI | Xvfb Tkinter |
|---------|-----|-----|---------|--------------|
| **Needs Display** | No (PTY) | No | Yes (Chrome) | Yes (Xvfb) |
| **Speed** | Slower | Very Fast | Slower | Fast |
| **Native Widgets** | N/A | Shows placeholders | Browser controls | ✅ Fully rendered |
| **Installation** | Standard | Standard | Chrome required | xvfb required |
| **Best For** | Terminal testing | CI/CD | Browser reference | Native widget demos |

## User Interaction Testing (Selenium-like API)

RawGUI provides a unified `User` class for simulating user interactions across both TUI and Tkinter renderers. This is similar to Selenium's WebDriver API.

### Basic Usage

```python
from rawgui.testing import User

# Test with Tkinter renderer (headless, fast)
with User("examples/counter.py", renderer="tkinter") as user:
    # Verify initial state
    assert user.contains("Count: 0")

    # Find and click a button
    btn = user.find_by_text("+ Increment")
    user.click_element(btn)

    # Verify result
    assert user.contains("Count: 1")

    # Take screenshot
    user.screenshot("result.png")

# Test with TUI renderer (runs in PTY subprocess)
with User("examples/counter.py", renderer="tui") as user:
    user.wait_for_text("Counter Demo")
    user.press_key("tab")
    user.press_key("space")
    assert user.contains("Count: 1")
```

### User API

**Element Finding:**
- `user.find_by_text(text)` - Find element containing text
- `user.find_by_tag(tag)` - Find elements by tag (button, input, label, etc.)
- `user.find_focused()` - Get currently focused element
- `user.get_elements()` - Get all rendered elements with coordinates

**Interactions:**
- `user.click(x, y)` - Click at screen coordinates
- `user.click_element(el)` - Click on element (uses center)
- `user.click_text(text)` - Click element containing text
- `user.press_key(key)` - Press key (enter, space, tab, escape, up, down, left, right)
- `user.type_text(text)` - Type text into focused input

**Assertions:**
- `user.contains(text)` - Check if text is visible
- `user.should_contain(text)` - Assert text is visible (raises if not)
- `user.should_not_contain(text)` - Assert text is not visible
- `user.get_text()` - Get all visible text

**Screenshots:**
- `user.screenshot(path)` - Save screenshot to file
- `user.get_image()` - Get PIL Image (Tkinter only)

**Element Info:**
```python
el = user.find_by_text("Submit")
print(el.x, el.y)        # Position
print(el.width, el.height)  # Size
print(el.center)         # (x, y) tuple
print(el.tag)            # "button", "input", etc.
print(el.text)           # Text content
print(el.focused)        # Is focused?
```

### Image Comparison

```python
from rawgui.testing import compare_images

# Compare two screenshots
are_equal, diff_ratio = compare_images("before.png", "after.png", threshold=0.01)
# diff_ratio: 0.0 = identical, 1.0 = completely different
```

### Cross-Renderer Testing

The same tests can run on both renderers:

```python
import pytest
from rawgui.testing import User

@pytest.mark.parametrize("renderer", ["tkinter", "tui"])
def test_increment(renderer):
    with User("examples/counter.py", renderer=renderer) as user:
        if renderer == "tui":
            user.wait_for_text("Counter Demo")
            user.press_key("tab")
            user.press_key("tab")
            user.press_key("space")
        else:
            btn = user.find_by_text("+ Increment")
            user.click_element(btn)

        assert user.contains("Count: 1")
```

### Key Differences Between Renderers

| Feature | TUI User | Tkinter User |
|---------|----------|--------------|
| `get_elements()` | Limited (text-based) | Full element info |
| `click(x, y)` | Not supported | Supported |
| `find_focused()` | Not supported | Supported |
| `wait_for_text()` | Yes (async) | Yes (immediate) |
| Screenshot | PTY capture | PIL render |
| Speed | Slower (subprocess) | Fast (headless) |

## Commands

```bash
poetry install          # Install dependencies
poetry run rawgui       # Run the application
poetry run pytest       # Run tests
```

## Reference

- NiceGUI documentation: https://raw.githubusercontent.com/Alyxion/nice-vibes/refs/heads/main/output/nice_vibes_extended.md
