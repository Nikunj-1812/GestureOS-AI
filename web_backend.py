import os
import sys

# Suppress third-party logging / console spam (MediaPipe, TensorFlow, OpenCV)
os.environ['GLOG_minloglevel'] = '2'          # Suppress MediaPipe info logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'       # Suppress TensorFlow info/warning logs
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'       # Suppress OpenCV info/warning logs
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'    # Suppress OpenCV FFMPEG logs

import base64
import cv2
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import time
from pathlib import Path

from config.settings_manager import SettingsManager
from modules.camera import CameraStream
from modules.hand_detector import HandDetector
from modules.gesture_engine import GestureEngine
from modules.action_dispatcher import ActionDispatcher
from loguru import logger

app = FastAPI(title="GestureOS AI Web Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared system states
settings_manager = SettingsManager()
config = settings_manager.build_app_config("config/settings.yaml")

# Configure logger level from settings
logger.remove()
logger.add(sys.stderr, level=config.log_level)

camera_stream = None
hand_detector = HandDetector(
    max_hands=2,
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
    global camera_stream, camera_running
    if camera_stream is not None:
        try:
            camera_stream.stop()
        except Exception:
            pass
    try:
        camera_stream = CameraStream(
            index=config.camera_index,
            width=config.camera_width,
            height=config.camera_height,
            fps=config.camera_fps,
        ).start()
        camera_running = True
        logger.info(f"Camera stream started on index {config.camera_index}.")
        return True
    except Exception as e:
        camera_stream = None
        camera_running = False
        logger.error(f"Failed to start camera: {e}")
        return False

def stop_camera_stream():
    global camera_stream, camera_running
    camera_running = False
    if camera_stream is not None:
        try:
            camera_stream.stop()
        except Exception:
            pass
        camera_stream = None
        logger.info("Camera stream stopped.")

@app.on_event("startup")
async def startup_event():
    # Start the camera stream by default
    start_camera_stream()

@app.on_event("shutdown")
async def shutdown_event():
    stop_camera_stream()
    try:
        hand_detector.close()
    except Exception:
        pass

@app.post("/api/camera/start")
def api_start_camera():
    success = start_camera_stream()
    return {"status": "success" if success else "error"}

@app.post("/api/camera/stop")
def api_stop_camera():
    stop_camera_stream()
    return {"status": "success"}

@app.post("/api/camera/reset")
def api_reset_camera():
    global hand_detector
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
        "virtual_mouse_brightness_min_distance_px": getattr(state, 'virtual_mouse_brightness_min_distance_px', 30.0),
        "virtual_mouse_brightness_max_distance_px": getattr(state, 'virtual_mouse_brightness_max_distance_px', 250.0),
        "virtual_mouse_brightness_smoothing": getattr(state, 'virtual_mouse_brightness_smoothing', 0.15),
    }

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
        virtual_mouse.dead_zone = config.virtual_mouse_dead_zone
        virtual_mouse.smoothing = config.virtual_mouse_smoothing
        if hasattr(config, 'virtual_mouse_click_threshold'):
            virtual_mouse.click_threshold = config.virtual_mouse_click_threshold
        if hasattr(config, 'virtual_mouse_right_click_threshold'):
            virtual_mouse.right_click_threshold = config.virtual_mouse_right_click_threshold
        if hasattr(config, 'virtual_mouse_scroll_sensitivity'):
            virtual_mouse.scroll_sensitivity = config.virtual_mouse_scroll_sensitivity
        if hasattr(config, 'virtual_mouse_scroll_dead_zone'):
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
            
            loop_start = time.perf_counter()

            # Profiling steps
            t0 = time.perf_counter()
            
            # Optimize: Downscale processing resolution to 640w for ~4x performance boost
            h_orig, w_orig = frame.shape[:2]
            if w_orig > 640:
                scale = 640.0 / w_orig
                target_h = int(h_orig * scale)
                frame = cv2.resize(frame, (640, target_h), interpolation=cv2.INTER_LINEAR)

            if config.flip_horizontal:
                frame = cv2.flip(frame, 1)
                
            h, w = frame.shape[:2]
            t_resize = time.perf_counter() - t0

            # Run MediaPipe hand detection
            t_det_start = time.perf_counter()
            detected_hands, mp_results = hand_detector.detect(frame)
            t_detect = time.perf_counter() - t_det_start
            
            gesture_label = "unknown"
            gesture_confidence = 0.0
            
            t_pred_start = time.perf_counter()
            if detected_hands:
                primary_hand = detected_hands[0]
                if gesture_engine.is_loaded:
                    gesture_label, gesture_confidence = gesture_engine.predict(primary_hand)
                    if gesture_label != "unknown":
                        action_dispatcher.dispatch(gesture_label, virtual_mouse_active=virtual_mouse.enabled)
                else:
                    gesture_label = "No Model"
            else:
                gesture_engine.reset()
            t_predict = time.perf_counter() - t_pred_start

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
                "click_counter": vm_result.get("click_counter", 0) if vm_result else 0,
                "current_action": vm_result.get("current_action", "None") if vm_result else "None",
                # Phase 3.3 — Right Click telemetry
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
                "volume_level": vm_result.get("volume_level", 0) if vm_result else 0,
                "volume_distance": vm_result.get("volume_distance", 0.0) if vm_result else 0.0,
                # Phase 3.5 — Mode Manager & Brightness telemetry
                "active_mode": vm_result.get("active_mode", "CURSOR") if vm_result else "CURSOR",
                "brightness_mode": vm_result.get("brightness_mode", False) if vm_result else False,
                "brightness_level": vm_result.get("brightness_level", 0) if vm_result else 0,
                "brightness_distance": vm_result.get("brightness_distance", 0.0) if vm_result else 0.0,
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
        .glass-panel {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(59, 130, 246, 0.3);
            box-shadow: 0 10px 30px -10px rgba(59, 130, 246, 0.15);
        }
        .scrollbar-thin::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
            background: transparent;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 9999px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.25);
        }
    </style>
</head>
<body class="bg-[#080710] text-gray-200 overflow-hidden">
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect, useRef } = React;

        // Custom Inline SVG Icons to match Lucide React exactly
        const HandIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v5" />
                <path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v6" />
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
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
        );

        const LogOutIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
            </svg>
        );

        const PlayIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
        );

        const SquareIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
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
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <path d="m3 3 7.07 16.97 2.51-7.39 7.39-2.51L3 3z" />
                <path d="m13 13 6 6" />
            </svg>
        );

        const SunIcon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2" />
                <path d="M12 20v2" />
                <path d="m4.93 4.93 1.41 1.41" />
                <path d="m17.66 17.66 1.41 1.41" />
                <path d="M2 12h2" />
                <path d="M20 12h2" />
                <path d="m6.34 17.66-1.41 1.41" />
                <path d="m19.07 4.93-1.41 1.41" />
            </svg>
        );

        const Volume2Icon = (props) => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
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
            const [volumeDistance, setVolumeDistance] = useState(0.0);
            const [virtualMouseVolumeMinDistancePx, setVirtualMouseVolumeMinDistancePx] = useState(30.0);
            const [virtualMouseVolumeMaxDistancePx, setVirtualMouseVolumeMaxDistancePx] = useState(250.0);
            const [virtualMouseVolumeSmoothing, setVirtualMouseVolumeSmoothing] = useState(0.15);
            const prevVolumeLevelRef = useRef(-1);

            // Phase 3.5 — Mode Manager & Brightness Control
            const [activeMode, setActiveMode] = useState('CURSOR');
            const [brightnessMode, setBrightnessMode] = useState(false);
            const [brightnessLevel, setBrightnessLevel] = useState(0);
            const [brightnessDistance, setBrightnessDistance] = useState(0.0);
            const [virtualMouseBrightnessMinDistancePx, setVirtualMouseBrightnessMinDistancePx] = useState(30.0);
            const [virtualMouseBrightnessMaxDistancePx, setVirtualMouseBrightnessMaxDistancePx] = useState(250.0);
            const [virtualMouseBrightnessSmoothing, setVirtualMouseBrightnessSmoothing] = useState(0.15);
            const prevBrightnessLevelRef = useRef(-1);
            const prevActiveModeRef = useRef('CURSOR');

            // Switches State
            const [showLandmarks, setShowLandmarks] = useState(true);
            const [showConnections, setShowConnections] = useState(true);
            const [showBoundingBox, setShowBoundingBox] = useState(true);
            const [showFingerStates, setShowFingerStates] = useState(true);
            const [showDistanceMeter, setShowDistanceMeter] = useState(true);
            const [showDebugPanel, setShowDebugPanel] = useState(true);
            const [showHud, setShowHud] = useState(true);

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
                            setClickCounter(data.click_counter || 0);
                            setCurrentAction(data.current_action || 'None');
                            // Phase 3.3 — Right Click
                            const prevRC = prevRightClickStatusRef.current;
                            const newRC = data.right_click_status || 'OPEN';
                            setRightClickStatus(newRC);
                            setRightClickCounter(data.right_click_counter || 0);
                            setRightPinchDistance(data.right_pinch_distance || 0.0);
                            // Log right-click event on transition into RIGHT_CLICK
                            if (newRC === 'RIGHT_CLICK' && prevRC !== 'RIGHT_CLICK') {
                                const timeString = new Date().toLocaleTimeString();
                                eventIdCounterRef.current += 1;
                                const rcEvent = {
                                    id: `${Date.now()}-${eventIdCounterRef.current}`,
                                    timestamp: timeString,
                                    gesture: 'Right Click',
                                    confidence: 1.0,
                                    action: `Right Click triggered | gesture=thumb_middle_pinch | dist=${(data.right_pinch_distance || 0).toFixed(4)}`
                                };
                                setEvents(prev => [rcEvent, ...prev].slice(0, 50));
                            }
                            prevRightClickStatusRef.current = newRC;
                            // Phase 3.4 — Scroll
                            const prevSM = prevScrollModeRef.current;
                            const newSM = data.scroll_mode || false;
                            setScrollMode(newSM);
                            setScrollDirection(data.scroll_direction || 'NONE');
                            setScrollSpeed(data.scroll_speed || 0.0);
                            setScrollCounter(data.scroll_counter || 0);
                            // Log scroll start/stop transitions
                            if (newSM && !prevSM) {
                                const timeString = new Date().toLocaleTimeString();
                                eventIdCounterRef.current += 1;
                                setEvents(prev => [{
                                    id: `${Date.now()}-${eventIdCounterRef.current}`,
                                    timestamp: timeString,
                                    gesture: 'Scroll Start',
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

                            // Phase 3.4 — Volume
                            const newVM = data.volume_mode || false;
                            setVolumeMode(newVM);
                            setVolumeLevel(data.volume_level || 0);
                            setVolumeDistance(data.volume_distance || 0.0);
                            // Log volume changes on integer level change
                            if (newVM && data.volume_level !== prevVolumeLevelRef.current) {
                                if (data.volume_level !== undefined) {
                                    const timeString = new Date().toLocaleTimeString();
                                    eventIdCounterRef.current += 1;
                                    const volumeEvent = {
                                        id: `${Date.now()}-${eventIdCounterRef.current}`,
                                        timestamp: timeString,
                                        gesture: 'Volume',
                                        confidence: 1.0,
                                        action: `[VOLUME] ${data.volume_level}% (Distance: ${(data.volume_distance || 0).toFixed(1)}px)`
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
                                        confidence: 1.0,
                                        action: `[BRIGHTNESS] ${data.brightness_level}% (Distance: ${(data.brightness_distance || 0).toFixed(1)}px)`
                                    };
                                    setEvents(prev => [brightnessEvent, ...prev].slice(0, 50));
                                    prevBrightnessLevelRef.current = data.brightness_level;
                                }
                            } else if (!newBM) {
                                prevBrightnessLevelRef.current = -1;
                            }

                            // Phase 3.5 — Mode Manager
                            const newAM = data.active_mode || 'CURSOR';
                            setActiveMode(newAM);
                            if (newAM !== prevActiveModeRef.current) {
                                const timeString = new Date().toLocaleTimeString();
                                eventIdCounterRef.current += 1;
                                const modeEvent = {
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
                        logSystemEvent("Camera stream started.");
                    }
                } catch (err) {
                    console.error('Error starting camera:', err);
                    logSystemEvent("Failed to start camera.");
                } finally {
                    setIsCameraLoading(false);
                }
            };

            const handleStopCamera = async () => {
                setIsCameraLoading(true);
                logSystemEvent("Camera stream stop requested.");
                try {
                    await fetch('/api/camera/stop', { method: 'POST' });
                    setCameraStatus('Disconnected');
                    setFrame(null);
                    setFps(0);
                    setHands(0);
                    setGesture('None');
                    setConfidence(0);
                    logSystemEvent("Camera stream stopped.");
                } catch (err) {
                    console.error('Error stopping camera:', err);
                    logSystemEvent("Failed to stop camera.");
                } finally {
                    setIsCameraLoading(false);
                }
            };

            const handleResetTracking = async () => {
                setIsResetting(true);
                logSystemEvent("Reset tracking requested.");
                try {
                    await fetch('/api/camera/reset', { method: 'POST' });
                    setEvents([]);
                    prevGestureRef.current = 'None';
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
                                    { id: 'analytics', name: 'Real-time Metrics', icon: TrendingUpIcon },
                                    { id: 'settings', name: 'System Settings', icon: SettingsIcon }
                                ].map((item) => {
                                    const Icon = item.icon;
                                    const isActive = activeMenu === item.id;
                                    return (
                                        <button
                                            key={item.id}
                                            onClick={() => {
                                                setActiveMenu(item.id);
                                                logSystemEvent(`Navigated to page: ${item.name}`);
                                            }}
                                            className={`w-full flex items-center justify-between px-4 py-3.5 rounded-xl transition-all duration-300 group ${
                                                isActive 
                                                    ? 'bg-blue-600/20 border border-blue-500/30 text-white font-medium shadow-md shadow-blue-500/5' 
                                                    : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                                            }`}
                                        >
                                            <div className="flex items-center gap-3.5">
                                                <Icon className={`w-5 h-5 transition-transform duration-300 group-hover:scale-110 ${
                                                    isActive ? 'text-accent-blue' : 'text-gray-400 group-hover:text-white'
                                                }`} />
                                                <span className="text-sm tracking-wide">{item.name}</span>
                                            </div>
                                            <ChevronRightIcon className={`w-4 h-4 opacity-0 transition-all duration-300 -translate-x-2 ${
                                                isActive ? 'opacity-100 translate-x-0 text-accent-blue' : 'group-hover:opacity-50 group-hover:translate-x-0'
                                            }`} />
                                        </button>
                                    );
                                })}
                            </nav>
                        </div>

                        {/* Sidebar Footer status */}
                        <div className="p-4 border-t border-glass-border">
                            <div className="glass-card rounded-xl p-4 flex flex-col gap-3">
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-gray-400 font-medium">Core Pipeline:</span>
                                    <span className="text-accent-green flex items-center gap-1.5 font-semibold">
                                        <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-ping" />
                                        Active
                                    </span>
                                </div>
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-gray-400 font-medium">WS Backend:</span>
                                    <span className={`flex items-center gap-1.5 font-semibold ${
                                        socketStatus === 'connected' ? 'text-accent-blue' : 'text-amber-500 animate-pulse'
                                    }`}>
                                        <span className={`w-1.5 h-1.5 rounded-full ${
                                            socketStatus === 'connected' ? 'bg-accent-blue' : 'bg-amber-500'
                                        }`} />
                                        {socketStatus === 'connected' ? 'Connected' : socketStatus === 'connecting' ? 'Connecting...' : 'Offline'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </aside>

                    {/* Main Content Area */}
                    <main className="flex-1 flex flex-col h-full overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-950/15 via-[#080710] to-[#080710]">
                        
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

                                <span className="w-px h-6 bg-glass-border hidden md:inline-block" />

                                <button className="p-2.5 rounded-xl glass-card text-gray-400 hover:text-white relative group">
                                    <BellIcon className="w-5 h-5" />
                                    <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-blue-500 rounded-full border-2 border-background" />
                                </button>

                                <button className="p-2.5 rounded-xl glass-card text-gray-400 hover:text-white group">
                                    <SettingsIcon className="w-5 h-5 transition-transform duration-300 group-hover:rotate-45" />
                                </button>

                                <div className="flex items-center gap-3 px-3 py-1.5 rounded-xl glass-card border border-glass-border text-left select-none">
                                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                                        <UserIcon className="w-4 h-4" />
                                    </div>
                                    <div className="hidden sm:block">
                                        <p className="text-xs font-semibold text-white">Operator</p>
                                        <p className="text-[10px] text-gray-400">Admin Role</p>
                                    </div>
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

                                            {/* Hands Detected Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 text-accent-purple">
                                                    <HandIcon className="w-6 h-6" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Hands Tracked</p>
                                                    <p className="text-2xl font-bold text-white mt-1 font-mono tracking-tight">
                                                        {hands}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Current Gesture Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className="p-3 bg-violet-500/10 rounded-xl border border-violet-500/20 text-purple-400">
                                                    <SparklesIcon className="w-6 h-6" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Current Gesture</p>
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
                                                <div>
                                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Volume Level</p>
                                                    <p className="text-2xl font-bold text-white mt-1 font-mono tracking-tight">
                                                        {volumeMode ? `${volumeLevel}%` : 'IDLE'}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Brightness Card */}
                                            <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                                                <div className={`p-3 rounded-xl border transition-colors ${
                                                    brightnessMode ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400 animate-pulse' : 'bg-zinc-500/10 border-zinc-500/20 text-gray-400'
                                                }`}>
                                                    <SunIcon className="w-6 h-6" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Brightness</p>
                                                    <p className="text-2xl font-bold text-white mt-1 font-mono tracking-tight">
                                                        {brightnessMode ? `${brightnessLevel}%` : 'IDLE'}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Layout Main Grid */}
                                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                            
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
                                                    </div>

                                                    {/* Centered Camera Stream with responsive aspect ratio */}
                                                    <div className="flex-1 flex items-center justify-center bg-black/40 rounded-xl overflow-hidden border border-glass-border relative mt-3">
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
                                                                <p className="text-xs text-gray-400 leading-relaxed">
                                                                    To analyze hand geometry and process shortcuts, please launch the camera using the Quick Actions panel below.
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Action & Log Cards (1 Column) */}
                                            <div className="flex flex-col gap-6">
                                                {/* Quick Actions Panel */}
                                                <div className="glass-card rounded-2xl p-5 flex flex-col justify-between">
                                                    <div>
                                                        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                                                            <SlidersIcon className="w-4 h-4 text-accent-purple" />
                                                            Quick Actions
                                                        </h3>
                                                        <p className="text-xs text-gray-500 mt-1 mb-4">Immediate system state triggers.</p>
                                                    </div>
                                                    
                                                    <div className="space-y-3">
                                                        <button
                                                            onClick={handleStartCamera}
                                                            disabled={cameraStatus === 'Connected' || isCameraLoading}
                                                            className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-zinc-800 disabled:to-zinc-800 disabled:border-zinc-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/10 border border-blue-500/30"
                                                        >
                                                            <PlayIcon className="w-4 h-4 fill-white" />
                                                            Start Camera
                                                        </button>
                                                        
                                                        <button
                                                            onClick={handleStopCamera}
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
                                                            Reset Tracking
                                                        </button>
                                                    </div>
                                                </div>

                                                {/* Display Settings Switches */}
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
                                                            { id: 'show_distance_meter', label: 'Distance Meter', value: showDistanceMeter, setter: setShowDistanceMeter },
                                                            { id: 'show_debug_panel', label: 'Debug Panel', value: showDebugPanel, setter: setShowDebugPanel },
                                                            { id: 'show_hud', label: 'HUD Overlay', value: showHud, setter: setShowHud },
                                                        ].map(item => (
                                                            <label key={item.id} className="flex items-center gap-2.5 cursor-pointer text-gray-300 hover:text-white select-none">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={item.value}
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
                                                        <p className="text-xs text-gray-500 mt-1 mb-4">Real-time prediction event stream.</p>
                                                    </div>

                                                    <div className="flex-1 overflow-y-auto bg-black/60 rounded-xl border border-glass-border p-3 font-mono text-[11px] leading-relaxed scrollbar-thin text-blue-400/90 h-[120px]">
                                                        {events.length === 0 ? (
                                                            <div className="text-gray-600 flex items-center justify-center h-full">
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
                                                                            )}
                                                                        </div>
                                                                        <div className="text-gray-400 text-[10px]">
                                                                            {evt.action}
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}
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
                                                <span className={`px-4 py-2 rounded-full text-xs font-semibold border ${
                                                    virtualMouseEnabled 
                                                        ? 'bg-emerald-500/10 border-emerald-500/20 text-accent-green' 
                                                        : 'bg-zinc-500/10 border-zinc-500/20 text-gray-400'
                                                }`}>
                                                    {virtualMouseEnabled ? 'Active' : 'Inactive'}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Two-Column Main Content Layout */}
                                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                            {/* Left: Camera Feed Preview (2 Columns) */}
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
                                                    </div>

                                                    {/* Centered Camera Stream */}
                                                    <div className="flex-1 flex items-center justify-center bg-black/40 rounded-xl overflow-hidden border border-glass-border relative mt-3">
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
                                                                <p className="text-xs text-gray-400 leading-relaxed">
                                                                    To analyze hand geometry and process mouse tracking, please launch the camera using the Quick Actions panel or back on the Dashboard.
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Right: Telemetry & Controls Panel (1 Column) */}
                                            <div className="flex flex-col gap-6">
                                                {/* Telemetry Dashboard Card */}
                                                <div className="glass-card rounded-2xl p-5 flex flex-col justify-between">
                                                    <div>
                                                        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                                                            <ActivityIcon className="w-4 h-4 text-accent-blue" />
                                                            Telemetry Dashboard
                                                        </h3>
                                                        <p className="text-xs text-gray-500 mt-1 mb-4">Real-time coordinates and performance.</p>
                                                    </div>

                                                    <div className="space-y-4">
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Cursor Coordinates</span>
                                                            <span className="font-mono font-bold text-white">
                                                                {trackingState === 'Tracking' ? `X: ${cursorX} , Y: ${cursorY}` : '-- , --'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Tracking State</span>
                                                            <span className={`font-semibold ${
                                                                trackingState === 'Tracking' ? 'text-accent-green' : trackingState === 'Disabled' ? 'text-gray-400' : 'text-rose-400'
                                                            }`}>
                                                                {trackingState}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Stream FPS</span>
                                                            <span className="font-mono font-bold text-white">
                                                                {fps > 0 ? `${fps.toFixed(1)} FPS` : '-- FPS'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Current Action</span>
                                                            <span className={`font-semibold ${
                                                                currentAction === 'Left Click' ? 'text-accent-green' :
                                                                currentAction === 'Right Click' ? 'text-orange-400' : 'text-white'
                                                            }`}>
                                                                {currentAction}
                                                            </span>
                                                        </div>

                                                        {/* Separator */}
                                                        <div className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold pt-1">Left Click (Index + Thumb)</div>

                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Click Status</span>
                                                            <span className={`font-semibold ${
                                                                clickStatus === 'LEFT_CLICK' || clickStatus === 'PINCH' ? 'text-accent-green' : clickStatus === 'RELEASE' ? 'text-accent-blue' : 'text-white'
                                                            }`}>
                                                                {clickStatus}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Pinch Distance</span>
                                                            <span className="font-mono font-bold text-white">
                                                                {pinchDistance.toFixed(4)}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Click Counter</span>
                                                            <span className="font-mono font-bold text-accent-blue">
                                                                {clickCounter}
                                                            </span>
                                                        </div>

                                                        {/* Phase 3.3 Right-Click Section */}
                                                        <div className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold pt-1">Right Click (Middle + Thumb)</div>

                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Right Click Status</span>
                                                            <span className={`font-semibold ${
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
                                                            <span className="text-gray-400">Scroll Direction</span>
                                                            <span className={`font-semibold ${
                                                                scrollDirection === 'UP' ? 'text-teal-400' :
                                                                scrollDirection === 'DOWN' ? 'text-amber-400' : 'text-gray-500'
                                                            }`}>
                                                                {scrollDirection === 'UP' ? '▲ UP' : scrollDirection === 'DOWN' ? '▼ DOWN' : '—'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Scroll Speed</span>
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
                                                            <span className={`font-semibold ${
                                                                volumeMode ? 'text-purple-400 animate-pulse' : 'text-gray-400'
                                                            }`}>
                                                                {volumeMode ? 'ACTIVE' : 'INACTIVE'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Current Volume Level</span>
                                                            <span className="font-mono font-bold text-purple-400">
                                                                {volumeLevel}%
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Hand Distance</span>
                                                            <span className="font-mono font-bold text-white">
                                                                {volumeMode ? `${volumeDistance.toFixed(1)} px` : '-- px'}
                                                            </span>
                                                        </div>

                                                        {/* Phase 3.5 Brightness Section */}
                                                        <div className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold pt-1">Brightness Control (Thumb+Index+Pinky Up)</div>

                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Brightness Mode Status</span>
                                                            <span className={`font-semibold ${
                                                                brightnessMode ? 'text-cyan-400 animate-pulse' : 'text-gray-400'
                                                            }`}>
                                                                {brightnessMode ? 'ACTIVE' : 'INACTIVE'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                                                            <span className="text-gray-400">Current Brightness</span>
                                                            <span className="font-mono font-bold text-cyan-400">
                                                                {brightnessLevel}%
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between items-center text-sm">
                                                            <span className="text-gray-400">Hand Distance</span>
                                                            <span className="font-mono font-bold text-white">
                                                                {brightnessMode ? `${brightnessDistance.toFixed(1)} px` : '-- px'}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Tracking Settings Card */}
                                                <div className="glass-card rounded-2xl p-5">
                                                    <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                                                        <SlidersIcon className="w-4 h-4 text-accent-purple" />
                                                        Tracking Settings
                                                    </h3>
                                                    <p className="text-xs text-gray-500 mt-1 mb-4">Configure virtual mouse parameters.</p>

                                                    <div className="space-y-5">
                                                        {/* Enable Toggle Switch */}
                                                        <label className="flex items-center justify-between cursor-pointer group">
                                                            <span className="text-sm font-semibold text-gray-300 group-hover:text-white">Enable Virtual Mouse</span>
                                                            <div className="relative">
                                                                <input 
                                                                    type="checkbox" 
                                                                    checked={virtualMouseEnabled} 
                                                                    onChange={(e) => {
                                                                        const checked = e.target.checked;
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
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Dead Zone Padding</span>
                                                                <span className="text-white font-mono">{Math.round(virtualMouseDeadZone * 100)}%</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.05" 
                                                                max="0.30" 
                                                                step="0.01"
                                                                value={virtualMouseDeadZone} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseDeadZone(val);
                                                                    updateSetting('virtual_mouse_dead_zone', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

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
                                                                    setVirtualMouseSmoothing(val);
                                                                    updateSetting('virtual_mouse_smoothing', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Click Threshold Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Click Threshold</span>
                                                                <span className="text-white font-mono">{virtualMouseClickThreshold.toFixed(3)}</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.01" 
                                                                max="0.15" 
                                                                step="0.005"
                                                                value={virtualMouseClickThreshold} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseClickThreshold(val);
                                                                    updateSetting('virtual_mouse_click_threshold', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Volume Min Distance Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
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

                                                        {/* Brightness Min Distance Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Brightness Min Distance</span>
                                                                <span className="text-white font-mono">{virtualMouseBrightnessMinDistancePx.toFixed(0)} px</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="10" 
                                                                max="100" 
                                                                step="5"
                                                                value={virtualMouseBrightnessMinDistancePx} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseBrightnessMinDistancePx(val);
                                                                    updateSetting('virtual_mouse_brightness_min_distance_px', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Brightness Max Distance Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Brightness Max Distance</span>
                                                                <span className="text-white font-mono">{virtualMouseBrightnessMaxDistancePx.toFixed(0)} px</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="150" 
                                                                max="400" 
                                                                step="10"
                                                                value={virtualMouseBrightnessMaxDistancePx} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseBrightnessMaxDistancePx(val);
                                                                    updateSetting('virtual_mouse_brightness_max_distance_px', val);
                                                                }}
                                                                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                                                            />
                                                        </div>

                                                        {/* Brightness Smoothing Slider */}
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-xs">
                                                                <span className="text-gray-400">Brightness Smoothing</span>
                                                                <span className="text-white font-mono">{virtualMouseBrightnessSmoothing.toFixed(2)}</span>
                                                            </div>
                                                            <input 
                                                                type="range" 
                                                                min="0.05" 
                                                                max="0.50" 
                                                                step="0.01"
                                                                value={virtualMouseBrightnessSmoothing} 
                                                                onChange={(e) => {
                                                                    const val = parseFloat(e.target.value);
                                                                    setVirtualMouseBrightnessSmoothing(val);
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
