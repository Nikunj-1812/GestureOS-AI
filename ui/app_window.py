"""
GestureOS AI — Main Application Window
======================================
CustomTkinter shell that provides the app chrome only:
left sidebar, top header, main content area, and bottom status bar.
"""

from __future__ import annotations

import time
import sys

import cv2
import customtkinter as ctk

from config.app_config import AppConfig
from config.settings_manager import SettingsManager, SettingsState
from dashboard.components.footer import FooterBar
from dashboard.components.header import TopHeader
from dashboard.components.sidebar import SidebarNav
from dashboard.pages.dashboard_page import DashboardPage
from dashboard.shell.page_registry import PAGE_CLASSES, PAGE_TITLES
from dashboard.theme import COLORS, SIZES
from modules.camera import CameraStream


class AppWindow(ctk.CTk):
    """Main GestureOS AI window with placeholder navigation pages."""

    def __init__(self) -> None:
        ctk.set_default_color_theme("blue")

        super().__init__()

        self._settings_manager = SettingsManager()
        self._config = self._settings_manager.build_app_config("config/settings.yaml")
        ctk.set_appearance_mode(self._config.theme)

        self.title(self._config.window_title)
        self.geometry("1920x1080")
        self.minsize(1280, 720)
        self.configure(fg_color=COLORS["base"])

        self._centre_window(SIZES["window_w"], SIZES["window_h"])
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

        self._current_page: ctk.CTkFrame | None = None
        self._camera_stream: CameraStream | None = None
        self._last_fps_tick = time.perf_counter()
        self._fps_smooth = 0.0

        self._build_shell()
        self._show_page("dashboard")
        self._start_camera()
        self.after(15, self._poll_camera)

    def _build_shell(self) -> None:
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
            self,
            fg_color=COLORS["base"],
            corner_radius=0,
        )
        self._content_frame.grid(row=1, column=1, sticky="nsew")
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=1)

        self._footer = FooterBar(self)
        self._footer.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self._footer.set_fps(0)
        self._footer.set_camera_status("Disconnected")
        self._footer.set_hand_status("Not Detected")
        self._footer.set_model_status("Not Loaded")

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
        except Exception:
            self._camera_stream = None
            self._footer.set_camera_status("Disconnected")

    def _restart_camera(self) -> None:
        self._start_camera()

    def _apply_settings(self, settings: SettingsState) -> None:
        camera_changed = settings.camera_index != self._config.camera_index
        fps_changed = settings.fps_limit != self._config.camera_fps

        self._config.camera_index = settings.camera_index
        self._config.camera_fps = settings.fps_limit
        self._config.theme = settings.theme

        ctk.set_appearance_mode(settings.theme)

        if camera_changed or fps_changed:
            self._restart_camera()

    def _poll_camera(self) -> None:
        if self._camera_stream is None:
            self.after(100, self._poll_camera)
            return

        frame = self._camera_stream.read()
        if frame is None:
            self._footer.set_camera_status("Starting")
            self.after(15, self._poll_camera)
            return

        if self._config.flip_horizontal:
            frame = cv2.flip(frame, 1)

        if isinstance(self._current_page, DashboardPage):
            self._current_page.set_camera_frame(frame)

        now = time.perf_counter()
        delta = max(now - self._last_fps_tick, 1e-6)
        instant_fps = 1.0 / delta
        self._fps_smooth = instant_fps if self._fps_smooth == 0 else (self._fps_smooth * 0.85 + instant_fps * 0.15)
        self._last_fps_tick = now

        self._footer.set_fps(self._fps_smooth)
        self._footer.set_camera_status("Connected")
        self._footer.set_hand_status("Not Detected")
        self._footer.set_model_status("Not Loaded")

        self.after(max(1, int(1000 / max(self._config.camera_fps, 1))), self._poll_camera)

    def _show_page(self, key: str) -> None:
        if key not in PAGE_CLASSES:
            return

        title_text = PAGE_TITLES.get(key, key.replace("_", " ").title())

        if self._current_page is not None:
            self._current_page.destroy()
            self._current_page = None

        page_class = PAGE_CLASSES[key]
        if key == "dashboard":
            page = DashboardPage(self._content_frame, on_navigate=self._show_page)
        elif key == "virtual_mouse":
            page = page_class(self._content_frame, on_navigate=self._show_page)
        elif key == "virtual_keyboard":
            page = page_class(self._content_frame, on_navigate=self._show_page)
        elif key == "settings":
            page = page_class(
                self._content_frame,
                settings_manager=self._settings_manager,
                on_settings_changed=self._apply_settings,
            )
        else:
            page = page_class(self._content_frame)

        page.grid(row=0, column=0, sticky="nsew")

        self._current_page = page
        self._header.set_page(title_text)
        self._sidebar.set_active(key)

    def _centre_window(self, w: int, h: int) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_exit(self) -> None:
        if self._camera_stream is not None:
            try:
                self._camera_stream.stop()
            except Exception:
                pass

        self.destroy()
        sys.exit(0)

    def run(self) -> int:
        self.mainloop()
        return 0
