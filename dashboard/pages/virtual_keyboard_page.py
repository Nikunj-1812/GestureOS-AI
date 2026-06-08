"""
GestureOS AI — Keyboard Page
===========================
Modern UI-only page for virtual keyboard controls.
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.components.widgets import Badge, EmptyState, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class VirtualKeyboardPage(BasePage):
    PAGE_KEY = "virtual_keyboard"
    PAGE_TITLE = "Keyboard Page"
    PAGE_ICON = "⌨"

    def __init__(self, master, on_navigate: callable | None = None, **kwargs) -> None:
        self._on_navigate = on_navigate
        super().__init__(master, **kwargs)

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
            text="Keyboard Page",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="A clean preview screen for future virtual keyboard controls. No keyboard logic is active yet.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(hero, text="UI Only", color=COLORS["yellow"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        SectionTitle(self, "Keyboard Layout Preview", "Placeholder area for the future on-screen keyboard.").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        layout_preview = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        layout_preview.grid(row=2, column=0, sticky="ew", padx=pad)
        layout_preview.grid_columnconfigure(0, weight=1)

        EmptyState(
            layout_preview,
            icon="⌨",
            title="Keyboard layout preview",
            subtitle="The on-screen keyboard grid will appear here during a future typing session.",
        ).grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)

        SectionTitle(self, "Future Features", "Planned keyboard interactions for this module.").grid(
            row=3, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        features = ctk.CTkFrame(self, fg_color="transparent")
        features.grid(row=4, column=0, sticky="ew", padx=pad, pady=0)
        for column in range(2):
            features.grid_columnconfigure(column, weight=1)

        feature_cards = [
            ("⌨", "Typing", "Compose text using finger gestures", COLORS["blue"]),
            ("⇧", "Special Keys", "Access Enter, Backspace, and modifiers", COLORS["green"]),
            ("⌘", "Shortcuts", "Trigger common system shortcuts", COLORS["mauve"]),
        ]

        for index, (icon, title, subtitle, accent) in enumerate(feature_cards):
            row = index // 2
            column = index % 2
            card = _FeatureCard(features, icon, title, subtitle, accent)
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if column == 0 else 0,
                pady=(0, SIZES["pad_sm"]),
            )

        nav_row = ctk.CTkFrame(self, fg_color="transparent")
        nav_row.grid(row=5, column=0, sticky="ew", padx=pad, pady=(pad, pad))
        nav_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            nav_row,
            text="← Back",
            command=lambda: self._navigate("dashboard"),
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["surface1"],
            hover_color=COLORS["nav_hover"],
            text_color=COLORS["text"],
            height=44,
            corner_radius=SIZES["btn_radius"],
        ).grid(row=0, column=0, sticky="ew", padx=(0, SIZES["pad_sm"]))

        ctk.CTkButton(
            nav_row,
            text="⌂ Home",
            command=lambda: self._navigate("dashboard"),
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=44,
            corner_radius=SIZES["btn_radius"],
        ).grid(row=0, column=1, sticky="ew")

    def _navigate(self, key: str) -> None:
        if self._on_navigate is not None:
            self._on_navigate(key)


class _FeatureCard(ctk.CTkFrame):
    def __init__(self, master, icon: str, title: str, subtitle: str, accent: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["card_border"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        icon_box = ctk.CTkFrame(self, fg_color=COLORS["base"], width=42, height=42, corner_radius=14)
        icon_box.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 8))
        icon_box.grid_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text=icon,
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=accent,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 4))

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            justify="left",
            wraplength=320,
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 14))