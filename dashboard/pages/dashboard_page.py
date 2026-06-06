"""
GestureOS AI — Dashboard Page
================================
Home screen showing:
  • 4 stat cards (FPS, Accuracy, Gestures Today, Uptime)
  • Quick-launch buttons for each control module
  • System status summary
  • Recent activity log placeholder
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import (
    StatCard, SectionTitle, Divider, Badge, EmptyState
)
from dashboard.theme import COLORS, FONTS, SIZES


class DashboardPage(BasePage):

    PAGE_KEY   = "dashboard"
    PAGE_TITLE = "Dashboard"
    PAGE_ICON  = "⊞"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]

        # ── Welcome banner ────────────────────────────────────────
        banner = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=SIZES["card_radius"],
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        banner.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        banner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            banner,
            text="Welcome to GestureOS AI  ✋",
            font=ctk.CTkFont(*FONTS["title"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            banner,
            text="Control your PC with hand gestures — no mouse, no keyboard.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        # Status badge
        Badge(banner, text="● System Ready", color=COLORS["green"]).grid(
            row=0, column=1, padx=pad, pady=pad, sticky="e"
        )

        # ── Stat cards row ────────────────────────────────────────
        SectionTitle(self, "Overview", "Real-time system metrics").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=2, column=0, sticky="ew", padx=pad, pady=0)
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="card")

        _stat_data = [
            ("▶",  "--",     "FPS",               COLORS["blue"]),
            ("◎",  "--",     "Detection Accuracy", COLORS["green"]),
            ("◈",  "0",      "Gestures Today",     COLORS["mauve"]),
            ("⏱",  "00:00",  "Session Uptime",     COLORS["peach"]),
        ]
        for col, (icon, val, label, color) in enumerate(_stat_data):
            StatCard(
                cards_frame,
                icon=icon, value=val, label=label, accent=color,
            ).grid(row=0, column=col, sticky="nsew", padx=(0, SIZES["pad_sm"]) if col < 3 else 0, pady=0)

        # ── Quick launch ──────────────────────────────────────────
        SectionTitle(self, "Quick Launch", "Start a control module").grid(
            row=3, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        launch_frame = ctk.CTkFrame(self, fg_color="transparent")
        launch_frame.grid(row=4, column=0, sticky="ew", padx=pad, pady=0)
        for i in range(3):
            launch_frame.grid_columnconfigure(i, weight=1, uniform="launch")

        _launch_items = [
            ("⊹", "Virtual Mouse",    COLORS["blue"]),
            ("⌨", "Virtual Keyboard", COLORS["sapphire"]),
            ("✏", "Air Drawing",      COLORS["mauve"]),
            ("▶", "Media Control",    COLORS["green"]),
            ("⚙", "System Control",   COLORS["peach"]),
            ("◈", "Gesture Training", COLORS["yellow"]),
        ]
        for idx, (icon, label, color) in enumerate(_launch_items):
            col = idx % 3
            row_offset = idx // 3

            btn_frame = ctk.CTkFrame(
                launch_frame,
                fg_color=COLORS["surface0"],
                corner_radius=SIZES["card_radius"],
                border_width=SIZES["border_w"],
                border_color=COLORS["card_border"],
            )
            btn_frame.grid(
                row=row_offset, column=col,
                sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if col < 2 else 0,
                pady=(0, SIZES["pad_sm"]),
            )
            btn_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                btn_frame, text=icon,
                font=ctk.CTkFont("Segoe UI", 28),
                text_color=color,
            ).grid(row=0, column=0, pady=(SIZES["pad_md"], 4))

            ctk.CTkLabel(
                btn_frame, text=label,
                font=ctk.CTkFont(*FONTS["body_bold"]),
                text_color=COLORS["text"],
            ).grid(row=1, column=0, pady=(0, 4))

            ctk.CTkButton(
                btn_frame, text="Launch",
                font=ctk.CTkFont(*FONTS["small"]),
                fg_color=COLORS["surface1"],
                hover_color=COLORS["accent"],
                text_color=COLORS["text"],
                height=28,
                corner_radius=6,
            ).grid(row=2, column=0, padx=SIZES["pad_md"], pady=(0, SIZES["pad_md"]), sticky="ew")

        # ── Recent activity ───────────────────────────────────────
        SectionTitle(self, "Recent Activity", "Last session events").grid(
            row=5, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        EmptyState(
            self,
            icon="◷",
            title="No activity yet",
            subtitle="Start a gesture session to see events here.",
        ).grid(row=6, column=0, sticky="nsew", padx=pad, pady=(0, pad))
