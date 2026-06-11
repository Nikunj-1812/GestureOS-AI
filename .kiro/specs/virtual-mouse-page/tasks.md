# Tasks — Virtual Mouse Page

## Task List

- [ ] 1. Verify page initialisation against SettingsState (Req 1)
  - [ ] 1.1 Confirm `_build_controls` reads all 6 keys from SettingsState and sets widgets
  - [ ] 1.2 Confirm `_sync_badge` is called with the correct initial enabled value
  - [ ] 1.3 Confirm no-SettingsManager path uses `_DEFAULTS` values for all widgets

- [ ] 2. Verify Enable/Disable toggle behaviour (Req 2)
  - [ ] 2.1 Confirm `_on_toggle` stages `virtual_mouse_enabled` to `_pending` and calls `_sync_badge`
  - [ ] 2.2 Confirm toggle interaction alone does NOT call `settings_manager.save()`

- [ ] 3. Verify Sensitivity slider (Req 3)
  - [ ] 3.1 Confirm slider is configured with `from_=0.5`, `to=3.0`, `number_of_steps=25`
  - [ ] 3.2 Confirm `_on_sens` updates label to `"Sensitivity:  {val:.2f}×"` and stages the value

- [ ] 4. Verify Smoothing slider (Req 4)
  - [ ] 4.1 Confirm slider is configured with `from_=0.05`, `to=0.50`, `number_of_steps=18`
  - [ ] 4.2 Confirm `_on_smooth` updates label to `"Smoothing:  {val:.2f}"` and stages the value

- [ ] 5. Verify Click Threshold slider (Req 5)
  - [ ] 5.1 Confirm slider is configured with `from_=0.01`, `to=0.15`, `number_of_steps=28`
  - [ ] 5.2 Confirm `_on_click_thresh` updates label to `"Click Threshold:  {val:.3f}"` and stages the value

- [ ] 6. Verify Scroll Sensitivity slider (Req 6)
  - [ ] 6.1 Confirm slider is configured with `from_=1.0`, `to=10.0`, `number_of_steps=18`
  - [ ] 6.2 Confirm `_on_scroll_sens` updates label to `"Scroll Sensitivity:  {val:.1f}×"` and stages the value

- [ ] 7. Verify Drag Threshold slider (Req 7)
  - [ ] 7.1 Confirm slider is configured with `from_=150.0`, `to=1000.0`, `number_of_steps=17`
  - [ ] 7.2 Confirm `_on_drag_thresh` updates label to `"Drag Threshold:  {val:.0f} ms"` and stages the value

- [ ] 8. Verify Live Telemetry display (Req 8)
  - [ ] 8.1 Confirm all five keys exist in `_tele_labels` after construction
  - [ ] 8.2 Confirm `set_camera_frame` with `tracking_state="Tracking"` shows `"{x} , {y}"` in cursor field
  - [ ] 8.3 Confirm `set_camera_frame` with any other tracking_state shows `"-- , --"`
  - [ ] 8.4 Confirm FPS field shows `"{fps:.1f} FPS"` when fps > 0, and `"-- FPS"` when fps == 0
  - [ ] 8.5 Confirm gesture field shows `"—"` for `"unknown"`, `""`, and `None`; otherwise shows the gesture string
  - [ ] 8.6 Confirm action field shows `current_action` when non-empty/non-None, otherwise shows `active_mode`
  - [ ] 8.7 Confirm `clear_camera_frame()` resets all five fields to idle defaults

- [ ] 9. Verify Reset Settings (Req 9)
  - [ ] 9.1 Confirm `_on_reset` calls `_apply_values(_DEFAULTS)` and clears `_pending`
  - [ ] 9.2 Confirm Reset does NOT call `settings_manager.save()`
  - [ ] 9.3 Confirm Status Badge and all slider labels reflect `_DEFAULTS` after Reset

- [ ] 10. Verify Save Settings (Req 10)
  - [ ] 10.1 Confirm `_on_save` with non-empty `_pending` calls `update(**_pending)` then `save()`
  - [ ] 10.2 Confirm `_on_save` with empty `_pending` calls `_stage_all()` first
  - [ ] 10.3 Confirm `on_settings_changed` callback is invoked with a `SettingsState` snapshot after save
  - [ ] 10.4 Confirm `_pending` is empty after a successful save

- [ ] 11. Write unit tests for VirtualMousePage (Req 1–10, 12)
  - File: `tests/test_virtual_mouse_page.py`
  - [ ] 11.1 Test: page without SettingsManager uses `_DEFAULTS` for all widgets
  - [ ] 11.2 Test: each slider's `from_`, `to`, and `number_of_steps` are correct
  - [ ] 11.3 Test: all five telemetry keys exist in `_tele_labels`
  - [ ] 11.4 Test: `clear_camera_frame()` resets all telemetry labels to idle values
  - [ ] 11.5 Test: stage changes + `_on_reset()` → widgets = `_DEFAULTS`, `_pending == {}`
  - [ ] 11.6 Test: `_on_save()` with empty `_pending` takes the `_stage_all` path
  - [ ] 11.7 Test: `on_settings_changed` mock is called with `SettingsState` after save
  - [ ] 11.8 Test: `settings_manager.save()` writes all expected VM keys to JSON
  - [ ] 11.9 Test: loading JSON with a missing key uses the SettingsState default

- [ ] 12. Write property-based tests (Req 1–11)
  - File: `tests/test_virtual_mouse_page_properties.py`
  - Requires: `hypothesis` (add to requirements.txt if not present)
  - [ ] 12.1 Property 1 — page loads widget values from SettingsState
  - [ ] 12.2 Property 2 — toggle stages correct pending value and syncs badge
  - [ ] 12.3 Property 3 — slider callbacks stage formatted label and pending value (all 5 sliders)
  - [ ] 12.4 Property 4 — widget interactions without save do not modify settings.json
  - [ ] 12.5 Property 5 — `_pending` is empty after `_on_save()`
  - [ ] 12.6 Property 6 — telemetry cursor display follows tracking_state
  - [ ] 12.7 Property 7 — telemetry FPS display is correctly formatted
  - [ ] 12.8 Property 8 — telemetry gesture and action display follow the conditional rules
  - [ ] 12.9 Property 9 — SettingsManager save/load round-trip preserves all values
