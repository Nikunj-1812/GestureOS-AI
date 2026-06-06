"""
GestureOS AI — Footer Status Bar Component
============================================
Slim bottom bar showing:
  • Connection / engine status message (left)
  • FPS indicator (centre)
  • App version + copyright (right)
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.theme import COLORS, FONTS, SIZES


class FooterBar(ctk.CTkFrame):
    """
    Bottom status bar — fixed at the bottom of the window.

    Args:
        master : Parent widget.
    """

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            height=SIZES["footer_h"],
            corner_radius=0,
            fg_color=COLORS["footer_bg"],
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)   # centre expands

        self._build()

    # ──────────────────────────────────────────────────────────────
    # Build
    # ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Top border
        border = ctk.CTkFrame(
            self,
            height=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
        )
        border.grid(row=0, column=0, columnspan=3, sticky="ew")

        # ── Left: status message ──────────────────────────────────
        self._status_dot = ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont("Segoe UI", 9),
            text_color=COLORS["status_ok"],
        )
        self._status_dot.grid(row=1, column=0, padx=(12, 2), pady=0, sticky="w")

        self._status_msg = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(*FONTS["footer"]),
            text_color=COLORS["subtext0"],
            anchor="w",
        )
        self._status_msg.grid(row=1, column=0, padx=(24, 0), pady=0, sticky="w")

        # ── Centre: FPS ────────────────────────────────────────────
        self._fps_label = ctk.CTkLabel(
            self,
            text="FPS: --",
            font=ctk.CTkFont(*FONTS["footer"]),
            text_color=COLORS["overlay1"],
        )
        self._fps_label.grid(row=1, column=1, pady=0)

        # ── Right: version ─────────────────────────────────────────
        version_label = ctk.CTkLabel(
            self,
            text="GestureOS AI  v1.0.0  •  © 2026",
            font=ctk.CTkFont(*FONTS["footer"]),
            text_color=COLORS["overlay0"],
            anchor="e",
        )
        version_label.grid(row=1, column=2, padx=(0, 16), pady=0, sticky="e")

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def set_status(self, message: str, level: str = "ok") -> None:
        """
        Updates the status message and dot colour.
        level: 'ok' | 'warn' | 'err' | 'off'
        """
        dot_colors = {
            "ok":   COLORS["status_ok"],
            "warn": COLORS["status_warn"],
            "err":  COLORS["status_err"],
            "off":  COLORS["overlay0"],
        }
        self._status_msg.configure(text=message)
        self._status_dot.configure(
            text_color=dot_colors.get(level, COLORS["overlay0"])
        )

    def set_fps(self, fps: float) -> None:
        """Updates the FPS display."""
        color = (COLORS["status_ok"] if fps >= 25
                 else COLORS["status_warn"] if fps >= 15
                 else COLORS["status_err"])
        self._fps_label.configure(
            text=f"FPS: {fps:.1f}",
            text_color=color,
        )
