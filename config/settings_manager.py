"""
GestureOS AI — Settings Manager
================================
JSON-backed application settings for startup and live updates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from config.app_config import AppConfig


@dataclass(slots=True)
class SettingsState:
    camera_index: int = 0
    theme: str = "dark"
    fps_limit: int = 30
    show_landmarks: bool = True
    show_connections: bool = True
    show_bounding_box: bool = True
    show_finger_states: bool = True
    show_distance_meter: bool = True
    show_debug_panel: bool = True
    show_hud: bool = True
    virtual_mouse_enabled: bool = False
    virtual_mouse_sensitivity: float = 1.5
    virtual_mouse_dead_zone: float = 0.15
    virtual_mouse_smoothing: float = 0.20
    virtual_mouse_click_threshold: float = 0.05
    virtual_mouse_right_click_threshold: float = 0.05  # Phase 3.3
    virtual_mouse_scroll_sensitivity: float = 5.0      # Phase 3.4
    virtual_mouse_scroll_dead_zone: float = 0.04       # Phase 3.4
    virtual_mouse_scroll_smoothing: float = 0.25       # Phase 3.4
    virtual_mouse_volume_min_distance_px: float = 30.0 # Phase 3.4
    virtual_mouse_volume_max_distance_px: float = 250.0 # Phase 3.4
    virtual_mouse_volume_smoothing: float = 0.15       # Phase 3.4
    virtual_mouse_brightness_min_distance_px: float = 30.0 # Phase 3.5
    virtual_mouse_brightness_max_distance_px: float = 250.0 # Phase 3.5
    virtual_mouse_brightness_smoothing: float = 0.15       # Phase 3.5


class SettingsManager:
    """Loads, updates, and persists GestureOS AI settings.json."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else Path(__file__).resolve().parent / "settings.json"
        self._state = self.load()

    @property
    def state(self) -> SettingsState:
        return self._state

    @property
    def camera_index(self) -> int:
        return self._state.camera_index

    @property
    def theme(self) -> str:
        return self._state.theme

    @property
    def fps_limit(self) -> int:
        return self._state.fps_limit

    def load(self) -> SettingsState:
        if not self.path.exists():
            return SettingsState()

        try:
            with self.path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (OSError, json.JSONDecodeError):
            return SettingsState()

        if isinstance(raw, dict) and {"camera_index", "theme", "fps_limit"}.issubset(raw):
            return SettingsState(
                camera_index=int(raw.get("camera_index", 0)),
                theme=self._normalize_theme(str(raw.get("theme", "dark"))),
                fps_limit=max(1, int(raw.get("fps_limit", 30))),
                show_landmarks=bool(raw.get("show_landmarks", True)),
                show_connections=bool(raw.get("show_connections", True)),
                show_bounding_box=bool(raw.get("show_bounding_box", True)),
                show_finger_states=bool(raw.get("show_finger_states", True)),
                show_distance_meter=bool(raw.get("show_distance_meter", True)),
                show_debug_panel=bool(raw.get("show_debug_panel", True)),
                show_hud=bool(raw.get("show_hud", True)),
                virtual_mouse_enabled=bool(raw.get("virtual_mouse_enabled", False)),
                virtual_mouse_sensitivity=float(raw.get("virtual_mouse_sensitivity", 1.5)),
                virtual_mouse_dead_zone=float(raw.get("virtual_mouse_dead_zone", 0.15)),
                virtual_mouse_smoothing=float(raw.get("virtual_mouse_smoothing", 0.20)),
                virtual_mouse_click_threshold=float(raw.get("virtual_mouse_click_threshold", 0.05)),
                virtual_mouse_right_click_threshold=float(raw.get("virtual_mouse_right_click_threshold", 0.05)),
                virtual_mouse_scroll_sensitivity=float(raw.get("virtual_mouse_scroll_sensitivity", 5.0)),
                virtual_mouse_scroll_dead_zone=float(raw.get("virtual_mouse_scroll_dead_zone", 0.04)),
                virtual_mouse_scroll_smoothing=float(raw.get("virtual_mouse_scroll_smoothing", 0.25)),
                virtual_mouse_volume_min_distance_px=float(raw.get("virtual_mouse_volume_min_distance_px", 30.0)),
                virtual_mouse_volume_max_distance_px=float(raw.get("virtual_mouse_volume_max_distance_px", 250.0)),
                virtual_mouse_volume_smoothing=float(raw.get("virtual_mouse_volume_smoothing", 0.15)),
                virtual_mouse_brightness_min_distance_px=float(raw.get("virtual_mouse_brightness_min_distance_px", 30.0)),
                virtual_mouse_brightness_max_distance_px=float(raw.get("virtual_mouse_brightness_max_distance_px", 250.0)),
                virtual_mouse_brightness_smoothing=float(raw.get("virtual_mouse_brightness_smoothing", 0.15)),
            )

        camera = raw.get("camera", {}) if isinstance(raw, dict) else {}
        ui = raw.get("ui", {}) if isinstance(raw, dict) else {}
        vm = raw.get("virtual_mouse", {}) if isinstance(raw, dict) else {}

        return SettingsState(
            camera_index=int(camera.get("index", 0)),
            theme=self._normalize_theme(str(ui.get("theme", "dark"))),
            fps_limit=max(1, int(camera.get("fps", 30))),
            show_landmarks=bool(ui.get("show_landmarks", True)),
            show_connections=bool(ui.get("show_connections", True)),
            show_bounding_box=bool(ui.get("show_bounding_box", True)),
            show_finger_states=bool(ui.get("show_finger_states", True)),
            show_distance_meter=bool(ui.get("show_distance_meter", True)),
            show_debug_panel=bool(ui.get("show_debug_panel", True)),
            show_hud=bool(ui.get("show_hud", True)),
            virtual_mouse_enabled=bool(vm.get("enabled", False)),
            virtual_mouse_sensitivity=float(vm.get("sensitivity", 1.5)),
            virtual_mouse_dead_zone=float(vm.get("dead_zone", 0.15)),
            virtual_mouse_smoothing=float(vm.get("smoothing", 0.20)),
            virtual_mouse_click_threshold=float(vm.get("click_threshold", 0.05)),
            virtual_mouse_right_click_threshold=float(vm.get("right_click_threshold", 0.05)),
            virtual_mouse_scroll_sensitivity=float(vm.get("scroll_sensitivity", 5.0)),
            virtual_mouse_scroll_dead_zone=float(vm.get("scroll_dead_zone", 0.04)),
            virtual_mouse_scroll_smoothing=float(vm.get("scroll_smoothing", 0.25)),
            virtual_mouse_volume_min_distance_px=float(vm.get("volume_min_distance_px", 30.0)),
            virtual_mouse_volume_max_distance_px=float(vm.get("volume_max_distance_px", 250.0)),
            virtual_mouse_volume_smoothing=float(vm.get("volume_smoothing", 0.15)),
            virtual_mouse_brightness_min_distance_px=float(vm.get("brightness_min_distance_px", 30.0)),
            virtual_mouse_brightness_max_distance_px=float(vm.get("brightness_max_distance_px", 250.0)),
            virtual_mouse_brightness_smoothing=float(vm.get("brightness_smoothing", 0.15)),
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "camera_index": self._state.camera_index,
            "theme": self._state.theme,
            "fps_limit": self._state.fps_limit,
            "show_landmarks": self._state.show_landmarks,
            "show_connections": self._state.show_connections,
            "show_bounding_box": self._state.show_bounding_box,
            "show_finger_states": self._state.show_finger_states,
            "show_distance_meter": self._state.show_distance_meter,
            "show_debug_panel": self._state.show_debug_panel,
            "show_hud": self._state.show_hud,
            "virtual_mouse_enabled": self._state.virtual_mouse_enabled,
            "virtual_mouse_sensitivity": self._state.virtual_mouse_sensitivity,
            "virtual_mouse_dead_zone": self._state.virtual_mouse_dead_zone,
            "virtual_mouse_smoothing": self._state.virtual_mouse_smoothing,
            "virtual_mouse_click_threshold": self._state.virtual_mouse_click_threshold,
            "virtual_mouse_right_click_threshold": self._state.virtual_mouse_right_click_threshold,
            "virtual_mouse_scroll_sensitivity": self._state.virtual_mouse_scroll_sensitivity,
            "virtual_mouse_scroll_dead_zone": self._state.virtual_mouse_scroll_dead_zone,
            "virtual_mouse_scroll_smoothing": self._state.virtual_mouse_scroll_smoothing,
            "virtual_mouse_volume_min_distance_px": self._state.virtual_mouse_volume_min_distance_px,
            "virtual_mouse_volume_max_distance_px": self._state.virtual_mouse_volume_max_distance_px,
            "virtual_mouse_volume_smoothing": self._state.virtual_mouse_volume_smoothing,
            "virtual_mouse_brightness_min_distance_px": self._state.virtual_mouse_brightness_min_distance_px,
            "virtual_mouse_brightness_max_distance_px": self._state.virtual_mouse_brightness_max_distance_px,
            "virtual_mouse_brightness_smoothing": self._state.virtual_mouse_brightness_smoothing,
        }
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")

    def update(
        self,
        *,
        camera_index: int | None = None,
        theme: str | None = None,
        fps_limit: int | None = None,
        show_landmarks: bool | None = None,
        show_connections: bool | None = None,
        show_bounding_box: bool | None = None,
        show_finger_states: bool | None = None,
        show_distance_meter: bool | None = None,
        show_debug_panel: bool | None = None,
        show_hud: bool | None = None,
        virtual_mouse_enabled: bool | None = None,
        virtual_mouse_sensitivity: float | None = None,
        virtual_mouse_dead_zone: float | None = None,
        virtual_mouse_smoothing: float | None = None,
        virtual_mouse_click_threshold: float | None = None,
        virtual_mouse_right_click_threshold: float | None = None,
        virtual_mouse_scroll_sensitivity: float | None = None,
        virtual_mouse_scroll_dead_zone: float | None = None,
        virtual_mouse_scroll_smoothing: float | None = None,
        virtual_mouse_volume_min_distance_px: float | None = None,
        virtual_mouse_volume_max_distance_px: float | None = None,
        virtual_mouse_volume_smoothing: float | None = None,
        virtual_mouse_brightness_min_distance_px: float | None = None,
        virtual_mouse_brightness_max_distance_px: float | None = None,
        virtual_mouse_brightness_smoothing: float | None = None,
        save: bool = True,
    ) -> bool:
        changed = False

        if camera_index is not None:
            normalized_camera = int(camera_index)
            if normalized_camera != self._state.camera_index:
                self._state.camera_index = normalized_camera
                changed = True

        if theme is not None:
            normalized_theme = self._normalize_theme(theme)
            if normalized_theme != self._state.theme:
                self._state.theme = normalized_theme
                changed = True

        if fps_limit is not None:
            normalized_fps = max(1, int(fps_limit))
            if normalized_fps != self._state.fps_limit:
                self._state.fps_limit = normalized_fps
                changed = True

        for key, val in [
            ("show_landmarks", show_landmarks),
            ("show_connections", show_connections),
            ("show_bounding_box", show_bounding_box),
            ("show_finger_states", show_finger_states),
            ("show_distance_meter", show_distance_meter),
            ("show_debug_panel", show_debug_panel),
            ("show_hud", show_hud),
            ("virtual_mouse_enabled", virtual_mouse_enabled),
            ("virtual_mouse_sensitivity", virtual_mouse_sensitivity),
            ("virtual_mouse_dead_zone", virtual_mouse_dead_zone),
            ("virtual_mouse_smoothing", virtual_mouse_smoothing),
            ("virtual_mouse_click_threshold", virtual_mouse_click_threshold),
            ("virtual_mouse_right_click_threshold", virtual_mouse_right_click_threshold),
            ("virtual_mouse_scroll_sensitivity", virtual_mouse_scroll_sensitivity),
            ("virtual_mouse_scroll_dead_zone", virtual_mouse_scroll_dead_zone),
            ("virtual_mouse_scroll_smoothing", virtual_mouse_scroll_smoothing),
            ("virtual_mouse_volume_min_distance_px", virtual_mouse_volume_min_distance_px),
            ("virtual_mouse_volume_max_distance_px", virtual_mouse_volume_max_distance_px),
            ("virtual_mouse_volume_smoothing", virtual_mouse_volume_smoothing),
            ("virtual_mouse_brightness_min_distance_px", virtual_mouse_brightness_min_distance_px),
            ("virtual_mouse_brightness_max_distance_px", virtual_mouse_brightness_max_distance_px),
            ("virtual_mouse_brightness_smoothing", virtual_mouse_brightness_smoothing),
        ]:
            if val is not None:
                current_val = getattr(self._state, key)
                if val != current_val:
                    setattr(self._state, key, val)
                    changed = True

        if changed and save:
            self.save()

        return changed

    def build_app_config(self, base_config_path: str | Path | None = None) -> AppConfig:
        try:
            base_config = AppConfig.from_yaml(str(base_config_path)) if base_config_path is not None else AppConfig()
        except Exception:
            base_config = AppConfig()

        self.apply_to_config(base_config)
        return base_config

    def apply_to_config(self, config: AppConfig) -> AppConfig:
        config.camera_index = self._state.camera_index
        config.camera_fps = self._state.fps_limit
        config.theme = self._state.theme
        config.show_landmarks = self._state.show_landmarks
        config.show_connections = self._state.show_connections
        config.show_bounding_box = self._state.show_bounding_box
        config.show_finger_states = self._state.show_finger_states
        config.show_distance_meter = self._state.show_distance_meter
        config.show_debug_panel = self._state.show_debug_panel
        config.show_hud = self._state.show_hud
        config.virtual_mouse_enabled = self._state.virtual_mouse_enabled
        config.virtual_mouse_sensitivity = self._state.virtual_mouse_sensitivity
        config.virtual_mouse_dead_zone = self._state.virtual_mouse_dead_zone
        config.virtual_mouse_smoothing = self._state.virtual_mouse_smoothing
        config.virtual_mouse_click_threshold = self._state.virtual_mouse_click_threshold
        config.virtual_mouse_right_click_threshold = self._state.virtual_mouse_right_click_threshold
        config.virtual_mouse_scroll_sensitivity = self._state.virtual_mouse_scroll_sensitivity
        config.virtual_mouse_scroll_dead_zone = self._state.virtual_mouse_scroll_dead_zone
        config.virtual_mouse_scroll_smoothing = self._state.virtual_mouse_scroll_smoothing
        config.virtual_mouse_volume_min_distance_px = self._state.virtual_mouse_volume_min_distance_px
        config.virtual_mouse_volume_max_distance_px = self._state.virtual_mouse_volume_max_distance_px
        config.virtual_mouse_volume_smoothing = self._state.virtual_mouse_volume_smoothing
        config.virtual_mouse_brightness_min_distance_px = self._state.virtual_mouse_brightness_min_distance_px
        config.virtual_mouse_brightness_max_distance_px = self._state.virtual_mouse_brightness_max_distance_px
        config.virtual_mouse_brightness_smoothing = self._state.virtual_mouse_brightness_smoothing
        return config

    def snapshot(self) -> SettingsState:
        return SettingsState(
            camera_index=self._state.camera_index,
            theme=self._state.theme,
            fps_limit=self._state.fps_limit,
            show_landmarks=self._state.show_landmarks,
            show_connections=self._state.show_connections,
            show_bounding_box=self._state.show_bounding_box,
            show_finger_states=self._state.show_finger_states,
            show_distance_meter=self._state.show_distance_meter,
            show_debug_panel=self._state.show_debug_panel,
            show_hud=self._state.show_hud,
            virtual_mouse_enabled=self._state.virtual_mouse_enabled,
            virtual_mouse_sensitivity=self._state.virtual_mouse_sensitivity,
            virtual_mouse_dead_zone=self._state.virtual_mouse_dead_zone,
            virtual_mouse_smoothing=self._state.virtual_mouse_smoothing,
            virtual_mouse_click_threshold=self._state.virtual_mouse_click_threshold,
            virtual_mouse_right_click_threshold=self._state.virtual_mouse_right_click_threshold,
            virtual_mouse_scroll_sensitivity=self._state.virtual_mouse_scroll_sensitivity,
            virtual_mouse_scroll_dead_zone=self._state.virtual_mouse_scroll_dead_zone,
            virtual_mouse_scroll_smoothing=self._state.virtual_mouse_scroll_smoothing,
            virtual_mouse_volume_min_distance_px=self._state.virtual_mouse_volume_min_distance_px,
            virtual_mouse_volume_max_distance_px=self._state.virtual_mouse_volume_max_distance_px,
            virtual_mouse_volume_smoothing=self._state.virtual_mouse_volume_smoothing,
            virtual_mouse_brightness_min_distance_px=self._state.virtual_mouse_brightness_min_distance_px,
            virtual_mouse_brightness_max_distance_px=self._state.virtual_mouse_brightness_max_distance_px,
            virtual_mouse_brightness_smoothing=self._state.virtual_mouse_brightness_smoothing,
        )

    def _normalize_theme(self, theme: str) -> str:
        normalized = theme.strip().lower()
        if normalized not in {"dark", "light", "system"}:
            return "dark"
        return normalized