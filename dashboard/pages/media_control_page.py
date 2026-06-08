"""
GestureOS AI — Media Control Page
=================================
Modern UI-only page for media gesture controls.
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.components.widgets import Badge, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class MediaControlPage(BasePage):
    PAGE_KEY = "media_control"
    PAGE_TITLE = "Media Page"
    PAGE_ICON = "▶"

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
            text="Media Page",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="A polished placeholder for future media controls. Volume and brightness are shown as UI bars only.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(hero, text="UI Only", color=COLORS["yellow"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        SectionTitle(self, "Controls", "Volume and brightness placeholders for the media module.").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=pad)
        controls.grid_columnconfigure((0, 1), weight=1)

        volume_card = _BarCard(
            controls,
            title="Volume Bar",
            subtitle="Future hand gesture volume control",
            accent=COLORS["blue"],
            fill_percent=72,
        )
        volume_card.grid(row=0, column=0, sticky="ew", padx=(0, SIZES["pad_sm"]))

        brightness_card = _BarCard(
            controls,
            title="Brightness Bar",
            subtitle="Future screen brightness control",
            accent=COLORS["peach"],
            fill_percent=58,
        )
        brightness_card.grid(row=0, column=1, sticky="ew", padx=(SIZES["pad_sm"], 0))

        SectionTitle(self, "Playback", "Transport buttons shown as inactive UI placeholders.").grid(
            row=3, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        playback = ctk.CTkFrame(self, fg_color=COLORS["surface0"], corner_radius=24, border_width=SIZES["border_w"], border_color=COLORS["card_border"])
        playback.grid(row=4, column=0, sticky="ew", padx=pad)
        playback.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for index, (label, accent, icon) in enumerate(
            [
                ("Previous", COLORS["mauve"], "⏮"),
                ("Play", COLORS["green"], "▶"),
                ("Pause", COLORS["yellow"], "⏸"),
                ("Next", COLORS["peach"], "⏭"),
            ]
        ):
            button = _PlaybackButton(playback, icon=icon, label=label, accent=accent)
            button.grid(
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
            text="No functionality yet.",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")


class _BarCard(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str, accent: str, fill_percent: int, **kwargs) -> None:
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
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 2))

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16)

        track = ctk.CTkFrame(
            self,
            fg_color=COLORS["crust"],
            corner_radius=999,
            height=18,
        )
        track.grid(row=2, column=0, sticky="ew", padx=16, pady=(14, 8))
        track.grid_propagate(False)
        track.grid_columnconfigure(0, weight=1)

        fill = ctk.CTkFrame(track, fg_color=accent, corner_radius=999, width=max(18, fill_percent * 4))
        fill.grid(row=0, column=0, sticky="w")
        fill.grid_propagate(False)

        ctk.CTkLabel(
            self,
            text=f"{fill_percent}%",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=accent,
            anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=16, pady=(0, 16))


class _PlaybackButton(ctk.CTkFrame):
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