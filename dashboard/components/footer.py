"""
GestureOS AI — Footer Status Bar Component
==========================================
Bottom status bar showing live dashboard metrics:
  • FPS
  • Camera status
  • Hand detection status
  • Model status
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.theme import COLORS, FONTS, SIZES


class FooterBar(ctk.CTkFrame):
    """Bottom status bar fixed at the bottom of the window."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            height=SIZES["footer_h"],
            corner_radius=0,
            fg_color=COLORS["footer_bg"],
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._build()

    def _build(self) -> None:
        border = ctk.CTkFrame(
            self,
            height=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
        )
        border.grid(row=0, column=0, columnspan=5, sticky="ew")

        self._fps_tile = _MetricTile(self, "FPS", "--", COLORS["blue"])
        self._fps_tile.grid(row=1, column=0, sticky="ew", padx=(12, 4), pady=6)

        self._camera_tile = _MetricTile(self, "Camera", "Disconnected", COLORS["red"])
        self._camera_tile.grid(row=1, column=1, sticky="ew", padx=4, pady=6)

        self._model_tile = _MetricTile(self, "Model", "Not Loaded", COLORS["overlay0"])
        self._model_tile.grid(row=1, column=2, sticky="ew", padx=4, pady=6)

        self._gesture_tile = _MetricTile(self, "Gesture", "None", COLORS["overlay1"])
        self._gesture_tile.grid(row=1, column=3, sticky="ew", padx=4, pady=6)

        self._system_tile = _MetricTile(self, "System Status", "Ready", COLORS["green"])
        self._system_tile.grid(row=1, column=4, sticky="ew", padx=(4, 12), pady=6)

    def set_fps(self, fps: float) -> None:
        """Updates the FPS metric."""
        color = COLORS["status_ok"] if fps >= 25 else COLORS["status_warn"] if fps >= 15 else COLORS["status_err"]
        value = f"{fps:.0f}" if fps >= 10 else f"{fps:.1f}"
        self._fps_tile.set_value(value)
        self._fps_tile.set_accent(color)

    def set_camera_status(self, status: str) -> None:
        """Updates the camera status metric."""
        color = COLORS["green"] if "Connected" in status else COLORS["yellow"] if "Starting" in status else COLORS["red"]
        self._camera_tile.set_value(status)
        self._camera_tile.set_accent(color)

    def set_hand_status(self, status: str) -> None:
        """Updates the hand detection status metric in the System Status tile."""
        color = COLORS["green"] if "Detected" in status else COLORS["overlay0"]
        self._system_tile.set_value(status)
        self._system_tile.set_accent(color)

    def set_model_status(self, status: str) -> None:
        """Updates the model status metric."""
        color = COLORS["green"] if "Loaded" in status else COLORS["red"]
        self._model_tile.set_value(status)
        self._model_tile.set_accent(color)

    def set_gesture(self, gesture: str, confidence: float) -> None:
        """Updates the current gesture metric."""
        if gesture in ("None", "unknown", "No Model"):
            self._gesture_tile.set_value(gesture)
            self._gesture_tile.set_accent(COLORS["overlay1"])
        else:
            display_text = f"{gesture.replace('_', ' ').title()} ({confidence * 100:.0f}%)"
            self._gesture_tile.set_value(display_text)
            self._gesture_tile.set_accent(COLORS["green"])

    def set_status(self, message: str, level: str = "ok") -> None:
        """Compatibility helper for older callers."""
        self._system_tile.set_value(message)
        color = COLORS["status_ok"] if level == "ok" else COLORS["status_warn"] if level == "warn" else COLORS["status_err"] if level == "err" else COLORS["overlay0"]
        self._system_tile.set_accent(color)


class _MetricTile(ctk.CTkFrame):
    """Small tile used for each footer metric."""

    def __init__(self, master, label: str, value: str, accent: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["divider"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        self._label = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(*FONTS["badge"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        self._label.grid(row=0, column=0, sticky="w", padx=10, pady=(7, 0))

        self._value = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=accent,
            anchor="w",
        )
        self._value.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 7))

    def set_value(self, value: str) -> None:
        self._value.configure(text=value)

    def set_accent(self, color: str) -> None:
        self._value.configure(text_color=color)
