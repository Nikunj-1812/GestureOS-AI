# Requirements Document

## Introduction

The Virtual Mouse Page is a control panel within the GestureOS AI CustomTkinter dashboard that lets users configure and monitor the gesture-driven virtual mouse subsystem. The page provides a Mouse Enable/Disable toggle, five sensitivity/behaviour sliders, a Live Telemetry panel, and Reset/Save Settings actions. Settings are persisted to `config/settings.json` through `SettingsManager` and take effect in the running gesture pipeline without requiring an application restart.

---

## Glossary

- **Page**: The `VirtualMousePage` CustomTkinter frame rendered inside the dashboard shell.
- **SettingsManager**: The `config/settings_manager.py` class responsible for loading, updating, and persisting application settings to `config/settings.json`.
- **SettingsState**: The dataclass that holds all current setting values in memory.
- **Pending Buffer**: An in-memory dictionary of staged setting changes that have not yet been written to disk.
- **Telemetry Feed**: The stream of runtime data (cursor position, FPS, gesture, action, hand count) pushed to the Page from the gesture processing loop.
- **Default Values**: The hardcoded reset values defined in the Page: `virtual_mouse_enabled=False`, `virtual_mouse_sensitivity=1.5`, `virtual_mouse_smoothing=0.20`, `virtual_mouse_click_threshold=0.05`, `virtual_mouse_scroll_sensitivity=5.0`, `drag_hold_threshold_ms=300.0`.
- **Toggle**: The `CTkSwitch` widget that enables or disables mouse tracking.
- **Sensitivity Slider**: Controls `virtual_mouse_sensitivity` (range 0.5–3.0).
- **Smoothing Slider**: Controls `virtual_mouse_smoothing` (range 0.05–0.50).
- **Click Threshold Slider**: Controls `virtual_mouse_click_threshold` (range 0.01–0.15).
- **Scroll Sensitivity Slider**: Controls `virtual_mouse_scroll_sensitivity` (range 1.0–10.0).
- **Drag Threshold Slider**: Controls `drag_hold_threshold_ms` (range 150–1000 ms).
- **Status Badge**: The label in the page header showing "Active" or "Inactive" based on the Toggle state.
- **Telemetry Panel**: The right-column card displaying live Cursor X/Y, FPS, Current Gesture, Current Action, and Hand Count.

---

## Requirements

### Requirement 1: Page Initialisation

**User Story:** As a user, I want the Virtual Mouse Page to load with the current saved settings, so that I can see and adjust the values that are already in effect.

#### Acceptance Criteria

1. WHEN the Virtual Mouse Page is constructed, THE Page SHALL read `virtual_mouse_enabled`, `virtual_mouse_sensitivity`, `virtual_mouse_smoothing`, `virtual_mouse_click_threshold`, `virtual_mouse_scroll_sensitivity`, and `drag_hold_threshold_ms` from the SettingsState provided by SettingsManager and populate each corresponding widget with those values.
2. WHEN the Virtual Mouse Page is constructed and `virtual_mouse_enabled` is `True`, THE Page SHALL display the Toggle in its selected (on) state and the Status Badge with text "Active".
3. WHEN the Virtual Mouse Page is constructed and `virtual_mouse_enabled` is `False`, THE Page SHALL display the Toggle in its deselected (off) state and the Status Badge with text "Inactive".
4. WHEN the Virtual Mouse Page is constructed without a SettingsManager instance, THE Page SHALL populate each widget with its Default Value.

---

### Requirement 2: Mouse Enable / Disable Toggle

**User Story:** As a user, I want a toggle to enable or disable mouse tracking, so that I can quickly turn the gesture mouse on or off without changing any other settings.

#### Acceptance Criteria

1. WHEN the user activates the Toggle, THE Page SHALL stage `virtual_mouse_enabled = True` in the Pending Buffer and update the Status Badge text to "Active".
2. WHEN the user deactivates the Toggle, THE Page SHALL stage `virtual_mouse_enabled = False` in the Pending Buffer and update the Status Badge text to "Inactive".
3. THE Page SHALL NOT write any value to `config/settings.json` as a result of interacting with the Toggle alone.

---

### Requirement 3: Sensitivity Slider

**User Story:** As a user, I want to adjust mouse sensitivity, so that cursor movement speed matches my preference and hand range of motion.

#### Acceptance Criteria

1. THE Sensitivity Slider SHALL have a minimum value of 0.5, a maximum value of 3.0, and 25 discrete steps.
2. WHEN the user moves the Sensitivity Slider, THE Page SHALL update the slider label to display the current value formatted as `Sensitivity: <value>×` (two decimal places) and stage `virtual_mouse_sensitivity = <value>` in the Pending Buffer.

---

### Requirement 4: Smoothing Slider

**User Story:** As a user, I want to adjust cursor smoothing, so that I can reduce jitter or increase responsiveness to suit my tracking style.

#### Acceptance Criteria

1. THE Smoothing Slider SHALL have a minimum value of 0.05, a maximum value of 0.50, and 18 discrete steps.
2. WHEN the user moves the Smoothing Slider, THE Page SHALL update the slider label to display the current value formatted as `Smoothing: <value>` (two decimal places) and stage `virtual_mouse_smoothing = <value>` in the Pending Buffer.

---

### Requirement 5: Click Threshold Slider

**User Story:** As a user, I want to configure the pinch distance that triggers a click, so that I can tune click sensitivity to avoid accidental or missed clicks.

#### Acceptance Criteria

1. THE Click Threshold Slider SHALL have a minimum value of 0.01, a maximum value of 0.15, and 28 discrete steps.
2. WHEN the user moves the Click Threshold Slider, THE Page SHALL update the slider label to display the current value formatted as `Click Threshold: <value>` (three decimal places) and stage `virtual_mouse_click_threshold = <value>` in the Pending Buffer.

---

### Requirement 6: Scroll Sensitivity Slider

**User Story:** As a user, I want to configure scroll speed, so that scrolling through documents and web pages feels natural.

#### Acceptance Criteria

1. THE Scroll Sensitivity Slider SHALL have a minimum value of 1.0, a maximum value of 10.0, and 18 discrete steps.
2. WHEN the user moves the Scroll Sensitivity Slider, THE Page SHALL update the slider label to display the current value formatted as `Scroll Sensitivity: <value>×` (one decimal place) and stage `virtual_mouse_scroll_sensitivity = <value>` in the Pending Buffer.

---

### Requirement 7: Drag Threshold Slider

**User Story:** As a user, I want to configure how long I must hold a pinch gesture before drag is activated, so that I can separate deliberate drag actions from regular clicks.

#### Acceptance Criteria

1. THE Drag Threshold Slider SHALL have a minimum value of 150 ms, a maximum value of 1000 ms, and 17 discrete steps.
2. WHEN the user moves the Drag Threshold Slider, THE Page SHALL update the slider label to display the current value formatted as `Drag Threshold: <value> ms` (zero decimal places) and stage `drag_hold_threshold_ms = <value>` in the Pending Buffer.

---

### Requirement 8: Live Telemetry Display

**User Story:** As a user, I want to see real-time cursor and gesture data on the page, so that I can verify the virtual mouse is tracking correctly while I adjust settings.

#### Acceptance Criteria

1. THE Telemetry Panel SHALL display five named fields: Cursor X / Y, FPS, Current Gesture, Current Action, and Hand Count.
2. WHEN the Page receives a telemetry update and `tracking_state` equals `"Tracking"`, THE Telemetry Panel SHALL display the cursor position as `<cursor_x> , <cursor_y>`.
3. WHEN the Page receives a telemetry update and `tracking_state` does not equal `"Tracking"`, THE Telemetry Panel SHALL display `-- , --` in the Cursor X / Y field.
4. WHEN the Page receives a telemetry update with `fps > 0`, THE Telemetry Panel SHALL display FPS formatted as `<fps> FPS` (one decimal place).
5. WHEN the Page receives a telemetry update with `fps` equal to 0, THE Telemetry Panel SHALL display `-- FPS` in the FPS field.
6. WHEN the Page receives a telemetry update with `gesture` equal to `"unknown"`, an empty string, or `None`, THE Telemetry Panel SHALL display `—` in the Current Gesture field.
7. WHEN the Page receives a telemetry update with a non-empty, non-`"unknown"` gesture string, THE Telemetry Panel SHALL display that gesture string in the Current Gesture field.
8. WHEN the Page receives a telemetry update, THE Telemetry Panel SHALL display the `current_action` value in the Current Action field; IF `current_action` is `"None"`, an empty string, or `None`, THEN THE Telemetry Panel SHALL display the `active_mode` value instead.
9. WHEN the Page receives a telemetry update, THE Telemetry Panel SHALL display the integer value of `hands_detected` in the Hand Count field.
10. WHEN `clear_camera_frame` is called, THE Telemetry Panel SHALL reset all fields to their default idle values: Cursor X / Y to `-- , --`, FPS to `-- FPS`, Current Gesture to `—`, Current Action to `None`, and Hand Count to `0`.

---

### Requirement 9: Reset Settings

**User Story:** As a user, I want a Reset Settings button that reverts all controls to defaults, so that I can quickly undo all unsaved changes.

#### Acceptance Criteria

1. WHEN the user activates the Reset Settings button, THE Page SHALL set all slider widgets and the Toggle to their Default Values.
2. WHEN the user activates the Reset Settings button, THE Page SHALL clear the Pending Buffer without writing any value to `config/settings.json`.
3. WHEN the user activates the Reset Settings button, THE Page SHALL update the Status Badge and all slider labels to reflect the Default Values.

---

### Requirement 10: Save Settings

**User Story:** As a user, I want a Save Settings button that persists my changes, so that my preferred virtual mouse configuration is restored the next time the application starts.

#### Acceptance Criteria

1. WHEN the user activates the Save Settings button and the Pending Buffer is non-empty, THE Page SHALL call `SettingsManager.update()` with all staged key-value pairs and then call `SettingsManager.save()` to write the values to `config/settings.json`.
2. WHEN the user activates the Save Settings button and the Pending Buffer is empty, THE Page SHALL capture the current widget state into the Pending Buffer and then call `SettingsManager.update()` and `SettingsManager.save()`.
3. WHEN the user activates the Save Settings button and an `on_settings_changed` callback is registered, THE Page SHALL invoke the callback with a SettingsState snapshot after saving.
4. WHEN the user activates the Save Settings button, THE Page SHALL clear the Pending Buffer after a successful save.
5. THE Page SHALL NOT persist any setting to `config/settings.json` unless the user explicitly activates the Save Settings button.

---

### Requirement 11: Settings Persistence Integrity

**User Story:** As a developer, I want the settings file to remain consistent after save operations, so that the application can reliably reload settings on the next launch.

#### Acceptance Criteria

1. WHEN SettingsManager saves settings, THE SettingsManager SHALL write all virtual mouse setting keys defined in SettingsState to `config/settings.json` as a flat JSON object.
2. WHEN SettingsManager loads `config/settings.json` and a key is absent, THE SettingsManager SHALL use the corresponding Default Value for that key.
3. FOR ALL valid SettingsState values saved by SettingsManager, loading the resulting `config/settings.json` SHALL produce a SettingsState equal to the one that was saved (round-trip property).

---

### Requirement 12: Theme Consistency

**User Story:** As a user, I want the Virtual Mouse Page to match the rest of the GestureOS AI dashboard visually, so that the interface feels cohesive.

#### Acceptance Criteria

1. THE Page SHALL render all background surfaces, text, slider accents, and button colours exclusively using values from the `COLORS` dictionary defined in `dashboard/theme.py`.
2. THE Page SHALL render all text using font families and sizes defined in the `FONTS` dictionary defined in `dashboard/theme.py`.
3. THE Page SHALL apply the Catppuccin Mocha-inspired dark palette (`base` colour `#1e1e2e` as the page background) at all times, regardless of system theme.
