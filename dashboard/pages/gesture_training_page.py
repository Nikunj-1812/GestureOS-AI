"""
GestureOS AI — Gesture Training Page
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import SectionTitle, CameraFeed, EmptyState, StatCard
from dashboard.theme import COLORS, FONTS, SIZES


class GestureTrainingPage(BasePage):

    PAGE_KEY   = "gesture_training"
    PAGE_TITLE = "Gesture Training"
    PAGE_ICON  = "◈"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]

        SectionTitle(
            self, "Gesture Training",
            "Record and train custom gesture classifiers"
        ).grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"]))

        # ── Stats row ─────────────────────────────────────────────
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", padx=pad)
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1, uniform="train_stat")

        for col, (icon, val, label, color) in enumerate([
            ("◈", "0",    "Gestures Trained",  COLORS["blue"]),
            ("▦", "0",    "Total Samples",      COLORS["green"]),
            ("▶", "--%",  "Model Accuracy",     COLORS["mauve"]),
            ("⊞", "--",   "Last Trained",        COLORS["peach"]),
        ]):
            StatCard(stats, icon=icon, value=val, label=label, accent=color).grid(
                row=0, column=col,
                padx=(0, SIZES["pad_sm"]) if col < 3 else 0,
                sticky="nsew",
            )

        # ── Training workspace ────────────────────────────────────
        SectionTitle(self, "Training Workspace").grid(
            row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=3, column=0, sticky="ew", padx=pad)
        workspace.grid_columnconfigure(0, weight=2)
        workspace.grid_columnconfigure(1, weight=1)

        # Left: camera feed
        CameraFeed(workspace, width=520, height=340).grid(
            row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_md"])
        )

        # Right: gesture list + recording controls
        right = ctk.CTkFrame(workspace, fg_color=COLORS["surface0"], corner_radius=SIZES["card_radius"])
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right, text="Gesture Name",
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=0, column=0, padx=SIZES["pad_md"], pady=(SIZES["pad_md"], 4), sticky="w")

        ctk.CTkEntry(
            right,
            placeholder_text="e.g.  thumbs_up",
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["input_bg"],
            border_color=COLORS["card_border"],
            text_color=COLORS["text"],
            height=36,
        ).grid(row=1, column=0, padx=SIZES["pad_md"], sticky="ew")

        ctk.CTkLabel(
            right, text="Samples to collect",
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=2, column=0, padx=SIZES["pad_md"], pady=(SIZES["pad_sm"], 4), sticky="w")

        ctk.CTkSlider(
            right, from_=50, to=500, number_of_steps=9,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
        ).grid(row=3, column=0, padx=SIZES["pad_md"], sticky="ew")

        ctk.CTkLabel(right, text="200 samples",
                     font=ctk.CTkFont(*FONTS["small"]),
                     text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=4, column=0, padx=SIZES["pad_md"], sticky="w")

        # Record + Train buttons
        btns = ctk.CTkFrame(right, fg_color="transparent")
        btns.grid(row=5, column=0, padx=SIZES["pad_md"], pady=SIZES["pad_md"], sticky="ew")
        btns.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btns, text="⏺  Record",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["red"],
            hover_color=COLORS["maroon"],
            text_color=COLORS["base"],
            height=38,
        ).grid(row=0, column=0, padx=(0, SIZES["pad_sm"]), sticky="ew")

        ctk.CTkButton(
            btns, text="◈  Train",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["accent"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=38,
        ).grid(row=0, column=1, sticky="ew")

        # Progress bar
        ctk.CTkLabel(right, text="Training Progress",
                     font=ctk.CTkFont(*FONTS["label"]),
                     text_color=COLORS["overlay1"], anchor="w",
        ).grid(row=6, column=0, padx=SIZES["pad_md"], pady=(SIZES["pad_sm"], 4), sticky="w")

        ctk.CTkProgressBar(
            right,
            progress_color=COLORS["accent"],
            fg_color=COLORS["surface1"],
            height=8, corner_radius=4,
        ).grid(row=7, column=0, padx=SIZES["pad_md"], pady=(0, SIZES["pad_md"]), sticky="ew")

        # ── Gesture library ───────────────────────────────────────
        SectionTitle(self, "Gesture Library", "All trained gestures").grid(
            row=4, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        EmptyState(
            self,
            icon="◈",
            title="No gestures trained yet",
            subtitle="Record samples and click Train to add a gesture to the library.",
        ).grid(row=5, column=0, sticky="nsew", padx=pad, pady=(0, pad))
