"""Unit tests for virtual keyboard UI and layout logic."""

import customtkinter as ctk
import pytest
from unittest.mock import MagicMock
from dashboard.pages.virtual_keyboard_page import VirtualKeyboardPage


@pytest.fixture(scope="module")
def root():
    r = ctk.CTk()
    # Withdraw to avoid displaying an actual window frame on desktop during test run
    r.withdraw()
    yield r
    r.destroy()


def test_keyboard_page_initialization(root):
    page = VirtualKeyboardPage(root)
    assert page.shift_active is False
    assert page.caps_lock_active is False
    assert page._lbl_hovered.cget("text") == "None"
    assert page._lbl_last_pressed.cget("text") == "None"
    assert page._lbl_fps.cget("text") == "-- FPS"
    assert page._typed_text.get("1.0", "end-1c") == ""


def test_keyboard_page_key_press_and_backspace(root):
    page = VirtualKeyboardPage(root)
    
    # Locate button element for 'A'
    btn_a = page._alphabet_buttons["A"]
    
    # Hover key
    page._on_key_hover("A")
    assert page._lbl_hovered.cget("text") == "A"
    
    # Leave key
    page._on_key_leave()
    assert page._lbl_hovered.cget("text") == "None"
    
    # Type 'a'
    page._on_key_press("A", btn_a)
    assert page._lbl_last_pressed.cget("text") == "A"
    assert page._typed_text.get("1.0", "end-1c") == "a"

    # Type 'b'
    btn_b = page._alphabet_buttons["B"]
    page._on_key_press("B", btn_b)
    assert page._typed_text.get("1.0", "end-1c") == "ab"

    # Press Space
    btn_space = MagicMock()
    page._on_key_press("Space", btn_space)
    assert page._typed_text.get("1.0", "end-1c") == "ab "

    # Press Backspace
    btn_backspace = MagicMock()
    page._on_key_press("Backspace", btn_backspace)
    assert page._typed_text.get("1.0", "end-1c") == "ab"
    
    # Clear
    page._clear_text()
    assert page._typed_text.get("1.0", "end-1c") == ""


def test_keyboard_page_modifiers(root):
    page = VirtualKeyboardPage(root)
    btn_a = page._alphabet_buttons["A"]
    btn_shift = page._btn_shift
    btn_caps = page._btn_caps

    # Toggle Shift active
    page._on_key_press("Shift", btn_shift)
    assert page.shift_active is True
    
    # Type 'A' (should be uppercase)
    page._on_key_press("A", btn_a)
    assert page._typed_text.get("1.0", "end-1c") == "A"
    
    # Shift should auto-release
    assert page.shift_active is False

    # Toggle Caps Lock active
    page._on_key_press("Caps Lock", btn_caps)
    assert page.caps_lock_active is True

    # Type 'A' again (should be uppercase)
    page._on_key_press("A", btn_a)
    assert page._typed_text.get("1.0", "end-1c") == "AA"
    
    # Caps Lock should remain active
    assert page.caps_lock_active is True


def test_keyboard_stats_and_suggestions(root):
    page = VirtualKeyboardPage(root)
    
    # Enable autocomplete/suggestions explicitly
    page.autocomplete_enabled = True
    page._update_analytics()
    
    # Initially suggestions should be empty since typed text is empty
    assert page._lbl_wpm.cget("text") == "0 WPM"
    assert page._lbl_accuracy.cget("text") == "100%"
    assert page._lbl_current_word.cget("text") == "None"
    assert page._lbl_recent_words.cget("text") == "None"
    
    # 1. Type "ges"
    btn_g = page._alphabet_buttons["G"]
    btn_e = page._alphabet_buttons["E"]
    btn_s = page._alphabet_buttons["S"]
    
    page._on_key_press("G", btn_g)
    page._on_key_press("E", btn_e)
    page._on_key_press("S", btn_s)
    
    # Verify current word is "ges"
    assert page._lbl_current_word.cget("text") == "ges"
    
    # Assert suggestion buttons are populated (should suggest "gesture")
    suggestion_texts = [btn.cget("text") for btn in page._suggestion_buttons]
    assert "gesture" in suggestion_texts
    
    # Find the index of "gesture" in the suggestions
    gesture_idx = suggestion_texts.index("gesture")
    
    # 2. Trigger autocomplete suggestion key press
    btn_suggest = page._suggestion_buttons[gesture_idx]
    page._on_key_press(f"Suggestion_{gesture_idx}", btn_suggest)
    
    # Typed text should be "gesture "
    assert page._typed_text.get("1.0", "end-1c") == "gesture "
    
    # 3. Test stats: accuracy and WPM
    # Add a backspace (simulating a correction cycle)
    btn_backspace = MagicMock()
    page._on_key_press("Backspace", btn_backspace) # backspace count becomes 1, total keystrokes is 5
    
    # Assert accuracy calculation:
    # total_keystrokes = 5 (G, E, S, Suggestion, Backspace)
    # backspace_count = 1
    # expected accuracy = (5 - 2 * 1) / 5 = 60%
    assert page.total_keystrokes == 5
    assert page.backspace_count == 1
    assert page._lbl_accuracy.cget("text") == "60%"
    
    # Clear text resets everything
    page._clear_text()
    assert page.total_keystrokes == 0
    assert page.backspace_count == 0
    assert page.typing_start_time is None
    assert page.recent_words == []

