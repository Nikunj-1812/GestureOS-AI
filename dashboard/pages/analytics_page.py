"""
GestureOS AI — Analytics Page
=============================
Modern UI-only page for performance analytics.
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.components.widgets import Badge, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class AnalyticsPage(BasePage):
    PAGE_KEY = "analytics"
    PAGE_TITLE = "Analytics Page"
    PAGE_ICON = "▦"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]
        self.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        hero.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero,
            text="Analytics Page",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="A modern analytics dashboard shell for gesture performance insights. Charts and session summaries are placeholders only.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(hero, text="UI Only", color=COLORS["yellow"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        SectionTitle(self, "Charts", "Placeholder views for core analytics trends.").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        charts = ctk.CTkFrame(self, fg_color="transparent")
        charts.grid(row=2, column=0, sticky="ew", padx=pad)
        charts.grid_columnconfigure((0, 1), weight=1)

        accuracy_chart = _ChartCard(
            charts,
            title="Accuracy Chart",
            subtitle="Gesture confidence and model accuracy trends",
            accent=COLORS["blue"],
            placeholder="Accuracy chart placeholder",
        )
        accuracy_chart.grid(row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_sm"]))

        usage_chart = _ChartCard(
            charts,
            title="Usage Chart",
            subtitle="Session activity and gesture usage trends",
            accent=COLORS["mauve"],
            placeholder="Usage chart placeholder",
        )
        usage_chart.grid(row=0, column=1, sticky="nsew", padx=(SIZES["pad_sm"], 0))

        SectionTitle(self, "Session Statistics", "Summary metrics shown as static dashboard cards.").grid(
            row=3, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=4, column=0, sticky="ew", padx=pad)
        stats.grid_columnconfigure((0, 1, 2), weight=1)

        stat_cards = [
            ("Total Sessions", "--", "Sessions recorded in this workspace", COLORS["green"]),
            ("Average Accuracy", "--%", "Model accuracy across sessions", COLORS["peach"]),
            ("Active Gestures", "--", "Distinct gestures available to the model", COLORS["sapphire"]),
        ]

        for index, (title, value, subtitle, accent) in enumerate(stat_cards):
            card = _StatCard(stats, title=title, value=value, subtitle=subtitle, accent=accent)
            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if index < 2 else 0,
            )

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", padx=pad, pady=(pad, pad))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text="No analytics logic yet.",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")


class _ChartCard(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str, accent: str, placeholder: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["card_border"],
            height=280,
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=380,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        body = ctk.CTkFrame(self, fg_color=COLORS["base"], corner_radius=20)
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            body,
            text=f"{placeholder}\n\nChart will render here",
            font=ctk.CTkFont("Segoe UI", 14),
            text_color=accent,
            justify="center",
        ).grid(row=0, column=0)


class _StatCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, subtitle: str, accent: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["card_border"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont("Segoe UI", 24, "bold"),
            text_color=accent,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            justify="left",
            wraplength=300,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))