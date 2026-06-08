"""
GestureOS AI — Dashboard Page
==============================
Modern home screen with:
  • Live camera preview area
  • Clickable module cards
  • Clean, responsive dashboard layout
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.components.widgets import Badge, CameraFeed, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class DashboardPage(BasePage):
    PAGE_KEY = "dashboard"
    PAGE_TITLE = "Dashboard"
    PAGE_ICON = "⊞"

    def __init__(
        self,
        master,
        on_navigate: callable | None = None,
        on_start_camera: callable | None = None,
        on_stop_camera: callable | None = None,
        on_reset_tracking: callable | None = None,
        settings_manager: SettingsManager | None = None,
        on_settings_changed: callable | None = None,
        **kwargs,
    ) -> None:
        self._on_navigate = on_navigate
        self._start_cam_callback = on_start_camera
        self._stop_cam_callback = on_stop_camera
        self._reset_tracking_callback = on_reset_tracking
        from config.settings_manager import SettingsManager
        self._settings_manager = settings_manager or SettingsManager()
        self._on_settings_changed = on_settings_changed
        super().__init__(master, **kwargs)

    def _build(self) -> None:
        pad = SIZES["pad_lg"]
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Let the preview shell row expand

        # ── Welcome Banner (Row 0) ─────────────────────────────────
        banner = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        banner.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        banner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            banner,
            text="Dashboard",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            banner,
            text="Monitor the camera feed and launch GestureOS modules from one control surface.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(banner, text="System Ready", color=COLORS["green"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        # ── Top Stat Cards Row (Row 1) ─────────────────────────────
        from dashboard.components.widgets import StatCard
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        for col in range(4):
            stats_frame.grid_columnconfigure(col, weight=1, uniform="stat")

        self._card_fps = StatCard(stats_frame, icon="▶", value="--", label="FPS", accent=COLORS["blue"])
        self._card_fps.grid(row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_sm"]))

        self._card_hands = StatCard(stats_frame, icon="✋", value="0", label="Hands Detected", accent=COLORS["green"])
        self._card_hands.grid(row=0, column=1, sticky="nsew", padx=SIZES["pad_sm"])

        self._card_gesture = StatCard(stats_frame, icon="◈", value="None", label="Current Gesture", accent=COLORS["mauve"])
        self._card_gesture.grid(row=0, column=2, sticky="nsew", padx=SIZES["pad_sm"])

        self._card_camera = StatCard(stats_frame, icon="◎", value="Disconnected", label="Camera Status", accent=COLORS["red"])
        self._card_camera.grid(row=0, column=3, sticky="nsew", padx=(SIZES["pad_sm"], 0))

        # ── Section Title (Row 2) ──────────────────────────────────
        SectionTitle(
            self,
            "Live Camera Preview",
            "A dedicated preview area for the active camera feed.",
        ).grid(row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"]))

        # ── Live Camera Preview Shell (Row 3) ──────────────────────
        preview_shell = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        preview_shell.grid(row=3, column=0, sticky="nsew", padx=pad, pady=0)
        preview_shell.grid_columnconfigure(0, weight=1)
        preview_shell.grid_rowconfigure(1, weight=1)  # Let the camera feed expand

        preview_header = ctk.CTkFrame(preview_shell, fg_color="transparent")
        preview_header.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        preview_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_header,
            text="Live Camera Preview Area",
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        Badge(preview_header, text="Camera Feed", color=COLORS["accent"]).grid(
            row=0, column=1, sticky="e"
        )

        # Reduced camera preview height slightly to 340px (was 420px)
        self._camera_feed = CameraFeed(preview_shell, width=1080, height=340, show_overlays=True)
        self._camera_feed.grid(
            row=1, column=0,
            sticky="nsew",
            padx=pad,
            pady=(SIZES["pad_md"], pad),
        )

        # ── Bottom Panels Frame: Recent Events + Switches + Quick Actions (Row 4) 
        bottom_row_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_row_frame.grid(row=4, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        bottom_row_frame.grid_columnconfigure(0, weight=2)  # Log gets weight 2
        bottom_row_frame.grid_columnconfigure(1, weight=2)  # Switches get weight 2
        bottom_row_frame.grid_columnconfigure(2, weight=1)  # Actions gets weight 1

        # ── Recent Events Log ──────────────────────────────────────
        recent_events = ctk.CTkFrame(
            bottom_row_frame,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
            height=180,
        )
        recent_events.grid(row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_md"]))
        recent_events.grid_propagate(False)
        recent_events.grid_columnconfigure(0, weight=1)
        recent_events.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            recent_events,
            text="Recent Activity Log",
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        self._log_textbox = ctk.CTkTextbox(
            recent_events,
            fg_color=COLORS["base"],
            text_color=COLORS["subtext1"],
            font=ctk.CTkFont("Consolas", 11),
            corner_radius=12,
            border_width=1,
            border_color=COLORS["divider"],
        )
        self._log_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        # Populate history from the root application window (self.winfo_toplevel())
        root = self.winfo_toplevel()
        history = getattr(root, "_log_history", ["[INFO] System initialized. Waiting for camera stream."])
        for line in history:
            self._log_textbox.insert("end", f"{line}\n")
        self._log_textbox.see("end")
        self._log_textbox.configure(state="disabled")
        self._last_logged_gesture = None

        # ── Display Settings (Switches) Panel ───────────────────────
        display_settings = ctk.CTkFrame(
            bottom_row_frame,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
            height=180,
        )
        display_settings.grid(row=0, column=1, sticky="nsew", padx=(0, SIZES["pad_md"]))
        display_settings.grid_propagate(False)
        display_settings.grid_columnconfigure(0, weight=1)
        display_settings.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            display_settings,
            text="Display Switches",
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        switches_frame = ctk.CTkFrame(display_settings, fg_color="transparent")
        switches_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        switches_frame.grid_columnconfigure((0, 1), weight=1)
        switches_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)

        toggles = [
            ("show_landmarks", "Landmarks", 0, 0),
            ("show_connections", "Connections", 0, 1),
            ("show_bounding_box", "Bounding Box", 1, 0),
            ("show_finger_states", "Finger States", 1, 1),
            ("show_distance_meter", "Distance Meter", 2, 0),
            ("show_debug_panel", "Debug Panel", 2, 1),
            ("show_hud", "HUD Overlay", 3, 0),
        ]

        self._checkboxes = {}
        state = self._settings_manager.state

        for key, label, r, c in toggles:
            var_val = getattr(state, key)
            cb = ctk.CTkCheckBox(
                switches_frame,
                text=label,
                font=ctk.CTkFont(*FONTS["small"]),
                command=lambda k=key: self._on_toggle_switched(k),
                border_color=COLORS["divider"],
                fg_color=COLORS["accent"],
                hover_color=COLORS["btn_hover"],
            )
            if var_val:
                cb.select()
            cb.grid(row=r, column=c, padx=4, pady=2, sticky="w")
            self._checkboxes[key] = cb

        # ── Quick Actions Panel ────────────────────────────────────
        quick_actions = ctk.CTkFrame(
            bottom_row_frame,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
            height=180,
        )
        quick_actions.grid(row=0, column=2, sticky="nsew")
        quick_actions.grid_propagate(False)
        quick_actions.grid_columnconfigure(0, weight=1)
        quick_actions.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            quick_actions,
            text="Quick Actions",
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        btn_frame = ctk.CTkFrame(quick_actions, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_rowconfigure((0, 1, 2), weight=1)

        self._btn_start = ctk.CTkButton(
            btn_frame,
            text="▶  Start Cam",
            font=ctk.CTkFont(*FONTS["small"]),
            fg_color=COLORS["btn_primary"],
            hover_color=COLORS["btn_hover"],
            text_color=COLORS["base"],
            height=32,
            corner_radius=8,
            command=self._on_start_camera,
        )
        self._btn_start.grid(row=0, column=0, padx=0, pady=2, sticky="ew")

        self._btn_stop = ctk.CTkButton(
            btn_frame,
            text="■  Stop Cam",
            font=ctk.CTkFont(*FONTS["small"]),
            fg_color=COLORS["surface1"],
            hover_color=COLORS["red"],
            text_color=COLORS["text"],
            height=32,
            corner_radius=8,
            command=self._on_stop_camera,
        )
        self._btn_stop.grid(row=1, column=0, padx=0, pady=2, sticky="ew")

        self._btn_reset = ctk.CTkButton(
            btn_frame,
            text="↺  Reset Track",
            font=ctk.CTkFont(*FONTS["small"]),
            fg_color=COLORS["surface1"],
            hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            height=32,
            corner_radius=8,
            command=self._on_reset_tracking,
        )
        self._btn_reset.grid(row=2, column=0, padx=0, pady=2, sticky="ew")

        # ── Modules List Section (Row 5) ───────────────────────────
        SectionTitle(
            self,
            "Modules",
            "Clickable cards for the main GestureOS AI tools.",
        ).grid(row=5, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"]))

        # ── Modules Cards (Row 6) ──────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=6, column=0, sticky="ew", padx=pad, pady=(0, pad))
        for column in range(4):
            cards_frame.grid_columnconfigure(column, weight=1, uniform="module")

        cards = [
            ("⊹", "Virtual Mouse", "Cursor and click control", "virtual_mouse", COLORS["blue"]),
            ("⌨", "Virtual Keyboard", "On-screen text entry", "virtual_keyboard", COLORS["sapphire"]),
            ("✏", "Air Drawing", "Sketch gestures in the air", "air_drawing", COLORS["mauve"]),
            ("▶", "Media Control", "Play and pause media", "media_control", COLORS["green"]),
            ("⚙", "System Control", "System shortcuts and actions", "system_control", COLORS["peach"]),
            ("◈", "Gesture Training", "Train custom gestures", "gesture_training", COLORS["yellow"]),
            ("▦", "Analytics", "Usage and performance insights", "analytics", COLORS["sky"]),
            ("≡", "Settings", "Application preferences", "settings", COLORS["rosewater"]),
        ]

        for index, (icon, title, subtitle, key, accent) in enumerate(cards):
            row = index // 4
            column = index % 4
            card = _ModuleCard(
                cards_frame,
                icon=icon,
                title=title,
                subtitle=subtitle,
                accent=accent,
                command=lambda page_key=key: self._navigate(page_key),
            )
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if column < 3 else 0,
                pady=(0, SIZES["pad_sm"]) if row == 0 else 0,
            )

    def _navigate(self, key: str) -> None:
        if self._on_navigate is not None:
            self._on_navigate(key)

    def _on_start_camera(self) -> None:
        if self._start_cam_callback is not None:
            self._start_cam_callback()
            self.log_event("Camera stream start requested.")

    def _on_stop_camera(self) -> None:
        if self._stop_cam_callback is not None:
            self._stop_cam_callback()
            self.log_event("Camera stream stop requested.")

    def _on_reset_tracking(self) -> None:
        if self._reset_tracking_callback is not None:
            self._reset_tracking_callback()
            self.log_event("Tracking history and detector reset.")

    def _on_toggle_switched(self, key: str) -> None:
        cb = self._checkboxes[key]
        val = bool(cb.get())
        changed = self._settings_manager.update(**{key: val})
        if changed:
            self._settings_manager.save()
            if self._on_settings_changed:
                self._on_settings_changed(self._settings_manager.snapshot())
            self.log_event(f"Display toggle '{key}' changed to: {val}")

    def log_event(self, message: str) -> None:
        """Pipes the log event to the centralized app window logging system."""
        self.winfo_toplevel().log_event(message)

    def append_log(self, formatted_message: str) -> None:
        """Appends a pre-formatted timestamped message to the textbox and auto-scrolls."""
        self._log_textbox.configure(state="normal")
        self._log_textbox.insert("end", f"{formatted_message}\n")
        self._log_textbox.see("end")
        self._log_textbox.configure(state="disabled")

    def set_camera_frame(self, frame, fps=0.0, gesture="unknown", confidence=0.0, hands_detected=0) -> None:
        """Updates the live camera preview frame and overlays."""
        self._camera_feed.set_frame(frame, fps=fps, gesture=gesture, confidence=confidence, hands_detected=hands_detected)

        # Update top status cards
        self._card_fps.set_value(f"{fps:.1f}" if fps > 0 else "--")
        self._card_hands.set_value(str(hands_detected))

        gesture_display = gesture.replace('_', ' ').title() if gesture not in ("unknown", "No Model") else gesture
        self._card_gesture.set_value(gesture_display)
        self._card_gesture._value_label.configure(
            text_color=COLORS["green"] if gesture not in ("unknown", "No Model", "None") else COLORS["overlay1"]
        )

        self._card_camera.set_value("Connected")
        self._card_camera._value_label.configure(text_color=COLORS["green"])

        # Log new gestures dynamically
        if gesture != self._last_logged_gesture:
            if gesture not in ("unknown", "None", "No Model"):
                self.log_event(f"Gesture Detected: {gesture_display} ({confidence * 100:.0f}%)")
            self._last_logged_gesture = gesture

    def clear_camera_frame(self) -> None:
        """Resets the live camera preview back to its placeholder."""
        self._camera_feed.clear()
        self._card_fps.set_value("--")
        self._card_hands.set_value("0")
        self._card_gesture.set_value("None")
        self._card_gesture._value_label.configure(text_color=COLORS["overlay1"])
        self._card_camera.set_value("Disconnected")
        self._card_camera._value_label.configure(text_color=COLORS["red"])
        self._last_logged_gesture = None


class _ModuleCard(ctk.CTkButton):
    """Clickable dashboard shortcut card."""

    def __init__(self, master, icon: str, title: str, subtitle: str, accent: str, command: callable, **kwargs) -> None:
        super().__init__(
            master,
            text="",
            command=command,
            fg_color=COLORS["surface0"],
            hover_color=COLORS["surface1"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["card_border"],
            height=140,
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        icon_shell = ctk.CTkFrame(
            self,
            width=42,
            height=42,
            corner_radius=14,
            fg_color=COLORS["base"],
        )
        icon_shell.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        icon_shell.grid_propagate(False)

        ctk.CTkLabel(
            icon_shell,
            text=icon,
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=accent,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            justify="left",
            wraplength=210,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))