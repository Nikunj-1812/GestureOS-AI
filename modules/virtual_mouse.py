"""
GestureOS AI — Virtual Mouse Module
===================================
Tracks index finger tip coordinates and maps them to screen movements
with dead-zone clipping, sensitivity scaling, and EMA smoothing.

Phase 3.3 — Right Click:
  Gesture : Thumb Tip (Landmark 4) + Middle Finger Tip (Landmark 12)
  State Machine: OPEN → PINCH → RIGHT_CLICK → RELEASE → READY
  Safety: single-fire per pinch, debounce protected, release required.

Phase 3.4 — Scroll Control:
  Gesture : Index Finger UP (LM 8 > LM 6) AND Middle Finger UP (LM 12 > LM 10)
  Control : Hand moves UP  → Scroll Up
            Hand moves DOWN → Scroll Down
  Safety  : Dead zone prevents accidental scrolls, adjustable sensitivity,
            EMA-smoothed scroll speed, exits when gesture changes.
"""

from __future__ import annotations

import math
import time
import pyautogui
from loguru import logger
from datetime import datetime
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
        right_click_threshold: float = 0.05,
        scroll_sensitivity: float = 5.0,
        scroll_dead_zone: float = 0.003,    # FIX: was 0.04, too large for normalized coords
        scroll_smoothing: float = 0.30,
        volume_min_distance_px: float = 30.0,
        volume_max_distance_px: float = 250.0,
        volume_smoothing: float = 0.15,
        brightness_min_distance_px: float = 30.0,
        brightness_max_distance_px: float = 250.0,
        brightness_smoothing: float = 0.15,
    ) -> None:
        self.enabled = enabled
        self.sensitivity = sensitivity
        self.dead_zone = dead_zone          # Padding fraction from camera edges [0.0, 0.35]
        self.smoothing = smoothing          # EMA coefficient alpha in [0.05, 0.5]
        self.click_threshold = click_threshold
        self.right_click_threshold = right_click_threshold  # Phase 3.3
        # Phase 3.4 scroll params
        self.scroll_sensitivity = scroll_sensitivity        # clicks per unit Y movement
        self.scroll_dead_zone = scroll_dead_zone            # min Y-delta to trigger scroll
        self.scroll_smoothing = scroll_smoothing            # EMA alpha for scroll velocity

        # Phase 3.4 volume params & controller
        from modules.volume_controller import VolumeController
        self._volume_controller = VolumeController(
            min_distance_px=volume_min_distance_px,
            max_distance_px=volume_max_distance_px,
            smoothing=volume_smoothing
        )
        self.volume_mode = False
        self.volume_level = 0
        self.volume_distance = 0.0
        self._volume_active_logged = False

        # Phase 3.5 brightness params & controller
        from modules.brightness_controller import BrightnessController
        self._brightness_controller = BrightnessController(
            min_distance_px=brightness_min_distance_px,
            max_distance_px=brightness_max_distance_px,
            smoothing=brightness_smoothing
        )
        self.brightness_mode = False
        self.brightness_level = 0
        self.brightness_distance = 0.0
        self._brightness_active_logged = False

        # Phase 3.5 mode manager
        from modules.mode_manager import ModeManager
        self._mode_manager = ModeManager(cooldown_ms=300.0)
        self.active_mode = "CURSOR"

        self.last_x: int | None = None
        self.last_y: int | None = None

        # ── Left-Click State Machine ──────────────────────────────────────
        # States: OPEN | PINCH | LEFT_CLICK | RELEASE | READY
        self.click_status = "OPEN"
        self.click_counter = 0
        self.current_action = "None"
        self.last_click_time = 0.0          # ms (time.monotonic() * 1000)
        self.debounce_ms = 300.0            # 300 ms debounce protection

        # ── Right-Click State Machine (Phase 3.3) ─────────────────────────
        # States: OPEN | PINCH | RIGHT_CLICK | RELEASE | READY
        self.right_click_status = "OPEN"
        self.right_click_counter = 0
        self.last_right_click_time = 0.0    # ms (time.monotonic() * 1000)
        self.right_debounce_ms = 300.0      # 300 ms debounce protection
        self.right_pinch_distance = 0.0     # live distance for telemetry

        # ── Scroll State Machine (Phase 3.4) ──────────────────────────────
        # States: IDLE | SCROLLING
        self.scroll_mode = False            # True while index+middle are both up
        self.scroll_direction = "NONE"      # "UP" | "DOWN" | "NONE"
        self.scroll_speed = 0.0            # smoothed scroll velocity (units/frame)
        self.scroll_counter = 0             # total scroll events fired
        self.scroll_anchor_y: float | None = None   # reference Y when scroll mode entered
        self.scroll_vel_smooth = 0.0        # EMA-smoothed Y velocity
        self._last_hand_y: float | None = None      # previous frame index-MCP Y
        self._scroll_accumulator = 0.0      # fractional scroll accumulator
        self._scroll_active_logged = False  # for start/stop logging

        # Optimize PyAutoGUI for real-time cursor updates
        pyautogui.PAUSE = 0.0
        pyautogui.FAILSAFE = False

        try:
            self.screen_w, self.screen_h = pyautogui.size()
        except Exception as e:
            logger.error(f"Failed to get screen size: {e}")
            self.screen_w, self.screen_h = 1920, 1080

    # ── Reset helpers ─────────────────────────────────────────────────────
    def reset(self) -> None:
        """Resets the last smoothed cursor coordinates to avoid jumps."""
        self.last_x = None
        self.last_y = None

    def _reset_right_click_state(self) -> None:
        """Resets the right-click state machine to OPEN (on disable / no hand)."""
        self.right_click_status = "OPEN"
        self.right_pinch_distance = 0.0

    def _reset_volume_state(self) -> None:
        """Resets volume control mode to IDLE (on disable / no hand / gesture exit)."""
        self.volume_mode = False
        self.volume_distance = 0.0
        if self._volume_controller:
            self.volume_level = self._volume_controller.get_current_volume()

    def _reset_brightness_state(self) -> None:
        """Resets brightness control mode to IDLE (on disable / no hand / gesture exit)."""
        self.brightness_mode = False
        self.brightness_distance = 0.0
        if self._brightness_controller:
            self.brightness_level = self._brightness_controller.get_current_brightness()

    def _reset_scroll_state(self) -> None:
        """Resets scroll mode to IDLE (on disable / no hand / gesture exit)."""
        self.scroll_mode = False
        self.scroll_direction = "NONE"
        self.scroll_speed = 0.0
        self.scroll_anchor_y = None
        self.scroll_vel_smooth = 0.0
        self._last_hand_y = None
        self._scroll_accumulator = 0.0

    # ── Main processing method ────────────────────────────────────────────
    def process_hand(self, hand_landmarks: HandLandmarks | None, frame_w: int = 1280, frame_h: int = 720) -> dict:
        """
        Process hand landmarks: move the cursor, trigger left/right clicks,
        and handle volume/brightness/scroll controls.
        """
        if not self.enabled:
            self.reset()
            self._reset_right_click_state()
            self._reset_scroll_state()
            self._reset_volume_state()
            self._reset_brightness_state()
            self.active_mode = "CURSOR"
            if self.click_status == "LEFT_CLICK":
                try:
                    pyautogui.mouseUp()
                except Exception:
                    pass
            self.click_status = "OPEN"
            self.current_action = "None"
            return self._build_result(0, 0, "Disabled", 0.0)

        if hand_landmarks is None:
            self.reset()
            self._reset_right_click_state()
            self._reset_scroll_state()
            self._reset_volume_state()
            self._reset_brightness_state()
            self.active_mode = "CURSOR"
            if self.click_status == "LEFT_CLICK":
                try:
                    pyautogui.mouseUp()
                except Exception:
                    pass
            self.click_status = "OPEN"
            self.current_action = "None"
            return self._build_result(0, 0, "No Hand", 0.0)

        # Need at least Landmark 20 for full finger detection
        if len(hand_landmarks.landmarks) < 21:
            self.reset()
            self._reset_right_click_state()
            self._reset_scroll_state()
            self._reset_volume_state()
            self._reset_brightness_state()
            self.active_mode = "CURSOR"
            if self.click_status == "LEFT_CLICK":
                try:
                    pyautogui.mouseUp()
                except Exception:
                    pass
            self.click_status = "OPEN"
            self.current_action = "None"
            return self._build_result(0, 0, "No Index Tip", 0.0)

        lm = hand_landmarks.landmarks

        # Key landmarks
        ix, iy, iz = lm[8]    # Index finger tip
        tx, ty, tz = lm[4]    # Thumb tip
        mx, my, mz = lm[12]   # Middle finger tip (Phase 3.3)
        # Index MCP (lm5) Y for scroll tracking
        scroll_track_y = lm[5][1]
        i_pip_y = lm[6][1]
        m_pip_y = lm[10][1]

        now = time.monotonic() * 1000  # ms

        # ── 3D Euclidean Distances ───────────────────────────────────────
        pinch_dist = math.sqrt((ix - tx) ** 2 + (iy - ty) ** 2 + (iz - tz) ** 2)
        right_pinch_dist = math.sqrt((mx - tx) ** 2 + (my - ty) ** 2 + (mz - tz) ** 2)
        self.right_pinch_distance = right_pinch_dist

        # Helper 2D distance for volume/brightness
        def _d(a_idx, b_idx):
            return math.hypot(lm[a_idx][0] - lm[b_idx][0], lm[a_idx][1] - lm[b_idx][1])
        tip_dist = _d(4, 0)
        ip_dist = _d(3, 0)
        tip_to_ip = _d(4, 3)
        thumb_up = (tip_dist > ip_dist + 0.04) and (tip_to_ip > 0.04)

        index_up = iy < i_pip_y - 0.01
        middle_up = my < m_pip_y - 0.01
        ring_up = lm[16][1] < lm[14][1] - 0.01
        pinky_up = lm[20][1] < lm[18][1] - 0.01

        # ── Gesture Definitions ──────────────────────────────────────────
        # BRIGHTNESS: Thumb, Index, Pinky UP; Middle, Ring DOWN
        brightness_gesture = thumb_up and index_up and pinky_up and not middle_up and not ring_up

        # VOLUME: Thumb, Pinky UP; Index, Middle, Ring DOWN
        volume_gesture = thumb_up and pinky_up and not index_up and not middle_up and not ring_up

        # SCROLL: Index, Middle UP; Thumb, Ring, Pinky DOWN
        scroll_gesture = index_up and middle_up and not thumb_up and not pinky_up and not ring_up

        # CLICK: Left click or Right click pinch active
        click_gesture = (pinch_dist <= self.click_threshold) or (right_pinch_dist <= self.right_click_threshold)

        # Update mode manager
        active_mode = self._mode_manager.update_mode(
            brightness_gesture=brightness_gesture,
            volume_gesture=volume_gesture,
            scroll_gesture=scroll_gesture,
            click_gesture=click_gesture,
        )
        self.active_mode = active_mode

        # Safety: release left click if we transitioned out of CLICK mode
        if active_mode != "CLICK" and self.click_status == "LEFT_CLICK":
            try:
                pyautogui.mouseUp()
            except Exception:
                pass
            self.click_status = "OPEN"

        # ── Mode Routing Execution ───────────────────────────────────────
        if active_mode == "BRIGHTNESS":
            self.brightness_mode = True
            self.volume_mode = False
            self.scroll_mode = False
            self._reset_right_click_state()
            self._reset_scroll_state()
            self._reset_volume_state()

            # Measure distance
            tx_px, ty_px = lm[4][0] * frame_w, lm[4][1] * frame_h
            ix_px, iy_px = lm[8][0] * frame_w, lm[8][1] * frame_h
            self.brightness_distance = math.hypot(tx_px - ix_px, ty_px - iy_px)

            if self._brightness_controller:
                self.brightness_level, _ = self._brightness_controller.update_brightness(self.brightness_distance)
            self.current_action = f"Brightness {self.brightness_level}%"

        elif active_mode == "VOLUME":
            self.volume_mode = True
            self.brightness_mode = False
            self.scroll_mode = False
            self._reset_right_click_state()
            self._reset_scroll_state()
            self._reset_brightness_state()

            # Measure distance
            tx_px, ty_px = lm[4][0] * frame_w, lm[4][1] * frame_h
            px_px, py_px = lm[20][0] * frame_w, lm[20][1] * frame_h
            self.volume_distance = math.hypot(tx_px - px_px, ty_px - py_px)

            if self._volume_controller:
                self.volume_level, _ = self._volume_controller.update_volume(self.volume_distance)
            self.current_action = f"Volume {self.volume_level}%"

        elif active_mode == "SCROLL":
            self.scroll_mode = True
            self.brightness_mode = False
            self.volume_mode = False
            self._reset_right_click_state()
            self._reset_volume_state()
            self._reset_brightness_state()

            if not self._scroll_active_logged:
                # Entering scroll mode
                self.scroll_anchor_y = scroll_track_y
                self._last_hand_y = scroll_track_y
                self.scroll_vel_smooth = 0.0
                self._scroll_accumulator = 0.0
                self._scroll_active_logged = True
                self.current_action = "Scroll"
            else:
                if self._last_hand_y is not None:
                    raw_dy = scroll_track_y - self._last_hand_y
                else:
                    raw_dy = 0.0

                self.scroll_vel_smooth = (
                    self.scroll_vel_smooth * (1.0 - self.scroll_smoothing)
                    + raw_dy * self.scroll_smoothing
                )

                if abs(self.scroll_vel_smooth) > self.scroll_dead_zone:
                    self._scroll_accumulator += -self.scroll_vel_smooth * self.scroll_sensitivity * 200
                    scroll_amount = int(self._scroll_accumulator)
                    self._scroll_accumulator -= scroll_amount

                    if scroll_amount != 0:
                        try:
                            pyautogui.scroll(scroll_amount)
                            self.scroll_counter += 1
                            direction = "UP" if scroll_amount > 0 else "DOWN"
                            self.scroll_direction = direction
                            self.scroll_speed = abs(self.scroll_vel_smooth * self.scroll_sensitivity * 200)
                            self.current_action = f"Scroll {direction}"
                        except Exception as e:
                            logger.error(f"Failed to execute scroll: {e}")
                else:
                    self.scroll_direction = "NONE"
                    self.scroll_speed = 0.0

                self._last_hand_y = scroll_track_y

        elif active_mode == "CLICK":
            self.brightness_mode = False
            self.volume_mode = False
            self.scroll_mode = False
            self._reset_scroll_state()
            self._reset_volume_state()
            self._reset_brightness_state()

            # Left Click State Machine
            if pinch_dist <= self.click_threshold:
                if self.click_status in ("OPEN", "READY"):
                    if now - self.last_click_time >= self.debounce_ms:
                        try:
                            pyautogui.click()
                            self.click_status = "LEFT_CLICK"
                            self.click_counter += 1
                            self.last_click_time = now
                            self.current_action = "Left Click"
                            logger.info(
                                f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                                f"Left Click triggered | Pinch={pinch_dist:.4f} | "
                                f"Count={self.click_counter}"
                            )
                        except Exception as e:
                            logger.error(f"Failed to execute left click: {e}")
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
                if self.click_status in ("LEFT_CLICK", "PINCH"):
                    self.click_status = "RELEASE"
                    self.current_action = "Move"
                else:
                    self.click_status = "READY"
                    self.current_action = "Move"

            # Right Click State Machine
            if right_pinch_dist <= self.right_click_threshold and pinch_dist > self.click_threshold:
                if self.right_click_status in ("OPEN", "READY"):
                    if now - self.last_right_click_time >= self.right_debounce_ms:
                        try:
                            pyautogui.rightClick()
                            self.right_click_status = "RIGHT_CLICK"
                            self.right_click_counter += 1
                            self.last_right_click_time = now
                            self.current_action = "Right Click"
                            logger.info(
                                f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                                f"Right Click triggered | gesture=thumb_middle_pinch | "
                                f"RightPinch={right_pinch_dist:.4f} | "
                                f"Count={self.right_click_counter}"
                            )
                        except Exception as e:
                            logger.error(f"Failed to execute right click: {e}")
                            self.right_click_status = "PINCH"
                    else:
                        self.right_click_status = "PINCH"
                elif self.right_click_status == "RIGHT_CLICK":
                    self.right_click_status = "PINCH"
                else:
                    self.right_click_status = "PINCH"
            else:
                if self.right_click_status in ("RIGHT_CLICK", "PINCH"):
                    self.right_click_status = "RELEASE"
                else:
                    self.right_click_status = "READY"
                    if self.current_action == "Right Click":
                        self.current_action = "Move"

        else:
            self.brightness_mode = False
            self.volume_mode = False
            self.scroll_mode = False
            self._reset_scroll_state()
            self._reset_volume_state()
            self._reset_brightness_state()
            self._reset_right_click_state()
            self.click_status = "READY"
            self.right_click_status = "READY"
            self.current_action = "Move"

        # ── Cursor Coordinate Movement Math ───────────────────────────────
        pad = self.dead_zone
        denom = 1.0 - 2.0 * pad
        if denom <= 0:
            denom = 0.001

        if ix < pad:
            nx = 0.0
        elif ix > 1.0 - pad:
            nx = 1.0
        else:
            nx = (ix - pad) / denom

        if iy < pad:
            ny = 0.0
        elif iy > 1.0 - pad:
            ny = 1.0
        else:
            ny = (iy - pad) / denom

        nx = (nx - 0.5) * self.sensitivity + 0.5
        ny = (ny - 0.5) * self.sensitivity + 0.5
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        target_x = int(nx * self.screen_w)
        target_y = int(ny * self.screen_h)

        if self.last_x is None or self.last_y is None:
            smoothed_x = target_x
            smoothed_y = target_y
        else:
            smoothed_x = int(self.last_x + (target_x - self.last_x) * self.smoothing)
            smoothed_y = int(self.last_y + (target_y - self.last_y) * self.smoothing)

        # Move cursor only in CURSOR or CLICK modes
        if active_mode in ("CURSOR", "CLICK"):
            try:
                pyautogui.moveTo(smoothed_x, smoothed_y)
            except Exception as e:
                logger.warning(f"Failed to move mouse: {e}")

        self.last_x = smoothed_x
        self.last_y = smoothed_y

        return self._build_result(smoothed_x, smoothed_y, "Tracking", pinch_dist)

    # ── Internal Helper ───────────────────────────────────────────────────
    def _build_result(
        self,
        cursor_x: int,
        cursor_y: int,
        tracking_state: str,
        pinch_distance: float,
    ) -> dict:
        """Build the standard telemetry dict returned by process_hand."""
        return {
            "cursor_x": cursor_x,
            "cursor_y": cursor_y,
            "tracking_state": tracking_state,
            "pinch_distance": float(round(pinch_distance, 4)),
            "click_status": self.click_status,
            "click_counter": self.click_counter,
            "current_action": self.current_action,
            "active_mode": self.active_mode,
            # Phase 3.3 — Right Click telemetry
            "right_click_status": self.right_click_status,
            "right_click_counter": self.right_click_counter,
            "right_pinch_distance": float(round(self.right_pinch_distance, 4)),
            # Phase 3.4 — Scroll telemetry
            "scroll_mode": self.scroll_mode,
            "scroll_direction": self.scroll_direction,
            "scroll_speed": float(round(self.scroll_speed, 3)),
            "scroll_counter": self.scroll_counter,
            # Phase 3.4 — Volume telemetry
            "volume_mode": self.volume_mode,
            "volume_level": self.volume_level,
            "volume_distance": float(round(self.volume_distance, 2)),
            # Phase 3.5 — Brightness telemetry
            "brightness_mode": self.brightness_mode,
            "brightness_level": self.brightness_level,
            "brightness_distance": float(round(self.brightness_distance, 2)),
        }
