"""
GestureOS AI — Reusable Widget Library
========================================
Small composable widgets used across multiple pages:

  StatCard       — metric card (icon + value + label)
  SectionTitle   — page section heading with optional subtitle
  Divider        — horizontal separator line
  Badge          — coloured pill label
  ToggleRow      — label + switch in one row
  InfoRow        — label + value in one row (for settings/info panels)
  CameraFeed     — placeholder frame for live camera preview
  EmptyState     — centred illustration + message when page has no data
"""

from __future__ import annotations

import cv2
import customtkinter as ctk
import numpy as np
from PIL import Image, ImageOps

from dashboard.theme import COLORS, FONTS, SIZES


# ──────────────────────────────────────────────────────────────────
# StatCard
# ──────────────────────────────────────────────────────────────────

class StatCard(ctk.CTkFrame):
    """
    Metric card showing:
      ┌──────────────────┐
      │  icon            │
      │  value  (large)  │
      │  label  (small)  │
      └──────────────────┘

    Args:
        icon  : Unicode symbol or emoji.
        value : String value to display large (e.g. "98.2%").
        label : Description below the value (e.g. "Detection Accuracy").
        accent: Accent colour for the icon and value.
    """

    def __init__(
        self,
        master,
        icon: str = "◈",
        value: str = "--",
        label: str = "Metric",
        accent: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLORS["card_bg"],
            corner_radius=SIZES["card_radius"],
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
            **kwargs,
        )
        accent = accent or COLORS["accent"]
        self.grid_columnconfigure(0, weight=1)

        # Icon
        ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont("Segoe UI", SIZES["icon_lg"]),
            text_color=accent,
        ).grid(row=0, column=0, padx=SIZES["pad_md"], pady=(SIZES["pad_md"], 4), sticky="w")

        # Value
        self._value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(*FONTS["stat_value"]),
            text_color=accent,
            anchor="w",
        )
        self._value_label.grid(row=1, column=0, padx=SIZES["pad_md"], pady=0, sticky="w")

        # Label
        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(*FONTS["stat_label"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=2, column=0, padx=SIZES["pad_md"], pady=(2, SIZES["pad_md"]), sticky="w")

    def set_value(self, value: str) -> None:
        self._value_label.configure(text=value)


# ──────────────────────────────────────────────────────────────────
# SectionTitle
# ──────────────────────────────────────────────────────────────────

class SectionTitle(ctk.CTkFrame):
    """
    Section heading with optional subtitle and a bottom divider.

    Args:
        title    : Main heading text.
        subtitle : Optional smaller text below the heading.
    """

    def __init__(self, master, title: str, subtitle: str = "", **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        if subtitle:
            ctk.CTkLabel(
                self,
                text=subtitle,
                font=ctk.CTkFont(*FONTS["small"]),
                text_color=COLORS["overlay1"],
                anchor="w",
            ).grid(row=1, column=0, sticky="ew", pady=(2, 0))

        Divider(self).grid(
            row=2, column=0, sticky="ew",
            pady=(SIZES["pad_sm"], 0),
        )


# ──────────────────────────────────────────────────────────────────
# Divider
# ──────────────────────────────────────────────────────────────────

class Divider(ctk.CTkFrame):
    """Horizontal 1px separator line."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            height=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
            **kwargs,
        )


# ──────────────────────────────────────────────────────────────────
# Badge
# ──────────────────────────────────────────────────────────────────

class Badge(ctk.CTkLabel):
    """
    Pill-shaped coloured label.

    Args:
        text  : Badge text.
        color : Background colour (defaults to accent).
    """

    def __init__(self, master, text: str, color: str | None = None, **kwargs) -> None:
        color = color or COLORS["accent"]
        super().__init__(
            master,
            text=f"  {text}  ",
            font=ctk.CTkFont(*FONTS["badge"]),
            text_color=COLORS["base"],
            fg_color=color,
            corner_radius=10,
            **kwargs,
        )


# ──────────────────────────────────────────────────────────────────
# ToggleRow
# ──────────────────────────────────────────────────────────────────

class ToggleRow(ctk.CTkFrame):
    """
    One row: label (left) + CTkSwitch (right).

    Args:
        label       : Row label text.
        description : Optional dim description below the label.
        default     : Initial toggle state (True = on).
        command     : Callback(value: bool) when toggled.
    """

    def __init__(
        self,
        master,
        label: str,
        description: str = "",
        default: bool = False,
        command: callable | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=SIZES["btn_radius"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        # Left: text block
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="w", padx=SIZES["pad_md"], pady=SIZES["pad_sm"])

        ctk.CTkLabel(
            text_frame,
            text=label,
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if description:
            ctk.CTkLabel(
                text_frame,
                text=description,
                font=ctk.CTkFont(*FONTS["small"]),
                text_color=COLORS["overlay1"],
                anchor="w",
            ).grid(row=1, column=0, sticky="w")

        # Right: switch
        self._var = ctk.BooleanVar(value=default)
        switch = ctk.CTkSwitch(
            self,
            text="",
            variable=self._var,
            onvalue=True,
            offvalue=False,
            progress_color=COLORS["accent"],
            button_color=COLORS["text"],
            command=lambda: command(self._var.get()) if command else None,
        )
        switch.grid(row=0, column=1, padx=SIZES["pad_md"], pady=SIZES["pad_sm"])

    @property
    def value(self) -> bool:
        return self._var.get()


# ──────────────────────────────────────────────────────────────────
# InfoRow
# ──────────────────────────────────────────────────────────────────

class InfoRow(ctk.CTkFrame):
    """
    One row: key label (left) + value label (right).
    Used in info panels, settings summaries, etc.
    """

    def __init__(self, master, key: str, value: str, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text=key,
            font=ctk.CTkFont(*FONTS["label"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            width=160,
        ).grid(row=0, column=0, sticky="w", padx=(0, SIZES["pad_md"]))

        self._val = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["text"],
            anchor="w",
        )
        self._val.grid(row=0, column=1, sticky="w")

    def set_value(self, value: str) -> None:
        self._val.configure(text=value)


# ──────────────────────────────────────────────────────────────────
# CameraFeed
# ──────────────────────────────────────────────────────────────────

class CameraFeed(ctk.CTkFrame):
    """
    Live camera preview frame.
    Renders OpenCV frames on the Tk main thread and resizes cleanly.
    """

    def __init__(self, master, width: int = 640, height: int = 360, show_overlays: bool = False, **kwargs) -> None:
        self._preferred_width = width
        self._preferred_height = height
        super().__init__(
            master,
            width=width,
            height=height,
            fg_color=COLORS["crust"],
            corner_radius=SIZES["card_radius"],
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._last_frame: np.ndarray | None = None
        self._photo: ctk.CTkImage | None = None
        self._mode: str = "placeholder"

        self._content = ctk.CTkLabel(self, text="")
        self._content.grid(row=0, column=0, sticky="nsew")

        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.grid(row=0, column=0)

        ctk.CTkLabel(
            self._placeholder,
            text="◎",
            font=ctk.CTkFont("Segoe UI", 48),
            text_color=COLORS["overlay0"],
        ).grid(row=0, column=0, pady=(0, 8))

        ctk.CTkLabel(
            self._placeholder,
            text="Camera feed will appear here",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
        ).grid(row=1, column=0)

        # Overlays setup
        self._show_overlays = show_overlays
        if self._show_overlays:
            self._overlay_fps = ctk.CTkLabel(
                self,
                text="FPS: --",
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                text_color=COLORS["blue"],
                fg_color=COLORS["crust"],
                corner_radius=6,
                padx=8,
                pady=4,
            )
            self._overlay_fps.place(relx=0.02, rely=0.03, anchor="nw")

            self._overlay_hands = ctk.CTkLabel(
                self,
                text="Hands: 0",
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                text_color=COLORS["overlay1"],
                fg_color=COLORS["crust"],
                corner_radius=6,
                padx=8,
                pady=4,
            )
            self._overlay_hands.place(relx=0.98, rely=0.03, anchor="ne")

            self._overlay_gesture = ctk.CTkLabel(
                self,
                text="Gesture: --",
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=COLORS["green"],
                fg_color=COLORS["crust"],
                corner_radius=6,
                padx=10,
                pady=6,
            )
            self._overlay_gesture.place(relx=0.02, rely=0.97, anchor="sw")

            self._overlay_confidence = ctk.CTkLabel(
                self,
                text="Confidence: --",
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                text_color=COLORS["mauve"],
                fg_color=COLORS["crust"],
                corner_radius=6,
                padx=8,
                pady=4,
            )
            self._overlay_confidence.place(relx=0.98, rely=0.97, anchor="se")

        self.bind("<Configure>", self._on_resize)

    def set_frame(
        self,
        frame: np.ndarray | None,
        fps: float = 0.0,
        gesture: str = "unknown",
        confidence: float = 0.0,
        hands_detected: int = 0,
    ) -> None:
        """Displays an OpenCV frame on the widget and updates overlays."""
        self._last_frame = frame.copy() if frame is not None else None
        if self._last_frame is None:
            self._show_placeholder()
            return

        self._render_current_frame()

        if self._show_overlays:
            fps_text = f"FPS: {fps:.1f}" if fps > 0 else "FPS: --"
            self._overlay_fps.configure(text=fps_text)

            hands_text = f"Hands: {hands_detected}"
            self._overlay_hands.configure(text=hands_text)
            self._overlay_hands.configure(
                text_color=COLORS["green"] if hands_detected > 0 else COLORS["overlay1"]
            )

            # Clean gesture label
            if gesture in ("unknown", "No Model"):
                gesture_text = f"Gesture: {gesture}"
                self._overlay_gesture.configure(text=gesture_text, text_color=COLORS["overlay1"])
            else:
                gesture_text = f"Gesture: {gesture.replace('_', ' ').title()}"
                self._overlay_gesture.configure(text=gesture_text, text_color=COLORS["green"])

            conf_text = f"Confidence: {confidence * 100:.0f}%" if confidence > 0 and gesture not in ("unknown", "No Model") else "Confidence: --"
            self._overlay_confidence.configure(text=conf_text)

            # Lift overlays above the canvas
            self._overlay_fps.lift()
            self._overlay_hands.lift()
            self._overlay_gesture.lift()
            self._overlay_confidence.lift()

    def clear(self) -> None:
        """Resets the preview back to its placeholder state."""
        self._last_frame = None
        self._show_placeholder()

    def _on_resize(self, _event) -> None:
        if self._last_frame is not None:
            self._render_current_frame()

    def _show_placeholder(self) -> None:
        self._mode = "placeholder"
        self._content.configure(image="", text="")
        self._placeholder.lift()
        if hasattr(self, "_show_overlays") and self._show_overlays:
            self._overlay_fps.configure(text="FPS: --")
            self._overlay_hands.configure(text="Hands: 0", text_color=COLORS["overlay1"])
            self._overlay_gesture.configure(text="Gesture: --", text_color=COLORS["overlay1"])
            self._overlay_confidence.configure(text="Confidence: --")

    def _render_current_frame(self) -> None:
        if self._last_frame is None:
            self._show_placeholder()
            return

        target_w = max(1, self.winfo_width() or self._preferred_width)
        target_h = max(1, self.winfo_height() or self._preferred_height)

        img_h, img_w = self._last_frame.shape[:2]
        img_ratio = img_w / img_h
        target_ratio = target_w / target_h

        if img_ratio > target_ratio:
            # Image is wider than target: crop sides
            new_w = int(img_h * target_ratio)
            left = (img_w - new_w) // 2
            right = left + new_w
            cropped = self._last_frame[:, left:right]
        else:
            # Image is taller than target: crop top/bottom
            new_h = int(img_w / target_ratio)
            top = (img_h - new_h) // 2
            bottom = top + new_h
            cropped = self._last_frame[top:bottom, :]

        # Optimized OpenCV resize (Fast Bilinear Interpolation)
        resized = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        fitted = Image.fromarray(rgb)

        self._photo = ctk.CTkImage(light_image=fitted, dark_image=fitted, size=(target_w, target_h))
        self._content.configure(image=self._photo, text="")
        self._content.lift()


# ──────────────────────────────────────────────────────────────────
# EmptyState
# ──────────────────────────────────────────────────────────────────

class EmptyState(ctk.CTkFrame):
    """
    Centred empty state widget shown when a page has no data yet.

    Args:
        icon    : Large Unicode symbol.
        title   : Main message.
        subtitle: Supporting hint text.
    """

    def __init__(
        self,
        master,
        icon: str = "◈",
        title: str = "Nothing here yet",
        subtitle: str = "Content will appear here once you get started.",
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=0)

        ctk.CTkLabel(
            inner,
            text=icon,
            font=ctk.CTkFont("Segoe UI", 52),
            text_color=COLORS["overlay0"],
        ).grid(row=0, column=0, pady=(0, 12))

        ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["subtext0"],
        ).grid(row=1, column=0, pady=(0, 6))

        ctk.CTkLabel(
            inner,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            wraplength=340,
            justify="center",
        ).grid(row=2, column=0)
