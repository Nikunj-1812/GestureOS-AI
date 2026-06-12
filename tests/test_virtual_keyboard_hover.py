"""Unit tests for virtual keyboard landmark hover detection, smoothing, and debouncing."""

import customtkinter as ctk
import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from dashboard.pages.virtual_keyboard_page import VirtualKeyboardPage


@pytest.fixture(scope="module")
def root():
    r = ctk.CTk()
    # Withdraw to avoid displaying an actual window frame on desktop during test run
    r.withdraw()
    yield r
    r.destroy()


@dataclass
class MockHand:
    landmarks: list[tuple[float, float, float]]
    handedness: str = "Right"
    bbox: tuple[int, int, int, int] = (0, 0, 100, 100)


def test_get_key_for_widget(root):
    page = VirtualKeyboardPage(root)
    # Locate 'A' key button
    btn_a = page._alphabet_buttons["A"]
    
    # Verify resolving key name with button directly
    assert page._get_key_for_widget(btn_a) == "A"
    
    # Verify resolving key name with internal sub-widget (canvas/label)
    child = MagicMock()
    child.master = btn_a
    assert page._get_key_for_widget(child) == "A"
    
    # Verify resolving with non-button widget
    non_matching = MagicMock()
    non_matching.master = None
    assert page._get_key_for_widget(non_matching) is None


def test_set_camera_frame_hover_delay_and_debounce(root):
    page = VirtualKeyboardPage(root)
    btn_a = page._alphabet_buttons["A"]
    
    # Mock window geometry properties
    page.winfo_width = MagicMock(return_value=800)
    page.winfo_height = MagicMock(return_value=600)
    page.winfo_rootx = MagicMock(return_value=0)
    page.winfo_rooty = MagicMock(return_value=0)
    
    # Mock widget containment query
    page.winfo_containing = MagicMock(return_value=btn_a)
    
    # Set up hand landmarks pointing to the middle (index tip Landmark 8), with no middle pinch
    landmarks = [(0.0, 0.0, 0.0)] * 21
    landmarks[8] = (0.5, 0.5, 0.0)
    landmarks[12] = (0.5, 0.5, 0.0)
    landmarks[4] = (0.5, 0.5, 0.1) # distance = 0.1, no pinch
    hand = MockHand(landmarks=landmarks)
    
    # 1. First frame should set key as a candidate but not highlight it immediately (delay = 150ms)
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[hand])
    assert page._active_hovered_key is None
    assert page._candidate_key == "A"
    assert page._lbl_hover_duration.cget("text") == "0.00s"
    
    # 2. Advance candidate start time back by 200ms to simulate 200ms elapsed
    page._candidate_start_time = datetime.now() - timedelta(milliseconds=200)
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[hand])
    
    # Active hovered key should now be updated to 'A'
    assert page._active_hovered_key == "A"
    assert page._lbl_hovered.cget("text") == "A"
    
    # 3. Simulate brief hand frame drop (no hands detected)
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[])
    
    # Debounce grace period (100ms) should keep hover active
    assert page._active_hovered_key == "A"
    
    # 4. Advance last hover detection back by 150ms to simulate debounce timeout
    page._last_hover_detect_time = datetime.now() - timedelta(milliseconds=150)
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[])
    
    # Active hovered key should be cleared now
    assert page._active_hovered_key is None
    assert page._candidate_key is None
    assert page._lbl_hovered.cget("text") == "None"


def test_set_camera_frame_pinch_typing(root, monkeypatch):
    page = VirtualKeyboardPage(root)
    btn_a = page._alphabet_buttons["A"]
    
    # Mock window geometry
    page.winfo_width = MagicMock(return_value=800)
    page.winfo_height = MagicMock(return_value=600)
    page.winfo_rootx = MagicMock(return_value=0)
    page.winfo_rooty = MagicMock(return_value=0)
    
    # Mock widget containment
    page.winfo_containing = MagicMock(return_value=btn_a)
    
    # Mock winsound Beep
    beep_mock = MagicMock()
    import dashboard.pages.virtual_keyboard_page as vk_page
    monkeypatch.setattr(vk_page, "winsound", MagicMock(Beep=beep_mock))
    
    # Ensure sound is enabled
    page.enable_sound = True
    
    # Target 'A' and hover it (using hover delay bypass)
    landmarks = [(0.0, 0.0, 0.0)] * 21
    landmarks[8] = (0.5, 0.5, 0.0)  # Index tip for moving/hovering
    landmarks[12] = (0.5, 0.5, 0.0) # Middle tip (3rd finger)
    landmarks[4] = (0.5, 0.5, 0.1)  # Thumb tip (distance = 0.1, no pinch)
    hand = MockHand(landmarks=landmarks)
    
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[hand])
    page._candidate_start_time = datetime.now() - timedelta(milliseconds=200)
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[hand])
    
    assert page._active_hovered_key == "A"
    assert page._pinch_active is False
    assert page._typed_text.get("1.0", "end-1c") == ""
    
    # 1. Perform pinch: decrease distance to < 0.05
    landmarks[4] = (0.5, 0.5, 0.02) # distance = 0.02, pinch active
    hand = MockHand(landmarks=landmarks)
    
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[hand])
    
    # Keystroke should trigger, 'A' should be typed
    assert page._pinch_active is True
    assert page._typed_text.get("1.0", "end-1c") == "a"
    assert page._lbl_last_pressed.cget("text") == "A"
    assert beep_mock.call_count == 1
    
    # 2. Sustain pinch: distance remains < 0.05. Keypress should NOT repeat (single-fire check)
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[hand])
    assert page._pinch_active is True
    assert page._typed_text.get("1.0", "end-1c") == "a" # still just "a"
    assert beep_mock.call_count == 1
    
    # 3. Release pinch: distance increases to > 0.05
    landmarks[4] = (0.5, 0.5, 0.1)
    hand = MockHand(landmarks=landmarks)
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[hand])
    assert page._pinch_active is False
    assert page._typed_text.get("1.0", "end-1c") == "a"
    
    # 4. Perform second pinch to type 'a' again
    landmarks[4] = (0.5, 0.5, 0.02)
    hand = MockHand(landmarks=landmarks)
    page.set_camera_frame(frame=None, fps=30.0, detected_hands=[hand])
    assert page._pinch_active is True
    assert page._typed_text.get("1.0", "end-1c") == "aa"
    assert beep_mock.call_count == 2


def test_system_typing_pyautogui(root, monkeypatch):
    import dashboard.pages.virtual_keyboard_page as vk_page
    mock_pyautogui = MagicMock()
    monkeypatch.setattr(vk_page, "pyautogui", mock_pyautogui)

    page = VirtualKeyboardPage(root)
    # By default, system typing should be False
    assert page.system_typing_active is False

    btn_a = page._alphabet_buttons["A"]

    # 1. Press A key with system typing disabled
    page._on_key_press("A", btn_a)
    assert mock_pyautogui.write.call_count == 0
    assert mock_pyautogui.press.call_count == 0

    # 2. Enable system typing
    page.system_typing_active = True

    # Press A key: should translate and call pyautogui.write("a") since Shift/Caps is not active
    page._on_key_press("A", btn_a)
    mock_pyautogui.write.assert_called_once_with("a")
    mock_pyautogui.write.reset_mock()

    # Press Shift: should toggle shift state and call pyautogui.press("shift")
    btn_shift = page._btn_shift
    page._on_key_press("Shift", btn_shift)
    mock_pyautogui.press.assert_called_once_with("shift")
    mock_pyautogui.press.reset_mock()
    assert page.shift_active is True

    # Press A key now (with Shift active): should call pyautogui.write("A")
    page._on_key_press("A", btn_a)
    mock_pyautogui.write.assert_called_once_with("A")
    mock_pyautogui.write.reset_mock()
    # Shift should auto-release
    assert page.shift_active is False

    # Press Space: should call pyautogui.press("space")
    btn_space = page._all_buttons["Space"]
    page._on_key_press("Space", btn_space)
    mock_pyautogui.press.assert_called_once_with("space")
    mock_pyautogui.press.reset_mock()

    # Press Backspace: should call pyautogui.press("backspace")
    btn_backspace = page._all_buttons["Backspace"]
    page._on_key_press("Backspace", btn_backspace)
    mock_pyautogui.press.assert_called_once_with("backspace")
    mock_pyautogui.press.reset_mock()

