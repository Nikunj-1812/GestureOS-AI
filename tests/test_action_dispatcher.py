"""Unit tests for the ActionDispatcher module."""

from unittest.mock import patch
from modules.action_dispatcher import ActionDispatcher


def test_unknown_gesture_returns_false():
    import time
    dispatcher = ActionDispatcher(cooldown_ms=0)
    dispatcher._start_time = time.monotonic() - 10.0  # bypass warmup
    result = dispatcher.dispatch("nonexistent_gesture")
    assert result is False


def test_known_gesture_dispatches():
    import time
    dispatcher = ActionDispatcher(cooldown_ms=0)
    dispatcher._start_time = time.monotonic() - 10.0  # bypass warmup
    with patch("modules.action_dispatcher.pyautogui") as mock_pg:
        mock_pg.hotkey.return_value = None
        mock_pg.scroll.return_value = None
        result = dispatcher.dispatch("point_up")
    assert result is True


def test_cooldown_blocks_rapid_dispatch():
    import time
    dispatcher = ActionDispatcher(cooldown_ms=9999)
    dispatcher._start_time = time.monotonic() - 10.0  # bypass warmup
    with patch("modules.action_dispatcher.pyautogui"):
        dispatcher.dispatch("point_up")
        result = dispatcher.dispatch("point_up")
    assert result is False
