"""Unit tests for AppConfig loading."""

import pytest
from config.app_config import AppConfig


def test_defaults():
    config = AppConfig()
    assert config.camera_fps == 30
    assert config.theme == "dark"
    assert config.confidence_threshold == 0.75


def test_from_yaml_missing_file():
    with pytest.raises(FileNotFoundError):
        AppConfig.from_yaml("nonexistent/path/settings.yaml")


def test_from_yaml_loads_correctly(tmp_path):
    yaml_content = """
app:
  name: "Test App"
  version: "2.0.0"
  debug: true
camera:
  fps: 60
model:
  confidence_threshold: 0.9
ui:
  theme: "light"
logging:
  level: "DEBUG"
"""
    cfg_file = tmp_path / "settings.yaml"
    cfg_file.write_text(yaml_content)
    config = AppConfig.from_yaml(str(cfg_file))

    assert config.app_name == "Test App"
    assert config.camera_fps == 60
    assert config.confidence_threshold == 0.9
    assert config.theme == "light"
    assert config.debug is True
