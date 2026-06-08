"""
GestureOS AI — Hand Detector
Wraps MediaPipe Hands to detect and extract hand landmarks from frames.

FIX BUG-005: The previous draw() method re-ran MediaPipe inference on
the same frame a second time, ignoring the `hands` parameter that was
already passed in. This doubled inference cost every frame.

Fix: draw() now accepts the MediaPipe result object directly (cached
from the most recent detect() call) and uses it without re-running
inference. The caller — typically the camera poll loop — calls detect()
once, stores the result, then passes both `detected` (HandLandmarks
list) and `results` (raw MediaPipe output) to draw() if landmark
overlays are needed.

For callers that only need bounding boxes / labels (not skeleton
overlays), detect() alone is sufficient.
"""

from __future__ import annotations

import os
import sys
import io
import time
from contextlib import contextmanager

# Suppress third-party logging / console spam (MediaPipe, TensorFlow, OpenCV)
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'

from dataclasses import dataclass
from typing import Any

import cv2
import mediapipe as mp
import numpy as np


@contextmanager
def silence_stderr():
    """Temporarily redirect stderr to devnull to silence C++ library spam."""
    try:
        stderr_fd = sys.stderr.fileno()
    except (AttributeError, io.UnsupportedOperation):
        yield
        return

    try:
        dup_stderr = os.dup(stderr_fd)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stderr_fd)
        try:
            yield
        finally:
            # Sleep briefly while stderr is still redirected to capture trailing async logs
            time.sleep(0.2)
            os.dup2(dup_stderr, stderr_fd)
            os.close(dup_stderr)
            os.close(devnull)
    except Exception:
        yield


@dataclass
class HandLandmarks:
    landmarks:  list[tuple[float, float, float]]  # (x, y, z) normalised
    handedness: str                               # "Left" | "Right"
    bbox:       tuple[int, int, int, int]         # (x, y, w, h) in pixels


class HandDetector:
    """
    Detects hands and extracts landmarks using MediaPipe.

    Typical usage
    -------------
    detector = HandDetector()
    ...
    hands, mp_results = detector.detect(frame)   # single inference
    frame = detector.draw(frame, mp_results)     # use cached result
    for hand in hands:
        gesture, conf = engine.predict(hand)
    """

    def __init__(
        self,
        max_hands: int = 2,
        detection_confidence: float = 0.7,
        tracking_confidence:  float = 0.7,
    ) -> None:
        self._mp_hands = mp.solutions.hands
        with silence_stderr():
            self._hands    = self._mp_hands.Hands(
                static_image_mode          = False,
                max_num_hands              = max_hands,
                model_complexity           = 0,
                min_detection_confidence   = detection_confidence,
                min_tracking_confidence    = tracking_confidence,
            )
        self._mp_draw  = mp.solutions.drawing_utils
        # Cache the last raw MediaPipe result for draw() to consume
        self._last_results: Any = None
        self._first_detect = True

    # ------------------------------------------------------------------ #
    def detect(self, frame: np.ndarray) -> tuple[list[HandLandmarks], Any]:
        """
        Run MediaPipe inference on a BGR frame.

        Returns
        -------
        detected : list[HandLandmarks]
            Structured landmark data for each detected hand.
        results : mediapipe.Hands result object
            Raw output cached internally; also returned so callers can
            pass it directly to draw() without a second inference.
        """
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self._first_detect:
            with silence_stderr():
                results = self._hands.process(rgb)
            self._first_detect = False
        else:
            results = self._hands.process(rgb)
        self._last_results = results          # cache for draw()

        detected: list[HandLandmarks] = []
        if not results.multi_hand_landmarks:
            return detected, results

        h, w = frame.shape[:2]
        for hand_lm, hand_info in zip(
            results.multi_hand_landmarks,
            results.multi_handedness,
        ):
            landmarks  = [(lm.x, lm.y, lm.z) for lm in hand_lm.landmark]
            handedness = hand_info.classification[0].label

            # Bounding box from landmark extent with padding
            xs = [lm.x * w for lm in hand_lm.landmark]
            ys = [lm.y * h for lm in hand_lm.landmark]
            x1 = max(0, int(min(xs)) - 10)
            y1 = max(0, int(min(ys)) - 10)
            x2 = min(w, int(max(xs)) + 10)
            y2 = min(h, int(max(ys)) + 10)
            bbox = (x1, y1, x2 - x1, y2 - y1)

            detected.append(
                HandLandmarks(
                    landmarks=landmarks,
                    handedness=handedness,
                    bbox=bbox,
                )
            )

        return detected, results

    # ------------------------------------------------------------------ #
    def draw(
        self,
        frame: np.ndarray,
        results: Any | None = None,
    ) -> np.ndarray:
        """
        Draw MediaPipe landmark skeleton overlays onto `frame` in-place.

        FIX BUG-005: Uses the provided `results` object (or falls back
        to the internally cached last result). Does NOT re-run inference.

        Parameters
        ----------
        frame   : BGR image to draw on.
        results : Raw MediaPipe Hands result from the most recent
                  detect() call.  If None, uses self._last_results.
        """
        mp_results = results if results is not None else self._last_results
        if mp_results is None or not mp_results.multi_hand_landmarks:
            return frame

        for hand_lm in mp_results.multi_hand_landmarks:
            self._mp_draw.draw_landmarks(
                frame,
                hand_lm,
                self._mp_hands.HAND_CONNECTIONS,
            )
        return frame

    # ------------------------------------------------------------------ #
    def close(self) -> None:
        """Release the MediaPipe Hands session and GPU resources."""
        self._hands.close()
