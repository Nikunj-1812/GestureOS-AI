"""
GestureOS AI — Gesture Engine
Loads an ONNX model and classifies hand landmarks into gesture labels.
Applies temporal smoothing to reduce flicker.

FIX BUG-007: The GestureClassifier model outputs raw logits (no softmax
layer). Using logits[argmax] directly as a "confidence" value produces
numbers that are not probabilities — they can be negative or exceed 1.0,
making the confidence_threshold comparison meaningless.

Fix: apply a numerically stable softmax over the raw logits before
extracting the winning probability.  scipy is not needed; the stable
softmax is implemented inline with numpy in two lines.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
import onnxruntime as ort
from loguru import logger

from modules.hand_detector import HandLandmarks


def _softmax(logits: np.ndarray) -> np.ndarray:
    """
    Numerically stable softmax over a 1-D logits array.

    Subtracting max(logits) before exp() prevents overflow for large
    logit values while keeping the output identical (the constant
    cancels in the ratio).  Output is a proper probability distribution
    summing to 1.0.
    """
    shifted = logits - logits.max()
    exp_vals = np.exp(shifted)
    return exp_vals / exp_vals.sum()


class GestureEngine:
    """Classifies gestures from MediaPipe hand landmarks via ONNX inference."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.75,
        smoothing_frames: int = 5,
    ) -> None:
        self.model_path           = model_path
        self.confidence_threshold = confidence_threshold
        self._history: deque[str]             = deque(maxlen=smoothing_frames)
        self._session: ort.InferenceSession | None = None
        self._labels:  list[str]             = []
        self._load_model()

    # ------------------------------------------------------------------ #
    @property
    def is_loaded(self) -> bool:
        """True when an ONNX session is open and labels are available."""
        return self._session is not None and len(self._labels) > 0

    # ------------------------------------------------------------------ #
    def _load_model(self) -> None:
        path = Path(self.model_path)
        if not path.exists():
            logger.warning(
                f"Model file not found: {self.model_path}. "
                "Gesture inference disabled."
            )
            return

        self._session = ort.InferenceSession(str(path))
        logger.info(f"Loaded gesture model: {self.model_path}")

        # Load companion label file produced by train_model.py
        label_path = path.with_suffix(".txt")
        if label_path.exists():
            self._labels = label_path.read_text(encoding="utf-8").strip().splitlines()
            logger.info(f"Loaded {len(self._labels)} gesture labels.")
        else:
            logger.warning(
                f"Label file not found: {label_path}. "
                "Predictions will return numeric class indices."
            )

    # ------------------------------------------------------------------ #
    def predict(self, hand: HandLandmarks) -> tuple[str, float]:
        """
        Predict the gesture for a single detected hand.

        Returns:
            (label, confidence) where confidence is a true probability
            in [0, 1] after softmax is applied to the model logits.
            Returns ("unknown", 0.0) if the model is not loaded or the
            top-class probability falls below confidence_threshold.
        """
        if self._session is None:
            return "unknown", 0.0

        # Validate input shape: 21 landmarks × 3 coords = 63 features
        raw = np.array(hand.landmarks, dtype=np.float32)
        if raw.shape != (21, 3):
            logger.warning(
                f"Unexpected landmark shape {raw.shape}; expected (21, 3). "
                "Skipping inference."
            )
            return "unknown", 0.0

        # Shape: (1, 63)  — batch of 1
        features   = raw.flatten()[np.newaxis, :]
        input_name = self._session.get_inputs()[0].name
        outputs    = self._session.run(None, {input_name: features})

        # FIX BUG-007: outputs[0][0] are raw logits.
        # Apply softmax to convert to proper probabilities [0, 1].
        logits     = outputs[0][0]               # shape: (num_classes,)
        probs      = _softmax(logits)            # now a probability distribution
        idx        = int(np.argmax(probs))
        confidence = float(probs[idx])           # guaranteed in (0, 1]

        if confidence < self.confidence_threshold:
            return "unknown", confidence

        label = self._labels[idx] if idx < len(self._labels) else str(idx)
        self._history.append(label)
        return self._smoothed_label(), confidence

    # ------------------------------------------------------------------ #
    def _smoothed_label(self) -> str:
        """Return the most frequent label in the recent history window."""
        if not self._history:
            return "unknown"
        return max(set(self._history), key=self._history.count)

    # ------------------------------------------------------------------ #
    def reset(self) -> None:
        """Clear the smoothing history (call when the hand disappears)."""
        self._history.clear()
