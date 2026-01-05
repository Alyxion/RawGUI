"""Table component.

NiceGUI-compatible data table with selection and pagination.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..element import Element


class Table(Element):
    """A data table component.

    Features:
    - Column headers
    - Row selection (single/multiple)
    - Sorting
    - Pagination
    - ASCII borders

    Example:
        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name'},
            {'name': 'age', 'label': 'Age', 'field': 'age'},
        ]
        rows = [
            {'name': 'Alice', 'age': 30},
            {'name': 'Bob', 'age': 25},
        ]
        ui.table(columns=columns, rows=rows, row_key='name')
    """

    def __init__(
        self,
        *,
        columns: List[Dict[str, Any]],
        rows: List[Dict[str, Any]],
        row_key: str = "id",
        title: Optional[str] = None,
        selection: Optional[str] = None,  # None, 'single', 'multiple'
        pagination: Optional[int] = None,  # Rows per page
        on_select: Optional[Callable[[List[Dict]], None]] = None,
    ) -> None:
        """Create a table.

        Args:
            columns: Column definitions with 'name', 'label', 'field' keys
            rows: List of row data dictionaries
            row_key: Key field to uniquely identify rows
            title: Optional table title
            selection: Selection mode ('single', 'multiple', or None)
            pagination: Number of rows per page (None = no pagination)
            on_select: Callback when selection changes
        """
        super().__init__()
        self.tag = "table"
        self._columns = columns
        self._rows = rows
        self.row_key = row_key
        self.title = title
        self.selection = selection
        self.pagination = pagination
        self._on_select = on_select

        # State
        self._selected: List[Any] = []  # Selected row keys
        self._current_page = 0
        self._sort_column: Optional[str] = None
        self._sort_ascending = True

    @property
    def columns(self) -> List[Dict[str, Any]]:
        """Get column definitions."""
        return self._columns

    @columns.setter
    def columns(self, value: List[Dict[str, Any]]) -> None:
        """Set column definitions."""
        self._columns = value

    @property
    def rows(self) -> List[Dict[str, Any]]:
        """Get all rows."""
        return self._rows

    @rows.setter
    def rows(self, value: List[Dict[str, Any]]) -> None:
        """Set rows."""
        self._rows = value

    @property
    def visible_rows(self) -> List[Dict[str, Any]]:
        """Get currently visible rows (with pagination and sorting)."""
        rows = self._rows.copy()

        # Sort
        if self._sort_column:
            col = next(
                (c for c in self._columns if c["name"] == self._sort_column),
                None
            )
            if col:
                field = col.get("field", col["name"])
                rows.sort(
                    key=lambda r: r.get(field, ""),
                    reverse=not self._sort_ascending,
                )

        # Paginate
        if self.pagination:
            start = self._current_page * self.pagination
            end = start + self.pagination
            rows = rows[start:end]

        return rows

    @property
    def selected(self) -> List[Dict[str, Any]]:
        """Get selected rows."""
        return [r for r in self._rows if r.get(self.row_key) in self._selected]

    @property
    def page_count(self) -> int:
        """Get total number of pages."""
        if not self.pagination:
            return 1
        return max(1, (len(self._rows) + self.pagination - 1) // self.pagination)

    def select(self, row_key: Any) -> None:
        """Select a row by key."""
        if self.selection == "single":
            self._selected = [row_key]
        elif self.selection == "multiple":
            if row_key not in self._selected:
                self._selected.append(row_key)

        if self._on_select:
            self._on_select(self.selected)

    def deselect(self, row_key: Any) -> None:
        """Deselect a row by key."""
        if row_key in self._selected:
            self._selected.remove(row_key)

        if self._on_select:
            self._on_select(self.selected)

    def toggle_select(self, row_key: Any) -> None:
        """Toggle row selection."""
        if row_key in self._selected:
            self.deselect(row_key)
        else:
            self.select(row_key)

    def clear_selection(self) -> None:
        """Clear all selections."""
        self._selected = []
        if self._on_select:
            self._on_select([])

    def select_all(self) -> None:
        """Select all rows (multiple selection only)."""
        if self.selection == "multiple":
            self._selected = [r.get(self.row_key) for r in self._rows]
            if self._on_select:
                self._on_select(self.selected)

    def sort(self, column: str, ascending: bool = True) -> None:
        """Sort by column."""
        self._sort_column = column
        self._sort_ascending = ascending

    def next_page(self) -> None:
        """Go to next page."""
        if self._current_page < self.page_count - 1:
            self._current_page += 1

    def prev_page(self) -> None:
        """Go to previous page."""
        if self._current_page > 0:
            self._current_page -= 1

    def go_to_page(self, page: int) -> None:
        """Go to specific page (0-indexed)."""
        self._current_page = max(0, min(page, self.page_count - 1))

    def add_rows(self, rows: List[Dict[str, Any]]) -> None:
        """Add rows to the table."""
        self._rows.extend(rows)

    def remove_rows(self, keys: List[Any]) -> None:
        """Remove rows by key."""
        self._rows = [r for r in self._rows if r.get(self.row_key) not in keys]
        self._selected = [k for k in self._selected if k not in keys]

    def update_rows(self, rows: List[Dict[str, Any]]) -> None:
        """Update rows (matches by row_key)."""
        key_map = {r.get(self.row_key): r for r in rows}
        for i, row in enumerate(self._rows):
            key = row.get(self.row_key)
            if key in key_map:
                self._rows[i] = key_map[key]
