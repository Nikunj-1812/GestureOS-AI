"""
GestureOS AI — Webcam Preview
==============================
A beginner-friendly, production-ready webcam viewer using OpenCV.

Features:
  - Live webcam feed
  - Real-time FPS counter (rolling average)
  - Flip / mirror mode (feels natural for gestures)
  - Press Q to quit cleanly

Usage:
  python webcam_preview.py
  python webcam_preview.py --camera 1    # use a different camera index
  python webcam_preview.py --no-flip     # disable mirror mode
"""

import argparse
import time
import sys
from collections import deque
from pathlib import Path

import cv2
import yaml


# ─────────────────────────────────────────────
# Config Loader
# ─────────────────────────────────────────────

def _load_default_camera_index() -> int:
    """
    Reads the camera index from config/settings.yaml.
    Falls back to 0 if the file is missing or unreadable.
    """
    config_path = Path(__file__).parent / "config" / "settings.yaml"
    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        return int(cfg.get("camera", {}).get("index", 0))
    except Exception:
        return 0


_DEFAULT_CAMERA_INDEX = _load_default_camera_index()


# ─────────────────────────────────────────────
# FPS Counter
# ─────────────────────────────────────────────

class FPSCounter:
    """
    Calculates a smooth, rolling-average FPS.

    Instead of measuring one frame at a time (which fluctuates a lot),
    it tracks timestamps over the last N frames for a stable reading.

    Args:
        window (int): How many recent frames to average over.
    """

    def __init__(self, window: int = 30) -> None:
        self._timestamps: deque[float] = deque(maxlen=window)

    def tick(self) -> float:
        """
        Call this once per frame.
        Returns the current FPS as a float.
        """
        self._timestamps.append(time.monotonic())

        # Need at least 2 timestamps to calculate FPS
        if len(self._timestamps) < 2:
            return 0.0

        # FPS = (number of intervals) / (total elapsed time)
        elapsed = self._timestamps[-1] - self._timestamps[0]
        if elapsed == 0:
            return 0.0

        return (len(self._timestamps) - 1) / elapsed


# ─────────────────────────────────────────────
# Drawing Helpers
# ─────────────────────────────────────────────

def draw_fps(frame, fps: float) -> None:
    """
    Draws a semi-transparent FPS badge in the top-left corner.

    We draw the text twice — once as a dark shadow, once as the
    bright text — so it's readable on any background.

    Args:
        frame: The OpenCV BGR frame to draw on (modified in-place).
        fps:   The current frames-per-second value.
    """
    label = f"FPS: {fps:.1f}"
    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness  = 2
    position   = (16, 38)

    # Dark shadow (offset by 1px) — improves readability
    cv2.putText(frame, label, (position[0] + 1, position[1] + 1),
                font, font_scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)

    # Bright green text on top
    cv2.putText(frame, label, position,
                font, font_scale, (0, 230, 0), thickness, cv2.LINE_AA)


def draw_instructions(frame) -> None:
    """
    Draws a small 'Press Q to quit' hint at the bottom of the frame.

    Args:
        frame: The OpenCV BGR frame to draw on (modified in-place).
    """
    h = frame.shape[0]
    label = "Press Q to quit"
    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness  = 1
    position   = (16, h - 16)

    # Shadow
    cv2.putText(frame, label, (position[0] + 1, position[1] + 1),
                font, font_scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)

    # White text
    cv2.putText(frame, label, position,
                font, font_scale, (220, 220, 220), thickness, cv2.LINE_AA)


# ─────────────────────────────────────────────
# Camera Setup
# ─────────────────────────────────────────────

def open_camera(index: int) -> cv2.VideoCapture:
    """
    Opens the webcam and applies recommended settings.

    Args:
        index (int): Camera index. 0 = default built-in webcam.

    Returns:
        cv2.VideoCapture: Ready-to-use capture object.

    Raises:
        SystemExit: If the camera cannot be opened.
    """
    cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera at index {index}.")
        print("        Try a different --camera index (e.g. 0, 1, 2).")
        sys.exit(1)

    # Request HD resolution — camera will use the closest it supports
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # Read back what the camera actually accepted
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"[INFO] Camera {index} opened: {actual_w}x{actual_h} @ {actual_fps:.0f}fps")

    return cap


# ─────────────────────────────────────────────
# Main Loop
# ─────────────────────────────────────────────

def run_preview(camera_index: int = _DEFAULT_CAMERA_INDEX, flip: bool = True) -> None:
    """
    Main webcam preview loop.

    Opens the camera, reads frames in a loop, draws the FPS overlay,
    and exits cleanly when the user presses Q.

    Args:
        camera_index (int): Which camera to use (default: 0).
        flip (bool):        Mirror the frame horizontally (default: True).
                            Mirroring feels more natural — like a mirror.
    """
    cap = open_camera(camera_index)
    fps_counter = FPSCounter(window=30)

    print("[INFO] Preview started. Press Q in the video window to quit.")

    while True:
        # ── Read a frame ──────────────────────────────────────────────
        ret, frame = cap.read()

        if not ret:
            # Camera disconnected or stream ended
            print("[WARNING] Failed to read frame. Camera may be disconnected.")
            break

        # ── Optional: mirror the image ────────────────────────────────
        # flipCode=1 flips left-right (like a selfie camera)
        if flip:
            frame = cv2.flip(frame, 1)

        # ── Calculate and draw FPS ────────────────────────────────────
        fps = fps_counter.tick()
        draw_fps(frame, fps)
        draw_instructions(frame)

        # ── Show the frame ────────────────────────────────────────────
        cv2.imshow("GestureOS AI — Webcam Preview", frame)

        # ── Check for Q key press ─────────────────────────────────────
        # cv2.waitKey(1) waits 1ms and returns the key code pressed.
        # Bitwise & 0xFF extracts the lower 8 bits (handles Num Lock etc.)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == ord("Q"):
            print("[INFO] Q pressed. Exiting...")
            break

    # ── Cleanup ───────────────────────────────────────────────────────
    # Always release the camera and close windows, even if an error occurred.
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Camera released. Goodbye.")


# ─────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GestureOS AI — Live Webcam Preview with FPS counter."
    )
    parser.add_argument(
        "--camera", type=int, default=_DEFAULT_CAMERA_INDEX,
        help=f"Camera index to use (default from config: {_DEFAULT_CAMERA_INDEX})"
    )
    parser.add_argument(
        "--no-flip", action="store_true",
        help="Disable horizontal mirror flip"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_preview(
        camera_index=args.camera,
        flip=not args.no_flip,
    )
