"""
GestureOS AI — Dashboard Theme & Design Tokens
================================================
Single source of truth for all colours, fonts, spacing, and sizes
used across the entire CustomTkinter dashboard.

Import this module anywhere with:
    from dashboard.theme import COLORS, FONTS, SIZES
"""

# ─────────────────────────────────────────────────────────────────
# COLOUR PALETTE  (Catppuccin Mocha-inspired dark theme)
# ─────────────────────────────────────────────────────────────────

COLORS = {
    # ── Base layers ──────────────────────────────────────────────
    "base":          "#1e1e2e",   # deepest background (app bg)
    "mantle":        "#181825",   # sidebar background
    "crust":         "#11111b",   # header / footer background
    "surface0":      "#313244",   # card / panel background
    "surface1":      "#45475a",   # raised card / hover bg
    "surface2":      "#585b70",   # border / divider
    "overlay0":      "#6c7086",   # placeholder / disabled text
    "overlay1":      "#7f849c",   # secondary text
    "overlay2":      "#9399b2",   # tertiary text

    # ── Text ─────────────────────────────────────────────────────
    "text":          "#cdd6f4",   # primary text
    "subtext1":      "#bac2de",   # secondary text
    "subtext0":      "#a6adc8",   # dim text

    # ── Accent colours ───────────────────────────────────────────
    "blue":          "#89b4fa",   # primary accent / active nav
    "lavender":      "#b4befe",   # secondary accent
    "sapphire":      "#74c7ec",   # info
    "sky":           "#89dceb",   # light accent
    "teal":          "#94e2d5",   # success alt
    "green":         "#a6e3a1",   # success / active
    "yellow":        "#f9e2af",   # warning
    "peach":         "#fab387",   # orange / highlight
    "maroon":        "#eba0ac",   # error alt
    "red":           "#f38ba8",   # error / danger
    "mauve":         "#cba6f7",   # purple accent
    "flamingo":      "#f2cdcd",   # pink
    "rosewater":     "#f5e0dc",   # lightest accent

    # ── Semantic aliases ─────────────────────────────────────────
    "accent":        "#89b4fa",   # == blue  — main brand accent
    "accent_hover":  "#74c7ec",   # == sapphire
    "nav_active":    "#89b4fa",   # sidebar active item
    "nav_hover":     "#313244",   # sidebar hover bg
    "nav_bg":        "#181825",   # sidebar background
    "header_bg":     "#11111b",   # top header background
    "footer_bg":     "#11111b",   # footer background
    "card_bg":       "#313244",   # stat card background
    "card_border":   "#45475a",   # stat card border
    "input_bg":      "#313244",   # input field background
    "btn_primary":   "#89b4fa",   # primary button
    "btn_hover":     "#74c7ec",   # primary button hover
    "btn_secondary": "#45475a",   # secondary button
    "divider":       "#45475a",   # separator line
    "status_ok":     "#a6e3a1",   # green status dot
    "status_warn":   "#f9e2af",   # yellow status dot
    "status_err":    "#f38ba8",   # red status dot
}

# ─────────────────────────────────────────────────────────────────
# FONTS
# ─────────────────────────────────────────────────────────────────

FONTS = {
    "app":        ("Segoe UI",  13),
    "small":      ("Segoe UI",  11),
    "body":       ("Segoe UI",  13),
    "body_bold":  ("Segoe UI",  13, "bold"),
    "label":      ("Segoe UI",  12),
    "heading":    ("Segoe UI",  16, "bold"),
    "title":      ("Segoe UI",  20, "bold"),
    "nav_item":   ("Segoe UI",  13),
    "nav_active": ("Segoe UI",  13, "bold"),
    "stat_value": ("Segoe UI",  28, "bold"),
    "stat_label": ("Segoe UI",  11),
    "footer":     ("Segoe UI",  11),
    "badge":      ("Segoe UI",  10, "bold"),
}

# ─────────────────────────────────────────────────────────────────
# SIZES  (pixels)
# ─────────────────────────────────────────────────────────────────

SIZES = {
    "window_w":      1920,
    "window_h":      1080,
    "sidebar_w":     280,
    "header_h":      80,
    "footer_h":      60,
    "nav_item_h":    44,
    "nav_icon_w":    32,
    "card_radius":   12,
    "btn_radius":    8,
    "input_radius":  8,
    "pad_xs":        4,
    "pad_sm":        8,
    "pad_md":        16,
    "pad_lg":        24,
    "pad_xl":        32,
    "stat_card_w":   180,
    "stat_card_h":   100,
    "icon_sm":       16,
    "icon_md":       20,
    "icon_lg":       28,
    "border_w":      1,
    "divider_h":     1,
}

