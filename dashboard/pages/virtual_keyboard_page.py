"""
GestureOS AI — Keyboard Page
===========================
Interactive, premium virtual keyboard page with camera stream, live typing, and telemetry.
"""

from __future__ import annotations

import customtkinter as ctk
from datetime import datetime
import math
from typing import TYPE_CHECKING
import pyautogui

try:
    import winsound
except ImportError:
    winsound = None

if TYPE_CHECKING:
    from config.settings_manager import SettingsManager

from dashboard.components.widgets import Badge, CameraFeed, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES
from loguru import logger
from modules import word_predictor


class VirtualKeyboardPage(BasePage):
    PAGE_KEY = "virtual_keyboard"
    PAGE_TITLE = "Keyboard Page"
    PAGE_ICON = "⌨"

    def __init__(
        self,
        master,
        on_navigate: callable | None = None,
        settings_manager: SettingsManager | None = None,
        **kwargs,
    ) -> None:
        self._on_navigate = on_navigate
        self._settings_manager = settings_manager
        
        # Load click threshold
        if self._settings_manager:
            self.click_threshold = self._settings_manager.state.virtual_mouse_click_threshold
        else:
            self.click_threshold = 0.05
            
        self.shift_active = False
        self.caps_lock_active = False
        self._alphabet_buttons: dict[str, ctk.CTkButton] = {}
        self._all_buttons: dict[str, ctk.CTkButton] = {}
        
        # Coordinates smoothing & hover tracking states
        self._smooth_x: float | None = None
        self._smooth_y: float | None = None
        self._candidate_key: str | None = None
        self._candidate_start_time: datetime | None = None
        self._active_hovered_key: str | None = None
        self._last_hover_detect_time: datetime | None = None
        
        # Pinch state machine & sound settings
        self._pinch_active = False
        
        # Load keyboard preferences from SettingsManager
        if self._settings_manager:
            self.enable_sound = self._settings_manager.state.keyboard_sound_enabled
            self.system_typing_active = self._settings_manager.state.keyboard_system_typing_enabled
            self.autocomplete_enabled = self._settings_manager.state.keyboard_autocomplete_enabled
        else:
            self.enable_sound = True
            self.system_typing_active = False
            self.autocomplete_enabled = True

        # Typing statistics & autocomplete state
        self.total_keystrokes = 0
        self.backspace_count = 0
        self.typing_start_time = None
        self.recent_words: list[str] = []
        self._suggestion_buttons: list[ctk.CTkButton] = []
        
        super().__init__(master, **kwargs)

    def _build(self) -> None:
        pad = SIZES["pad_lg"]
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── 1. Hero Header Section ───────────────────────────────────────
        hero = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        hero.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero,
            text="Virtual Keyboard Controls",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            hero,
            text="Hover over key elements using the mouse or index cursor to highlight them. Click/Pinch to register keystrokes.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(hero, text="Interactive", color=COLORS["green"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        # ── 2. Two-Column Main Content Layout ────────────────────────────
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=1, column=0, sticky="nsew", padx=pad, pady=(pad, 0))
        main_content.grid_columnconfigure(0, weight=3)  # Camera stream
        main_content.grid_columnconfigure(1, weight=2)  # Controls/Telemetry panel
        main_content.grid_rowconfigure(0, weight=1)

        # Left Column: Live Preview Area
        preview_frame = ctk.CTkFrame(
            main_content,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, SIZES["pad_md"]))
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)

        self._camera_feed = CameraFeed(preview_frame, width=640, height=360, show_overlays=True)
        self._camera_feed.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)

        # Right Column: Telemetry & Controls Panel
        right_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=1)

        # Telemetry Card
        telemetry_card = ctk.CTkFrame(
            right_panel,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        telemetry_card.grid(row=0, column=0, sticky="nsew")
        telemetry_card.grid_rowconfigure(14, weight=1) # text box row expands

        ctk.CTkLabel(
            telemetry_card,
            text="Keyboard Telemetry",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        # Telemetry fields
        self._lbl_hovered = self._create_data_label(telemetry_card, "Current Hovered Key", "None", 1)
        self._lbl_last_pressed = self._create_data_label(telemetry_card, "Last Pressed Key", "None", 2)
        self._lbl_fps = self._create_data_label(telemetry_card, "Stream FPS", "-- FPS", 3)
        self._lbl_hover_duration = self._create_data_label(telemetry_card, "Hover Duration", "0.00s", 4)
        self._lbl_pinch_distance = self._create_data_label(telemetry_card, "Pinch Distance", "0.0000", 5)
        self._lbl_wpm = self._create_data_label(telemetry_card, "Typing Speed", "0 WPM", 6)
        self._lbl_accuracy = self._create_data_label(telemetry_card, "Accuracy", "100%", 7)
        self._lbl_current_word = self._create_data_label(telemetry_card, "Current Word", "None", 8)
        self._lbl_recent_words = self._create_data_label(telemetry_card, "Recent Words", "None", 9)

        # Sound Toggle row
        sound_toggle_frame = ctk.CTkFrame(telemetry_card, fg_color="transparent")
        sound_toggle_frame.grid(row=10, column=0, columnspan=2, padx=16, pady=2, sticky="ew")
        sound_toggle_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            sound_toggle_frame,
            text="Sound Feedback",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            width=140
        ).grid(row=0, column=0, sticky="w")

        self._sound_switch = ctk.CTkSwitch(
            sound_toggle_frame,
            text="",
            progress_color=COLORS["accent"],
            command=self._on_sound_toggle_changed
        )
        self._sound_switch.grid(row=0, column=1, sticky="w")
        if self.enable_sound:
            self._sound_switch.select()
        else:
            self._sound_switch.deselect()

        # System Typing (OS) Toggle row
        system_typing_frame = ctk.CTkFrame(telemetry_card, fg_color="transparent")
        system_typing_frame.grid(row=11, column=0, columnspan=2, padx=16, pady=2, sticky="ew")
        system_typing_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            system_typing_frame,
            text="System Typing (OS)",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            width=140
        ).grid(row=0, column=0, sticky="w")

        self._system_typing_switch = ctk.CTkSwitch(
            system_typing_frame,
            text="",
            progress_color=COLORS["accent"],
            command=self._on_system_typing_changed
        )
        self._system_typing_switch.grid(row=0, column=1, sticky="w")
        if self.system_typing_active:
            self._system_typing_switch.select()
        else:
            self._system_typing_switch.deselect()

        # Autocomplete Toggle row
        autocomplete_frame = ctk.CTkFrame(telemetry_card, fg_color="transparent")
        autocomplete_frame.grid(row=12, column=0, columnspan=2, padx=16, pady=2, sticky="ew")
        autocomplete_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            autocomplete_frame,
            text="Word Suggestions",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            width=140
        ).grid(row=0, column=0, sticky="w")

        self._autocomplete_switch = ctk.CTkSwitch(
            autocomplete_frame,
            text="",
            progress_color=COLORS["accent"],
            command=self._on_autocomplete_changed
        )
        self._autocomplete_switch.grid(row=0, column=1, sticky="w")
        if self.autocomplete_enabled:
            self._autocomplete_switch.select()
        else:
            self._autocomplete_switch.deselect()

        # Live typed text header with a Clear button
        text_header_frame = ctk.CTkFrame(telemetry_card, fg_color="transparent")
        text_header_frame.grid(row=13, column=0, columnspan=2, padx=16, pady=(8, 4), sticky="ew")
        text_header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            text_header_frame,
            text="Live Typed Text",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            text_header_frame,
            text="Clear",
            width=60,
            height=24,
            font=ctk.CTkFont(*FONTS["badge"]),
            fg_color=COLORS["red"],
            hover_color=COLORS["maroon"],
            text_color=COLORS["base"],
            corner_radius=6,
            command=self._clear_text
        ).grid(row=0, column=1, sticky="e")

        # Live typed text input display
        self._typed_text = ctk.CTkTextbox(
            telemetry_card,
            fg_color=COLORS["base"],
            text_color=COLORS["text"],
            font=ctk.CTkFont("Consolas", 14),
            corner_radius=12,
            border_width=1,
            border_color=COLORS["card_border"]
        )
        self._typed_text.grid(row=14, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="nsew")

        # ── 3. Keyboard Layout Grid Section ──────────────────────────────
        SectionTitle(self, "QWERTY Keyboard Grid", "Click or use hand pinch gestures to type text.").grid(
            row=2, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"])
        )

        keyboard_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        keyboard_frame.grid(row=3, column=0, sticky="ew", padx=pad, pady=(0, pad))

        # 1. Suggestions row (Phase 4.5)
        self._suggestions_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        self._suggestions_frame.pack(fill="x", padx=16, pady=(16, 2))
        for col in range(3):
            self._suggestions_frame.grid_columnconfigure(col, weight=1)
            btn = ctk.CTkButton(
                self._suggestions_frame,
                text="",
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(*FONTS["body_bold"]),
                fg_color=COLORS["surface2"],
                hover_color=COLORS["overlay0"],
                text_color=COLORS["accent"],
                command=lambda idx=col: self._on_suggestion_clicked(idx)
            )
            btn.grid(row=0, column=col, padx=6, pady=2, sticky="ew")
            self._suggestion_buttons.append(btn)
            
            # Register in all_buttons for hand-tracking hover & pinch detection
            s_key = f"Suggestion_{col}"
            self._all_buttons[s_key] = btn
            btn.bind("<Enter>", lambda e, k=s_key: self._on_key_hover(k))
            btn.bind("<Leave>", lambda e: self._on_key_leave())
            btn.bind("<Button-1>", lambda e, k=s_key, b=btn: self._on_key_press(k, b))

        # Setup QWERTY rows
        r1_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        r1_frame.pack(fill="x", padx=16, pady=(4, 4))
        r2_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        r2_frame.pack(fill="x", padx=16, pady=4)
        r3_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        r3_frame.pack(fill="x", padx=16, pady=4)
        r4_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        r4_frame.pack(fill="x", padx=16, pady=4)
        r5_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        r5_frame.pack(fill="x", padx=16, pady=(4, 4))

        # Emoji row (Phase 4.5)
        emoji_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        emoji_frame.pack(fill="x", padx=16, pady=(4, 16))
        
        emojis = ["😊", "😂", "👍", "🔥", "❤️", "🎉", "✨", "🚀", "👋", "👀"]
        for col, emoji in enumerate(emojis):
            emoji_frame.grid_columnconfigure(col, weight=1)
            btn = ctk.CTkButton(
                emoji_frame,
                text=emoji,
                height=40,
                corner_radius=8,
                font=ctk.CTkFont("Segoe UI Emoji", 16),
                fg_color=COLORS["surface1"],
                hover_color=COLORS["surface2"],
                text_color=COLORS["text"],
                command=lambda em=emoji: None
            )
            btn.grid(row=0, column=col, padx=4, pady=2, sticky="ew")
            
            # Register in all_buttons for hand-tracking hover & pinch detection
            self._all_buttons[emoji] = btn
            btn.bind("<Enter>", lambda e, em=emoji: self._on_key_hover(em))
            btn.bind("<Leave>", lambda e: self._on_key_leave())
            btn.bind("<Button-1>", lambda e, em=emoji, b=btn: self._on_key_press(em, b))

        # Row 1 (Numbers)
        row1_keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        for col, key in enumerate(row1_keys):
            r1_frame.grid_columnconfigure(col, weight=1)
            self._create_keyboard_button(r1_frame, key, row=0, column=col)

        # Row 2 (Tab + letters Q-P)
        row2_keys = ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"]
        r2_frame.grid_columnconfigure(0, weight=2) # Tab is wider
        for col in range(1, 11):
            r2_frame.grid_columnconfigure(col, weight=1)
        
        self._create_keyboard_button(r2_frame, "Tab", row=0, column=0, is_modifier=True)
        for idx, key in enumerate(row2_keys[1:]):
            self._create_keyboard_button(r2_frame, key, row=0, column=idx + 1)

        # Row 3 (Caps Lock + letters A-L + Enter)
        row3_keys = ["Caps Lock", "A", "S", "D", "F", "G", "H", "J", "K", "L", "Enter"]
        r3_frame.grid_columnconfigure(0, weight=2)  # Caps Lock is wider
        for col in range(1, 10):
            r3_frame.grid_columnconfigure(col, weight=1)
        r3_frame.grid_columnconfigure(10, weight=2) # Enter is wider

        self._btn_caps = self._create_keyboard_button(r3_frame, "Caps Lock", row=0, column=0, is_modifier=True)
        for idx, key in enumerate(row3_keys[1:10]):
            self._create_keyboard_button(r3_frame, key, row=0, column=idx + 1)
        self._create_keyboard_button(r3_frame, "Enter", row=0, column=10, is_modifier=True)

        # Row 4 (Shift + letters Z-M + Backspace)
        row4_keys = ["Shift", "Z", "X", "C", "V", "B", "N", "M", "Backspace"]
        r4_frame.grid_columnconfigure(0, weight=2)  # Shift is wider
        for col in range(1, 8):
            r4_frame.grid_columnconfigure(col, weight=1)
        r4_frame.grid_columnconfigure(8, weight=3)  # Backspace is wider

        self._btn_shift = self._create_keyboard_button(r4_frame, "Shift", row=0, column=0, is_modifier=True)
        for idx, key in enumerate(row4_keys[1:8]):
            self._create_keyboard_button(r4_frame, key, row=0, column=idx + 1)
        self._create_keyboard_button(r4_frame, "Backspace", row=0, column=8, is_modifier=True)

        # Row 5 (Space)
        r5_frame.grid_columnconfigure(0, weight=1)
        self._create_keyboard_button(r5_frame, "Space", row=0, column=0, is_modifier=True)

    def _create_keyboard_button(
        self,
        parent: ctk.CTkFrame,
        key: str,
        row: int,
        column: int,
        is_modifier: bool = False
    ) -> ctk.CTkButton:
        btn_text = key.lower() if len(key) == 1 else key
        
        # Color schemes based on key type
        if is_modifier:
            fg_color = COLORS["surface2"]
            hover_color = COLORS["overlay0"]
        else:
            fg_color = COLORS["surface1"]
            hover_color = COLORS["surface2"]

        btn = ctk.CTkButton(
            parent,
            text=btn_text,
            height=48,
            corner_radius=SIZES["btn_radius"],
            font=ctk.CTkFont(*FONTS["body_bold"]),
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=COLORS["text"],
            command=lambda k=key: None # command mapped dynamically via bind to capture events cleanly
        )
        btn.grid(row=row, column=column, padx=4, pady=2, sticky="ew")

        # Store alphabetic keys for case updates
        if len(key) == 1 and key.isalpha():
            self._alphabet_buttons[key] = btn

        # Store all keys for hover mapping
        self._all_buttons[key] = btn

        # Bind events for telemetry and press highlights
        btn.bind("<Enter>", lambda e, k=key: self._on_key_hover(k))
        btn.bind("<Leave>", lambda e: self._on_key_leave())
        btn.bind("<Button-1>", lambda e, k=key, b=btn: self._on_key_press(k, b))

        return btn

    def _create_data_label(self, parent: ctk.CTkFrame, title: str, value: str, row: int) -> ctk.CTkLabel:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, columnspan=2, padx=16, pady=4, sticky="ew")
        container.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            container,
            text=title,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            width=140
        ).grid(row=0, column=0, sticky="w")

        val_label = ctk.CTkLabel(
            container,
            text=value,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="w"
        )
        val_label.grid(row=0, column=1, sticky="w")
        return val_label

    def _get_key_for_widget(self, widget) -> str | None:
        w = widget
        while w:
            for key, btn in self._all_buttons.items():
                if w == btn:
                    return key
            try:
                w = w.master
            except AttributeError:
                break
        return None

    def _set_active_hovered_key(self, key: str | None) -> None:
        # 1. Restore previous active key color
        if self._active_hovered_key and self._active_hovered_key in self._all_buttons:
            prev_btn = self._all_buttons[self._active_hovered_key]
            if self._active_hovered_key == "Shift":
                resting = COLORS["accent"] if self.shift_active else COLORS["surface2"]
            elif self._active_hovered_key == "Caps Lock":
                resting = COLORS["accent"] if self.caps_lock_active else COLORS["surface2"]
            elif self._active_hovered_key in ("Tab", "Enter", "Backspace", "Space"):
                resting = COLORS["surface2"]
            else:
                resting = COLORS["surface1"]
            prev_btn.configure(fg_color=resting)

        # 2. Update state
        self._active_hovered_key = key
        self._lbl_hovered.configure(text=key if key else "None")

        # 3. Highlight new active key
        if key and key in self._all_buttons:
            new_btn = self._all_buttons[key]
            new_btn.configure(fg_color=COLORS["accent_hover"])

    def set_camera_frame(self, frame, fps: float = 0.0, detected_hands: list | None = None) -> None:
        """Receives live camera stream frames."""
        self._camera_feed.set_frame(frame, fps=fps)
        self._lbl_fps.configure(text=f"{fps:.1f} FPS" if fps > 0 else "-- FPS")

        detected_key = None
        now = datetime.now()
        pinch_dist = 0.0

        if detected_hands and len(detected_hands) > 0:
            primary_hand = detected_hands[0]
            if len(primary_hand.landmarks) > 12:
                raw_x, raw_y, _ = primary_hand.landmarks[8]
                x_mirrored = 1.0 - raw_x
                
                # Smooth coordinates
                smoothing = 0.20
                if self._smooth_x is None or self._smooth_y is None:
                    self._smooth_x = x_mirrored
                    self._smooth_y = raw_y
                else:
                    self._smooth_x += (x_mirrored - self._smooth_x) * smoothing
                    self._smooth_y += (raw_y - self._smooth_y) * smoothing

                try:
                    w_width = self.winfo_width()
                    w_height = self.winfo_height()
                    root_x = self.winfo_rootx()
                    root_y = self.winfo_rooty()
                    
                    screen_x = root_x + int(self._smooth_x * w_width)
                    screen_y = root_y + int(self._smooth_y * w_height)
                    
                    # Direct, fast bounding-box matching to avoid slow winfo_containing OS queries
                    for key, btn in self._all_buttons.items():
                        bx = btn.winfo_rootx()
                        by = btn.winfo_rooty()
                        bw = btn.winfo_width()
                        bh = btn.winfo_height()
                        if bw > 1 and bh > 1 and bx <= screen_x <= bx + bw and by <= screen_y <= by + bh:
                            detected_key = key
                            break
                    
                    if not detected_key:
                        target_widget = self.winfo_containing(screen_x, screen_y)
                        if target_widget:
                            detected_key = self._get_key_for_widget(target_widget)
                except Exception as e:
                    logger.debug(f"Error resolving hovered widget: {e}")

                # Compute pinch distance between Middle Finger Tip (12) and Thumb Tip (4)
                mx, my, mz = primary_hand.landmarks[12]
                tx, ty, tz = primary_hand.landmarks[4]
                pinch_dist = math.sqrt((mx - tx)**2 + (my - ty)**2 + (mz - tz)**2)
        else:
            self._smooth_x = None
            self._smooth_y = None

        # Update pinch distance telemetry
        self._lbl_pinch_distance.configure(text=f"{pinch_dist:.4f}")

        # Hover Delay and Debouncing (Anti-flicker)
        if detected_key:
            self._last_hover_detect_time = now
            if detected_key == self._candidate_key:
                elapsed = (now - self._candidate_start_time).total_seconds()
                self._lbl_hover_duration.configure(text=f"{elapsed:.2f}s")
                if elapsed >= 0.150:
                    if self._active_hovered_key != detected_key:
                        self._set_active_hovered_key(detected_key)
            else:
                self._candidate_key = detected_key
                self._candidate_start_time = now
                self._lbl_hover_duration.configure(text="0.00s")
        else:
            debounce_elapsed = 0.0
            if self._last_hover_detect_time:
                debounce_elapsed = (now - self._last_hover_detect_time).total_seconds()
                
            if debounce_elapsed >= 0.100 or not self._last_hover_detect_time:
                self._candidate_key = None
                self._candidate_start_time = None
                self._lbl_hover_duration.configure(text="0.00s")
                if self._active_hovered_key:
                    self._set_active_hovered_key(None)

        # Key Press Detection (Typing Logic)
        if detected_hands and len(detected_hands) > 0 and pinch_dist > 0:
            if pinch_dist <= self.click_threshold:
                if not self._pinch_active:
                    self._pinch_active = True
                    if self._active_hovered_key:
                        btn = self._all_buttons.get(self._active_hovered_key)
                        if btn:
                            self._on_key_press(self._active_hovered_key, btn)
                            if self.enable_sound and winsound:
                                import threading
                                try:
                                    threading.Thread(
                                        target=winsound.Beep,
                                        args=(1000, 50),
                                        daemon=True
                                    ).start()
                                except Exception as sound_err:
                                    logger.debug(f"Audio beep failed: {sound_err}")
            else:
                if pinch_dist > self.click_threshold + 0.005:  # small hysteresis
                    self._pinch_active = False
        else:
            self._pinch_active = False

    def _on_key_hover(self, key: str) -> None:
        self._set_active_hovered_key(key)

    def _on_key_leave(self) -> None:
        self._set_active_hovered_key(None)

    def _on_key_press(self, key: str, btn: ctk.CTkButton) -> None:
        # 1. Update pressed status
        self._lbl_last_pressed.configure(text=key)

        # 2. Trigger animation
        self._animate_press(key, btn)

        # 3. Handle statistics tracking
        if self.typing_start_time is None:
            self.typing_start_time = datetime.now()
        if key == "Backspace":
            self.backspace_count += 1
        self.total_keystrokes += 1

        # 4. Resolve character value (handling case of standard keys)
        if len(key) == 1 and key.isalpha():
            is_upper = self.caps_lock_active or self.shift_active
            char = key.upper() if is_upper else key.lower()
        else:
            char = key

        # 5. Process Suggestion Autocomplete
        if key.startswith("Suggestion_"):
            idx = int(key.split("_")[1])
            suggested_word = self._suggestion_buttons[idx].cget("text")
            if suggested_word:
                text = self._typed_text.get("1.0", "end-1c")
                prefix = word_predictor.get_current_word(text)
                
                # Delete prefix from textbox
                if prefix:
                    prefix_len = len(prefix)
                    self._typed_text.delete(f"end-1c-{prefix_len}c", "end-1c")
                
                # Insert suggestion + space
                self._typed_text.insert("insert", suggested_word + " ")
                
                # Inject to OS if active
                if self.system_typing_active:
                    try:
                        for _ in range(len(prefix)):
                            pyautogui.press("backspace")
                        pyautogui.write(suggested_word + " ")
                    except Exception as e:
                        logger.error(f"Error executing pyautogui autocomplete: {e}")
                
                self._auto_release_shift()
                self._update_analytics()
            return

        # 6. Process key logic (OS System Typing)
        if self.system_typing_active:
            try:
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
                    # Safe paste utility for emojis or non-ASCII characters
                    if any(ord(c) > 127 for c in char):
                        try:
                            self.clipboard_clear()
                            self.clipboard_append(char)
                            self.update()
                            pyautogui.hotkey("ctrl", "v")
                        except Exception as clip_err:
                            logger.debug(f"Tkinter clipboard paste failed: {clip_err}")
                            pyautogui.write(char)
                    else:
                        pyautogui.write(char)
            except Exception as e:
                logger.error(f"Error executing pyautogui keypress: {e}")

        # 7. Process local text box logic
        if key == "Shift":
            self.shift_active = not self.shift_active
            self._update_modifiers_ui()
        elif key == "Caps Lock":
            self.caps_lock_active = not self.caps_lock_active
            self._update_modifiers_ui()
        elif key == "Backspace":
            try:
                # Delete last character
                text = self._typed_text.get("1.0", "end-1c")
                if text:
                    self._typed_text.delete("end-2c", "end-1c")
            except Exception as e:
                logger.error(f"Error handling backspace deletion: {e}")
        elif key == "Space":
            self._typed_text.insert("insert", " ")
            self._auto_release_shift()
        elif key == "Tab":
            self._typed_text.insert("insert", "    ")
            self._auto_release_shift()
        elif key == "Enter":
            self._typed_text.insert("insert", "\n")
            self._auto_release_shift()
        else:
            # Standard alphabetical, numerical, or emoji key
            self._typed_text.insert("insert", char)
            self._auto_release_shift()

        # Update analytics & prediction panels
        self._update_analytics()

    def _animate_press(self, key: str, btn: ctk.CTkButton) -> None:
        # Temporarily flash peach accent color
        btn.configure(fg_color=COLORS["peach"])
        
        def restore():
            if key == "Shift":
                resting = COLORS["accent"] if self.shift_active else COLORS["surface2"]
            elif key == "Caps Lock":
                resting = COLORS["accent"] if self.caps_lock_active else COLORS["surface2"]
            elif key in ("Tab", "Enter", "Backspace", "Space") or key.startswith("Suggestion_") or any(ord(c) > 127 for c in key):
                resting = COLORS["surface2"]
            else:
                resting = COLORS["surface1"]
            btn.configure(fg_color=resting)
            
        self.after(80, restore)

    def _auto_release_shift(self) -> None:
        if self.shift_active:
            self.shift_active = False
            self._update_modifiers_ui()

    def _update_modifiers_ui(self) -> None:
        # Update Shift button styling
        shift_color = COLORS["accent"] if self.shift_active else COLORS["surface2"]
        shift_text_color = COLORS["base"] if self.shift_active else COLORS["text"]
        self._btn_shift.configure(fg_color=shift_color, text_color=shift_text_color)
        
        # Update Caps Lock button styling
        caps_color = COLORS["accent"] if self.caps_lock_active else COLORS["surface2"]
        caps_text_color = COLORS["base"] if self.caps_lock_active else COLORS["text"]
        self._btn_caps.configure(fg_color=caps_color, text_color=caps_text_color)

        # Update alphabetical key labels dynamically
        is_upper = self.caps_lock_active or self.shift_active
        for char, btn in self._alphabet_buttons.items():
            btn.configure(text=char.upper() if is_upper else char.lower())

    def _clear_text(self) -> None:
        self._typed_text.delete("1.0", "end")
        self.total_keystrokes = 0
        self.backspace_count = 0
        self.typing_start_time = None
        self.recent_words = []
        self._update_analytics()

    def _on_sound_toggle_changed(self) -> None:
        self.enable_sound = self._sound_switch.get() == 1
        if self._settings_manager:
            self._settings_manager.update(keyboard_sound_enabled=self.enable_sound)

    def _on_system_typing_changed(self) -> None:
        self.system_typing_active = self._system_typing_switch.get() == 1
        if self._settings_manager:
            self._settings_manager.update(keyboard_system_typing_enabled=self.system_typing_active)

    def _on_autocomplete_changed(self) -> None:
        self.autocomplete_enabled = self._autocomplete_switch.get() == 1
        if self._settings_manager:
            self._settings_manager.update(keyboard_autocomplete_enabled=self.autocomplete_enabled)
        self._update_analytics()

    def _on_suggestion_clicked(self, idx: int) -> None:
        btn = self._suggestion_buttons[idx]
        suggested_word = btn.cget("text")
        if suggested_word:
            self._on_key_press(f"Suggestion_{idx}", btn)

    def _update_analytics(self) -> None:
        text = self._typed_text.get("1.0", "end-1c")
        
        # 1. Update WPM
        if self.typing_start_time:
            elapsed_seconds = (datetime.now() - self.typing_start_time).total_seconds()
            elapsed_minutes = max(5.0, elapsed_seconds) / 60.0 # clamp to min 5 seconds for stability
            wpm = int((len(text) / 5) / elapsed_minutes)
        else:
            wpm = 0
            
        self._lbl_wpm.configure(text=f"{wpm} WPM")
        
        # 2. Update Accuracy
        if self.total_keystrokes > 0:
            accuracy = max(0.0, (self.total_keystrokes - 2 * self.backspace_count) / self.total_keystrokes * 100)
        else:
            accuracy = 100.0
            
        self._lbl_accuracy.configure(text=f"{accuracy:.0f}%")
        
        # 3. Update Current Word & Suggestions
        curr_word = word_predictor.get_current_word(text)
        self._lbl_current_word.configure(text=curr_word if curr_word else "None")
        
        if self.autocomplete_enabled and curr_word:
            suggestions = word_predictor.get_suggestions(curr_word)
        else:
            suggestions = []
            
        for idx in range(3):
            btn = self._suggestion_buttons[idx]
            if idx < len(suggestions):
                btn.configure(text=suggestions[idx], state="normal", fg_color=COLORS["accent"], text_color=COLORS["base"])
            else:
                btn.configure(text="", state="disabled", fg_color=COLORS["surface2"], text_color=COLORS["accent"])
                
        # 4. Update Recent Words
        words = text.split()
        if words:
            completed_words = words[:-1] if not text[-1].isspace() else words
            recent = []
            for w in reversed(completed_words):
                w_clean = "".join(c for c in w if c.isalnum())
                if w_clean and w_clean not in recent:
                    recent.append(w_clean)
                    if len(recent) >= 5:
                        break
            self.recent_words = recent
            
        self._lbl_recent_words.configure(text=", ".join(self.recent_words) if self.recent_words else "None")

    def _navigate(self, key: str) -> None:
        if self._on_navigate is not None:
            self._on_navigate(key)