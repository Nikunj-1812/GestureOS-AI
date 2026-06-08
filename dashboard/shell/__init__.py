"""
GestureOS AI — Dashboard Shell Package
======================================
Coordinates the dashboard window, navigation metadata, and page registry.
"""

from .navigation import NAV_PAGES
from .page_registry import PAGE_CLASSES, PAGE_TITLES
from .window import GestureOSApp, main

__all__ = [
    "NAV_PAGES",
    "PAGE_CLASSES",
    "PAGE_TITLES",
    "GestureOSApp",
    "main",
]