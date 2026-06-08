"""
GestureOS AI — Dashboard Pages
==============================
Exports the page classes used by the dashboard shell.
"""

from .air_drawing_page import AirDrawingPage
from .analytics_page import AnalyticsPage
from .base_page import BasePage
from .dashboard_page import DashboardPage
from .gesture_training_page import GestureTrainingPage
from .media_control_page import MediaControlPage
from .settings_page import SettingsPage
from .system_control_page import SystemControlPage
from .virtual_keyboard_page import VirtualKeyboardPage
from .virtual_mouse_page import VirtualMousePage

__all__ = [
	"AirDrawingPage",
	"AnalyticsPage",
	"BasePage",
	"DashboardPage",
	"GestureTrainingPage",
	"MediaControlPage",
	"SettingsPage",
	"SystemControlPage",
	"VirtualKeyboardPage",
	"VirtualMousePage",
]
