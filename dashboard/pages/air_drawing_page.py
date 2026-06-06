"""
GestureOS AI — Air Drawing Page
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.pages.base_page import BasePage
from dashboard.components.widgets import SectionTitle, CameraFeed, ToggleRow
from dashboard.theme import COLORS, FONTS, SIZES


class AirDrawingPage(BasePage):

    PAGE_KEY   = "air_drawing"
    PAGE_TITLE = "Air Drawing"
    PAGE_ICON  = "✏"

    def _build(self) -> None:
        pad = SIZES["pad_lg"]

        SectionTitle(self, "Air Drawing", "Draw in the air with your index finger").grid(
            row=0, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        # Main area: camera (left) + canvas preview (right)
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=pad)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        CameraFeed(content, width=480, height=320).grid(
            row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_md"])
        )

        # Canvas placeholder
        canvas_frame = ctk.CTkFrame(
            content,
            fg_color=COLORS["crust"],
            corner_radius=SIZES["card_radius"],
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        canvas_frame.grid(row=0, column=1, sticky="nsew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            canvas_frame,
            text="✏\n\nDrawing Canvas",
            font=ctk.CTkFont("Segoe UI", 20),
            text_color=COLORS["overlay0"],
            justify="center",
        ).grid(row=0, column=0)

        # ── Toolbar ───────────────────────────────────────────────
        SectionTitle(self, "Drawing Tools").grid(
            row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        toolbar = ctk.CTkFrame(self, fg_color=COLORS["surface0"], corner_radius=SIZES["card_radius"])
        toolbar.grid(row=3, column=0, sticky="ew", padx=pad)
        toolbar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Colour swatches
        colours_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        colours_frame.grid(row=0, column=0, padx=SIZES["pad_md"], pady=SIZES["pad_md"], sticky="w")

        ctk.CTkLabel(
            colours_frame, text="Colour",
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"],
        ).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 4))

        for i, clr in enumerate([
            COLORS["red"], COLORS["green"], COLORS["blue"],
            COLORS["yellow"], COLORS["mauve"], COLORS["text"],
        ]):
            ctk.CTkButton(
                colours_frame,
                text="", width=24, height=24,
                fg_color=clr,
                hover_color=clr,
                corner_radius=12,
            ).grid(row=1, column=i, padx=2)

        # Brush size
        brush_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        brush_frame.grid(row=0, column=1, padx=SIZES["pad_md"], pady=SIZES["pad_md"], sticky="ew")
        brush_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            brush_frame, text="Brush Size",
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ctk.CTkSlider(
            brush_frame, from_=1, to=20,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
        ).grid(row=1, column=0, columnspan=2, sticky="ew")

        # Actions
        actions = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions.grid(row=0, column=3, padx=SIZES["pad_md"], pady=SIZES["pad_md"], sticky="e")

        for text, color in [
            ("⌫ Undo",    COLORS["surface1"]),
            ("⊞ Save",    COLORS["accent"]),
            ("✕ Clear",   COLORS["surface1"]),
        ]:
            ctk.CTkButton(
                actions, text=text,
                font=ctk.CTkFont(*FONTS["small"]),
                fg_color=color,
                hover_color=COLORS["btn_hover"],
                text_color=COLORS["text"] if color == COLORS["surface1"] else COLORS["base"],
                height=32, width=90,
            ).grid(row=0, column=actions.grid_size()[1], padx=(0, SIZES["pad_sm"]))

        # ── Settings ──────────────────────────────────────────────
        SectionTitle(self, "Settings").grid(
            row=4, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )
        sf = ctk.CTkFrame(self, fg_color=COLORS["surface0"], corner_radius=SIZES["card_radius"])
        sf.grid(row=5, column=0, sticky="ew", padx=pad)
        sf.grid_columnconfigure(0, weight=1)

        for label, desc in [
            ("Enable Air Drawing",     "Activate finger-tracking drawing mode"),
            ("Show Trail Effect",      "Display fading ink trail"),
            ("Mirror Canvas",          "Mirror drawing left-right"),
        ]:
            ToggleRow(sf, label=label, description=desc).grid(
                row=sf.grid_size()[1], column=0, sticky="ew",
                padx=SIZES["pad_md"], pady=(SIZES["pad_sm"], 0)
            )

        ctk.CTkButton(
            self, text="▶  Start Air Drawing",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=44, corner_radius=SIZES["btn_radius"],
        ).grid(row=6, column=0, sticky="ew", padx=pad, pady=pad)
