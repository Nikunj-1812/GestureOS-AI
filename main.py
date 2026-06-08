"""
GestureOS AI — Canonical Application Entry Point
=================================================
All startup paths now converge here.

FIX ARCH-001 / BUG-001:
  Previously main.py launched ui/app_window.py (AppWindow) — a legacy,
  feature-incomplete window class.  The active window is GestureOSApp
  in dashboard/shell/window.py which has keyboard shortcuts, navigation
  history, and the gesture pipeline hook.

  ui/app_window.py is retained for reference but is no longer the
  startup target.  Running either:
      python main.py
      python run_dashboard.py
  now starts the same GestureOSApp window.
"""

import sys
from pathlib import Path

# Ensure the project root is always on sys.path regardless of where
# the interpreter is launched from.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dashboard.shell.window import main

if __name__ == "__main__":
    main()
