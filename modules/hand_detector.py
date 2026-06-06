"""
GestureOS AI — Hand Detector
Wraps MediaPipe Hands to detect and extract hand landmarks from frames.
"""

from __future__ import annotations
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np


@dataclass
class HandLandmarks:
    landmarks: list[tuple[float, float, float]]  # (x, y, z) normalized
    handedness: str                               # "Left" | "Right"
    bbox: tuple[int, int, int, int]               # (x, y, w, h) in pixels


class HandDetector:
    """Detects hands and extracts landmarks using MediaPipe."""

    def __init__(
        self,
        max_hands: int = 2,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.7,
    ) -> None:
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._mp_draw = mp.solutions.drawing_utils

    def detect(self, frame: np.ndarray) -> list[HandLandmarks]:
        """Run detection on a BGR frame; returns a list of detected hands."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        detected: list[HandLandmarks] = []

        if not results.multi_hand_landmarks:
            return detected

        h, w = frame.shape[:2]
        for hand_lm, hand_info in zip(
            results.multi_hand_landmarks,
            results.multi_handedness,
        ):
            landmarks = [
                (lm.x, lm.y, lm.z) for lm in hand_lm.landmark
            ]
            handedness = hand_info.classification[0].label

            # Bounding box from landmark extent
            xs = [lm.x * w for lm in hand_lm.landmark]
            ys = [lm.y * h for lm in hand_lm.landmark]
            x1, y1 = int(min(xs)) - 10, int(min(ys)) - 10
            x2, y2 = int(max(xs)) + 10, int(max(ys)) + 10
            bbox = (x1, y1, x2 - x1, y2 - y1)

            detected.append(HandLandmarks(landmarks=landmarks, handedness=handedness, bbox=bbox))

        return detected

    def draw(self, frame: np.ndarray, hands: list[HandLandmarks]) -> np.ndarray:
        """Draw landmark overlays onto the frame (in-place)."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        if results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                self._mp_draw.draw_landmarks(
                    frame, hand_lm, self._mp_hands.HAND_CONNECTIONS
                )
        return frame

    def close(self) -> None:
        self._hands.close()
