# JavaScript and CSS Support for RawGUI

## Overview

This plan outlines how to add JavaScript execution and proper DOM/CSS compatibility to RawGUI, enabling the chat_with_ai example and other JavaScript-dependent applications.

## Architecture

### 1. DOM Property System

Create a unified property system where Python elements expose HTML DOM properties:

**Read Properties:**
- `scrollHeight` - Total scrollable content height
- `scrollWidth` - Total scrollable content width
- `clientHeight` - Visible height (height - scrollbars)
- `clientWidth` - Visible width (width - scrollbars)
- `offsetHeight` - Total height including borders
- `offsetWidth` - Total width including borders
- `innerHeight` - Window inner height
- `innerWidth` - Window inner width
- `scrollTop` - Current vertical scroll position
- `scrollLeft` - Current horizontal scroll position

**Write Properties:**
- `scrollTop` - Set scroll position
- `scrollLeft` - Set scroll position

**Implementation:**
```python
class Element:
    @property
    def scrollHeight(self) -> int:
        """Return total scrollable height in pixels."""
        # For TUI: convert to character units
        # For Tkinter: return actual pixels
        
    @property
    def clientHeight(self) -> int:
        """Return visible height in pixels."""
```

### 2. CSS/Tailwind Layout System

Enhance the existing class system to support CSS-style layout:

**Existing Classes (Tailwind-inspired):**
- `w-full`, `h-full` - Full width/height
- `flex-grow` - Flex grow
- `items-stretch` - Stretch items
- `max-w-2xl` - Max width
- `mx-auto`, `my-6` - Margins
- `p-4`, `pt-2` - Padding

**Enhancement:**
- Parse Tailwind classes and convert to pixel values
- Support responsive sizing (flex, flex-grow, flex-shrink)
- Support min/max dimensions
- Support gaps and spacing

### 3. JavaScript Engine Integration

Use `py_mini_racer` to execute JavaScript:

```python
from py_mini_racer import MiniRacer

class JavaScriptContext:
    def __init__(self):
        self.runtime = MiniRacer()
        self._setup_dom()
        
    def _setup_dom(self):
        """Initialize DOM objects and methods."""
        self.runtime.eval("""
            window = {
                scrollTo: (x, y) => { /* ... */ },
                scrollBy: (x, y) => { /* ... */ },
            };
            document = {
                body: {
                    scrollHeight: 0,
                    clientHeight: 0,
                },
                getElementById: (id) => { /* ... */ },
                querySelector: (selector) => { /* ... */ },
                querySelectorAll: (selector) => { /* ... */ },
                addEventListener: (event, callback) => { /* ... */ },
            };
            console = {
                log: (...args) => { /* ... */ },
                error: (...args) => { /* ... */ },
                warn: (...args) => { /* ... */ },
            };
        """)
    
    def execute(self, code: str) -> Any:
        """Execute JavaScript code."""
        return self.runtime.eval(code)
```

### 4. HTML DOM Compatibility

Every Element must act like an HTML DOM node:

```python
class Element:
    # DOM Properties
    @property
    def dataset(self) -> Dict[str, str]:
        """HTML5 data-* attributes."""
        return self._data_attributes
    
    # DOM Methods
    def addEventListener(self, event: str, callback: Callable) -> None:
        """Register event listener."""
        
    def removeEventListener(self, event: str, callback: Callable) -> None:
        """Unregister event listener."""
        
    def getElementById(self, id: str) -> Optional["Element"]:
        """Find element by ID."""
        
    def querySelector(self, selector: str) -> Optional["Element"]:
        """Find first matching element."""
        
    def querySelectorAll(self, selector: str) -> List["Element"]:
        """Find all matching elements."""
    
    # DOM Tree Methods
    def appendChild(self, child: "Element") -> None:
        """Add child element."""
        
    def removeChild(self, child: "Element") -> None:
        """Remove child element."""
```

### 5. Responsive Sizing

Create a layout system that respects CSS-style properties:

**Container Types:**
- `Column` - Vertical flexbox (flex-direction: column)
- `Row` - Horizontal flexbox (flex-direction: row)
- `Card` - Block container with padding

**Flex Properties:**
- `flex-grow: 1` - Take available space
- `flex-shrink: 1` - Shrink if needed
- `flex-basis: auto` - Base size
- `items-stretch` - Children fill parent
- `justify-center` - Center items

**Implementation:**
```python
class Row(Element):
    def __init__(self):
        super().__init__(tag='row')
        self._flex_direction = 'row'
        self._flex_wrap = 'nowrap'
        self._gap = 0
        
    def apply_class(self, cls: str):
        """Parse and apply Tailwind class."""
        if cls == 'flex-grow':
            self._flex_grow = 1
        elif cls.startswith('gap-'):
            size = int(cls.split('-')[1])
            self._gap = size * 4  # Tailwind unit conversion
```

### 6. TUI vs Tkinter Differences

**TUI Mode:**
- All dimensions in character cells
- Convert pixels: `char_col = pixel_x // 12`, `char_row = pixel_y // 24`
- Round to nearest even size to avoid fractional cells
- Use ANSI/Unicode for visual elements

**Tkinter Mode:**
- All dimensions in pixels
- Direct pixel rendering
- Sub-pixel precision possible
- Use PIL for drawing

## Implementation Phases

### Phase 1: DOM Property System (Current)
- [ ] Add scrollHeight, clientHeight, etc. to Element
- [ ] Implement getter/setter logic
- [ ] Support for all container types

### Phase 2: JavaScript Engine
- [ ] Install py_mini_racer
- [ ] Create JavaScriptContext class
- [ ] Implement basic console.log, window.scrollTo
- [ ] Test with simple examples

### Phase 3: CSS/Tailwind Integration
- [ ] Parse existing Tailwind classes
- [ ] Map to pixel values
- [ ] Support responsive sizing
- [ ] Calculate flex layouts

### Phase 4: DOM Methods
- [ ] Implement querySelector, getElementById
- [ ] Add addEventListener/removeEventListener
- [ ] Support DOM traversal (parent, children, etc.)

### Phase 5: Chat Example
- [ ] Port chat_with_ai to RawGUI
- [ ] Test scrolling behavior
- [ ] Verify JavaScript execution

## Example: scrollTo Implementation

```python
# Python side
async def run_javascript(code: str) -> Any:
    """Execute JavaScript and return result."""
    js_context.execute(code)

# In chat example
await run_javascript('window.scrollTo(0, document.body.scrollHeight)')

# JavaScript runtime
window.scrollTo = (x, y) -> {
    # Find the scrollable container
    # Set scrollTop = y
    # Trigger re-render
}
```

## Files to Create/Modify

1. `rawgui/dom.py` - DOM property system
2. `rawgui/javascript.py` - JavaScript execution context
3. `rawgui/css_parser.py` - CSS/Tailwind parser
4. Update `rawgui/element.py` - Add DOM methods
5. Update `rawgui/adapters/tkinter_adapter.py` - Layout calculations
6. Update `CLAUDE.md` - Document JavaScript support

## Implementation Status

### Phase 1: CSS/Tailwind Support ✅ STARTED

**Created Files:**

1. **`rawgui/css_tailwind.py`** (590 lines)
   - `CSSProperties` dataclass with all CSS properties
   - `TailwindParser` class for parsing Tailwind classes
   - Complete Tailwind color palette (50+ colors)
   - All spacing utilities (0-96 scale)
   - All sizing utilities (w-*, h-*, min-*, max-*)
   - Complete padding/margin support
   - Full flexbox support
   - Text utilities, border radius, display, overflow
   - Responsive prefix support (sm:, md:, lg:, xl:, 2xl:)
   - Returns computed pixel values for all properties

2. **`rawgui/dom.py`** (550 lines)
   - `DOMElement` mixin class with full HTML DOM API
   - Read-only properties: scrollHeight, scrollWidth, clientHeight, clientWidth, offsetHeight, offsetWidth
   - Read-write properties: scrollTop, scrollLeft
   - Query methods: getElementById, querySelector, querySelectorAll
   - Event system: addEventListener, removeEventListener, dispatchEvent
   - DOM tree methods: appendChild, removeChild, replaceChild, parentElement, children, firstChild, lastChild
   - Bounds method: getBoundingClientRect
   - Data attributes: dataset, get_data, set_data
   - Helper classes: WindowObject, DocumentObject, ConsoleObject
   - Full implementation ready for integration

### Phase 2: JavaScript Engine Integration 🔲 TODO

**Files to Create:**

1. **`rawgui/javascript.py`** (TBD)
   - JavaScriptContext class with py_mini_racer integration
   - window object with:
     - innerWidth, innerHeight properties
     - scrollTo(x, y), scrollBy(x, y) methods
     - addEventListener(event, callback)
   - document object with:
     - body property (returns root element)
     - getElementById(id), querySelector(sel), querySelectorAll(sel)
     - addEventListener(event, callback)
   - console object with:
     - log(...args), error(...args), warn(...args), info(...args)
     - clear()
   - Execute arbitrary JavaScript code
   - Map Python elements to JS objects
   - Handle return values and async execution

### Phase 3: Responsive Layout Engine 🔲 TODO

**Files to Modify:**

1. **`rawgui/adapters/tkinter_adapter.py`**
   - Parse CSS properties from element classes
   - Implement flex layout calculations
   - Support all width/height constraints
   - Calculate responsive sizing
   - Support percentage-based sizing (1/2, 1/3, 2/3, etc.)
   - Consider child flex properties in parent calculations

2. **`rawgui/adapters/tui_adapter.py`**
   - Convert pixel values to character cells
   - Handle 12px=1col, 24px=1row conversion
   - Round to even sizes for clean alignment
   - Apply TUI-specific constraints

### Phase 4: Element Integration 🔲 TODO

**Files to Modify:**

1. **`rawgui/element.py`**
   - Make all elements inherit from DOMElement (via multiple inheritance)
   - Add `_css_properties` attribute
   - Update `classes()` method to parse Tailwind classes
   - Store computed CSS properties after parsing
   - Ensure backward compatibility

2. **`rawgui/elements/column.py`** and **`row.py`**
   - Use CSS properties for flex layout
   - Support flex-grow, flex-shrink, flex-basis

3. **`examples/chat_with_ai.py`** (New)
   - Port from NiceGUI example
   - Demonstrate:
     - Responsive layout with `flex-grow`
     - Message containers
     - Auto-scroll with JavaScript
     - Event handling

## Dependencies to Install

```bash
pip install py_mini_racer
```

## Integration Checklist

### Phase 1 Setup (TUI & Tkinter)
- [x] Create Tailwind parser in `css_tailwind.py`
- [x] Create DOM compatibility in `dom.py`
- [ ] Import DOMElement in `element.py`
- [ ] Test CSS parsing
- [ ] Test DOM property access

### Phase 2 Setup (JavaScript)
- [ ] Install py_mini_racer
- [ ] Create `javascript.py` with MiniRacer integration
- [ ] Implement window/document/console objects
- [ ] Test basic JavaScript execution
- [ ] Test element access from JavaScript
- [ ] Test callback execution

### Phase 3 Setup (Layout)
- [ ] Integrate CSS properties into Tkinter layout
- [ ] Implement flex calculations
- [ ] Test with simple flex examples
- [ ] Update TUI layout for pixel-to-char conversion
- [ ] Test TUI responsive behavior

### Phase 4 Setup (Examples)
- [ ] Create chat_with_ai example
- [ ] Test scrolling behavior
- [ ] Test JavaScript execution
- [ ] Test responsive layout
- [ ] Verify all features work together

## Testing Strategy

### Unit Tests
- CSS parser: Test all Tailwind classes
- DOM properties: Test scrollHeight, clientHeight, etc.
- DOM methods: Test getElementById, querySelector, appendChild, etc.
- JavaScript: Test basic execution, element access

### Integration Tests
- Full CSS + DOM + Layout pipeline
- JavaScript + Python integration
- Responsive layout on different terminal sizes
- Chat example end-to-end test

### Manual Testing
- Run examples with different renderers (TUI, Tkinter)
- Test with various Tailwind class combinations
- Verify JavaScript console.log output
- Check scrolling behavior in chat example

## Known Limitations & Gotchas

1. **JavaScript Async/Promises**: py_mini_racer may not support all async features. May need sync-only approach initially.

2. **DOM Selectors**: Only support basic selectors (.class, #id, tag). No complex selectors (>, +, ~) initially.

3. **CSS Units**: Only support px and Tailwind units. No em, rem, vh, vw initially.

4. **Responsive Design**: Breakpoints won't auto-adjust to window size. May need manual re-render on resize.

5. **Performance**: Re-parsing CSS classes on every render could be slow. Should cache CSSProperties.

6. **TUI Limitations**:
   - Character-based rendering means fractional pixels become problematic
   - Some CSS properties (rounded corners, opacity) not applicable
   - Need to round/snap to character grid

## Performance Considerations

1. **CSS Parsing**: Cache parsed CSSProperties at element level
2. **JavaScript Execution**: Reuse MiniRacer instance, don't recreate on each call
3. **Layout Calculations**: Implement incremental layout (only recalc changed elements)
4. **DOM Queries**: Index elements by ID and class for fast lookups

## Future Enhancements

1. CSS Grid support (in addition to Flexbox)
2. Transforms and animations
3. Media query support for dynamic breakpoints
4. CSS custom properties (variables)
5. Sass/SCSS preprocessing
6. CSS-in-JS solutions
7. Shadow DOM support
8. Web Components

