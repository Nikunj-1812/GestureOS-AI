"""
GestureOS AI — Action Dispatcher
Maps recognized gesture labels to OS-level actions.
"""

from __future__ import annotations
import time

import pyautogui
from loguru import logger


# Gesture label → callable action
ACTION_MAP: dict[str, callable] = {
    "fist":         lambda: pyautogui.hotkey("win", "l"),               # Lock screen
    "thumbs_up":    lambda: pyautogui.hotkey("volumeup"),               # Volume up
    "thumbs_down":  lambda: pyautogui.hotkey("volumedown"),             # Volume down
    "peace_sign":   lambda: pyautogui.hotkey("alt", "tab"),             # Switch window
    "point_up":     lambda: pyautogui.scroll(3),                        # Scroll up
    "point_down":   lambda: pyautogui.scroll(-3),                       # Scroll down
    "swipe_left":   lambda: pyautogui.hotkey("ctrl", "win", "left"),    # Prev desktop
    "swipe_right":  lambda: pyautogui.hotkey("ctrl", "win", "right"),   # Next desktop
}

# How long (seconds) after startup before any action can be dispatched.
# This prevents stray gesture detections during camera/model warmup from
# firing hotkeys (the source of the '|' ghost-keystroke bug).
_STARTUP_WARMUP_S = 3.0


class ActionDispatcher:
    """Dispatches OS actions from gesture labels with cooldown protection."""

    def __init__(self, cooldown_ms: int = 1500) -> None:
        self._cooldown_ms = cooldown_ms
        self._last_dispatch: float = 0.0
        self._start_time: float = time.monotonic()   # track process start

    def dispatch(self, gesture: str, virtual_mouse_active: bool = False) -> bool:
        """
        Executes the OS action for the given gesture label.

        Parameters:
            gesture: Recognized gesture label.
            virtual_mouse_active: When True, action dispatch is suppressed
                so VM hand gestures don't accidentally trigger global hotkeys.

        Returns:
            True if action was fired, False otherwise.
        """
        # ── Safety guard 1: startup warmup ──────────────────────────────
        elapsed = time.monotonic() - self._start_time
        if elapsed < _STARTUP_WARMUP_S:
            return False   # silently ignore during warmup

        # ── Safety guard 2: virtual mouse is active ──────────────────────
        if virtual_mouse_active:
            return False   # VM gestures must not fire global hotkeys

        # ── Cooldown check ───────────────────────────────────────────────
        now = time.monotonic() * 1000
        if now - self._last_dispatch < self._cooldown_ms:
            return False

        action = ACTION_MAP.get(gesture)
        if action is None:
            return False

        try:
            action()
            self._last_dispatch = now
            logger.info(f"Action dispatched for gesture: '{gesture}'")
            return True
        except Exception as exc:
            logger.error(f"Failed to dispatch action for '{gesture}': {exc}")
            return False
