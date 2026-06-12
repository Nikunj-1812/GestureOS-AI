"""
GestureOS AI — Air Drawing Page
===============================
Canvas page for drawing in the air using index-thumb pinch.
"""

from __future__ import annotations

import math
import os
import time
import tkinter as tk
from datetime import datetime
from loguru import logger
import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageTk

from dashboard.components.widgets import Badge, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class AirDrawingPage(BasePage):
    PAGE_KEY = "air_drawing"
    PAGE_TITLE = "Drawing Page"
    PAGE_ICON = "✏"

    def _build(self) -> None:
        # Initial Brush Settings
        self._brush_size = 5
        self._brush_color = COLORS["mauve"]
        self._brush_color_name = "Mauve"
        self._current_state = "Idle"
        
        # Undo/Redo Stacks
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self._current_stroke: dict | None = None
        self._stroke_counter = 0

        # Hand Tracking coordinates smoothing
        self._smooth_x: float | None = None
        self._smooth_y: float | None = None

        # Camera frame caching
        self._last_frame: np.ndarray | None = None
        self._tk_photo: ImageTk.PhotoImage | None = None

        # Grid config
        pad = SIZES["pad_lg"]
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main horizontal container
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)
        main_content.grid_columnconfigure(0, weight=3)  # Canvas column
        main_content.grid_columnconfigure(1, weight=2)  # Controls/Telemetry column
        main_content.grid_rowconfigure(0, weight=1)

        # ── Left Column: Live Preview & Drawing Canvas Area ───────────
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

        # Sized standard 640x360
        self._canvas = tk.Canvas(
            preview_frame,
            width=640,
            height=360,
            bg=COLORS["crust"],
            highlightthickness=0,
            bd=0
        )
        self._canvas.grid(row=0, column=0, padx=pad, pady=pad)

        # Initialize placeholder screen
        self._show_placeholder()

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
            text="Drawing Telemetry",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        # Telemetry fields
        self._lbl_status = self._create_data_label(telemetry_card, "Drawing Status", "Idle", 1)
        self._lbl_cursor_pos = self._create_data_label(telemetry_card, "Pointer Coordinates", "-- , --", 2)
        self._lbl_pinch_distance = self._create_data_label(telemetry_card, "Pinch Distance", "0.0000", 3)
        self._lbl_fps = self._create_data_label(telemetry_card, "Stream FPS", "-- FPS", 4)
        self._lbl_brush_size_telemetry = self._create_data_label(telemetry_card, "Active Brush Size", "5 px", 5)
        self._lbl_brush_color_telemetry = self._create_data_label(telemetry_card, "Active Brush Color", "Mauve", 6)

        # 2. Settings Controls Card
        controls_card = ctk.CTkFrame(
            right_panel,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        controls_card.grid(row=1, column=0, sticky="nsew")
        controls_card.grid_columnconfigure(0, weight=1)

        # Brush Size Header
        ctk.CTkLabel(
            controls_card,
            text="Brush Size",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["overlay1"],
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        # Size slider
        self._size_slider = ctk.CTkSlider(
            controls_card,
            from_=1,
            to=30,
            number_of_steps=29,
            command=self._on_size_slider_changed,
            progress_color=COLORS["blue"],
        )
        self._size_slider.set(self._brush_size)
        self._size_slider.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")

        # Brush Color Header
        ctk.CTkLabel(
            controls_card,
            text="Brush Color",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["overlay1"],
        ).grid(row=2, column=0, padx=16, pady=(4, 4), sticky="w")

        # Palette
        palette_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        palette_frame.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="w")

        color_options = [
            ("Mauve", COLORS["mauve"]),
            ("Blue", COLORS["blue"]),
            ("Green", COLORS["green"]),
            ("Yellow", COLORS["yellow"]),
            ("Peach", COLORS["peach"]),
            ("Red", COLORS["red"]),
            ("White", "#FFFFFF"),
            ("Black", "#000000"),
        ]

        self._color_buttons = {}
        for idx, (name, hex_color) in enumerate(color_options):
            btn = ctk.CTkButton(
                palette_frame,
                text="",
                width=28,
                height=28,
                corner_radius=14,
                fg_color=hex_color,
                hover_color=hex_color,
                border_width=2 if name == "Mauve" else 0,
                border_color=COLORS["text"],
                command=lambda n=name, c=hex_color: self._select_color(n, c)
            )
            row = idx // 4
            col = idx % 4
            btn.grid(row=row, column=col, padx=4, pady=4)
            self._color_buttons[name] = btn

        # Toolbar Buttons Frame
        toolbar_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        toolbar_frame.grid(row=4, column=0, padx=16, pady=(8, 16), sticky="ew")
        toolbar_frame.grid_columnconfigure((0, 1), weight=1)

        self._btn_undo = ctk.CTkButton(
            toolbar_frame,
            text="↶ Undo",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["surface1"],
            hover_color=COLORS["surface2"],
            text_color=COLORS["text"],
            command=self._undo,
        )
        self._btn_undo.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self._btn_redo = ctk.CTkButton(
            toolbar_frame,
            text="↷ Redo",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["surface1"],
            hover_color=COLORS["surface2"],
            text_color=COLORS["text"],
            command=self._redo,
        )
        self._btn_redo.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self._btn_clear = ctk.CTkButton(
            toolbar_frame,
            text="🗑 Clear",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["red"],
            hover_color=COLORS["red"],
            text_color="#FFFFFF",
            command=self._clear_canvas,
        )
        self._btn_clear.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        self._btn_save = ctk.CTkButton(
            toolbar_frame,
            text="💾 Save PNG",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue"],
            text_color="#FFFFFF",
            command=self._save_drawing,
        )
        self._btn_save.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        self._update_button_states()

    def _create_data_label(self, parent, label: str, value: str, row: int) -> ctk.CTkLabel:
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
        ).grid(row=row, column=0, padx=16, pady=6, sticky="w")

        lbl_val = ctk.CTkLabel(
            parent,
            text=value,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
        )
        lbl_val.grid(row=row, column=1, padx=16, pady=6, sticky="e")
        return lbl_val

    def _on_size_slider_changed(self, value: float) -> None:
        self._brush_size = int(value)
        self._lbl_brush_size_telemetry.configure(text=f"{self._brush_size} px")

    def _select_color(self, name: str, hex_color: str) -> None:
        self._brush_color = hex_color
        self._brush_color_name = name
        self._lbl_brush_color_telemetry.configure(text=name)
        for n, btn in self._color_buttons.items():
            if n == name:
                btn.configure(border_width=2, border_color=COLORS["text"])
            else:
                btn.configure(border_width=0)

    def log_event(self, message: str) -> None:
        toplevel = self.winfo_toplevel()
        if hasattr(toplevel, "log_event"):
            toplevel.log_event(message)
        else:
            logger.info(message)

    def _update_button_states(self) -> None:
        if self._undo_stack:
            self._btn_undo.configure(state="normal", fg_color=COLORS["surface1"])
        else:
            self._btn_undo.configure(state="disabled", fg_color=COLORS["surface0"])

        if self._redo_stack:
            self._btn_redo.configure(state="normal", fg_color=COLORS["surface1"])
        else:
            self._btn_redo.configure(state="disabled", fg_color=COLORS["surface0"])

    def _show_placeholder(self) -> None:
        self._canvas.delete("all")
        w = self._canvas.winfo_width() or 640
        h = self._canvas.winfo_height() or 360
        self._canvas.create_rectangle(0, 0, w, h, fill=COLORS["crust"], outline=COLORS["card_border"], tags="placeholder")

        self._canvas.create_text(
            w / 2, h / 2 - 20,
            text="✏",
            font=("Segoe UI", 54, "bold"),
            fill=COLORS["overlay0"],
            tags="placeholder"
        )
        self._canvas.create_text(
            w / 2, h / 2 + 30,
            text="Live Camera Preview Canvas",
            font=("Segoe UI", 16, "bold"),
            fill=COLORS["subtext0"],
            tags="placeholder"
        )
        self._canvas.create_text(
            w / 2, h / 2 + 60,
            text="Start the camera on the Dashboard to begin drawing",
            font=("Segoe UI", 12),
            fill=COLORS["overlay1"],
            tags="placeholder"
        )

    def _redraw_strokes(self) -> None:
        self._canvas.delete("stroke")
        for stroke in self._undo_stack:
            points = stroke["points"]
            tag = stroke["tag"]
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i+1]
                self._canvas.create_line(
                    x1, y1, x2, y2,
                    fill=stroke["color"],
                    width=stroke["size"],
                    capstyle="round",
                    joinstyle="round",
                    tags=("stroke", tag)
                )

    def _undo(self) -> None:
        if self._undo_stack:
            stroke = self._undo_stack.pop()
            self._redo_stack.append(stroke)
            self._canvas.delete(stroke["tag"])
            self._update_button_states()
            self.log_event("Undid last drawing stroke.")

    def _redo(self) -> None:
        if self._redo_stack:
            stroke = self._redo_stack.pop()
            self._undo_stack.append(stroke)
            points = stroke["points"]
            tag = stroke["tag"]
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i+1]
                self._canvas.create_line(
                    x1, y1, x2, y2,
                    fill=stroke["color"],
                    width=stroke["size"],
                    capstyle="round",
                    joinstyle="round",
                    tags=("stroke", tag)
                )
            self._update_button_states()
            self.log_event("Redid popped drawing stroke.")

    def _clear_canvas(self) -> None:
        self._canvas.delete("stroke")
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._current_stroke = None
        self._update_button_states()
        self.log_event("Cleared drawing canvas.")

    def _save_drawing(self) -> None:
        if not self._undo_stack:
            logger.warning("Save drawing clicked, but canvas is empty.")
            self.log_event("Cannot save: canvas is empty.")
            return

        canvas_w = self._canvas.winfo_width() or 640
        canvas_h = self._canvas.winfo_height() or 360

        img = Image.new("RGB", (canvas_w, canvas_h), "white")
        draw = ImageDraw.Draw(img)

        for stroke in self._undo_stack:
            points = stroke["points"]
            color = stroke["color"]
            size = stroke["size"]

            if len(points) > 1:
                draw.line(points, fill=color, width=int(size), joint="round")
            elif len(points) == 1:
                x, y = points[0]
                r = size / 2.0
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

        try:
            os.makedirs("drawings", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"drawings/drawing_{timestamp}.png"
            img.save(filename)
            logger.info(f"Saved drawing to {filename}")
            self.log_event(f"Drawing saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save drawing: {e}")
            self.log_event(f"Failed to save drawing: {e}")

    def _map_landmarks_to_canvas(self, x: float, y: float, img_w: int, img_h: int, canvas_w: int, canvas_h: int) -> tuple[float, float]:
        img_ratio = img_w / img_h
        canvas_ratio = canvas_w / canvas_h

        if img_ratio > canvas_ratio:
            new_w = img_h * canvas_ratio
            left = (img_w - new_w) / 2.0
            x_cropped = (x * img_w - left) / new_w
            y_cropped = y
        else:
            new_h = img_w / canvas_ratio
            top = (img_h - new_h) / 2.0
            x_cropped = x
            y_cropped = (y * img_h - top) / new_h

        canvas_x = x_cropped * canvas_w
        canvas_y = y_cropped * canvas_h
        return canvas_x, canvas_y

    def _draw_cursor(self, x: float, y: float, is_drawing: bool = False) -> None:
        self._clear_cursor()
        r = self._brush_size / 2.0
        outline_color = COLORS["green"] if is_drawing else COLORS["blue"]
        fill_color = self._brush_color if is_drawing else ""

        self._canvas.create_oval(
            x - r - 2, y - r - 2, x + r + 2, y + r + 2,
            outline=outline_color,
            width=2,
            tags="cursor"
        )
        if is_drawing:
            self._canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill=fill_color,
                outline=fill_color,
                tags="cursor"
            )
        self._canvas.create_oval(
            x - 2, y - 2, x + 2, y + 2,
            fill=outline_color,
            outline=outline_color,
            tags="cursor"
        )

    def _clear_cursor(self) -> None:
        self._canvas.delete("cursor")

    def _render_current_frame(self) -> None:
        if self._last_frame is None:
            self._show_placeholder()
            return

        target_w = max(1, self._canvas.winfo_width() or 640)
        target_h = max(1, self._canvas.winfo_height() or 360)

        img_h, img_w = self._last_frame.shape[:2]
        img_ratio = img_w / img_h
        target_ratio = target_w / target_h

        if img_ratio > target_ratio:
            new_w = int(img_h * target_ratio)
            left = (img_w - new_w) // 2
            right = left + new_w
            cropped = self._last_frame[:, left:right]
        else:
            new_h = int(img_w / target_ratio)
            top = (img_h - new_h) // 2
            bottom = top + new_h
            cropped = self._last_frame[top:bottom, :]

        resized = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        fitted = Image.fromarray(rgb)

        self._tk_photo = ImageTk.PhotoImage(image=fitted)
        self._canvas.delete("bg")
        self._canvas.create_image(0, 0, image=self._tk_photo, anchor="nw", tags="bg")
        self._canvas.tag_lower("bg")

    def _start_new_stroke(self, x: float, y: float) -> None:
        self._stroke_counter += 1
        tag = f"stroke_{self._stroke_counter}"
        self._current_stroke = {
            "points": [(x, y)],
            "color": self._brush_color,
            "size": self._brush_size,
            "tag": tag
        }
        self._redo_stack.clear()

    def _continue_stroke(self, x: float, y: float) -> None:
        if self._current_stroke is None:
            self._start_new_stroke(x, y)
            return

        points = self._current_stroke["points"]
        last_x, last_y = points[-1]

        if abs(x - last_x) < 1.0 and abs(y - last_y) < 1.0:
            return

        points.append((x, y))
        self._canvas.create_line(
            last_x, last_y, x, y,
            fill=self._current_stroke["color"],
            width=self._current_stroke["size"],
            capstyle="round",
            joinstyle="round",
            tags=("stroke", self._current_stroke["tag"])
        )

    def _end_stroke(self) -> None:
        if self._current_stroke is not None:
            if len(self._current_stroke["points"]) > 0:
                self._undo_stack.append(self._current_stroke)
            self._current_stroke = None
            self._update_button_states()

    def set_camera_frame(self, frame: np.ndarray | None, fps: float = 0.0, detected_hands: list | None = None) -> None:
        """Receives live camera stream frames and hand landmarks."""
        self._last_frame = frame.copy() if frame is not None else None
        self._lbl_fps.configure(text=f"{fps:.1f} FPS" if fps > 0 else "-- FPS")
        self._render_current_frame()

        detected_state = "Idle"
        pinch_dist = 0.0

        if detected_hands and len(detected_hands) > 0:
            primary_hand = detected_hands[0]
            if len(primary_hand.landmarks) >= 21:
                lm = primary_hand.landmarks
                ix, iy, _ = lm[8]
                
                canvas_w = self._canvas.winfo_width() or 640
                canvas_h = self._canvas.winfo_height() or 360
                
                if frame is not None:
                    img_h, img_w = frame.shape[:2]
                else:
                    img_h, img_w = 360, 640
                
                cx, cy = self._map_landmarks_to_canvas(ix, iy, img_w, img_h, canvas_w, canvas_h)
                
                smoothing = 0.25
                if self._smooth_x is None or self._smooth_y is None:
                    self._smooth_x = cx
                    self._smooth_y = cy
                else:
                    self._smooth_x += (cx - self._smooth_x) * smoothing
                    self._smooth_y += (cy - self._smooth_y) * smoothing
                
                ix_3d, iy_3d, iz_3d = lm[8]
                tx_3d, ty_3d, tz_3d = lm[4]
                pinch_dist = math.sqrt((ix_3d - tx_3d)**2 + (iy_3d - ty_3d)**2 + (iz_3d - tz_3d)**2)
                
                click_threshold = 0.05
                if pinch_dist <= click_threshold:
                    detected_state = "Drawing"
                    if self._current_state != "Drawing":
                        self._start_new_stroke(self._smooth_x, self._smooth_y)
                    else:
                        self._continue_stroke(self._smooth_x, self._smooth_y)
                else:
                    detected_state = "Hovering"
                    if self._current_state == "Drawing":
                        self._end_stroke()
                
                self._draw_cursor(self._smooth_x, self._smooth_y, is_drawing=(detected_state == "Drawing"))
                self._lbl_cursor_pos.configure(text=f"X: {int(self._smooth_x)}, Y: {int(self._smooth_y)}")
            else:
                self._smooth_x = None
                self._smooth_y = None
                self._clear_cursor()
                if self._current_state == "Drawing":
                    self._end_stroke()
        else:
            self._smooth_x = None
            self._smooth_y = None
            self._clear_cursor()
            if self._current_state == "Drawing":
                self._end_stroke()

        self._current_state = detected_state
        self._lbl_status.configure(text=detected_state)
        
        if detected_state == "Drawing":
            self._lbl_status.configure(text_color=COLORS["green"])
        elif detected_state == "Hovering":
            self._lbl_status.configure(text_color=COLORS["yellow"])
        else:
            self._lbl_status.configure(text_color=COLORS["overlay1"])
            self._lbl_cursor_pos.configure(text="-- , --")

        self._lbl_pinch_distance.configure(text=f"{pinch_dist:.4f}")

    def on_enter(self) -> None:
        self._redraw_strokes()

    def on_leave(self) -> None:
        self._last_frame = None
        self._smooth_x = None
        self._smooth_y = None
        if self._current_state == "Drawing":
            self._end_stroke()
        self._show_placeholder()