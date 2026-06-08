"""
GestureOS AI — Top Header Component
===================================
Modern dashboard header containing:
  • Project logo and title
  • Current profile
  • Current mode
  • Notifications icon
  • Settings icon
  • Exit button
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.theme import COLORS, FONTS, SIZES


class TopHeader(ctk.CTkFrame):
    """Top header bar fixed above the main dashboard content."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            height=SIZES["header_h"],
            corner_radius=0,
            fg_color=COLORS["header_bg"],
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        self._page_title = "Dashboard"
        self._profile_name = "Admin"
        self._mode_name = "Live Mode"
        self._compact_mode = False

        self._build()
        self.bind("<Configure>", self._on_resize)

    def _build(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(20, 12), pady=0)
        left.grid_columnconfigure(1, weight=1)

        logo_box = ctk.CTkFrame(
            left,
            width=46,
            height=46,
            corner_radius=14,
            fg_color=COLORS["surface0"],
            border_width=1,
            border_color=COLORS["divider"],
        )
        logo_box.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 14), pady=15)
        logo_box.grid_propagate(False)

        ctk.CTkLabel(
            logo_box,
            text="✦",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=COLORS["accent"],
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.grid(row=0, column=1, sticky="w", pady=(14, 0))

        ctk.CTkLabel(
            title_row,
            text="GestureOS AI",
            font=ctk.CTkFont(*FONTS["title"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._page_label = ctk.CTkLabel(
            title_row,
            text=self._page_title,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        self._page_label.grid(row=1, column=0, sticky="w", pady=(1, 0))

        self._profile_chip = _InfoChip(
            self,
            icon="◉",
            label="Profile",
            value=self._profile_name,
            accent=COLORS["blue"],
        )
        self._profile_chip.grid(row=0, column=1, sticky="e", padx=8, pady=16)

        self._mode_chip = _InfoChip(
            self,
            icon="◈",
            label="Mode",
            value=self._mode_name,
            accent=COLORS["green"],
        )
        self._mode_chip.grid(row=0, column=2, sticky="e", padx=(0, 8), pady=16)

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=3, sticky="e", padx=(0, 20), pady=0)

        self._notifications_btn = _ActionButton(right, text="🔔")
        self._notifications_btn.grid(row=0, column=0, padx=(0, 8), pady=20)

        self._settings_btn = _ActionButton(right, text="⚙")
        self._settings_btn.grid(row=0, column=1, padx=(0, 10), pady=20)

        self._exit_btn = ctk.CTkButton(
            right,
            text="Exit ✕",
            font=ctk.CTkFont(*FONTS["badge"]),
            height=34,
            corner_radius=10,
            border_width=0,
            fg_color="#3d1f24",
            hover_color=COLORS["red"],
            text_color=COLORS["rosewater"],
            command=self._exit_app,
        )
        self._exit_btn.grid(row=0, column=2, pady=20)

        border = ctk.CTkFrame(
            self,
            height=SIZES["divider_h"],
            fg_color=COLORS["divider"],
            corner_radius=0,
        )
        border.grid(row=1, column=0, columnspan=4, sticky="ew", padx=0, pady=0)

    def set_page(self, title: str, breadcrumb: str = "") -> None:
        """Update the subtitle shown under the brand title."""
        self._page_title = breadcrumb or title
        self._page_label.configure(text=self._page_title)

    def set_profile(self, profile: str) -> None:
        """Update the current profile label."""
        self._profile_name = profile
        self._profile_chip.set_value(profile)

    def set_mode(self, mode: str) -> None:
        """Update the current mode label."""
        self._mode_name = mode
        self._mode_chip.set_value(mode)

    def set_camera_status(self, active: bool) -> None:
        """Kept for compatibility with the existing shell API."""
        self._mode_chip.set_accent(COLORS["green"] if active else COLORS["overlay0"])

    def set_system_status(self, status: str) -> None:
        """Kept for compatibility with the existing shell API."""
        self._mode_chip.set_accent(_InfoChip.STATUS_COLORS.get(status, COLORS["green"]))

    def _exit_app(self) -> None:
        root = self.winfo_toplevel()
        if hasattr(root, "_on_exit"):
            root._on_exit()
        else:
            root.destroy()

    def _on_resize(self, event) -> None:
        compact = getattr(event, "width", 0) < 1480
        if compact == self._compact_mode:
            return

        self._compact_mode = compact
        self._profile_chip.toggle_compact(compact)
        self._mode_chip.toggle_compact(compact)
        self._notifications_btn.configure(text="🔔" if not compact else "🔔")
        self._settings_btn.configure(text="⚙" if not compact else "⚙")
        self._exit_btn.configure(text="Exit ✕" if not compact else "✕")

class _InfoChip(ctk.CTkFrame):
    """Small dashboard chip with icon, label, and value."""

    STATUS_COLORS = {
        "ok": COLORS["status_ok"],
        "warn": COLORS["status_warn"],
        "err": COLORS["status_err"],
        "off": COLORS["overlay0"],
    }

    def __init__(self, master, icon: str, label: str, value: str, accent: str, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface0"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["divider"],
            **kwargs,
        )
        self._compact = False
        self._accent = accent
        self.grid_columnconfigure(1, weight=1)

        self._icon = ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=accent,
        )
        self._icon.grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=8)

        self._label = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(*FONTS["badge"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        )
        self._label.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(8, 0))

        self._value = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="w",
        )
        self._value.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=(0, 8))

    def set_value(self, value: str) -> None:
        self._value.configure(text=value)

    def set_accent(self, color: str) -> None:
        self._icon.configure(text_color=color)
        self._value.configure(text_color=color)

    def toggle_compact(self, compact: bool) -> None:
        self._compact = compact
        if compact:
            self._label.grid_remove()
            self._value.configure(font=ctk.CTkFont(*FONTS["badge"]))
        else:
            self._label.grid()
            self._value.configure(font=ctk.CTkFont(*FONTS["body_bold"]))


class _ActionButton(ctk.CTkButton):
    """Rounded icon button used for header actions."""

    def __init__(self, master, text: str, **kwargs) -> None:
        super().__init__(
            master,
            text=text,
            width=38,
            height=34,
            corner_radius=10,
            fg_color=COLORS["surface0"],
            hover_color=COLORS["surface1"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["divider"],
            font=ctk.CTkFont("Segoe UI", 14),
            command=lambda: None,
            **kwargs,
        )