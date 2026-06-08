"""
GestureOS AI — Dashboard Page Registry
======================================
Central mapping between navigation keys and page classes.
"""

from __future__ import annotations

from dashboard.pages.air_drawing_page import AirDrawingPage
from dashboard.pages.analytics_page import AnalyticsPage
from dashboard.pages.dashboard_page import DashboardPage
from dashboard.pages.gesture_training_page import GestureTrainingPage
from dashboard.pages.media_control_page import MediaControlPage
from dashboard.pages.settings_page import SettingsPage
from dashboard.pages.system_control_page import SystemControlPage
from dashboard.pages.virtual_keyboard_page import VirtualKeyboardPage
from dashboard.pages.virtual_mouse_page import VirtualMousePage

from .navigation import NAV_PAGES

PAGE_CLASSES: dict[str, type] = {
    "dashboard": DashboardPage,
    "virtual_mouse": VirtualMousePage,
    "virtual_keyboard": VirtualKeyboardPage,
    "air_drawing": AirDrawingPage,
    "media_control": MediaControlPage,
    "system_control": SystemControlPage,
    "gesture_training": GestureTrainingPage,
    "analytics": AnalyticsPage,
    "settings": SettingsPage,
}

PAGE_TITLES: dict[str, str] = {
    "dashboard": "Dashboard",
    "virtual_mouse": "Mouse Page",
    "virtual_keyboard": "Keyboard Page",
    "air_drawing": "Drawing Page",
    "media_control": "Media Page",
    "system_control": "System Page",
    "gesture_training": "Training Page",
    "analytics": "Analytics Page",
    "settings": "Settings Page",
}