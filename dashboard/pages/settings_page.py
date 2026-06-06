"""
GestureOS AI — Settings Page
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import SectionTitle, ToggleRow, InfoRow, Divider
from dashboard.theme import COLORS, FONTS, SIZES


class SettingsPage(BasePage):

    PAGE_KEY   = "settings"
    PAGE_TITLE = "Settings"
    PAGE_ICON  = "≡"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]

        SectionTitle(self, "Settings", "Configure GestureOS AI preferences").grid(
            row=0, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        # ── Camera ────────────────────────────────────────────────
        self._section("Camera", row=1)

        cam = self._card(row=2)
        cam.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(cam, text="Camera Index",
                     font=ctk.CTkFont(*FONTS["label"]),
                     text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        cam_row = ctk.CTkFrame(cam, fg_color="transparent")
        cam_row.grid(row=1, column=0, sticky="ew", padx=pad, pady=(0, SIZES["pad_sm"]))
        cam_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(cam_row, text="Index:",
                     font=ctk.CTkFont(*FONTS["body"]),
                     text_color=COLORS["text"], anchor="w", width=80,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkOptionMenu(
            cam_row, values=["0 — Built-in", "1 — External", "2 — Other"],
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["surface1"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["btn_hover"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["surface0"],
            dropdown_text_color=COLORS["text"],
            width=240, height=36,
        ).grid(row=0, column=1, sticky="w", padx=(0, SIZES["pad_md"]))

        for label, desc in [
            ("Flip Horizontal",   "Mirror camera feed left-right"),
            ("HD Resolution",     "Use 1280×720 instead of 640×480"),
        ]:
            ToggleRow(cam, label=label, description=desc, default=True).grid(
                row=cam.grid_size()[1], column=0, sticky="ew",
                padx=pad, pady=(0, SIZES["pad_sm"])
            )

        # ── Detection ─────────────────────────────────────────────
        self._section("Detection & Model", row=3)

        det = self._card(row=4)
        det.grid_columnconfigure(0, weight=1)

        self._slider_row(det, "Detection Confidence", 0, 100, 75, "%")
        self._slider_row(det, "Tracking Confidence",  0, 100, 65, "%")
        self._slider_row(det, "Smoothing Frames",     1, 30,  15, "")

        for label, desc in [
            ("Use GPU Acceleration",  "Enable CUDA if available"),
            ("Show Landmark Dots",    "Render hand skeleton overlay"),
            ("Show FPS Counter",      "Display FPS in top-left corner"),
        ]:
            ToggleRow(det, label=label, description=desc, default=(label == "Show Landmark Dots")).grid(
                row=det.grid_size()[1], column=0, sticky="ew",
                padx=pad, pady=(0, SIZES["pad_sm"])
            )

        # ── UI ────────────────────────────────────────────────────
        self._section("Interface", row=5)

        ui = self._card(row=6)
        ui.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ui, text="Theme",
                     font=ctk.CTkFont(*FONTS["label"]),
                     text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkSegmentedButton(
            ui, values=["Dark", "Light", "System"],
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["surface1"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["btn_hover"],
            unselected_color=COLORS["surface1"],
            unselected_hover_color=COLORS["nav_hover"],
            text_color=COLORS["text"],
        ).grid(row=1, column=0, padx=pad, pady=(0, SIZES["pad_sm"]), sticky="w")

        ctk.CTkLabel(ui, text="Overlay Opacity",
                     font=ctk.CTkFont(*FONTS["label"]),
                     text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=2, column=0, padx=pad, pady=(SIZES["pad_sm"], 4), sticky="w")

        op_row = ctk.CTkFrame(ui, fg_color="transparent")
        op_row.grid(row=3, column=0, sticky="ew", padx=pad, pady=(0, pad))
        op_row.grid_columnconfigure(0, weight=1)

        ctk.CTkSlider(
            op_row, from_=0, to=100, number_of_steps=20,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
        ).grid(row=0, column=0, sticky="ew")

        # ── Logging ───────────────────────────────────────────────
        self._section("Logging", row=7)

        log = self._card(row=8)
        log.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log, text="Log Level",
                     font=ctk.CTkFont(*FONTS["label"]),
                     text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkOptionMenu(
            log, values=["DEBUG", "INFO", "WARNING", "ERROR"],
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["surface1"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["btn_hover"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["surface0"],
            dropdown_text_color=COLORS["text"],
            width=180, height=36,
        ).grid(row=1, column=0, padx=pad, pady=(0, SIZES["pad_sm"]), sticky="w")

        for label, desc in [
            ("Save Logs to File",  "Write session logs to /logs directory"),
            ("Log Gestures",       "Record each detected gesture event"),
        ]:
            ToggleRow(log, label=label, description=desc, default=True).grid(
                row=log.grid_size()[1], column=0, sticky="ew",
                padx=pad, pady=(0, SIZES["pad_sm"])
            )

        # ── About ─────────────────────────────────────────────────
        self._section("About", row=9)

        about = self._card(row=10)
        about.grid_columnconfigure(0, weight=1)

        for key, val in [
            ("Application",  "GestureOS AI"),
            ("Version",      "v1.0.0"),
            ("Python",       "3.11+"),
            ("MediaPipe",    "0.10.x"),
            ("CustomTkinter","5.2.2"),
            ("Author",       "GestureOS AI Team"),
        ]:
            InfoRow(about, key=key, value=val).grid(
                row=about.grid_size()[1], column=0, sticky="ew",
                padx=pad, pady=(SIZES["pad_sm"], 0)
            )

        # ── Save / Reset buttons ──────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=11, column=0, sticky="ew", padx=pad, pady=pad)

        ctk.CTkButton(
            btn_row, text="↺  Reset to Defaults",
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["surface1"],
            hover_color=COLORS["status_err"],
            text_color=COLORS["text"],
            height=40, width=180,
        ).grid(row=0, column=0, padx=(0, SIZES["pad_md"]))

        ctk.CTkButton(
            btn_row, text="✓  Save Settings",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=40, width=180,
        ).grid(row=0, column=1)

    # ── Helpers ───────────────────────────────────────────────────

    def _section(self, title: str, row: int) -> None:
        SectionTitle(self, title).grid(
            row=row, column=0, sticky="ew",
            padx=SIZES["pad_lg"], pady=(SIZES["pad_lg"], SIZES["pad_sm"])
        )

    def _card(self, row: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=SIZES["card_radius"],
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        card.grid(row=row, column=0, sticky="ew", padx=SIZES["pad_lg"])
        card.grid_columnconfigure(0, weight=1)
        return card

    def _slider_row(self, parent, label: str, lo: int, hi: int, default: int, unit: str) -> None:
        pad = SIZES["pad_lg"]
        row = parent.grid_size()[1]

        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=pad, pady=(SIZES["pad_sm"], 0))
        f.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f, text=label,
                     font=ctk.CTkFont(*FONTS["body"]),
                     text_color=COLORS["text"], anchor="w", width=200,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkSlider(
            f, from_=lo, to=hi,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
        ).grid(row=0, column=1, sticky="ew", padx=(SIZES["pad_md"], SIZES["pad_sm"]))

        ctk.CTkLabel(f, text=f"{default}{unit}",
                     font=ctk.CTkFont(*FONTS["small"]),
                     text_color=COLORS["overlay1"], width=40, anchor="e",
        ).grid(row=0, column=2, sticky="e")
