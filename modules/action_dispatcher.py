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
    "open_palm":    lambda: pyautogui.hotkey("win", "shift", "s"),      # Screenshot
    "fist":         lambda: pyautogui.hotkey("win", "l"),               # Lock screen
    "thumbs_up":    lambda: pyautogui.hotkey("volumeup"),               # Volume up
    "thumbs_down":  lambda: pyautogui.hotkey("volumedown"),             # Volume down
    "peace_sign":   lambda: pyautogui.hotkey("alt", "tab"),             # Switch window
    "point_up":     lambda: pyautogui.scroll(3),                        # Scroll up
    "point_down":   lambda: pyautogui.scroll(-3),                       # Scroll down
    "swipe_left":   lambda: pyautogui.hotkey("ctrl", "win", "left"),    # Prev desktop
    "swipe_right":  lambda: pyautogui.hotkey("ctrl", "win", "right"),   # Next desktop
}


class ActionDispatcher:
    """Dispatches OS actions from gesture labels with cooldown protection."""

    def __init__(self, cooldown_ms: int = 800) -> None:
        self._cooldown_ms = cooldown_ms
        self._last_dispatch: float = 0.0

    def dispatch(self, gesture: str) -> bool:
        """
        Executes the OS action for the given gesture label.
        Returns True if action was fired, False if on cooldown or unknown.
        """
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
