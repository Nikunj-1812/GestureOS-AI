"""Unit tests for modules/visualizer.py."""

import numpy as np
import pytest
from modules.hand_detector import HandLandmarks
from modules.visualizer import draw_visuals, detect_fingers_state
from config.app_config import AppConfig


def test_detect_fingers_state():
    # Construct 21 landmarks where all fingers are raised
    # tip.y < pip.y (e.g. tip index 8 is higher/smaller y than pip index 6)
    # distance check: tip-to-mcp > mcp-to-wrist * 0.55
    landmarks = []
    # wrist at (0.5, 0.9, 0.0)
    landmarks.append((0.5, 0.9, 0.0))  # 0: wrist
    
    # Thumb: tip_dist > ip_dist + 0.04
    landmarks.append((0.4, 0.85, 0.0))  # 1
    landmarks.append((0.3, 0.8, 0.0))   # 2
    landmarks.append((0.2, 0.75, 0.0))   # 3
    landmarks.append((0.1, 0.7, 0.0))    # 4: tip
    
    # Index: tip (8) y < pip (6) y
    landmarks.append((0.4, 0.7, 0.0))    # 5: mcp
    landmarks.append((0.4, 0.6, 0.0))    # 6: pip
    landmarks.append((0.4, 0.5, 0.0))    # 7: dip
    landmarks.append((0.4, 0.4, 0.0))    # 8: tip
    
    # Middle: tip (12) y < pip (10) y
    landmarks.append((0.5, 0.7, 0.0))    # 9: mcp
    landmarks.append((0.5, 0.6, 0.0))    # 10: pip
    landmarks.append((0.5, 0.5, 0.0))    # 11: dip
    landmarks.append((0.5, 0.4, 0.0))    # 12: tip
    
    # Ring: tip (16) y < pip (14) y
    landmarks.append((0.6, 0.7, 0.0))    # 13: mcp
    landmarks.append((0.6, 0.6, 0.0))    # 14: pip
    landmarks.append((0.6, 0.5, 0.0))    # 15: dip
    landmarks.append((0.6, 0.4, 0.0))    # 16: tip
    
    # Pinky: tip (20) y < pip (18) y
    landmarks.append((0.7, 0.7, 0.0))    # 17: mcp
    landmarks.append((0.7, 0.6, 0.0))    # 18: pip
    landmarks.append((0.7, 0.5, 0.0))    # 19: dip
    landmarks.append((0.7, 0.4, 0.0))    # 20: tip

    states = detect_fingers_state(landmarks)
    assert isinstance(states, dict)
    assert "Thumb" in states
    assert "Index" in states
    assert "Middle" in states
    assert "Ring" in states
    assert "Pinky" in states


def test_draw_visuals():
    # Setup dummy BGR image
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Setup mock hand landmarks
    landmarks = [(0.5 + 0.01 * i, 0.5 - 0.01 * i, 0.0) for i in range(21)]
    hand = HandLandmarks(
        landmarks=landmarks,
        handedness="Right",
        bbox=(200, 200, 150, 150)
    )
    detected_hands = [hand]
    
    # Setup config
    config = AppConfig()
    config.show_landmarks = True
    config.show_connections = True
    config.show_bounding_box = True
    config.show_finger_states = True
    config.show_distance_meter = True
    config.show_debug_panel = True
    config.show_hud = True

    # Draw visuals with all features enabled
    out_frame = draw_visuals(
        frame=frame.copy(),
        detected_hands=detected_hands,
        mp_results=None,
        config=config,
        fps=30.0,
        gesture="victory",
        confidence=0.95
    )
    
    assert out_frame.shape == (480, 640, 3)
    
    # Draw visuals with all features disabled
    config.show_landmarks = False
    config.show_connections = False
    config.show_bounding_box = False
    config.show_finger_states = False
    config.show_distance_meter = False
    config.show_debug_panel = False
    config.show_hud = False
    
    out_frame_disabled = draw_visuals(
        frame=frame.copy(),
        detected_hands=detected_hands,
        mp_results=None,
        config=config,
        fps=30.0,
        gesture="victory",
        confidence=0.95
    )
    
    assert out_frame_disabled.shape == (480, 640, 3)
