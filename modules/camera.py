"""
GestureOS AI — Camera Stream
Thread-safe camera capture using OpenCV.
"""

import threading
from pathlib import Path

import cv2
import numpy as np
import yaml
from loguru import logger


def _load_camera_config() -> dict:
    """Loads camera section from config/settings.yaml."""
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
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps

        self._cap: cv2.VideoCapture | None = None
        self._frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> "CameraStream":
        self._cap = cv2.VideoCapture(self.index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)

        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera at index {self.index}")

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Camera {self.index} started ({self.width}x{self.height} @ {self.fps}fps)")
        return self

    def _capture_loop(self) -> None:
        while self._running and self._cap is not None:
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._frame = frame

    def read(self) -> np.ndarray | None:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        logger.info("Camera stopped.")
