"""
GestureOS AI — Gesture Training Page
====================================
Modern UI-only page for gesture recording and training.
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.components.widgets import Badge, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class GestureTrainingPage(BasePage):
    PAGE_KEY = "gesture_training"
    PAGE_TITLE = "Training Page"
    PAGE_ICON = "◈"

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
            text="Training Page",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="A clean placeholder for gesture recording, mapping, and model training. No AI implementation is active yet.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(hero, text="UI Only", color=COLORS["yellow"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        SectionTitle(self, "Training Details", "Gesture metadata shown as static layout placeholders.").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        details = ctk.CTkFrame(self, fg_color="transparent")
        details.grid(row=2, column=0, sticky="ew", padx=pad)
        details.grid_columnconfigure((0, 1, 2), weight=1)

        gesture_card = _DetailCard(
            details,
            title="Gesture Name",
            value="thumbs_up",
            subtitle="Name for the gesture sample set",
            accent=COLORS["blue"],
        )
        gesture_card.grid(row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_sm"]))

        mapping_card = _DetailCard(
            details,
            title="Action Mapping",
            value="Play / Pause",
            subtitle="Action assigned to this gesture",
            accent=COLORS["green"],
        )
        mapping_card.grid(row=0, column=1, sticky="nsew", padx=(SIZES["pad_sm"], SIZES["pad_sm"]))

        samples_card = _DetailCard(
            details,
            title="Samples Count",
            value="200",
            subtitle="Number of recorded samples",
            accent=COLORS["peach"],
        )
        samples_card.grid(row=0, column=2, sticky="nsew", padx=(SIZES["pad_sm"], 0))

        SectionTitle(self, "Training Controls", "Inactive buttons for recording and model workflow.").grid(
            row=3, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        controls = ctk.CTkFrame(self, fg_color=COLORS["surface0"], corner_radius=24, border_width=SIZES["border_w"], border_color=COLORS["card_border"])
        controls.grid(row=4, column=0, sticky="ew", padx=pad)
        controls.grid_columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(controls, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(pad, SIZES["pad_sm"]), pady=pad)
        left.grid_columnconfigure(0, weight=1)

        for index, (label, accent, icon) in enumerate(
            [
                ("Start Recording", COLORS["green"], "⏺"),
                ("Stop Recording", COLORS["red"], "⏹"),
            ]
        ):
            button = _TrainingButton(left, icon=icon, label=label, accent=accent)
            button.grid(row=index, column=0, sticky="ew", pady=(0, SIZES["pad_sm"]) if index == 0 else 0)

        right = ctk.CTkFrame(controls, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(SIZES["pad_sm"], pad), pady=pad)
        right.grid_columnconfigure(0, weight=1)

        for index, (label, accent, icon) in enumerate(
            [
                ("Train Model", COLORS["mauve"], "◈"),
                ("Save Gesture", COLORS["peach"], "⌁"),
            ]
        ):
            button = _TrainingButton(right, icon=icon, label=label, accent=accent)
            button.grid(row=index, column=0, sticky="ew", pady=(0, SIZES["pad_sm"]) if index == 0 else 0)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", padx=pad, pady=(pad, pad))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text="No AI implementation yet.",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")


class _DetailCard(ctk.CTkFrame):
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
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
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
            wraplength=280,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))


class _TrainingButton(ctk.CTkFrame):
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