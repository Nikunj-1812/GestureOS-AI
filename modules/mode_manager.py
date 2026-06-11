"""
Central Mode Manager for GestureOS AI
=====================================
Prevents gesture conflicts by ensuring only one active mode at a time
with a defined priority order and transition cooldown.
"""

import time
from loguru import logger
from datetime import datetime

class ModeManager:
    """Manages system modes: BRIGHTNESS, VOLUME, SCROLL, CLICK, CURSOR."""

    # Priority list (highest to lowest)
    PRIORITY = ["BRIGHTNESS", "VOLUME", "SCROLL", "CLICK", "CURSOR"]

    def __init__(self, cooldown_ms: float = 300.0) -> None:
        self.cooldown_ms = cooldown_ms
        self.current_mode = "CURSOR"
        self.last_mode_change_time = 0.0  # monotonic ms

    def update_mode(
        self,
        *,
        brightness_gesture: bool,
        volume_gesture: bool,
        scroll_gesture: bool,
        click_gesture: bool,
    ) -> str:
        """
        Determines the active mode based on gesture priority and transition cooldown.
        """
        # Determine target mode based on priority
        target_mode = "CURSOR"
        if brightness_gesture:
            target_mode = "BRIGHTNESS"
        elif volume_gesture:
            target_mode = "VOLUME"
        elif scroll_gesture:
            target_mode = "SCROLL"
        elif click_gesture:
            target_mode = "CLICK"

        now = time.monotonic() * 1000  # ms

        # Check cooldown if changing mode
        if target_mode != self.current_mode:
            if now - self.last_mode_change_time >= self.cooldown_ms:
                # Logging mode change
                logger.info(
                    f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                    f"[MODE] {target_mode.title()}"
                )
                self.current_mode = target_mode
                self.last_mode_change_time = now

        return self.current_mode
