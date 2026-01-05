# RawGUI Development Plan

## Current Status

### Completed
- [x] TUI renderer with blessed library
- [x] Tkinter/PIL renderer with Roboto fonts
- [x] Multi-adapter architecture (TUI, Tkinter, NiceGUI)
- [x] User interaction testing API (Selenium-like)
- [x] Screenshot capture for all renderers
- [x] Intelligent rendering graph with caching support
- [x] Native widget infrastructure (`ui.native_widget`)
- [x] Native widget demo (`examples/native_widget_demo.py`)
- [x] Fixed native widget positioning using `canvas.create_window()`
- [x] 149 tests passing

### Recently Completed
1. **Native Widget Rendering - FIXED ✅**
   - Added `pack_propagate(False)` to prevent frames from shrinking to fit children
   - Added `frame.update_idletasks()` to force geometry calculation
   - Changed frame parent from Canvas to root window for proper rendering and event handling
   - **CRITICAL FIX**: Fixed render order in `_run_tkinter()` - now builds page, then renders AFTER window created
   - Native widgets are now successfully created when running the Tkinter app with a display
   - All 149 tests passing

2. **Xvfb Screenshot Utility - CREATED ✅**
   - Created `rawgui/testing/screenshot_xvfb.py` for capturing Tkinter windows
   - Shows actual native widgets (Scale, Text, Listbox, Canvas)
   - Both Python API and CLI interface
   - Works on headless systems with Xvfb
   - Successfully captured native_widget_demo with all widgets visible

## Current Work: JavaScript and CSS Support

### Phase 1: CSS/Tailwind Support ⏳ IN PROGRESS

**Completed:**
- [ ] Created `rawgui/css_tailwind.py` - Comprehensive Tailwind parser
  - Complete Tailwind color palette (Slate, Gray, Red, etc.)
  - All spacing scale values (0-96, with proper 4px unit conversion)
  - All sizing utilities (w-*, h-*, min-*, max-*)
  - All padding/margin utilities (p-, m-, pt-, mt-, px-, my-, etc.)
  - Flexbox support (flex, flex-direction, justify-content, align-items, gap, etc.)
  - Text utilities (size, color, alignment)
  - Border radius (rounded-*)
  - Display utilities (hidden, block, flex, inline, etc.)
  - Overflow utilities
  - Responsive prefix support (sm:, md:, lg:, xl:, 2xl:)
  - Returns `CSSProperties` dataclass with all computed pixel values

- [ ] Created `rawgui/dom.py` - HTML DOM compatibility layer
  - `DOMElement` mixin class for all elements
  - DOM properties: scrollHeight, scrollWidth, clientHeight, clientWidth, offsetHeight, offsetWidth, scrollTop, scrollLeft
  - Element query methods: getElementById, querySelector, querySelectorAll
  - Event system: addEventListener, removeEventListener, dispatchEvent
  - DOM tree methods: appendChild, removeChild, replaceChild, parentElement, children, firstChild, lastChild
  - Data attributes (HTML5 dataset): get_data, set_data, dataset property
  - Position methods: getBoundingClientRect, offsetParent
  - Helper classes: `WindowObject`, `DocumentObject`, `ConsoleObject`

### Phase 2: JavaScript Engine Integration ⏳ TODO

**Tasks:**
- [ ] Install py_mini_racer dependency
- [ ] Create `rawgui/javascript.py` - JavaScript runtime context
  - Integrate py_mini_racer MiniRacer engine
  - Set up window, document, console global objects
  - Map Python DOM elements to JavaScript
  - Execute arbitrary JavaScript code
  - Return values from JS to Python
  - Handle promise/async execution

- [ ] Implement common JS methods in window/document:
  - `window.scrollTo(x, y)` - Scroll to position
  - `window.scrollBy(x, y)` - Scroll by delta
  - `window.addEventListener(event, callback)`
  - `document.body` - Access root element
  - `document.body.scrollHeight` - Get total scroll height
  - `document.getElementById(id)`
  - `document.querySelector(selector)`
  - `document.querySelectorAll(selector)`
  - `console.log(...args)` - Log output
  - `console.error(...args)` - Log errors
  - `console.warn(...args)` - Log warnings
  - `console.clear()` - Clear console

### Phase 3: Responsive Layout Engine ⏳ TODO

**Tasks:**
- [ ] Update `rawgui/adapters/tkinter_adapter.py` layout calculations
  - Parse CSS properties from element classes
  - Support flex layout (flex-direction, justify-content, align-items, gap)
  - Support width/height constraints (w-full, h-full, max-w-2xl, etc.)
  - Support responsive sizing (flex-grow, flex-shrink, flex-basis)
  - Calculate actual pixel dimensions based on Tailwind classes
  - Support percentage-based sizing (1/2, 1/3, 2/3, etc.)

- [ ] Add to TUI adapter layout logic:
  - Convert pixel values to character cells (12px width = 1 col, 24px height = 1 row)
  - Round to even sizes for clean character alignment
  - Support TUI-specific constraints (terminal width/height)
  - Maintain pixel-perfect alignment across renders

### Phase 4: Element Integration ⏳ TODO

**Tasks:**
- [ ] Update `rawgui/element.py` to inherit from DOMElement
  - All elements become DOM nodes
  - Support CSS property parsing in `classes()` method
  - Store computed CSS properties
  - Update layout calculations to use CSS properties
  - Maintain backward compatibility with existing API

- [ ] Create example: `examples/chat_with_ai.py`
  - Port NiceGUI chat example to RawGUI
  - Use `ui.column()` with `flex-grow` for expandable container
  - Use `ui.chat_message()` for message display
  - Implement auto-scroll with `window.scrollTo(0, document.body.scrollHeight)`
  - Test JavaScript execution
  - Verify responsive layout

### Implementation Notes

**Pixel Coordinate System:**
- All calculations done in pixels (base unit)
- TUI converts to character cells at render time
- Spacing scale: 4px base unit (Tailwind standard)
- Character conversion: 12px = 1 column, 24px = 1 row

**CSS Property Application:**
- Classes parsed in order when applied
- Later classes override earlier ones
- Support cascading/specificity rules
- Store final computed properties for layout

**JavaScript Context:**
- Single global runtime instance
- Elements registered as JavaScript objects
- Python callbacks callable from JavaScript
- Bidirectional communication (Python ↔ JS)

**Layout Calculation Order:**
1. Parse Tailwind classes → CSSProperties
2. Calculate flex layouts based on CSS
3. Compute actual pixel dimensions
4. TUI: Convert pixels to character cells
5. Render with final dimensions

## Immediate Tasks (Next Session)

### 1. Phase 2: JavaScript Engine
- Install py_mini_racer
- Create JavaScript runtime in `rawgui/javascript.py`
- Implement window/document/console objects
- Test basic JS execution

### 2. Phase 3: Layout Engine
- Integrate CSS properties into Tkinter layout calculations
- Add responsive sizing support
- Test with Tailwind classes

### 3. Create chat_with_ai Example
- Port from NiceGUI example
- Test scrolling behavior
- Verify JavaScript integration

### 4. Documentation
- Update CLAUDE.md with JavaScript/CSS guide
- Add examples for common patterns
- Document limitations and gotchas

## Architecture Notes

### Native Widget System
- `NativeWidget` element in `rawgui/elements/native_widget.py`
- Factory pattern: user provides `widget_factory(parent) -> tk.Widget`
- Widgets placed via `canvas.create_window()` (ensures proper layering)
- Placeholder rendered by Pillow, actual widget overlaid by Tkinter

### Intelligent Caching (Tkinter)
- `RenderNode` dataclass tracks `cached_image`, `dirty`, `is_cacheable`
- Container elements (row, column, card) are cacheable
- Cache key based on element ID and tag
- Background image uses `tag_lower()` to stay behind native widgets

## File Locations

| File | Purpose |
|------|---------|
| `rawgui/adapters/tkinter_adapter.py` | Tkinter/PIL rendering with caching |
| `rawgui/elements/native_widget.py` | NativeWidget element class |
| `rawgui/testing/user.py` | Selenium-like testing API |
| `examples/native_widget_demo.py` | Native widget demonstration |
| `CLAUDE.md` | Full project documentation |

## Commands

```bash
# Run tests
poetry run pytest -x -q

# Run with TUI (default)
poetry run python examples/counter.py

# Run with Tkinter
RAWGUI_RENDERER=tkinter poetry run python examples/counter.py

# Run native widget demo
RAWGUI_RENDERER=tkinter poetry run python examples/native_widget_demo.py
```
