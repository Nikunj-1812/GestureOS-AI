"""
GestureOS AI — Sidebar Navigation Component
=============================================
A collapsible left sidebar with:
  • App logo + name at the top
  • Grouped navigation items with section headers
  • Active item highlight
  • Hover effect
  • Collapse / expand toggle button at the bottom
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.theme import COLORS, FONTS, SIZES, NAV_PAGES


class SidebarNav(ctk.CTkFrame):
    """
    Left sidebar navigation panel.

    Args:
        master      : Parent widget.
        on_navigate : Callback(page_key: str) called when a nav item is clicked.
    """

    def __init__(self, master, on_navigate: callable, **kwargs) -> None:
        super().__init__(
            master,
            width=SIZES["sidebar_w"],
            corner_radius=0,
            fg_color=COLORS["nav_bg"],
            **kwargs,
        )
        self.on_navigate = on_navigate
        self._active_key: str = "dashboard"
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self.grid_rowconfigure(1, weight=1)   # nav area expands
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

        self._build_logo()
        self._build_nav()
        self._build_collapse_btn()

    # ──────────────────────────────────────────────────────────────
    # Logo area
    # ──────────────────────────────────────────────────────────────

    def _build_logo(self) -> None:
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=72)
        logo_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        logo_frame.grid_propagate(False)
        logo_frame.grid_columnconfigure(0, weight=1)

        # Accent dot
        dot = ctk.CTkLabel(
            logo_frame,
            text="●",
            font=ctk.CTkFont("Segoe UI", 18),
            text_color=COLORS["accent"],
        )
        dot.grid(row=0, column=0, padx=(20, 4), pady=(20, 0), sticky="w")

        # App name
        name = ctk.CTkLabel(
            logo_frame,
            text="GestureOS AI",
            font=ctk.CTkFont(*FONTS["title"]),
            text_color=COLORS["text"],
            anchor="w",
        )
        name.grid(row=0, column=0, padx=(44, 8), pady=(20, 0), sticky="w")

        # Version tag
        version = ctk.CTkLabel(
            logo_frame,
            text="v1.0.0",
            font=ctk.CTkFont(*FONTS["badge"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        version.grid(row=1, column=0, padx=(20, 8), pady=(0, 10), sticky="w")

        # Divider under logo
        divider = ctk.CTkFrame(
            logo_frame,
            height=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
        )
        divider.grid(row=2, column=0, sticky="ew", padx=12, pady=0)

    # ──────────────────────────────────────────────────────────────
    # Navigation items
    # ──────────────────────────────────────────────────────────────

    def _build_nav(self) -> None:
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["surface1"],
            scrollbar_button_hover_color=COLORS["surface2"],
            corner_radius=0,
        )
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(8, 0))
        scroll_frame.grid_columnconfigure(0, weight=1)

        current_section = None

        for page in NAV_PAGES:
            # ── Section header ─────────────────────────────────────
            if page["section"] != current_section:
                current_section = page["section"]

                section_label = ctk.CTkLabel(
                    scroll_frame,
                    text=current_section,
                    font=ctk.CTkFont(*FONTS["badge"]),
                    text_color=COLORS["overlay0"],
                    anchor="w",
                )
                section_label.grid(
                    row=scroll_frame.grid_size()[1],
                    column=0,
                    sticky="ew",
                    padx=(20, 8),
                    pady=(14, 2),
                )

            # ── Nav button ─────────────────────────────────────────
            btn = ctk.CTkButton(
                scroll_frame,
                text=f"  {page['icon']}   {page['label']}",
                font=ctk.CTkFont(*FONTS["nav_item"]),
                anchor="w",
                height=SIZES["nav_item_h"],
                corner_radius=8,
                border_width=0,
                fg_color="transparent",
                hover_color=COLORS["nav_hover"],
                text_color=COLORS["subtext1"],
                command=lambda k=page["key"]: self._on_click(k),
            )
            btn.grid(
                row=scroll_frame.grid_size()[1],
                column=0,
                sticky="ew",
                padx=10,
                pady=1,
            )
            self._nav_buttons[page["key"]] = btn

        # Set initial active item
        self.set_active("dashboard")

    # ──────────────────────────────────────────────────────────────
    # Bottom section — exit button
    # ──────────────────────────────────────────────────────────────

    def _build_collapse_btn(self) -> None:
        # Divider above bottom section
        ctk.CTkFrame(
            self,
            height=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
        ).grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 0))

        # Bottom frame
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=(6, 12))
        bottom.grid_columnconfigure(0, weight=1)

        # Exit button — red, calls root window _on_exit
        ctk.CTkButton(
            bottom,
            text="  ✕   Exit",
            font=ctk.CTkFont(*FONTS["nav_item"]),
            anchor="w",
            height=SIZES["nav_item_h"],
            corner_radius=8,
            border_width=0,
            fg_color="transparent",
            hover_color="#3d1f24",
            text_color=COLORS["red"],
            command=self._exit,
        ).grid(row=0, column=0, sticky="ew")

    def _exit(self) -> None:
        """Delegates exit to the root GestureOSApp window."""
        root = self.winfo_toplevel()
        if hasattr(root, "_on_exit"):
            root._on_exit()
        else:
            root.destroy()

    # ──────────────────────────────────────────────────────────────
    # State management
    # ──────────────────────────────────────────────────────────────

    def _on_click(self, key: str) -> None:
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key: str) -> None:
        """Highlights the active nav item and resets the previous one."""
        # Reset previous
        if self._active_key in self._nav_buttons:
            prev = self._nav_buttons[self._active_key]
            prev.configure(
                fg_color="transparent",
                text_color=COLORS["subtext1"],
                font=ctk.CTkFont(*FONTS["nav_item"]),
            )

        # Highlight new
        self._active_key = key
        if key in self._nav_buttons:
            btn = self._nav_buttons[key]
            btn.configure(
                fg_color=COLORS["surface0"],
                text_color=COLORS["nav_active"],
                font=ctk.CTkFont(*FONTS["nav_active"]),
            )
