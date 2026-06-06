"""
GestureOS AI — Frame Preprocessor
Prepares raw camera frames for model inference (resize, normalize, etc.).
"""

from __future__ import annotations
import cv2
import numpy as np


class Preprocessor:
    """Applies preprocessing pipeline to raw BGR frames."""

    def __init__(self, target_size: tuple[int, int] = (224, 224)) -> None:
        self.target_size = target_size

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Resize → RGB → normalize to [0, 1].
        Returns float32 array of shape (H, W, 3).
        """
        resized = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = rgb.astype(np.float32) / 255.0
        return normalized

    def to_tensor(self, frame: np.ndarray) -> np.ndarray:
        """Convert (H, W, C) → (1, C, H, W) for PyTorch-style inference."""
        processed = self.process(frame)
        tensor = np.transpose(processed, (2, 0, 1))[np.newaxis, :]  # NCHW
        return tensor
