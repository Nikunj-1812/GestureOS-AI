"""
GestureOS AI — System Control Page
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import SectionTitle, CameraFeed, ToggleRow
from dashboard.theme import COLORS, FONTS, SIZES


class SystemControlPage(BasePage):

    PAGE_KEY   = "system_control"
    PAGE_TITLE = "System Control"
    PAGE_ICON  = "⚙"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]

        SectionTitle(self, "System Control", "Control OS functions with gestures").grid(
            row=0, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        # ── System action tiles ───────────────────────────────────
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=1, column=0, sticky="ew", padx=pad)
        for i in range(4):
            actions_frame.grid_columnconfigure(i, weight=1, uniform="sys")

        _actions = [
            ("⊞", "App Switcher",    "Alt+Tab",         COLORS["blue"]),
            ("⊡", "Show Desktop",    "Win+D",           COLORS["sapphire"]),
            ("⊠", "Task Manager",    "Ctrl+Shift+Esc",  COLORS["yellow"]),
            ("⊗", "Lock Screen",     "Win+L",           COLORS["red"]),
            ("⊕", "Screenshot",      "Win+Shift+S",     COLORS["green"]),
            ("≡", "Start Menu",      "Win key",         COLORS["mauve"]),
            ("◱", "Snap Left",       "Win+Left",        COLORS["peach"]),
            ("◲", "Snap Right",      "Win+Right",       COLORS["teal"]),
        ]

        for idx, (icon, label, shortcut, color) in enumerate(_actions):
            col = idx % 4
            row_off = idx // 4

            card = ctk.CTkFrame(
                actions_frame,
                fg_color=COLORS["surface0"],
                corner_radius=SIZES["card_radius"],
                border_width=SIZES["border_w"],
                border_color=COLORS["card_border"],
            )
            card.grid(
                row=row_off, column=col, sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if col < 3 else 0,
                pady=(0, SIZES["pad_sm"]),
            )
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont("Segoe UI", 26),
                         text_color=color).grid(row=0, column=0, pady=(SIZES["pad_md"], 2))
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(*FONTS["body_bold"]),
                         text_color=COLORS["text"]).grid(row=1, column=0)
            ctk.CTkLabel(card, text=shortcut, font=ctk.CTkFont(*FONTS["small"]),
                         text_color=COLORS["overlay1"]).grid(row=2, column=0, pady=(2, SIZES["pad_md"]))

        # ── Live camera + detected gesture ────────────────────────
        SectionTitle(self, "Camera Feed").grid(
            row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        feed_row = ctk.CTkFrame(self, fg_color="transparent")
        feed_row.grid(row=3, column=0, sticky="ew", padx=pad)
        feed_row.grid_columnconfigure(0, weight=2)
        feed_row.grid_columnconfigure(1, weight=1)

        CameraFeed(feed_row, width=540, height=300).grid(row=0, column=0, padx=(0, SIZES["pad_md"]))

        info = ctk.CTkFrame(feed_row, fg_color=COLORS["surface0"], corner_radius=SIZES["card_radius"])
        info.grid(row=0, column=1, sticky="nsew")
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(info, text="Detected Action",
                     font=ctk.CTkFont(*FONTS["label"]),
                     text_color=COLORS["overlay1"]).grid(row=0, column=0, pady=(SIZES["pad_md"], 4))
        ctk.CTkLabel(info, text="--",
                     font=ctk.CTkFont("Segoe UI", 28, "bold"),
                     text_color=COLORS["accent"]).grid(row=1, column=0)
        ctk.CTkLabel(info, text="Waiting for gesture...",
                     font=ctk.CTkFont(*FONTS["small"]),
                     text_color=COLORS["overlay1"]).grid(row=2, column=0, pady=(4, SIZES["pad_md"]))

        # ── Settings ──────────────────────────────────────────────
        SectionTitle(self, "Settings").grid(
            row=4, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )
        sf = ctk.CTkFrame(self, fg_color=COLORS["surface0"], corner_radius=SIZES["card_radius"])
        sf.grid(row=5, column=0, sticky="ew", padx=pad)
        sf.grid_columnconfigure(0, weight=1)

        for label, desc in [
            ("Enable System Control",   "Use gestures to trigger OS shortcuts"),
            ("Confirm Before Execute",  "Show preview before running action"),
            ("Gesture Hold Duration",   "Require gesture hold before triggering"),
        ]:
            ToggleRow(sf, label=label, description=desc).grid(
                row=sf.grid_size()[1], column=0, sticky="ew",
                padx=SIZES["pad_md"], pady=(SIZES["pad_sm"], 0)
            )

        ctk.CTkButton(
            self, text="▶  Start System Control",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=44, corner_radius=SIZES["btn_radius"],
        ).grid(row=6, column=0, sticky="ew", padx=pad, pady=pad)
