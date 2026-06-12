# Upgrade Tasks — Phase 3.6 (Feature Management, Settings, Telemetry) & Drag & Drop

- [ ] Update dependencies and configuration:
  - [ ] Add `psutil` to `requirements.txt`.
  - [ ] Update `config/app_config.py` with new settings state.
  - [ ] Update `config/settings_manager.py` to support toggles, sliders, and defaults.
- [ ] Implement core engines & routing logic:
  - [ ] Update `modules/mode_manager.py` to prioritize enabled modes only.
  - [ ] Implement Drag & Drop pinch-hold state machine in `modules/virtual_mouse.py`.
  - [ ] Implement cursor acceleration algorithm in `modules/virtual_mouse.py`.
  - [ ] Support dynamic update cooldowns in volume and brightness controllers.
- [ ] Update rendering & visualizer overlays:
  - [ ] Add `DRAGGING` orange feedback text banner overlay.
  - [ ] Update visualizer to support global show/hide overlays config toggle.
- [ ] Integrate with Backend & Web Dashboard:
  - [ ] Integrate CPU/RAM measurements and websocket serialization in `web_backend.py`.
  - [ ] Redesign React dashboard with Sidebar navigation (Dashboard, Stream, Logs, Settings).
  - [ ] Implement live resource charts (CPU, RAM, FPS) on the Telemetry page.
  - [ ] Implement Event Log controls (search, filter categories, CSV download export) in UI.
  - [ ] Add advanced configuration cards (Cursor, Click, Scroll, Volume, Brightness, Global) in settings view.
- [ ] Integrate with Desktop UI:
  - [ ] Update `dashboard/shell/window.py` to forward new telemetry fields.
  - [ ] Update `dashboard/pages/virtual_mouse_page.py` with Drag metrics and toggles.
- [ ] Verification & testing:
  - [ ] Create validation script `scratch/test_drag.py`.
  - [ ] Expand unit tests in `tests/test_virtual_mouse.py`.
  - [ ] Run test suite and check backend server launch.


# Enable CORS
INFO:     connection open

  - `volume_smoothing`: 0.15

#### [MODIFY] [app_config.py](file:///c:/Users/nikun/OneDrive/Desktop/GestureOS-AI-main/config/app_config.py)
- Load new parameters from `set
    for line_num, line in enumerate(lines, 1):
        i = 0
        while i < len(line):
            char = line[i]
            if in_line_comment:
                i += 1
                continue
   
logger.add(sys.stderr, level=config.log_level)

camera_stream = No
            print(f"Unclosed '{item[0]}' from line {item[1]}:{item[2]}: {item[3].strip()}")
    else:
    detection_confidence=0.5,
    tracking_confidence=0.5
)

model_path = str(Path(config.model_dir) / config.default_model)
gesture_engine = GestureEngine(
    model_path=model_path,
    confidence_threshold=config.confidence_threshold,
    smoothing_frames=config.smoothing_frames,
)
action_dispatcher = ActionDispatcher(cooldown_ms=800)

from modules.virtual_mouse import VirtualMouse
virtual_mouse = VirtualMouse(
    enabled=config.virtual_mouse_enabled,
    sensitivity=config.virtual_mouse_sensitivity,
    dead_zone=config.virtual_mouse_dead_zone,
    smoothing=config.virtual_mouse_smoothing,
    click_threshold=getattr(config, 'virtual_mouse_click_threshold', 0.05),
    right_click_threshold=getattr(config, 'virtual_mouse_right_click_threshold', 0.05),
    scroll_sensitivity=getattr(config, 'virtual_mouse_scroll_sensitivity', 5.0),
    scroll_dead_zone=getattr(config, 'virtual_mouse_scroll_dead_zone', 0.04),
    scroll_smoothing=getattr(config, 'virtual_mouse_scroll_smoothing', 0.25),
    volume_min_distance_px=getattr(config, 'virtual_mouse_volume_min_distance_px', 30.0),
    volume_max_distance_px=getattr(config, 'virtual_mouse_volume_max_distance_px', 250.0),
    volume_smoothing=getattr(config, 'virtual_mouse_volume_smoothing', 0.15),
)

camera_running = False

def start_camera_stream():
  - **Event Logs Tab**: Intercept `Drag Start`, `Drag End`, and `Drag Duration` log patterns and display them in the monitoring console with CSV exporting.
  - **Settings Panel Tab**: Add a Click & Drag configuration card with drag toggle and hold duration threshold slider.

---

## Verification Plan

### Automated Tests
- Run `pytest tests/test_virtual_mouse.py`.
- Add test cases verifying:
  - Short pinch holding (< threshold) triggers a single Left Click on release.
  - Long pinch holding ($\ge$ threshold) triggers MouseDown and enters Dragging state.
  - Releasing pinch after Dragging triggers MouseUp and returns correct duration.

### Manual Verification
- Start the server using `python web_backend.py`.
- Open settings, adjust drag hold threshold slider, pinch-hold items on screen, move hand, and verify dragging behavior works without conflicts.

### Manual Verification
- Start server using `python web_backend.py`.
- Verify the active mode transitions on log console: `[MODE] Volume`, `[MODE] Brightness`, etc.
- Verify screen brightness adjusts on Windows when holding Brightness gesture and shifting distance.

- Extend only Thumb and Pinky: verify Volume Mode triggers, volume adjustments match distance, and actual Windows volume changes.
- Verify logs indicate `[VOLUME] 50%` without spamming logs.

| 4 | Hold still (< dead zone) | No scroll fires, Direction = `—` |
| 5 | Lower any finger | Scroll Mode = IDLE, cursor resumes movement |
| 6 | Normal cursor movement | Unaffected when scroll mode off |
| 7 | Left click (LM4+LM8) | Only fires when NOT in scroll mode |
| 8 | Right click (LM4+LM12) | Only fires when NOT in scroll mode |
| 9 | Dashboard telemetry | Scroll Mode, Direction, Speed, Counter update live |
| 10 | Scroll Sensitivity slider | Higher = faster scroll immediately |
| 11 | Scroll Dead Zone slider | Higher = less sensitive, ignores small movements |
| 12 | Activity Log | `Scroll Start` + `Scroll Stop` events logged |
| 13 | ESC key | VM stops, all states (scroll, click) reset |
| 14 | FPS ≥ 25 | No frame drop during continuous scrolling |

---

## Log Format

```
[15:06:45.123] Scroll Start | gesture=index_middle_up | anchor_y=0.4821
[15:06:45.210] Scroll UP | vel=-0.0051 | amount=2 | count=1
[15:06:45.294] Scroll DOWN | vel=0.0038 | amount=-1 | count=2
[15:06:47.891] Scroll Stop | Total scroll events=14
```

                                'name': name,
                                'is_closing': is_closing,
                                'is_self_closing': is_self_closing,
                                'line_num': line_num,
                                'line': line,
                                'tag_str': tag_str
                                'is_closing': is_closing,
                                'is_self_closing': is_self_closing,
                                'line_num': line_num,
                                'line': line,
    gesture_engine.reset()
    try:
        hand_detector.close()
    except Exception:
        pass
    hand_detector = HandDetector(
        max_hands=2,
        detection_confidence=0.5,
        tracking_confidence=0.5
    )
    return {"status": "success"}

@app.get("/api/settings")
def api_get_settings():
    state = settings_manager.state
    return {
        "show_landmarks": state.show_landmarks,
        "show_connections": state.show_connections,
        "show_bounding_box": state.show_bounding_box,
        "show_finger_states": state.show_finger_states,
        "show_distance_meter": state.show_distance_meter,
        "show_debug_panel": state.show_debug_panel,
        "show_hud": state.show_hud,
        "virtual_mouse_enabled": state.virtual_mouse_enabled,
        "virtual_mouse_sensitivity": state.virtual_mouse_sensitivity,
        "virtual_mouse_dead_zone": state.virtual_mouse_dead_zone,
        "virtual_mouse_smoothing": state.virtual_mouse_smoothing,
        "virtual_mouse_click_threshold": getattr(state, 'virtual_mouse_click_threshold', 0.05),
        "virtual_mouse_right_click_threshold": getattr(state, 'virtual_mouse_right_click_threshold', 0.05),
        "virtual_mouse_scroll_sensitivity": getattr(state, 'virtual_mouse_scroll_sensitivity', 5.0),
        "virtual_mouse_scroll_dead_zone": getattr(state, 'virtual_mouse_scroll_dead_zone', 0.04),
        "virtual_mouse_scroll_smoothing": getattr(state, 'virtual_mouse_scroll_smoothing', 0.25),
        "virtual_mouse_volume_min_distance_px": getattr(state, 'virtual_mouse_volume_min_distance_px', 30.0),
        "virtual_mouse_volume_max_distance_px": getattr(state, 'virtual_mouse_volume_max_distance_px', 250.0),
        "virtual_mouse_volume_smoothing": getattr(state, 'virtual_mouse_volume_smoothing', 0.15),
    }

@app.post("/api/settings/update")
def api_update_settings(updates: dict):
    params = {}

@app.post("/api/settings/update")
def api_update_settings(updates: dict):
    params = {}
    bool_keys = [
        "show_landmarks", "show_connections", "show_bounding_box",
        "show_finger_states", "show_distance_meter", "show_debug_panel",
        "show_hud", "virtual_mouse_enabled"
    ]
    float_keys = [
        "virtual_mouse_sensitivity", "virtual_mouse_dead_zone", "virtual_mouse_smoothing",
        "virtual_mouse_click_threshold", "virtual_mouse_right_click_threshold",
        "virtual_mouse_scroll_sensitivity", "virtual_mouse_scroll_dead_zone", "virtual_mouse_scroll_smoothing",
        "virtual_mouse_volume_min_distance_px", "virtual_mouse_volume_max_distance_px", "virtual_mouse_volume_smoothing",
        "virtual_mouse_brightness_min_distance_px", "virtual_mouse_brightness_max_distance_px", "virtual_mouse_brightness_smoothing"
    ]
    for key in bool_keys:
        if key in updates:
            params[key] = bool(updates[key])
    for key in float_keys:
        if key in updates:
            params[key] = float(updates[key])
    
    changed = settings_manager.update(**params)
    if changed:
        settings_manager.save()
        settings_manager.apply_to_config(config)
        # Apply to live instance
        virtual_mouse.enabled = config.virtual_mouse_enabled
        virtual_mouse.sensitivity = config.virtual_mouse_sensitivity
        virtual_mouse.dead_zone = config.virtual_mouse_dead_z
        if hasattr(config, 'virtual_mouse_click_threshold'):
            virtual_mouse.click_threshold = config.virtual_mouse_click_threshold
        if hasattr(config, 'virtual_mouse_right_click_threshold'):
            virtual_mouse.right_click_threshold = config.virtual_mouse_right_click_threshold
        if hasattr(config, 'virtual_mouse_scroll_sensitivity'):
            virtual_mouse.scroll_sensitivity = config.virtual_mouse_scroll_sensitivity
        if hasattr(config, 'virtual_mouse_scroll_dead_zone'):
            virtual_mouse.scroll_dead_zone = config.virtual_mouse_scroll_dead_zone
            virtual_mouse.scroll_dead_zone = config.virtual_mouse_scroll_dead_zone
        if hasattr(config, 'virtual_mouse_scroll_smoothing'):
            virtual_mouse.scroll_smoothing = config.virtual_mouse_scroll_smoothing
        if hasattr(config, 'virtual_mouse_volume_min_distance_px') and virtual_mouse._volume_controller:
            virtual_mouse._volume_controller.min_distance = config.virtual_mouse_volume_min_distance_px
        if hasattr(config, 'virtual_mouse_volume_max_distance_px') and virtual_mouse._volume_controller:
            virtual_mouse._volume_controller.max_distance = config.virtual_mouse_volume_max_distance_px
        if hasattr(config, 'virtual_mouse_volume_smoothing') and virtual_mouse._volume_controller:
            virtual_mouse._volume_controller.smoothing = config.virtual_mouse_volume_smoothing
        if hasattr(config, 'virtual_mouse_brightness_min_distance_px') and virtual_mouse._brightness_controller:
            virtual_mouse._brightness_controller.min_distance = config.virtual_mouse_brightness_min_distance_px
        if hasattr(config, 'virtual_mouse_brightness_max_distance_px') and virtual_mouse._brightness_controller:
            virtual_mouse._brightness_controller.max_distance = config.virtual_mouse_brightness_max_distance_px
        if hasattr(config, 'virtual_mouse_brightness_smoothing') and virtual_mouse._brightness_controller:
            virtual_mouse._brightness_controller.smoothing = config.virtual_mouse_brightness_smoothing
    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    last_fps_tick = time.perf_counter()
    fps_smooth = 0.0
    last_frame_id = -1
    last_gesture = "unknown"
    
    try:
        while True:
            # Capture frame & run pipeline if running
            if not camera_running or camera_stream is None:
                # Send empty / disconnected state
                await websocket.send_json({
                    "fps": 0.0,
                    "hands": 0,
                    "gesture": "None",
                    "confidence": 0.0,
                    "camera_status": "Disconnected",
                    "frame": None
                })
                await asyncio.sleep(0.1)
                continue
                
            frame = camera_stream.read()
            if frame is None:
                await websocket.send_json({
                    "fps": 0.0,
                    "hands": 0,
                    "gesture": "None",
                    "confidence": 0.0,
                    "camera_status": "Starting",
                    "frame": None
                })
                await asyncio.sleep(0.05)
                continue
                
            # Avoid duplicate frame processing
            current_frame_id = camera_stream.frame_id
            if current_frame_id == last_frame_id:
                await asyncio.sleep(0.005)
                continue
            last_frame_id = current_frame_id
                pyautogui.press("backspace")
            # Write suggestion + space
            pyautogui.write(suggestion + " ")
            return {"status": "success"}

        if key == "Space":
            pyautogui.press("space")
        elif key == "Backspace":
            pyautogui.press("backspace")
        elif key == "Enter":
            pyautogui.press("enter")
        elif key == "Tab":
            pyautogui.press("tab")
        elif key == "Shift":
            pyautogui.press("shift")
        elif key == "Caps Lock":
            pyautogui.press("capslock")
        else:
            is_upper = caps or shift
            char = key.upper() if is_upper and len(key) == 1 else key
            # Check if it's emoji / unicode
            if any(ord(c) > 127 for c in char):
                import pyperclip
                pyperclip.copy(char)
                pyautogui.hotkey("ctrl", "v")
            else:
                pyautogui.write(char)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error executing pyautogui keypress from web backend: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/keyboard/suggest")
def api_keyboard_suggest(payload: dict):
    text = payload.get("text", "")
    curr_word = word_predictor.get_current_word(text)
    suggestions = word_predictor.get_suggestions(curr_word)
    return {
        "status": "success",
            # Log only on gesture change
            if gesture_label != last_gesture:
                logger.info(f"Gesture changed: '{last_gesture}' -> '{gesture_label}'")
                last_gesture = gesture_label

            # Run Virtual Mouse coordinate mapping & pointer movement
            vm_result = None
            if virtual_mouse.enabled:
                if detected_hands:
                    vm_result = virtual_mouse.process_hand(detected_hands[0], frame_w=w, frame_h=h)
                else:
                    vm_result = virtual_mouse.process_hand(None, frame_w=w, frame_h=h)
            else:
                virtual_mouse.reset()

            cursor_x = vm_result["cursor_x"] if vm_result else 0
            cursor_y = vm_result["cursor_y"] if vm_result else 0
            tracking_state = vm_result["tracking_state"] if vm_result else "Disabled"
                
            # Render active Phase 1 overlays on the frame
            t_vis_start = time.perf_counter()
            from modules.visualizer import draw_visuals
            frame = draw_visuals(
                frame=frame,
                detected_hands=detected_hands,
                mp_results=mp_results,
                config=config,
                fps=fps_smooth,
                gesture=gesture_label,
                confidence=gesture_confidence,
                click_state=vm_result
            )
            t_visuals = time.perf_counter() - t_vis_start
                
            # Compress to JPEG and base64 encode
            t_enc_start = time.perf_counter()
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            t_encode = time.perf_counter() - t_enc_start
            
            # FPS Calculation
            now = time.perf_counter()
            delta = max(now - last_fps_tick, 1e-6)
            instant_fps = 1.0 / delta
            fps_smooth = instant_fps if fps_smooth == 0 else (fps_smooth * 0.85 + instant_fps * 0.15)
            last_fps_tick = now
            
            # Send live telemetry + frame over WebSocket
            payload = {
                "fps": float(round(fps_smooth, 1)),
                "hands": len(detected_hands),
                "gesture": gesture_label,
                "confidence": float(round(gesture_confidence, 3)),
                "camera_status": "Connected",
                "frame": f"data:image/jpeg;base64,{frame_b64}",
                "cursor_x": cursor_x,
                "cursor_y": cursor_y,
                "tracking_state": tracking_state,
                "pinch_distance": vm_result.get("pinch_distance", 0.0) if vm_result else 0.0,
                "click_status": vm_result.get("click_status", "OPEN") if vm_result else "OPEN",
            t_enc_start = time.perf_counter()
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            t_encode = time.perf_counter() - t_enc_start
            
            # FPS Calculation
            now = time.perf_counter()
            delta = max(now - last_fps_tick, 1e-6)
            instant_fps = 1.0 / delta
            fps_smooth = instant_fps if fps_smooth == 0 else (fps_smooth * 0.85 + instant_fps * 0.15)
            last_fps_tick = now
            
            # Send live telemetry + frame over WebSocket
            payload = {
                "fps": float(round(fps_smooth, 1)),
                "hands": len(detected_hands),
                "gesture": gesture_label,
                "confidence": float(round(gesture_confidence, 3)),
                "camera_status": "Connected",
                "frame": f"data:image/jpeg;base64,{frame_b64}",
                "cursor_x": cursor_x,
                "cursor_y": cursor_y,
                "tracking_state": tracking_state,
                "pinch_distance": vm_result.get("pinch_distance", 0.0) if vm_result else 0.0,
                "click_status": vm_result.get("click_status", "OPEN") if vm_result else "OPEN",
                "click_counter": vm_result.get("click_counter", 0) if vm_result else 0,
                "current_action": vm_result.get("current_action", "None") if vm_result else "None",
          
                "right_click_status": vm_result.get("right_click_status", "OPEN") if vm_result else "OPEN",
                "right_click_counter": vm_result.get("right_click_counter", 0) if vm_result else 0,
                "right_pinch_distance": vm_result.get("right_pinch_distance", 0.0) if vm_result else 0.0,
                # Phase 3.4 — Scroll telemetry
                "scroll_mode": vm_result.get("scroll_mode", False) if vm_result else False,
                "scroll_direction": vm_result.get("scroll_direction", "NONE") if vm_result else "NONE",
                "scroll_speed": vm_result.get("scroll_speed", 0.0) if vm_result else 0.0,
                "scroll_counter": vm_result.get("scroll_counter", 0) if vm_result else 0,
                # Phase 3.4 — Volume telemetry
                "volume_mode": vm_result.get("volume_mode", False) if vm_result else False,
            
            # FPS Calculation
            now = time.perf_counter()
            delta = max(now - last_fps_tick, 1e-6)
            instant_fps = 1.0 / delta
            fps_smooth = instant_fps if fps_smooth == 0 else (fps_smooth * 0.85 + instant_fps * 0.15)
            last_fps_tick = now
            
            # Send live telemetry + frame over WebSocket
            payload = {
                "fps": float(round(fps_smooth, 1)),
                "hands": len(detected_hands),
                "gesture": gesture_label,
                "confidence": float(round(gesture_confidence, 3)),
                "camera_status": "Connected",
                "frame": f"data:image/jpeg;base64,{frame_b64}",
                "cursor_x": cursor_x,
                "cursor_y": cursor_y,
                "tracking_state": tracking_state,
                "pinch_distance": vm_result.get("pinch_distance", 0.0) if vm_result else 0.0,
                "click_status": vm_result.get("click_status", "OPEN") if vm_result else "OPEN",
                "click_counter": vm_result.get("click_counter", 0) if vm_result else 0,
                "current_action": vm_result.get("current_action", "None") if vm_result else "None",
                # Phase 3.3 — Right Click telemetry
                "right_click_status": vm_result.get("right_click_status", "OPEN") if vm_result else "OPEN",
                "right_click_counter": vm_result.get("right_click_counter", 0)
            t_enc_start = time.perf_counter()
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            t_encode = time.perf_counter() - t_enc_start
            
            # FPS Calculation
            now = time.perf_counter()
            delta = max(now - last_fps_tick, 1e-6)
            instant_fps = 1.0 / delta
            fps_smooth = instant_fps if fps_smooth == 0 else (fps_smooth * 0.85 + instant_fps * 0.15)
            last_fps_tick = now
            
            primary_hand = detected_hands[0] if detected_hands else None
            index_tip_x = float(round(primary_hand.landmarks[8][0], 4)) if (primary_hand and len(primary_hand.landmarks) > 8) else None
            index_tip_y = float(round(primary_hand.landmarks[8][1], 4)) if (primary_hand and len(primary_hand.landmarks) > 8) else None

            # Compute live pinch distance for virtual keyboard: Middle Finger (12) and Thumb (4)
                "drag_counter": vm_result.get("drag_counter", 0) if vm_result else 0,
                "drag_duration": vm_result.get("drag_duration", 0.0) if vm_result else 0.0,
                # Resource metrics
                "cpu_usage": float(cpu_usage),
                "ram_usage": float(ram_usage),
            }
            
            t_send_start = time.perf_counter()
            await websocket.send_json(payload)
            t_send = time.perf_counter() - t_send_start
            
            t_total = time.perf_counter() - t0
            
            # Maintain roughly target frame rate
            elapsed = time.perf_counter() - loop_start
            interval = max(0.001, 1.0 / max(config.camera_fps, 1) - elapsed)
            await asyncio.sleep(interval)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GestureOS AI - Web Dashboard</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        background: "#080710",
                        glass: {
                            light: "rgba(255, 255, 255, 0.05)",
                            border: "rgba(255, 255, 255, 0.06)",
                            glow: "rgba(59, 130, 246, 0.15)",
                        },
                        accent: {
                            blue: "#3b82f6",
                            purple: "#8b5cf6",
                            green: "#10b981",
                        }
                    },
                    fontFamily: {
                        sans: ["Outfit", "Inter", "sans-serif"],
                        mono: ["JetBrains Mono", "Fira Code", "monospace"],
                    }
                }
            }
        }
    </script>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    
    <!-- React & Babel CDNs -->
    <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

    <style>
        body {
            background-color: #080710;
            color: #e2e8f0;
            font-family: 'Outfit', 'Inter', sans-serif;
        }
     
                "drag_status": vm_result.get("drag_status", "IDLE") if vm_result else "IDLE",
                "drag_duration": vm_result.get("drag_duration", 0.0) if vm_result else 0.0,
                "drag_counter": vm_result.get("drag_counter", 0) if vm_result else 0,
            }

            
            t_send_start = time.perf_counter()
            await websocket.send_json(payload)
            t_send = time.perf_counter() - t_send_start
            
            t_total = time.perf_counter() - t0
            
            # Maintain roughly target frame rate
            elapsed = time.perf_counter() - loop_start
            interval = max(0.001, 1.0 / max(config.camera_fps, 1) - elapsed)
            await asyncio.sleep(interval)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
            </svg>
        );

        const BellIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
                <polyline points="3 3 3 8 8 8"/>
            </svg>
        );

        const ActivityIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                <path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8.5" />
                <path d="M10 18H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2v0a2 2 0 0 1 2 2v2" />
                <path d="M6 14v0a6 6 0 0 0 12 0v-3" />
                <path d="M18 15h1a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2h-9a6 6 0 0 1-6-6v0" />
            </svg>
        );

        const CameraIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
                <circle cx="12" cy="13" r="3"/>
            </svg>
        );

        const VideoOffIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M10.66 6H14.5a2.5 2.5 0 0 1 2.5 2.5v3.84M2 2l20 20M3.5 8H4M18.5 8H19a2.5 2.5 0 0 1 2.5 2.5v3a2.5 2.5 0 0 1-.5 1.5M7.34 16H4.5A2.5 2.5 0 0 1 2 13.5v-5A2.5 2.5 0 0 1 4.5 6h.84M17 17H7a2.5 2.5 0 0 1-2.5-2.5V10.5"/>
            </svg>
        );

        const CpuIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <rect x="4" y="4" width="16" height="16" rx="2"/>
                <path d="M9 9h6v6H9zM9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 15h3M1 9h3M1 15h3"/>
            </svg>
        );

        const SparklesIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            </svg>
        );

        const UserIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
            </svg>
        );

        const BellIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
            </svg>
        );

        const SettingsIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" heig
                <polygon points="2 17 12 22 22 17"/>
                <polygon points="2 12 12 17 22 12"/>
            </svg>
        );

        const MousePointerIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="m3 3 7.07 16.97 2.51-7.39 7.39-2.51L3 3z" />
                <path d="m13 13 6 6" />
            </svg>
        );

        function App() {
            const [fps, setFps] = useState(0);
            const [hands, setHands] = useState(0);
            const [gesture, setGesture] = useState('None');
            const [confidence, setConfidence] = useState(0);
            const [cameraStatus, setCameraStatus] = useState('Disconnected');
            const [frame, setFrame] = useState(null);
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            </svg>
        );

        const RotateCcwIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <polyline points="3 3 3 8 8 8"/>
            </svg>
        );

        const ActivityIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
        );

        const ChevronRightIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <polyline points="9 18 15 12 9 6"/>
            </svg>
        );

        const TrendingUpIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                <polyline points="17 6 23 6 23 12"/>
            </svg>
        );

        const SlidersIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <line x1="4" y1="21" x2="4" y2="14"/>
                <line x1="4" y1="10" x2="4" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12" y2="3"/>
                <line x1="20" y1="21" x2="20" y2="16"/>
                <line x1="20" y1="12" x2="20" y2="3"/>
                <line x1="1" y1="14" x2="7" y2="14"/>
                <line x1="9" y1="8" x2="15" y2="8"/>
                <line x1="17" y1="16" x2="23" y2="16"/>
            </svg>
        );

        const LayersIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                <polygon points="2 17 12 22 22 17"/>
                <polygon points="2 12 12 17 22 12"/>
            </svg>
        );

        const MousePointerIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke=
            const prevGestureRef = useRef('None');
            const socketRef = useRef(null);
            const eventIdCounterRef = useRef(0);

            // Connect to the WebSocket backend
            useEffect(() => {
                const connectWS = () => {
                    setSocketStatus('connecting');
                            setFps(data.fps);
                            setHands(data.hands);
                            setGesture(data.gesture);
                            setConfidence(data.confidence);
                            setCameraStatus(data.camera_status);
                            setFrame(data.frame);
                            setCursorX(data.cursor_x || 0);
                            setCursorY(data.cursor_y || 0);
                            setTrackingState(data.tracking_state || 'Disabled');
                            setPinchDistance(data.pinch_distance || 0.0);
                            setClickStatus(data.click_status || 'OPEN');
                            setClickCounter(data.click_counter || 0);
                            setCurrentAction(data.current_action || 'None');
                            // Phase 3.3 — Right Click
                            const prevRC = prevRightClickStatusRef.current;
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            </svg>
        );

        function App() {
            const [fps, setFps] = useState(0);
            const [hands, setHands] = useState(0);
            const [gesture, setGesture] = useState('None');
            const [confidence, setConfidence] = useState(0);
            const [cameraStatus, setCameraStatus] = useState('Disconnected');
            const [frame, setFrame] = useState(null);
            
            const [socketStatus, setSocketStatus] = useState('disconnected');
            const [events, setEvents] = useState([]);
            const [activeMenu, setActiveMenu] = useState('dashboard');
            const [isResetting, setIsResetting] = useState(false);
            const [isCameraLoading, setIsCameraLoading] = useState(false);

            // Virtual Mouse States
            const [virtualMouseEnabled, setVirtualMouseEnabled] = useState(false);
            const [virtualMouseSensitivity, setVirtualMouseSensitivity] = useState(1.5);
            const [virtualMouseDeadZone, setVirtualMouseDeadZone] = useState(0.15);
            const [virtualMouseSmoothing, setVirtualMouseSmoothing] = useState(0.20);
            const [virtualMouseClickThreshold, setVirtualMouseClickThreshold] = useState(0.05);
            const [virtualMouseRightClickThreshold, setVirtualMouseRightClickThreshold] = useState(0.05);
            
            const [cursorX, setCursorX] = useState(0);
            const [cursorY, setCursorY] = useState(0);
            const [trackingState, setTrackingState] = useState('Disabled');
            const [pinchDistance, setPinchDistance] = useState(0.0);
            const [clickStatus, setClickStatus] = useState('OPEN');
            const [clickCounter, setClickCounter] = useState(0);
            const [currentAction, setCurrentAction] = useState('None');
            // Phase 3.3 — Right Click
            const [rightClickStatus, setRightClickStatus] = useState('OPEN');
            const [rightClickCounter, setRightClickCounter] = useState(0);
            const [rightPinchDistance, setRightPinchDistance] = useState(0.0);
            const prevRightClickStatusRef = useRef('OPEN');
            // Phase 3.4 — Scroll Control
            const [scrollMode, setScrollMode] = useState(false);
            const [scrollDirection, setScrollDirection] = useState('NONE');
            const [scrollSpeed, setScrollSpeed] = useState(0.0);
            const [scrollCounter, setScrollCounter] = useState(0);
            const [virtualMouseScrollSensitivity, setVirtualMouseScrollSensitivity] = useState(5.0);
            const [virtualMouseScrollDeadZone, setVirtualMouseScrollDeadZone] = useState(0.04);
            const [virtualMouseScrollSmoothing, setVirtualMouseScrollSmoothing] = useState(0.25);
            const prevScrollModeRef = useRef(false);
            // Phase 3.4 — Volume Control
            const [volumeMode, setVolumeMode] = useState(false);
            const [volumeLevel, setVolumeLevel] = useState(0);
            const [volumeDistance, 
                            setVolumeMode(newVM);
                            setVolumeLevel(data.v
                            console.error('Error decoding WebSocket JSON payload:', err);
                        }
                    };

                    ws.onclose = () => {
                        setSocketStatus('disconnected');
                                    confidence: 1.0,
                                    action: 'Scroll Mode activated | gesture=index_middle_up'
                                }, ...prev].slice(0, 50));
                            } else if (!newSM && prevSM) {
                                const timeString = new Date().toLocaleTimeString();
                                eventIdCounterRef.current += 1;
                                setEvents(prev => [{
                                    id: `${Date.now()}-${eventIdCounterRef.current}`,
                                    timestamp: timeString,
                                    gesture: 'Scroll Stop',
                                    confidence: 1.0,
                                    action: `Scroll Mode deactivated | total events=${data.scroll_counter || 0}`
                                }, ...prev].slice(0, 50));
                            }
                            prevScrollModeRef.current = newSM;


            const prevGestureRef = useRef('None');
            const socketRef = useRef(null);
            const eventIdCounterRef = useRef(0);

            // Connect to the WebSocket backend
            useEffect(() => {
                const connectWS = () => {
                    setSocketStatus('connecting');
                    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
                    console.log(`Connecting to WebSocket: ${wsUrl}`);
                    
                    const ws = new WebSocket(wsUrl);
                    socketRef.current = ws;

                    ws.onopen = () => {
                        setSocketStatus('connected');
                        console.log('WebSocket connection established');
                    };

                    ws.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            setFps(data.fps);
                            setHands(data.hands);
                            setGesture(data.gesture);
                            setConfidence(data.confidence);
                            setCameraStatus(data.camera_status);
                            setFrame(data.frame);
                            setCursorX(data.cursor_x || 0);
                            setCursorY(data.cursor_y || 0);
                            setTrackingState(data.tracking_state || 'Disabled');
                            setPinchDistance(data.pinch_distance || 0.0);
                            setClickStatus(data.click_status || 'OPEN');
                    .then(data => {
                        setShowLandmarks(data.show_landmarks);
                        setShowConnections(data.show_connections);
                        setShowBoundingBox(data.show_bounding_box);
                        setShowFingerStates(data.show_finger_states);
                        setShowDistanceMeter(data.show_distance_meter);
                        setShowDebugPanel(data.show_debug_panel);
                        setShowHud(data.show_hud);
                        
                        setVirtualMouseEnabled(data.virtual_mouse_enabled);
                        setVirtualMouseSensitivity(data.virtual_mouse_sensitivity);
                        setVirtualMouseDeadZone(data.virtual_mouse_dead_zone);
                        setVirtualMouseSmoothing(data.virtual_mouse_smoothing);
                        if (data.virtual_mouse_click_threshold !== undefined) {
                            setVirtualMouseClickThreshold(data.virtual_mouse_click_threshold);
                        }
                        if (data.virtual_mouse_right_click_threshold !== undefined) {
                            setVirtualMouseRightClickThreshold(data.virtual_mouse_right_click_threshold);
                        }
                        if (data.virtual_mouse_scroll_sensitivity !== undefined) {
                            setVirtualMouseScrollSensitivity(data.virtual_mouse_scroll_sensitivity);
                        }
                        if (data.virtual_mouse_scroll_dead_zone !== undefined) {
                            setVirtualMouseScrollDeadZone(data.virtual_mouse_scroll_dead_zone);
                        }
                        if (data.virtual_mouse_scroll_smoothing !== undefined) {
                            setVirtualMouseScrollSmoothing(data.virtual_mouse_scroll_smoothing);
                        }
                        if (data.virtual_mouse_volume_min_distance_px !== undefined) {
                            setVirtualMouseVolumeMinDistancePx(data.virtual_mouse_volume_min_distance_px);
                        }
                        if (data.virtual_mouse_volume_max_distance_px !== undefined) {
                            setVirtualMouseVolumeMaxDistancePx(data.virtual_mouse_volume_max_distance_px);
                        }
                        if (data.virtual_mouse_volume_smoothing !== undefined) {
                            setVirtualMouseVolumeSmoothing(data.virtual_mouse_volume_smoothing);
                        }
                    })
                    .catch(err => console.error('Error loading config settings:', err));

                // Escape key emergency stop listener
                const handleEscape = (e) => {
                    if (e.key === 'Escape') {
                        setVirtualMouseEnabled(false);
                        updateSetting('virtual_mouse_enabled', false);
                        setRightClickStatus('OPEN');
                        setScrollMode(false);
                        setScrollDirection('NONE');
                        logSystemEvent('\u26a0 EMERGENCY STOP: Virtual mouse disabled via ESC key.');
                    }
                };
                window.addEventListener('keydown', handleEscape);

                return () => {
                    window.removeEventListener('keydown', handleEscape);
                    if (socketRef.current) {
                        socketRef.current.close();
                    }
                };
            }, []);
            const [virtualMouseClickThreshold, setVirtualMouseClickThreshold] = useState(0.05);
            const [virtualMouseRightClickThreshold, setVirtualMouseRightClickThreshold] = useState(0.05);
            
            const [cursorX, setCursorX] = useState(0);
            const [cursorY, setCursorY] = useState(0);
                                    timestamp: timeString,
                                    gesture: 'Right Click',
                                    confidence: 1.0,
                                    action: `Right Click triggered | gesture=thumb_middle_pinch | dist=${(data.right_pinch_distance || 0).toFixed(4)}`
                                    };
                                    setEvents(prev => [volumeEvent, ...prev].slice(0, 50));
                                    prevVolumeLevelRef.current = data.volume_level;
                                }
                            } else if (!newVM) {
                                prevVolumeLevelRef.current = -1;
                            }

                            // Phase 3.5 — Brightness
                            const newBM = data.brightness_mode || false;
                            setBrightnessMode(newBM);
                            setBrightnessLevel(data.brightness_level || 0);
                            setBrightnessDistance(data.brightness_distance || 0.0);
                            // Log brightness changes on integer level change
                            if (newBM && data.brightness_level !== prevBrightnessLevelRef.current) {
                                if (data.brightness_level !== undefined) {
                                    const timeString = new Date().toLocaleTimeString();
                                    eventIdCounterRef.current += 1;
                                    const brightnessEvent = {
                                        id: `${Date.now()}-${eventIdCounterRef.current}`,
                                        timestamp: timeString,
                                        gesture: 'Brightness',
                                        confidenc
                        if (data.virtual_mouse_scroll_smoothing !== undefined) {
                            setVirtualMouseScrollSmoothing(data.virtual_mouse_scroll_smoothing);
                        }
                        if (data.virtual_mouse_volume_min_distance_px !== undefined) {
                            setVirtualMouseVolumeMinDistancePx(data.virtual_mouse_volume_min_distance_px);
                        }
                        if (data.virtual_mouse_volume_max_distance_px !== undefined) {
                            setVirtualMouseVolumeMaxDistancePx(data.virtual_mouse_volume_max_distance_px);
                        }
                        if (data.virtual_mouse_volume_smoothing !== undefined) {
                            setVirtualMouseVolumeSmoothing(data.virtual_mouse_volume_smoothing);
                        }
                    })
                    .catch(err => console.error('Error loading config settings:', err));

                // Escape key emergency stop listener
                                    id: `${Date.now()}-${eventIdCounterRef.current}`,
                                    timestamp: timeString,
                                    gesture: 'Mode Switch',
                                    confidence: 1.0,
                                    action: `[MODE] ${newAM}`
                                };
                                setEvents(prev => [modeEvent, ...prev].slice(0, 50));
                                prevActiveModeRef.current = newAM;
                            }

                            // Trigger logs on gesture change (ignoring empty/None/unknown)
                            if (data.gesture !== prevGestureRef.current) {
                                if (data.gesture && data.gesture !== 'None' && data.gesture !== 'unknown') {
                                    const timeString = new Date().toLocaleTimeString();
                                    eventIdCounterRef.current += 1;
                                    const newEvent = {
                                        id: `${Date.now()}-${eventIdCounterRef.current}`,
                                        timestamp: timeString,
                                        gesture: data.gesture,
                                        confidence: data.confidence,
                                        action: `Triggered mapped shortcut for [${data.gesture}]`
                                    };
                                    setEvents(prev => [newEvent, ...prev].slice(0, 50));
                                }
                                prevGestureRef.current = data.gesture;
                            }
                        } catch (err) {
                            console.error('Error decoding WebSocket JSON payload:', err);
                        }
                    };

                    ws.onclose = () => {
                        setSocketStatus('disconnected');
                        console.log('WebSocket connection lost, retrying in 3 seconds...');
                        setTimeout(connectWS, 3000);
                    };

                    ws.onerror = (error) => {
                        console.error('WebSocket encountered an error:', error);
                    };
                };

                connectWS();

                // Fetch initial switches configuration from backend
                fetch('/api/settings')
                    .then(res => res.json())
                    .then(data => {
                        setShowLandmarks(data.show_landmarks);
                        setShowConnections(data.show_connections);
                        setShowBoundingBox(data.show_bounding_box);
                        setShowFingerStates(data.show_finger_states);
                        setShowDistanceMeter(data.show_distance_meter);
                        setShowDebugPanel(data.show_debug_panel);
                        setShowHud(data.show_hud);
                        
                        setVirtualMouseEnabled(data.virtual_mouse_enabled);
                        setVirtual
            const [dragStatus, setDragStatus] = useState('IDLE');
            const [dragDuration, setDragDuration] = useState(0.0);
            const [dragCounter, setDragCounter] = useState(0);
            const [virtualMouseDragThresholdMs, setVirtualMouseDragThresholdMs] = useState(200.0);
            const prevDragStatusRef = useRef('IDLE');

            // Virtual Keyboard UI States
            const [hoveredKey, setHoveredKey] = useState('None');
            const [lastPressedKey, setLastPressedKey] = useState('None');
            const [typedText, setTypedText] = useState('');
            const [isShiftActive, setIsShiftActive] = useState(false);
            const [isCapsLockActive, setIsCapsLockActive] = useState(false);
            const [pressedKey, setPressedKey] = useState(null);
            const [hoverDuration, setHoverDuration] = useState(0.0);
            const [enableKeyboardSound, setEnableKeyboardSound] = useState(true);
            const [systemTypingEnabled, setSystemTypingEnabled] = useState(false);
            const [autocompleteEnabled, setAutocompleteEnabled] = useState(true);
            const [wpm, setWpm] = useState(0);
            const [accuracy, setAccuracy] = useState(100);
            const [currentWord, setCurrentWord] = useState('');
            const [recentWords, setRecentWords] = useState([]);
            const [predictions, setPredictions] = useState([]);
                        }
                        if (data.virtual_mouse_volume_smoothing !== undefined) {
                            setVirtualMouseVolumeSmoothing(data.virtual_mouse_volume_smoothing);
                        }
                        if (data.virtual_mouse_brightness_min_distance_px !== undefined) {
                            setVirtualMouseBrightnessMinDistancePx(data.virtual_mouse_brightness_min_distance_px);
                        }
                        if (data.virtual_mouse_brightness_max_distance_px !== undefined) {
                            setVirtualMouseBrightnessMaxDistancePx(data.virtual_mouse_brightness_max_distance_px);
                        }
                        if (data.virtual_mouse_brightness_smoothing !== undefined) {
                            setVirtualMouseBrightnessSmoothing(data.virtual_mouse_brightness_smoothing);
                        }
                    })
                    .catch(err => console.error('Error loading config settings:', err));

                // Escape key emergency stop listener
                const handleEscape = (e) => {
                    if (e.key === 'Escape') {
                        setVirtualMouseEnabled(false);
                        updateSetting('virtual_mouse_enabled', false);
                        setRightClickStatus('OPEN');
                        setScrollMode(false);
                        setScrollDirection('NONE');
                        logSystemEvent('\u26a0 EMERGENCY STOP: Virtual mouse disabled via ESC key.');
                    }
                };
                window.addEventListener('keydown', handleEscape);

                return () => {
                    window.removeEventListener('keydown', handleEscape);
                    if (socketRef.current) {
                        socketRef.current.close();
                    }
                };
            }, []);

            const logSystemEvent = (msg) => {
                const timeString = new Date().toLocaleTimeString();
                eventIdCounterRef.current += 1;
                const newEvent = {
                    id: `${Date.now()}-${eventIdCounterRef.current}`,
                    timestamp: timeString,
                    gesture: 'System',
                    confidence: 1.0,
                    action: msg
                };
                setEvents(prev => [newEvent, ...prev].slice(0, 50));
            };

            // REST API Actions
            const handleStartCamera = async () => {
                setIsCameraLoading(true);
                logSystemEvent("Camera stream start requested.");
                try {
                    const res = await fetch('/api/camera/start', { method: 'POST' });
                    const data = await res.json();
                    if (data.status === 'success') {
                        setCameraStatus('Connected');
                        logSystemEvent("Camera stream s
                    body: JSON.stringify(updates)
                }).catch(err => console.error("Error saving brush settings:", err));
            };

            const [webBrushSize, _setWebBrushSize] = useState(15);
            const webBrushSizeRef = useRef(15);
            const setWebBrushSize = (val) => {
                _setWebBrushSize(val);
                webBrushSizeRef.current = val;
                saveBrushSetting({ brush_size: val });
            };

            const [webBrushColor, _setWebBrushColor] = useState('#c6a0f6'); // Mauve
            const webBrushColorRef = useRef('#c6a0f6');
            const setWebBrushColor = (val) => {
                _setWebBrushColor(val);
                webBrushColorRef.current = val;
                saveBrushSetting({ brush_color: val });
            };

            const [webBrushColorName, _setWebBrushColorName] = useState('Mauve');
            const setWebBrushColorName = (val) => {
            const showHoverTrailRef = useRef(true);
            const setShowHoverTrail = (val) => {
                _setShowHoverTrail(val);
                showHoverTrailRef.current = val;
            };

            const [canvasWidth, _setCanvasWidth] = useState(640);
            const canvasWidthRef = useRef(640);
            const setCanvasWidth = (val) => {
                _setCanvasWidth(val);
                canvasWidthRef.current = val;
            };

            const [canvasHeight, _setCanvasHeight] = useState(360);
                    logSystemEvent("Tracking reset complete.");
                } catch (err) {
                    console.error('Error resetting tracking:', err);
                    logSystemEvent("Failed to reset tracking.");
                } finally {
                    setTimeout(() => setIsResetting(false), 800);
                }
            };

            const updateSetting = async (key, val) => {
                try {
                    await fetch('/api/settings/update', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ [key]: val })
                    });
                } catch (err) {
                    console.error('Error updating switch setting:', err);
                }
            };

            // Format confidence displays based on gesture states
            const formatConfidence = () => {
                if (gesture === 'None' || gesture === 'unknown' || gesture === 'No Model' || hands === 0) {
                    return '0%';
                }
                return `${(confidence * 100).toFixed(0)}%`;
            };

            return (
                <div className="flex h-screen bg-[#080710] font-sans antialiased text-gray-200 overflow-hidden">
                    
                    {/* Left Sidebar */}
                    <aside className="w-72 glass-panel border-r border-glass-border flex flex-col justify-between h-full z-10">
                        <div>
                            {/* Logo section - centered, minimal empty space */}
                            <div className="flex items-center gap-3 px-6 py-6 border-b border-glass-border justify-center">
                                <div className="p-2.5 bg-blue-500/10 rounded-xl border border-blue-500/20 text-accent-blue">
                                    <HandIcon className="w-6 h-6 stroke-[2]" />
                                </div>
                                <div>
                                    <h1 className="text-lg font-bold tracking-wider bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                                        GestureOS
                                    </h1>
                                    <p className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Intelligence Edition</p>
                                </div>
                            </div>

                            {/* Navigation */}
                            <nav className="px-4 py-6 space-y-2">
                                {[
                                    { id: 'dashboard', name: 'Dashboard', icon: LayersIcon },
                                    { id: 'mouse', name: 'Virtual Mouse', icon: MousePointerIcon },
                                    { id: 'shortcuts', name: 'Gestures Map', icon: SlidersIcon },
                                    { id: 'analytics', name: '
                                <p className="text-xs text-gray-400 mt-0.5">
                                    {activeMenu === 'dashboard' 
                                        ? 'Telemetry overview and input gesture mapping controls.' 
                                        : activeMenu === 'mouse' 
                                        ? 'Real-time mouse tracking coordinates, status, and settings.' 
                                        : 'Calibrate input settings and device thresholds.'}
                                </p>
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                    Engine Online
                                </div>

                                <span className="w-px h-6 bg-glass-border hidden md:inline-block" />

                                <button className="p-2.5 rounded-xl glass-card text-gray-400 hover:text-white relative group">
                                    <BellIcon className="w-5 h-5" />
                                    <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-blue-500 rounded-full border-2 border-backgro
                                            
                                            {/* Camera Feed Preview (2 Columns) */}
                                            <div className="lg:col-span-2 flex flex-col gap-4">
                                                <div className="glass-card rounded-2xl p-4 flex flex-col h-[480px] justify-between relative group overflow-hidden">
                                                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                                    
                                                    <div className="flex items-center justify-between pb-3 border-b border-glass-border">
                                                        <div className="flex items-center gap-2 text-sm">
                                                            <CameraIcon className="w-4 h-4 text-accent-blue" />
                                                            <span className="font-semibold text-gray-200">Device Stream Input</span>
                                                        </div>
                            // Hover Delay (150ms) and Debouncing (100ms)
                            if (detectedKey) {
                                lastHoverDetectTimeRef.current = wsNow;
                                if (detectedKey === candidateKeyRef.current) {
                                    const elapsed = (wsNow - candidateStartTimeRef.current) / 1000;
                                    setHoverDuration(elapsed);
                                    if (elapsed >= 0.150) {
                                        setHoveredKey(detectedKey);
                                        hoveredKeyRef.current = detectedKey;
                                    }
                                } else {
                                    candidateKeyRef.current = detectedKey;
                                    candidateStartTimeRef.current = wsNow;
                                    setHoverDuration(0.0);
                                }
                            } else {
                                let debounceElapsed = 0;
                                if (lastHoverDetectTimeRef.current) {
                                    debounceElapsed = (wsNow - lastHoverDetectTimeRef.current) / 1000;
                resizeObserver.observe(container);
                                    <>
                                        {/* Status Cards Grid */}
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                                            {/* FPS Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 text-accent-blue">
                                                    <ActivityIcon className="w-6 h-6" />
                                                </div>
                        
                        {/* Header Row - vertically aligned profile, mode status, notifications, settings, exit */}
                        <header className="h-20 border-b border-glass-border px-8 flex items-center justify-between backdrop-blur-md z-10 shrink-0">
                            <div>
                                <h2 className="text-xl font-bold tracking-wide text-white">
                                    {activeMenu === 'dashboard' ? 'System Monitor' : activeMenu === 'mouse' ? 'Virtual Mouse Monitor' : 'System Configuration'}
                                </h2>
                                <p className="text-xs text-gray-400 mt-0.5">
                                    {activeMenu === 'dashboard' 
                                        ? 'Telemetry overview and input gesture mapping controls.' 
                                        : activeMenu === 'mouse' 
                                        ? 'Real-time mouse tracking coordinates, status, and settings.' 
                                        : 'Calibrate input settings and device thresholds.'}
                                </p>
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                    Engine Online
                                </div>

                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className="p-3 bg-violet-500/10 rounded-xl border border-violet-500/20 text-purple-400">
                                                    <SparklesIcon className="w-6 h-6" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Current Gesture</p>
                                                    <div className="flex items-baseline gap-2 mt-1">
                                                        <p cla
                ctx.save();
                ctx.beginPath();
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                
                                            </div>

                                            {/* Camera Status Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className={`p-3 rounded-xl border transition-colors ${
                                                    cameraStatus === 'Connected' 
                                </div>

                                <button 
                                    onClick={handleStopCamera}
                                    className="p-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/30 text-red-400 hover:text-red-300 transition-all duration-300 group"
                                    title="Stop Engine"
                                >
                                    <LogOutIcon className="w-5 h-5" />
                                </button>
                            </div>
                        </header>

                        {/* Outer scrollable viewport */}
                        <div className="flex-1 overflow-y-auto p-8 scrollbar-thin">
                            <div className="max-w-6xl mx-auto space-y-6">
                                
                                {activeMenu === 'dashboard' ? (
                                    <>
                                        {/* Status Cards Grid */}
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5">
                                            {/* FPS Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className="p-3 b
                if (points.length === 1) {
                    const pt = points[0];
                    ctx.arc(pt.x, pt.y, size / 2, 0, 2 * Math.PI);
                    ctx.fill();
                } else if (points.length === 2) {
                    ctx.moveTo(points[0].x, points[0].y);
                    ctx.lineTo(points[1].x, points[1].y);
                    ctx.stroke();
                } else {
                    ctx.moveTo(points[0].x, points[0].y);
                    for (let i = 1; i < points.length - 1; i++) {
                        const xc = (points[i].x + points[i + 1].x) / 2;
                        const yc = (points[i].y + points[i + 1].y) / 2;
                        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
                    }
                    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
                    ctx.stroke();
                }
                ctx.restore();
            };

            // Draw smooth hover trail
            const drawHoverTrail = (ctx, trail) => {
                for (let i = 1; i < trail.length; i++) {
                    ctx.beginPath();
                    ctx.moveTo(trail[i - 1].x, trail[i - 1].y);
                    ctx.lineTo(trail[i].x, trail[i].y);
                    const opacity = (i / trail.length) * 0.4;

            const handleWebClear = () => {
                                                    <div className="flex items-baseline gap-2 mt-1">
                                                        <p className="text-2xl font-bold text-white tracking-tight capitalize">
                                                            {gesture === 'None' || gesture === 'unknown' ? 'Idle' : gesture}
                                                        </p>
                                                        <span className="text-xs text-gray-500 font-mono">({formatConfidence()})</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Active Mode Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className={`p-3 rounded-xl border transition-colors ${
                                                    activeMode === 'CURSOR' ? 'bg-blue-500/10 border-blue-500/20 text-accent-blue' :
                                                    activeMode === 'CLICK' ? 'bg-emerald-500/10 border-emerald-500/20 text-accent-green' :
                                                    activeMode === 'SCROLL' ? 'bg-teal-500/10 border-teal-500/20 text-teal-400' :
                                                    activeMode === 'VOLUME' ? 'bg-purple-500/10 border-purple-500/20 text-purple-400' :
                                                    'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'
                                                }`}>
                                                    <MousePointerIcon className="w-6 h-6" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Active Mode</p>
                                                    <p className="text-2xl font-bold text-white mt-1 tracking-tight">
                                                        {activeMode}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Volume Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className={`p-3 rounded-xl border transition-colors ${
                                                    volumeMode ? 'bg-purple-500/10 border-purple-500/20 text-purple-400 animate-pulse' : 'bg-zinc-500/10 border-zinc-500/20 text-gray-400'
                                                }`}>
                                                    <Volume2Icon className="w-6 h-6" />
                                                </div>
                        
                setRedoStack(prev => [...prev, popped]);
                redrawCanvas(nextUndo);
            };

            const handleWebRedo = () => {
                if (redoStack.length === 0) return;
                const nextRedo = [...redoStack];
                const popped = nextRedo.pop();
                setRedoStack(nextRedo);
                setUndoStack(prev => [...prev, popped]);
                redrawCanvas([...undoStack, popped]);
            };

            const handleWebClear = () => {
                setUndoStack([]);
                setRedoStack([]);
                const canvas = document.getElementById('drawing-canvas');
                if (canvas) {
                    const ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                }
            };

            const handleWebSave = () => {
                if (undoStack.length === 0) return;
                const tempCanvas = document.createElement('canvas');
                                            {/* Camera Feed Preview (2 Columns) */}
                                            <div className="lg:col-span-2 flex flex-col gap-4">
                                                <div className="glass-card rounded-2xl p-4 flex flex-col h-[480px] justify-between relative group overflow-hidden">
                                                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                                    
                                                    <div className="flex items-center justify-between pb-3 border-b border-glass-border">
                                                        <div className="flex items-center gap-2 text-sm">
                                                            <CameraIcon className="w-4 h-4 text-accent-blue" />
                                                            <span className="font-semibold text-gray-200">Device Stream Input</span>
                                                        </div>
                                                        <div className="flex items-center gap-1.5 text-xs text-gray-400">
                                                            <span className={`w-1.5 h-1.5 rounded-full ${
                                                                cameraStatus === 'Connected' ? 'bg-accent-green animate-ping' : 'bg-red-400'
                                                            }`} />
                                                            {cameraStatus === 'Connected' ? 'Streaming live' : 'Offline'}
                                                        </div>
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        logSystemEvent(`Saved web drawing to: ${data.filepath}`);
                        alert(`Drawing saved successfully to ${data.filepath}`);
                    } else {
                        logSystemEvent(`Failed to save web drawing: ${data.message}`);
                        alert(`Failed to save drawing: ${data.message}`);
                    }
                })
                .catch(err => {
                    console.error('Error saving drawing:', err);
                    alert('Error saving drawing.');
                });
            };

            useEffect(() => {
                if (activeMenu === 'drawing') {
                    setTimeout(() => {
                        redrawCanvas(undoStack);
                    }, 50);
                }
            }, [activeMenu]);

            const getCurrentWordJS = (text) => {
                if (!text) return "";
                const match = text.match(new RegExp("[\\w'-]+$"));
                return match ? match[0] : "";
            };
            const smoothXRef = useRef(null);
            const smoothYRef = useRef(null);
            const candidateKeyRef = useRef(null);
            const candidateStartTimeRef = useRef(null);
            const lastHoverDetectTimeRef = useRef(null);
            const hoveredKeyRef = useRef('None');
            const pinchActiveRef = useRef(false);


            // Switches State
            const [showLandmarks, setShowLandmarks] = useState(true);
            const [showConnections, setShowConnections] = useState(true);
            const [showBoundingBox, setShowBoundingBox] = useState(true);
            const [showFingerStates, setShowFingerStates] = useState(true);
            const [showDistanceMeter, setShowDistanceMeter] = useState(true);
            const [showDebugPanel, setShowDebugPanel] = useState(true);
            const [showHud, setShowHud] = useState(true);

            const prevGestureRef = useRef('None');
                                                            disabled={cameraStatus !== 'Connected' || isCameraLoading}
                                                            className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-white/5 hover:bg-red-500/10 hover:text-red-400 border border-glass-border hover:border-red-500/25 disabled:opacity-50 disabled:hover:bg-white/5 disabled:hover:text-gray-400 text-gray-300 font-semibold rounded-xl transition-all duration-300"
                                                        >
                                                            <SquareIcon className="w-4 h-4" />
                                                            Stop Camera
                                                        </button>

                                                        <button
                                                            onClick={handleResetTracking}
                                                            disabled={isResetting}
                                                            className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-white/5 hover:bg-white/10 border border-glass-border disabled:opacity-50 text-gray-300 font-semibold rounded-xl transition-all duration-300"
                                                        >
                                                            <RotateCcwIcon className={`w-4 h-4 ${isResetting ? 'animate-spin' : ''}`} />
              
                    ws.onopen = () => {
                        setSocketStatus('connected');
                        console.log('WebSocket connection established');
                    };

                    ws.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            setFps(data.fps);
                            setHands(data.hands);
                            setGesture(data.gesture);
                            setConfidence(data.confidence);
                            setCameraStatus(data.camera_status);
                            if (data.frame) {
                                if (!hasFrameRef.current) {
                                    hasFrameRef.current = true;
                                    setHasFrameState(true);
                                                                {scrollDirection === 'UP' ? '▲ UP' : scrollDirection === 'DOWN' ? '▼ DOWN' : '—'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Scroll Speed</span>
                                                            <span className="font-mono font-bold text-white">
                                                                {scrollSpeed.toFixed(2)}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm">
                                                            <span className="text-gray-400">Scroll Counter</span>
                                                            <span className="font-mono font-bold text-teal-400">
                                                                {scrollCounter}
                                                            </span>
                                                        </div>
                                                    </div>
# === GAP: MISSING LINE 1497 ===
# === GAP: MISSING LINE 1498 ===
# === GAP: MISSING LINE 1499 ===
                            setCursorX(data.cursor_x || 0);
                            setCursorY(data.cursor_y || 0);
                            setTrackingState(data.tracking_state || 'Disabled');
                            setPinchDistance(data.pinch_distance || 0.0);
                            setClickStatus(data.click_status || 'OPEN');
                            setClickCounter(data.click_counter || 0);
                            setCurrentAction(data.current_action || 'None');

                            // Key Hover Detection for Web Keyboard
                            let detectedKey = null;
                            const wsNow = Date.now();

                            if (data.index_tip_x !== undefined && data.index_tip_y !== undefined && data.index_tip_x !== null && data.index_tip_y !== null) {
                                const rawX = data.index_tip_x;
                                const rawY = data.index_tip_y;
                                const xMirrored = 1.0 - rawX; // Mirror horizontal to match screen direction
                                                                <span>Waiting for events...</span>
                                                            </div>
                                                        ) : (
                                                            <div className="space-y-2.5">
                                                                {events.map((evt) => (
                                                                    <div key={evt.id} className="border-b border-white/5 pb-1.5 last:border-0 last:pb-0">
                                                                        <div className="flex items-center justify-between text-gray-500 font-semibold mb-0.5">
                                                                            <span>[{evt.timestamp}]</span>
                                                                            {evt.gesture !== 'System' && <span className="text-accent-green">{(evt.confidence * 100).toFixed(0)}%</span>}
                                                                        </div>
                                                                        <div className="text-white">
                                                                            {evt.gesture === 'System' ? (
                                                                                <span>Event: <span className="text-accent-purple font-bold">System Log</span></span>
                                                                            ) : (
                                                                                <span>Gesture: <span className="capitalize text-accent-blue font-bold">{evt.gesture}</span></span>
                                                            <span className="text-gray-400">Scroll Speed</span>
                                                            <span className="font-mono font-bold text-white">
                                                                {scrollSpeed.toFixed(2)}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Scroll Counter</span>
                                                            <span className="font-mono font-bold text-teal-400">
                                                                {scrollCounter}
                                                    </div>
                                                </div>
                                            </div>

                                        </div>
                                    </>
                                ) : activeMenu === 'mouse' ? (
                                    <>
                                        {/* Hero Header Section */}
                                        <div className="glass-panel rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between border border-glass-border relative overflow-hidden">
                                            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                            <div>
                                                <h2 className="text-2xl font-bold tracking-wide text-white">Virtual Mouse Controls</h2>
                                                <p className="text-xs text-gray-400 mt-1 max-w-xl">
                                                    Control your system cursor in real-time using your index finger. Calibrate tracking properties below.
                                                </p>
                                            </div>
                                            <div className="mt-4 md:mt-0">
                                                <span className={`px-4 
                                        setHoveredKey(detectedKey);
                                        hoveredKeyRef.current = detectedKey;
                                    }
                                } else {
                                    candidateKeyRef.current = detectedKey;
                                    candidateStartTimeRef.current = wsNow;
                                    setHoverDuration(0.0);
                                }
                            } else {
                                let debounceElapsed = 0;
                                if (lastHoverDetectTimeRef.current) {
                                    debounceElapsed = (wsNow - lastHoverDetectTimeRef.current) / 1000;
                                }
                                if (debounceElapsed >= 0.100 || !lastHoverDetectTimeRef.current) {
                                    candidateKeyRef.current = null;
                                    candidateStartTimeRef.current = null;
                                    setHoverDuration(0.0);
                                    setHoveredKey('None');
                                    hoveredKeyRef.current = 'None';
                                }
                            }

# === GAP: MISSING LINE 1581 ===
# === GAP: MISSING LINE 1582 ===
# === GAP: MISSING LINE 1583 ===
# === GAP: MISSING LINE 1584 ===
# === GAP: MISSING LINE 1585 ===
# === GAP: MISSING LINE 1586 ===
# === GAP: MISSING LINE 1587 ===
# === GAP: MISSING LINE 1588 ===
# === GAP: MISSING LINE 1589 ===
# === GAP: MISSING LINE 1590 ===
# === GAP: MISSING LINE 1591 ===
# === GAP: MISSING LINE 1592 ===
# === GAP: MISSING LINE 1593 ===
                                                            </div>
                                                        </label>

                                                        {/* Sensitivity Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Sensitivity</span>
                                                                <span className="text-white font-mono">{virtualMouseSensitivity.toFixed(2)}x</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.5" 
                                                                max="3.0" 
                                                                step="0.1"
                                                                value={virtualMouseSensitivity} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseSensitivity(val);
                                                                    updateSetting('virtual_mouse_sensitivity', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Dead Zone Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Dead Zone Padding</span>
                                                                <span className="text-white font-mono">{Math.round(virtualMouseDeadZone * 100)}%</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.05" 
                                                                max="0.30" 
        root.render(<App />);
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTML_CONTENT

if __name__ == "__main__":
    uvicorn.run("web_backend:app", host="127.0.0.1", port=8000, log_level="info")

                                        gesture: data.gesture,
                                        confidence: data.confidence,
                                        action: `Triggered mapped shortcut for [${data.gesture}]`
                                    };
                                    setEvents(prev => [newEvent, ...prev].slice(0, 50));
                                }
                                prevGestureRef.current = data.gesture;
                            }


                                        confidence: data.confidence,
                                        action: `Triggered mapped shortcut for [${data.gesture}]`
                                    };
                                    setEvents(prev => [newEvent, ...prev].slice(0, 50));
                                }
                                prevGestureRef.current = data.gesture;
                            }

                            // Phase 5.1 — Air Drawing Canvas
                            if (activeMenuRef.current === 'drawing') {
                                                            <span className="font-mono font-bold text-white">
                                                                {scrollSpeed.toFixed(2)}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Scroll Counter</span>
                                                            <span className="font-mono font-bold text-teal-400">
                                                                {scrollCounter}
                                                            </span>
                                                        </div>

                                                        {/* Phase 3.4 Volume Section */}
                                                        <div className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold pt-1">Volume Control (Thumb + Pinky Up)</div>

                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Volume Mode Status</span>
                        
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Volume Min Distance Slider */}
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Current Volume Level</span>
                                                                rightClickStatus === 'RIGHT_CLICK' ? 'text-orange-400' :
                                                                rightClickStatus === 'PINCH' ? 'text-amber-300' :
                                                                rightClickStatus === 'RELEASE' ? 'text-accent-blue' : 'text-white'
                                                            }`}>
                                                                {rightClickStatus}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Right Pinch Distance</span>
                                                            <span className="font-mono font-bold text-white">
                                                                {rightPinchDistance.toFixed(4)}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Right Click Counter</span>
                                                            <span className="font-mono font-bold text-orange-400">
                                                                {rightClickCounter}
                                                            </span>
                                                        </div>

                                                        {/* Phase 3.4 Scroll Section */}
                                                        <div className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold pt-1">Scroll Mode (Index + Middle Up)</div>

                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Scroll Mode Status</span>
                                                            <span className={`font-semibold ${
                                                                scrollMode ? 'text-teal-400' : 'text-white'
                                                            }`}>
                                                                {scrollMode ? 'ACTIVE' : 'IDLE'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-g
                                                                    updateSetting('virtual_mouse_volume_max_distance_px', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Volume Smoothing Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Volume Smoothing</span>
                                                                <span className="text-white font-mono">{virtualMouseVolumeSmoothing.toFixed(2)}</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.05" 
                                                                max="0.50" 
                                                                step="0.01"
                                                                value={virtualMouseVolumeSmoothing} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseVolumeSmoothing(val);
                                                                    updateSetting('virtual_mouse_volume_smoothing', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="glass-card rounded-2xl p-8 text-center text-gray-400">
                                        <p>This page is currently under construction. Please use the Dashboard or Virtual Mouse navigation links.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </main>
                </div>
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTML_CONTENT

if __name__ == "__main__":
    uvicorn.run("web_backend:app", host="127.0.0.1", port=8000, log_level="info")

                                        smoothedY = filterYRef.current.filter(mappedY, nowMs);
                                    smoothedPinchDistRef.current = 0.0;
                                    consecutivePinchFramesRef.current = 0;
                                    consecutiveReleaseFramesRef.current = 0;
                                    
                                    // If we were in grace period and hand returns, keep stroke alive
                                    if (inGracePeriodRef.current) {
                                        clearTimeout(gracePeriodTimeoutRef.current);
                                        inGracePeriodRef.current = false;
                                    }
                                }
                                wasHandDetectedRef.current = isHandDetected;

                                // Filter based on confidence threshold
                                let validHand = isHandDetected;
                                if (isHandDetected && handScore < 0.55) {
                                    validHand = false; // Ignore unreliable frame measurements

                                                        {/* Smoothing Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Smoothing (Response)</span>
                                                                <span className="text-white font-mono">{virtualMouseSmoothing.toFixed(2)}</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.05" 
                                                                max="0.50" 
                                                                step="0.02"
                                                                value={virtualMouseSmoothing} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                        setVirtualMouseEnabled(checked);
                                                                        updateSetting('virtual_mouse_enabled', checked);
                                                                        logSystemEvent(`Virtual Mouse set to: ${checked ? 'Enabled' : 'Disabled'}`);
                                                                    }}
                                                                    className="sr-only peer" 
                                                                />
                                                                <div className="w-11 h-6 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                                            </div>
                                                        </label>

                                                        {/* Sensitivity Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Sensitivity</span>
                                                                <span className="text-white font-mono">{virtualMouseSensitivity.toFixed(2)}x</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.5" 
                                                                max="3.0" 
                                                                step="0.1"
                                                                value={virtualMouseSensitivity} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseSensitivity(val);
                                                                    updateSetting('virtual_mouse_sensitivity', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Dead Zone Slider */}
                                                        <div className="space-y-2">
          
                                                            <input 
                                                                type="range" 
                                                                min="10" 
                                                                max="100" 
                                                                step="5"
                                                                value={virtualMouseVolumeMinDistancePx} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseVolumeMinDistancePx(val);
                                                                    updateSetting('virtual_mouse_volume_min_distance_px', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Volume Max Distance Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Volume Max Distance</span>
                                                                <span className="text-white font-mono">{virtualMouseVolumeMaxDistancePx.toFixed(0)} px</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="150" 
                                                                max="400" 
                                                                step="10"
                                                                value={virtualMouseVolumeMaxDistancePx} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseVolumeMaxDistancePx(val);
                                                                    updateSetting('virtual_mouse_volume_max_distance_px', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Volume Smoothing Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Volume Smoothing</span>
                                                                <span className="text-white font-mono">{virtualMouseVolumeSmoothing.toFixed(2)}</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.05" 
                                                                max="0.50" 
                                                                step="0.01"
                                                                value={virtualMouseVolumeSmoothing} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseVolumeSmoothing(val);
                                                                    updateSetting('virtual_mouse_volume_smoothing', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="glass-card rounded-2xl p-8 text-center text-gray-400">
                                                                <span className="text-gray-400">Volume Min Distance</span>
                                                                <span className="text-white font-mono">{virtualMouseVolumeMinDistancePx.toFixed(0)} px</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="10" 
                                                                max="100" 
                                                                step="5"
                                                                value={virtualMouseVolumeMinDistancePx} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseVolumeMinDistancePx(val);
                                                                    updateSetting('virtual_mouse_volume_min_distance_px', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Volume Max Distance Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Volume Max Distance</span>
                                                                <span className="text-white font-mono">{virtualMouseVolumeMaxDistancePx.toFixed(0)} px</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="150" 
                                                                max="400" 
                                                                step="10"
                                                                value={virtualMouseVolumeMaxDistancePx} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseVolumeMaxDistancePx(val);
                                                                    updateSetting('vir
                                        
                                        const distBadge = cursorEl.querySelector('.cursor-dist');
                                        if (distBadge) {
                                            distBadge.textContent = ipDist.toFixed(4);
                                        }
                                        
                                        const confBadge = cursorEl.querySelector('.cursor-confidence');
                                        if (confBadge) {
                                            confBadge.textContent = `${Math.round(handScore * 100)}%`;
                                        }
                                    }
                                } else {
                                    // Hand not detected or too low confidence
                                    consecutivePinchFramesRef.current = 0;
                                                : currentStatus === 'Grace Period' 
                                                    ? 'text-amber-500 animate-pulse' 
                                                    : 'text-accent-yellow'
                                        }`;
                                    }
                                    
                                    const coordsEl = document.getElementById('telemetry-pointer-coords');
                                    if (coordsEl) {
                                        coordsEl.textContent = `${Math.round(smoothedX)}, ${Math.round(smoothedY)}`;
                                    }
                                    
                                    const pinchDistEl = document.getElementById('telemetry-pinch-distance');
                                    if (pinchDistEl) {
                                        pinchDistEl.textContent = `${ipDist.toFixed(4)} (raw: ${rawPinchDist.toFixed(4)})`;
                                    }
                                    
                                    const confEl = document.getElementById('telemetry-pinch-confidence');
                                    if (confEl) {
                                        confEl.textContent = `${Math.round(handScore * 100)}%`;
                                    }
                                    
                                    const pinchFram
                        {/* Sidebar Footer status */}
                        <div className="p-4 border-t border-glass-border">
                                    }
                                    
                                            }
                                            
                                            // During grace period, continue stroke coordinates so path remains seamless
                                            if (currentStrokeRef.current) {
                                                currentStrokeRef.current.points.push({ x: smoothedX, y: smoothedY });
                                            }
                                            lastPointRef.current = { x: smoothedX, y: smoothedY };
                                        } else {
                                            setDrawingStatus('Hovering');
                                            
                                            // Track hover trail preview
                                            if (showHoverTrailRef.current) {
                                                hoverTrailRef.current.push({ x: smoothedX, y: smoothedY });
                                                if (hoverTrailRef.current.length > 12) {
                                                    hoverTrailRef.current.shift();
                                                }
                                            } else {
                                                hoverTrailRef.current = [];
                                            }
                                            lastPointRef.current = { x: smoothedX, y: smoothedY };
                                        }
                                    }
                                    
                                    renderAll();
                                    
                                    // Get current status for UI
                                    const currentStatus = inGracePeriodRef.current 
                                        ? 'Grace Period' 
                                        : isDrawModeActive 
                                            ? 'Drawing' 
                                            : 'Hovering';
                                            
                                    // Telemetry updates in sidebar
                                    const statusEl = document.getElementById('telemetry-drawing-status');
                                    if (statusEl) {
                                        statusEl.textContent = currentStatus;
                                        statusEl.className = `text-sm font-bold ${
                                            currentStatus === 'Drawing' 
                                                ? 'text-accent-green' 
                                                : currentStatus === 'Grace Period' 
                                                    ? 'text-amber-500 animate-pulse' 
                                                    : 'text-accent-yellow'
                                        }`;
                                                                    updateSetting('virtual_mouse_brightness_smoothing', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="glass-card rounded-2xl p-8 text-center text-gray-400">
                                        <p>This page is currently under construction. Please use the Dashboard or Virtual Mouse navigation links.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </main>
                </div>
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTML_CONTENT

if __name__ == "__main__":
    uvicorn.run("web_backend:app", host="127.0.0.1", port=8000, log_level="info")


                        {/* Outer scrollable viewport */}
                        <div className="flex-1 overflow-y-auto p-8 scrollbar-thin">
                            <div className="max-w-6xl mx-auto space-y-6">
                                
                                {activeMenu === 'dashboard' ? (
                                    <>
                                        {/* Status Cards Grid */}
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5">
                                            {/* FPS Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 text-accent-blue">
                                                    <ActivityIcon className="w-6 h-6" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Frames Per Second</p>
                                                    <p className="text-2xl font-bold text-white mt-1 font-mono tracking-tight">
                                                        {fps > 0 ? fps : '0.0'}
                                                    </p>
                                                </div>
                                            </div>

                                                                step="0.01"
                                                                value={virtualMouseBrightnessSmoothing} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                            <div className="flex justify-between text-xs">
                                                ? '#a6da95' 
                                                : currentStatus === 'Grace Period' 
                                                    ? '#f5a97f' 
                                                    : '#8aadf4';
                                            cursorRing.style.borderStyle = currentStatus === 'Drawing' ? 'solid' : 'dashed';
                                        }
                                        
                                        const cursorDot = cursorEl.querySelector('.cursor-dot');
                                        if (cursorDot) {
                                            cursorDot.style.width = `${webBrushSizeRef.current}px`;
                                            cursorDot.style.height = `${webBrushSizeRef.current}px`;
                                            cursorDot.style.backgroundColor = webBrushToolRef.current === 'eraser' ? '#ed8796' : webBrushColorRef.current;
                                        }
                                        
                                        const sizeBadge = cursorEl.querySelector('.cursor-size');
                                        if (sizeBadge) sizeBadge.textContent = `${webBrushSizeRef.current}px`;
                                        
                                        const colorBadge = cursorEl.querySelector('.cursor-color-badge');
                                        if (colorBadge) colorBadge.style.backgroundColor = webBrushToolRef.current === 'eraser' ? '#ed8796' : webBrushColorRef.current;
                                        
                                        const stateBadge = cursorEl.querySelector('.cursor-state');
                                        if (stateBadge) {
                                            let cursorStateText = currentStatus.toUpperCase();
                                            if (currentStatus === 'Drawing') {
                                                cursorStateText = webBrushToolRef.current.toUpperCase();
                                            }
                                            stateBadge.textContent = cursorStateText;
                                            
                                            if (currentStatus === 'Drawing') {
                                                stateBadge.style.color = webBrushToolRef.current === 'eraser' ? '#ed8796'
                                                                       : webBrushToolRef.current === 'highlighter' ? '#eed49f'
                                                                       : '#a6da95';
                                            } else {
                                                stateBadge.style.color = currentStatus === 'Grace Period' ? '#f5a97f' : '#8aadf4';
                                            }
                                        }
                                        
                                        const distBadge = cursorEl.querySelector('.cursor-dis
                                                    </div>
                        }
                    };

                    ws.onclose = () => {
                        setSocketStatus('disconnected');
                        console.log('WebSocket connection lost, retrying in 3 seconds...');
                        setTimeout(connectWS, 3000);
                    };

                    ws.onerror = (error) => {
                        console.error('WebSocket encountered an error:', error);
                    };
                };

                connectWS();

                // Fetch initial switches configuration from backend
                fetch('/api/settings')
                    .then(res => res.json())
                    .then(data => {
                        setShowLandmarks(data.show_landmarks);
                        setShowConnections(data.show_connections);
                        setShowBoundingBox(data.show_bounding_box);
                        setShowFingerStates(data.show_finger_states);
                        setShowDistanceMeter(data.show_distance_meter);
                        setShowDebugPanel(data.show_debug_panel);
                        setShowHud(data.show_hud);
                        
                        setVirtualMouseEnabled(data.virtual_mouse_enabled);
                        setVirtualMouseSensitivity(data.virtual_mouse_sensitivity);
                        setVirtualMouseDeadZone(data.virtual_mouse_dead_zone);
                        setVirtualMouseSmoothing(data.virtual_mouse_smoothing);
                        if (data.virtual_mouse_click_threshold !== undefined) {
                            setVirtualMouseClickThreshold(data.virtual_mouse_click_threshold);
                        }
                        if (data.virtual_mouse_right_click_threshold !== undefined) {
                            setVirtualMouseRightClickThreshold(data.virtual_mouse_right_click_threshold);
                        }
                        if (data.virtual_mouse_scroll_sensitivity !== undefined) {
                            setVirtualMouseScrollSensitivity(data.virtual_mouse_scroll_sensitivity);
                        }
                        if (data.virtual_mouse_scroll_dead_zone !== undefined) {
                            setVirtualMouseScrollDeadZone(data.virtual_mouse_scroll_dead_zone);
                        }
                        if (data.virtual_mouse_scroll_smoothing !== undefined) {
                            setVirtualMouseScrollSmoothing(data.virtual_mouse_scroll_smoothing);
                        }
                        if (data.virtual_mouse_volume_min_distance_px !== undefined) {
                            setVirtualMouseVolumeMinDistancePx(data.virtual_mouse_volume_min_distance_px);
                        }
                                                }
                                            }, 250);
                                        }
                                    } else if (!inGracePeriodRef.current) {
                                        setDrawingStatus('Idle');
                                        hoverTrailRef.current = [];
                                        
                                        const statusEl = document.getElementById('telemetry-drawing-status');
                                        if (statusEl) {
                                            statusEl.textContent = 'Idle';
                                            statusEl.className = 'text-sm font-bold text-gray-450';
                                        }
                                        
                                        renderAll();
                                        
                                        const cursorEl = document.getElementById('drawing-cursor');
                                        if (cursorEl) cursorEl.style.display = 'none';
                                    }
                                }
                            }
                        } catch (err) {
                            console.error('Error decoding WebSocket JSON payload:', err);
                        }
                    };

                    ws.onclose = () => {
                        setSocketStatus('disconnected');
                        console.log('WebSocket connection lost, retrying in 3 seconds...');
                        setTimeout(connectWS, 3000);
                    };

                    ws.onerror = (error) => {
                        console.error('WebSocket encountered an error:', error);
                    };
                };

                connectWS();

                // Fetch initial switches configuration from backend
                fetch('/api/settings')
                    .then(res => res.json())
                    .then(data => {
                        setShowLandmarks(data.show_landmarks);
                        setShowConnections(data.show_connections);
                        setShowBoundingBox(data.show_bounding_box);
                        setShowFingerStates(data.show_finger_states);
                        setShowDistanceMeter(data.show_distance_meter);
                        setShowDebugPanel(data.show_debug_panel);
                        setShowHud(data.show_hud);
                        
                        setVirtualMouseEnabled(data.virtual_mouse_enabled);
                        setVirtualMouseSensitivity(data.virtual_mouse_sensitivity);
                        setVirtualMouseDeadZone(data.virtual_mouse_dead_zone);
                        setVirtualMouseSmoothing(data.virtual_mouse_smoothing);
                        if (data.virtual_mouse_click_threshold !== undefined) {
                            setVirtualMouseClickThreshold(data.virtual_mouse_click_threshold);
                        }
                        if 
# === GAP: MISSING LINE 2228 ===
# === GAP: MISSING LINE 2229 ===
# === GAP: MISSING LINE 2230 ===
# === GAP: MISSING LINE 2231 ===
# === GAP: MISSING LINE 2232 ===
# === GAP: MISSING LINE 2233 ===
# === GAP: MISSING LINE 2234 ===
# === GAP: MISSING LINE 2235 ===
# === GAP: MISSING LINE 2236 ===
# === GAP: MISSING LINE 2237 ===
                        }
                        if (data.virtual_mouse_volume_min_distance_px !== undefined) {
                            setVirtualMouseVolumeMinDistancePx(data.virtual_mouse_volume_min_distance_px);
                        }
                        if (data.virtual_mouse_volume_max_distance_px !== undefined) {
                            setVirtualMouseVolumeMaxDistancePx(data.virtual_mouse_volume_max_distance_px);
                        }
                        if (data.virtual_mouse_volume_smoothing !== undefined) {
                            setVirtualMouseVolumeSmoothing(data.virtual_mouse_volume_smoothing);
                        }
                        if (data.virtual_mouse_brightness_min_distance_px !== undefined) {
                            setVirtualMouseBrightnessMinDistancePx(data.virtual_mouse_brightness_min_distance_px);
                        }
                        if (data.virtual_mouse_brightness_max_distance_px !== undefined) {
                            setVirtualMouseBrightnessMaxDistancePx(data.virtual_mouse_brightness_max_distance_px);
                        }
                        if (data.virtual_mouse_brightness_smoothing !== undefined) {
                            setVirtualMouseBrightnessSmoothing(data.virtual_mouse_brightness_smoothing);
                        }
                        if (data.virtual_mouse_drag_threshold_ms !== undefined) {
                            setVirtualMouseDragThresholdMs(data.virtual_mouse_drag_threshold_ms);
                                    if (data.keybo
                                        setSystemTypingEnabled(data.keyboard_system_typing_enabled);
                                    }
                                    if (data.keyboard_autocomplete_enabled !== undefined) {
                                        setAutocompleteEnabled(data.keyboard_autocomplete_enabled);
                                    }
                                    if (data.brush_size !== undefined) {
                                        setWebBrushSize(data.brush_size);
                                        webBrushSizeRef.current = data.brush_size;
                                    }
                                    if (data.brush_color !== undefined) {
   
# === GAP: MISSING LINE 2271 ===
# === GAP: MISSING LINE 2272 ===
# === GAP: MISSING LINE 2273 ===
# === GAP: MISSING LINE 2274 ===
# === GAP: MISSING LINE 2275 ===
# === GAP: MISSING LINE 2276 ===
# === GAP: MISSING LINE 2277 ===
                                        webBrushToolRef.current = data.brush_tool;
                                    }
                                })
                                                                    onClick={handleWebUndo}
                                                                    disabled={undoStack.length === 0}
                                                                    className={`py-2 px-3 rounded-xl font-semibold text-xs border transition-all ${
                                                                        undoStack.length === 0
                                                                            ? 'bg-zinc-850/40 border-zinc-900/10 text-zinc-650 cursor-not-allowed'
                                                                            : 'bg-zinc-800 hover:bg-zinc-700 border-zinc-700 text-white active:scale-95'
                                                                    }`}
                                                                >
                                                                    ↶ Undo
                                                                </button>
                                                                <button 
                                                                    onClick={handleWebRedo}
                                                                    disabled={redoStack.length === 0}
                                                                    className={`py-2 px-3 rounded-xl font-semibold text-xs border transition-all ${
                                                                        redoStack.length === 0
# === GAP: MISSING LINE 2296 ===
# === GAP: MISSING LINE 2297 ===
# === GAP: MISSING LINE 2298 ===
# === GAP: MISSING LINE 2299 ===
# === GAP: MISSING LINE 2300 ===
# === GAP: MISSING LINE 2301 ===
# === GAP: MISSING LINE 2302 ===
# === GAP: MISSING LINE 2303 ===
# === GAP: MISSING LINE 2304 ===
# === GAP: MISSING LINE 2305 ===
# === GAP: MISSING LINE 2306 ===
# === GAP: MISSING LINE 2307 ===
# === GAP: MISSING LINE 2308 ===
# === GAP: MISSING LINE 2309 ===
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                                                    }`}
                                                                >
                                                                    💾 Save PNG
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </>
                                    ) : (
                                        <div className="glass-card rounded-2xl p-8 text-center text-gray-400">
                                            <p>This page is currently under construction. Please use the Dashboard or Virtual Mouse navigation links.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </main>
                    </div>
                );
            }

            const root = ReactDOM.createRoot(document.getElementById('root'));
            root.render(<App />);
        </script>
    </body>
</html>"""

@app.get("/static/react.min.js")
def get_react():
    from fastapi.responses import FileResponse
    return FileResponse("static/react.min.js", media_type="application/javascript")

@app.get("/static/react-dom.min.js")
def get_react_dom():
    from fastapi.responses import FileResponse
                                                        </div>
                                                    </div>

                                                    <div className="flex-1 flex flex-col gap-2 mt-4">
                                                    
                                                    <div className="flex-1 my-4 flex items-center justify-center bg-black/45 rounded-xl overflow-hidden border border-glass-border relative">
                                                        {cameraStatus === 'Connected' && frame ? (
                                                            <img 
                                                                src={frame} 
                                                                alt="Camera Feed" 
                                                                className="w-full h-full object-contain rounded-xl"
                                                            />
                                                        ) : (
                                                            <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm">
                                                                <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 mb-4 animate-pulse">
                                                                    <VideoOffIcon className="w-8 h-8" />
                                                                </div>
                                                                <h4 className="text-white font-medium mb-1">Camera Stream Inactive</h4>
                          
# === GAP: MISSING LINE 2370 ===
# === GAP: MISSING LINE 2371 ===
# === GAP: MISSING LINE 2372 ===
# === GAP: MISSING LINE 2373 ===
# === GAP: MISSING LINE 2374 ===
# === GAP: MISSING LINE 2375 ===
# === GAP: MISSING LINE 2376 ===
# === GAP: MISSING LINE 2377 ===
# === GAP: MISSING LINE 2378 ===
                                                        className={`w-full h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                <div className="glass-card rounded-2xl p-6 border border-glass-border flex flex-col justify-between h-[400px] relative overflow-hidden">
                                                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                                    
                                                    <div>
                                                        <h3 className="text-sm font-semibold text-white pb-3 border-b border-glass-border mb-4">
                                                            Keyboard Telemetry
                                                        </h3>
                                                        
                                                        <div className="space-y-3">
                                                            <div className="flex justify-between items-center text-xs">
                                                                <span className="text-gray-400">Current Hovered Key</span>
                                                                <span className="px-2 py-1 rounded bg-zinc-800 text-white font-mono font-bold">{hoveredKey}</span>
                                                            </div>
                                                            <div className="flex justify-between items-center text-xs">
                                                                <span className="text-gray-400">Hover Duration</span>
                                                                <span className="text-accent-blue font-bold">{hoverDuration.toFixed(2)}s</span>
                                                            </div>
                                                            <div className="flex justify-between items-center text-xs">
                                                                <span className="text-gray-400">Last Pressed Key</span>
                                                                <span className="px-2 py-1 rounded bg-zinc-800 text-white font-mono font-bold">{lastPressedKey}</span>
                                                            </div>
                                                            <div className="flex justify-between items-center text-xs">
                                                                <span className="text-gray-400">Stream FPS</span>
                                                                <span className="text-accent-blue font-bold">{fps.toFixed(1)} FPS</span>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <div className="flex-1 flex flex-col gap-2 mt-4">
                                                        <div className="flex justify-between items-center text-xs">
                                                            <span className="text-gray-400 font-semibold">Live Typed Text</span>
                                          
                                                    </button>
                                                    {["Z", "X", "C", "V", "B", "N", "M"].map(key => {
                                                        const label = isCapsLockActive || isShiftActive ? key.toUpperCase() : key.toLowerCase();
                                                        return (
                                                            <button 
                                                                key={key}
                                                                onMouseEnter={() => setHoveredKey(key)}
                                                                onMouseLeave={() => setHoveredKey('None')}
                                                </div>
                                            </div>

                                            {/* Right: Keyboard Telemetry Panel (1 Column) */}
                                            <div className="flex flex-col gap-4">
                                                <div className="glass-card rounded-2xl p-6 border border-glass-border flex flex-col justify-between h-[400px] relative overflow-hidden">
                                                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                                    
                                                    <div>
                                                        <h3 className="text-sm font-semibold text-white pb-3 border-b border-glass-border mb-4">
                                                            Keyboard Telemetry
                                                        </h3>
                                                        
                                                        <div className="space-y-3">
                                                            <div className="flex justify-between items-center text-xs">
                                                                <span className="text-gray-400">Current Hovered Key</span>
                                                               
                                            {/* Responsive Keyboard */}
                                            <div className="flex flex-col gap-2 max-w-4xl mx-auto w-full bg-zinc-950/40 p-4 rounded-2xl border border-glass-border">
                                                {/* Row 1 (Numbers) */}
                                                <div className="flex gap-1.5 w-full justify-between">
                                                </div>

                                                {/* Row 5 */}
                                                <div className="flex gap-1.5 w-full justify-between">
                                                    <button 
                                                        onMouseEnter={() => setHoveredKey('Space')}
                                                        onMouseLeave={() => setHoveredKey('None')}
# === GAP: MISSING LINE 2448 ===
                                                        className={`w-full h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                            <div className="flex justify-between items-center text-xs">
                                                                <span className="text-gray-400">Current Hovered Key</span>
                                                                <span className="px-2 py-1 rounded bg-zinc-800 text-white font-mono font-bold">{hoveredKey}</span>
                                                            </div>
                                                            <div className="flex justify-between items-center text-xs">
                                                                <span className="text-gray-400">Hover Duration</span>
                                                                <span className="text-accent-blue font-bold">{hoverDuration.toFixed(2)}s</span>
                                                            </div>
                                                            <div className="flex justify-between items-center text-xs">
                                                                <span className="text-gray-400">Pinch Distance</span>
                                                                <span className="text-accent-blue font-mono font-bold">{pinchDistance.toFixed(4)}</span>
                                                            </div>
                                                            <div className="flex justify-between items-center text-xs">
   
                                                    </div>

                                                    <div className="flex-1 flex flex-col gap-2 mt-4">
                                                        <div className="flex justify-between items-center text-xs">
                                                            <span className="text-gray-400 font-semibold">Live Typed Text</span>
                                                            <button 
                                                                onClick={() => setTypedText('')}
                                                            </button>
                                                        );
                                                    })}
                                                    <button 
                                                        onMouseEnter={() => setHoveredKey('Enter')}
                                                        onMouseLeave={() => setHoveredKey('None')}
                                                        onClick={() => handleWebKeyPress('Enter')}
                                                        className={`w-20 h-12 rounded-lg text-xs font-bold transition-all duration-100 ${
                                                            pressedKey === 'Enter' ? 'bg-amber-500 text-black scale-95' : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Enter
                                                            pressedKey === 'Tab' 
                                                                ? 'bg-amber-500 text-black scale-95' 
                                                                : hoveredKey === 'Tab'
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Tab
                                                    </button>
                                                    {["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"].map(key => {
                                                        const label = isCapsLockActive || isShiftActive ? key.toUpperCase() : key.toLowerCase();
                                                        return (
                                                            <button 
                                                                key={key}
                                                            >
                                                                Clear Buffer
                                                            </button>
                                                        </div>
                                                        <textarea 
                                                            readOnly
                                                            value={typedText}
                                                            className="flex-1 w-full bg-zinc-950/60 rounded-xl p-3 border border-glass-border text-sm text-gray-200 focus:outline-none focus:border-blue-500/40 font-mono resize-none"
                                                            placeholder="Typed output will stream here..."
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                                <div className="glass-card rounded-2xl p-5">
                                                    <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                                                        <SlidersIcon className="w-4 h-4 text-accent-blue" />
                                                        Display Settings
                                                    </h3>
                                                    <p className="text-xs text-gray-500 mt-1 mb-4">Toggle live stream visual overlays.</p>
                                                    
                                                    <div className="grid grid-cols-2 gap-y-3.5 gap-x-2 text-[11px]">
                                                        {[
                                                            { id: 'show_landmarks', label: 'Landmarks', value: showLandmarks, setter: setShowLandmarks },
                                                            { id: 'show_connections', label: 'Connections', value: showConnections, setter: setShowConnections },
                                                            { id: 'show_bounding_box', label: 'Bounding Box', value: showBoundingBox, setter: setShowBoundingBox },
                                                            { id: 'show_finger_states', label: 'Finger States', value: showFingerStates, setter: setShowFingerStates },
    
                                                    {["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"].map(key => (
                                                        <button 
                                                            key={key}
                                                            data-key={key}
                                                            onMouseEnter={() => setHoveredKey(key)}
                                                            onMouseLeave={() => setHoveredKey('None')}
                                                            onClick={() => handleWebKeyPress(key)}
                                                                    onChange={(e) => {
                                                                        const checked = e.target.checked;
                                                                        item.setter(checked);
                                                                        updateSetting(item.id, checked);
                                                                    }}
                                                                    className="w-3.5 h-3.5 rounded border-glass-border bg-[#080710] text-blue-500 focus:ring-blue-500/40 cursor-pointer"
                                                                />
                                                                <span>{item.label}</span>
                                                            </label>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Activity Log Panel */}
                                                <div className="glass-card rounded-2xl p-5 flex flex-col flex-1 min-h-[220px] justify-between">
                                                    <div>
                                                        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                                                            <CpuIcon className="w-4 h-4 text-accent-blue" />
                                                            Activity Log
                                                        </h3>
# === GAP: MISSING LINE 2551 ===
# === GAP: MISSING LINE 2552 ===
# === GAP: MISSING LINE 2553 ===
# === GAP: MISSING LINE 2554 ===
# === GAP: MISSING LINE 2555 ===
# === GAP: MISSING LINE 2556 ===
# === GAP: MISSING LINE 2557 ===
# === GAP: MISSING LINE 2558 ===
# === GAP: MISSING LINE 2559 ===
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : activeMenu === 'keyboard' ? (
                                    <>
                                        {/* Hero Header Section */}
                                        <div className="glass-panel rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between border border-glass-border relative overflow-hidden">
                                            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                            <div>
                                                <h2 className="text-2xl font-bold tracking-wide text-white">Virtual Keyboard Controls</h2>
                                                <p className="text-xs text-gray-400 mt-1 max-w-xl">
                                                    Type text using standard mouse clicks or finger-pinch gestures. Customize your layouts and monitor live inputs.
                                                </p>
                                            </div>
                                            <div className="mt-4 md:mt-0">
                                                <span className="px-4 py-2 rounded-full text-xs font-semibold border bg-emerald-500/10 border-emerald-500/20 text-accent-green">
                                                    Interactive
                                                            }`} />
                                                            {cameraStatus === 'Connected' ? 'Streaming live' : 'Offline'}
                                                        </div>
                                                    </div>
                                                    
                                                    <div className="flex-1 my-4 flex items-center justify-center bg-black/45 rounded-xl overflow-hidden border border-glass-border relative">
                                                        {cameraStatus === 'Connected' && frame ? (
                                                            <img 
                                                                src={frame} 
                                                                alt="Camera Feed" 
                                                                className="w-full h-full object-contain rounded-xl"
                                                            />
                                                        ) : (
                                                            <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm">
                                                                <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 mb-4 animate-pulse">
                                                                    : isCapsLockActive 
                                                                        ? 'bg-blue-600 hover:bg-blue-500 text-white' 
                                                                        : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Caps
                                                    </button>
                                                    {["A", "S", "D", "F", "G", "H", "J", "K", "L"].map(key => {
                                                        const label = isCapsLockActive || isShiftActive ? key.toUpperCase() : key.toLowerCase();
                                                        return (
                                                            <button 
                                                                key={key}
                                                                data-key={key}
                                                                onMouseEnter={() => setHoveredKey(key)}
                                                                onMouseLeave={() => setHoveredKey('None')}
                                                                onClick={() => handleWebKeyPress(key)}
                                                                className={`flex-1 h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                                    pressedKey === key 
                                                                        ? 'bg-amber-500 text-black scale-95' 
                                                                        : hoveredKey === key
       
# === GAP: MISSING LINE 2617 ===
# === GAP: MISSING LINE 2618 ===
# === GAP: MISSING LINE 2619 ===
# === GAP: MISSING LINE 2620 ===
# === GAP: MISSING LINE 2621 ===
# === GAP: MISSING LINE 2622 ===
# === GAP: MISSING LINE 2623 ===
# === GAP: MISSING LINE 2624 ===
# === GAP: MISSING LINE 2625 ===
# === GAP: MISSING LINE 2626 ===
# === GAP: MISSING LINE 2627 ===
# === GAP: MISSING LINE 2628 ===
# === GAP: MISSING LINE 2629 ===
# === GAP: MISSING LINE 2630 ===
# === GAP: MISSING LINE 2631 ===
# === GAP: MISSING LINE 2632 ===
# === GAP: MISSING LINE 2633 ===
# === GAP: MISSING LINE 2634 ===
# === GAP: MISSING LINE 2635 ===
# === GAP: MISSING LINE 2636 ===
# === GAP: MISSING LINE 2637 ===
# === GAP: MISSING LINE 2638 ===
# === GAP: MISSING LINE 2639 ===
# === GAP: MISSING LINE 2640 ===
# === GAP: MISSING LINE 2641 ===
# === GAP: MISSING LINE 2642 ===
# === GAP: MISSING LINE 2643 ===
# === GAP: MISSING LINE 2644 ===
# === GAP: MISSING LINE 2645 ===
# === GAP: MISSING LINE 2646 ===
# === GAP: MISSING LINE 2647 ===
# === GAP: MISSING LINE 2648 ===
# === GAP: MISSING LINE 2649 ===
# === GAP: MISSING LINE 2650 ===
# === GAP: MISSING LINE 2651 ===
# === GAP: MISSING LINE 2652 ===
                                                                    : isShiftActive 
                                                                        ? 'bg-blue-600 hover:bg-blue-500 text-white' 
                                                                        : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Shift
                                                    </button>
                                                    {["Z", "X", "C", "V", "B", "N", "M"].map(key => {
                                                        const label = isCapsLockActive || isShiftActive ? key.toUpperCase() : key.toLowerCase();
                                                        return (
                                                            <button 
                                                                key={key}
                                                                data-key={key}
                                                                onMouseEnter={() => setHoveredKey(key)}
                                                                onMouseLeave={() => setHoveredKey('None')}
                                                                onClick={() => handleWebKeyPress(key)}
                                                                className={`flex-1 h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                                    pressedKey === key 
                                                                        ? 'bg-amber-500 text-black scale-95' 
                                                                        : hoveredKey === key
                                                                            ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                            : 'bg-zinc-850 hover:bg-zinc-700 text-white active:scale-95 border border-zinc-750'
                                                                }`}
                                                            >
                                                                {label}
                                                            </button>
                                                        );
                                                    })}
                                                    <button 
                                                        data-key="Backspace"
                                                        onMouseEnter={() => setHoveredKey('Backspace')}
                                                        onMouseLeave={() => setHoveredKey('None')}
                                                        onClick={() => handleWebKeyPress('Backspace')}
                                          
# === GAP: MISSING LINE 2687 ===
# === GAP: MISSING LINE 2688 ===
# === GAP: MISSING LINE 2689 ===
# === GAP: MISSING LINE 2690 ===
# === GAP: MISSING LINE 2691 ===
# === GAP: MISSING LINE 2692 ===
# === GAP: MISSING LINE 2693 ===
# === GAP: MISSING LINE 2694 ===
# === GAP: MISSING LINE 2695 ===
# === GAP: MISSING LINE 2696 ===
# === GAP: MISSING LINE 2697 ===
# === GAP: MISSING LINE 2698 ===
# === GAP: MISSING LINE 2699 ===
                                                                <span className="text-white font-mono">{virtualMouseVolumeMinDistancePx.toFixed(0)} px</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="10" 
                                                                max="100" 
                                                                step="5"
                                                                value={virtualMouseVolumeMinDistancePx} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseVolumeMinDistancePx(val);
                                                                    updateSetting('virtual_mouse_volume_min_distance_px', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>


# === GAP: MISSING LINE 2718 ===
# === GAP: MISSING LINE 2719 ===
                                    <div className="glass-card rounded-2xl p-8 text-center text-gray-400">
                                        <p>This page is currently under construction. Please use the Dashboard or Virtual Mouse navigation links.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </main>
                </div>
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>"""

@app.get("/static/react.min.js")
def get_react():
    from fastapi.responses import FileResponse
    return FileResponse("static/react.min.js", media_type="application/javascript")

@app.get("/static/react-dom.min.js")
def get_react_dom():
    from fastapi.responses import FileResponse
    return FileResponse("static/react-dom.min.js", media_type="application/javascript")

@app.get("/static/babel.min.js")
def get_babel():
    from fastapi.responses import FileResponse
                                                <div className="flex gap-2 w-full mb-2">
                                                    {[0, 1, 2].map(idx => {
                                                        const pred = predictions[idx] || '';
                                                        return (
                                                            <button
                                                                key={`suggest-${idx}`}
                                                                data-key={`Suggestion_${idx}`}
                                                                disabled={!pred}
                                                                onMouseEnter={() => pred && setHoveredKey(`Suggestion_${idx}`)}
                                                                onMouseLeave={() => setHoveredKey('None')}
                                                                onClick={() => pred && handleWebKeyPress(`Suggestion_${idx}`)}
                                                                className={`flex-1 h-10 rounded-lg text-sm font-bold transition-all duration-100 ${
                                                                    !pred
                                                                        ? 'bg-zinc-900/40 text-zinc-600 border border-zinc-900/20 cursor-not-allowed'
                                                                        : pressedKey === `Suggestion_${idx}`
# === GAP: MISSING LINE 2765 ===
# === GAP: MISSING LINE 2766 ===
# === GAP: MISSING LINE 2767 ===
# === GAP: MISSING LINE 2768 ===
# === GAP: MISSING LINE 2769 ===
# === GAP: MISSING LINE 2770 ===
# === GAP: MISSING LINE 2771 ===
# === GAP: MISSING LINE 2772 ===
# === GAP: MISSING LINE 2773 ===
# === GAP: MISSING LINE 2774 ===
# === GAP: MISSING LINE 2775 ===
# === GAP: MISSING LINE 2776 ===
# === GAP: MISSING LINE 2777 ===
# === GAP: MISSING LINE 2778 ===
# === GAP: MISSING LINE 2779 ===
# === GAP: MISSING LINE 2780 ===
                                                            key={key}
                                                            data-key={key}
                                                            onMouseEnter={() => setHoveredKey(key)}
                                                            onMouseLeave={() => setHoveredKey('None')}
                                                            onClick={() => handleWebKeyPress(key)}
                                                            className={`flex-1 h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                                pressedKey === key 
                                                                    ? 'bg-amber-500 text-black scale-95' 
                                                                    : hoveredKey === key
                                                                        ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                        : 'bg-zinc-850 hover:bg-zinc-700 text-white active:scale-95 border border-zinc-750'
                                                            }`}
                                                        >
                                                            {key}
                                                        </button>
                                                    ))}
                                                </div>

                                                {/* Row 2 */}
                                                <div className="flex gap-1.5 w-full justify-between">
# === GAP: MISSING LINE 2801 ===
# === GAP: MISSING LINE 2802 ===
# === GAP: MISSING LINE 2803 ===
# === GAP: MISSING LINE 2804 ===
# === GAP: MISSING LINE 2805 ===
# === GAP: MISSING LINE 2806 ===
# === GAP: MISSING LINE 2807 ===
# === GAP: MISSING LINE 2808 ===
# === GAP: MISSING LINE 2809 ===
# === GAP: MISSING LINE 2810 ===
# === GAP: MISSING LINE 2811 ===
# === GAP: MISSING LINE 2812 ===
# === GAP: MISSING LINE 2813 ===
# === GAP: MISSING LINE 2814 ===
# === GAP: MISSING LINE 2815 ===
# === GAP: MISSING LINE 2816 ===
# === GAP: MISSING LINE 2817 ===
# === GAP: MISSING LINE 2818 ===
# === GAP: MISSING LINE 2819 ===
# === GAP: MISSING LINE 2820 ===
# === GAP: MISSING LINE 2821 ===
# === GAP: MISSING LINE 2822 ===
# === GAP: MISSING LINE 2823 ===
# === GAP: MISSING LINE 2824 ===
# === GAP: MISSING LINE 2825 ===
# === GAP: MISSING LINE 2826 ===
# === GAP: MISSING LINE 2827 ===
# === GAP: MISSING LINE 2828 ===
# === GAP: MISSING LINE 2829 ===
# === GAP: MISSING LINE 2830 ===
# === GAP: MISSING LINE 2831 ===
# === GAP: MISSING LINE 2832 ===
# === GAP: MISSING LINE 2833 ===
# === GAP: MISSING LINE 2834 ===
# === GAP: MISSING LINE 2835 ===
# === GAP: MISSING LINE 2836 ===
# === GAP: MISSING LINE 2837 ===
# === GAP: MISSING LINE 2838 ===
# === GAP: MISSING LINE 2839 ===
# === GAP: MISSING LINE 2840 ===
# === GAP: MISSING LINE 2841 ===
# === GAP: MISSING LINE 2842 ===
# === GAP: MISSING LINE 2843 ===
# === GAP: MISSING LINE 2844 ===
# === GAP: MISSING LINE 2845 ===
# === GAP: MISSING LINE 2846 ===
# === GAP: MISSING LINE 2847 ===
# === GAP: MISSING LINE 2848 ===
# === GAP: MISSING LINE 2849 ===
# === GAP: MISSING LINE 2850 ===
# === GAP: MISSING LINE 2851 ===
# === GAP: MISSING LINE 2852 ===
# === GAP: MISSING LINE 2853 ===
# === GAP: MISSING LINE 2854 ===
# === GAP: MISSING LINE 2855 ===
# === GAP: MISSING LINE 2856 ===
# === GAP: MISSING LINE 2857 ===
# === GAP: MISSING LINE 2858 ===
# === GAP: MISSING LINE 2859 ===
# === GAP: MISSING LINE 2860 ===
# === GAP: MISSING LINE 2861 ===
# === GAP: MISSING LINE 2862 ===
# === GAP: MISSING LINE 2863 ===
# === GAP: MISSING LINE 2864 ===
# === GAP: MISSING LINE 2865 ===
# === GAP: MISSING LINE 2866 ===
# === GAP: MISSING LINE 2867 ===
# === GAP: MISSING LINE 2868 ===
# === GAP: MISSING LINE 2869 ===
# === GAP: MISSING LINE 2870 ===
# === GAP: MISSING LINE 2871 ===
# === GAP: MISSING LINE 2872 ===
# === GAP: MISSING LINE 2873 ===
# === GAP: MISSING LINE 2874 ===
# === GAP: MISSING LINE 2875 ===
# === GAP: MISSING LINE 2876 ===
# === GAP: MISSING LINE 2877 ===
# === GAP: MISSING LINE 2878 ===
# === GAP: MISSING LINE 2879 ===
                                                        data-key="Enter"
                                                        onMouseEnter={() => setHoveredKey('Enter')}
                                                        onMouseLeave={() => setHoveredKey('None')}
                                                        onClick={() => handleWebKeyPress('Enter')}
                                                        className={`w-20 h-12 rounded-lg text-xs font-bold transition-all duration-100 ${
                                                            pressedKey === 'Enter' 
                                                                ? 'bg-amber-500 text-black scale-95' 
                                                                : hoveredKey === 'Enter'
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Enter
                                                    </button>
                                                </div>

                                                {/* Row 4 */}
                                               
# === GAP: MISSING LINE 2898 ===
# === GAP: MISSING LINE 2899 ===
# === GAP: MISSING LINE 2900 ===
# === GAP: MISSING LINE 2901 ===
# === GAP: MISSING LINE 2902 ===
                                                        className={`w-24 h-12 rounded-lg text-xs font-bold transition-all duration-100 ${
                                                            pressedKey === 'Shift' 
                                                                ? 'bg-amber-500 text-black scale-95' 
                                                                : hoveredKey === 'Shift'
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : isShiftActive 
                                                                        ? 'bg-blue-600 hover:bg-blue-500 text-white' 
                                                                        : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Shift
                                                    </button>
                                                    {["Z", "X", "C", "V", "B", "N", "M"].map(key => {
                                                        const label = isCapsLockActive || isShiftActive ? key.toUpperCase() : key.toLowerCase();
                                                        return (
                                                            <button 
                                                                key={key}
                                                                data-key={key}
                                                                onMouseEnter={() => setHoveredKey(key)}
                                                                onMouseLeave={() => setHoveredKey('None')}
                                                                onClick={() => handleWebKeyPress(key)}
                                                                className={`flex-1 h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                                    pressedKey === key 
                                                                        ? 'bg-amber-500 text-black scale-95' 
                                                                        : hoveredKey === key
                                                                            ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                            : 'bg-zinc-850 hover:bg-zinc-700 text-white active:scale-95 border border-zinc-750'
                                                                }`}
                                                            >
                                                                {label}
                                                            </button>
                                                        );
                                                    })}
                          
# === GAP: MISSING LINE 2937 ===
# === GAP: MISSING LINE 2938 ===
# === GAP: MISSING LINE 2939 ===
# === GAP: MISSING LINE 2940 ===
# === GAP: MISSING LINE 2941 ===
# === GAP: MISSING LINE 2942 ===
# === GAP: MISSING LINE 2943 ===
# === GAP: MISSING LINE 2944 ===
# === GAP: MISSING LINE 2945 ===
# === GAP: MISSING LINE 2946 ===
# === GAP: MISSING LINE 2947 ===
# === GAP: MISSING LINE 2948 ===
# === GAP: MISSING LINE 2949 ===
                                                    </button>
                                                </div>

                                                {/* Row 5 */}
                                                <div className="flex gap-1.5 w-full justify-between">
                                                    <button 
                                                        data-key="Space"
                                                        onMouseEnter={() => setHoveredKey('Space')}
                                                        onMouseLeave={() => setHoveredKey('None')}
                                                        onClick={() => handleWebKeyPress('Space')}
                                                        className={`w-full h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                            pressedKey === 'Space' 
                                                                ? 'bg-amber-500 text-black scale-95' 
                                                                : hoveredKey === 'Space'
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750 active:scale-95'
                                                        }`}
                                                    >
                                                        Space
                                                    </button>
                                                </div>

                                                {/* Row 6 (Emojis) */}
                                                <div className="flex gap-1.5 w-full justify-between mt-2">
                                                    {["😊", "😂", "👍", "🔥", "❤️", "🎉", "✨", "🚀", "👋", "👀"].map(emoji => (
                                                        <button
                                                            key={emoji}
                                                            data-key={emoji}
                                                            onMouseEnter={() => setHoveredKey(emoji)}
                                                            onMouseLeave={() => setHoveredKey('None')}
                                                            onClick={() => handleWebKeyPress(emoji)}
                                                            className={`flex-1 h-10 rounded-lg text-base transition-all duration-100 ${
                                                                pressedKey === emoji
                                                                    ? 'bg-amber-500 text-black scale-95'
                                                                    : hoveredKey === emoji
                                                                        ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                        : 'bg-zinc-850 hover:bg-zinc-700 active:scale-95 border border-zinc-750'
                                                            }`}
                                                        >
                                                            {emoji}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="glass-card rounded-2xl p-8 text-center text-gray-400">
                                        <p>This page is currently under construction. Please use the Dashboard or Virtual Mouse navigation links.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </main>
                </div>
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
# === GAP: MISSING LINE 3011 ===
# === GAP: MISSING LINE 3012 ===
# === GAP: MISSING LINE 3013 ===
# === GAP: MISSING LINE 3014 ===
# === GAP: MISSING LINE 3015 ===
# === GAP: MISSING LINE 3016 ===
# === GAP: MISSING LINE 3017 ===
# === GAP: MISSING LINE 3018 ===
# === GAP: MISSING LINE 3019 ===
# === GAP: MISSING LINE 3020 ===
# === GAP: MISSING LINE 3021 ===
# === GAP: MISSING LINE 3022 ===
# === GAP: MISSING LINE 3023 ===
# === GAP: MISSING LINE 3024 ===
# === GAP: MISSING LINE 3025 ===
# === GAP: MISSING LINE 3026 ===
# === GAP: MISSING LINE 3027 ===
# === GAP: MISSING LINE 3028 ===
# === GAP: MISSING LINE 3029 ===
# === GAP: MISSING LINE 3030 ===
# === GAP: MISSING LINE 3031 ===
# === GAP: MISSING LINE 3032 ===
# === GAP: MISSING LINE 3033 ===
# === GAP: MISSING LINE 3034 ===
# === GAP: MISSING LINE 3035 ===
# === GAP: MISSING LINE 3036 ===
# === GAP: MISSING LINE 3037 ===
# === GAP: MISSING LINE 3038 ===
# === GAP: MISSING LINE 3039 ===
# === GAP: MISSING LINE 3040 ===
# === GAP: MISSING LINE 3041 ===
# === GAP: MISSING LINE 3042 ===
# === GAP: MISSING LINE 3043 ===
# === GAP: MISSING LINE 3044 ===
# === GAP: MISSING LINE 3045 ===
# === GAP: MISSING LINE 3046 ===
# === GAP: MISSING LINE 3047 ===
# === GAP: MISSING LINE 3048 ===
# === GAP: MISSING LINE 3049 ===
# === GAP: MISSING LINE 3050 ===
# === GAP: MISSING LINE 3051 ===
# === GAP: MISSING LINE 3052 ===
# === GAP: MISSING LINE 3053 ===
# === GAP: MISSING LINE 3054 ===
# === GAP: MISSING LINE 3055 ===
# === GAP: MISSING LINE 3056 ===
# === GAP: MISSING LINE 3057 ===
# === GAP: MISSING LINE 3058 ===
# === GAP: MISSING LINE 3059 ===
# === GAP: MISSING LINE 3060 ===
# === GAP: MISSING LINE 3061 ===
# === GAP: MISSING LINE 3062 ===
# === GAP: MISSING LINE 3063 ===
# === GAP: MISSING LINE 3064 ===
# === GAP: MISSING LINE 3065 ===
# === GAP: MISSING LINE 3066 ===
# === GAP: MISSING LINE 3067 ===
# === GAP: MISSING LINE 3068 ===
# === GAP: MISSING LINE 3069 ===
# === GAP: MISSING LINE 3070 ===
# === GAP: MISSING LINE 3071 ===
# === GAP: MISSING LINE 3072 ===
# === GAP: MISSING LINE 3073 ===
# === GAP: MISSING LINE 3074 ===
# === GAP: MISSING LINE 3075 ===
# === GAP: MISSING LINE 3076 ===
# === GAP: MISSING LINE 3077 ===
# === GAP: MISSING LINE 3078 ===
# === GAP: MISSING LINE 3079 ===
# === GAP: MISSING LINE 3080 ===
# === GAP: MISSING LINE 3081 ===
# === GAP: MISSING LINE 3082 ===
# === GAP: MISSING LINE 3083 ===
# === GAP: MISSING LINE 3084 ===
# === GAP: MISSING LINE 3085 ===
# === GAP: MISSING LINE 3086 ===
# === GAP: MISSING LINE 3087 ===
# === GAP: MISSING LINE 3088 ===
# === GAP: MISSING LINE 3089 ===
# === GAP: MISSING LINE 3090 ===
# === GAP: MISSING LINE 3091 ===
# === GAP: MISSING LINE 3092 ===
# === GAP: MISSING LINE 3093 ===
# === GAP: MISSING LINE 3094 ===
# === GAP: MISSING LINE 3095 ===
# === GAP: MISSING LINE 3096 ===
# === GAP: MISSING LINE 3097 ===
# === GAP: MISSING LINE 3098 ===
# === GAP: MISSING LINE 3099 ===
# === GAP: MISSING LINE 3100 ===
# === GAP: MISSING LINE 3101 ===
# === GAP: MISSING LINE 3102 ===
# === GAP: MISSING LINE 3103 ===
# === GAP: MISSING LINE 3104 ===
# === GAP: MISSING LINE 3105 ===
# === GAP: MISSING LINE 3106 ===
# === GAP: MISSING LINE 3107 ===
# === GAP: MISSING LINE 3108 ===
# === GAP: MISSING LINE 3109 ===
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : activeMenu === 'keyboard' ? (
                                    <>
                                        {/* Hero Header Section */}
                                        <div className="glass-panel rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between border border-glass-border relative overflow-hidden">
                                            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                            <div>
                                                <h2 className="text-2xl font-bold tracking-wide text-white">Virtual Keyboard Controls</h2>
                                                <p className="text-xs text-gray-400 mt-1 max-w-xl">
                                                    Type text using standard mouse clicks or finger-pinch gestures. Customize your layouts and monitor live inputs.
                                                </p>
                                            </div>
                                            <div className="mt-4 md:mt-0">
                                                <span className="px-4 py-2 rounded-full text-xs font-semibold border bg-emerald-500/10 border-emerald-500/20 text-accent-green">
                                                    Interactive
                                                </span>
                                            </div>
                                        </div>

                                        {/* Two-Column Main Content Layout */}
                                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                            {/* Left: Camera Feed Preview (2 Columns) */}
                                            <div className="lg:col-span-2 flex flex-col gap-4">
                                                <div className="glass-card rounded-2xl p-4 flex flex-col h-[400px] justify-between relative group overflow-hidden">
                                                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                                    
                                                    <div className="flex items-center justify-between pb-3 border-b border-glass-border">
                                                        <div className="flex items-center gap-2 text-sm">
                                                            <CameraIcon className="w-4 h-4 text-accent-blue" />
                                                            <span className="font-semibold text-white">Live Camera Stream</span>
                                                        </div>
                                                        <div className="flex items-center gap-
# === GAP: MISSING LINE 3146 ===
# === GAP: MISSING LINE 3147 ===
# === GAP: MISSING LINE 3148 ===
# === GAP: MISSING LINE 3149 ===
# === GAP: MISSING LINE 3150 ===
# === GAP: MISSING LINE 3151 ===
# === GAP: MISSING LINE 3152 ===
# === GAP: MISSING LINE 3153 ===
                                                        {cameraStatus === 'Connected' && hasFrameState ? (
                                                            <img 
                                                                id="keyboard-camera-preview"
                                                                alt="Camera Feed" 
                                                                className="w-full h-full object-contain rounded-xl"
                                                            />
                                                        ) : (
                                                            <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm">
                                                                <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 mb-4 animate-pulse">
                                                                    <VideoOffIcon className="w-8 h-8" />
                                                                </div>
                                                                <h4 className="text-white font-medium mb-1">Camera Stream Inactive</h4>
                                                                <p className="text-xs text-gray-400 leading-relaxed">
                                                                    To analyze hand geometry and process keyboard inputs, please launch the camera from the Dashboard.
                                                                </p>
                                                            </div>
                                                        )}
                                                    >
                                                        Enter
                                                    </button>
                                                </div>

                                                {/* Row 4 */}
                                                <div className="flex gap-1.5 w-full justify-between">
                                                    <button 
                                                        data-key="Shift"
                                                        onMouseEnter={() => setHoveredKey('Shift')}
                                                        onMouseLeave={() => setHoveredKey('None')}
                                                        onClick={() => handleWebKeyPress('Shift')}
                                                        className={`w-24 h-12 rounded-lg text-xs font-bold transition-all duration-100 ${
                                                            pressedKey === 'Shift' 
                                                                ? 'bg-amber-500 text-black scale-95' 
                                                                : hoveredKey === 'Shift'
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : isShiftActive 
                                                                        ? 'bg-blue-600 hover:bg-blue-500 text-white' 
                                                                        : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Shift
                                                    </button>
                                                    {["Z", "X", "C", "V", "B", "N", "M"].map(key => {
                                                        const label = isCapsLockActive || isShiftActive ? key.toUpperCase() : key.toLowerCase();
                                                        return (
                                                            <button 
                                                                key={key}
                                                                data-key={key}
                                                                onMouseEnter={() => setHoveredKey(key)}
                                                                onMouseLeave={() => setHoveredKey('None')}
                                                                onClick={() => handleWebKeyPress(key)}
                                                                className={`flex-1 h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                                    pressedKey === key 
                
# === GAP: MISSING LINE 3207 ===
# === GAP: MISSING LINE 3208 ===
# === GAP: MISSING LINE 3209 ===
# === GAP: MISSING LINE 3210 ===
# === GAP: MISSING LINE 3211 ===
# === GAP: MISSING LINE 3212 ===
# === GAP: MISSING LINE 3213 ===
# === GAP: MISSING LINE 3214 ===
# === GAP: MISSING LINE 3215 ===
# === GAP: MISSING LINE 3216 ===
# === GAP: MISSING LINE 3217 ===
# === GAP: MISSING LINE 3218 ===
# === GAP: MISSING LINE 3219 ===
# === GAP: MISSING LINE 3220 ===
# === GAP: MISSING LINE 3221 ===
# === GAP: MISSING LINE 3222 ===
# === GAP: MISSING LINE 3223 ===
# === GAP: MISSING LINE 3224 ===
# === GAP: MISSING LINE 3225 ===
# === GAP: MISSING LINE 3226 ===
# === GAP: MISSING LINE 3227 ===
# === GAP: MISSING LINE 3228 ===
# === GAP: MISSING LINE 3229 ===
# === GAP: MISSING LINE 3230 ===
# === GAP: MISSING LINE 3231 ===
# === GAP: MISSING LINE 3232 ===
# === GAP: MISSING LINE 3233 ===
# === GAP: MISSING LINE 3234 ===
# === GAP: MISSING LINE 3235 ===
# === GAP: MISSING LINE 3236 ===
# === GAP: MISSING LINE 3237 ===
# === GAP: MISSING LINE 3238 ===
# === GAP: MISSING LINE 3239 ===
                                                        className={`w-full h-12 rounded-lg text-sm font-semibold transition-all duration-100 ${
                                                            pressedKey === 'Space' 
                                                                ? 'bg-amber-500 text-black scale-95' 
                                                                : hoveredKey === 'Space'
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750 active:scale-95'
                                                        }`}
                                                    >
                                                        Space
                                                    </button>
                                                </div>

                                                {/* Row 6 (Emojis) */}
                                                <div className="flex gap-1.5 w-full justify-between mt-2">
                                                    {["😊", "😂", "👍", "🔥", "❤️", "🎉", "✨", "🚀", "👋", "👀"].map(emoji => (
                                                        <button
                                                            key={emoji}
# === GAP: MISSING LINE 3257 ===
# === GAP: MISSING LINE 3258 ===
# === GAP: MISSING LINE 3259 ===
# === GAP: MISSING LINE 3260 ===
# === GAP: MISSING LINE 3261 ===
# === GAP: MISSING LINE 3262 ===
# === GAP: MISSING LINE 3263 ===
# === GAP: MISSING LINE 3264 ===
# === GAP: MISSING LINE 3265 ===
# === GAP: MISSING LINE 3266 ===
# === GAP: MISSING LINE 3267 ===
# === GAP: MISSING LINE 3268 ===
# === GAP: MISSING LINE 3269 ===
                                                                onClick={handleClearBuffer}
                                                                className="px-2.5 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[10px] font-semibold border border-red-500/10 transition-colors"
                                                            >
                                                                Clear Buffer
                                                            </button>
                                                        </div>
                                                        <textarea 
                                                            readOnly
                                                            value={typedText}
                                                            className="flex-1 w-full bg-zinc-950/60 rounded-xl p-3 border border-glass-border text-sm text-gray-200 focus:outline-none focus:border-blue-500/40 font-mono resize-none"
                                                            placeholder="Typed output will stream here..."
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* QWERTY Keyboard Grid Section */}
                                        <div className="glass-panel rounded-3xl p-6 border border-glass-border relative overflow-hidden flex flex-col gap-4">
                                            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                            <div>
                                                <h3 className="text-lg font-bold text-white">QWERTY Keyboard Grid</h3>
                                                <p className="text-xs text-gray-400">Click keys to trigger typing action. Layout dynamically matches Caps/Shift states.</p>
                                            </div>

                                            {/* Responsive Keyboard */}
                                            <div className="flex flex-col gap-2 max-w-4xl mx-auto w-full bg-zinc-950/40 p-4 rounded-2xl border border-glass-border">
                                                {/* Suggestions Bar */}
                                                <div className="flex gap-2 w-full mb-2">
                                                    {[0, 1, 2].map(idx => {
                                                        const pred = predictions[idx] || '';
# === GAP: MISSING LINE 3301 ===
# === GAP: MISSING LINE 3302 ===
# === GAP: MISSING LINE 3303 ===
# === GAP: MISSING LINE 3304 ===
# === GAP: MISSING LINE 3305 ===
# === GAP: MISSING LINE 3306 ===
# === GAP: MISSING LINE 3307 ===
# === GAP: MISSING LINE 3308 ===
# === GAP: MISSING LINE 3309 ===
# === GAP: MISSING LINE 3310 ===
# === GAP: MISSING LINE 3311 ===
# === GAP: MISSING LINE 3312 ===
# === GAP: MISSING LINE 3313 ===
# === GAP: MISSING LINE 3314 ===
# === GAP: MISSING LINE 3315 ===
# === GAP: MISSING LINE 3316 ===
# === GAP: MISSING LINE 3317 ===
# === GAP: MISSING LINE 3318 ===
# === GAP: MISSING LINE 3319 ===
# === GAP: MISSING LINE 3320 ===
# === GAP: MISSING LINE 3321 ===
# === GAP: MISSING LINE 3322 ===
# === GAP: MISSING LINE 3323 ===
# === GAP: MISSING LINE 3324 ===
# === GAP: MISSING LINE 3325 ===
# === GAP: MISSING LINE 3326 ===
# === GAP: MISSING LINE 3327 ===
# === GAP: MISSING LINE 3328 ===
# === GAP: MISSING LINE 3329 ===
# === GAP: MISSING LINE 3330 ===
# === GAP: MISSING LINE 3331 ===
# === GAP: MISSING LINE 3332 ===
# === GAP: MISSING LINE 3333 ===
# === GAP: MISSING LINE 3334 ===
# === GAP: MISSING LINE 3335 ===
# === GAP: MISSING LINE 3336 ===
# === GAP: MISSING LINE 3337 ===
# === GAP: MISSING LINE 3338 ===
# === GAP: MISSING LINE 3339 ===
# === GAP: MISSING LINE 3340 ===
# === GAP: MISSING LINE 3341 ===
# === GAP: MISSING LINE 3342 ===
# === GAP: MISSING LINE 3343 ===
# === GAP: MISSING LINE 3344 ===
# === GAP: MISSING LINE 3345 ===
# === GAP: MISSING LINE 3346 ===
# === GAP: MISSING LINE 3347 ===
# === GAP: MISSING LINE 3348 ===
# === GAP: MISSING LINE 3349 ===
                                                                <span className="text-sm font-bold text-white">{webBrushColorName}</span>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Settings Controls Card */}
                                                    <div className="glass-panel rounded-3xl p-6 border border-glass-border">
                                                        <h3 className="text-lg font-bold text-white mb-4">Drawing Controls</h3>
                                                        
                                                        {/* Size Slider */}
                                                        <div className="mb-4">
                                                            <div className="flex justify-between text-xs text-gray-400 mb-2">
                                                                <span>Brush Size</span>
                                                                <span>{webBrushSize} px</span>
                                                            </div>
                                                            <input 
                                                                type="range"
                                                                min="1"
    
# === GAP: MISSING LINE 3369 ===
# === GAP: MISSING LINE 3370 ===
# === GAP: MISSING LINE 3371 ===
# === GAP: MISSING LINE 3372 ===
# === GAP: MISSING LINE 3373 ===
# === GAP: MISSING LINE 3374 ===
# === GAP: MISSING LINE 3375 ===
# === GAP: MISSING LINE 3376 ===
# === GAP: MISSING LINE 3377 ===
# === GAP: MISSING LINE 3378 ===
# === GAP: MISSING LINE 3379 ===
# === GAP: MISSING LINE 3380 ===
# === GAP: MISSING LINE 3381 ===
# === GAP: MISSING LINE 3382 ===
# === GAP: MISSING LINE 3383 ===
# === GAP: MISSING LINE 3384 ===
# === GAP: MISSING LINE 3385 ===
# === GAP: MISSING LINE 3386 ===
# === GAP: MISSING LINE 3387 ===
# === GAP: MISSING LINE 3388 ===
# === GAP: MISSING LINE 3389 ===
# === GAP: MISSING LINE 3390 ===
# === GAP: MISSING LINE 3391 ===
# === GAP: MISSING LINE 3392 ===
# === GAP: MISSING LINE 3393 ===
# === GAP: MISSING LINE 3394 ===
# === GAP: MISSING LINE 3395 ===
# === GAP: MISSING LINE 3396 ===
# === GAP: MISSING LINE 3397 ===
# === GAP: MISSING LINE 3398 ===
# === GAP: MISSING LINE 3399 ===
# === GAP: MISSING LINE 3400 ===
# === GAP: MISSING LINE 3401 ===
# === GAP: MISSING LINE 3402 ===
# === GAP: MISSING LINE 3403 ===
# === GAP: MISSING LINE 3404 ===
# === GAP: MISSING LINE 3405 ===
# === GAP: MISSING LINE 3406 ===
# === GAP: MISSING LINE 3407 ===
# === GAP: MISSING LINE 3408 ===
# === GAP: MISSING LINE 3409 ===
# === GAP: MISSING LINE 3410 ===
# === GAP: MISSING LINE 3411 ===
# === GAP: MISSING LINE 3412 ===
# === GAP: MISSING LINE 3413 ===
# === GAP: MISSING LINE 3414 ===
# === GAP: MISSING LINE 3415 ===
# === GAP: MISSING LINE 3416 ===
# === GAP: MISSING LINE 3417 ===
# === GAP: MISSING LINE 3418 ===
# === GAP: MISSING LINE 3419 ===
# === GAP: MISSING LINE 3420 ===
# === GAP: MISSING LINE 3421 ===
# === GAP: MISSING LINE 3422 ===
# === GAP: MISSING LINE 3423 ===
# === GAP: MISSING LINE 3424 ===
# === GAP: MISSING LINE 3425 ===
# === GAP: MISSING LINE 3426 ===
# === GAP: MISSING LINE 3427 ===
# === GAP: MISSING LINE 3428 ===
# === GAP: MISSING LINE 3429 ===
# === GAP: MISSING LINE 3430 ===
# === GAP: MISSING LINE 3431 ===
# === GAP: MISSING LINE 3432 ===
# === GAP: MISSING LINE 3433 ===
# === GAP: MISSING LINE 3434 ===
                                                            >
                                                                🗑 Clear
                                                                className="py-2 px-3 rounded-xl font-semibold text-xs bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-200 active:scale-95 transition-all"
                                                            >
                                                                🗑 Clear
                                                            </button>
                                                            <button 
                                                                onClick={handleWebSave}
                                                                disabled={undoStack.length === 0}
                                                                className={`py-2 px-3 rounded-xl font-semibold text-xs border transition-all ${
                                                                    undoStack.length === 0
                                                                        ? 'bg-zinc-850/40 border-zinc-900/10 text-zinc-650 cursor-not-allowed'
                                                                        : 'bg-blue-600/20 hover:bg-blue-600/30 border-blue-500/30 text-blue-200 active:scale-95'
                                                                }`}
                                                            >
                                                                💾 Save PNG
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <p>This page is currently under construction. Please use the Dashboard or Virtual Mouse navigation links.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </main>
                    </div>
                );
            }

            const root = ReactDOM.createRoot(document.getElementById('root'));
            root.render(<App />);
        </script>
    </body>
</html>

@app.get("/static/react.min.js")
def get_react():
    from fastapi.responses import FileResponse
    return FileResponse("static/react.min.js", media_type="application/javascript")

@app.get("/static/react-dom.min.js")
def get_react_dom():
    from fastapi.responses import FileResponse
    return FileResponse("static/react-dom.min.js", media_type="application/javascript")

@app.get("/static/babel.min.js")
def get_babel():
    from fastapi.responses import FileResponse
    return FileResponse("static/babel.min.js", media_type="application/javascript")

@app.get("/static/tailwind.js")
def get_tailwind():
    from fastapi.responses import FileResponse
                                                            pressedKey === 'Backspace' 
                                                                ? 'bg-amber-500 text-black scale-95' 
                                                                : hoveredKey === 'Backspace'
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Backspace
                                                    </button>
                                                </div>

                                                {/* Row 5 */}
                                                <div className="flex gap-1.5 w-full justify-between">
                                                    <button 
                                                        data-key="Space"
                                                        onMouseEnter={() => setHoveredKey('Space')}
                                                        onMouseLeave={() => setHoveredKey('None')}
                                                        onClick={() => handleWebKeyPress('Space')}
    
# === GAP: MISSING LINE 3509 ===
# === GAP: MISSING LINE 3510 ===
# === GAP: MISSING LINE 3511 ===
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750 active:scale-95'
                                                        }`}
                                                    >
                                                        Space
                                                    </button>
                                                </div>

                                                {/* Row 6 (Emojis) */}
                                                <div className="flex gap-1.5 w-full justify-between mt-2">
                                                    {["😊", "😂", "👍", "🔥", "❤️", "🎉", "✨", "🚀", "👋", "👀"].map(emoji => (
                                                        <button
                                                            key={emoji}
                                                            data-key={emoji}
                                                            onMouseEnter={() => setHoveredKey(emoji)}
                                                            onMouseLeave={() => setHoveredKey('None')}
                                                            onClick={() => handleWebKeyPress(emoji)}
                                                            className={`flex-1 h-10 rounded-lg text-base transition-all duration-100 ${
                                                                pressedKey === emoji
                                                                    ? 'bg-amber-500 text-black scale-95'
                                                                    : hoveredKey === emoji
                                                                        ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                        : 'b
                                                            }`}
                                                        >
                                                            {emoji}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                                       ) : activeMenu === 'drawing' ? (
                                        <>
                                            {/* Hero Header Section - Hidden in fullscreen mode */}
                                            {!fullScreenMode && (
                                                <div className="glass-panel rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between border border-glass-border relative overflow-hidden">
                                                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                                    <div>
                                                        <h2 className="text-2xl font-bold tracking-wide text-white">Air Drawing Canvas</h2>
                                                        <p className="text-xs text-gray-400 mt-1 max-w-xl">
                                                            Draw in the air using finger pinch gestures. Customize brush size and color, and manage drawings.
                                                        </p>
                                                    </div>
                                                    <div className="mt-4 md:mt-0">
                                                        <span className="px-4 py-2 rounded-full text-xs font-semibold border bg-emerald-500/10 border-emerald-500/20 text-accent-green">
                                                            Live Canvas
                                                        </span>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Drawing Page Layout */}
                                            <div className={`grid grid-cols-1 ${fullScreenMode ? '' : 'lg:grid-cols-3 gap-6 mt-6'}`}>
                                                {/* Canvas Workspace Column */}
                                                <div className={`relative ${
                                                    fullScreenMode 
                                                        ? 'fixed inset-0 w-screen h-screen z-50 p-0 m-0 overflow-hidden bg-[#0b0a15]' 
                                                        : 'lg:col-span-2 glass-panel rounded-3xl p-6 border border-glass-border flex flex-col relative bg-black/40 min-h-[500px]'
                                                }`} id="drawing-view-container">
                                                    <div 
                                                        id="drawing-canvas-wrapper" 
                                                        className={`relative w-full h-full overflow-hidden rounded-2xl ${
                                                            fullScreenMode ? 'rounded-none' : 'border border-glass-border'
                                                        } ${backgroundMode === 'whiteboard' ? 'whiteboard-grid' : 'bg-zinc-950'}`}
                                                        style={{ minHeight: fullScreenMode ? '100vh
# === GAP: MISSING LINE 3576 ===
# === GAP: MISSING LINE 3577 ===
# === GAP: MISSING LINE 3578 ===
# === GAP: MISSING LINE 3579 ===
# === GAP: MISSING LINE 3580 ===
# === GAP: MISSING LINE 3581 ===
# === GAP: MISSING LINE 3582 ===
# === GAP: MISSING LINE 3583 ===
# === GAP: MISSING LINE 3584 ===
# === GAP: MISSING LINE 3585 ===
# === GAP: MISSING LINE 3586 ===
# === GAP: MISSING LINE 3587 ===
# === GAP: MISSING LINE 3588 ===
# === GAP: MISSING LINE 3589 ===
# === GAP: MISSING LINE 3590 ===
# === GAP: MISSING LINE 3591 ===
# === GAP: MISSING LINE 3592 ===
# === GAP: MISSING LINE 3593 ===
# === GAP: MISSING LINE 3594 ===
# === GAP: MISSING LINE 3595 ===
# === GAP: MISSING LINE 3596 ===
# === GAP: MISSING LINE 3597 ===
# === GAP: MISSING LINE 3598 ===
# === GAP: MISSING LINE 3599 ===
# === GAP: MISSING LINE 3600 ===
# === GAP: MISSING LINE 3601 ===
# === GAP: MISSING LINE 3602 ===
# === GAP: MISSING LINE 3603 ===
# === GAP: MISSING LINE 3604 ===
                                                                    <div className="flex items-center gap-1.5">
                                                                        <button 
                                                                            onClick={() => setPipSize(prev => prev === 'sm' ? 'md' : prev === 'md' ? 'lg' : 'sm')}
                                                                            className="text-[10px] text-white hover:text-blue-400 bg-white/5 px-1.5 py-0.5 rounded border border-white/5"
                                                                            title="Resize Preview"
                                                                        >
                                                                            ⤢
                                                                        </button>
                                                                        <button 
                                                                            onClick={() => setPipHidden(true)}
                                                                            className="text-[10px] text-white hover:text-red-400 bg-white/5 px-1.5 py-0.5 rounded border border-white/5"
                                                                            title="Hide Preview"
                                                                        >
                                                                            ✕
                                                                        </button>
                                                                    </div>
# === GAP: MISSING LINE 3621 ===
# === GAP: MISSING LINE 3622 ===
# === GAP: MISSING LINE 3623 ===
# === GAP: MISSING LINE 3624 ===
# === GAP: MISSING LINE 3625 ===
# === GAP: MISSING LINE 3626 ===
# === GAP: MISSING LINE 3627 ===
# === GAP: MISSING LINE 3628 ===
# === GAP: MISSING LINE 3629 ===
                                                                />
                                                            </div>
                                                        )}
                                                        
                                                        {/* Button to restore PiP if hidden */}
                                                        {backgroundMode === 'whiteboard' && pipHidden && (
                                                            <button
                                                                onClick={() => setPipHidden(false)}
                                                                className="absolute bottom-6 right-6 z-20 px-3 py-1.5 rounded-xl bg-blue-600/30 hover:bg-blue-600/50 border border-blue-500/30 text-xs font-semibold text-white transition-all active:scale-95"
                                                            >
                                                                📷 Show Camera
                                                            </button>
                                                        )}

                                                        {/* Custom Circular Cursor Indicator */}
                                                        <div 
                                                            id="drawing-cursor"
                                                            className="absolute pointer-ev
# === GAP: MISSING LINE 3648 ===
# === GAP: MISSING LINE 3649 ===
# === GAP: MISSING LINE 3650 ===
# === GAP: MISSING LINE 3651 ===
# === GAP: MISSING LINE 3652 ===
# === GAP: MISSING LINE 3653 ===
# === GAP: MISSING LINE 3654 ===
                                                            {/* Core brush pointer */}
                                                            <div 
                                                                className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/30 cursor-dot"
                                                                style={{ 
                                                                    width: '5px', 
                                                                    height: '5px',
                                                                    backgroundColor: '#c6a0f6' 
                                                                }}
                                                            />

                                                            {/* Telemetry Tooltip Pill */}
                                                            <div className="absolute top-full mt-3 left-1/2 transform -translate-x-1/2 px-2.5 py-1 rounded-full bg-zinc-950/90 border border-white/10 flex items-center gap-1.5 text-[9px] font-semibold text-white pointer-events-none whitespace-nowrap shadow-xl">
                                                                <span className="w-1.5 h-1.5 rounded-full cursor-color-badge" style={{ backgroundColor: '#c6a0f6' }} />
                                                                <span className="cursor-size">5px</span>
                                                                <span className="text-gray-500">|</span>
                                                                <span className="cursor-state" style={{ color: '#8aadf4' }}>
                                                                    HOVER
                                                                </span>
                                                                <span className="text-gray-500">|</span>
                                                                <span className="cursor-confidence">--%</span>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Floating Toolbar/Dock in Full Screen Mode */}
                                                    {fullScreenMode && (
                                                        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 glass-panel border border-glass-border px-6 py-3 rounded-2xl flex items-center gap-5 shadow-2xl z-40 transition-all duration-300">
                                                            {/* Exit Full Screen */}
                                                            <button 
                                                                onClick={() => setFullScreenMode(false)}
                                                                className="p-2 rounded-lg bg-zinc-855 hover:bg-zinc-750 text-white font-semibold text-xs border border-zinc-700 transition-all active:scale-95 flex items-center gap-1"
                                                                title="Exit Full Screen"
                                                            >
                                                                🗙 Exit Fullscreen
                                                            </button>

                                                            <span className="w-px h-6 bg-glass-border" />

                                                            {/* View Mode Toggle */}
                                                            <div className="flex bg-zinc-900 rounded-lg p-0.5 border border-zinc-800">
                                                                <button 
                                                                    onClick={() => setBackgroundMode('camera')}
                                                                    className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${
                                                                        backgroundMode === 'camera' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
                                                                    }`}
                                                                >
# === GAP: MISSING LINE 3701 ===
# === GAP: MISSING LINE 3702 ===
# === GAP: MISSING LINE 3703 ===
# === GAP: MISSING LINE 3704 ===
# === GAP: MISSING LINE 3705 ===
# === GAP: MISSING LINE 3706 ===
# === GAP: MISSING LINE 3707 ===
# === GAP: MISSING LINE 3708 ===
# === GAP: MISSING LINE 3709 ===
# === GAP: MISSING LINE 3710 ===
# === GAP: MISSING LINE 3711 ===
# === GAP: MISSING LINE 3712 ===
# === GAP: MISSING LINE 3713 ===
# === GAP: MISSING LINE 3714 ===
# === GAP: MISSING LINE 3715 ===
# === GAP: MISSING LINE 3716 ===
# === GAP: MISSING LINE 3717 ===
# === GAP: MISSING LINE 3718 ===
# === GAP: MISSING LINE 3719 ===
# === GAP: MISSING LINE 3720 ===
# === GAP: MISSING LINE 3721 ===
# === GAP: MISSING LINE 3722 ===
# === GAP: MISSING LINE 3723 ===
# === GAP: MISSING LINE 3724 ===
# === GAP: MISSING LINE 3725 ===
# === GAP: MISSING LINE 3726 ===
# === GAP: MISSING LINE 3727 ===
# === GAP: MISSING LINE 3728 ===
# === GAP: MISSING LINE 3729 ===
# === GAP: MISSING LINE 3730 ===
# === GAP: MISSING LINE 3731 ===
# === GAP: MISSING LINE 3732 ===
# === GAP: MISSING LINE 3733 ===
# === GAP: MISSING LINE 3734 ===
# === GAP: MISSING LINE 3735 ===
# === GAP: MISSING LINE 3736 ===
# === GAP: MISSING LINE 3737 ===
# === GAP: MISSING LINE 3738 ===
# === GAP: MISSING LINE 3739 ===
# === GAP: MISSING LINE 3740 ===
# === GAP: MISSING LINE 3741 ===
# === GAP: MISSING LINE 3742 ===
# === GAP: MISSING LINE 3743 ===
# === GAP: MISSING LINE 3744 ===
# === GAP: MISSING LINE 3745 ===
# === GAP: MISSING LINE 3746 ===
# === GAP: MISSING LINE 3747 ===
# === GAP: MISSING LINE 3748 ===
# === GAP: MISSING LINE 3749 ===
                                                            </div>

                                                            <span className="w-px h-6 bg-glass-border" />

                                                            {/* Action Buttons */}
                                                            <div className="flex gap-1.5">
                                                                <button 
                                                                    onClick={handleWebUndo}
                                                                    disabled={undoStack.length === 0}
                                                                    className={`p-1.5 rounded-lg border transition-all text-xs ${
                                                        </span>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Drawing Page Layout */}
                                            <div className={`grid grid-cols-1 ${fullScreenMode ? '' : 'lg:grid-cols-3 gap-6 mt-6'}`}>
                                                {/* Canvas Workspace Column */}
                                                <div className={`relative ${
                                                    fullScreenMode 
                                                        ? 'fixed inset-0 w-screen h-screen z-50 p-0 m-0 overflow-hidden bg-[#0b0a15]' 
                                                        : 'lg:col-span-2 glass-panel rounded-3xl p-6 border border-glass-border flex flex-col relative bg-black/40 min-h-[500px]'
                                                }`} id="drawing-view-container">
                                                    <div 
                                                        id="drawing-canvas-wrapper" 
                                                        className={`relative w-full h-full overflow-hidden rounded-2xl ${
                                                            fullScreenMode ? 'rounded-none' : 'border border-glass-border'
                                        
# === GAP: MISSING LINE 3778 ===
# === GAP: MISSING LINE 3779 ===
                                                        {/* Camera Video Stream (Background in Camera mode) */}
                                                        {backgroundMode === 'camera' && (
                                                            <img 
                                                                id="drawing-camera-preview"
                                                                src="" 
                                                                alt="Camera Stream"
                                                                className="absolute inset-0 w-full h-full object-cover select-none pointer-events-none"
                                                            />
                                                        )}

                                                        {/* HTML5 Canvas Drawing Overlay Layer */}
                                                        <canvas 
                                                            id="drawing-canvas"
                                                            width={canvasWidth}
                                                            height={canvasHeight}
                                                            className="absolute inset-0 w-full h-full cursor-crosshair select-none z-10"
                                                        />

                                                        {/* Floating PiP Camera Card (in Whiteboard mode) */}
                                                        {backgroundMode === 'whiteboard' && !pipHidden && (
                                                    <button 
                                                        data-key="Backspace"
                                                        onMouseEnter={() => setHoveredKey('Backspace')}
                                                        onMouseLeave={() => setHoveredKey('None')}
                                                        onClick={() => handleWebKeyPress('Backspace')}
                                                        className={`w-28 h-12 rounded-lg text-xs font-bold transition-all duration-100 ${
                                                            pressedKey === 'Backspace' 
                                                                ? 'bg-amber-500 text-black scale-95' 
                                                                : hoveredKey === 'Backspace'
                                                                    ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                    : 'bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-zinc-750'
                                                        }`}
                                                    >
                                                        Backspace
                                                    </button>
                                                </div>

                        
                                                                    <span className="text-xs text-gray-400">Pinch Distance</span>
                                                                    <span className="text-sm font-bold text-white font-mono">{pinchDistance.toFixed(4)}</span>
                                                                </div>
                                                                <div className="flex justify-between items-center py-2 border-b border-white/5">
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                                <img 
                                                                    id="drawing-camera-preview-pip"
                                                                    src="" 
                                                                    alt="Camera Stream PiP"
                                                                    className="w-full h-full object-cover select-none pointer-events-none"
                                                                />
                                                            </div>
                                                        )}
                                                        
                                                        {/* Button to restore PiP if hidden */}
                                                        {backgroundMode === 'whiteboard' && pipHidden && (
                                                            <button
                                                                onClick={() => setPipHidden(false)}
                                                                className="absolute bottom-6 right-6 z-20 px-3 py-1.5 rounded-xl bg-blue-600/30 hover:bg-blue-600/50 border border-blue-500/30 text-xs font-semibold text-white transition-all active:scale-95"
                                                            >
                                                                📷 Show Camera
                                                            </button>
                                                        )}

                                                        {/* Custom Circular Cursor Indicator */}
                                                        <div 
                                                                pressedKey === emoji
                                                                    ? 'bg-amber-500 text-black scale-95'
                                                                    : hoveredKey === emoji
                                                                        ? 'bg-blue-600/40 text-white border border-blue-500/80 shadow-md shadow-blue-500/20'
                                                                        : 'bg-zinc-850 hover:bg-zinc-700 active:scale-95 border border-zinc-750'
                                                            }`}
                                                        >
                                                            {emoji}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : activeMenu === 'drawing' ? (
                                        <>
                                            {/* Hero Header Section - Hidden in fullscreen mode */}
                                            {!fullScreenMode && (
                                                <div className="glass-panel rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between border border-glass-border relative overflow-hidden">
                                                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                                                    <div>
                                                        <h2 className="text-2xl font-bold tracking-wide text-white">Air Drawing Canvas</h2>
                                                        <p className="text-xs text-gray-400 mt-1 max-w-xl">
                                                            Draw in the air using finger pinch gestures. Customize brush size and color, and manage drawings.
                                                        </p>
                                                    </div>
                                                    <div className="mt-4 md:mt-0">
                                                        <span className="px-4 py-2 rounded-full text-xs font-semibold border bg-emerald-500/10 border-emerald-500/20 text-accent-green">
                                                            Live Canvas
                                                        </span>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Drawing Page Layout */}
                                            <div className={`grid grid-cols-1 ${fullScreenMode ? '' : 'lg:grid-cols-3 gap-6 mt-6'}`}>
                                                {/* Canvas Workspace Column */}
                                           
                                                        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 glass-panel border border-glass-border px-6 py-3 rounded-2xl flex items-center gap-5 shadow-2xl z-40 transition-all duration-300">
                                                            {/* Exit Full Screen */}
                                                            <button 
                                                                onClick={() => setFullScreenMode(false)}
                                                                className="p-2 rounded-lg bg-zinc-855 hover:bg-zinc-750 text-white font-semibold text-xs border border-zinc-700 transition-all active:scale-95 flex items-center gap-1"
                                                                title="Exit Full Screen"
                                                            >
                                                                🗙 Exit Fullscreen
                                                            </button>

                                                            <span className="w-px h-6 bg-glass-border" />

                                                            {/* View Mode Toggle */}
                                                            <div className="flex bg-zinc-900 rounded-lg p-0.5 border border-zinc-800">
                                                                <button 
                                                                    onClick={() => setBackgroundMode('camera')}
                                                                    className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${
                                                                        backgroundMode === 'camera' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
                                                                    }`}
                                                                >
                                                                    📷 Camera
                                                                </button>
                                                                <button 
                                                                    onClick={() => setBackgroundMode('whiteboard')}
                                                                    className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${
                                                                        backgroundMode === 'whiteboard' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
                                                                    }`}
                                                                >
                                                                    ✏️ Whiteboard
                                                                </button>
                                                            </div>

                                                            <span className="w-px h-6 bg-glass-border" />

                                                        
# === GAP: MISSING LINE 3919 ===
# === GAP: MISSING LINE 3920 ===
# === GAP: MISSING LINE 3921 ===
# === GAP: MISSING LINE 3922 ===
# === GAP: MISSING LINE 3923 ===
# === GAP: MISSING LINE 3924 ===
# === GAP: MISSING LINE 3925 ===
                                                        <div 
                                                            id="drawing-tool-menu"
                                                            className="absolute top-16 right-6 w-80 glass-panel rounded-2xl p-5 border border-white/10 bg-[#0b0a15]/85 backdrop-blur-md shadow-2xl z-30 transition-all duration-300 hidden"
                                                        >
                                                            {/* Header */}
                                                            <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
                                                                <h4 className="text-xs font-bold text-white flex items-center gap-1.5 uppercase tracking-wide">
                                                                    ✋ Tool Settings
                                                                </h4>
                                                                <button 
                                                                    onClick={() => {
                                                                        const el = document.getElementById('drawing-tool-menu');
                                                                        if (el) el.classList.add('hidden');
                                                                    }}
                                                      
# === GAP: MISSING LINE 3941 ===
# === GAP: MISSING LINE 3942 ===
# === GAP: MISSING LINE 3943 ===
# === GAP: MISSING LINE 3944 ===
# === GAP: MISSING LINE 3945 ===
# === GAP: MISSING LINE 3946 ===
# === GAP: MISSING LINE 3947 ===
# === GAP: MISSING LINE 3948 ===
# === GAP: MISSING LINE 3949 ===
# === GAP: MISSING LINE 3950 ===
# === GAP: MISSING LINE 3951 ===
# === GAP: MISSING LINE 3952 ===
# === GAP: MISSING LINE 3953 ===
# === GAP: MISSING LINE 3954 ===
# === GAP: MISSING LINE 3955 ===
# === GAP: MISSING LINE 3956 ===
# === GAP: MISSING LINE 3957 ===
# === GAP: MISSING LINE 3958 ===
                                                                            ? 'bg-zinc-850/40 border-zinc-900/10 text-zinc-650 cursor-not-allowed'
                                                                            : 'bg-zinc-800 hover:bg-zinc-700 border-zinc-700 text-white active:scale-95'
                                                                    }`}
                                                                >
                                                                    ↷ Redo
                                                                </button>
                                                                <button 
                                                                    onClick={handleWebClear}
                                                                    className="py-2 px-3 rounded-xl font-semibold text-xs bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-200 active:scale-95 transition-all"
                                                                >
                                                                    🗑 Clear
                                                                </button>
                                                                <button 
                                                                    onClick={handleWebSave}
                                                                    disabled={undoStack.length === 0}
                                                                    className={`py-2 px-3 rounded-xl font-semibold text-xs border transition-all ${
                                                                        undoStack.length === 0
                                                                            ? 'bg-zinc-850/40 border-zinc-900/10 text-zinc-650 cursor-not-allowed'
                                                                            : 'bg-blue-600/20 hover:bg-blue-600/30 border-blue-500/30 text-blue-200 active:scale-95'
                                                                    }`}
                                                                >
                                                                >
                                                                    💾 Save PNG
                                                                </button>
                                                                    onClick={handleWebClear}
                                                                    className="p-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-200 text-xs active:scale-95 transition-all"
                                                                                    : 'bg-zinc-800/50 border-zinc-700 text-gray-300'
                                                                            }`}
                                                                        >
                                                                            {size}px
                                                                        </button>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                            
                                                            {/* Gesture Guide Cheat-Sheet */}
                                                            <div className="border-t border-white/10 pt-3 mt-2 space-y-2">
                                                                <span className="text-[10px] text-gray-450 font-bold block uppercase tracking-wider">Gesture Cheat-Sheet</span>
                                                                <div className="space-y-1.5 text-[10px] text-gray-300 font-sans">
                                                                    <div className="flex justify-between py-1 px-2 rounded bg-white/5 border border-white/5">
                                                                        <span>☝️ Index UP</span>
                                                                        <span className="font-semibold text-accent-green">✏️ Draw</span>
                                                                    </div>
                                                                    <div className="flex justify-between py-1 px-2 rounded bg-white/5 border border-white/5">
                                                                        <span>✌️ Index + Middle UP</span>
                                                                        <span className="font-semibold text-accent-yellow">⏸️ Pause</span>
                                                                    </div>
                                                                    <div className="flex justify-between py-1 px-2 rounded bg-white/5 border border-white/5">
                                                                        <span>✊ Closed Fist</span>
                                                                        <span className="font-semibold text-accent-red">🗑️ Clear Canvas</span>
                                                                    </div>
                                                                    <div className="flex justify-between py-1 px-2 rounded bg-white/5 border border-white/5">
                                                                        <span>🖐️ Open Palm</span>
                                                                        <span className="font-semibold text-accent-blue">✋ Show Menu</span>
                                                                    </div>
                                                                </div>
                                                            </div>
# === GAP: MISSING LINE 4016 ===
# === GAP: MISSING LINE 4017 ===
# === GAP: MISSING LINE 4018 ===
# === GAP: MISSING LINE 4019 ===
                                                                        {drawingStatus !== 'Idle' && lastPointRef.current ? `${Math.round(lastPointRef.current.x)}, ${Math.round(lastPointRef.current.y)}` : '-- , --'}
                                                                    </span>
                                                                </div>
                                                                <div className="flex justify-between items-center py-2 border-b border-white/5">
                                                                    <span className="text-xs text-gray-400">Pinch Distance</span>
                                                                    <span id="telemetry-pinch-distance" className="text-sm font-bold text-white font-mono">{pinchDistance.toFixed(4)}</span>
                                                                </div>
                                                                <div className="flex justify-between items-center py-2 border-b border-white/5">
                                                                    <span className="text-xs text-gray-400">Pinch Confidence</span>
                                                                    <span id="telemetry-pinch-confidence" className="text-sm font-bold text-white font-mono">
                                                                        --%
                                                                    </span>
                                                                </div>
                                                                <div className="flex justify-between items-center py-2 border-b border-white/5">
                                                                    <span className="text-xs text-gray-400">Pinch State</span>
                                                                    <span id="telemetry-pinch-state" className="text-sm font-bold text-gray-450">
                                                                        Idle
                                                                    </span>
                                                                </div>
                                                                <div className="flex justify-between items-center py-2 border-b border-white/5">
                                                                    <span className="text-xs text-gray-400">Pinch / Release Frames</span>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Settings Controls Card */}
                                                        <div className="glass-panel rounded-3xl p-6 border border-glass-border space-y-5">
                                                            <h3 className="text-lg font-bold text-white pb-3 border-b border-glass-border mb-0">Drawing Controls</h3>
                                                            
# === GAP: MISSING LINE 4049 ===
# === GAP: MISSING LINE 4050 ===
# === GAP: MISSING LINE 4051 ===
# === GAP: MISSING LINE 4052 ===
# === GAP: MISSING LINE 4053 ===
# === GAP: MISSING LINE 4054 ===
# === GAP: MISSING LINE 4055 ===
# === GAP: MISSING LINE 4056 ===
# === GAP: MISSING LINE 4057 ===
# === GAP: MISSING LINE 4058 ===
# === GAP: MISSING LINE 4059 ===
# === GAP: MISSING LINE 4060 ===
# === GAP: MISSING LINE 4061 ===
# === GAP: MISSING LINE 4062 ===
# === GAP: MISSING LINE 4063 ===
# === GAP: MISSING LINE 4064 ===
# === GAP: MISSING LINE 4065 ===
# === GAP: MISSING LINE 4066 ===
# === GAP: MISSING LINE 4067 ===
# === GAP: MISSING LINE 4068 ===
# === GAP: MISSING LINE 4069 ===
# === GAP: MISSING LINE 4070 ===
# === GAP: MISSING LINE 4071 ===
# === GAP: MISSING LINE 4072 ===
# === GAP: MISSING LINE 4073 ===
# === GAP: MISSING LINE 4074 ===
# === GAP: MISSING LINE 4075 ===
# === GAP: MISSING LINE 4076 ===
# === GAP: MISSING LINE 4077 ===
# === GAP: MISSING LINE 4078 ===
# === GAP: MISSING LINE 4079 ===
# === GAP: MISSING LINE 4080 ===
# === GAP: MISSING LINE 4081 ===
                                                                    </button>
                                                                </div>
                                                            </div>

                                                            {/* Jitter Reduction Filter */}
                                                            <div className="space-y-2">
                                                                <div className="flex justify-between text-xs text-gray-400">
                                                                    <span>Jitter Filter</span>
                                                                    <span>{filterIntensity === 1 ? 'Off' : filterIntensity === 2 ? 'Low' : filterIntensity === 3 ? 'Medium' : filterIntensity === 4 ? 'High' : 'Super'}</span>
                                                                </div>
                                                                <input 
                                                                    type="range"
                                                                    min="1"
                                                                    max="5"
                                                                    value={filterIntensity}
                                                                    onChange={(e) => {
                                                                        const val = parseInt(e.target.value);
                                                                        setFilterIntensity(val);
                                                    </div>

                                                    {/* Floating Toolbar/Dock in Full Screen Mode */}
                                                    {fullScreenMode && (
                                                        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 glass-panel border border-glass-border px-6 py-3 rounded-2xl flex items-center gap-5 shadow-2xl z-40 transition-all duration-300">
                                                            {/* Exit Full Screen */}
                                                            <button 
                                                                onClick={() => setFullScreenMode(false)}
                                                                className="p-2 rounded-lg bg-zinc-855 hover:bg-zinc-750 text-white font-semibold text-xs border border-zinc-700 transition-all active:scale-95 flex items-center gap-1"
                                                                title="Exit Full Screen"
                                                            >
                                                                🗙 Exit Fullscreen
                                                            </button>

                                                            <span className="w-px h-6 bg-glass-border" />

                                                            {/* View Mode Toggle */}

# === GAP: MISSING LINE 4118 ===
# === GAP: MISSING LINE 4119 ===
# === GAP: MISSING LINE 4120 ===
# === GAP: MISSING LINE 4121 ===
# === GAP: MISSING LINE 4122 ===
# === GAP: MISSING LINE 4123 ===
# === GAP: MISSING LINE 4124 ===
# === GAP: MISSING LINE 4125 ===
# === GAP: MISSING LINE 4126 ===
# === GAP: MISSING LINE 4127 ===
# === GAP: MISSING LINE 4128 ===
# === GAP: MISSING LINE 4129 ===
# === GAP: MISSING LINE 4130 ===
# === GAP: MISSING LINE 4131 ===
# === GAP: MISSING LINE 4132 ===
# === GAP: MISSING LINE 4133 ===
# === GAP: MISSING LINE 4134 ===
# === GAP: MISSING LINE 4135 ===
# === GAP: MISSING LINE 4136 ===
# === GAP: MISSING LINE 4137 ===
# === GAP: MISSING LINE 4138 ===
# === GAP: MISSING LINE 4139 ===
# === GAP: MISSING LINE 4140 ===
# === GAP: MISSING LINE 4141 ===
# === GAP: MISSING LINE 4142 ===
# === GAP: MISSING LINE 4143 ===
# === GAP: MISSING LINE 4144 ===
# === GAP: MISSING LINE 4145 ===
# === GAP: MISSING LINE 4146 ===
# === GAP: MISSING LINE 4147 ===
# === GAP: MISSING LINE 4148 ===
# === GAP: MISSING LINE 4149 ===
# === GAP: MISSING LINE 4150 ===
# === GAP: MISSING LINE 4151 ===
# === GAP: MISSING LINE 4152 ===
# === GAP: MISSING LINE 4153 ===
# === GAP: MISSING LINE 4154 ===
# === GAP: MISSING LINE 4155 ===
# === GAP: MISSING LINE 4156 ===
# === GAP: MISSING LINE 4157 ===
# === GAP: MISSING LINE 4158 ===
                                                                    />
                                                                ))}
                                                            </div>

                                                            <span className="w-px h-6 bg-glass-border" />

                                                            {/* Size Slider (Mini) */}
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-[10px] text-gray-400 w-8">{webBrushSize}px</span>
                                                                <input 
                                                                    type="range"
                                                                    min="1"
                                                                    max="30"
                                                                    value={webBrushSize}
                                                                    onChange={(e) => setWebBrushSize(parseInt(e.target.value))}
                                                                    className="w-24 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                                                />
                                                            </div>

                                                            <span className="w-px h-6 bg-glass-border" />

                                                            {/* Action Buttons */}
# === GAP: MISSING LINE 4181 ===
# === GAP: MISSING LINE 4182 ===
# === GAP: MISSING LINE 4183 ===
# === GAP: MISSING LINE 4184 ===
# === GAP: MISSING LINE 4185 ===
# === GAP: MISSING LINE 4186 ===
# === GAP: MISSING LINE 4187 ===
# === GAP: MISSING LINE 4188 ===
# === GAP: MISSING LINE 4189 ===
# === GAP: MISSING LINE 4190 ===
# === GAP: MISSING LINE 4191 ===
# === GAP: MISSING LINE 4192 ===
# === GAP: MISSING LINE 4193 ===
# === GAP: MISSING LINE 4194 ===
# === GAP: MISSING LINE 4195 ===
# === GAP: MISSING LINE 4196 ===
# === GAP: MISSING LINE 4197 ===
# === GAP: MISSING LINE 4198 ===
# === GAP: MISSING LINE 4199 ===
                                                                    ↷
                                                                </button>
                                                                <button 
                                                                    onClick={handleWebClear}
                                                                    className="p-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-200 text-xs active:scale-95 transition-all"
                                                                    title="Clear Canvas"
                                                                >
                                                                    🗑
                                                                </button>
                                                                <button 
                                                                    onClick={handleWebSave}
                                                                    disabled={undoStack.length === 0}
                                                                    className={`p-1.5 rounded-lg border transition-all text-xs ${
                                                                        undoStack.length === 0 ? 'text-zinc-650 border-zinc-900/10 cursor-not-allowed' : 'bg-blue-600/20 hover:bg-blue-600/30 border-blue-500/30 text-blue-200 active:scale-95'
                                      
# === GAP: MISSING LINE 4215 ===
# === GAP: MISSING LINE 4216 ===
# === GAP: MISSING LINE 4217 ===
# === GAP: MISSING LINE 4218 ===
# === GAP: MISSING LINE 4219 ===
# === GAP: MISSING LINE 4220 ===
# === GAP: MISSING LINE 4221 ===
# === GAP: MISSING LINE 4222 ===
# === GAP: MISSING LINE 4223 ===
# === GAP: MISSING LINE 4224 ===
# === GAP: MISSING LINE 4225 ===
# === GAP: MISSING LINE 4226 ===
# === GAP: MISSING LINE 4227 ===
# === GAP: MISSING LINE 4228 ===
# === GAP: MISSING LINE 4229 ===
# === GAP: MISSING LINE 4230 ===
# === GAP: MISSING LINE 4231 ===
# === GAP: MISSING LINE 4232 ===
# === GAP: MISSING LINE 4233 ===
# === GAP: MISSING LINE 4234 ===
# === GAP: MISSING LINE 4235 ===
# === GAP: MISSING LINE 4236 ===
# === GAP: MISSING LINE 4237 ===
# === GAP: MISSING LINE 4238 ===
# === GAP: MISSING LINE 4239 ===
# === GAP: MISSING LINE 4240 ===
# === GAP: MISSING LINE 4241 ===
# === GAP: MISSING LINE 4242 ===
# === GAP: MISSING LINE 4243 ===
# === GAP: MISSING LINE 4244 ===
# === GAP: MISSING LINE 4245 ===
# === GAP: MISSING LINE 4246 ===
# === GAP: MISSING LINE 4247 ===
# === GAP: MISSING LINE 4248 ===
# === GAP: MISSING LINE 4249 ===
# === GAP: MISSING LINE 4250 ===
# === GAP: MISSING LINE 4251 ===
# === GAP: MISSING LINE 4252 ===
# === GAP: MISSING LINE 4253 ===
# === GAP: MISSING LINE 4254 ===
# === GAP: MISSING LINE 4255 ===
# === GAP: MISSING LINE 4256 ===
# === GAP: MISSING LINE 4257 ===
# === GAP: MISSING LINE 4258 ===
# === GAP: MISSING LINE 4259 ===
# === GAP: MISSING LINE 4260 ===
# === GAP: MISSING LINE 4261 ===
# === GAP: MISSING LINE 4262 ===
# === GAP: MISSING LINE 4263 ===
# === GAP: MISSING LINE 4264 ===
# === GAP: MISSING LINE 4265 ===
# === GAP: MISSING LINE 4266 ===
# === GAP: MISSING LINE 4267 ===
# === GAP: MISSING LINE 4268 ===
# === GAP: MISSING LINE 4269 ===
# === GAP: MISSING LINE 4270 ===
# === GAP: MISSING LINE 4271 ===
# === GAP: MISSING LINE 4272 ===
# === GAP: MISSING LINE 4273 ===
# === GAP: MISSING LINE 4274 ===
# === GAP: MISSING LINE 4275 ===
# === GAP: MISSING LINE 4276 ===
# === GAP: MISSING LINE 4277 ===
# === GAP: MISSING LINE 4278 ===
# === GAP: MISSING LINE 4279 ===
# === GAP: MISSING LINE 4280 ===
# === GAP: MISSING LINE 4281 ===
# === GAP: MISSING LINE 4282 ===
# === GAP: MISSING LINE 4283 ===
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Settings Controls Card */}
                                                        <div className="glass-panel rounded-3xl p-6 border border-glass-border space-y-5">
                                                            <h3 className="text-lg font-bold text-white pb-3 border-b border-glass-border mb-0">Drawing Controls</h3>
                                                            
                                                            {/* View Configuration */}
                                                            <div className="space-y-3">
                                                                <span className="text-xs text-gray-400 block font-semibold">View Options</span>
                                                                <div className="flex gap-2">
                                                                    <button 
                                                                        onClick={() => setFullScreenMode(true)}
                                                                        className="flex-1 py-2 px-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-white font-semibold text-xs active:scale-95 transition-all flex items-center justify-center gap-1.5"
                                                                    >
                                                                        🖥️ Fullscreen
                                                                    </button>
                                                                    <button 
                                                                        onClick={() => setBackgroundMode(prev => prev === 'camera' ? 'whiteboard' : 'camera')}
                                                                        className="flex-1 py-2 px-3 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-200 font-semibold text-xs active:scale-95 transition-all"
                                                                    >
                                                                        {backgroundMode === 'camera' ? '✏️ Whiteboard' : '📷 Camera'}
                                                                    </button>
                                                                </div>
                                                            </div>

                                                            {/* Jitter Reduction Filter */}
                                                            <div className="space-y-2">
                                                                <div className="flex justify-between text-xs text-gray-400">
                                                                    <span>Jitter Filter</span>
                  
# === GAP: MISSING LINE 4317 ===
# === GAP: MISSING LINE 4318 ===
# === GAP: MISSING LINE 4319 ===
# === GAP: MISSING LINE 4320 ===
# === GAP: MISSING LINE 4321 ===
# === GAP: MISSING LINE 4322 ===
# === GAP: MISSING LINE 4323 ===
# === GAP: MISSING LINE 4324 ===
# === GAP: MISSING LINE 4325 ===
# === GAP: MISSING LINE 4326 ===
# === GAP: MISSING LINE 4327 ===
# === GAP: MISSING LINE 4328 ===
# === GAP: MISSING LINE 4329 ===
# === GAP: MISSING LINE 4330 ===
# === GAP: MISSING LINE 4331 ===
# === GAP: MISSING LINE 4332 ===
# === GAP: MISSING LINE 4333 ===
# === GAP: MISSING LINE 4334 ===
# === GAP: MISSING LINE 4335 ===
# === GAP: MISSING LINE 4336 ===
# === GAP: MISSING LINE 4337 ===
# === GAP: MISSING LINE 4338 ===
# === GAP: MISSING LINE 4339 ===
# === GAP: MISSING LINE 4340 ===
# === GAP: MISSING LINE 4341 ===
# === GAP: MISSING LINE 4342 ===
# === GAP: MISSING LINE 4343 ===
# === GAP: MISSING LINE 4344 ===
# === GAP: MISSING LINE 4345 ===
# === GAP: MISSING LINE 4346 ===
# === GAP: MISSING LINE 4347 ===
# === GAP: MISSING LINE 4348 ===
# === GAP: MISSING LINE 4349 ===
# === GAP: MISSING LINE 4350 ===
# === GAP: MISSING LINE 4351 ===
# === GAP: MISSING LINE 4352 ===
# === GAP: MISSING LINE 4353 ===
# === GAP: MISSING LINE 4354 ===
# === GAP: MISSING LINE 4355 ===
# === GAP: MISSING LINE 4356 ===
# === GAP: MISSING LINE 4357 ===
# === GAP: MISSING LINE 4358 ===
# === GAP: MISSING LINE 4359 ===
# === GAP: MISSING LINE 4360 ===
# === GAP: MISSING LINE 4361 ===
# === GAP: MISSING LINE 4362 ===
# === GAP: MISSING LINE 4363 ===
# === GAP: MISSING LINE 4364 ===
# === GAP: MISSING LINE 4365 ===
# === GAP: MISSING LINE 4366 ===
# === GAP: MISSING LINE 4367 ===
# === GAP: MISSING LINE 4368 ===
# === GAP: MISSING LINE 4369 ===
# === GAP: MISSING LINE 4370 ===
# === GAP: MISSING LINE 4371 ===
# === GAP: MISSING LINE 4372 ===
# === GAP: MISSING LINE 4373 ===
# === GAP: MISSING LINE 4374 ===
# === GAP: MISSING LINE 4375 ===
# === GAP: MISSING LINE 4376 ===
# === GAP: MISSING LINE 4377 ===
# === GAP: MISSING LINE 4378 ===
# === GAP: MISSING LINE 4379 ===
# === GAP: MISSING LINE 4380 ===
# === GAP: MISSING LINE 4381 ===
# === GAP: MISSING LINE 4382 ===
                                                                                webBrushColor === item.color ? 'border-white scale-110' : 'border-transparent hover:scale-105'
                                                                            }`}
                                                                            title={item.name}
                                                                        />
                                                                    ))}
                                                                </div>
                                                            </div>

                                                            {/* Toolbar buttons */}
                                                            <div className="grid grid-cols-2 gap-2">
                                                                <button 
                                                                    onClick={handleWebUndo}
                                                                    disabled={undoStack.length === 0}
                                                                    className={`py-2 px-3 rounded-xl font-semibold text-xs border transition-all ${
                                                                        undoStack.length === 0
                                                                            ? 'bg-zinc-850/40 border-zinc-900/10 text-zinc-650 cursor-not-allowed'
                                                                            : 'bg-zinc-800 hover:bg-zinc-700 border-zinc-700 text-white active:scale-95'
                                                                    }`}
