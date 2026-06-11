"""
GestureOS AI — Virtual Mouse Dashboard Page
===========================================
Highly responsive UI page showing live camera preview, virtual mouse
tracking coordinates, status telemetries, and slider controls.
"""

from __future__ import annotations

import customtkinter as ctk
from typing import TYPE_CHECKING

from dashboard.components.widgets import Badge, CameraFeed, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES

if TYPE_CHECKING:
    from config.settings_manager import SettingsManager


class VirtualMousePage(BasePage):
    PAGE_KEY = "virtual_mouse"
    PAGE_TITLE = "Virtual Mouse"
    PAGE_ICON = "⊹"

    def __init__(
        self,
        master,
        on_navigate: callable | None = None,
        settings_manager: SettingsManager | None = None,
        on_settings_changed: callable | None = None,
        **kwargs,
    ) -> None:
        self._on_navigate = on_navigate
        self._settings_manager = settings_manager
        self._on_settings_changed = on_settings_changed
        super().__init__(master, **kwargs)

    def _build(self) -> None:
        pad = SIZES["pad_lg"]
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Hero Header Section ───────────────────────────────────────
        hero = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        hero.grid(row=0, column=0, columnspan=2, sticky="ew", padx=pad, pady=(pad, 0))
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero,
            text="Virtual Mouse Controls",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="Control your system cursor in real-time using your index finger. Calibrate tracking properties below.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        self._status_badge = Badge(hero, text="Active", color=COLORS["green"])
        self._status_badge.grid(row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e")

        # ── Two-Column Main Content Layout ────────────────────────────
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=1, column=0, sticky="nsew", padx=pad, pady=(pad, 0))
        main_content.grid_columnconfigure(0, weight=3)  # Camera stream
        main_content.grid_columnconfigure(1, weight=2)  # Controls/Telemetry panel
        main_content.grid_rowconfigure(0, weight=1)

        # ── Left Column: Live Preview Area ────────────────────────────
        preview_frame = ctk.CTkFrame(
            main_content,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_md"]))
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)

        self._camera_feed = CameraFeed(preview_frame, width=640, height=360, show_overlays=True)
        self._camera_feed.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)

        # ── Right Column: Telemetry & Controls Panel ──────────────────
        right_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure((0, 1), weight=1)

        # 1. Telemetry Dashboard Card
        telemetry_card = ctk.CTkFrame(
            right_panel,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        telemetry_card.grid(row=0, column=0, sticky="nsew", pady=(0, SIZES["pad_md"]))
        telemetry_card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            telemetry_card,
            text="Telemetry Dashboard",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        # Telemetry fields
        self._lbl_cursor_pos = self._create_data_label(telemetry_card, "Cursor Coordinates", "-- , --", 1)
        self._lbl_tracking_state = self._create_data_label(telemetry_card, "Tracking State", "No Hand", 2)
        self._lbl_fps = self._create_data_label(telemetry_card, "Stream FPS", "-- FPS", 3)

        # Click telemetry fields
        self._lbl_current_action = self._create_data_label(telemetry_card, "Current Action", "None", 4)
        self._lbl_pinch_distance = self._create_data_label(telemetry_card, "Pinch Distance", "0.0000", 5)
        self._lbl_click_status = self._create_data_label(telemetry_card, "Click Status", "OPEN", 6)
        self._lbl_click_counter = self._create_data_label(telemetry_card, "Click Counter", "0", 7)

        # Volume telemetry fields (Phase 3.4)
        self._lbl_volume_mode = self._create_data_label(telemetry_card, "Volume Mode", "INACTIVE", 8)
        self._lbl_volume_level = self._create_data_label(telemetry_card, "Volume Level", "0%", 9)
        self._lbl_volume_distance = self._create_data_label(telemetry_card, "Volume Distance", "-- px", 10)

        # Brightness & Active Mode telemetry fields (Phase 3.5)
        self._lbl_active_mode = self._create_data_label(telemetry_card, "Active Mode", "CURSOR", 11)
        self._lbl_brightness_mode = self._create_data_label(telemetry_card, "Brightness Mode", "INACTIVE", 12)
        self._lbl_brightness_level = self._create_data_label(telemetry_card, "Brightness Level", "0%", 13)
        self._lbl_brightness_distance = self._create_data_label(telemetry_card, "Brightness Distance", "-- px", 14)

        # 2. Settings Controls Card
        settings_card = ctk.CTkFrame(
            right_panel,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        settings_card.grid(row=1, column=0, sticky="nsew")
        settings_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            settings_card,
            text="Tracking Settings",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        # Toggle Switch
        state = self._settings_manager.state if self._settings_manager else None
        enabled_val = state.virtual_mouse_enabled if state else False

        self._toggle_switch = ctk.CTkSwitch(
            settings_card,
            text="Enable Virtual Mouse",
            command=self._on_toggle_toggled,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            progress_color=COLORS["blue"],
        )
        self._toggle_switch.grid(row=1, column=0, padx=16, pady=8, sticky="w")
        if enabled_val:
            self._toggle_switch.select()
        else:
            self._toggle_switch.deselect()

        # Sliders
        sens_val = state.virtual_mouse_sensitivity if state else 1.5
        dz_val = state.virtual_mouse_dead_zone if state else 0.15
        smooth_val = state.virtual_mouse_smoothing if state else 0.20

        # Sensitivity Slider
        self._lbl_sens = ctk.CTkLabel(settings_card, text=f"Sensitivity: {sens_val:.2f}x", font=ctk.CTkFont(*FONTS["small"]), text_color=COLORS["overlay1"])
        self._lbl_sens.grid(row=2, column=0, padx=16, pady=(8, 2), sticky="w")
        self._sens_slider = ctk.CTkSlider(settings_card, from_=0.5, to=3.0, number_of_steps=25, command=self._on_sens_changed)
        self._sens_slider.set(sens_val)
        self._sens_slider.grid(row=3, column=0, padx=16, pady=(0, 8), sticky="ew")

        # Dead Zone Slider
        self._lbl_dz = ctk.CTkLabel(settings_card, text=f"Dead Zone Padding: {int(dz_val * 100)}%", font=ctk.CTkFont(*FONTS["small"]), text_color=COLORS["overlay1"])
        self._lbl_dz.grid(row=4, column=0, padx=16, pady=(8, 2), sticky="w")
        self._dz_slider = ctk.CTkSlider(settings_card, from_=0.05, to=0.30, number_of_steps=25, command=self._on_dz_changed)
        self._dz_slider.set(dz_val)
        self._dz_slider.grid(row=5, column=0, padx=16, pady=(0, 8), sticky="ew")

        # Smoothing Slider
        self._lbl_smooth = ctk.CTkLabel(settings_card, text=f"Smoothing (Response): {smooth_val:.2f}", font=ctk.CTkFont(*FONTS["small"]), text_color=COLORS["overlay1"])
        self._lbl_smooth.grid(row=6, column=0, padx=16, pady=(8, 2), sticky="w")
        self._smooth_slider = ctk.CTkSlider(settings_card, from_=0.05, to=0.50, number_of_steps=18, command=self._on_smooth_changed)
        self._smooth_slider.set(smooth_val)
        self._smooth_slider.grid(row=7, column=0, padx=16, pady=(0, 8), sticky="ew")

        # Click Threshold Slider
        click_thresh_val = getattr(state, 'virtual_mouse_click_threshold', 0.05) if state else 0.05
        self._lbl_click_thresh = ctk.CTkLabel(settings_card, text=f"Click Threshold: {click_thresh_val:.3f}", font=ctk.CTkFont(*FONTS["small"]), text_color=COLORS["overlay1"])
        self._lbl_click_thresh.grid(row=8, column=0, padx=16, pady=(8, 2), sticky="w")
        self._click_thresh_slider = ctk.CTkSlider(settings_card, from_=0.01, to=0.15, number_of_steps=28, command=self._on_click_thresh_changed)
        self._click_thresh_slider.set(click_thresh_val)
        self._click_thresh_slider.grid(row=9, column=0, padx=16, pady=(0, 16), sticky="ew")

        self._update_badge(enabled_val)

        # ── Bottom Row: Navigation ────────────────────────────────────
        nav_row = ctk.CTkFrame(self, fg_color="transparent")
        nav_row.grid(row=2, column=0, sticky="ew", padx=pad, pady=pad)
        nav_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            nav_row,
            text="← Back to Dashboard",
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
            text="System Settings",
            command=lambda: self._navigate("settings"),
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=44,
            corner_radius=SIZES["btn_radius"],
        ).grid(row=0, column=1, sticky="ew")

    def _create_data_label(self, parent, label_text: str, default_val: str, row_idx: int) -> ctk.CTkLabel:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=16, pady=4)
        container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            container,
            text=label_text,
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        val_label = ctk.CTkLabel(
            container,
            text=default_val,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="e",
        )
        val_label.grid(row=0, column=1, sticky="e")
        return val_label

    def _on_toggle_toggled(self) -> None:
        val = bool(self._toggle_switch.get())
        self._update_badge(val)
        self._update_setting("virtual_mouse_enabled", val)

    def _on_sens_changed(self, val: float) -> None:
        self._lbl_sens.configure(text=f"Sensitivity: {val:.2f}x")
        self._update_setting("virtual_mouse_sensitivity", val)

    def _on_dz_changed(self, val: float) -> None:
        self._lbl_dz.configure(text=f"Dead Zone Padding: {int(val * 100)}%")
        self._update_setting("virtual_mouse_dead_zone", val)

    def _on_smooth_changed(self, val: float) -> None:
        self._lbl_smooth.configure(text=f"Smoothing (Response): {val:.2f}")
        self._update_setting("virtual_mouse_smoothing", val)

    def _on_click_thresh_changed(self, val: float) -> None:
        self._lbl_click_thresh.configure(text=f"Click Threshold: {val:.3f}")
        self._update_setting("virtual_mouse_click_threshold", val)

    def _update_setting(self, key: str, val: bool | float) -> None:
        if self._settings_manager:
            changed = self._settings_manager.update(**{key: val})
            if changed:
                self._settings_manager.save()
                if self._on_settings_changed:
                    self._on_settings_changed(self._settings_manager.snapshot())

    def _update_badge(self, enabled: bool) -> None:
        if enabled:
            self._status_badge.configure(text="Active")
            self._status_badge._label.configure(text_color=COLORS["green"])
        else:
            self._status_badge.configure(text="Inactive")
            self._status_badge._label.configure(text_color=COLORS["overlay1"])

    def set_camera_frame(
        self,
        frame,
        fps=0.0,
        gesture="unknown",
        confidence=0.0,
        hands_detected=0,
        cursor_x=0,
        cursor_y=0,
        tracking_state="No Hand",
        click_status="OPEN",
        click_counter=0,
        pinch_distance=0.0,
        current_action="None",
        volume_mode=False,
        volume_level=0,
        volume_distance=0.0,
        active_mode="CURSOR",
        brightness_mode=False,
        brightness_level=0,
        brightness_distance=0.0,
    ) -> None:
        """Receives live camera frame and telemetry from the central window loop."""
        self._camera_feed.set_frame(
            frame, fps=fps, gesture=gesture, confidence=confidence, hands_detected=hands_detected
        )

        # Update dynamic telemetry labels
        self._lbl_fps.configure(text=f"{fps:.1f} FPS" if fps > 0 else "-- FPS")
        self._lbl_cursor_pos.configure(text=f"X: {cursor_x} , Y: {cursor_y}" if tracking_state == "Tracking" else "-- , --")

        self._lbl_tracking_state.configure(text=tracking_state)
        if tracking_state == "Tracking":
            self._lbl_tracking_state.configure(text_color=COLORS["green"])
        elif tracking_state == "Disabled":
            self._lbl_tracking_state.configure(text_color=COLORS["overlay1"])
        else:
            self._lbl_tracking_state.configure(text_color=COLORS["red"])

        # Update click telemetry labels
        self._lbl_current_action.configure(text=current_action)
        if current_action == "Left Click":
            self._lbl_current_action.configure(text_color=COLORS["green"])
        else:
            self._lbl_current_action.configure(text_color=COLORS["text"])

        self._lbl_pinch_distance.configure(text=f"{pinch_distance:.4f}")

        self._lbl_click_status.configure(text=click_status)
        if click_status in ("LEFT_CLICK", "PINCH"):
            self._lbl_click_status.configure(text_color=COLORS["green"])
        elif click_status == "RELEASE":
            self._lbl_click_status.configure(text_color=COLORS["blue"])
        else:
            self._lbl_click_status.configure(text_color=COLORS["text"])

        self._lbl_click_counter.configure(text=str(click_counter))

        # Update volume telemetry labels
        self._lbl_volume_mode.configure(text="ACTIVE" if volume_mode else "INACTIVE")
        if volume_mode:
            self._lbl_volume_mode.configure(text_color=COLORS["mauve"])
            self._lbl_current_action.configure(text_color=COLORS["mauve"])
        else:
            self._lbl_volume_mode.configure(text_color=COLORS["overlay1"])

        self._lbl_volume_level.configure(text=f"{volume_level}%")
        self._lbl_volume_distance.configure(text=f"{volume_distance:.1f} px" if volume_mode else "-- px")

        # Update active mode & brightness telemetry labels
        self._lbl_active_mode.configure(text=active_mode)
        if active_mode == "CURSOR":
            self._lbl_active_mode.configure(text_color=COLORS["blue"])
        elif active_mode == "CLICK":
            self._lbl_active_mode.configure(text_color=COLORS["green"])
        elif active_mode == "SCROLL":
            self._lbl_active_mode.configure(text_color=COLORS["teal"])
        elif active_mode == "VOLUME":
            self._lbl_active_mode.configure(text_color=COLORS["mauve"])
        elif active_mode == "BRIGHTNESS":
            self._lbl_active_mode.configure(text_color=COLORS["sky"])

        self._lbl_brightness_mode.configure(text="ACTIVE" if brightness_mode else "INACTIVE")
        if brightness_mode:
            self._lbl_brightness_mode.configure(text_color=COLORS["sky"])
        else:
            self._lbl_brightness_mode.configure(text_color=COLORS["overlay1"])

        self._lbl_brightness_level.configure(text=f"{brightness_level}%")
        self._lbl_brightness_distance.configure(text=f"{brightness_distance:.1f} px" if brightness_mode else "-- px")

    def clear_camera_frame(self) -> None:
        self._camera_feed.clear()
        self._lbl_fps.configure(text="-- FPS")
        self._lbl_cursor_pos.configure(text="-- , --")
        self._lbl_tracking_state.configure(text="Disconnected", text_color=COLORS["red"])
        self._lbl_current_action.configure(text="None", text_color=COLORS["text"])
        self._lbl_pinch_distance.configure(text="0.0000")
        self._lbl_click_status.configure(text="OPEN", text_color=COLORS["text"])
        self._lbl_click_counter.configure(text="0")
        self._lbl_volume_mode.configure(text="INACTIVE", text_color=COLORS["overlay1"])
        self._lbl_volume_level.configure(text="0%")
        self._lbl_volume_distance.configure(text="-- px")
        self._lbl_active_mode.configure(text="CURSOR", text_color=COLORS["blue"])
        self._lbl_brightness_mode.configure(text="INACTIVE", text_color=COLORS["overlay1"])
        self._lbl_brightness_level.configure(text="0%")
        self._lbl_brightness_distance.configure(text="-- px")

    def _navigate(self, key: str) -> None:
        if self._on_navigate is not None:
            self._on_navigate(key)