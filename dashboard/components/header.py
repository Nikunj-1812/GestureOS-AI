"""
GestureOS AI — Top Header Component
=====================================
Full-width header bar containing:
  • Page title (updates on navigation)
  • Breadcrumb path
  • Camera status indicator
  • System status dot
  • Current time (live updating)
"""

from __future__ import annotations
import time
from datetime import datetime
import customtkinter as ctk
from dashboard.theme import COLORS, FONTS, SIZES


class TopHeader(ctk.CTkFrame):
    """
    Top header bar — fixed at the top of the main content area.

    Args:
        master : Parent widget.
    """

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            height=SIZES["header_h"],
            corner_radius=0,
            fg_color=COLORS["header_bg"],
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)   # title area expands

        self._page_title = "Dashboard"
        self._build()
        self._tick()   # start clock

    # ──────────────────────────────────────────────────────────────
    # Build
    # ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Left: page title + breadcrumb ─────────────────────────
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="nsw", padx=(20, 0), pady=0)

        self._title_label = ctk.CTkLabel(
            title_frame,
            text=self._page_title,
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["text"],
            anchor="w",
        )
        self._title_label.grid(row=0, column=0, sticky="w", pady=(10, 0))

        self._breadcrumb = ctk.CTkLabel(
            title_frame,
            text="GestureOS AI  /  Dashboard",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        self._breadcrumb.grid(row=1, column=0, sticky="w", pady=(0, 8))

        # ── Centre: spacer (handled by column weight) ──────────────

        # ── Right: status indicators + clock ──────────────────────
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="nse", padx=(0, 20), pady=0)

        # Camera status chip
        self._cam_chip = _StatusChip(
            right_frame,
            label="Camera",
            status="off",
        )
        self._cam_chip.grid(row=0, column=0, padx=(0, 12), pady=14)

        # System status chip
        self._sys_chip = _StatusChip(
            right_frame,
            label="System",
            status="ok",
        )
        self._sys_chip.grid(row=0, column=1, padx=(0, 20), pady=14)

        # Vertical divider
        div = ctk.CTkFrame(
            right_frame,
            width=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
        )
        div.grid(row=0, column=2, sticky="ns", padx=(0, 16), pady=8)

        # Clock
        self._clock_label = ctk.CTkLabel(
            right_frame,
            text="00:00:00",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["subtext1"],
        )
        self._clock_label.grid(row=0, column=3, pady=14)

        # Bottom border
        border = ctk.CTkFrame(
            self,
            height=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
        )
        border.grid(row=1, column=0, columnspan=3, sticky="ew", padx=0, pady=0)

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def set_page(self, title: str, breadcrumb: str = "") -> None:
        """Updates the page title and breadcrumb text."""
        self._page_title = title
        self._title_label.configure(text=title)
        crumb = breadcrumb or f"GestureOS AI  /  {title}"
        self._breadcrumb.configure(text=crumb)

    def set_camera_status(self, active: bool) -> None:
        """Updates the camera status chip."""
        self._cam_chip.set_status("ok" if active else "off")

    def set_system_status(self, status: str) -> None:
        """Updates the system status chip. status: 'ok' | 'warn' | 'err'"""
        self._sys_chip.set_status(status)

    # ──────────────────────────────────────────────────────────────
    # Clock
    # ──────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._clock_label.configure(text=now)
        self.after(1000, self._tick)   # update every second


# ──────────────────────────────────────────────────────────────────
# Helper widget — status chip
# ──────────────────────────────────────────────────────────────────

class _StatusChip(ctk.CTkFrame):
    """
    Small pill-shaped indicator showing a coloured dot + label.
    status: 'ok' → green  |  'warn' → yellow  |  'err' → red  |  'off' → grey
    """

    _DOT_COLORS = {
        "ok":   COLORS["status_ok"],
        "warn": COLORS["status_warn"],
        "err":  COLORS["status_err"],
        "off":  COLORS["overlay0"],
    }

    def __init__(self, master, label: str, status: str = "off", **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=12,
            **kwargs,
        )
        self._label_text = label
        self.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=self._DOT_COLORS.get(status, COLORS["overlay0"]),
        )
        self._dot.grid(row=0, column=0, padx=(8, 2), pady=4)

        self._lbl = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["subtext1"],
        )
        self._lbl.grid(row=0, column=1, padx=(0, 8), pady=4)

    def set_status(self, status: str) -> None:
        color = self._DOT_COLORS.get(status, COLORS["overlay0"])
        self._dot.configure(text_color=color)
