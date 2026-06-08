"""
GestureOS AI — Base Page
==========================
All pages inherit from BasePage which provides:
  • Scrollable content area
  • Consistent padding
  • on_enter() / on_leave() lifecycle hooks for future use
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.theme import COLORS, SIZES


class BasePage(ctk.CTkScrollableFrame):
    """
    Base class for all dashboard pages.

    Inherits CTkScrollableFrame so content scrolls automatically
    when it exceeds the visible area.

    Subclasses should:
      1. Call super().__init__(master, **kwargs)
      2. Implement _build() to create their UI
      3. Optionally override on_enter() / on_leave()
    """

    # Page metadata — override in subclasses
    PAGE_KEY   : str = ""
    PAGE_TITLE : str = "Page"
    PAGE_ICON  : str = "◈"

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["base"],
            scrollbar_button_color=COLORS["surface1"],
            scrollbar_button_hover_color=COLORS["surface2"],
            corner_radius=0,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        """Override in subclasses to create page content."""
        pass

    def on_enter(self) -> None:
        """Called when this page becomes visible. Override for live updates."""
        pass

    def on_leave(self) -> None:
        """Called when navigating away from this page."""
        pass
