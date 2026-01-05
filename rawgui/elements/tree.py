"""Tree view component.

NiceGUI-compatible hierarchical tree display.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..element import Element


class Tree(Element):
    """A hierarchical tree view.

    Features:
    - Expandable/collapsible nodes
    - Keyboard navigation
    - Selection support
    - Checkbox mode

    Example:
        tree = ui.tree([
            {'id': '1', 'label': 'Fruits', 'children': [
                {'id': '1.1', 'label': 'Apple'},
                {'id': '1.2', 'label': 'Banana'},
            ]},
            {'id': '2', 'label': 'Vegetables'},
        ])
    """

    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        *,
        label_key: str = "label",
        children_key: str = "children",
        node_key: str = "id",
        on_select: Optional[Callable[[Dict], None]] = None,
        on_expand: Optional[Callable[[Dict], None]] = None,
        tick_strategy: Optional[str] = None,  # None, 'leaf', 'leaf-filtered'
    ) -> None:
        """Create a tree view.

        Args:
            nodes: List of node dicts with children
            label_key: Key for node label
            children_key: Key for child nodes
            node_key: Key for node identifier
            on_select: Callback when node is selected
            on_expand: Callback when node is expanded
            tick_strategy: Checkbox mode strategy
        """
        super().__init__()
        self.tag = "tree"
        self._nodes = nodes
        self.label_key = label_key
        self.children_key = children_key
        self.node_key = node_key
        self._on_select = on_select
        self._on_expand = on_expand
        self.tick_strategy = tick_strategy

        # State
        self._expanded: set = set()
        self._selected: Optional[str] = None
        self._ticked: set = set()

    @property
    def nodes(self) -> List[Dict[str, Any]]:
        """Get tree nodes."""
        return self._nodes

    @nodes.setter
    def nodes(self, value: List[Dict[str, Any]]) -> None:
        """Set tree nodes."""
        self._nodes = value

    def expand(self, node_id: str) -> None:
        """Expand a node."""
        self._expanded.add(node_id)
        node = self._find_node(node_id)
        if node and self._on_expand:
            self._on_expand(node)

    def collapse(self, node_id: str) -> None:
        """Collapse a node."""
        self._expanded.discard(node_id)

    def toggle_expand(self, node_id: str) -> None:
        """Toggle node expansion."""
        if node_id in self._expanded:
            self.collapse(node_id)
        else:
            self.expand(node_id)

    def expand_all(self) -> None:
        """Expand all nodes."""
        self._expand_recursive(self._nodes)

    def collapse_all(self) -> None:
        """Collapse all nodes."""
        self._expanded.clear()

    def _expand_recursive(self, nodes: List[Dict]) -> None:
        """Recursively expand nodes."""
        for node in nodes:
            node_id = node.get(self.node_key)
            if node_id:
                self._expanded.add(node_id)
            children = node.get(self.children_key, [])
            if children:
                self._expand_recursive(children)

    def select(self, node_id: str) -> None:
        """Select a node."""
        self._selected = node_id
        node = self._find_node(node_id)
        if node and self._on_select:
            self._on_select(node)

    def tick(self, node_id: str) -> None:
        """Tick a node checkbox."""
        self._ticked.add(node_id)

    def untick(self, node_id: str) -> None:
        """Untick a node checkbox."""
        self._ticked.discard(node_id)

    def toggle_tick(self, node_id: str) -> None:
        """Toggle node checkbox."""
        if node_id in self._ticked:
            self.untick(node_id)
        else:
            self.tick(node_id)

    def _find_node(self, node_id: str, nodes: Optional[List[Dict]] = None) -> Optional[Dict]:
        """Find a node by ID."""
        if nodes is None:
            nodes = self._nodes

        for node in nodes:
            if node.get(self.node_key) == node_id:
                return node
            children = node.get(self.children_key, [])
            if children:
                found = self._find_node(node_id, children)
                if found:
                    return found
        return None

    @property
    def selected(self) -> Optional[Dict]:
        """Get selected node."""
        if self._selected:
            return self._find_node(self._selected)
        return None

    @property
    def ticked(self) -> List[Dict]:
        """Get all ticked nodes."""
        result = []
        for node_id in self._ticked:
            node = self._find_node(node_id)
            if node:
                result.append(node)
        return result
