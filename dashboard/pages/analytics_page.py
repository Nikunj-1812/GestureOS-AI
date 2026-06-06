"""
GestureOS AI — Analytics Page
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import SectionTitle, StatCard, EmptyState
from dashboard.theme import COLORS, FONTS, SIZES


class AnalyticsPage(BasePage):

    PAGE_KEY   = "analytics"
    PAGE_TITLE = "Analytics"
    PAGE_ICON  = "▦"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]

        SectionTitle(self, "Analytics", "Session statistics and performance trends").grid(
            row=0, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        # ── Summary stat cards ────────────────────────────────────
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", padx=pad)
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1, uniform="analytics_stat")

        for col, (icon, val, label, color) in enumerate([
            ("▦",  "0",      "Total Sessions",     COLORS["blue"]),
            ("◈",  "0",      "Total Gestures",     COLORS["green"]),
            ("▶",  "--%",    "Avg Accuracy",        COLORS["mauve"]),
            ("⏱",  "0h 0m",  "Total Usage Time",   COLORS["peach"]),
        ]):
            StatCard(stats, icon=icon, value=val, label=label, accent=color).grid(
                row=0, column=col,
                padx=(0, SIZES["pad_sm"]) if col < 3 else 0,
                sticky="nsew",
            )

        # ── Charts area ───────────────────────────────────────────
        SectionTitle(self, "Performance Charts").grid(
            row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        charts_row = ctk.CTkFrame(self, fg_color="transparent")
        charts_row.grid(row=3, column=0, sticky="ew", padx=pad)
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)

        for col, title in enumerate(["FPS Over Time", "Gesture Accuracy"]):
            chart_card = ctk.CTkFrame(
                charts_row,
                fg_color=COLORS["surface0"],
                corner_radius=SIZES["card_radius"],
                border_width=SIZES["border_w"],
                border_color=COLORS["card_border"],
                height=220,
            )
            chart_card.grid(
                row=0, column=col, sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if col == 0 else 0,
            )
            chart_card.grid_propagate(False)
            chart_card.grid_rowconfigure(1, weight=1)
            chart_card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                chart_card, text=title,
                font=ctk.CTkFont(*FONTS["body_bold"]),
                text_color=COLORS["text"], anchor="w",
            ).grid(row=0, column=0, padx=SIZES["pad_md"], pady=(SIZES["pad_md"], 0), sticky="w")

            # Chart placeholder
            ctk.CTkLabel(
                chart_card,
                text="▦\n\nChart will render here",
                font=ctk.CTkFont("Segoe UI", 14),
                text_color=COLORS["overlay0"],
                justify="center",
            ).grid(row=1, column=0)

        # ── Gesture usage breakdown ───────────────────────────────
        SectionTitle(self, "Gesture Usage Breakdown").grid(
            row=4, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        breakdown_row = ctk.CTkFrame(self, fg_color="transparent")
        breakdown_row.grid(row=5, column=0, sticky="ew", padx=pad)
        breakdown_row.grid_columnconfigure(0, weight=1)
        breakdown_row.grid_columnconfigure(1, weight=1)

        # Pie chart placeholder
        pie = ctk.CTkFrame(
            breakdown_row,
            fg_color=COLORS["surface0"],
            corner_radius=SIZES["card_radius"],
            height=200,
        )
        pie.grid(row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_sm"]))
        pie.grid_propagate(False)
        pie.grid_rowconfigure(0, weight=1)
        pie.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(pie, text="◉\n\nGesture distribution\nchart placeholder",
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=COLORS["overlay0"], justify="center").grid(row=0, column=0)

        # Top gestures list
        top_list = ctk.CTkFrame(
            breakdown_row,
            fg_color=COLORS["surface0"],
            corner_radius=SIZES["card_radius"],
        )
        top_list.grid(row=0, column=1, sticky="nsew")
        top_list.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_list, text="Top Gestures",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"], anchor="w",
        ).grid(row=0, column=0, padx=SIZES["pad_md"], pady=(SIZES["pad_md"], SIZES["pad_sm"]), sticky="w")

        for i, gesture in enumerate(["--", "--", "--", "--", "--"]):
            row_frame = ctk.CTkFrame(top_list, fg_color="transparent")
            row_frame.grid(row=i + 1, column=0, sticky="ew", padx=SIZES["pad_md"], pady=2)
            row_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row_frame, text=f"{i+1}.", width=24,
                         font=ctk.CTkFont(*FONTS["small"]),
                         text_color=COLORS["overlay0"]).grid(row=0, column=0)
            ctk.CTkLabel(row_frame, text=gesture,
                         font=ctk.CTkFont(*FONTS["body"]),
                         text_color=COLORS["subtext1"], anchor="w").grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(row_frame, text="0",
                         font=ctk.CTkFont(*FONTS["small"]),
                         text_color=COLORS["overlay1"]).grid(row=0, column=2)

        # ── Export ────────────────────────────────────────────────
        SectionTitle(self, "Export Data").grid(
            row=6, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        export_row = ctk.CTkFrame(self, fg_color="transparent")
        export_row.grid(row=7, column=0, sticky="ew", padx=pad, pady=(0, pad))

        for text, color in [
            ("⊞ Export CSV",   COLORS["surface1"]),
            ("▦ Export JSON",  COLORS["surface1"]),
            ("◎ Export PDF",   COLORS["accent"]),
        ]:
            ctk.CTkButton(
                export_row, text=text,
                font=ctk.CTkFont(*FONTS["body"]),
                fg_color=color,
                hover_color=COLORS["btn_hover"],
                text_color=COLORS["text"] if color == COLORS["surface1"] else COLORS["base"],
                height=38, width=150, corner_radius=SIZES["btn_radius"],
            ).grid(row=0, column=export_row.grid_size()[1], padx=(0, SIZES["pad_sm"]))
