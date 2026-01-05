"""HTML DOM compatibility layer for RawGUI elements.

This module provides DOM-compatible properties and methods for all RawGUI elements,
enabling JavaScript execution and browser-like behavior.

Key concepts:
- All elements act like HTML DOM nodes
- Properties return pixel values (converted from TUI character cells if needed)
- Methods support querySelector, getElementById, etc.
- Event listeners and callbacks work like DOM events
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .element import Element

# Pixel-to-character conversion (TUI mode)
CHAR_WIDTH_PX = 12  # 1 character = 12 pixels
CHAR_HEIGHT_PX = 24  # 1 row = 24 pixels


class DOMElement:
    """Mixin that adds HTML DOM compatibility to Elements."""
    
    def __init__(self, *args, **kwargs):
        """Initialize DOM properties."""
        super().__init__(*args, **kwargs)
        
        # Layout properties (in pixels)
        self._width: Optional[int] = None
        self._height: Optional[int] = None
        self._scroll_top: int = 0
        self._scroll_left: int = 0
        self._scroll_height: int = 0
        self._scroll_width: int = 0
        
        # Position (in pixels)
        self._offset_parent: Optional[DOMElement] = None
        self._client_rect = (0, 0, 0, 0)  # x, y, width, height
        
        # Event listeners
        self._event_listeners: Dict[str, List[Callable]] = {}
        
        # Data attributes (HTML5 dataset)
        self._data_attributes: Dict[str, str] = {}
    
    # ========================================================================
    # Layout Properties (Read-only, computed from layout engine)
    # ========================================================================
    
    @property
    def scrollHeight(self) -> int:
        """Total height of scrollable content in pixels.
        
        This is the full height of the element's contents, including
        content that may be hidden by scrolling.
        """
        return self._scroll_height
    
    @property
    def scrollWidth(self) -> int:
        """Total width of scrollable content in pixels."""
        return self._scroll_width
    
    @property
    def clientHeight(self) -> int:
        """Visible height in pixels (height - scrollbars - borders).
        
        For elements without scrollbars, this equals the element's height.
        """
        if self._height is not None:
            return self._height
        return 0
    
    @property
    def clientWidth(self) -> int:
        """Visible width in pixels (width - scrollbars - borders)."""
        if self._width is not None:
            return self._width
        return 0
    
    @property
    def offsetHeight(self) -> int:
        """Total height including padding, border, and margin."""
        height = self.clientHeight
        # Add padding and border
        if hasattr(self, '_css_properties'):
            props = self._css_properties
            height += props.padding_y + (props.border_width * 2)
        return height
    
    @property
    def offsetWidth(self) -> int:
        """Total width including padding, border, and margin."""
        width = self.clientWidth
        # Add padding and border
        if hasattr(self, '_css_properties'):
            props = self._css_properties
            width += props.padding_x + (props.border_width * 2)
        return width
    
    @property
    def scrollTop(self) -> int:
        """Current vertical scroll position in pixels."""
        return self._scroll_top
    
    @scrollTop.setter
    def scrollTop(self, value: int) -> None:
        """Set vertical scroll position."""
        self._scroll_top = max(0, min(value, self._scroll_height - self.clientHeight))
        self._trigger_scroll_event()
    
    @property
    def scrollLeft(self) -> int:
        """Current horizontal scroll position in pixels."""
        return self._scroll_left
    
    @scrollLeft.setter
    def scrollLeft(self, value: int) -> None:
        """Set horizontal scroll position."""
        self._scroll_left = max(0, min(value, self._scroll_width - self.clientWidth))
        self._trigger_scroll_event()
    
    # ========================================================================
    # Position and Bounds
    # ========================================================================
    
    @property
    def offsetParent(self) -> Optional[DOMElement]:
        """Parent element used for calculating offsets."""
        return self._offset_parent
    
    def getBoundingClientRect(self) -> Dict[str, int]:
        """Get element's position and size relative to viewport.
        
        Returns:
            Dictionary with keys: top, left, bottom, right, width, height, x, y
        """
        x, y, w, h = self._client_rect
        return {
            'top': y,
            'left': x,
            'bottom': y + h,
            'right': x + w,
            'width': w,
            'height': h,
            'x': x,
            'y': y,
        }
    
    # ========================================================================
    # Element Query Methods (querySelector, getElementById, etc.)
    # ========================================================================
    
    def getElementById(self, element_id: str) -> Optional[DOMElement]:
        """Find element by ID in this element's tree."""
        if hasattr(self, 'id') and self.id == element_id:
            return self
        
        # Search children
        if hasattr(self, 'children'):
            for child in self.children:
                result = child.getElementById(element_id)
                if result:
                    return result
        
        return None
    
    def querySelector(self, selector: str) -> Optional[DOMElement]:
        """Find first element matching CSS selector."""
        # Simple selector support: .class, #id, element
        if selector.startswith('.'):
            # Class selector
            class_name = selector[1:]
            return self._find_by_class(class_name)
        elif selector.startswith('#'):
            # ID selector
            element_id = selector[1:]
            return self.getElementById(element_id)
        else:
            # Tag selector
            return self._find_by_tag(selector)
    
    def querySelectorAll(self, selector: str) -> List[DOMElement]:
        """Find all elements matching CSS selector."""
        results = []
        
        if selector.startswith('.'):
            # Class selector
            class_name = selector[1:]
            self._find_all_by_class(class_name, results)
        elif selector.startswith('#'):
            # ID selector - only one match possible
            element_id = selector[1:]
            found = self.getElementById(element_id)
            if found:
                results.append(found)
        else:
            # Tag selector
            self._find_all_by_tag(selector, results)
        
        return results
    
    def _find_by_class(self, class_name: str) -> Optional[DOMElement]:
        """Find first element with given class."""
        if hasattr(self, '_classes') and class_name in self._classes:
            return self
        
        if hasattr(self, 'children'):
            for child in self.children:
                result = child._find_by_class(class_name)
                if result:
                    return result
        
        return None
    
    def _find_all_by_class(self, class_name: str, results: List[DOMElement]) -> None:
        """Find all elements with given class."""
        if hasattr(self, '_classes') and class_name in self._classes:
            results.append(self)
        
        if hasattr(self, 'children'):
            for child in self.children:
                child._find_all_by_class(class_name, results)
    
    def _find_by_tag(self, tag: str) -> Optional[DOMElement]:
        """Find first element with given tag."""
        if hasattr(self, 'tag') and self.tag == tag:
            return self
        
        if hasattr(self, 'children'):
            for child in self.children:
                result = child._find_by_tag(tag)
                if result:
                    return result
        
        return None
    
    def _find_all_by_tag(self, tag: str, results: List[DOMElement]) -> None:
        """Find all elements with given tag."""
        if hasattr(self, 'tag') and self.tag == tag:
            results.append(self)
        
        if hasattr(self, 'children'):
            for child in self.children:
                child._find_all_by_tag(tag, results)
    
    # ========================================================================
    # Event Handling
    # ========================================================================
    
    def addEventListener(self, event_type: str, callback: Callable) -> None:
        """Register an event listener.
        
        Args:
            event_type: Event type (e.g., 'click', 'scroll', 'change')
            callback: Function to call when event fires
        """
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(callback)
    
    def removeEventListener(self, event_type: str, callback: Callable) -> None:
        """Unregister an event listener."""
        if event_type in self._event_listeners:
            try:
                self._event_listeners[event_type].remove(callback)
            except ValueError:
                pass
    
    def dispatchEvent(self, event_type: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Dispatch an event to all registered listeners."""
        if event_type in self._event_listeners:
            for callback in self._event_listeners[event_type]:
                try:
                    if event_data:
                        callback(event_data)
                    else:
                        callback()
                except Exception as e:
                    print(f"Error in event listener: {e}")
    
    def _trigger_scroll_event(self) -> None:
        """Trigger scroll event."""
        self.dispatchEvent('scroll')
    
    # ========================================================================
    # Data Attributes (HTML5 dataset)
    # ========================================================================
    
    @property
    def dataset(self) -> Dict[str, str]:
        """Access data-* attributes as a dictionary."""
        return self._data_attributes
    
    def set_data(self, key: str, value: str) -> None:
        """Set data-* attribute."""
        self._data_attributes[key] = value
    
    def get_data(self, key: str, default: str = '') -> str:
        """Get data-* attribute."""
        return self._data_attributes.get(key, default)
    
    # ========================================================================
    # DOM Tree Methods
    # ========================================================================
    
    def appendChild(self, child: DOMElement) -> DOMElement:
        """Add a child element."""
        if not hasattr(self, 'default_slot'):
            raise ValueError("Element does not support children")
        
        self.default_slot.add(child)
        return child
    
    def removeChild(self, child: DOMElement) -> DOMElement:
        """Remove a child element."""
        if not hasattr(self, 'default_slot'):
            raise ValueError("Element does not support children")
        
        if child in self.default_slot.elements:
            self.default_slot.elements.remove(child)
        
        return child
    
    def replaceChild(self, new_child: DOMElement, old_child: DOMElement) -> DOMElement:
        """Replace a child element."""
        if not hasattr(self, 'default_slot'):
            raise ValueError("Element does not support children")
        
        try:
            idx = self.default_slot.elements.index(old_child)
            self.default_slot.elements[idx] = new_child
        except ValueError:
            raise ValueError("Old child not found")
        
        return old_child
    
    @property
    def parentElement(self) -> Optional[DOMElement]:
        """Get parent element."""
        if hasattr(self, 'parent_slot') and self.parent_slot:
            return self.parent_slot.parent
        return None
    
    @property
    def children(self) -> List[DOMElement]:
        """Get all child elements."""
        if hasattr(self, 'default_slot'):
            return self.default_slot.elements
        return []
    
    @property
    def firstChild(self) -> Optional[DOMElement]:
        """Get first child element."""
        children = self.children
        return children[0] if children else None
    
    @property
    def lastChild(self) -> Optional[DOMElement]:
        """Get last child element."""
        children = self.children
        return children[-1] if children else None


# Window and Document objects for JavaScript context
class WindowObject:
    """Represents the global window object in JavaScript."""
    
    def __init__(self, root_element: Optional[DOMElement] = None):
        self.root = root_element
        self.scroll_x = 0
        self.scroll_y = 0
    
    @property
    def innerWidth(self) -> int:
        """Window viewport width."""
        if self.root and hasattr(self.root, 'clientWidth'):
            return self.root.clientWidth
        return 800  # Default
    
    @property
    def innerHeight(self) -> int:
        """Window viewport height."""
        if self.root and hasattr(self.root, 'clientHeight'):
            return self.root.clientHeight
        return 600  # Default
    
    def scrollTo(self, x: int, y: int) -> None:
        """Scroll to position."""
        self.scroll_x = x
        self.scroll_y = y
    
    def scrollBy(self, x: int, y: int) -> None:
        """Scroll by delta."""
        self.scroll_x += x
        self.scroll_y += y


class DocumentObject:
    """Represents the global document object in JavaScript."""
    
    def __init__(self, root_element: Optional[DOMElement] = None):
        self.root = root_element
    
    @property
    def body(self) -> Optional[DOMElement]:
        """The body element."""
        return self.root
    
    def getElementById(self, element_id: str) -> Optional[DOMElement]:
        """Find element by ID."""
        if self.root:
            return self.root.getElementById(element_id)
        return None
    
    def querySelector(self, selector: str) -> Optional[DOMElement]:
        """Find element by selector."""
        if self.root:
            return self.root.querySelector(selector)
        return None
    
    def querySelectorAll(self, selector: str) -> List[DOMElement]:
        """Find all elements by selector."""
        if self.root:
            return self.root.querySelectorAll(selector)
        return []


class ConsoleObject:
    """Represents the console object in JavaScript."""
    
    def __init__(self):
        self.logs: List[str] = []
    
    def log(self, *args) -> None:
        """Log message."""
        message = ' '.join(str(arg) for arg in args)
        self.logs.append(message)
        print(f"[console.log] {message}")
    
    def error(self, *args) -> None:
        """Log error."""
        message = ' '.join(str(arg) for arg in args)
        self.logs.append(f"ERROR: {message}")
        print(f"[console.error] {message}")
    
    def warn(self, *args) -> None:
        """Log warning."""
        message = ' '.join(str(arg) for arg in args)
        self.logs.append(f"WARN: {message}")
        print(f"[console.warn] {message}")
    
    def clear(self) -> None:
        """Clear console."""
        self.logs.clear()
    
    def info(self, *args) -> None:
        """Log info."""
        self.log(*args)
