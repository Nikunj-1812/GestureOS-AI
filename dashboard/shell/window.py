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

import sys
import time
from pathlib import Path

import cv2
import customtkinter as ctk

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

        # ── Camera ────────────────────────────────────────────────────
        self._camera_stream: CameraStream | None = None
        self._last_fps_tick  = time.perf_counter()
        self._fps_smooth     = 0.0

        # ── Gesture pipeline components ───────────────────────────────
        # HandDetector is always created (MediaPipe is always available).
        self._hand_detector = HandDetector(
            max_hands=self._config.smoothing_frames,   # typically 2
            detection_confidence=self._config.confidence_threshold,
            tracking_confidence=self._config.confidence_threshold,
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
        except Exception as exc:
            self._camera_stream = None
            self._footer.set_camera_status("Disconnected")

    def _restart_camera(self) -> None:
        self._start_camera()

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

        frame = self._camera_stream.read()
        if frame is None:
            self._footer.set_camera_status("Starting")
            self.after(15, self._poll_camera)
            return

        # ── Flip ─────────────────────────────────────────────────────
        if self._config.flip_horizontal:
            frame = cv2.flip(frame, 1)

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

        model_status = (
            f"Loaded · {gesture_label} ({gesture_confidence * 100:.0f}%)"
            if self._gesture_engine.is_loaded and detected_hands
            else ("Loaded" if self._gesture_engine.is_loaded else "Not Loaded")
        )
        self._footer.set_model_status(model_status)

        # ── Step 6: Forward frame to DashboardPage preview ───────────
        if isinstance(self._current_page, DashboardPage):
            # Optionally draw landmark skeleton on the preview frame
            if self._config.show_landmarks and detected_hands:
                self._hand_detector.draw(frame, mp_results)
            self._current_page.set_camera_frame(frame)

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

        # Schedule next poll
        interval_ms = max(1, int(1000 / max(self._config.camera_fps, 1)))
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

        ctk.set_appearance_mode(settings.theme)

        if camera_changed or fps_changed:
            self._restart_camera()

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
                self._content_frame, on_navigate=self._show_page
            )
        if key in ("virtual_mouse", "virtual_keyboard"):
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

        # ESC — go back one page
        self.bind_all("<Escape>", lambda _e: self._shortcut_back())

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
        if isinstance(focused, (ctk.CTkEntry, ctk.CTkTextbox)):
            return
        self._on_exit()

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
