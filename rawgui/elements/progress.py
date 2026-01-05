"""Progress bar and spinner components.

NiceGUI-compatible progress indicators.
"""

from __future__ import annotations

from typing import Optional

from ..element import Element


class ProgressBar(Element):
    """A horizontal progress bar.

    Features:
    - Determinate progress (0-1)
    - Indeterminate mode (animated)
    - Optional label/percentage display
    - ASCII block characters

    Example:
        progress = ui.progress(value=0.5)
        progress.value = 0.75
    """

    def __init__(
        self,
        value: float = 0.0,
        *,
        show_value: bool = False,
        size: Optional[str] = None,
    ) -> None:
        """Create a progress bar.

        Args:
            value: Progress value 0.0 to 1.0 (None for indeterminate)
            show_value: Show percentage text
            size: Bar size ('sm', 'md', 'lg')
        """
        super().__init__()
        self.tag = "progress"
        self._indeterminate = value is None
        # Clamp initial value
        if value is not None:
            self._value = max(0.0, min(1.0, value))
        else:
            self._value = value
        self.show_value = show_value
        self.size = size or "md"

    @property
    def value(self) -> Optional[float]:
        """Get progress value (0-1)."""
        return self._value

    @value.setter
    def value(self, val: Optional[float]) -> None:
        """Set progress value."""
        if val is None:
            self._indeterminate = True
            self._value = None
        else:
            self._indeterminate = False
            self._value = max(0.0, min(1.0, val))

    @property
    def percentage(self) -> int:
        """Get progress as percentage."""
        if self._value is None:
            return 0
        return int(self._value * 100)

    def set_indeterminate(self) -> None:
        """Switch to indeterminate mode."""
        self._value = None
        self._indeterminate = True


class CircularProgress(Element):
    """A circular/spinner progress indicator.

    Features:
    - Spinning animation for indeterminate
    - Progress arc for determinate
    - ASCII spinner characters

    Example:
        spinner = ui.spinner()
        spinner = ui.spinner(value=0.5)  # Show 50% progress
    """

    # Spinner animation frames
    SPINNER_FRAMES = ["|", "/", "-", "\\"]

    def __init__(
        self,
        value: Optional[float] = None,
        *,
        size: Optional[str] = None,
    ) -> None:
        """Create a circular progress.

        Args:
            value: Progress value 0.0 to 1.0 (None for spinner)
            size: Size ('sm', 'md', 'lg')
        """
        super().__init__()
        self.tag = "spinner"
        self._value = value
        self.size = size or "md"
        self._frame = 0

    @property
    def value(self) -> Optional[float]:
        """Get progress value."""
        return self._value

    @value.setter
    def value(self, val: Optional[float]) -> None:
        """Set progress value."""
        if val is not None:
            self._value = max(0.0, min(1.0, val))
        else:
            self._value = None

    @property
    def current_frame(self) -> str:
        """Get current spinner frame character."""
        return self.SPINNER_FRAMES[self._frame % len(self.SPINNER_FRAMES)]

    def advance(self) -> None:
        """Advance spinner animation."""
        self._frame = (self._frame + 1) % len(self.SPINNER_FRAMES)


class LinearProgress(ProgressBar):
    """Alias for ProgressBar (NiceGUI compatibility)."""

    pass
