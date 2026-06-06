"""
GestureOS AI — Media Control Page
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import SectionTitle, CameraFeed, ToggleRow, StatCard
from dashboard.theme import COLORS, FONTS, SIZES


class MediaControlPage(BasePage):

    PAGE_KEY   = "media_control"
    PAGE_TITLE = "Media Control"
    PAGE_ICON  = "▶"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]

        SectionTitle(self, "Media Control", "Control playback, volume and apps with gestures").grid(
            row=0, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        # ── Gesture map cards ─────────────────────────────────────
        map_frame = ctk.CTkFrame(self, fg_color="transparent")
        map_frame.grid(row=1, column=0, sticky="ew", padx=pad)
        for i in range(3):
            map_frame.grid_columnconfigure(i, weight=1, uniform="media")

        _gesture_map = [
            ("✋", "Open Palm",     "Play / Pause",     COLORS["green"]),
            ("✊", "Fist",          "Stop",             COLORS["red"]),
            ("☝", "Index Up",      "Volume Up",        COLORS["blue"]),
            ("👇", "Index Down",   "Volume Down",      COLORS["sapphire"]),
            ("👈", "Swipe Left",   "Previous Track",   COLORS["mauve"]),
            ("👉", "Swipe Right",  "Next Track",       COLORS["peach"]),
        ]

        for idx, (icon, gesture, action, color) in enumerate(_gesture_map):
            col = idx % 3
            row_off = idx // 3

            card = ctk.CTkFrame(
                map_frame,
                fg_color=COLORS["surface0"],
                corner_radius=SIZES["card_radius"],
                border_width=SIZES["border_w"],
                border_color=COLORS["card_border"],
            )
            card.grid(
                row=row_off, column=col, sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if col < 2 else 0,
                pady=(0, SIZES["pad_sm"]),
            )
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont("Segoe UI", 32),
                         text_color=color).grid(row=0, column=0, pady=(SIZES["pad_md"], 2))
            ctk.CTkLabel(card, text=gesture, font=ctk.CTkFont(*FONTS["body_bold"]),
                         text_color=COLORS["text"]).grid(row=1, column=0)
            ctk.CTkLabel(card, text=f"→  {action}", font=ctk.CTkFont(*FONTS["small"]),
                         text_color=COLORS["overlay1"]).grid(row=2, column=0, pady=(2, SIZES["pad_md"]))

        # ── Live feed ─────────────────────────────────────────────
        SectionTitle(self, "Camera Feed", "Gesture detection preview").grid(
            row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        feed_row = ctk.CTkFrame(self, fg_color="transparent")
        feed_row.grid(row=3, column=0, sticky="ew", padx=pad)
        feed_row.grid_columnconfigure(0, weight=2)
        feed_row.grid_columnconfigure(1, weight=1)

        CameraFeed(feed_row, width=540, height=300).grid(row=0, column=0, padx=(0, SIZES["pad_md"]))

        status_card = ctk.CTkFrame(
            feed_row, fg_color=COLORS["surface0"], corner_radius=SIZES["card_radius"]
        )
        status_card.grid(row=0, column=1, sticky="nsew")
        status_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(status_card, text="Active Gesture",
                     font=ctk.CTkFont(*FONTS["label"]),
                     text_color=COLORS["overlay1"]).grid(row=0, column=0, pady=(SIZES["pad_md"], 4))
        ctk.CTkLabel(status_card, text="--",
                     font=ctk.CTkFont("Segoe UI", 32, "bold"),
                     text_color=COLORS["accent"]).grid(row=1, column=0)
        ctk.CTkLabel(status_card, text="Confidence:  --%",
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
            ("Enable Media Control",   "Use gestures to control media playback"),
            ("Show Gesture Overlay",   "Display gesture name on screen"),
            ("Hold to Confirm",        "Require 0.5s hold before triggering"),
        ]:
            ToggleRow(sf, label=label, description=desc).grid(
                row=sf.grid_size()[1], column=0, sticky="ew",
                padx=SIZES["pad_md"], pady=(SIZES["pad_sm"], 0)
            )

        ctk.CTkButton(
            self, text="▶  Start Media Control",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=44, corner_radius=SIZES["btn_radius"],
        ).grid(row=6, column=0, sticky="ew", padx=pad, pady=pad)
