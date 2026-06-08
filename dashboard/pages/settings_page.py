"""
GestureOS AI — Settings Page
============================
Modern UI for JSON-backed application settings.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from config.settings_manager import SettingsManager, SettingsState
from dashboard.components.widgets import Badge, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class SettingsPage(BasePage):
    PAGE_KEY = "settings"
    PAGE_TITLE = "Settings Page"
    PAGE_ICON = "≡"

    def __init__(
        self,
        master,
        settings_manager: SettingsManager | None = None,
        on_settings_changed: Callable[[SettingsState], None] | None = None,
        **kwargs,
    ) -> None:
        self._settings_manager = settings_manager or SettingsManager()
        self._on_settings_changed = on_settings_changed
        self._camera_menu: ctk.CTkOptionMenu | None = None
        self._theme_menu: ctk.CTkSegmentedButton | None = None
        self._fps_slider: ctk.CTkSlider | None = None
        self._camera_value_label: ctk.CTkLabel | None = None
        self._theme_value_label: ctk.CTkLabel | None = None
        self._fps_value_label: ctk.CTkLabel | None = None
        self._status_label: ctk.CTkLabel | None = None
        super().__init__(master, **kwargs)

    def _build(self) -> None:
        pad = SIZES["pad_lg"]
        state = self._settings_manager.state
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
            text="Settings Page",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="Load settings from settings.json and keep them in sync automatically. Camera selection, theme, and FPS limit are saved as soon as they change.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(hero, text="Loaded from settings.json", color=COLORS["yellow"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        SectionTitle(self, "Configuration", "Camera, theme, and frame rate controls.").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.grid(row=2, column=0, sticky="ew", padx=pad)
        grid.grid_columnconfigure((0, 1), weight=1)

        camera_card = _SettingCard(
            grid,
            title="Camera Selection",
            subtitle="Select the active camera source.",
            accent=COLORS["blue"],
        )
        camera_card.grid(row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_sm"]), pady=(0, SIZES["pad_sm"]))

        theme_card = _SettingCard(
            grid,
            title="Theme Selection",
            subtitle="Choose the dashboard appearance.",
            accent=COLORS["mauve"],
        )
        theme_card.grid(row=0, column=1, sticky="nsew", padx=(SIZES["pad_sm"], 0), pady=(0, SIZES["pad_sm"]))

        fps_card = _SettingCard(
            grid,
            title="FPS Limit",
            subtitle="Set the maximum camera refresh rate.",
            accent=COLORS["peach"],
        )
        fps_card.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self._build_camera_controls(camera_card, state)
        self._build_theme_controls(theme_card, state)
        self._build_fps_controls(fps_card, state)

        actions = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        actions.grid(row=3, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        actions.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            actions,
            text="Save Settings",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            actions,
            text="Changes auto-save immediately, and this button re-saves the current state.",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16)

        ctk.CTkButton(
            actions,
            text="✓  Save Settings",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=42,
            corner_radius=SIZES["btn_radius"],
            command=self._save_now,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(12, 16))

        self._status_label = ctk.CTkLabel(
            actions,
            text="Loaded settings.json",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        self._status_label.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 16))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=pad, pady=(pad, pad))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text=f"Source: {self._settings_manager.path.name}",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

    def _build_camera_controls(self, card: ctk.CTkFrame, state: SettingsState) -> None:
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Active Camera",
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        self._camera_menu = ctk.CTkOptionMenu(
            card,
            values=self._camera_options(state.camera_index),
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["surface1"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["btn_hover"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["surface0"],
            dropdown_text_color=COLORS["text"],
            width=280,
            height=38,
            command=self._handle_camera_change,
        )
        self._camera_menu.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))
        self._camera_menu.set(self._camera_label(state.camera_index))

        self._camera_value_label = ctk.CTkLabel(
            card,
            text=f"Current source: {self._camera_label(state.camera_index)}",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        self._camera_value_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

    def _build_theme_controls(self, card: ctk.CTkFrame, state: SettingsState) -> None:
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Current Theme",
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        self._theme_menu = ctk.CTkSegmentedButton(
            card,
            values=["Dark", "Light", "System"],
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["surface1"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["btn_hover"],
            unselected_color=COLORS["surface1"],
            unselected_hover_color=COLORS["nav_hover"],
            text_color=COLORS["text"],
            command=self._handle_theme_change,
        )
        self._theme_menu.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))
        self._theme_menu.set(state.theme.title())

        self._theme_value_label = ctk.CTkLabel(
            card,
            text=f"Theme loaded from JSON: {state.theme.title()}",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        self._theme_value_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

    def _build_fps_controls(self, card: ctk.CTkFrame, state: SettingsState) -> None:
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="FPS Limit",
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        slider_row = ctk.CTkFrame(card, fg_color="transparent")
        slider_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        slider_row.grid_columnconfigure(0, weight=1)

        self._fps_slider = ctk.CTkSlider(
            slider_row,
            from_=10,
            to=60,
            number_of_steps=50,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            command=self._handle_fps_change,
        )
        self._fps_slider.grid(row=0, column=0, sticky="ew")
        self._fps_slider.set(state.fps_limit)

        self._fps_value_label = ctk.CTkLabel(
            card,
            text=f"Current limit: {state.fps_limit} FPS",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        self._fps_value_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

    def _handle_camera_change(self, selection: str) -> None:
        camera_index = self._parse_camera_index(selection)
        changed = self._settings_manager.update(camera_index=camera_index)
        if not changed:
            return

        if self._camera_value_label is not None:
            self._camera_value_label.configure(text=f"Current source: {self._camera_label(camera_index)}")

        self._mark_saved("Camera selection saved")
        self._emit_settings_changed()

    def _handle_theme_change(self, selection: str) -> None:
        theme = selection.lower()
        changed = self._settings_manager.update(theme=theme)
        ctk.set_appearance_mode(theme)

        if self._theme_value_label is not None:
            self._theme_value_label.configure(text=f"Theme loaded from JSON: {theme.title()}")

        if changed:
            self._mark_saved("Theme saved")
            self._emit_settings_changed()

    def _handle_fps_change(self, value: float) -> None:
        fps_limit = int(round(float(value)))
        changed = self._settings_manager.update(fps_limit=fps_limit)

        if self._fps_value_label is not None:
            self._fps_value_label.configure(text=f"Current limit: {fps_limit} FPS")

        if changed:
            self._mark_saved("FPS limit saved")
            self._emit_settings_changed()

    def _save_now(self) -> None:
        self._settings_manager.save()
        self._mark_saved("Settings saved")

    def _emit_settings_changed(self) -> None:
        if self._on_settings_changed is not None:
            self._on_settings_changed(self._settings_manager.snapshot())

    def _mark_saved(self, message: str) -> None:
        if self._status_label is not None:
            self._status_label.configure(text=message)

    def _camera_options(self, current_index: int) -> list[str]:
        options = [
            "0 — Built-in Camera",
            "1 — External Camera",
            "2 — Secondary Camera",
        ]
        current_label = self._camera_label(current_index)
        if current_label not in options:
            options.insert(0, current_label)
        return options

    def _camera_label(self, index: int) -> str:
        labels = {
            0: "0 — Built-in Camera",
            1: "1 — External Camera",
            2: "2 — Secondary Camera",
        }
        return labels.get(index, f"{index} — Custom Camera")

    def _parse_camera_index(self, selection: str) -> int:
        try:
            return int(selection.split(" — ", 1)[0])
        except (ValueError, IndexError):
            return self._settings_manager.camera_index


class _SettingCard(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str, accent: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["card_border"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            justify="left",
            wraplength=420,
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        ctk.CTkFrame(self, fg_color=accent, corner_radius=999, height=2).grid(
            row=2, column=0, sticky="ew", padx=16, pady=(0, 0)
        )