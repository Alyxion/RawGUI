# RawGUI - Long-Term Goals

## Primary Goal

Create a TUI (Terminal User Interface) version of NiceGUI that allows running standard NiceGUI applications in the terminal.

## Core Requirements

### 1. 100% NiceGUI API Compatibility

- All RawGUI elements must match the NiceGUI API exactly (at least high-level calls)
- Not necessary to replicate below-the-surface implementation details
- Eventually allow running any standard NiceGUI sample by overriding imports:
  ```python
  # Original: from nicegui import ui
  # Becomes:  from rawgui import ui (e.g., with mocking)
  ```

### 2. NiceGUI Principles to Implement

- **Context is key**: Sub-elements are added by entering their context with `with` and then creating them
- **Root element detection**: Root elements detect on which pages they are created
- **Page definitions**: Via `@ui.page` decorators or referred as subpage of `ui.sub_pages`

### 3. Browser-Like Behavior

- Pages with proper URL routing
- Navigation history (back/forward)
- Scrolling support:
  - Main scrollview for entire content (can be forced hidden)
  - Nested scrollviews like in a real browser
- Full mouse support (clicks, hover states, drag where applicable)

### 4. Auto-Reload

- File watching like NiceGUI's development mode
- Automatic UI refresh on Python file changes
- Preserve navigation state across reloads

### 5. Style System

- Mimic browser behavior regarding styles and classes
- `.classes()` method for Tailwind-like class application
- `.style()` method for inline CSS-style properties
- Map web styles to terminal attributes (colors, bold, underline, borders)

#### Data-Driven Style Definitions (No Hardcoded Magic)

The style system MUST use clean, maintainable data structures instead of hardcoded values:

- **Static Classes**: Dictionary mapping exact class names to terminal attributes
  ```python
  STATIC_CLASSES = {
      "font-bold": {"bold": True},
      "text-center": {"text_align": "center"},
      "border": {"border": True},
  }
  ```

- **Pattern-Based Classes**: List of regex patterns with handlers for dynamic classes
  ```python
  CLASS_PATTERNS = [
      {"pattern": r"^text-([\w]+)(?:-(\d+))?$", "handler": "text_color"},
      {"pattern": r"^p([xytrbl])?-(\d+)$", "handler": "padding"},
      {"pattern": r"^gap-(\d+)$", "handler": "gap"},
  ]
  ```

- **Configuration Dictionaries**: Separate data structures for colors, sizes, etc.
  ```python
  COLOR_MAP = {"red": "red", "blue": "blue", "cyan": "cyan", ...}
  SHADE_BRIGHTNESS = {50: "bright_", 100: "bright_", 900: "", ...}
  QUASAR_SIZES = {"xs": 1, "sm": 2, "md": 4, "lg": 6, "xl": 8}
  ```

This approach ensures:
1. Easy maintenance and extension of supported classes
2. Clear mapping between Tailwind/Quasar/CSS classes and terminal attributes
3. No magic lambda functions or scattered conditionals
4. Future ability to load definitions from JSON/YAML files if needed

### 6. Graphics Rendering

- Detect terminal capabilities at runtime
- Prefer RGB halfpixel / sixel graphics where supported
- Fallback to ASCII art for unsupported terminals
- Handle images and charts appropriately for terminal display

## Testing Strategy

### SubprocessTerminal Framework

Build a PTY-based testing utility similar to Selenium for web:

```python
"""Subprocess-based terminal tester.

Runs a real terminal application in a PTY subprocess and allows:
- Sending keystrokes
- Capturing terminal state
- Rendering screenshots to PNG
- Finding text (like Selenium's find_element)

Usage:
    tester = SubprocessTerminal("poetry run rawgui")
    tester.start()
    tester.wait_for_text("Welcome")
    tester.send_keys("↓↓↓\n")
    tester.screenshot("output.png")
    tester.stop()
"""
```

### Visual Comparison Testing

1. Use Selenium + NiceGUI Screen to create screenshots of NiceGUI samples
2. Run the same samples with RawGUI and capture terminal output
3. Compare outputs to ensure TUI samples are as close as possible to NiceGUI

### NiceGUI Screen Principles

- Use NiceGUI's testing utilities via Screen class
- Capture web rendering for comparison baseline
- Structural comparison of element hierarchy

## Implementation Approach

1. Evaluate NiceGUI samples to identify most critical components
2. Start with essential elements (label, button, input, row, column, card)
3. If stable, continue step by step with additional components
4. Prioritize components used most frequently in NiceGUI samples

## Tech Stack

- **Python**: >=3.12, <4.0
- **Package Manager**: Poetry
- **TUI Framework**: blessed
- **Testing Dependencies**:
  - pexpect (PTY subprocess management)
  - pyte (terminal emulation)
  - Pillow (screenshot rendering)
  - Selenium (NiceGUI screenshot capture)
  - nicegui (for comparison testing)

## Success Criteria

1. All tier 1-3 UI elements match NiceGUI API signatures
2. Context pattern (`with ui.row(): ui.label('x')`) works identically
3. `@ui.page()` decorator functions correctly
4. Auto-reload triggers UI refresh on file changes
5. TUI output structurally matches NiceGUI layout
6. Basic NiceGUI samples run with simple import swap

## Reference Documentation

- NiceGUI comprehensive reference: https://raw.githubusercontent.com/Alyxion/nice-vibes/refs/heads/main/output/nice_vibes_extended.md
