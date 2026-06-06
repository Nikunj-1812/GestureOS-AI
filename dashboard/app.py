"""
GestureOS AI — Main Application Window
========================================
Entry point for the CustomTkinter dashboard.

Layout (1920 × 1080):
┌────────────────────────────────────────────────────────────────┐
│                       TOP HEADER  (56px)                       │
├───────────────┬────────────────────────────────────────────────┤
│               │                                                │
│  LEFT SIDEBAR │           MAIN CONTENT AREA                   │
│   (220px)     │         (scrollable page frame)               │
│               │                                                │
├───────────────┴────────────────────────────────────────────────┤
│                     FOOTER STATUS BAR (32px)                   │
└────────────────────────────────────────────────────────────────┘

Navigation flow:
  SidebarNav  ──on_navigate(key)──►  AppWindow._show_page(key)
                                          │
                                          ▼
                                   destroy old page
                                   create new page
                                   update header title

Run:
    python run_dashboard.py
    — or —
    python -m dashboard.app
"""

from __future__ import annotations

import sys
import customtkinter as ctk
from dashboard.theme import COLORS, FONTS, SIZES, NAV_PAGES
from dashboard.components.sidebar import SidebarNav
from dashboard.components.header import TopHeader
from dashboard.components.footer import FooterBar

# ── Page imports ──────────────────────────────────────────────────
from dashboard.pages.dashboard_page       import DashboardPage
from dashboard.pages.virtual_mouse_page   import VirtualMousePage
from dashboard.pages.virtual_keyboard_page import VirtualKeyboardPage
from dashboard.pages.air_drawing_page     import AirDrawingPage
from dashboard.pages.media_control_page   import MediaControlPage
from dashboard.pages.system_control_page  import SystemControlPage
from dashboard.pages.gesture_training_page import GestureTrainingPage
from dashboard.pages.analytics_page       import AnalyticsPage
from dashboard.pages.settings_page        import SettingsPage


# ── Page registry ─────────────────────────────────────────────────
PAGE_CLASSES: dict[str, type] = {
    "dashboard":        DashboardPage,
    "virtual_mouse":    VirtualMousePage,
    "virtual_keyboard": VirtualKeyboardPage,
    "air_drawing":      AirDrawingPage,
    "media_control":    MediaControlPage,
    "system_control":   SystemControlPage,
    "gesture_training": GestureTrainingPage,
    "analytics":        AnalyticsPage,
    "settings":         SettingsPage,
}

# ── Page title lookup ─────────────────────────────────────────────
PAGE_TITLES: dict[str, str] = {p["key"]: p["label"] for p in NAV_PAGES}


# ═════════════════════════════════════════════════════════════════
# Main Application Window
# ═════════════════════════════════════════════════════════════════

class GestureOSApp(ctk.CTk):
    """
    Root application window.

    Responsibilities:
      • Set up CustomTkinter appearance and colour theme
      • Build the fixed shell (header, sidebar, footer)
      • Manage page switching in the content area
      • Handle clean application exit
    """

    def __init__(self) -> None:
        # ── CustomTkinter global config ───────────────────────────
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        super().__init__()

        # ── Window setup ──────────────────────────────────────────
        self.title("GestureOS AI")
        self.geometry(f"{SIZES['window_w']}x{SIZES['window_h']}")
        self.minsize(1024, 640)
        self.configure(fg_color=COLORS["base"])

        # Centre window on screen
        self._centre_window(SIZES["window_w"], SIZES["window_h"])

        # Intercept the window close (X) button
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

        # Current active page instance
        self._current_page: ctk.CTkBaseClass | None = None
        self._current_key: str = "dashboard"

        # ── Build shell ───────────────────────────────────────────
        self._build_layout()

        # ── Show default page ─────────────────────────────────────
        self._show_page("dashboard")

    # ──────────────────────────────────────────────────────────────
    # Layout construction
    # ──────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """
        Creates the four fixed shell regions.

        Grid layout:
          row 0 — TopHeader    (spans all columns, fixed height)
          row 1 — SidebarNav   (column 0, expands vertically)
                  content area (column 1, expands in both axes)
          row 2 — FooterBar    (spans all columns, fixed height)
        """

        # Row/column weights
        self.grid_rowconfigure(0, weight=0)   # header  — fixed
        self.grid_rowconfigure(1, weight=1)   # content — expands
        self.grid_rowconfigure(2, weight=0)   # footer  — fixed
        self.grid_columnconfigure(0, weight=0)  # sidebar — fixed width
        self.grid_columnconfigure(1, weight=1)  # content — expands

        # ── Top header ────────────────────────────────────────────
        self._header = TopHeader(self)
        self._header.grid(
            row=0, column=0, columnspan=2,
            sticky="nsew",
        )

        # ── Left sidebar ──────────────────────────────────────────
        self._sidebar = SidebarNav(
            self,
            on_navigate=self._show_page,
        )
        self._sidebar.grid(
            row=1, column=0,
            sticky="nsew",
        )

        # ── Content area wrapper ──────────────────────────────────
        # A plain frame that acts as the mounting point for pages.
        # Pages fill this frame completely.
        self._content_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["base"],
            corner_radius=0,
        )
        self._content_frame.grid(
            row=1, column=1,
            sticky="nsew",
        )
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=1)

        # ── Footer ────────────────────────────────────────────────
        self._footer = FooterBar(self)
        self._footer.grid(
            row=2, column=0, columnspan=2,
            sticky="nsew",
        )

    # ──────────────────────────────────────────────────────────────
    # Page switching
    # ──────────────────────────────────────────────────────────────

    def _show_page(self, key: str) -> None:
        """
        Destroys the current page and instantiates the requested one.

        Steps:
          1. Call on_leave() on the outgoing page (lifecycle hook)
          2. Destroy the outgoing page widget
          3. Create the new page in _content_frame
          4. Call on_enter() on the new page
          5. Update header title + breadcrumb
          6. Update sidebar active state
          7. Update footer status message
        """
        if key not in PAGE_CLASSES:
            return

        # ── Teardown outgoing page ────────────────────────────────
        if self._current_page is not None:
            try:
                self._current_page.on_leave()
            except Exception:
                pass
            self._current_page.destroy()
            self._current_page = None

        # ── Build new page ────────────────────────────────────────
        PageClass = PAGE_CLASSES[key]
        page = PageClass(self._content_frame)
        page.grid(row=0, column=0, sticky="nsew")
        self._current_page = page
        self._current_key  = key

        # Lifecycle hook
        try:
            page.on_enter()
        except Exception:
            pass

        # ── Update shell components ───────────────────────────────
        title = PAGE_TITLES.get(key, key.replace("_", " ").title())
        self._header.set_page(title)
        self._sidebar.set_active(key)
        self._footer.set_status(f"Viewing  {title}", level="ok")

    # ──────────────────────────────────────────────────────────────
    # Window helpers
    # ──────────────────────────────────────────────────────────────

    def _centre_window(self, w: int, h: int) -> None:
        """Positions the window in the centre of the primary monitor."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ──────────────────────────────────────────────────────────────
    # Exit
    # ──────────────────────────────────────────────────────────────

    def _on_exit(self) -> None:
        """
        Clean application shutdown.
        Called by the window's X button and by any 'Exit' button
        in the UI that invokes  app._on_exit()  or  app.destroy().
        """
        # Notify current page
        if self._current_page is not None:
            try:
                self._current_page.on_leave()
            except Exception:
                pass

        self.destroy()
        sys.exit(0)


# ═════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════

def main() -> None:
    app = GestureOSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
