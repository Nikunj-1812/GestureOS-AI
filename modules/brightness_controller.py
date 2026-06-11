"""
Brightness Controller Module for GestureOS AI
=============================================
Manages Windows system brightness via screen_brightness_control,
maps hand distance to brightness level, smooths adjustments, and logs changes.
"""

import time
from loguru import logger
from datetime import datetime

class BrightnessController:
    """Controls system brightness based on thumb-index distance using screen-brightness-control."""

    def __init__(
        self,
        min_distance_px: float = 30.0,
        max_distance_px: float = 250.0,
        smoothing: float = 0.15,
        dead_zone_pct: float = 2.0,  # 2% dead zone
    ) -> None:
        self.min_distance = min_distance_px
        self.max_distance = max_distance_px
        self.smoothing = smoothing
        self.dead_zone_pct = dead_zone_pct

        self.last_brightness_pct = -1.0  # Float tracking current brightness percentage
        self.last_logged_pct = -1        # Integer tracking last logged brightness percentage
        self.last_update_time = 0.0      # Monotonic ms
        self._sbc = None

        self._initialize_sbc()

    def _initialize_sbc(self) -> None:
        """Initialize the screen-brightness-control library."""
        try:
            import screen_brightness_control as sbc
            self._sbc = sbc
            # Sync initially with the current OS system brightness
            curr = sbc.get_brightness()
            if isinstance(curr, list) and len(curr) > 0:
                curr = curr[0]
            self.last_brightness_pct = float(curr)
            self.last_logged_pct = int(round(self.last_brightness_pct))
            logger.info(f"BrightnessController initialized. Synced with system brightness: {self.last_logged_pct}%")
        except Exception as e:
            logger.warning(f"Could not initialize screen-brightness-control: {e}. Fallback to simulated brightness mode.")

    def get_current_brightness(self) -> int:
        """Returns the current brightness percentage."""
        if self._sbc is not None:
            try:
                curr = self._sbc.get_brightness()
                if isinstance(curr, list) and len(curr) > 0:
                    curr = curr[0]
                self.last_brightness_pct = float(curr)
                return int(round(self.last_brightness_pct))
            except Exception:
                pass
        return int(round(max(0.0, self.last_brightness_pct)))

    def update_brightness(self, distance_px: float) -> tuple[int, bool]:
        """
        Updates the brightness based on the measured hand distance.
        
        Maps distance to brightness: min_distance -> 0%, max_distance -> 100%.
        Smooths using an Exponential Moving Average (EMA) and sets OS brightness.
        
        Returns:
            (brightness_percentage, has_changed)
        """
        now = time.monotonic() * 1000  # ms
        
        # Cooldown check: update system brightness at most once every 100ms
        if now - self.last_update_time < 100.0 and self.last_brightness_pct >= 0.0:
            return int(round(self.last_brightness_pct)), False

        # Map distance to raw brightness level [0.0, 100.0]
        if distance_px <= self.min_distance:
            raw_pct = 0.0
        elif distance_px >= self.max_distance:
            raw_pct = 100.0
        else:
            raw_pct = ((distance_px - self.min_distance) / 
                       (self.max_distance - self.min_distance)) * 100.0

        # Apply EMA smoothing
        if self.last_brightness_pct < 0.0:
            self.last_brightness_pct = raw_pct
        else:
            self.last_brightness_pct = (self.last_brightness_pct * (1.0 - self.smoothing) + 
                                        raw_pct * self.smoothing)

        # Clamp brightness level
        self.last_brightness_pct = max(0.0, min(100.0, self.last_brightness_pct))
        int_pct = int(round(self.last_brightness_pct))

        # Check dead zone (ignore changes smaller than 2%)
        if self.last_logged_pct >= 0 and abs(int_pct - self.last_logged_pct) < self.dead_zone_pct:
            return self.last_logged_pct, False

        self.last_update_time = now

        # Set system brightness using screen-brightness-control if available
        if self._sbc is not None:
            try:
                self._sbc.set_brightness(int_pct)
            except Exception as e:
                logger.error(f"Failed to set Windows system brightness: {e}")

        # Check for change to log
        changed = (int_pct != self.last_logged_pct)
        if changed:
            self.last_logged_pct = int_pct
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [BRIGHTNESS] {int_pct}%")

        return int_pct, changed
