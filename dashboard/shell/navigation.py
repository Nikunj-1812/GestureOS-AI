"""
GestureOS AI — Dashboard Navigation Definition
===============================================
Navigation metadata for the CustomTkinter sidebar.
"""

from __future__ import annotations

NAV_PAGES = [
    {"key": "dashboard", "label": "Dashboard", "icon": "⊞", "section": "MAIN"},
    {"key": "virtual_mouse", "label": "Virtual Mouse", "icon": "⊹", "section": "CONTROL"},
    {"key": "virtual_keyboard", "label": "Virtual Keyboard", "icon": "⌨", "section": "CONTROL"},
    {"key": "air_drawing", "label": "Air Drawing", "icon": "✏", "section": "CONTROL"},
    {"key": "media_control", "label": "Media Control", "icon": "▶", "section": "CONTROL"},
    {"key": "system_control", "label": "System Control", "icon": "⚙", "section": "CONTROL"},
    {"key": "gesture_training", "label": "Gesture Training", "icon": "◈", "section": "INTELLIGENCE"},
    {"key": "analytics", "label": "Analytics", "icon": "▦", "section": "INTELLIGENCE"},
    {"key": "settings", "label": "Settings", "icon": "≡", "section": "CONFIG"},
]