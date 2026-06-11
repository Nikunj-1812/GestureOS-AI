"""Unit tests for modules/virtual_mouse.py."""

import math
import time
import pytest
from unittest.mock import MagicMock, patch
from modules.virtual_mouse import VirtualMouse
from modules.hand_detector import HandLandmarks


def _make_hand(landmarks):
    """Helper to build a HandLandmarks object from a list of (x, y, z) tuples."""
    return HandLandmarks(landmarks=landmarks, handedness="Right", bbox=(0, 0, 100, 100))


def _default_landmarks():
    """Create 21 landmarks at center, all fingers touching (pinch-safe)."""
    return [(0.5, 0.5, 0.0) for _ in range(21)]


# ──────────────────────────────────────────────────────────────────
# Basic movement tests (updated to use dict return)
# ──────────────────────────────────────────────────────────────────

def test_virtual_mouse_disabled():
    vm = VirtualMouse(enabled=False)
    mock_landmarks = _default_landmarks()
    hand = _make_hand(mock_landmarks)
    result = vm.process_hand(hand)
    assert result["tracking_state"] == "Disabled"
    assert result["cursor_x"] == 0
    assert result["cursor_y"] == 0


def test_virtual_mouse_no_hand():
    vm = VirtualMouse(enabled=True)
    result = vm.process_hand(None)
    assert result["tracking_state"] == "No Hand"
    assert result["cursor_x"] == 0
    assert result["cursor_y"] == 0


def test_virtual_mouse_no_index_tip():
    vm = VirtualMouse(enabled=True)
    # Hand with only 5 landmarks (less than index tip index 8)
    mock_landmarks = [(0.5, 0.5, 0.0) for _ in range(5)]
    hand = _make_hand(mock_landmarks)
    result = vm.process_hand(hand)
    assert result["tracking_state"] == "No Index Tip"
    assert result["cursor_x"] == 0
    assert result["cursor_y"] == 0


@patch("modules.virtual_mouse.pyautogui")
def test_virtual_mouse_coordinate_mapping(mock_pyautogui):
    mock_pyautogui.size.return_value = (1920, 1080)
    vm = VirtualMouse(enabled=True, sensitivity=1.0, dead_zone=0.15, smoothing=1.0)
    vm.screen_w = 1920
    vm.screen_h = 1080

    # Test center mapping (0.5, 0.5)
    mock_landmarks = _default_landmarks()
    hand = _make_hand(mock_landmarks)
    result = vm.process_hand(hand)
    assert result["tracking_state"] == "Tracking"
    assert result["cursor_x"] == 960  # 1920 * 0.5
    assert result["cursor_y"] == 540  # 1080 * 0.5

    # Test left boundary (ix <= dead_zone)
    vm.reset()
    mock_landmarks = _default_landmarks()
    mock_landmarks[8] = (0.1, 0.5, 0.0)
    hand = _make_hand(mock_landmarks)
    result = vm.process_hand(hand)
    assert result["cursor_x"] == 0
    assert result["cursor_y"] == 540

    # Test right boundary (ix >= 1 - dead_zone)
    vm.reset()
    mock_landmarks = _default_landmarks()
    mock_landmarks[8] = (0.9, 0.5, 0.0)
    hand = _make_hand(mock_landmarks)
    result = vm.process_hand(hand)
    assert result["cursor_x"] == 1920
    assert result["cursor_y"] == 540


@patch("modules.virtual_mouse.pyautogui")
def test_virtual_mouse_sensitivity_and_clamping(mock_pyautogui):
    mock_pyautogui.size.return_value = (1000, 1000)
    vm = VirtualMouse(enabled=True, sensitivity=2.0, dead_zone=0.0, smoothing=1.0)
    vm.screen_w = 1000
    vm.screen_h = 1000

    # Center mapping should still map to center: (0.5 - 0.5) * 2 + 0.5 = 0.5
    mock_landmarks = _default_landmarks()
    hand = _make_hand(mock_landmarks)
    result = vm.process_hand(hand)
    assert result["cursor_x"] == 500
    assert result["cursor_y"] == 500

    # Off-center: ix = 0.75 -> nx = (0.75 - 0.5) * 2.0 + 0.5 = 1.0 (right edge)
    vm.reset()
    mock_landmarks = _default_landmarks()
    mock_landmarks[8] = (0.75, 0.5, 0.0)
    hand = _make_hand(mock_landmarks)
    result = vm.process_hand(hand)
    assert result["cursor_x"] == 1000

    # Clamping: ix = 0.9 -> nx = (0.9 - 0.5) * 2.0 + 0.5 = 1.3 -> clamped to 1.0
    vm.reset()
    mock_landmarks = _default_landmarks()
    mock_landmarks[8] = (0.9, 0.5, 0.0)
    hand = _make_hand(mock_landmarks)
    result = vm.process_hand(hand)
    assert result["cursor_x"] == 1000


@patch("modules.virtual_mouse.pyautogui")
def test_virtual_mouse_ema_smoothing(mock_pyautogui):
    mock_pyautogui.size.return_value = (1000, 1000)
    vm = VirtualMouse(enabled=True, sensitivity=1.0, dead_zone=0.0, smoothing=0.20)
    vm.screen_w = 1000
    vm.screen_h = 1000

    # First update: last_x is None, should immediately jump to target
    mock_landmarks = _default_landmarks()
    mock_landmarks[8] = (0.6, 0.6, 0.0)
    hand = _make_hand(mock_landmarks)
    r1 = vm.process_hand(hand)
    assert r1["cursor_x"] == 600
    assert r1["cursor_y"] == 600

    # Second update: target at 700, smoothed = 600 + (700 - 600) * 0.20 = 620
    mock_landmarks = _default_landmarks()
    mock_landmarks[8] = (0.7, 0.7, 0.0)
    hand = _make_hand(mock_landmarks)
    r2 = vm.process_hand(hand)
    assert r2["cursor_x"] == 620
    assert r2["cursor_y"] == 620

    # Reset should clear history
    vm.reset()
    assert vm.last_x is None
    assert vm.last_y is None


# ──────────────────────────────────────────────────────────────────
# Click State Machine Tests
# ──────────────────────────────────────────────────────────────────

def test_pinch_distance_calculation():
    """Verify Euclidean 3D distance between thumb (lm 4) and index (lm 8)."""
    vm = VirtualMouse(enabled=True, click_threshold=0.05)
    lm = _default_landmarks()
    # Place thumb at (0.1, 0.1, 0.0) and index at (0.1, 0.1, 0.0) → distance = 0.0
    lm[4] = (0.1, 0.1, 0.0)
    lm[8] = (0.1, 0.1, 0.0)
    hand = _make_hand(lm)
    result = vm.process_hand(hand)
    assert result["pinch_distance"] == 0.0

    # Reset, put thumb at (0.1, 0.1, 0.0) and index at (0.2, 0.1, 0.0) → dist = 0.1
    vm.reset()
    vm.click_status = "OPEN"
    lm = _default_landmarks()
    lm[4] = (0.1, 0.1, 0.0)
    lm[8] = (0.2, 0.1, 0.0)
    hand = _make_hand(lm)
    result = vm.process_hand(hand)
    assert abs(result["pinch_distance"] - 0.1) < 0.001


@patch("modules.virtual_mouse.pyautogui")
def test_click_state_machine_transitions(mock_pyautogui):
    """Test: OPEN → PINCH (on first pinch trigger) → LEFT_CLICK → RELEASE → READY."""
    mock_pyautogui.size.return_value = (1920, 1080)
    vm = VirtualMouse(enabled=True, click_threshold=0.05, sensitivity=1.0, dead_zone=0.0, smoothing=1.0)
    vm.screen_w = 1920
    vm.screen_h = 1080
    vm.debounce_ms = 0  # Disable debounce for test

    # Initial state
    assert vm.click_status == "OPEN"
    assert vm.click_counter == 0

    # Pinch close (distance < threshold) → triggers click
    lm = _default_landmarks()
    lm[4] = (0.5, 0.5, 0.0)
    lm[8] = (0.5, 0.5, 0.0)
    hand = _make_hand(lm)
    r = vm.process_hand(hand)
    assert r["click_status"] == "LEFT_CLICK"
    assert r["click_counter"] == 1
    assert r["current_action"] == "Left Click"
    mock_pyautogui.click.assert_called_once()

    # Fingers still close → transitions to PINCH (no second click)
    mock_pyautogui.click.reset_mock()
    r2 = vm.process_hand(hand)
    assert r2["click_status"] == "PINCH"
    assert r2["click_counter"] == 1  # No additional click
    mock_pyautogui.click.assert_not_called()

    # Open fingers (release) → RELEASE
    lm_open = _default_landmarks()
    lm_open[4] = (0.1, 0.1, 0.0)
    lm_open[8] = (0.9, 0.9, 0.0)
    hand_open = _make_hand(lm_open)
    r3 = vm.process_hand(hand_open)
    assert r3["click_status"] == "RELEASE"

    # Stay open → READY
    r4 = vm.process_hand(hand_open)
    assert r4["click_status"] == "READY"


@patch("modules.virtual_mouse.pyautogui")
def test_single_trigger_per_pinch(mock_pyautogui):
    """Ensure only ONE click fires per pinch, even with many frames."""
    mock_pyautogui.size.return_value = (1920, 1080)
    vm = VirtualMouse(enabled=True, click_threshold=0.05)
    vm.screen_w = 1920
    vm.screen_h = 1080
    vm.debounce_ms = 0

    # Pinch close
    lm = _default_landmarks()
    lm[4] = (0.5, 0.5, 0.0)
    lm[8] = (0.5, 0.5, 0.0)
    hand = _make_hand(lm)

    # Process 10 frames with pinch closed
    for _ in range(10):
        vm.process_hand(hand)

    # Should have triggered exactly 1 click
    assert vm.click_counter == 1
    assert mock_pyautogui.click.call_count == 1


@patch("modules.virtual_mouse.pyautogui")
def test_debounce_protection(mock_pyautogui):
    """Verify that debounce prevents rapid clicks."""
    mock_pyautogui.size.return_value = (1920, 1080)
    vm = VirtualMouse(enabled=True, click_threshold=0.05)
    vm.screen_w = 1920
    vm.screen_h = 1080
    vm.debounce_ms = 300  # 300ms debounce

    lm_close = _default_landmarks()
    lm_close[4] = (0.5, 0.5, 0.0)
    lm_close[8] = (0.5, 0.5, 0.0)
    hand_close = _make_hand(lm_close)

    lm_open = _default_landmarks()
    lm_open[4] = (0.1, 0.1, 0.0)
    lm_open[8] = (0.9, 0.9, 0.0)
    hand_open = _make_hand(lm_open)

    # First click
    vm.process_hand(hand_close)
    assert vm.click_counter == 1

    # Release
    vm.process_hand(hand_open)
    vm.process_hand(hand_open)

    # Try to click again immediately (within debounce window)
    vm.process_hand(hand_close)
    assert vm.click_counter == 1  # Should NOT increment due to debounce


@patch("modules.virtual_mouse.pyautogui")
def test_emergency_release_on_none_hand(mock_pyautogui):
    """When hand is lost during a click, ensure mouseUp is called."""
    mock_pyautogui.size.return_value = (1920, 1080)
    vm = VirtualMouse(enabled=True, click_threshold=0.05)
    vm.screen_w = 1920
    vm.screen_h = 1080
    vm.debounce_ms = 0

    # Trigger a click
    lm = _default_landmarks()
    lm[4] = (0.5, 0.5, 0.0)
    lm[8] = (0.5, 0.5, 0.0)
    hand = _make_hand(lm)
    vm.process_hand(hand)
    assert vm.click_status == "LEFT_CLICK"

    # Hand lost
    result = vm.process_hand(None)
    mock_pyautogui.mouseUp.assert_called_once()
    assert result["click_status"] == "OPEN"
    assert result["tracking_state"] == "No Hand"


def test_return_dict_structure():
    """Verify process_hand returns all expected keys."""
    vm = VirtualMouse(enabled=True)
    result = vm.process_hand(None)
    expected_keys = {
        "cursor_x", "cursor_y", "tracking_state",
        "pinch_distance", "click_status", "click_counter", "current_action",
        "right_click_status", "right_click_counter", "right_pinch_distance",
        "scroll_mode", "scroll_direction", "scroll_speed", "scroll_counter",
        "volume_mode", "volume_level", "volume_distance",
        "active_mode", "brightness_mode", "brightness_level", "brightness_distance"
    }
    assert set(result.keys()) == expected_keys


def test_volume_gesture_activation():
    """Verify that volume mode is activated when only thumb and pinky are extended."""
    vm = VirtualMouse(enabled=True)
    # Set all fingers folded (Y coordinates below PIP joints)
    lm = [(0.5, 0.5, 0.0) for _ in range(21)]
    # Set PIP joints Y
    lm[3] = (0.5, 0.5, 0.0) # thumb IP
    lm[6] = (0.5, 0.5, 0.0) # index PIP
    lm[10] = (0.5, 0.5, 0.0) # middle PIP
    lm[14] = (0.5, 0.5, 0.0) # ring PIP
    lm[18] = (0.5, 0.5, 0.0) # pinky PIP

    # Fold Index, Middle, Ring
    lm[8] = (0.5, 0.6, 0.0)   # Index tip below PIP
    lm[12] = (0.5, 0.6, 0.0)  # Middle tip below PIP
    lm[16] = (0.5, 0.6, 0.0)  # Ring tip below PIP

    # Extend Pinky (tip Y < PIP Y)
    lm[20] = (0.5, 0.4, 0.0)

    # Extend Thumb (distance tip-wrist > IP-wrist + 0.04)
    # Wrist is at 0: (0.5, 0.9, 0.0)
    lm[0] = (0.5, 0.9, 0.0)   # Wrist
    lm[3] = (0.5, 0.7, 0.0)   # IP
    lm[4] = (0.5, 0.6, 0.0)   # Tip

    hand = _make_hand(lm)
    result = vm.process_hand(hand, frame_w=1000, frame_h=1000)
    assert result["volume_mode"] is True
    assert result["current_action"].startswith("Volume")


def test_mode_manager_priority_and_cooldown():
    from modules.mode_manager import ModeManager
    mm = ModeManager(cooldown_ms=300.0)
    assert mm.current_mode == "CURSOR"

    # Priority Test: If multiple gestures are active, higher priority wins
    # BRIGHTNESS > VOLUME > SCROLL > CLICK > CURSOR
    mode = mm.update_mode(brightness_gesture=True, volume_gesture=True, scroll_gesture=True, click_gesture=True)
    assert mode == "BRIGHTNESS"
    assert mm.current_mode == "BRIGHTNESS"

    # Cooldown Test: Try to switch immediately to VOLUME (should be blocked by 300ms cooldown)
    mode2 = mm.update_mode(brightness_gesture=False, volume_gesture=True, scroll_gesture=False, click_gesture=False)
    assert mode2 == "BRIGHTNESS"

    # Advance time by resetting last_mode_change_time
    mm.last_mode_change_time = 0.0
    mode3 = mm.update_mode(brightness_gesture=False, volume_gesture=True, scroll_gesture=False, click_gesture=False)
    assert mode3 == "VOLUME"
    assert mm.current_mode == "VOLUME"


def test_brightness_gesture_activation():
    vm = VirtualMouse(enabled=True)
    # Set all fingers folded (Y coordinates below PIP joints)
    lm = [(0.5, 0.5, 0.0) for _ in range(21)]
    # Set PIP joints Y
    lm[3] = (0.5, 0.5, 0.0) # thumb IP
    lm[6] = (0.5, 0.5, 0.0) # index PIP
    lm[10] = (0.5, 0.5, 0.0) # middle PIP
    lm[14] = (0.5, 0.5, 0.0) # ring PIP
    lm[18] = (0.5, 0.5, 0.0) # pinky PIP

    # Fold Middle, Ring
    lm[12] = (0.5, 0.6, 0.0)  # Middle tip Y below PIP Y
    lm[16] = (0.5, 0.6, 0.0)  # Ring tip Y below PIP Y

    # Extend Index (tip Y < PIP Y)
    lm[8] = (0.5, 0.4, 0.0)

    # Extend Pinky (tip Y < PIP Y)
    lm[20] = (0.5, 0.4, 0.0)

    # Extend Thumb (distance tip-wrist > IP-wrist + 0.04)
    lm[0] = (0.5, 0.9, 0.0)   # Wrist Y
    lm[3] = (0.5, 0.7, 0.0)   # IP Y
    lm[4] = (0.5, 0.6, 0.0)   # Tip Y

    hand = _make_hand(lm)
    # Bypass WMI setting/getting by forcing a mock sbc
    with patch("screen_brightness_control.get_brightness", return_value=[50]) as mock_get, \
         patch("screen_brightness_control.set_brightness") as mock_set:
        # Re-initialize sbc inside controller to bind mock
        vm._brightness_controller._initialize_sbc()
        result = vm.process_hand(hand, frame_w=1000, frame_h=1000)
        assert result["brightness_mode"] is True
        assert result["current_action"].startswith("Brightness")

