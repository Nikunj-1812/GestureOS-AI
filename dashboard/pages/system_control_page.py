"""
GestureOS AI — System Control Page
==================================
Modern UI-only page for system gesture controls.
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.components.widgets import Badge, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class SystemControlPage(BasePage):
    PAGE_KEY = "system_control"
    PAGE_TITLE = "System Page"
    PAGE_ICON = "⚙"

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
            text="System Page",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="A modern placeholder for system-level actions. App cards and control buttons are shown for layout only.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(hero, text="UI Only", color=COLORS["yellow"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        SectionTitle(self, "Application Cards", "Common desktop apps shown as future gesture targets.").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        apps = ctk.CTkFrame(self, fg_color="transparent")
        apps.grid(row=2, column=0, sticky="ew", padx=pad)
        for column in range(2):
            apps.grid_columnconfigure(column, weight=1)

        app_cards = [
            ("🌐", "Chrome", "Browser launch placeholder", COLORS["blue"]),
            ("", "VS Code", "Editor launch placeholder", COLORS["teal"]),
            ("📝", "Notepad", "Quick notes placeholder", COLORS["green"]),
            ("🗂", "Explorer", "File manager placeholder", COLORS["mauve"]),
            ("🧮", "Calculator", "Utility app placeholder", COLORS["peach"]),
        ]

        for index, (icon, title, subtitle, accent) in enumerate(app_cards):
            row = index // 2
            column = index % 2
            card = _AppCard(apps, icon=icon, title=title, subtitle=subtitle, accent=accent)
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if column == 0 else 0,
                pady=(0, SIZES["pad_sm"]),
            )

        SectionTitle(self, "System Actions", "Inactive action buttons for future OS gestures.").grid(
            row=3, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        actions = ctk.CTkFrame(self, fg_color=COLORS["surface0"], corner_radius=24, border_width=SIZES["border_w"], border_color=COLORS["card_border"])
        actions.grid(row=4, column=0, sticky="ew", padx=pad)
        actions.grid_columnconfigure((0, 1, 2), weight=1)

        for index, (icon, label, accent) in enumerate(
            [
                ("📸", "Screenshot", COLORS["green"]),
                ("🔒", "Lock Screen", COLORS["red"]),
                ("🧰", "Task Manager", COLORS["yellow"]),
            ]
        ):
            button = _ActionButton(actions, icon=icon, label=label, accent=accent)
            button.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if index < 2 else 0,
                pady=pad,
            )

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", padx=pad, pady=(pad, pad))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text="No functionality yet.",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")


class _AppCard(ctk.CTkFrame):
    def __init__(self, master, icon: str, title: str, subtitle: str, accent: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["card_border"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        icon_box = ctk.CTkFrame(self, fg_color=COLORS["base"], width=50, height=50, corner_radius=16)
        icon_box.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))
        icon_box.grid_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text=icon,
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=accent,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            justify="left",
            wraplength=320,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))


class _ActionButton(ctk.CTkFrame):
    def __init__(self, master, icon: str, label: str, accent: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["base"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["divider"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        chip = ctk.CTkFrame(self, fg_color=COLORS["surface1"], width=48, height=48, corner_radius=16)
        chip.grid(row=0, column=0, pady=(16, 8))
        chip.grid_propagate(False)

        ctk.CTkLabel(
            chip,
            text=icon,
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=accent,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
        ).grid(row=1, column=0, pady=(0, 16))