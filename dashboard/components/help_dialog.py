"""
GestureOS AI — Help Dialog
===========================
Modal overlay listing all global keyboard shortcuts.
Triggered via F1 or the Help action.
"""

from __future__ import annotations

import customtkinter as ctk

from dashboard.theme import COLORS, FONTS, SIZES


# Keyboard shortcuts shown in the dialog
_SHORTCUTS: list[tuple[str, str]] = [
    ("F1",  "Show this Help dialog"),
    ("H",   "Go to Home / Dashboard"),
    ("ESC", "Go back to previous page"),
    ("Q",   "Quit the application"),
]


class HelpDialog(ctk.CTkToplevel):
    """
    Modal help window listing global keyboard shortcuts.

    Usage::

        HelpDialog(parent)          # blocks until closed
        HelpDialog(parent).wait()   # explicit wait
    """

    def __init__(self, master) -> None:
        super().__init__(master)

        self.title("Keyboard Shortcuts — GestureOS AI")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["base"])

        # Keep on top of the parent window
        self.transient(master)
        self.grab_set()

        self._build()
        self._centre(400, 360)

        # Close on Escape or F1
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<F1>",     lambda _e: self.destroy())

    # ------------------------------------------------------------------ #
    #  Layout                                                              #
    # ------------------------------------------------------------------ #

    def _build(self) -> None:
        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=COLORS["crust"], corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="⌨  Keyboard Shortcuts",
            font=ctk.CTkFont(*FONTS["heading"]),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(side="left", padx=SIZES["pad_lg"], pady=SIZES["pad_md"])

        ctk.CTkButton(
            header,
            text="✕",
            width=32,
            height=32,
            corner_radius=8,
            fg_color=COLORS["surface0"],
            hover_color=COLORS["red"],
            text_color=COLORS["text"],
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self.destroy,
        ).pack(side="right", padx=SIZES["pad_md"], pady=SIZES["pad_md"])

        # ── Divider ───────────────────────────────────────────────────────
        ctk.CTkFrame(
            self, height=SIZES["divider_h"], fg_color=COLORS["divider"], corner_radius=0
        ).pack(fill="x")

        # ── Shortcut rows ────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SIZES["pad_lg"], pady=SIZES["pad_lg"])
        body.grid_columnconfigure(1, weight=1)

        for row_idx, (key, description) in enumerate(_SHORTCUTS):
            # Key badge
            badge_frame = ctk.CTkFrame(
                body,
                fg_color=COLORS["surface0"],
                corner_radius=SIZES["btn_radius"],
                border_width=SIZES["border_w"],
                border_color=COLORS["accent"],
            )
            badge_frame.grid(row=row_idx, column=0, sticky="w", padx=(0, SIZES["pad_md"]), pady=6)

            ctk.CTkLabel(
                badge_frame,
                text=key,
                font=ctk.CTkFont("Courier New", 13, "bold"),
                text_color=COLORS["accent"],
                width=52,
                anchor="center",
            ).pack(padx=SIZES["pad_sm"], pady=5)

            # Description
            ctk.CTkLabel(
                body,
                text=description,
                font=ctk.CTkFont(*FONTS["body"]),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=row_idx, column=1, sticky="w", pady=6)

        # ── Footer hint ───────────────────────────────────────────────────
        ctk.CTkFrame(
            self, height=SIZES["divider_h"], fg_color=COLORS["divider"], corner_radius=0
        ).pack(fill="x", pady=(0, 0))

        ctk.CTkLabel(
            self,
            text="Press  F1  or  ESC  to close",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["overlay1"],
        ).pack(pady=SIZES["pad_md"])

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _centre(self, w: int, h: int) -> None:
        self.update_idletasks()
        parent = self.master
        px = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, px)}+{max(0, py)}")

    def wait(self) -> None:
        """Block until the dialog is closed."""
        self.wait_window(self)
