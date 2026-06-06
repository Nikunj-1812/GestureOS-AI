"""
GestureOS AI — Dashboard Launcher
===================================
Run this file to start the CustomTkinter dashboard:

    python run_dashboard.py

Requirements:
    pip install customtkinter==5.2.2
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so dashboard package is importable
sys.path.insert(0, str(Path(__file__).parent))

from dashboard.app import main

if __name__ == "__main__":
    main()
