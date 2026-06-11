# Design Document — Virtual Mouse Page

## Overview

The Virtual Mouse Page (`VirtualMousePage`) is a CustomTkinter dashboard page within GestureOS AI that
lets users configure the gesture-driven virtual mouse subsystem and observe its real-time telemetry.
The page already has a complete implementation in `dashboard/pages/virtual_mouse_page.py`.

This document describes how that implementation satisfies all requirements in `requirements.md` and
identifies any gaps or improvements needed.

### Design Goals

1. All controls reflect persisted settings on load and write back only when the user explicitly saves.
2. Live telemetry updates arrive on the Tkinter main thread — no background threads involved.
3. Visual consistency with the rest of the dashboard via `COLORS`, `FONTS`, and `SIZES` from `dashboard/theme.py`.

---

## Architecture

### Component Hierarchy

```
GestureOSApp (CTkTk — root window)
├── TopHeader
├── SidebarNav
├── CTkFrame (content_frame)
│   └── VirtualMousePage  ← subject of this spec
│       ├── Page header card        (CTkFrame / surface0)
│       │   ├── Title label         ("Virtual Mouse")
│       │   ├── Subtitle label
│       │   └── Status Badge        (Badge widget — "Active" / "Inactive")
│       ├── Body frame              (transparent, 2-column grid)
│       │   ├── Controls card       (col 0 — CTkFrame / surface0)
│       │   │   ├── "Controls" label
│       │   │   ├── Divider
│       │   │   ├── Mouse Tracking toggle frame
│       │   │   │   └── CTkSwitch (self._toggle)
│       │   │   ├── Sensitivity slider row
│       │   │   ├── Smoothing slider row
│       │   │   ├── Click Threshold slider row
│       │   │   ├── Scroll Sensitivity slider row
│       │   │   └── Drag Threshold slider row
│       │   └── Telemetry card      (col 1 — CTkFrame / surface0)
│       │       ├── "Live Telemetry" label
│       │       ├── Divider
│       │       ├── Cursor X / Y pill row
│       │       ├── FPS pill row
│       │       ├── Current Gesture pill row
│       │       ├── Current Action pill row
│       │       └── Hand Count pill row
│       └── Actions bar             (transparent, 3-column grid)
│           ├── ← Back to Dashboard button
│           ├── ↺ Reset Settings button
│           └── ✓ Save Settings button
├── FooterBar
└── ...
```

### Class Inheritance

```
ctk.CTkScrollableFrame
    └── BasePage          (dashboard/pages/base_page.py)
            └── VirtualMousePage  (dashboard/pages/virtual_mouse_page.py)
```

`BasePage` provides:
- `fg_color = COLORS["base"]`, `corner_radius = 0` — full-bleed dark background.
- `grid_columnconfigure(0, weight=1)` — single column that stretches.
- `on_enter()` / `on_leave()` lifecycle hooks (empty by default).
- Calls `self._build()` at the end of `__init__`.

### Key Dependencies

| Dependency | Role |
|---|---|
| `config.settings_manager.SettingsManager` | Loads, updates, and persists settings to `config/settings.json` |
| `config.settings_manager.SettingsState` | Typed dataclass carrying all setting values in memory |
| `dashboard.theme.COLORS / FONTS / SIZES` | Single source of truth for all visual tokens |
| `dashboard.components.widgets.Badge` | Pill-shaped status label in the page header |
| `GestureOSApp._poll_camera` | Calls `set_camera_frame()` on every processed camera frame |

---

## Components and Interfaces

### VirtualMousePage

**File:** `dashboard/pages/virtual_mouse_page.py`

```python
class VirtualMousePage(BasePage):
    PAGE_KEY   = "virtual_mouse"
    PAGE_TITLE = "Virtual Mouse"
    PAGE_ICON  = "⊹"

    def __init__(
        self,
        master,
        on_navigate: callable | None = None,
        settings_manager: SettingsManager | None = None,
        on_settings_changed: callable | None = None,
        **kwargs,
    ) -> None: ...

    # ── Build (called by BasePage.__init__) ────────────────────
    def _build(self) -> None: ...
    def _build_controls(self, parent, state) -> None: ...
    def _add_slider(self, parent, row, name, val, lo, hi, steps, fmt, cb) -> int: ...
    def _build_telemetry(self, parent, state) -> None: ...
    def _build_actions(self, pad: int) -> None: ...

    # ── Slider callbacks ────────────────────────────────────────
    def _on_toggle(self) -> None: ...
    def _on_sens(self, val: float) -> None: ...
    def _on_smooth(self, val: float) -> None: ...
    def _on_click_thresh(self, val: float) -> None: ...
    def _on_scroll_sens(self, val: float) -> None: ...
    def _on_drag_thresh(self, val: float) -> None: ...

    # ── Action callbacks ────────────────────────────────────────
    def _on_reset(self) -> None: ...
    def _on_save(self) -> None: ...

    # ── Helpers ─────────────────────────────────────────────────
    def _stage(self, key: str, val) -> None: ...
    def _stage_all(self) -> None: ...
    def _apply_values(self, d: dict) -> None: ...
    def _sync_badge(self, enabled: bool) -> None: ...
    def _navigate(self, key: str) -> None: ...

    # ── Public live-update interface ────────────────────────────
    def set_camera_frame(self, frame=None, fps=0.0, gesture="unknown",
                         confidence=0.0, hands_detected=0, cursor_x=0,
                         cursor_y=0, tracking_state="No Hand",
                         click_status="OPEN", click_counter=0,
                         pinch_distance=0.0, current_action="None",
                         volume_mode=False, volume_level=0,
                         volume_distance=0.0, active_mode="CURSOR",
                         brightness_mode=False, brightness_level=0,
                         brightness_distance=0.0, drag_status="INACTIVE",
                         drag_counter=0, drag_duration=0.0) -> None: ...

    def clear_camera_frame(self) -> None: ...
```

### Constructor Parameters

| Parameter | Type | Purpose |
|---|---|---|
| `master` | `CTkBaseClass` | Parent widget (content_frame in GestureOSApp) |
| `on_navigate` | `callable(key: str)` | Triggers page navigation via the shell |
| `settings_manager` | `SettingsManager \| None` | Provides and persists settings; if `None`, hardcoded defaults are used (Req 1.4) |
| `on_settings_changed` | `callable(SettingsState)` | Called after a successful save; used by `GestureOSApp._apply_settings` to hot-reload pipeline params |

### Internal State

| Attribute | Type | Purpose |
|---|---|---|
| `self._pending` | `dict` | Pending Buffer — staged changes not yet written to disk |
| `self._toggle` | `CTkSwitch` | Mouse Enable/Disable widget |
| `self._slider_labels` | `dict[str, CTkLabel]` | Label above each slider showing the live formatted value |
| `self._slider_widgets` | `dict[str, CTkSlider]` | Slider widgets keyed by display name |
| `self._tele_labels` | `dict[str, CTkLabel]` | Value labels in the Telemetry card keyed by field key |
| `self._status_badge` | `Badge` | Header badge showing "Active" / "Inactive" |

---

## Data Models

### Settings Keys

The page reads and writes a flat subset of `SettingsState` fields:

| Widget | SettingsState field | Type | Range |
|---|---|---|---|
| Mouse Tracking toggle | `virtual_mouse_enabled` | `bool` | — |
| Sensitivity slider | `virtual_mouse_sensitivity` | `float` | 0.5 – 3.0 |
| Smoothing slider | `virtual_mouse_smoothing` | `float` | 0.05 – 0.50 |
| Click Threshold slider | `virtual_mouse_click_threshold` | `float` | 0.01 – 0.15 |
| Scroll Sensitivity slider | `virtual_mouse_scroll_sensitivity` | `float` | 1.0 – 10.0 |
| Drag Threshold slider | `drag_hold_threshold_ms` | `float` | 150 – 1000 ms |

### Default Values (`_DEFAULTS`)

```python
_DEFAULTS = {
    "virtual_mouse_enabled":        False,
    "virtual_mouse_sensitivity":    1.5,
    "virtual_mouse_smoothing":      0.20,
    "virtual_mouse_click_threshold":0.05,
    "virtual_mouse_scroll_sensitivity": 5.0,
    "drag_hold_threshold_ms":       300.0,
}
```

These are the values applied by the Reset Settings action (Req 9). They are **not** written to disk
by Reset — only by Save.

### Telemetry Fields

| Key | Label | Idle default | Source kwarg |
|---|---|---|---|
| `cursor_xy` | Cursor X / Y | `-- , --` | `cursor_x`, `cursor_y`, `tracking_state` |
| `fps` | FPS | `-- FPS` | `fps` |
| `gesture` | Current Gesture | `—` | `gesture` |
| `action` | Current Action | `None` | `current_action`, `active_mode` |
| `hand_count` | Hand Count | `0` | `hands_detected` |

### SettingsManager JSON Schema

`config/settings.json` is a **flat JSON object**. The virtual-mouse-relevant keys are:

```json
{
  "virtual_mouse_enabled": true,
  "virtual_mouse_sensitivity": 1.8,
  "virtual_mouse_smoothing": 0.31,
  "virtual_mouse_click_threshold": 0.04,
  "virtual_mouse_scroll_sensitivity": 5.0,
  "drag_hold_threshold_ms": 300.0,
  ...
}
```

`SettingsManager.load()` accepts both the flat key structure and a legacy nested structure; missing
keys fall back to `SettingsState` field defaults.

---

## Data Flow

### Initialisation Flow (Req 1)

```
GestureOSApp._instantiate_page("virtual_mouse")
    │
    ├─ VirtualMousePage.__init__(master, settings_manager, ...)
    │       │
    │       └─ BasePage.__init__() → _build()
    │               │
    │               ├─ state = settings_manager.state   ← SettingsState (live object)
    │               ├─ _build_controls(body, state)
    │               │       ├─ reads state.virtual_mouse_enabled  → toggle.select/deselect
    │               │       ├─ reads state.virtual_mouse_sensitivity → slider.set(...)
    │               │       ├─ reads state.virtual_mouse_smoothing   → slider.set(...)
    │               │       ├─ reads state.virtual_mouse_click_threshold → slider.set(...)
    │               │       ├─ reads state.virtual_mouse_scroll_sensitivity → slider.set(...)
    │               │       └─ reads state.drag_hold_threshold_ms → slider.set(...)
    │               ├─ _build_telemetry(body, state)    (idle defaults)
    │               ├─ _build_actions(pad)
    │               └─ _sync_badge(state.virtual_mouse_enabled)
    │
    └─ page.grid(row=0, col=0, sticky="nsew")
```

### Pending Buffer / Save Flow (Req 2–7, 9, 10)

```
User interacts with widget
    │
    ├─ callback (_on_toggle / _on_sens / ... )
    │       └─ self._stage(key, val)
    │               └─ self._pending[key] = val      ← in-memory only
    │
    ├─ [optional] more interactions → more _stage() calls
    │
    ├─ "Save Settings" clicked
    │       └─ _on_save()
    │               ├─ (if _pending empty) _stage_all()   ← snapshot widgets → _pending
    │               ├─ settings_manager.update(**_pending)  ← mutates SettingsState in-memory
    │               ├─ settings_manager.save()             ← writes config/settings.json
    │               ├─ on_settings_changed(settings_manager.snapshot())  ← hot-reload pipeline
    │               └─ self._pending.clear()
    │
    └─ "Reset Settings" clicked
            └─ _on_reset()
                    ├─ _apply_values(_DEFAULTS)   ← push defaults to widgets
                    └─ self._pending.clear()       ← discard staged changes (no disk write)
```

### Telemetry Update Flow (Req 8)

```
[main thread, ~30 fps]

GestureOSApp._poll_camera()
    │
    ├─ CameraStream.read()          → frame
    ├─ HandDetector.detect(frame)   → detected_hands
    ├─ GestureEngine.predict(hand)  → (gesture_label, confidence)
    ├─ VirtualMouse.process_hand()  → vm_result dict
    │       { cursor_x, cursor_y, tracking_state, fps, gesture,
    │         current_action, active_mode, hands_detected, ... }
    │
    └─ if current_page is VirtualMousePage:
            └─ page.set_camera_frame(
                    fps=..., gesture=..., hands_detected=...,
                    cursor_x=..., cursor_y=..., tracking_state=...,
                    current_action=..., active_mode=..., ...
               )
                    │
                    ├─ _tele_labels["cursor_xy"].configure(...)
                    ├─ _tele_labels["fps"].configure(...)
                    ├─ _tele_labels["gesture"].configure(...)
                    ├─ _tele_labels["action"].configure(...)
                    └─ _tele_labels["hand_count"].configure(...)
```

`clear_camera_frame()` is called when the camera is stopped or when navigating away from the page,
resetting all telemetry labels to their idle defaults.

### Settings Hot-Reload Flow (Req 10.3)

```
_on_save() calls on_settings_changed(snapshot)
    │
    └─ GestureOSApp._apply_settings(settings: SettingsState)
            ├─ self._virtual_mouse.enabled     = settings.virtual_mouse_enabled
            ├─ self._virtual_mouse.sensitivity  = settings.virtual_mouse_sensitivity
            ├─ self._virtual_mouse.smoothing    = settings.virtual_mouse_smoothing
            ├─ ... (all virtual mouse fields applied to the live VirtualMouse instance)
            └─ (camera restart only if camera_index or fps_limit changed)
```

This ensures saved settings take effect immediately in the running pipeline without restarting the
application.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a
system — essentially, a formal statement about what the system should do. Properties serve as the
bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Page loads widget values from SettingsState

*For any* `SettingsState` with arbitrary values for `virtual_mouse_enabled`,
`virtual_mouse_sensitivity`, `virtual_mouse_smoothing`, `virtual_mouse_click_threshold`,
`virtual_mouse_scroll_sensitivity`, and `drag_hold_threshold_ms`, constructing a
`VirtualMousePage` with a `SettingsManager` holding that state SHALL result in each corresponding
widget reflecting the same value, the toggle being in the correct selected/deselected state, and
the Status Badge showing "Active" or "Inactive" accordingly.

**Validates: Requirements 1.1, 1.2, 1.3**

---

### Property 2: Toggle interaction stages the correct pending value

*For any* toggle interaction (select or deselect), the `_pending` dict SHALL contain
`"virtual_mouse_enabled"` mapped to the boolean matching the toggle's new state, and the
Status Badge text SHALL match ("Active" when `True`, "Inactive" when `False`).

**Validates: Requirements 2.1, 2.2**

---

### Property 3: Slider callback stages formatted label and pending value

*For any* valid float value `v` within a slider's configured range, invoking the slider's
callback SHALL update the slider's label to display `v` in the specified format string AND stage
`_pending[settings_key] = v`. This property applies to all five sliders:
Sensitivity, Smoothing, Click Threshold, Scroll Sensitivity, and Drag Threshold.

**Validates: Requirements 3.2, 4.2, 5.2, 6.2, 7.2**

---

### Property 4: Widget interactions do not write to disk

*For any* sequence of toggle activations and slider movements that does not include a
"Save Settings" action, the contents of `config/settings.json` SHALL remain byte-for-byte
identical to their state before the interactions began.

**Validates: Requirements 2.3, 10.5**

---

### Property 5: Pending buffer is empty after save

*For any* non-empty `_pending` dict passed to `_on_save()`, after the save completes the
`_pending` dict SHALL be empty.

**Validates: Requirements 10.1, 10.4**

---

### Property 6: Telemetry cursor display follows tracking state

*For any* `(cursor_x, cursor_y)` pair, calling `set_camera_frame` with
`tracking_state="Tracking"` SHALL display `"{cursor_x} , {cursor_y}"` in the Cursor X / Y
field; calling it with any other `tracking_state` SHALL display `"-- , --"`.

**Validates: Requirements 8.2, 8.3**

---

### Property 7: Telemetry FPS display

*For any* `fps > 0`, calling `set_camera_frame(fps=fps)` SHALL display `f"{fps:.1f} FPS"` in
the FPS field. When `fps == 0`, it SHALL display `"-- FPS"`.

**Validates: Requirements 8.4, 8.5**

---

### Property 8: Telemetry gesture and action display

*For any* non-empty, non-`"unknown"` gesture string `g`, calling
`set_camera_frame(gesture=g)` SHALL display `g` in the Current Gesture field. For
`gesture` equal to `"unknown"`, `""`, or `None`, it SHALL display `"—"`.

*For any* `(current_action, active_mode)` pair, the Current Action field SHALL display
`current_action` when it is not `"None"`, `""`, or `None`; otherwise it SHALL display
`active_mode`.

**Validates: Requirements 8.6, 8.7, 8.8, 8.9**

---

### Property 9: SettingsManager save/load round-trip

*For any* valid `SettingsState` (with arbitrary values within each field's valid domain),
calling `SettingsManager.save()` followed by `SettingsManager.load()` SHALL produce a
`SettingsState` equal to the one that was saved.

**Validates: Requirements 11.3**

---

## Error Handling

### Missing SettingsManager

If `settings_manager=None` is passed to `VirtualMousePage`, the build logic falls back to
hardcoded constants for all widget initial values (`enabled=False`, `sensitivity=1.5`, etc. —
see `_DEFAULTS`). This is handled with `state.field if state else default` inline checks in
`_build_controls`. (Req 1.4)

### Save with No Staged Changes

If `_on_save()` is called with an empty `_pending` dict, `_stage_all()` is called first to
capture the current widget state before persisting. This ensures a redundant Save click is
safe and idempotent. (Req 10.2)

### SettingsManager Missing/Corrupt JSON

`SettingsManager.load()` wraps file I/O in a `try/except (OSError, json.JSONDecodeError)` block
and returns a `SettingsState()` with all defaults if the file is absent or malformed. (Req 11.2)

### Missing JSON Keys

`SettingsManager.load()` uses `raw.get(key, default)` for every field. Any key absent from the
file silently falls back to its `SettingsState` field default. (Req 11.2)

### Corrupt SettingsState on Update

`SettingsManager.update()` performs per-field type coercion (`int()`, `float()`, `bool()`, clamped
`max(1, ...)` for fps) before mutating `_state`, so partial or lightly invalid inputs are
normalized rather than causing a crash.

---

## Testing Strategy

### Unit Tests (example-based)

Target file: `tests/test_virtual_mouse_page.py`

Cover specific scenarios and slider configuration checks that do not benefit from randomization:

- **Req 1.4** — Construct page without SettingsManager, verify all widgets show `_DEFAULTS` values.
- **Req 3.1 / 4.1 / 5.1 / 6.1 / 7.1** — Verify each slider's `from_`, `to`, and `number_of_steps`
  after construction.
- **Req 8.1** — Verify all five keys exist in `_tele_labels` after construction.
- **Req 8.10** — Call `clear_camera_frame()`, verify all five labels show idle defaults.
- **Req 9.1–9.2** — Stage changes, call `_on_reset()`, verify widgets = `_DEFAULTS` and
  `_pending == {}`.
- **Req 10.2** — With empty `_pending`, call `_on_save()`, verify `_stage_all` path is taken and
  SettingsManager receives widget values.
- **Req 10.3** — Register `on_settings_changed` mock, save, verify mock called with a `SettingsState`.
- **Req 11.1** — Call `settings_manager.save()`, reload JSON, verify all expected keys are present.
- **Req 11.2** — Delete a key from the JSON, reload, verify the default value is used.
- **Req 12.3** — Verify `page.cget("fg_color")` == `COLORS["base"]` after construction.

### Property-Based Tests

Target file: `tests/test_virtual_mouse_page_properties.py`

Use `hypothesis` as the property-based testing library. Each test runs a minimum of 100 iterations.

```
pip install hypothesis
```

**Property 1** — `Feature: virtual-mouse-page, Property 1: page loads widget values from SettingsState`
- Strategy: `@given(st.floats(0.5, 3.0), st.floats(0.05, 0.50), st.floats(0.01, 0.15),
  st.floats(1.0, 10.0), st.floats(150.0, 1000.0), st.booleans())`
- Assert: slider.get() ≈ generated value, toggle state matches enabled, badge text matches.

**Property 2** — `Feature: virtual-mouse-page, Property 2: toggle interaction stages the correct pending value`
- Strategy: `@given(st.booleans())`
- Assert: after programmatically selecting/deselecting toggle, `_pending["virtual_mouse_enabled"]`
  matches and badge text is correct.

**Property 3** — `Feature: virtual-mouse-page, Property 3: slider callback stages formatted label and pending value`
- Strategy: one `@given` per slider with its value range (e.g. `st.floats(0.5, 3.0)` for Sensitivity).
- Assert: label text matches format string applied to the value, `_pending[key] == v`.

**Property 4** — `Feature: virtual-mouse-page, Property 4: widget interactions do not write to disk`
- Strategy: `@given(st.lists(st.sampled_from(["sens", "smooth", "click", "scroll", "drag", "toggle"])))`
- Assert: after a random sequence of interactions (no save), JSON file contents are unchanged.

**Property 5** — `Feature: virtual-mouse-page, Property 5: pending buffer is empty after save`
- Strategy: `@given(st.dictionaries(st.sampled_from([...keys...]), st.floats()))`
- Assert: after `_on_save()`, `page._pending == {}`.

**Property 6** — `Feature: virtual-mouse-page, Property 6: telemetry cursor display follows tracking state`
- Strategy: `@given(st.integers(-9999, 9999), st.integers(-9999, 9999), st.text())`
- Assert: when tracking_state == "Tracking", display matches; otherwise "-- , --".

**Property 7** — `Feature: virtual-mouse-page, Property 7: telemetry FPS display`
- Strategy: `@given(st.floats(0.01, 300.0))`
- Assert: label == f"{fps:.1f} FPS".

**Property 8** — `Feature: virtual-mouse-page, Property 8: telemetry gesture and action display`
- Strategy: `@given(st.text(min_size=1).filter(lambda s: s not in ("unknown", "")))` for gesture;
  `@given(st.text(), st.text())` for (current_action, active_mode).
- Assert: gesture label == input; action logic follows the conditional.

**Property 9** — `Feature: virtual-mouse-page, Property 9: SettingsManager save/load round-trip`
- Strategy: `@given(...)` generating a `SettingsState` with all fields randomized within valid ranges.
- Assert: `load(save(state)) == state` (all field values identical).

### Integration Tests

- Construct a full `GestureOSApp` in headless mode (or mock the camera), navigate to the virtual
  mouse page, save settings, and verify the `VirtualMouse` instance reflects the new values.
- Verify that `on_settings_changed` triggered by `_on_save` propagates to `_apply_settings` and
  updates `self._virtual_mouse` attributes.
