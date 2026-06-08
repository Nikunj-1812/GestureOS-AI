"""
GestureOS AI — Virtual Mouse Module
===================================
Tracks index finger tip coordinates and maps them to screen movements
with dead-zone clipping, sensitivity scaling, and EMA smoothing.
"""

from __future__ import annotations

import math
import time
import pyautogui
from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.hand_detector import HandLandmarks


class VirtualMouse:
    """Manages virtual mouse pointer coordinate mapping, movements, and click triggers."""

    def __init__(
        self,
        enabled: bool = False,
        sensitivity: float = 1.5,
        dead_zone: float = 0.15,
        smoothing: float = 0.20,
        click_threshold: float = 0.05,
    ) -> None:
        self.enabled = enabled
        self.sensitivity = sensitivity
        self.dead_zone = dead_zone  # Padding fraction from camera edges [0.0, 0.35]
        self.smoothing = smoothing  # EMA coefficient alpha in [0.05, 0.5]
        self.click_threshold = click_threshold

        self.last_x: int | None = None
        self.last_y: int | None = None

        # Click state machine variables
        self.click_status = "OPEN"      # OPEN | PINCH | LEFT_CLICK | RELEASE | READY
        self.click_counter = 0
        self.current_action = "None"
        self.last_click_time = 0.0      # Timestamp in ms (using time.monotonic() * 1000)
        self.debounce_ms = 300.0        # 300ms debounce protection

        # Optimize PyAutoGUI for real-time cursor updates
        pyautogui.PAUSE = 0.0
        pyautogui.FAILSAFE = False

        try:
            self.screen_w, self.screen_h = pyautogui.size()
        except Exception as e:
            logger.error(f"Failed to get screen size: {e}")
            self.screen_w, self.screen_h = 1920, 1080

    def reset(self) -> None:
        """Resets the last smoothed cursor coordinates to avoid jumps."""
        self.last_x = None
        self.last_y = None

    def process_hand(self, hand_landmarks: HandLandmarks | None) -> dict:
        """
        Process the hand landmarks, move the mouse pointer, and trigger left clicks.

        Parameters:
            hand_landmarks: Detected hand landmarks object or None.

        Returns:
            dict containing cursor_x, cursor_y, tracking_state, pinch_distance,
                 click_status, click_counter, and current_action.
        """
        if not self.enabled:
            self.reset()
            if self.click_status == "LEFT_CLICK":
                try:
                    pyautogui.mouseUp()
                except Exception:
                    pass
            self.click_status = "OPEN"
            self.current_action = "None"
            return {
                "cursor_x": 0,
                "cursor_y": 0,
                "tracking_state": "Disabled",
                "pinch_distance": 0.0,
                "click_status": self.click_status,
                "click_counter": self.click_counter,
                "current_action": self.current_action
            }

        if hand_landmarks is None:
            self.reset()
            if self.click_status == "LEFT_CLICK":
                try:
                    pyautogui.mouseUp()
                except Exception:
                    pass
            self.click_status = "OPEN"
            self.current_action = "None"
            return {
                "cursor_x": 0,
                "cursor_y": 0,
                "tracking_state": "No Hand",
                "pinch_distance": 0.0,
                "click_status": self.click_status,
                "click_counter": self.click_counter,
                "current_action": self.current_action
            }

        # Landmark 8 is the index finger tip, Landmark 4 is the thumb tip
        if len(hand_landmarks.landmarks) <= 8:
            self.reset()
            if self.click_status == "LEFT_CLICK":
                try:
                    pyautogui.mouseUp()
                except Exception:
                    pass
            self.click_status = "OPEN"
            self.current_action = "None"
            return {
                "cursor_x": 0,
                "cursor_y": 0,
                "tracking_state": "No Index Tip",
                "pinch_distance": 0.0,
                "click_status": self.click_status,
                "click_counter": self.click_counter,
                "current_action": self.current_action
            }

        ix, iy, iz = hand_landmarks.landmarks[8]
        tx, ty, tz = hand_landmarks.landmarks[4]

        # Calculate 3D Euclidean distance for pinch detection
        pinch_dist = math.sqrt((ix - tx) ** 2 + (iy - ty) ** 2 + (iz - tz) ** 2)

        # Click state machine check
        now = time.monotonic() * 1000
        click_triggered = False

        if pinch_dist <= self.click_threshold:
            if self.click_status in ("OPEN", "READY"):
                if now - self.last_click_time >= self.debounce_ms:
                    try:
                        pyautogui.click()
                        click_triggered = True
                        self.click_status = "LEFT_CLICK"
                        self.click_counter += 1
                        self.last_click_time = now
                        self.current_action = "Left Click"
                        
                        from datetime import datetime
                        logger.info(
                            f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                            f"Click Event triggered: Pinch Distance = {pinch_dist:.4f}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to execute click: {e}")
                        self.click_status = "PINCH"
                        self.current_action = "Move"
                else:
                    self.click_status = "PINCH"
                    self.current_action = "Move"
            elif self.click_status == "LEFT_CLICK":
                self.click_status = "PINCH"
                self.current_action = "Move"
            else:
                self.click_status = "PINCH"
                self.current_action = "Move"
        else:
            # pinch_dist > click_threshold
            if self.click_status in ("LEFT_CLICK", "PINCH"):
                self.click_status = "RELEASE"
                self.current_action = "Move"
            else:
                self.click_status = "READY"
                self.current_action = "Move"

        # Standard Cursor Coordinate Movement Math
        # 1. Dead Zone Active Region Mapping
        # Map normalized coordinate [dead_zone, 1.0 - dead_zone] -> [0.0, 1.0]
        pad = self.dead_zone
        denom = 1.0 - 2.0 * pad
        if denom <= 0:
            denom = 0.001

        # Map X
        if ix < pad:
            nx = 0.0
        elif ix > 1.0 - pad:
            nx = 1.0
        else:
            nx = (ix - pad) / denom

        # Map Y
        if iy < pad:
            ny = 0.0
        elif iy > 1.0 - pad:
            ny = 1.0
        else:
            ny = (iy - pad) / denom

        # 2. Apply Sensitivity Centered around 0.5
        nx = (nx - 0.5) * self.sensitivity + 0.5
        ny = (ny - 0.5) * self.sensitivity + 0.5

        # Clamp mapping coordinates to screen boundaries [0, 1]
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        # 3. Scale to Full Screen Coordinates
        target_x = int(nx * self.screen_w)
        target_y = int(ny * self.screen_h)

        # 4. Apply Exponential Moving Average (EMA) Smoothing
        if self.last_x is None or self.last_y is None:
            smoothed_x = target_x
            smoothed_y = target_y
        else:
            smoothed_x = int(self.last_x + (target_x - self.last_x) * self.smoothing)
            smoothed_y = int(self.last_y + (target_y - self.last_y) * self.smoothing)

        # 5. Execute Screen Pointer Move
        try:
            pyautogui.moveTo(smoothed_x, smoothed_y)
        except Exception as e:
            logger.warning(f"Failed to move mouse: {e}")

        self.last_x = smoothed_x
        self.last_y = smoothed_y

        return {
            "cursor_x": smoothed_x,
            "cursor_y": smoothed_y,
            "tracking_state": "Tracking",
            "pinch_distance": float(round(pinch_dist, 4)),
            "click_status": self.click_status,
            "click_counter": self.click_counter,
            "current_action": self.current_action
        }
