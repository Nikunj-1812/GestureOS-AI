"""
GestureOS AI — Utilities
Shared helper functions for drawing, FPS counting, and frame annotation.
"""

from __future__ import annotations
import time

import cv2
import numpy as np


class FPSCounter:
    """Rolling-average FPS counter."""

    def __init__(self, window: int = 30) -> None:
        self._times: list[float] = []
        self._window = window

    def tick(self) -> float:
        self._times.append(time.monotonic())
        if len(self._times) > self._window:
            self._times.pop(0)
        if len(self._times) < 2:
            return 0.0
        elapsed = self._times[-1] - self._times[0]
        return (len(self._times) - 1) / elapsed if elapsed > 0 else 0.0


def draw_fps(frame: np.ndarray, fps: float) -> np.ndarray:
    cv2.putText(
        frame, f"FPS: {fps:.1f}", (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
    )
    return frame


def draw_gesture_label(frame: np.ndarray, label: str, confidence: float) -> np.ndarray:
    text = f"{label} ({confidence * 100:.1f}%)"
    cv2.putText(
        frame, text, (10, 65),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 80, 80), 2,
    )
    return frame


def draw_bounding_box(
    frame: np.ndarray,
    bbox: tuple[int, int, int, int],
    label: str = "",
    color: tuple[int, int, int] = (0, 200, 255),
) -> np.ndarray:
    x, y, w, h = bbox
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    if label:
        cv2.putText(frame, label, (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
    return frame
