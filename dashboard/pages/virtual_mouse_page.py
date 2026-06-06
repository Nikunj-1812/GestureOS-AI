"""
GestureOS AI — Virtual Mouse Page
=====================================
UI layout for the virtual mouse control module.
Functionality will be wired in a later phase.
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import (
    StatCard, SectionTitle, ToggleRow, CameraFeed, InfoRow
)
from dashboard.theme import COLORS, FONTS, SIZES


class VirtualMousePage(BasePage):

    PAGE_KEY   = "virtual_mouse"
    PAGE_TITLE = "Virtual Mouse"
    PAGE_ICON  = "⊹"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]
        self.grid_columnconfigure(0, weight=1)

        # ── Camera feed + controls (two-column layout) ────────────
        SectionTitle(self, "Live Tracking", "Hand position controls the cursor").grid(
            row=0, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=pad, pady=0)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)

        # Left: camera feed
        CameraFeed(content, width=640, height=380).grid(
            row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_md"]), pady=0
        )

        # Right: stat cards
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        for i, (icon, val, label, color) in enumerate([
            ("⊹", "--", "Cursor X",     COLORS["blue"]),
            ("⊹", "--", "Cursor Y",     COLORS["sapphire"]),
            ("▦", "--", "Click Count",  COLORS["green"]),
            ("▶", "--", "FPS",          COLORS["peach"]),
        ]):
            StatCard(right, icon=icon, value=val, label=label, accent=color).grid(
                row=i, column=0, sticky="ew", pady=(0, SIZES["pad_sm"])
            )

        # ── Settings ──────────────────────────────────────────────
        SectionTitle(self, "Mouse Settings", "Sensitivity and behaviour").grid(
            row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        settings_frame = ctk.CTkFrame(self, fg_color=COLORS["surface0"], corner_radius=SIZES["card_radius"])
        settings_frame.grid(row=3, column=0, sticky="ew", padx=pad, pady=0)
        settings_frame.grid_columnconfigure(0, weight=1)

        for i, (label, desc) in enumerate([
            ("Enable Virtual Mouse",     "Use hand gestures to control cursor"),
            ("Smooth Movement",          "Apply movement smoothing filter"),
            ("Click on Pinch",           "Pinch thumb+index to left-click"),
            ("Scroll on Two Fingers",    "Two-finger vertical gesture for scroll"),
        ]):
            ToggleRow(settings_frame, label=label, description=desc, default=(i == 0)).grid(
                row=i, column=0, sticky="ew",
                padx=SIZES["pad_md"], pady=(SIZES["pad_sm"], 0)
            )

        # Sensitivity slider
        slider_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        slider_frame.grid(row=4, column=0, sticky="ew", padx=SIZES["pad_md"], pady=SIZES["pad_md"])
        slider_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            slider_frame, text="Sensitivity",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["text"], anchor="w", width=140,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkSlider(
            slider_frame,
            from_=1, to=10,
            number_of_steps=9,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["btn_hover"],
        ).grid(row=0, column=1, sticky="ew", padx=(SIZES["pad_md"], 0))

        # Start button
        ctk.CTkButton(
            self, text="▶  Start Virtual Mouse",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=44,
            corner_radius=SIZES["btn_radius"],
        ).grid(row=4, column=0, sticky="ew", padx=pad, pady=pad)
