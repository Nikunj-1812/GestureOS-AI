"""
GestureOS AI — Professional Hand Tracking HUD
===============================================
A full-featured heads-up display combining every subsystem built
so far into one polished, production-quality UI.

LAYOUT  (1280 × 720 frame)
──────────────────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────────┐
  │ [TOP BAR]  GestureOS AI  ────────  mode chip  ──  datetime  │
  ├──────────────┬───────────────────────────────┬───────────────┤
  │  LEFT PANEL  │                               │  RIGHT PANEL  │
  │  System HUD  │     LIVE CAMERA FEED          │  Per-hand     │
  │  • FPS       │     + skeleton overlay        │  • Finger     │
  │  • Status    │     + bounding boxes          │    states     │
  │  • # hands   │     + crosshairs              │  • Conf bar   │
  │  • Avg conf  │                               │  • W×H        │
  │  • Mode      │                               │  (one card    │
  │  • Uptime    │                               │   per hand)   │
  ├──────────────┴───────────────────────────────┴───────────────┤
  │ [BOTTOM BAR]  FPS graph  ──  shortcut hints  ──  version     │
  └──────────────────────────────────────────────────────────────┘

MODES  (cycle with M key)
  TRACKING  → Skeleton + bounding boxes visible
  GESTURE   → Fingertip state rings + skeleton
  MINIMAL   → Skeleton only, panels hidden

CONTROLS
  Q  → Quit
  M  → Cycle mode
  H  → Toggle left/right side panels

Usage:
  python gesture_hud.py
  python gesture_hud.py --camera 1
  python gesture_hud.py --max-hands 1 --no-flip
"""

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — IMPORTS
# ═══════════════════════════════════════════════════════════════════

import argparse
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import cv2
import mediapipe as mp
import numpy as np


# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — MEDIAPIPE SETUP
# ═══════════════════════════════════════════════════════════════════

mp_hands = mp.solutions.hands


# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — CONSTANTS & COLOUR PALETTE
# ═══════════════════════════════════════════════════════════════════
#
# Design language: dark navy base, cyan/amber accents, green = good.
# All colours are (Blue, Green, Red) — OpenCV BGR order.
#
# Panel geometry constants are defined alongside colours so that
# changing the layout is a one-place edit.
# ───────────────────────────────────────────────────────────────────

APP_NAME    = "GestureOS AI"
VERSION     = "v1.0.0"

# ── Base palette ──────────────────────────────────────────────────
C_BG_DEEP   = (18,  18,  32 )   # deepest background layer
C_BG_PANEL  = (22,  24,  44 )   # panel background
C_BG_CARD   = (30,  32,  56 )   # card background inside panels
C_BORDER    = (55,  60,  100)   # subtle panel border
C_DIVIDER   = (40,  44,  72 )   # row dividers

# ── Text colours ──────────────────────────────────────────────────
C_TEXT_PRI  = (235, 235, 245)   # primary text (near white)
C_TEXT_SEC  = (140, 145, 175)   # secondary / dim labels
C_TEXT_DIM  = (80,  84,  120)   # very dim — decorative labels

# ── Accent colours ────────────────────────────────────────────────
C_CYAN      = (255, 220, 0  )   # accent cyan  (BGR: 255,220,0)
C_AMBER     = (0,   190, 255)   # accent amber (BGR: 0,190,255)
C_GREEN     = (80,  210, 80 )   # positive / UP
C_RED       = (60,  60,  220)   # negative / DOWN / alert
C_PURPLE    = (200, 100, 180)   # mode chip
C_YELLOW    = (0,   230, 230)   # crosshair / center

# ── Confidence colour thresholds ──────────────────────────────────
C_CONF_HI   = (80,  210, 80 )   # >= 90 %
C_CONF_MED  = (0,   190, 255)   # 70–90 %
C_CONF_LO   = (60,  60,  220)   # < 70 %

# ── Hand identity colours ─────────────────────────────────────────
C_RIGHT     = (0,   200, 255)   # amber-gold — right hand
C_LEFT      = (255, 160, 0  )   # cyan-blue  — left hand

# ── Skeleton ──────────────────────────────────────────────────────
C_BONE      = (100, 105, 150)   # muted bone lines
C_DOT       = (210, 215, 240)   # landmark dots
C_BLACK     = (0,   0,   0  )

# ── Layout ────────────────────────────────────────────────────────
TOP_BAR_H   = 40    # px — top bar height
BOT_BAR_H   = 36    # px — bottom bar height
LEFT_W      = 210   # px — left system panel width
RIGHT_W     = 220   # px — right hand-info panel width
PANEL_PAD   = 10    # px — inner panel padding
ROW_H       = 24    # px — standard row height

FONT        = cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD   = cv2.FONT_HERSHEY_DUPLEX
LINE_AA     = cv2.LINE_AA


# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — MODE ENUM
# ═══════════════════════════════════════════════════════════════════
#
# Three display modes control what skeleton/overlay is shown.
# Cycling is done with the M key in the main loop.
# ───────────────────────────────────────────────────────────────────

class Mode(Enum):
    TRACKING  = "TRACKING"   # Full skeleton + bounding boxes + crosshair
    GESTURE   = "GESTURE"    # Fingertip state rings + skeleton
    LANDMARK  = "LANDMARK"   # Numbered landmark dots (debug/study view)
    MINIMAL   = "MINIMAL"    # Skeleton only, panels hidden

MODE_CYCLE = [Mode.TRACKING, Mode.GESTURE, Mode.LANDMARK, Mode.MINIMAL]

MODE_COLORS = {
    Mode.TRACKING:  C_CYAN,
    Mode.GESTURE:   C_AMBER,
    Mode.LANDMARK:  (80, 200, 120),   # soft green
    Mode.MINIMAL:   C_PURPLE,
}


# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — LANDMARK ANATOMY & FINGER DETECTION
# ═══════════════════════════════════════════════════════════════════

FINGER_JOINTS: dict[str, tuple[int, int]] = {
    "Thumb":  (4,  3 ),   # tip, IP   — x-axis comparison
    "Index":  (8,  6 ),   # tip, PIP  — y-axis comparison
    "Middle": (12, 10),
    "Ring":   (16, 14),
    "Pinky":  (20, 18),
}
FINGERTIP_IDS = [4, 8, 12, 16, 20]


@dataclass
class FingerState:
    """UP/DOWN state for all 5 fingers on one hand."""
    thumb:  bool = False
    index:  bool = False
    middle: bool = False
    ring:   bool = False
    pinky:  bool = False

    @property
    def raised(self) -> int:
        return sum([self.thumb, self.index, self.middle, self.ring, self.pinky])

    def as_list(self) -> list[tuple[str, bool]]:
        return [
            ("Thumb",  self.thumb),
            ("Index",  self.index),
            ("Middle", self.middle),
            ("Ring",   self.ring),
            ("Pinky",  self.pinky),
        ]


def detect_fingers(hand_landmarks, hand_label: str) -> FingerState:
    """
    Returns UP/DOWN state per finger — improved accuracy.

    THUMB  : Distance-based. TIP must be far from both WRIST and IP.
             Handles front palm, back palm, fist, thumbs-up correctly.

    FINGERS: Dual-condition — tip must be ABOVE pip (y-axis) AND
             tip-to-mcp distance must exceed a curl threshold.
             This prevents false UP when finger is bent sideways.
    """
    import math
    lm = hand_landmarks.landmark

    def _d(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    # ── Thumb (distance-based, orientation-independent) ───────────────
    tip_dist  = _d(lm[4], lm[0])   # TIP  → WRIST
    ip_dist   = _d(lm[3], lm[0])   # IP   → WRIST
    tip_to_ip = _d(lm[4], lm[3])   # TIP  → IP
    thumb = (tip_dist > ip_dist + 0.04) and (tip_to_ip > 0.04)

    # ── Four fingers — dual condition for accuracy ────────────────────
    # Condition 1: tip.y < pip.y  (tip above PIP joint — extended)
    # Condition 2: tip-to-mcp distance > mcp-to-wrist * 0.6
    #              (ensures finger is actually stretched, not bent sideways)
    def finger_up(tip_id: int, pip_id: int, mcp_id: int) -> bool:
        y_check   = lm[tip_id].y < lm[pip_id].y - 0.01   # small hysteresis
        dist_check = _d(lm[tip_id], lm[mcp_id]) > _d(lm[mcp_id], lm[0]) * 0.55
        return y_check and dist_check

    return FingerState(
        thumb  = thumb,
        index  = finger_up(8,  6,  5),
        middle = finger_up(12, 10, 9),
        ring   = finger_up(16, 14, 13),
        pinky  = finger_up(20, 18, 17),
    )


# ═══════════════════════════════════════════════════════════════════
# SECTION 6 — HAND DATA DATACLASS
# ═══════════════════════════════════════════════════════════════════
#
# One HandData instance is built per detected hand each frame.
# It bundles all the computed values needed by every drawing function,
# avoiding repeated recalculation and messy parameter lists.
# ───────────────────────────────────────────────────────────────────

@dataclass
class HandData:
    """All computed values for one detected hand."""
    label:      str           # "Left" | "Right"
    confidence: float         # 0.0–1.0 from MediaPipe
    finger:     FingerState   # per-finger UP/DOWN
    landmarks:  object        # raw NormalizedLandmarkList
    # Bounding box (pixels)
    bx: int = 0; by: int = 0
    bw: int = 0; bh: int = 0
    cx: int = 0; cy: int = 0  # center

    @property
    def bx2(self) -> int: return self.bx + self.bw
    @property
    def by2(self) -> int: return self.by + self.bh
    @property
    def color(self) -> tuple:
        return C_RIGHT if self.label == "Right" else C_LEFT
    @property
    def conf_color(self) -> tuple:
        if self.confidence >= 0.90: return C_CONF_HI
        if self.confidence >= 0.70: return C_CONF_MED
        return C_CONF_LO


def build_hand_data(hand_landmarks, handedness,
                    frame_w: int, frame_h: int) -> HandData:
    """Computes all HandData fields from raw MediaPipe output."""
    label      = handedness.classification[0].label
    confidence = handedness.classification[0].score

    xs = [lm.x * frame_w for lm in hand_landmarks.landmark]
    ys = [lm.y * frame_h for lm in hand_landmarks.landmark]

    pad = 26
    bx = max(0,       int(min(xs)) - pad)
    by = max(0,       int(min(ys)) - pad)
    bx2 = min(frame_w, int(max(xs)) + pad)
    by2 = min(frame_h, int(max(ys)) + pad)
    bw = bx2 - bx
    bh = by2 - by

    return HandData(
        label      = label,
        confidence = confidence,
        finger     = detect_fingers(hand_landmarks, label),
        landmarks  = hand_landmarks,
        bx=bx, by=by, bw=bw, bh=bh,
        cx=bx + bw // 2,
        cy=by + bh // 2,
    )


# ═══════════════════════════════════════════════════════════════════
# SECTION 7 — FPS COUNTER + GRAPH DATA
# ═══════════════════════════════════════════════════════════════════

class FPSCounter:
    """Rolling-average FPS with history for the bottom graph."""

    def __init__(self, window: int = 30, history: int = 80) -> None:
        self._ts:      deque[float] = deque(maxlen=window)
        self.history:  deque[float] = deque(maxlen=history)

    def tick(self) -> float:
        self._ts.append(time.monotonic())
        if len(self._ts) < 2:
            fps = 0.0
        else:
            elapsed = self._ts[-1] - self._ts[0]
            fps = (len(self._ts) - 1) / elapsed if elapsed > 0 else 0.0
        self.history.append(fps)
        return fps


# ═══════════════════════════════════════════════════════════════════
# SECTION 8 — DRAWING PRIMITIVES
# ═══════════════════════════════════════════════════════════════════

def shadow_text(frame, text: str, pos: tuple, scale: float,
                color: tuple, thickness: int = 1) -> None:
    """Draws text with a 1px black shadow for readability."""
    x, y = pos
    cv2.putText(frame, text, (x+1, y+1), FONT, scale, C_BLACK, thickness+1, LINE_AA)
    cv2.putText(frame, text, pos,        FONT, scale, color,   thickness,   LINE_AA)


def bold_text(frame, text: str, pos: tuple, scale: float,
              color: tuple, thickness: int = 1) -> None:
    """Shadow text using the duplex (bold) font variant."""
    x, y = pos
    cv2.putText(frame, text, (x+1, y+1), FONT_BOLD, scale, C_BLACK, thickness+1, LINE_AA)
    cv2.putText(frame, text, pos,        FONT_BOLD, scale, color,   thickness,   LINE_AA)


def alpha_rect(frame, x1: int, y1: int, x2: int, y2: int,
               color: tuple, alpha: float = 0.75) -> None:
    """Draws a semi-transparent filled rectangle."""
    ov = frame.copy()
    cv2.rectangle(ov, (x1, y1), (x2, y2), color, -1, LINE_AA)
    cv2.addWeighted(ov, alpha, frame, 1 - alpha, 0, frame)


def conf_bar(frame, x: int, y: int, w: int, h: int,
             value: float, bar_color: tuple) -> None:
    """
    Draws a horizontal progress bar for a 0.0–1.0 value.

    Background track is drawn first, then the filled portion
    scaled by `value`, then a percentage label on top.
    """
    # Track
    cv2.rectangle(frame, (x, y), (x + w, y + h), C_DIVIDER, -1, LINE_AA)
    # Fill
    fill_w = int(w * value)
    if fill_w > 0:
        cv2.rectangle(frame, (x, y), (x + fill_w, y + h), bar_color, -1, LINE_AA)
    # Border
    cv2.rectangle(frame, (x, y), (x + w, y + h), C_BORDER, 1, LINE_AA)
    # Label centred over bar
    pct = f"{value * 100:.0f}%"
    (tw, _), _ = cv2.getTextSize(pct, FONT, 0.38, 1)
    shadow_text(frame, pct, (x + (w - tw) // 2, y + h - 2),
                0.38, C_TEXT_PRI)


def corner_bracket(frame, x1: int, y1: int, x2: int, y2: int,
                   color: tuple, arm: int = 20, thick: int = 2) -> None:
    """Draws four corner brackets around a rectangle."""
    arm = min(arm, (x2 - x1) // 4, (y2 - y1) // 4)
    for px, py, dx, dy in [
        (x1, y1,  1,  1), (x2, y1, -1,  1),
        (x1, y2,  1, -1), (x2, y2, -1, -1),
    ]:
        cv2.line(frame, (px, py), (px + dx*arm, py),       color, thick, LINE_AA)
        cv2.line(frame, (px, py), (px,           py+dy*arm), color, thick, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 9 — TOP BAR
# ═══════════════════════════════════════════════════════════════════
#
# Full-width bar at the top of the frame containing:
#   Left:   App logo + name
#   Centre: Thin decorative scan line
#   Right:  Mode chip  |  current time
# ───────────────────────────────────────────────────────────────────

def draw_top_bar(frame, mode: Mode, frame_w: int) -> None:
    """Draws the top application bar."""

    # Background
    alpha_rect(frame, 0, 0, frame_w, TOP_BAR_H, C_BG_PANEL, alpha=0.92)
    # Bottom border line
    cv2.line(frame, (0, TOP_BAR_H), (frame_w, TOP_BAR_H), C_BORDER, 1, LINE_AA)

    # ── Logo dot + app name ───────────────────────────────────────────
    cv2.circle(frame, (16, TOP_BAR_H // 2), 6, C_CYAN, -1, LINE_AA)
    cv2.circle(frame, (16, TOP_BAR_H // 2), 6, C_BLACK, 1, LINE_AA)
    bold_text(frame, APP_NAME, (28, TOP_BAR_H // 2 + 6), 0.55, C_TEXT_PRI, 1)

    # ── Decorative centre scan line ───────────────────────────────────
    mid_x = frame_w // 2
    cv2.line(frame, (mid_x - 80, TOP_BAR_H // 2),
             (mid_x + 80, TOP_BAR_H // 2), C_BORDER, 1, LINE_AA)
    cv2.circle(frame, (mid_x, TOP_BAR_H // 2), 3, C_CYAN, -1, LINE_AA)

    # ── Mode chip (right side) ────────────────────────────────────────
    mode_color = MODE_COLORS[mode]
    mode_text  = mode.value
    (tw, th), _ = cv2.getTextSize(mode_text, FONT, 0.45, 1)
    chip_x = frame_w - tw - 120
    chip_y = 6
    chip_w = tw + 16
    chip_h = TOP_BAR_H - 12

    # Chip background
    alpha_rect(frame, chip_x - 8, chip_y, chip_x + chip_w, chip_y + chip_h,
               mode_color, alpha=0.18)
    cv2.rectangle(frame, (chip_x - 8, chip_y),
                  (chip_x + chip_w, chip_y + chip_h), mode_color, 1, LINE_AA)
    shadow_text(frame, mode_text, (chip_x, chip_y + chip_h - 6), 0.45, mode_color)

    # ── Clock ─────────────────────────────────────────────────────────
    clock = datetime.now().strftime("%H:%M:%S")
    (cw, _), _ = cv2.getTextSize(clock, FONT, 0.45, 1)
    shadow_text(frame, clock, (frame_w - cw - 10, TOP_BAR_H // 2 + 6),
                0.45, C_TEXT_SEC)


# ═══════════════════════════════════════════════════════════════════
# SECTION 10 — LEFT SYSTEM PANEL
# ═══════════════════════════════════════════════════════════════════
#
# Fixed panel on the left edge showing system-level metrics:
#   • FPS  (with colour coding: green ≥ 25, amber 15–25, red < 15)
#   • Detection status  (ACTIVE / STANDBY)
#   • Number of hands detected
#   • Average confidence across all hands
#   • Current mode
#   • Session uptime
# ───────────────────────────────────────────────────────────────────

def draw_left_panel(frame, fps: float, num_hands: int,
                    avg_conf: float, mode: Mode,
                    uptime: float, frame_h: int) -> None:
    """Draws the left system status panel."""

    y1 = TOP_BAR_H
    y2 = frame_h - BOT_BAR_H
    x2 = LEFT_W

    # Panel background + border
    alpha_rect(frame, 0, y1, x2, y2, C_BG_PANEL, alpha=0.88)
    cv2.line(frame, (x2, y1), (x2, y2), C_BORDER, 1, LINE_AA)

    px = PANEL_PAD
    py = y1 + 18

    # ── Section header ────────────────────────────────────────────────
    shadow_text(frame, "SYSTEM", (px, py), 0.42, C_TEXT_DIM)
    py += 4
    cv2.line(frame, (px, py), (x2 - px, py), C_DIVIDER, 1, LINE_AA)
    py += ROW_H - 4

    # ── FPS row with colour-coded value ──────────────────────────────
    fps_color = C_GREEN if fps >= 25 else (C_AMBER if fps >= 15 else C_RED)
    shadow_text(frame, "FPS", (px, py), 0.44, C_TEXT_SEC)
    bold_text(frame, f"{fps:.1f}", (x2 - 55, py), 0.52, fps_color, 1)
    py += ROW_H

    # ── Uptime ────────────────────────────────────────────────────────
    mins  = int(uptime // 60)
    secs  = int(uptime % 60)
    shadow_text(frame, "Uptime", (px, py), 0.44, C_TEXT_SEC)
    shadow_text(frame, f"{mins:02d}:{secs:02d}", (x2 - 55, py), 0.44, C_TEXT_PRI)
    py += ROW_H + 6

    # ── Detection section ─────────────────────────────────────────────
    shadow_text(frame, "DETECTION", (px, py), 0.42, C_TEXT_DIM)
    py += 4
    cv2.line(frame, (px, py), (x2 - px, py), C_DIVIDER, 1, LINE_AA)
    py += ROW_H - 4

    # Status indicator dot + label
    status_color = C_GREEN if num_hands > 0 else C_TEXT_DIM
    status_text  = "ACTIVE"  if num_hands > 0 else "STANDBY"
    cv2.circle(frame, (px + 5, py - 4), 5, status_color, -1, LINE_AA)
    shadow_text(frame, status_text, (px + 16, py), 0.46, status_color)
    py += ROW_H

    # Hands count
    shadow_text(frame, "Hands", (px, py), 0.44, C_TEXT_SEC)
    bold_text(frame, str(num_hands), (x2 - 30, py), 0.55, C_TEXT_PRI)
    py += ROW_H

    # Average confidence bar
    shadow_text(frame, "Avg Conf", (px, py), 0.44, C_TEXT_SEC)
    py += 16
    conf_clr = C_CONF_HI if avg_conf >= 0.90 else (C_CONF_MED if avg_conf >= 0.70 else C_CONF_LO)
    conf_bar(frame, px, py, x2 - px * 2, 12, avg_conf, conf_clr)
    py += 22

    # ── Mode section ──────────────────────────────────────────────────
    shadow_text(frame, "DISPLAY", (px, py), 0.42, C_TEXT_DIM)
    py += 4
    cv2.line(frame, (px, py), (x2 - px, py), C_DIVIDER, 1, LINE_AA)
    py += ROW_H - 4

    mode_clr = MODE_COLORS[mode]
    shadow_text(frame, "Mode", (px, py), 0.44, C_TEXT_SEC)
    shadow_text(frame, mode.value, (px + 65, py), 0.44, mode_clr)
    py += ROW_H

    shadow_text(frame, "[M] cycle", (px, py), 0.38, C_TEXT_DIM)
    shadow_text(frame, "[H] panels", (px + 70, py), 0.38, C_TEXT_DIM)


# ═══════════════════════════════════════════════════════════════════
# SECTION 11 — RIGHT HAND INFO PANEL
# ═══════════════════════════════════════════════════════════════════
#
# One card per detected hand (stacked vertically) showing:
#   ┌─ [●] Right Hand  97.4% ──────────────────┐
#   │  Conf  ████████████████░░  97%            │
#   │  Size  312 × 428 px                       │
#   │  ─────────────────────────────────────    │
#   │  Thumb  ● UP    Index  ● UP               │
#   │  Middle ● DOWN  Ring   ● DOWN             │
#   │  Pinky  ● UP                              │
#   └───────────────────────────────────────────┘
# ───────────────────────────────────────────────────────────────────

CARD_H     = 185   # height per hand card
CARD_GAP   = 8     # gap between cards

def draw_right_panel(frame, hands: list[HandData], frame_w: int, frame_h: int) -> None:
    """Draws per-hand info cards on the right side."""

    x1 = frame_w - RIGHT_W
    y1 = TOP_BAR_H
    y2 = frame_h - BOT_BAR_H

    # Panel background
    alpha_rect(frame, x1, y1, frame_w, y2, C_BG_PANEL, alpha=0.88)
    cv2.line(frame, (x1, y1), (x1, y2), C_BORDER, 1, LINE_AA)

    if not hands:
        # No hands — show a placeholder
        msg = "No hand"
        (tw, _), _ = cv2.getTextSize(msg, FONT, 0.45, 1)
        shadow_text(frame, msg,
                    (x1 + (RIGHT_W - tw) // 2, (y1 + y2) // 2),
                    0.45, C_TEXT_DIM)
        return

    cy_card = y1 + CARD_GAP   # current card top

    for hand in hands[:2]:    # max 2 cards
        if cy_card + CARD_H > y2 - CARD_GAP:
            break

        px = x1 + PANEL_PAD
        bx2 = frame_w - PANEL_PAD

        # ── Card background ───────────────────────────────────────────
        alpha_rect(frame, x1 + 5, cy_card, frame_w - 5, cy_card + CARD_H,
                   C_BG_CARD, alpha=0.90)
        cv2.rectangle(frame, (x1 + 5, cy_card),
                      (frame_w - 5, cy_card + CARD_H),
                      hand.color, 1, LINE_AA)

        ry = cy_card + 18

        # ── Card header: dot + label + conf % ────────────────────────
        cv2.circle(frame, (px + 6, ry - 4), 5, hand.color, -1, LINE_AA)
        bold_text(frame, f"{hand.label} Hand", (px + 16, ry), 0.50, hand.color, 1)
        conf_str = f"{hand.confidence * 100:.1f}%"
        (tw, _), _ = cv2.getTextSize(conf_str, FONT, 0.44, 1)
        shadow_text(frame, conf_str, (frame_w - tw - PANEL_PAD, ry),
                    0.44, hand.conf_color)
        ry += 6

        cv2.line(frame, (px, ry), (frame_w - PANEL_PAD, ry), C_DIVIDER, 1, LINE_AA)
        ry += 14

        # ── Confidence bar ────────────────────────────────────────────
        shadow_text(frame, "Conf", (px, ry), 0.40, C_TEXT_SEC)
        conf_bar(frame, px + 36, ry - 10, RIGHT_W - 56, 12,
                 hand.confidence, hand.conf_color)
        ry += ROW_H - 2

        # ── Size ──────────────────────────────────────────────────────
        shadow_text(frame, "Size", (px, ry), 0.40, C_TEXT_SEC)
        shadow_text(frame, f"{hand.bw} x {hand.bh} px",
                    (px + 36, ry), 0.40, C_TEXT_PRI)
        ry += 8

        cv2.line(frame, (px, ry), (frame_w - PANEL_PAD, ry), C_DIVIDER, 1, LINE_AA)
        ry += 14

        # ── Finger states (5 rows in 2 columns) ───────────────────────
        #
        # We lay out fingers in a 2-column grid:
        #   Col 0: Thumb, Middle, Pinky
        #   Col 1: Index, Ring
        # Each cell shows a dot (green=UP, red=DOWN) + name + state.
        # ─────────────────────────────────────────────────────────────
        COL_W = (RIGHT_W - PANEL_PAD * 2) // 2

        finger_grid = [
            [("Thumb",  hand.finger.thumb),  ("Index",  hand.finger.index)],
            [("Middle", hand.finger.middle), ("Ring",   hand.finger.ring)],
            [("Pinky",  hand.finger.pinky),  None],
        ]

        for row_items in finger_grid:
            for col_i, item in enumerate(row_items):
                if item is None:
                    continue
                fname, is_up = item
                dot_clr  = C_GREEN if is_up else C_RED
                state_str = "UP" if is_up else "DN"
                fx = px + col_i * COL_W
                # Dot
                cv2.circle(frame, (fx + 5, ry - 4), 4, dot_clr, -1, LINE_AA)
                cv2.circle(frame, (fx + 5, ry - 4), 4, C_BLACK,  1, LINE_AA)
                # Name + state
                shadow_text(frame, fname, (fx + 14, ry), 0.38, C_TEXT_PRI)
                shadow_text(frame, state_str, (fx + COL_W - 22, ry), 0.38, dot_clr)
            ry += ROW_H - 4

        cy_card += CARD_H + CARD_GAP


# ═══════════════════════════════════════════════════════════════════
# SECTION 12 — BOTTOM BAR (FPS graph + hints + version)
# ═══════════════════════════════════════════════════════════════════
#
# The FPS graph is a waveform drawn from the fps_history deque.
# Each sample maps to a vertical bar whose height is proportional
# to fps / max_fps.  This gives a real-time performance readout.
# ───────────────────────────────────────────────────────────────────

def draw_bottom_bar(frame, fps_history: deque, fps: float,
                    frame_w: int, frame_h: int) -> None:
    """Draws the bottom status bar with FPS sparkline and shortcuts."""

    y1 = frame_h - BOT_BAR_H
    y2 = frame_h

    alpha_rect(frame, 0, y1, frame_w, y2, C_BG_PANEL, alpha=0.92)
    cv2.line(frame, (0, y1), (frame_w, y1), C_BORDER, 1, LINE_AA)

    # ── FPS sparkline graph ───────────────────────────────────────────
    #
    # Graph area: LEFT_W … LEFT_W + graph_w pixels wide, inset by 4px
    # Each history sample is one vertical bar.
    # Bar height = (fps / 60) * graph_h  — capped at 60 FPS max.
    # ─────────────────────────────────────────────────────────────────
    graph_x   = LEFT_W + 4
    graph_w   = 160
    graph_h   = BOT_BAR_H - 8
    graph_y_b = y2 - 4   # bottom of graph
    max_fps   = 60.0

    # Faint graph background
    alpha_rect(frame, graph_x, y1 + 4, graph_x + graph_w, y2 - 4,
               C_BG_CARD, alpha=0.6)

    samples = list(fps_history)[-graph_w:]   # at most one sample per pixel
    if len(samples) > 1:
        bar_w = max(1, graph_w // len(samples))
        for i, sample in enumerate(samples):
            bar_h = int((min(sample, max_fps) / max_fps) * graph_h)
            bx    = graph_x + i * bar_w
            by    = graph_y_b - bar_h
            # Colour shifts green→amber as FPS drops below 25
            bar_c = C_GREEN if sample >= 25 else (C_AMBER if sample >= 15 else C_RED)
            cv2.rectangle(frame, (bx, by), (bx + bar_w - 1, graph_y_b),
                          bar_c, -1, LINE_AA)

    # Graph label
    shadow_text(frame, "FPS", (graph_x + 2, y1 + 14), 0.36, C_TEXT_DIM)
    shadow_text(frame, f"{fps:.0f}", (graph_x + graph_w - 24, y1 + 14),
                0.38, C_GREEN if fps >= 25 else C_AMBER)

    # ── Shortcut hints (centre) ───────────────────────────────────────
    hints = "[Q] Quit   [M] Mode   [H] Panels  (4 modes)"
    (hw, _), _ = cv2.getTextSize(hints, FONT, 0.38, 1)
    shadow_text(frame, hints,
                ((frame_w - hw) // 2, y2 - 10),
                0.38, C_TEXT_DIM)

    # ── Version (right) ───────────────────────────────────────────────
    (vw, _), _ = cv2.getTextSize(VERSION, FONT, 0.38, 1)
    shadow_text(frame, VERSION, (frame_w - vw - 8, y2 - 10), 0.38, C_TEXT_DIM)


# ═══════════════════════════════════════════════════════════════════
# SECTION 13 — SKELETON + LANDMARK OVERLAY
# ═══════════════════════════════════════════════════════════════════

def draw_skeleton(frame, hand: HandData, frame_w: int, frame_h: int) -> None:
    """Grey bone lines between all 21 landmark connections."""
    for s_id, e_id in mp_hands.HAND_CONNECTIONS:
        s = hand.landmarks.landmark[s_id]
        e = hand.landmarks.landmark[e_id]
        x1, y1 = int(s.x * frame_w), int(s.y * frame_h)
        x2, y2 = int(e.x * frame_w), int(e.y * frame_h)
        cv2.line(frame, (x1, y1), (x2, y2), C_BONE, 2, LINE_AA)


def draw_dots(frame, hand: HandData, frame_w: int, frame_h: int) -> None:
    """White dots on all 21 landmark positions."""
    for lm in hand.landmarks.landmark:
        cx = int(lm.x * frame_w)
        cy = int(lm.y * frame_h)
        cv2.circle(frame, (cx, cy), 4, C_DOT,   -1, LINE_AA)
        cv2.circle(frame, (cx, cy), 4, C_BLACK,  1, LINE_AA)


def draw_landmark_ids(frame, hand: HandData, frame_w: int, frame_h: int) -> None:
    """
    LANDMARK mode — draws every joint as a colour-coded numbered dot.

    Colour scheme:
      Wrist (0)          → yellow
      Fingertips (4,8…)  → red  (colour changes if UP/DOWN)
      Knuckles (MCP)     → cyan
      All other joints   → light green

    ID number is printed beside each dot (0–20).
    """
    WRIST_C     = (0,   220, 255)   # yellow
    TIP_UP_C    = (80,  210, 80 )   # green  — fingertip UP
    TIP_DOWN_C  = (60,  60,  220)   # red    — fingertip DOWN
    KNUCKLE_C   = (255, 180, 0  )   # cyan
    JOINT_C     = (160, 255, 120)   # light green
    ID_C        = (200, 200, 200)   # dim white for ID numbers

    FINGERTIP_SET = {4, 8, 12, 16, 20}
    KNUCKLE_SET   = {1, 5, 9, 13, 17}
    tip_states    = [hand.finger.thumb, hand.finger.index,
                     hand.finger.middle, hand.finger.ring, hand.finger.pinky]
    tip_state_map = dict(zip(sorted(FINGERTIP_SET), tip_states))

    for idx, lm in enumerate(hand.landmarks.landmark):
        cx = int(lm.x * frame_w)
        cy = int(lm.y * frame_h)

        if idx == 0:
            color, r = WRIST_C, 8
        elif idx in FINGERTIP_SET:
            is_up = tip_state_map.get(idx, False)
            color, r = (TIP_UP_C if is_up else TIP_DOWN_C), 9
        elif idx in KNUCKLE_SET:
            color, r = KNUCKLE_C, 7
        else:
            color, r = JOINT_C, 5

        # Outlined dot
        cv2.circle(frame, (cx, cy), r + 2, C_BLACK, -1, LINE_AA)
        cv2.circle(frame, (cx, cy), r,     color,   -1, LINE_AA)

        # ID number with shadow
        cv2.putText(frame, str(idx), (cx + 10, cy - 8),
                    FONT, 0.34, C_BLACK, 2, LINE_AA)
        cv2.putText(frame, str(idx), (cx + 10, cy - 8),
                    FONT, 0.34, ID_C,    1, LINE_AA)


def draw_fingertip_rings(frame, hand: HandData, frame_w: int, frame_h: int) -> None:
    """
    Coloured rings on fingertips — green = UP, red = DOWN.
    Drawn in GESTURE mode for a clear finger-state read at a glance.
    """
    states = [hand.finger.thumb, hand.finger.index, hand.finger.middle,
              hand.finger.ring,  hand.finger.pinky]
    for tip_id, is_up in zip(FINGERTIP_IDS, states):
        lm = hand.landmarks.landmark[tip_id]
        cx = int(lm.x * frame_w)
        cy = int(lm.y * frame_h)
        c  = C_GREEN if is_up else C_RED
        cv2.circle(frame, (cx, cy), 14, c,       2, LINE_AA)
        cv2.circle(frame, (cx, cy), 7,  c,      -1, LINE_AA)
        cv2.circle(frame, (cx, cy), 7,  C_BLACK,  1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 14 — TRACKING MODE OVERLAYS (bounding box + crosshair)
# ═══════════════════════════════════════════════════════════════════

def draw_tracking_overlay(frame, hand: HandData) -> None:
    """
    TRACKING mode per-hand overlays:
      • Corner-bracket bounding box
      • Center crosshair + coordinate label
    """
    # Corner brackets
    corner_bracket(frame, hand.bx, hand.by, hand.bx2, hand.by2,
                   hand.color, arm=22, thick=2)

    # Faint full outline at 25% opacity
    ov = frame.copy()
    cv2.rectangle(ov, (hand.bx, hand.by), (hand.bx2, hand.by2), hand.color, 1, LINE_AA)
    cv2.addWeighted(ov, 0.25, frame, 0.75, 0, frame)

    # Crosshair
    cx, cy = hand.cx, hand.cy
    for (ax1, ay1), (ax2, ay2) in [
        ((cx-18, cy), (cx-6, cy)), ((cx+6, cy), (cx+18, cy)),
        ((cx, cy-18), (cx, cy-6)), ((cx, cy+6), (cx, cy+18)),
    ]:
        cv2.line(frame, (ax1, ay1), (ax2, ay2), C_BLACK,  3, LINE_AA)
        cv2.line(frame, (ax1, ay1), (ax2, ay2), C_YELLOW, 1, LINE_AA)
    cv2.circle(frame, (cx, cy), 5, C_BLACK,  -1, LINE_AA)
    cv2.circle(frame, (cx, cy), 3, C_YELLOW, -1, LINE_AA)

    # Coordinate label
    coord = f"({cx},{cy})"
    shadow_text(frame, coord, (cx - 26, cy + 22), 0.38, C_YELLOW)

    # Dimension labels
    w_text = f"W:{hand.bw}px"
    (tw, _), _ = cv2.getTextSize(w_text, FONT, 0.38, 1)
    shadow_text(frame, w_text, (hand.bx + (hand.bw - tw)//2, hand.by - 6), 0.38, C_TEXT_SEC)

    h_text = f"H:{hand.bh}px"
    shadow_text(frame, h_text, (hand.bx2 + 6, hand.by + hand.bh//2), 0.38, C_TEXT_SEC)


# ═══════════════════════════════════════════════════════════════════
# SECTION 15 — CAMERA SETUP
# ═══════════════════════════════════════════════════════════════════

def open_camera(index: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {index}. Try --camera 0, 1, or 2.")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS,          30)
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"[INFO] Camera {index} opened: {w}x{h} @ {fps:.0f}fps")
    return cap


# ═══════════════════════════════════════════════════════════════════
# SECTION 16 — MAIN LOOP
# ═══════════════════════════════════════════════════════════════════
#
# Per-frame pipeline:
#
#   read → flip → apply dark vignette → BGR→RGB → MediaPipe
#     ↓
#   build HandData list from results
#     ↓
#   for each hand (if not MINIMAL):
#     draw_skeleton()
#     draw_dots()
#     mode == GESTURE  → draw_fingertip_rings()
#     mode == TRACKING → draw_tracking_overlay()
#     ↓
#   if show_panels:
#     draw_top_bar()
#     draw_left_panel()
#     draw_right_panel()
#     draw_bottom_bar()
#   else:
#     minimal FPS badge only
#     ↓
#   imshow → waitKey → Q / M / H
# ───────────────────────────────────────────────────────────────────

def apply_vignette(frame) -> None:
    """
    Applies a subtle dark vignette around the frame edges.
    This draws the viewer's eye toward the center where the hand is,
    and gives the camera feed a cinematic look.

    Implementation: 4 semi-transparent dark rectangles on each edge.
    """
    h, w = frame.shape[:2]
    fade = 60   # width of the fade band

    for region, alpha in [
        ((0, 0, w, fade),           0.35),   # top
        ((0, h - fade, w, h),       0.35),   # bottom
        ((0, 0, fade, h),           0.25),   # left
        ((w - fade, 0, w, h),       0.25),   # right
    ]:
        x1, y1, x2, y2 = region
        alpha_rect(frame, x1, y1, x2, y2, (0, 0, 0), alpha=alpha)


def run(camera_index: int = 0, max_hands: int = 2, flip: bool = True) -> None:
    """GestureOS AI — Full HUD main loop."""

    cap         = open_camera(camera_index)
    fps_counter = FPSCounter(window=30, history=80)
    start_time  = time.monotonic()
    mode        = Mode.TRACKING
    show_panels = True

    # ── Handedness smoother ───────────────────────────────────────────
    # MediaPipe flickers Left/Right during fast movement.
    # Majority vote over last 15 frames per hand slot keeps label stable.
    SMOOTH_N      = 15
    label_history = [deque(maxlen=SMOOTH_N), deque(maxlen=SMOOTH_N)]

    def stable_label(slot: int, raw: str) -> str:
        label_history[slot].append(raw)
        return max(set(label_history[slot]), key=label_history[slot].count)

    with mp_hands.Hands(
        static_image_mode        = False,
        max_num_hands            = max_hands,
        min_detection_confidence = 0.75,
        min_tracking_confidence  = 0.65,
    ) as hands_model:

        print("[INFO] GestureOS AI HUD running.")
        print("       Q=Quit  M=Cycle mode  H=Toggle panels")

        while True:

            # ── 1. Frame capture ──────────────────────────────────────
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Camera read failed.")
                break

            if flip:
                frame = cv2.flip(frame, 1)

            frame_h, frame_w = frame.shape[:2]

            # ── 2. Vignette ───────────────────────────────────────────
            apply_vignette(frame)

            # ── 3. MediaPipe inference ────────────────────────────────
            rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands_model.process(rgb)

            # Reset smoother when no hands detected
            if not results.multi_hand_landmarks:
                for h in label_history:
                    h.clear()

            # ── 4. Build HandData list with smoothed labels ───────────
            hands: list[HandData] = []
            if results.multi_hand_landmarks:
                for slot, (lm, hd) in enumerate(zip(
                        results.multi_hand_landmarks,
                        results.multi_handedness)):
                    raw = hd.classification[0].label
                    # Patch the label in handedness before building data
                    hd.classification[0].label = stable_label(slot, raw)
                    hands.append(build_hand_data(lm, hd, frame_w, frame_h))

            # ── 5. Per-hand overlays (drawn on camera feed area) ──────
            for hand in hands:
                # Skeleton always drawn in all modes except LANDMARK
                # (LANDMARK draws its own coloured connections)
                if mode == Mode.LANDMARK:
                    draw_skeleton(frame, hand, frame_w, frame_h)
                    draw_landmark_ids(frame, hand, frame_w, frame_h)
                else:
                    draw_skeleton(frame, hand, frame_w, frame_h)
                    draw_dots(frame, hand, frame_w, frame_h)

                    if mode == Mode.GESTURE:
                        draw_fingertip_rings(frame, hand, frame_w, frame_h)
                    elif mode == Mode.TRACKING:
                        draw_tracking_overlay(frame, hand)

            # ── 6. HUD panels ─────────────────────────────────────────
            fps     = fps_counter.tick()
            uptime  = time.monotonic() - start_time
            avg_conf = (
                sum(h.confidence for h in hands) / len(hands)
                if hands else 0.0
            )

            if show_panels:
                draw_top_bar(frame, mode, frame_w)
                draw_left_panel(frame, fps, len(hands), avg_conf,
                                mode, uptime, frame_h)
                draw_right_panel(frame, hands, frame_w, frame_h)
                draw_bottom_bar(frame, fps_counter.history, fps,
                                frame_w, frame_h)
            else:
                # Minimal mode: just FPS badge top-left
                fps_clr = C_GREEN if fps >= 25 else C_AMBER
                shadow_text(frame, f"FPS {fps:.0f}", (12, 30), 0.6, fps_clr, 2)

            # ── 7. Display ────────────────────────────────────────────
            cv2.imshow("GestureOS AI", frame)

            # ── 8. Key handling ───────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q")):
                print("[INFO] Quit.")
                break

            elif key in (ord("m"), ord("M")):
                # Cycle through modes: TRACKING → GESTURE → MINIMAL → …
                cur_idx = MODE_CYCLE.index(mode)
                mode    = MODE_CYCLE[(cur_idx + 1) % len(MODE_CYCLE)]
                print(f"[INFO] Mode → {mode.value}")

            elif key in (ord("h"), ord("H")):
                show_panels = not show_panels
                print(f"[INFO] Panels → {'ON' if show_panels else 'OFF'}")

    # ── Cleanup ───────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Done.")


# ═══════════════════════════════════════════════════════════════════
# SECTION 17 — CLI & ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GestureOS AI — Professional Hand Tracking HUD"
    )
    p.add_argument("--camera",    type=int, default=0,
                   help="Camera index (default 0 = laptop built-in webcam)")
    p.add_argument("--max-hands", type=int, default=2, choices=[1, 2],
                   help="Max simultaneous hands (default 2)")
    p.add_argument("--no-flip",   action="store_true",
                   help="Disable mirror mode")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        camera_index = args.camera,
        max_hands    = args.max_hands,
        flip         = not args.no_flip,
    )
