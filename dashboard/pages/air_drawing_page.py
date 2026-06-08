"""
GestureOS AI — Drawing Page
===========================
Modern UI-only page for air drawing.
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.components.widgets import Badge, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class AirDrawingPage(BasePage):
    PAGE_KEY = "air_drawing"
    PAGE_TITLE = "Drawing Page"
    PAGE_ICON = "✏"

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
            text="Drawing Page",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="A clean preview screen for future air drawing controls. No drawing functionality is active yet.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(hero, text="UI Only", color=COLORS["yellow"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        SectionTitle(self, "Canvas Placeholder", "Future drawing canvas area.").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        canvas = ctk.CTkFrame(
            self,
            fg_color=COLORS["crust"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
            height=420,
        )
        canvas.grid(row=2, column=0, sticky="ew", padx=pad)
        canvas.grid_propagate(False)
        canvas.grid_rowconfigure(0, weight=1)
        canvas.grid_columnconfigure(0, weight=1)

        placeholder = ctk.CTkFrame(canvas, fg_color="transparent")
        placeholder.grid(row=0, column=0)

        ctk.CTkLabel(
            placeholder,
            text="✏",
            font=ctk.CTkFont("Segoe UI", 54, "bold"),
            text_color=COLORS["overlay0"],
        ).grid(row=0, column=0, pady=(0, 10))

        ctk.CTkLabel(
            placeholder,
            text="Canvas Placeholder",
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["subtext0"],
        ).grid(row=1, column=0, pady=(0, 6))

        ctk.CTkLabel(
            placeholder,
            text="The drawing surface will appear here in a future version.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
        ).grid(row=2, column=0)

        SectionTitle(self, "Toolbar Placeholder", "Future drawing tools and actions.").grid(
            row=3, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        toolbar = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        toolbar.grid(row=4, column=0, sticky="ew", padx=pad)
        toolbar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        tool_specs = [
            ("✎", "Brush", COLORS["blue"]),
            ("⌫", "Eraser", COLORS["green"]),
            ("↶", "Undo", COLORS["mauve"]),
            ("⊞", "Save", COLORS["peach"]),
        ]

        for index, (icon, label, accent) in enumerate(tool_specs):
            card = _ToolCard(toolbar, icon, label, accent)
            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if index < 3 else 0,
                pady=pad,
            )

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", padx=pad, pady=(pad, pad))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text="Modern design. No drawing functionality yet.",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")


class _ToolCard(ctk.CTkFrame):
    def __init__(self, master, icon: str, label: str, accent: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["base"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["divider"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        icon_box = ctk.CTkFrame(self, fg_color=COLORS["surface1"], width=44, height=44, corner_radius=14)
        icon_box.grid(row=0, column=0, pady=(14, 8), sticky="n")
        icon_box.grid_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text=icon,
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=accent,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
        ).grid(row=1, column=0, pady=(0, 14))