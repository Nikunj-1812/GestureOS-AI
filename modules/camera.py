"""
GestureOS AI — Camera Stream
Thread-safe camera capture using OpenCV.

FIX BUG-006: Removed the redundant time.sleep() from _capture_loop.
cv2.VideoCapture.read() is a blocking call that already waits for the
next hardware frame at the camera's native rate. Adding an extra sleep
of 1/fps seconds after every read() was causing the thread to pause for
a full additional frame period, effectively halving the real capture
rate (30fps config → ~15fps actual). Removing the sleep lets read()
self-pace against the hardware frame clock.

A short yield (time.sleep(0)) is kept only on failed reads so the loop
does not busy-spin on a disconnected or erroring camera device.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import cv2
import numpy as np
import yaml
from loguru import logger


def _load_camera_config() -> dict:
    """Loads camera section from config/settings.yaml at import time."""
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("camera", {})
    except Exception:
        return {}


_CAMERA_CFG = _load_camera_config()


class CameraStream:
    """Captures frames from a camera in a background thread."""

    def __init__(
        self,
        index: int  = _CAMERA_CFG.get("index", 0),
        width: int  = _CAMERA_CFG.get("width", 1280),
        height: int = _CAMERA_CFG.get("height", 720),
        fps: int    = _CAMERA_CFG.get("fps", 30),
    ) -> None:
        self.index  = index
        self.width  = width
        self.height = height
        self.fps    = fps

        self._cap:    cv2.VideoCapture | None = None
        self._frame:  np.ndarray | None = None
        self._lock    = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------ #
    def start(self) -> "CameraStream":
        """Open the camera device and launch the capture thread."""
        self._cap = cv2.VideoCapture(self.index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS,          self.fps)

        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera at index {self.index}")

        self._running = True
        self._thread  = threading.Thread(
            target=self._capture_loop, daemon=True, name="CameraCapture"
        )
        self._thread.start()
        logger.info(
            f"Camera {self.index} started "
            f"({self.width}x{self.height} @ {self.fps}fps)"
        )
        return self

    # ------------------------------------------------------------------ #
    def _capture_loop(self) -> None:
        """
        Background capture loop.

        FIX BUG-006: cap.read() is already blocking — it waits for the
        next hardware frame before returning. The previous sleep(1/fps)
        doubled the inter-frame delay. It is removed entirely.

        On a failed read (camera error / disconnect) we do a short
        sleep so we don't busy-spin and saturate the CPU.
        """
        while self._running and self._cap is not None:
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._frame = frame
            else:
                # Failed read — back off briefly to avoid CPU spin
                time.sleep(0.05)

    # ------------------------------------------------------------------ #
    def read(self) -> np.ndarray | None:
        """Return a copy of the most recent captured frame, or None."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    # ------------------------------------------------------------------ #
    def stop(self) -> None:
        """Signal the capture thread to stop and release the device."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        logger.info("Camera stopped.")
