"""
GestureOS AI — Transparent Overlay Widget
A frameless, always-on-top overlay for showing gesture hints on screen.
"""

from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget


class OverlayWidget(QWidget):
    """Semi-transparent floating HUD that shows the active gesture."""

    def __init__(self, opacity: float = 0.85) -> None:
        super().__init__()
        self._gesture = ""
        self._confidence = 0.0
        self.setWindowOpacity(opacity)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 70)

    def update_gesture(self, gesture: str, confidence: float) -> None:
        self._gesture = gesture
        self._confidence = confidence
        self.repaint()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background pill
        painter.setBrush(QColor(30, 30, 46, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)

        # Gesture label
        painter.setPen(QColor(205, 214, 244))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter,
            f"{self._gesture}  {self._confidence * 100:.0f}%",
        )
