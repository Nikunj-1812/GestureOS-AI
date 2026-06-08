"""
GestureOS AI — Shared Utilities
================================
Helper functions for FPS counting, frame annotation, and drawing.

FIX BUG-004: FPSCounter now uses collections.deque(maxlen=N) instead of
a plain list with pop(0). list.pop(0) is O(n) — it shifts every element
left after each removal. deque with a fixed maxlen discards the oldest
entry in O(1) and matches the implementation used by all standalone
scripts (hand_tracking.py, finger_state_detector.py, etc.).
"""

from __future__ import annotations

import time
from collections import deque

import cv2
import numpy as np


class FPSCounter:
    """
    Rolling-average FPS counter backed by a fixed-size timestamp deque.

    Uses collections.deque(maxlen=window) for O(1) append and automatic
    eviction of the oldest timestamp — no manual list management needed.
    """

    def __init__(self, window: int = 30) -> None:
        self._timestamps: deque[float] = deque(maxlen=window)

    def tick(self) -> float:
        """Record the current time and return the smoothed FPS."""
        self._timestamps.append(time.monotonic())
        if len(self._timestamps) < 2:
            return 0.0
        elapsed = self._timestamps[-1] - self._timestamps[0]
        return (len(self._timestamps) - 1) / elapsed if elapsed > 0 else 0.0

    def reset(self) -> None:
        """Clear the timestamp history."""
        self._timestamps.clear()


# ──────────────────────────────────────────────────────────────────
# Frame annotation helpers
# ──────────────────────────────────────────────────────────────────

def draw_fps(frame: np.ndarray, fps: float) -> np.ndarray:
    """Overlay a green FPS counter in the top-left corner."""
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
    )
    return frame


def draw_gesture_label(
    frame: np.ndarray, label: str, confidence: float
) -> np.ndarray:
    """Overlay the current gesture label and confidence score."""
    text = f"{label} ({confidence * 100:.1f}%)"
    cv2.putText(
        frame,
        text,
        (10, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 80, 80),
        2,
    )
    return frame


def draw_bounding_box(
    frame: np.ndarray,
    bbox: tuple[int, int, int, int],
    label: str = "",
    color: tuple[int, int, int] = (0, 200, 255),
) -> np.ndarray:
    """Draw a labelled bounding box on the frame."""
    x, y, w, h = bbox
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    if label:
        cv2.putText(
            frame, label, (x, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1,
        )
    return frame
