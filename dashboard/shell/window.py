"""
GestureOS AI — Dashboard Window
================================
Main CustomTkinter shell: header, sidebar, page host, footer.

PIPELINE CONNECTION (ARCH-002 fix)
-----------------------------------
The gesture recognition pipeline is now wired into the camera poll
loop:

    CameraStream.read()
        └─▶ HandDetector.detect(frame)
                └─▶ GestureEngine.predict(hand)
                        └─▶ ActionDispatcher.dispatch(gesture)
                                └─▶ Footer status updated live

The pipeline runs on every camera frame that arrives on the main
thread via the self.after() polling mechanism.  This keeps it safely
on the Tkinter main thread (no cross-thread widget updates).

GestureEngine and HandDetector are created lazily: if the ONNX model
file does not exist yet (pre-training), the pipeline runs in detection-
only mode — landmarks and hand status still update; gesture label and
confidence remain "No Model".

ADDITIONAL FIXES IN THIS FILE
------------------------------
- BUG-001 : duplicate _show_page logic refactored into _instantiate_page()
- RISK-005: _nav_history capped at MAX_HISTORY entries
- RISK-002: Q-key shortcut skipped when a text Entry widget has focus
"""

from __future__ import annotations

import os
import sys

# Suppress third-party logging / console spam (MediaPipe, TensorFlow, OpenCV)
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'

import time
from pathlib import Path

import cv2
import customtkinter as ctk
from loguru import logger

from config.settings_manager import SettingsManager, SettingsState
from dashboard.components.footer import FooterBar
from dashboard.components.header import TopHeader
from dashboard.components.help_dialog import HelpDialog
from dashboard.components.sidebar import SidebarNav
from dashboard.pages.dashboard_page import DashboardPage
from dashboard.shell.page_registry import PAGE_CLASSES, PAGE_TITLES
from dashboard.theme import COLORS, SIZES
from modules.camera import CameraStream
from modules.hand_detector import HandDetector, HandLandmarks
from modules.gesture_engine import GestureEngine
from modules.action_dispatcher import ActionDispatcher
from modules.virtual_mouse import VirtualMouse

# Maximum navigation history kept in memory
_MAX_HISTORY = 20


class GestureOSApp(ctk.CTk):
    """
    Root dashboard window.

    Wires the fixed chrome (header / sidebar / footer) and swaps page
    widgets into the main content region.  Also runs the gesture
    recognition pipeline on every camera frame.
    """

    def __init__(self) -> None:
        ctk.set_default_color_theme("blue")
        super().__init__()

        # ── Settings & config ─────────────────────────────────────────
        self._settings_manager = SettingsManager()
        self._config = self._settings_manager.build_app_config(
            "config/settings.yaml"
        )
        ctk.set_appearance_mode(self._config.theme)

        # Configure logger level from settings
        logger.remove()
        logger.add(sys.stderr, level=self._config.log_level)

        # ── Window chrome ─────────────────────────────────────────────
        self.title(self._config.window_title)
        self.geometry(f"{SIZES['window_w']}x{SIZES['window_h']}")
        self.minsize(1024, 640)
        self.configure(fg_color=COLORS["base"])
        self._centre_window(SIZES["window_w"], SIZES["window_h"])
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

        # ── State ─────────────────────────────────────────────────────
        self._current_page: ctk.CTkBaseClass | None = None
        self._current_key:  str  = "dashboard"
        self._nav_history:  list[str] = []   # capped at _MAX_HISTORY
        self._log_history:  list[str] = ["[INFO] System initialized. Waiting for camera stream."]

        # ── Camera ────────────────────────────────────────────────────
        self._camera_stream: CameraStream | None = None
        self._last_fps_tick  = time.perf_counter()
        self._fps_smooth     = 0.0
        self._last_frame_id  = -1

        # ── Gesture pipeline components ───────────────────────────────
        # HandDetector is always created (MediaPipe is always available).
        # We decouple detector confidence (set to 0.5) from model confidence for stable tracking.
        self._hand_detector = HandDetector(
            max_hands=2,
            detection_confidence=0.5,
            tracking_confidence=0.5,
        )

        # GestureEngine loads the ONNX model if present; otherwise runs
        # in detection-only mode (is_loaded == False).
        model_path = str(
            Path(self._config.model_dir) / self._config.default_model
        )
        self._gesture_engine = GestureEngine(
            model_path=model_path,
            confidence_threshold=self._config.confidence_threshold,
            smoothing_frames=self._config.smoothing_frames,
        )
        self._virtual_mouse = VirtualMouse(
            enabled=self._config.virtual_mouse_enabled,
            sensitivity=self._config.virtual_mouse_sensitivity,
            dead_zone=self._config.virtual_mouse_dead_zone,
            smoothing=self._config.virtual_mouse_smoothing,
            click_threshold=getattr(self._config, 'virtual_mouse_click_threshold', 0.05),
        )

        # ActionDispatcher fires OS-level actions.
        self._action_dispatcher = ActionDispatcher(cooldown_ms=800)

        # ── Build UI ──────────────────────────────────────────────────
        self._build_layout()
        self._show_page("dashboard")
        self._start_camera()
        self.after(15, self._poll_camera)
        self._bind_shortcuts()

    # ================================================================== #
    # Layout                                                               #
    # ================================================================== #

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._header = TopHeader(self)
        self._header.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self._sidebar = SidebarNav(self, on_navigate=self._show_page)
        self._sidebar.grid(row=1, column=0, sticky="nsew")

        self._content_frame = ctk.CTkFrame(
            self, fg_color=COLORS["base"], corner_radius=0
        )
        self._content_frame.grid(row=1, column=1, sticky="nsew")
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=1)

        self._footer = FooterBar(self)
        self._footer.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self._footer.set_fps(0)
        self._footer.set_camera_status("Disconnected")
        self._footer.set_hand_status("Not Detected")
        self._footer.set_model_status(
            "Loaded" if self._gesture_engine.is_loaded else "Not Loaded"
        )
        self._footer.set_gesture("None", 0.0)

    # ================================================================== #
    # Camera                                                               #
    # ================================================================== #

    def _start_camera(self) -> None:
        if self._camera_stream is not None:
            try:
                self._camera_stream.stop()
            except Exception:
                pass

        try:
            self._camera_stream = CameraStream(
                index=self._config.camera_index,
                width=self._config.camera_width,
                height=self._config.camera_height,
                fps=self._config.camera_fps,
            ).start()
            self._footer.set_camera_status("Starting")
            self.log_event("Camera stream started.")
        except Exception as exc:
            self._camera_stream = None
            self._footer.set_camera_status("Disconnected")
            self.log_event(f"Failed to start camera: {exc}")

    def _restart_camera(self) -> None:
        self._start_camera()

    def _stop_camera(self) -> None:
        if self._camera_stream is not None:
            try:
                self._camera_stream.stop()
            except Exception:
                pass
            self._camera_stream = None
            self._footer.set_camera_status("Disconnected")
            self.log_event("Camera stream stopped.")
            if isinstance(self._current_page, DashboardPage):
                self._current_page.clear_camera_frame()

    def _reset_tracking(self) -> None:
        self._gesture_engine.reset()
        try:
            self._hand_detector.close()
        except Exception:
            pass
        self._hand_detector = HandDetector(
            max_hands=2,
            detection_confidence=0.5,
            tracking_confidence=0.5,
        )
        self.log_event("Tracking reset.")

    # ================================================================== #
    # Camera poll — runs the full gesture pipeline                         #
    # ================================================================== #

    def _poll_camera(self) -> None:
        """
        Called via self.after() on the main thread at roughly camera fps.

        Pipeline on each frame:
            1. Read frame from CameraStream
            2. HandDetector.detect() → list[HandLandmarks] + mp_results
            3. GestureEngine.predict() per hand (if model loaded)
            4. ActionDispatcher.dispatch() for dominant hand gesture
            5. Update footer status labels
            6. Forward raw frame to DashboardPage camera preview
        """
        if self._camera_stream is None:
            self.after(100, self._poll_camera)
            return

        current_frame_id = self._camera_stream.frame_id
        if current_frame_id == self._last_frame_id:
            self.after(5, self._poll_camera)
            return

        frame = self._camera_stream.read()
        if frame is None:
            self._footer.set_camera_status("Starting")
            self.after(15, self._poll_camera)
            return

        self._last_frame_id = current_frame_id
        start_time = time.perf_counter()

        # Optimize: Downscale processing resolution to 640w for ~4x performance boost
        h, w = frame.shape[:2]
        if w > 640:
            scale = 640.0 / w
            target_h = int(h * scale)
            frame = cv2.resize(frame, (640, target_h), interpolation=cv2.INTER_LINEAR)

        # ── Flip ─────────────────────────────────────────────────────
        if self._config.flip_horizontal:
            frame = cv2.flip(frame, 1)

        if not hasattr(self, "_debug_frame_count"):
            self._debug_frame_count = 0
        if not hasattr(self, "_last_gesture"):
            self._last_gesture = "unknown"

        # ── Step 2: Hand detection ────────────────────────────────────
        detected_hands, mp_results = self._hand_detector.detect(frame)

        # ── Step 3 & 4: Gesture recognition + action dispatch ─────────
        gesture_label      = "unknown"
        gesture_confidence = 0.0

        if detected_hands:
            # Use the first (most prominent) detected hand for dispatch
            primary_hand = detected_hands[0]

            if self._gesture_engine.is_loaded:
                gesture_label, gesture_confidence = (
                    self._gesture_engine.predict(primary_hand)
                )
                # Dispatch OS action if a known gesture is recognised
                if gesture_label != "unknown":
                    self._action_dispatcher.dispatch(gesture_label)
            else:
                gesture_label = "No Model"
        else:
            # No hands — reset smoothing history
            self._gesture_engine.reset()

        if gesture_label != self._last_gesture:
            logger.info(f"Gesture changed: '{self._last_gesture}' -> '{gesture_label}'")
            self._last_gesture = gesture_label

        # ── Step 5: Update footer status ─────────────────────────────
        if detected_hands:
            hand_count = len(detected_hands)
            hand_label = detected_hands[0].handedness
            self._footer.set_hand_status(
                f"Detected · {hand_label} · {hand_count} hand"
                f"{'s' if hand_count > 1 else ''}"
            )
        else:
            self._footer.set_hand_status("Not Detected")

        # Update model status in footer
        model_status = "Loaded" if self._gesture_engine.is_loaded else "Not Loaded"
        self._footer.set_model_status(model_status)

        # Update gesture status in footer
        self._footer.set_gesture(gesture_label, gesture_confidence)

        # ── FPS calculation ───────────────────────────────────────────
        now         = time.perf_counter()
        delta       = max(now - self._last_fps_tick, 1e-6)
        instant_fps = 1.0 / delta
        self._fps_smooth = (
            instant_fps
            if self._fps_smooth == 0
            else (self._fps_smooth * 0.85 + instant_fps * 0.15)
        )
        self._last_fps_tick = now

        self._footer.set_fps(self._fps_smooth)
        self._footer.set_camera_status("Connected")

        # ── Step 6: Virtual Mouse & Forward frame to active page preview ───────────
        vm_result = None
        if self._virtual_mouse.enabled:
            if detected_hands:
                vm_result = self._virtual_mouse.process_hand(detected_hands[0])
            else:
                vm_result = self._virtual_mouse.process_hand(None)
        else:
            self._virtual_mouse.reset()

        # Extract cursor fields for page forwarding
        cursor_x = vm_result["cursor_x"] if vm_result else 0
        cursor_y = vm_result["cursor_y"] if vm_result else 0
        tracking_state = vm_result["tracking_state"] if vm_result else "Disabled"

        if isinstance(self._current_page, (DashboardPage, VirtualMousePage)):
            from modules.visualizer import draw_visuals
            frame = draw_visuals(
                frame=frame,
                detected_hands=detected_hands,
                mp_results=mp_results,
                config=self._config,
                fps=self._fps_smooth,
                gesture=gesture_label,
                confidence=gesture_confidence,
                click_state=vm_result
            )
            if isinstance(self._current_page, DashboardPage):
                self._current_page.set_camera_frame(
                    frame,
                    fps=self._fps_smooth,
                    gesture=gesture_label,
                    confidence=gesture_confidence,
                    hands_detected=len(detected_hands)
                )
            elif isinstance(self._current_page, VirtualMousePage):
                self._current_page.set_camera_frame(
                    frame,
                    fps=self._fps_smooth,
                    gesture=gesture_label,
                    confidence=gesture_confidence,
                    hands_detected=len(detected_hands),
                    cursor_x=cursor_x,
                    cursor_y=cursor_y,
                    tracking_state=tracking_state,
                    click_status=vm_result.get("click_status", "OPEN") if vm_result else "OPEN",
                    click_counter=vm_result.get("click_counter", 0) if vm_result else 0,
                    pinch_distance=vm_result.get("pinch_distance", 0.0) if vm_result else 0.0,
                    current_action=vm_result.get("current_action", "None") if vm_result else "None",
                )

        # Schedule next poll
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        interval_ms = max(1, int(1000 / max(self._config.camera_fps, 1)) - elapsed_ms)
        self.after(interval_ms, self._poll_camera)

    # ================================================================== #
    # Settings                                                             #
    # ================================================================== #

    def _apply_settings(self, settings: SettingsState) -> None:
        camera_changed = settings.camera_index != self._config.camera_index
        fps_changed    = settings.fps_limit    != self._config.camera_fps

        self._config.camera_index = settings.camera_index
        self._config.camera_fps   = settings.fps_limit
        self._config.theme        = settings.theme
        
        self._config.show_landmarks = settings.show_landmarks
        self._config.show_connections = settings.show_connections
        self._config.show_bounding_box = settings.show_bounding_box
        self._config.show_finger_states = settings.show_finger_states
        self._config.show_distance_meter = settings.show_distance_meter
        self._config.show_debug_panel = settings.show_debug_panel
        self._config.show_hud = settings.show_hud

        self._config.virtual_mouse_enabled = settings.virtual_mouse_enabled
        self._config.virtual_mouse_sensitivity = settings.virtual_mouse_sensitivity
        self._config.virtual_mouse_dead_zone = settings.virtual_mouse_dead_zone
        self._config.virtual_mouse_smoothing = settings.virtual_mouse_smoothing

        self._virtual_mouse.enabled = settings.virtual_mouse_enabled
        self._virtual_mouse.sensitivity = settings.virtual_mouse_sensitivity
        self._virtual_mouse.dead_zone = settings.virtual_mouse_dead_zone
        self._virtual_mouse.smoothing = settings.virtual_mouse_smoothing
        if hasattr(settings, 'virtual_mouse_click_threshold'):
            self._virtual_mouse.click_threshold = settings.virtual_mouse_click_threshold

        ctk.set_appearance_mode(settings.theme)

        if camera_changed or fps_changed:
            self._restart_camera()

    def log_event(self, message: str) -> None:
        """Appends a timestamped message to the centralized log history."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        self._log_history.append(formatted)
        
        # Limit history size to 200 items to avoid memory growth
        if len(self._log_history) > 200:
            self._log_history.pop(0)

        # If dashboard page is currently active, update its textbox
        if isinstance(self._current_page, DashboardPage):
            self._current_page.append_log(formatted)

    # ================================================================== #
    # Page navigation                                                       #
    # ================================================================== #

    def _instantiate_page(self, key: str) -> ctk.CTkBaseClass:
        """
        Factory: create the correct page widget for `key`.

        Centralises all per-page constructor kwargs in one place,
        fixing DUP-003 (the same if/elif chain was duplicated in
        _show_page and _show_page_no_history).
        """
        page_class = PAGE_CLASSES[key]

        if key == "dashboard":
            return DashboardPage(
                self._content_frame,
                on_navigate=self._show_page,
                on_start_camera=self._start_camera,
                on_stop_camera=self._stop_camera,
                on_reset_tracking=self._reset_tracking,
                settings_manager=self._settings_manager,
                on_settings_changed=self._apply_settings,
            )
        if key == "virtual_mouse":
            return page_class(
                self._content_frame,
                on_navigate=self._show_page,
                settings_manager=self._settings_manager,
                on_settings_changed=self._apply_settings,
            )
        if key == "virtual_keyboard":
            return page_class(
                self._content_frame, on_navigate=self._show_page
            )
        if key == "settings":
            return page_class(
                self._content_frame,
                settings_manager=self._settings_manager,
                on_settings_changed=self._apply_settings,
            )
        return page_class(self._content_frame)

    def _swap_page(self, key: str) -> None:
        """Tear down the current page and mount the new one."""
        title = PAGE_TITLES.get(key, key.replace("_", " ").title())
        self.log_event(f"Navigated to page: {title}")

        if self._current_page is not None:
            try:
                self._current_page.on_leave()
            except Exception:
                pass
            self._current_page.destroy()
            self._current_page = None

        page = self._instantiate_page(key)
        page.grid(row=0, column=0, sticky="nsew")
        self._current_page = page
        self._current_key  = key

        try:
            page.on_enter()
        except Exception:
            pass

        self._header.set_page(title)
        self._sidebar.set_active(key)

    def _show_page(self, key: str) -> None:
        """Navigate to `key`, pushing current page onto history."""
        if key not in PAGE_CLASSES:
            return
        # Push to history; cap length to avoid unbounded growth (RISK-005)
        if self._current_key and self._current_key != key:
            self._nav_history.append(self._current_key)
            if len(self._nav_history) > _MAX_HISTORY:
                self._nav_history.pop(0)
        self._swap_page(key)

    def _show_page_no_history(self, key: str) -> None:
        """Navigate to `key` without modifying history (used by ESC/H)."""
        if key not in PAGE_CLASSES:
            return
        self._swap_page(key)

    # ================================================================== #
    # Keyboard shortcuts                                                   #
    # ================================================================== #

    def _bind_shortcuts(self) -> None:
        """Register global keyboard shortcuts on the root window."""
        # Q — quit (RISK-002 fix: skip when an Entry widget has focus)
        self.bind_all("<q>", self._shortcut_quit)
        self.bind_all("<Q>", self._shortcut_quit)

        # ESC — emergency stop virtual mouse
        self.bind_all("<Escape>", lambda _e: self._shortcut_emergency_stop())

        # H / h — home dashboard
        self.bind_all("<h>", lambda _e: self._show_page("dashboard"))
        self.bind_all("<H>", lambda _e: self._show_page("dashboard"))

        # F1 — help dialog
        self.bind_all("<F1>", lambda _e: self._show_help())

    def _shortcut_quit(self, event) -> None:
        """
        Fire quit only when no text-entry widget currently has focus.
        Prevents accidentally quitting while typing in the Settings page.
        """
        focused = self.focus_get()
        if focused is not None:
            cls_name = focused.__class__.__name__.lower()
            if "entry" in cls_name or "text" in cls_name:
                return
        self._on_exit()

    def _shortcut_emergency_stop(self) -> None:
        """Emergency stop: immediately disable virtual mouse."""
        if self._virtual_mouse.enabled:
            self._virtual_mouse.enabled = False
            self._config.virtual_mouse_enabled = False
            if self._settings_manager:
                self._settings_manager.update(virtual_mouse_enabled=False)
                self._settings_manager.save()
            self.log_event("⚠ EMERGENCY STOP: Virtual mouse disabled via ESC key.")
            logger.warning("Emergency stop triggered: Virtual mouse disabled.")
        else:
            # If virtual mouse is already off, use ESC for back navigation
            self._shortcut_back()

    def _shortcut_back(self) -> None:
        """Navigate to the previous page; home if history is empty."""
        if self._nav_history:
            self._show_page_no_history(self._nav_history.pop())
        else:
            self._show_page_no_history("dashboard")

    def _show_help(self) -> None:
        """Open the keyboard-shortcuts help dialog."""
        HelpDialog(self).wait()

    # ================================================================== #
    # Window helpers                                                       #
    # ================================================================== #

    def _centre_window(self, w: int, h: int) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_exit(self) -> None:
        """Clean up all resources and close the application."""
        if self._camera_stream is not None:
            try:
                self._camera_stream.stop()
            except Exception:
                pass

        try:
            self._hand_detector.close()
        except Exception:
            pass

        if self._current_page is not None:
            try:
                self._current_page.on_leave()
            except Exception:
                pass

        self.destroy()
        sys.exit(0)


# ====================================================================== #
# Module entry point                                                       #
# ====================================================================== #

def main() -> None:
    app = GestureOSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
