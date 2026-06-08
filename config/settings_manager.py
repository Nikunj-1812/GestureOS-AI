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
            )

        camera = raw.get("camera", {}) if isinstance(raw, dict) else {}
        ui = raw.get("ui", {}) if isinstance(raw, dict) else {}

        return SettingsState(
            camera_index=int(camera.get("index", 0)),
            theme=self._normalize_theme(str(ui.get("theme", "dark"))),
            fps_limit=max(1, int(camera.get("fps", 30))),
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "camera_index": self._state.camera_index,
            "theme": self._state.theme,
            "fps_limit": self._state.fps_limit,
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
        return config

    def snapshot(self) -> SettingsState:
        return SettingsState(
            camera_index=self._state.camera_index,
            theme=self._state.theme,
            fps_limit=self._state.fps_limit,
        )

    def _normalize_theme(self, theme: str) -> str:
        normalized = theme.strip().lower()
        if normalized not in {"dark", "light", "system"}:
            return "dark"
        return normalized