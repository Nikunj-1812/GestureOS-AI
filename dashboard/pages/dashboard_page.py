"""
GestureOS AI — Dashboard Page
==============================
Modern home screen with:
  • Live camera preview area
  • Clickable module cards
  • Clean, responsive dashboard layout
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.components.widgets import Badge, CameraFeed, SectionTitle
from dashboard.pages.base_page import BasePage
from dashboard.theme import COLORS, FONTS, SIZES


class DashboardPage(BasePage):
    PAGE_KEY = "dashboard"
    PAGE_TITLE = "Dashboard"
    PAGE_ICON = "⊞"

    def __init__(self, master, on_navigate: callable | None = None, **kwargs) -> None:
        self._on_navigate = on_navigate
        super().__init__(master, **kwargs)

    def _build(self) -> None:
        pad = SIZES["pad_lg"]
        self.grid_columnconfigure(0, weight=1)

        banner = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        banner.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        banner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            banner,
            text="Dashboard",
            font=ctk.CTkFont("Segoe UI", 26, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=pad, pady=(pad, 4), sticky="w")

        ctk.CTkLabel(
            banner,
            text="Monitor the camera feed and launch GestureOS modules from one control surface.",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["overlay1"],
            anchor="w",
        ).grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="w")

        Badge(banner, text="System Ready", color=COLORS["green"]).grid(
            row=0, column=1, rowspan=2, padx=pad, pady=pad, sticky="e"
        )

        SectionTitle(
            self,
            "Live Camera Preview",
            "A dedicated preview area for the active camera feed.",
        ).grid(row=1, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"]))

        preview_shell = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface0"],
            corner_radius=24,
            border_width=SIZES["border_w"],
            border_color=COLORS["card_border"],
        )
        preview_shell.grid(row=2, column=0, sticky="ew", padx=pad, pady=0)
        preview_shell.grid_columnconfigure(0, weight=1)

        preview_header = ctk.CTkFrame(preview_shell, fg_color="transparent")
        preview_header.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        preview_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_header,
            text="Live Camera Preview Area",
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        Badge(preview_header, text="Camera Feed", color=COLORS["accent"]).grid(
            row=0, column=1, sticky="e"
        )

        self._camera_feed = CameraFeed(preview_shell, width=1080, height=420)
        self._camera_feed.grid(
            row=1, column=0,
            sticky="nsew",
            padx=pad,
            pady=(SIZES["pad_md"], pad),
        )

        SectionTitle(
            self,
            "Modules",
            "Clickable cards for the main GestureOS AI tools.",
        ).grid(row=3, column=0, sticky="ew", padx=pad, pady=(pad, SIZES["pad_sm"]))

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=4, column=0, sticky="ew", padx=pad, pady=(0, pad))
        for column in range(4):
            cards_frame.grid_columnconfigure(column, weight=1, uniform="module")

        cards = [
            ("⊹", "Virtual Mouse", "Cursor and click control", "virtual_mouse", COLORS["blue"]),
            ("⌨", "Virtual Keyboard", "On-screen text entry", "virtual_keyboard", COLORS["sapphire"]),
            ("✏", "Air Drawing", "Sketch gestures in the air", "air_drawing", COLORS["mauve"]),
            ("▶", "Media Control", "Play and pause media", "media_control", COLORS["green"]),
            ("⚙", "System Control", "System shortcuts and actions", "system_control", COLORS["peach"]),
            ("◈", "Gesture Training", "Train custom gestures", "gesture_training", COLORS["yellow"]),
            ("▦", "Analytics", "Usage and performance insights", "analytics", COLORS["sky"]),
            ("≡", "Settings", "Application preferences", "settings", COLORS["rosewater"]),
        ]

        for index, (icon, title, subtitle, key, accent) in enumerate(cards):
            row = index // 4
            column = index % 4
            card = _ModuleCard(
                cards_frame,
                icon=icon,
                title=title,
                subtitle=subtitle,
                accent=accent,
                command=lambda page_key=key: self._navigate(page_key),
            )
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, SIZES["pad_sm"]) if column < 3 else 0,
                pady=(0, SIZES["pad_sm"]) if row == 0 else 0,
            )

    def _navigate(self, key: str) -> None:
        if self._on_navigate is not None:
            self._on_navigate(key)

    def set_camera_frame(self, frame) -> None:
        """Updates the live camera preview frame."""
        self._camera_feed.set_frame(frame)

    def clear_camera_frame(self) -> None:
        """Resets the live camera preview back to its placeholder."""
        self._camera_feed.clear()


class _ModuleCard(ctk.CTkButton):
    """Clickable dashboard shortcut card."""

    def __init__(self, master, icon: str, title: str, subtitle: str, accent: str, command: callable, **kwargs) -> None:
        super().__init__(
            master,
            text="",
            command=command,
            fg_color=COLORS["surface0"],
            hover_color=COLORS["surface1"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["card_border"],
            height=140,
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        icon_shell = ctk.CTkFrame(
            self,
            width=42,
            height=42,
            corner_radius=14,
            fg_color=COLORS["base"],
        )
        icon_shell.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        icon_shell.grid_propagate(False)

        ctk.CTkLabel(
            icon_shell,
            text=icon,
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=accent,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
            anchor="w",
            justify="left",
            wraplength=210,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))