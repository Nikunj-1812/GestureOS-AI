"""
GestureOS AI — AppConfig dataclass
Loads and validates settings.yaml into a typed config object.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class AppConfig:
    # App
    app_name: str = "GestureOS AI"
    version: str = "1.0.0"
    debug: bool = False

    # Camera
    camera_index: int = 0
    camera_width: int = 1280
    camera_height: int = 720
    camera_fps: int = 30
    flip_horizontal: bool = True

    # Model
    model_dir: str = "models/weights"
    default_model: str = "gesture_classifier_v1.onnx"
    confidence_threshold: float = 0.75
    device: str = "cpu"

    # Gestures
    smoothing_frames: int = 5
    hold_duration_ms: int = 400

    # UI
    theme: str = "dark"
    overlay_opacity: float = 0.85
    show_landmarks: bool = True
    show_fps: bool = True
    window_title: str = "GestureOS AI"

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"

    @classmethod
    def from_yaml(cls, path: str) -> "AppConfig":
        cfg_path = Path(path)
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with cfg_path.open("r") as f:
            raw = yaml.safe_load(f)

        app = raw.get("app", {})
        cam = raw.get("camera", {})
        mdl = raw.get("model", {})
        ges = raw.get("gestures", {})
        ui = raw.get("ui", {})
        log = raw.get("logging", {})

        return cls(
            app_name=app.get("name", cls.app_name),
            version=app.get("version", cls.version),
            debug=app.get("debug", cls.debug),
            camera_index=cam.get("index", cls.camera_index),
            camera_width=cam.get("width", cls.camera_width),
            camera_height=cam.get("height", cls.camera_height),
            camera_fps=cam.get("fps", cls.camera_fps),
            flip_horizontal=cam.get("flip_horizontal", cls.flip_horizontal),
            model_dir=mdl.get("dir", cls.model_dir),
            default_model=mdl.get("default", cls.default_model),
            confidence_threshold=mdl.get("confidence_threshold", cls.confidence_threshold),
            device=mdl.get("device", cls.device),
            smoothing_frames=ges.get("smoothing_frames", cls.smoothing_frames),
            hold_duration_ms=ges.get("hold_duration_ms", cls.hold_duration_ms),
            theme=ui.get("theme", cls.theme),
            overlay_opacity=ui.get("overlay_opacity", cls.overlay_opacity),
            show_landmarks=ui.get("show_landmarks", cls.show_landmarks),
            show_fps=ui.get("show_fps", cls.show_fps),
            window_title=ui.get("window_title", cls.window_title),
            log_level=log.get("level", cls.log_level),
            log_dir=log.get("dir", cls.log_dir),
        )
