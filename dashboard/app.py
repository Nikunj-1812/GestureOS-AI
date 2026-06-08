"""
GestureOS AI — Dashboard Entry Point
====================================
Canonical thin wrapper around the dashboard shell.
Delegates directly to GestureOSApp via the shell main().

FIX BUG-001: Removed duplicate main() definition. The second
shadowed-and-dead implementation has been deleted. There is now
exactly one main() and one if __name__ guard.
"""

from __future__ import annotations

from dashboard.shell.window import main


if __name__ == "__main__":
    main()
