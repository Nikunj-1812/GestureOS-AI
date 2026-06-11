"""
Validation script for BrightnessController interpolation, smoothing, and dead zone logic.
"""

import os
import sys

# Ensure modules directory is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock
from modules.brightness_controller import BrightnessController

def run_validation():
    print("=== BrightnessController Validation Started ===")
    
    # 1. Initialize with screen_brightness_control mocked to avoid system calls
    # We will test simulated mode by default
    bc = BrightnessController(
        min_distance_px=30.0,
        max_distance_px=230.0, # 200px span for easy mapping
        smoothing=0.20,
        dead_zone_pct=2.0
    )
    bc._sbc = None # Set to None to use simulated fallback mode
    
    # Force initial base level
    bc.last_brightness_pct = 50.0
    bc.last_logged_pct = 50
    bc.last_update_time = 0.0 # reset cooldown
    
    print(f"Initial State: Level={bc.get_current_brightness()}%, smoothing={bc.smoothing}")
    
    # 2. Test Interpolation (min distance -> 0%, max distance -> 100%)
    # Distance = 30px (min) -> should map raw to 0.0
    # EMA formula: last = 50.0 * 0.8 + 0.0 * 0.2 = 40.0
    val, changed = bc.update_brightness(30.0)
    print(f"Update 30px (min): value={val}%, changed={changed}")
    assert val == 40, f"Expected 40% but got {val}%"
    assert changed is True
    
    # Reset cooldown and update again with same distance:
    # last = 40.0 * 0.8 + 0.0 * 0.2 = 32.0 (change is 8%, dead zone is 2% -> updates)
    bc.last_update_time = 0.0
    val, changed = bc.update_brightness(30.0)
    print(f"Update 30px (min) again: value={val}%, changed={changed}")
    assert val == 32
    assert changed is True
    
    # 3. Test Dead Zone (changes smaller than 2% should be ignored)
    # Target value: we want a small change. Let's see:
    # Current level = 32.0.
    # If we set distance to 30.0px again:
    # raw_pct = 0.0
    # smoothed = 32.0 * 0.8 + 0.0 * 0.2 = 25.6 -> round to 26 (change of 6% -> updates)
    # Let's test a very small distance change that results in < 2% change in smoothed pct.
    # Say we want raw_pct = 30.0 (distance = 30 + 0.3 * 200 = 90px)
    # smoothed = 32.0 * 0.8 + 30.0 * 0.2 = 31.6 -> round to 32
    # Current logged is 32. Change is 0% -> ignored
    bc.last_update_time = 0.0
    val, changed = bc.update_brightness(90.0)
    print(f"Update 90px (small change): value={val}%, changed={changed}")
    assert val == 32
    assert changed is False

    # 4. Test Cooldown (within 100ms)
    # First set last_update_time to 0 to force a successful update setting it to now
    bc.last_update_time = 0.0
    val, changed = bc.update_brightness(230.0) # distance = max (100% target)
    print(f"Trigger successful update: value={val}%, changed={changed}")
    assert changed is True

    # Try updating again immediately (within 100ms) -> should be blocked by cooldown
    val2, changed2 = bc.update_brightness(30.0)
    print(f"Update within 100ms (cooldown): value={val2}%, changed={changed2}")
    assert changed2 is False
    assert val2 == val
    
    print("=== All Brightness Controller Validation Tests PASS ===")

if __name__ == "__main__":
    run_validation()
