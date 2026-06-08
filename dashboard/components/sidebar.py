"""
GestureOS AI — Sidebar Navigation Component
=============================================
A professional left sidebar with:
    • Brand header at the top
    • Grouped navigation items with section labels
    • Active item highlight and hover state
    • Responsive width adaptation
    • Exit action anchored at the bottom
"""

from __future__ import annotations
import customtkinter as ctk
from dashboard.shell.navigation import NAV_PAGES
from dashboard.theme import COLORS, FONTS, SIZES


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
        self._compact_mode = False

        self.grid_rowconfigure(1, weight=1)   # nav area expands
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

        self.bind("<Configure>", self._on_resize)

        self._build_logo()
        self._build_nav()
        self._build_collapse_btn()

    # ──────────────────────────────────────────────────────────────
    # Logo area
    # ──────────────────────────────────────────────────────────────

    def _build_logo(self) -> None:
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=88)
        logo_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        logo_frame.grid_propagate(False)
        logo_frame.grid_columnconfigure(0, weight=1)

        brand_chip = ctk.CTkFrame(
            logo_frame,
            fg_color=COLORS["surface0"],
            corner_radius=18,
            height=56,
        )
        brand_chip.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")
        brand_chip.grid_propagate(False)
        brand_chip.grid_columnconfigure(1, weight=1)

        accent = ctk.CTkFrame(
            brand_chip,
            width=12,
            fg_color=COLORS["accent"],
            corner_radius=6,
        )
        accent.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10, sticky="ns")

        # App name
        name = ctk.CTkLabel(
            brand_chip,
            text="GestureOS AI",
            font=ctk.CTkFont(*FONTS["title"]),
            text_color=COLORS["text"],
            anchor="w",
        )
        name.grid(row=0, column=1, padx=(0, 12), pady=(10, 0), sticky="w")

        version = ctk.CTkLabel(
            brand_chip,
            text="v1.0.0",
            font=ctk.CTkFont(*FONTS["badge"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        version.grid(row=1, column=1, padx=(0, 12), pady=(0, 10), sticky="w")

        divider = ctk.CTkFrame(
            logo_frame,
            height=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
        )
        divider.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 0))

    # ──────────────────────────────────────────────────────────────
    # Navigation items
    # ──────────────────────────────────────────────────────────────

    def _build_nav(self) -> None:
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["nav_bg"],
            scrollbar_button_color=COLORS["surface1"],
            scrollbar_button_hover_color=COLORS["surface2"],
            corner_radius=0,
        )
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(8, 0))
        scroll_frame.grid_columnconfigure(0, weight=1)

        current_section = None
        self._scroll_frame = scroll_frame

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
                    padx=(18, 8),
                    pady=(18, 4),
                )

            # ── Nav button ─────────────────────────────────────────
            icon_box = ctk.CTkFrame(
                scroll_frame,
                width=28,
                height=28,
                corner_radius=10,
                fg_color=COLORS["surface0"],
            )
            btn = ctk.CTkButton(
                scroll_frame,
                text=f"  {page['icon']}   {page['label']}",
                font=ctk.CTkFont(*FONTS["nav_item"]),
                anchor="w",
                height=SIZES["nav_item_h"],
                corner_radius=12,
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
                padx=12,
                pady=3,
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

        # FIX BUG-008: Previously two buttons were both placed at row=0,col=0
        # causing the second to overlay the first (one was invisible/dead).
        # Kept only the styled "Close App" button; removed the duplicate.
        ctk.CTkButton(
            bottom,
            text="  ✕   Close App",
            font=ctk.CTkFont(*FONTS["nav_item"]),
            anchor="w",
            height=SIZES["nav_item_h"],
            corner_radius=12,
            border_width=0,
            fg_color=COLORS["surface0"],
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

    # ──────────────────────────────────────────────────────────────
    # Responsive sizing
    # ──────────────────────────────────────────────────────────────

    def _on_resize(self, event) -> None:
        width = getattr(event, "width", SIZES["sidebar_w"])
        compact = width < 220

        if compact == self._compact_mode:
            return

        self._compact_mode = compact
        self.configure(width=180 if compact else SIZES["sidebar_w"])

        for page in NAV_PAGES:
            btn = self._nav_buttons.get(page["key"])
            if not btn:
                continue
            label = page["label"] if not compact else page["label"].split()[0]
            btn.configure(text=f"  {page['icon']}   {label}")
