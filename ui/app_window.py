"""
GestureOS AI — Main Application Window (PyQt6)
Renders live camera feed with gesture overlay.
"""

from __future__ import annotations
import sys

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from loguru import logger

from config.app_config import AppConfig
from modules.camera import CameraStream
from modules.gesture_engine import GestureEngine
from modules.hand_detector import HandDetector
from modules.action_dispatcher import ActionDispatcher
from modules.utils import FPSCounter, draw_fps, draw_gesture_label, draw_bounding_box


class AppWindow(QMainWindow):
    """Main window: shows camera feed + gesture annotations."""

    def __init__(self, camera: CameraStream, engine: GestureEngine, config: AppConfig) -> None:
        self._qt_app = QApplication(sys.argv)
        super().__init__()

        self.camera = camera
        self.engine = engine
        self.config = config
        self.detector = HandDetector()
        self.dispatcher = ActionDispatcher()
        self.fps_counter = FPSCounter()

        self._build_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_frame)
        self._timer.start(1000 // config.camera_fps)

    def _build_ui(self) -> None:
        self.setWindowTitle(self.config.window_title)
        self.setMinimumSize(960, 560)

        self._video_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self._video_label)
        self.setCentralWidget(container)

    def _update_frame(self) -> None:
        frame = self.camera.read()
        if frame is None:
            return

        if self.config.flip_horizontal:
            frame = cv2.flip(frame, 1)

        hands = self.detector.detect(frame)

        for hand in hands:
            label, conf = self.engine.predict(hand)
            self.dispatcher.dispatch(label)

            if self.config.show_landmarks:
                frame = draw_bounding_box(frame, hand.bbox, label=hand.handedness)

            frame = draw_gesture_label(frame, label, conf)

        fps = self.fps_counter.tick()
        if self.config.show_fps:
            frame = draw_fps(frame, fps)

        self._display(frame)

    def _display(self, frame: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self._video_label.setPixmap(QPixmap.fromImage(qt_image))

    def run(self) -> int:
        self.camera.start()
        self.show()
        logger.info("UI launched.")
        return self._qt_app.exec()

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self.camera.stop()
        self.detector.close()
        super().closeEvent(event)
