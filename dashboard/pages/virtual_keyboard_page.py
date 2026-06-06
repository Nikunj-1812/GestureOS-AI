"""
GestureOS AI — Virtual Keyboard Page
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import SectionTitle, CameraFeed, ToggleRow, EmptyState
from dashboard.theme import COLORS, FONTS, SIZES


class VirtualKeyboardPage(BasePage):

    PAGE_KEY   = "virtual_keyboard"
    PAGE_TITLE = "Virtual Keyboard"
    PAGE_ICON  = "⌨"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]

        SectionTitle(self, "Virtual Keyboard", "Type with hand gestures in mid-air").grid(
            row=0, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        # Two-column layout
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=pad)
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=1)

        CameraFeed(content, width=560, height=340).grid(
            row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_md"])
        )

        # Right panel — typed text preview
        right = ctk.CTkFrame(
            content,
            fg_color=COLORS["surface0"],
            corner_radius=SIZES["card_radius"],
        )
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right, text="Typed Text",
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=0, column=0, padx=SIZES["pad_md"], pady=(SIZES["pad_md"], 4), sticky="w")

        ctk.CTkTextbox(
            right,
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["crust"],
            text_color=COLORS["text"],
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
            corner_radius=SIZES["input_radius"],
            height=180,
        ).grid(row=1, column=0, padx=SIZES["pad_md"], pady=0, sticky="ew")

        ctk.CTkButton(
            right, text="⌫  Clear",
            font=ctk.CTkFont(*FONTS["small"]),
            fg_color=COLORS["surface1"],
            hover_color=COLORS["status_err"],
            text_color=COLORS["text"],
            height=32,
        ).grid(row=2, column=0, padx=SIZES["pad_md"], pady=SIZES["pad_md"], sticky="ew")

        # ── Keyboard layout preview ───────────────────────────────
        SectionTitle(self, "Keyboard Layout", "On-screen key map").grid(
            row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        EmptyState(
            self,
            icon="⌨",
            title="Keyboard layout",
            subtitle="The virtual key grid will be rendered here during an active session.",
        ).grid(row=3, column=0, sticky="nsew", padx=pad, pady=0)

        # ── Settings ──────────────────────────────────────────────
        SectionTitle(self, "Settings").grid(
            row=4, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        sf = ctk.CTkFrame(self, fg_color=COLORS["surface0"], corner_radius=SIZES["card_radius"])
        sf.grid(row=5, column=0, sticky="ew", padx=pad)
        sf.grid_columnconfigure(0, weight=1)

        for label, desc in [
            ("Enable Virtual Keyboard", "Activate air-typing mode"),
            ("Show Key Highlights",     "Highlight hovered keys"),
            ("Auto Capitalise",         "Capitalise first letter of sentences"),
        ]:
            ToggleRow(sf, label=label, description=desc).grid(
                row=sf.grid_size()[1], column=0, sticky="ew",
                padx=SIZES["pad_md"], pady=(SIZES["pad_sm"], 0)
            )

        ctk.CTkButton(
            self, text="▶  Start Virtual Keyboard",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=44,
            corner_radius=SIZES["btn_radius"],
        ).grid(row=6, column=0, sticky="ew", padx=pad, pady=pad)
