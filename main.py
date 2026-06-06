"""
GestureOS AI — Application Entry Point
Initializes configuration, camera feed, gesture engine, and UI.
"""

import sys
from loguru import logger
from dotenv import load_dotenv

from config.app_config import AppConfig
from modules.gesture_engine import GestureEngine
from modules.camera import CameraStream
from ui.app_window import AppWindow


def main() -> None:
    # Load environment variables
    load_dotenv()

    # Load app configuration
    config = AppConfig.from_yaml("config/settings.yaml")

    # Configure logging
    logger.add(
        f"{config.log_dir}/gestureos_{{time}}.log",
        level=config.log_level,
        rotation="10 MB",
        retention="7 days",
    )
    logger.info("Starting GestureOS AI...")

    # Initialize core components
    camera = CameraStream(
        index=config.camera_index,
        width=config.camera_width,
        height=config.camera_height,
        fps=config.camera_fps,
    )
    engine = GestureEngine(model_path=config.default_model)

    # Launch UI
    app = AppWindow(camera=camera, engine=engine, config=config)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
