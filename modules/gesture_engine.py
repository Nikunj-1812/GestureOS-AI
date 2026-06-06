"""
GestureOS AI — Gesture Engine
Loads an ONNX model and classifies hand landmarks into gesture labels.
Applies temporal smoothing to reduce flicker.
"""

from __future__ import annotations
from collections import deque
from pathlib import Path

import numpy as np
import onnxruntime as ort
from loguru import logger

from modules.hand_detector import HandLandmarks


class GestureEngine:
    """Classifies gestures from MediaPipe hand landmarks via ONNX inference."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.75,
        smoothing_frames: int = 5,
    ) -> None:
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self._history: deque[str] = deque(maxlen=smoothing_frames)
        self._session: ort.InferenceSession | None = None
        self._labels: list[str] = []
        self._load_model()

    def _load_model(self) -> None:
        path = Path(self.model_path)
        if not path.exists():
            logger.warning(f"Model file not found: {self.model_path}. Inference disabled.")
            return

        self._session = ort.InferenceSession(str(path))
        logger.info(f"Loaded gesture model: {self.model_path}")

        # Load label file if present alongside the model
        label_path = path.with_suffix(".txt")
        if label_path.exists():
            self._labels = label_path.read_text().strip().splitlines()
            logger.info(f"Loaded {len(self._labels)} gesture labels.")

    def predict(self, hand: HandLandmarks) -> tuple[str, float]:
        """
        Predicts gesture for a single hand.
        Returns (label, confidence). Falls back to 'unknown' if model not loaded.
        """
        if self._session is None:
            return "unknown", 0.0

        # Flatten 21 landmarks × 3 coords → (1, 63) float32
        features = np.array(hand.landmarks, dtype=np.float32).flatten()[np.newaxis, :]
        input_name = self._session.get_inputs()[0].name
        outputs = self._session.run(None, {input_name: features})

        probs = outputs[0][0]
        idx = int(np.argmax(probs))
        confidence = float(probs[idx])

        if confidence < self.confidence_threshold:
            return "unknown", confidence

        label = self._labels[idx] if idx < len(self._labels) else str(idx)
        self._history.append(label)
        return self._smoothed_label(), confidence

    def _smoothed_label(self) -> str:
        """Returns the most frequent label in the recent history window."""
        if not self._history:
            return "unknown"
        return max(set(self._history), key=self._history.count)
