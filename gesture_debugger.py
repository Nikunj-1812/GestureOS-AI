"""
GestureOS AI — Gesture Debugger
=================================
A single-file development tool that shows every computed property
of the hand tracking pipeline simultaneously, so you can inspect
and tune the system in real time.

SCREEN LAYOUT
──────────────────────────────────────────────────────────────────
 ┌─────────────────────────────────────────────────────────────┐
 │  TOP BAR  — GestureOS Debugger ● LIVE  FPS ██  D=toggle    │
 ├──────────────────────────────────────┬──────────────────────┤
 │                                      │  DEBUG PANEL         │
 │   LIVE CAMERA FEED                   │                      │
 │   + numbered landmark dots           │  ① SYSTEM           │
 │   + colour-coded skeleton            │    FPS / frame time  │
 │   + fingertip UP/DOWN rings          │    hands detected    │
 │   + corner bounding box              │                      │
 │   + centre crosshair                 │  ② HAND A           │
 │   + thumb↔index distance line        │    conf bar          │
 │                                      │    bbox W×H          │
 │                                      │    centre coords     │
 │                                      │                      │
 │                                      │  ③ FINGER STATES    │
 │                                      │    thumb/idx/mid…    │
 │                                      │    raised count      │
 │                                      │                      │
 │                                      │  ④ LANDMARKS (21)   │
 │                                      │    scrollable list   │
 │                                      │    x / y / z raw     │
 │                                      │                      │
 │                                      │  ⑤ DISTANCES        │
 │                                      │    thumb↔index px/cm │
 │                                      │    all tip combos    │
 └──────────────────────────────────────┴──────────────────────┘

CONTROLS
  D  — Toggle debug panel on/off
  Q  — Quit

Usage:
  python gesture_debugger.py
  python gesture_debugger.py --camera 1 --max-hands 2
  python gesture_debugger.py --no-flip
"""

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — IMPORTS
# ═══════════════════════════════════════════════════════════════════

import argparse
import math
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np


# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — MEDIAPIPE SETUP
# ═══════════════════════════════════════════════════════════════════

mp_hands = mp.solutions.hands


# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — COLOUR PALETTE & LAYOUT CONSTANTS
# ═══════════════════════════════════════════════════════════════════
#
# "Debugger" design language:
#   Dark charcoal base  →  feels like an IDE/terminal
#   Cyan accent         →  active / live values
#   Amber               →  warnings / mid states
#   Green               →  good / UP states
#   Red                 →  low / DOWN states
#   Purple              →  section headers
#
# All colours are (Blue, Green, Red) — OpenCV BGR order.
# ───────────────────────────────────────────────────────────────────

# ── Base colours ──────────────────────────────────────────────────
C_BG         = (14,  16,  26 )   # darkest — camera border
C_PANEL      = (20,  22,  38 )   # debug panel background
C_CARD       = (28,  30,  50 )   # section card inside panel
C_BORDER     = (50,  55,  95 )   # panel / card border
C_DIVIDER    = (38,  42,  68 )   # row separator
C_TOPBAR     = (16,  18,  34 )   # top bar background

# ── Text ──────────────────────────────────────────────────────────
C_PRI        = (235, 238, 250)   # primary text
C_SEC        = (130, 138, 170)   # secondary / dim text
C_DIM        = (70,  76,  110)   # very dim
C_BLACK      = (0,   0,   0  )

# ── Accents ───────────────────────────────────────────────────────
C_CYAN       = (245, 210, 0  )   # live / highlight
C_AMBER      = (0,   185, 255)   # mid / warning
C_GREEN      = (75,  205, 75 )   # up / good
C_RED        = (55,  55,  215)   # down / alert
C_PURPLE     = (190, 90,  175)   # section headers

# ── Confidence gradient ───────────────────────────────────────────
C_CONF_HI    = (75,  205, 75 )   # ≥90 %
C_CONF_MED   = (0,   185, 255)   # 70–90 %
C_CONF_LO    = (55,  55,  215)   # <70 %

# ── Hand identity ─────────────────────────────────────────────────
C_RIGHT      = (0,   195, 255)   # amber-gold
C_LEFT       = (255, 150, 0  )   # cyan-blue

# ── Skeleton ──────────────────────────────────────────────────────
C_BONE       = (80,  88,  140)
C_DOT_BASE   = (200, 210, 235)
C_TIP_UP     = (75,  205, 75 )
C_TIP_DOWN   = (55,  55,  215)

# ── Distance line ─────────────────────────────────────────────────
C_DIST_CLOSE = (75,  205, 75 )   # ≤80 px
C_DIST_MID   = (0,   185, 255)   # ≤200 px
C_DIST_FAR   = (55,  55,  215)   # >200 px

# ── Layout geometry ───────────────────────────────────────────────
TOP_H        = 38    # top bar height
DBG_W        = 290   # debug panel width
PAD          = 10    # inner padding
ROW          = 20    # standard row height

FONT         = cv2.FONT_HERSHEY_SIMPLEX
FONT_BD      = cv2.FONT_HERSHEY_DUPLEX
AA           = cv2.LINE_AA

# Landmark names for the 21 MediaPipe hand points
LM_NAMES = [
    "WRIST",
    "THUMB_CMC","THUMB_MCP","THUMB_IP","THUMB_TIP",
    "INDEX_MCP","INDEX_PIP","INDEX_DIP","INDEX_TIP",
    "MID_MCP",  "MID_PIP",  "MID_DIP",  "MID_TIP",
    "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
    "PINKY_MCP","PINKY_PIP","PINKY_DIP","PINKY_TIP",
]
FINGERTIP_IDS = [4, 8, 12, 16, 20]
FINGER_NAMES  = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# Distance calibration: knuckle span ID 5→17 ≈ 7 cm on adult hand
REF_CM = 7.0


# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — DATA CLASSES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class FingerState:
    thumb: bool = False
    index: bool = False
    middle: bool = False
    ring:  bool = False
    pinky: bool = False

    @property
    def raised(self) -> int:
        return sum([self.thumb, self.index, self.middle, self.ring, self.pinky])

    def as_list(self) -> list[tuple[str, bool]]:
        return list(zip(FINGER_NAMES,
                        [self.thumb, self.index, self.middle, self.ring, self.pinky]))


@dataclass
class DistanceData:
    """All thumb-index distance values computed for one hand."""
    px:     float = 0.0    # pixel distance
    cm:     float = 0.0    # cm estimate
    ref_px: float = 0.0    # calibration reference span (px)
    colour: tuple = field(default_factory=lambda: (75, 205, 75))

    # All 10 tip-to-tip pixel distances (C(5,2) combinations)
    tip_pairs: dict = field(default_factory=dict)


@dataclass
class HandDebugData:
    """Complete per-hand debug snapshot for one frame."""
    label:       str
    confidence:  float
    finger:      FingerState
    landmarks:   object          # raw NormalizedLandmarkList
    dist:        DistanceData
    # Bounding box (pixels)
    bx: int = 0; by: int = 0
    bw: int = 0; bh: int = 0
    cx: int = 0; cy: int = 0    # box centre

    @property
    def bx2(self): return self.bx + self.bw
    @property
    def by2(self): return self.by + self.bh
    @property
    def hand_color(self):
        return C_RIGHT if self.label == "Right" else C_LEFT
    @property
    def conf_color(self):
        if self.confidence >= 0.90: return C_CONF_HI
        if self.confidence >= 0.70: return C_CONF_MED
        return C_CONF_LO


# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — COMPUTATION HELPERS
# ═══════════════════════════════════════════════════════════════════

def lm_px(lm_list, idx: int, fw: int, fh: int) -> tuple[int, int]:
    """Converts normalised landmark[idx] → pixel (x, y)."""
    lm = lm_list[idx]
    return (int(lm.x * fw), int(lm.y * fh))


def px_dist(p1: tuple, p2: tuple) -> float:
    """Euclidean pixel distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def dist_color(d: float) -> tuple:
    if d <= 80:  return C_DIST_CLOSE
    if d <= 200: return C_DIST_MID
    return C_DIST_FAR


def detect_fingers(lm, label: str) -> FingerState:
    """
    Detects UP/DOWN per finger from landmark list.
    Fingers: tip.y < pip.y → UP.
    Thumb:   distance-based (TIP farther from WRIST than MCP → UP).
             Robust to front-facing palm and mirror flip.
    """
    import math
    def _d(a, b): return math.hypot(a.x - b.x, a.y - b.y)
    tip_dist  = _d(lm[4], lm[0])   # TIP → WRIST
    ip_dist   = _d(lm[3], lm[0])   # IP  → WRIST
    tip_to_ip = _d(lm[4], lm[3])   # TIP → IP
    thumb = (tip_dist > ip_dist + 0.04) and (tip_to_ip > 0.04)
    return FingerState(
        thumb  = thumb,
        index  = lm[8].y  < lm[6].y,
        middle = lm[12].y < lm[10].y,
        ring   = lm[16].y < lm[14].y,
        pinky  = lm[20].y < lm[18].y,
    )


def compute_distances(lm, fw: int, fh: int) -> DistanceData:
    """
    Computes thumb↔index distance plus all 10 tip-pair distances.

    The calibration reference (landmark 5 → 17) gives us the live
    px-to-cm ratio so results scale with hand distance from camera.
    """
    # Reference span for cm conversion
    ref_px_val = px_dist(lm_px(lm, 5, fw, fh), lm_px(lm, 17, fw, fh))
    cm_per_px  = (REF_CM / ref_px_val) if ref_px_val > 1 else 0.0

    # Primary: thumb tip (4) ↔ index tip (8)
    p_thumb = lm_px(lm, 4, fw, fh)
    p_index = lm_px(lm, 8, fw, fh)
    d_px    = px_dist(p_thumb, p_index)
    d_cm    = d_px * cm_per_px

    # All 10 tip-to-tip combinations
    pairs = {}
    for i in range(len(FINGERTIP_IDS)):
        for j in range(i + 1, len(FINGERTIP_IDS)):
            id_a  = FINGERTIP_IDS[i]
            id_b  = FINGERTIP_IDS[j]
            pa    = lm_px(lm, id_a, fw, fh)
            pb    = lm_px(lm, id_b, fw, fh)
            key   = f"{FINGER_NAMES[i][0]}-{FINGER_NAMES[j][0]}"
            pairs[key] = px_dist(pa, pb)

    return DistanceData(
        px=d_px, cm=d_cm,
        ref_px=ref_px_val,
        colour=dist_color(d_px),
        tip_pairs=pairs,
    )


def build_debug_data(
    hand_lm, handedness, fw: int, fh: int
) -> HandDebugData:
    """Builds the full HandDebugData snapshot for one detected hand."""
    label      = handedness.classification[0].label
    confidence = handedness.classification[0].score
    lm         = hand_lm.landmark

    xs  = [l.x * fw for l in lm]
    ys  = [l.y * fh for l in lm]
    pad = 26
    bx  = max(0,  int(min(xs)) - pad)
    by  = max(0,  int(min(ys)) - pad)
    bx2 = min(fw, int(max(xs)) + pad)
    by2 = min(fh, int(max(ys)) + pad)

    return HandDebugData(
        label      = label,
        confidence = confidence,
        finger     = detect_fingers(lm, label),
        landmarks  = hand_lm,
        dist       = compute_distances(lm, fw, fh),
        bx=bx, by=by, bw=bx2-bx, bh=by2-by,
        cx=(bx + bx2) // 2, cy=(by + by2) // 2,
    )


# ═══════════════════════════════════════════════════════════════════
# SECTION 6 — DRAWING PRIMITIVES
# ═══════════════════════════════════════════════════════════════════

def txt(frame, text: str, pos: tuple, scale: float,
        color: tuple, thick: int = 1, bold: bool = False) -> None:
    """Shadow-backed text. bold=True uses FONT_BD."""
    f = FONT_BD if bold else FONT
    x, y = pos
    cv2.putText(frame, text, (x+1, y+1), f, scale, C_BLACK, thick+1, AA)
    cv2.putText(frame, text, pos,        f, scale, color,   thick,   AA)


def alpha_fill(frame, x1: int, y1: int, x2: int, y2: int,
               color: tuple, alpha: float = 0.80) -> None:
    """Semi-transparent filled rect."""
    ov = frame.copy()
    cv2.rectangle(ov, (x1, y1), (x2, y2), color, -1, AA)
    cv2.addWeighted(ov, alpha, frame, 1 - alpha, 0, frame)


def progress_bar(frame, x: int, y: int, w: int, h: int,
                 value: float, bar_color: tuple,
                 label: str = "") -> None:
    """Horizontal progress bar 0.0–1.0 with optional label."""
    cv2.rectangle(frame, (x, y), (x+w, y+h), C_DIVIDER, -1, AA)
    fw = int(w * max(0.0, min(1.0, value)))
    if fw > 0:
        cv2.rectangle(frame, (x, y), (x+fw, y+h), bar_color, -1, AA)
    cv2.rectangle(frame, (x, y), (x+w, y+h), C_BORDER, 1, AA)
    if label:
        (tw, _), _ = cv2.getTextSize(label, FONT, 0.34, 1)
        cv2.putText(frame, label, (x + (w-tw)//2, y+h-2),
                    FONT, 0.34, C_PRI, 1, AA)


def section_header(frame, text: str, x: int, y: int, w: int) -> int:
    """
    Draws a coloured section header with a bottom divider.
    Returns the new y cursor position after the header.
    """
    cv2.putText(frame, text, (x, y), FONT, 0.38, C_PURPLE, 1, AA)
    y += 4
    cv2.line(frame, (x, y), (x + w - PAD, y), C_DIVIDER, 1, AA)
    return y + ROW - 4


def bracket_box(frame, x1: int, y1: int, x2: int, y2: int,
                color: tuple, arm: int = 18, thick: int = 2) -> None:
    """Corner-bracket bounding box."""
    a = min(arm, (x2-x1)//4, (y2-y1)//4)
    for px, py, dx, dy in [(x1,y1,1,1),(x2,y1,-1,1),(x1,y2,1,-1),(x2,y2,-1,-1)]:
        cv2.line(frame,(px,py),(px+dx*a,py),color,thick,AA)
        cv2.line(frame,(px,py),(px,py+dy*a),color,thick,AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 7 — CAMERA FEED OVERLAYS
# ═══════════════════════════════════════════════════════════════════
#
# All overlays drawn ON TOP of the camera image.
# Drawing order: skeleton lines → dots → bounding box → crosshair
#             → distance line → fingertip rings
# ───────────────────────────────────────────────────────────────────

def draw_skeleton(frame, hand: HandDebugData, fw: int, fh: int) -> None:
    """Draws all 21 bone connections."""
    for s_id, e_id in mp_hands.HAND_CONNECTIONS:
        s = hand.landmarks.landmark[s_id]
        e = hand.landmarks.landmark[e_id]
        x1, y1 = int(s.x*fw), int(s.y*fh)
        x2, y2 = int(e.x*fw), int(e.y*fh)
        cv2.line(frame, (x1,y1), (x2,y2), C_BONE, 2, AA)


def draw_landmark_dots(frame, hand: HandDebugData, fw: int, fh: int) -> None:
    """
    Draws every landmark as a numbered dot.
    Fingertips get a colour-coded ring (green=UP, red=DOWN).
    All other joints get a small white dot.
    Numbers are printed beside each dot.
    """
    states = [hand.finger.thumb, hand.finger.index, hand.finger.middle,
              hand.finger.ring,  hand.finger.pinky]
    tip_state = dict(zip(FINGERTIP_IDS, states))

    for idx, lm in enumerate(hand.landmarks.landmark):
        cx = int(lm.x * fw)
        cy = int(lm.y * fh)

        if idx in FINGERTIP_IDS:
            is_up = tip_state[idx]
            ring_c = C_TIP_UP if is_up else C_TIP_DOWN
            cv2.circle(frame, (cx,cy), 13, ring_c,  2, AA)
            cv2.circle(frame, (cx,cy),  7, ring_c, -1, AA)
            cv2.circle(frame, (cx,cy),  7, C_BLACK,  1, AA)
        else:
            cv2.circle(frame, (cx,cy), 5, C_DOT_BASE, -1, AA)
            cv2.circle(frame, (cx,cy), 5, C_BLACK,     1, AA)

        # ID number beside the dot (shifted right+up)
        cv2.putText(frame, str(idx), (cx+9, cy-8),
                    FONT, 0.32, C_DIM, 1, AA)


def draw_bounding_box(frame, hand: HandDebugData) -> None:
    """Corner-bracket box + faint outline + centre crosshair."""
    bracket_box(frame, hand.bx, hand.by, hand.bx2, hand.by2,
                hand.hand_color, arm=20, thick=2)

    # Faint full outline at 20% opacity
    ov = frame.copy()
    cv2.rectangle(ov, (hand.bx,hand.by),(hand.bx2,hand.by2),
                  hand.hand_color, 1, AA)
    cv2.addWeighted(ov, 0.20, frame, 0.80, 0, frame)

    # Crosshair at box centre
    cx, cy = hand.cx, hand.cy
    for (ax1,ay1),(ax2,ay2) in [
        ((cx-16,cy),(cx-5,cy)), ((cx+5,cy),(cx+16,cy)),
        ((cx,cy-16),(cx,cy-5)), ((cx,cy+5),(cx,cy+16)),
    ]:
        cv2.line(frame,(ax1,ay1),(ax2,ay2), C_BLACK,  3, AA)
        cv2.line(frame,(ax1,ay1),(ax2,ay2), C_CYAN,   1, AA)
    cv2.circle(frame,(cx,cy), 4, C_BLACK, -1, AA)
    cv2.circle(frame,(cx,cy), 3, C_CYAN,  -1, AA)


def draw_distance_line(frame, hand: HandDebugData, fw: int, fh: int) -> None:
    """
    Draws the thumb↔index measurement line with:
      • Shadow + coloured solid line
      • Animated white dashes (static in debugger — use frame counter externally)
      • Endpoint dots (cyan=thumb, amber=index)
      • Floating label chip at the midpoint
    """
    lm   = hand.landmarks.landmark
    tx   = int(lm[4].x * fw);  ty = int(lm[4].y * fh)
    ix   = int(lm[8].x * fw);  iy = int(lm[8].y * fh)
    d    = hand.dist
    lc   = d.colour

    # Shadow + solid line
    cv2.line(frame, (tx,ty), (ix,iy), C_BLACK, 6, AA)
    cv2.line(frame, (tx,ty), (ix,iy), lc,      2, AA)

    # Endpoint circles
    for pt, color in [((tx,ty), C_CYAN), ((ix,iy), C_AMBER)]:
        cv2.circle(frame, pt, 10, C_BLACK, -1, AA)
        cv2.circle(frame, pt, 7,  color,   -1, AA)
        cv2.circle(frame, pt, 3,  C_BLACK, -1, AA)

    # Midpoint dot
    mx, my = (tx+ix)//2, (ty+iy)//2
    cv2.circle(frame, (mx,my), 5, C_BLACK, -1, AA)
    cv2.circle(frame, (mx,my), 3, (255,255,255), -1, AA)

    # Floating label chip
    label = f"{d.px:.0f}px  {d.cm:.1f}cm"
    (lw, lh), _ = cv2.getTextSize(label, FONT, 0.46, 1)
    chip_x = mx - lw//2 - 8
    chip_y = my - lh - 24
    chip_x = max(4, min(chip_x, fw - lw - 20))
    chip_y = max(4, min(chip_y, fh - lh - 20))

    cv2.line(frame, (mx, my-4), (chip_x + lw//2 + 8, chip_y + lh + 8),
             lc, 1, AA)
    alpha_fill(frame, chip_x, chip_y, chip_x+lw+16, chip_y+lh+10,
               C_BG, alpha=0.82)
    cv2.rectangle(frame, (chip_x, chip_y),
                  (chip_x+lw+16, chip_y+lh+10), lc, 1, AA)
    cv2.putText(frame, label, (chip_x+8, chip_y+lh+2),
                FONT, 0.46, C_PRI, 1, AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 8 — TOP BAR
# ═══════════════════════════════════════════════════════════════════

def draw_top_bar(frame, fps: float, debug_on: bool, num_hands: int,
                 fw: int) -> None:
    """
    Full-width top bar:
      Left:   logo dot + "GestureOS Debugger"
      Centre: live hand count chip
      Right:  FPS + D-key hint + clock
    """
    alpha_fill(frame, 0, 0, fw, TOP_H, C_TOPBAR, alpha=0.95)
    cv2.line(frame, (0, TOP_H), (fw, TOP_H), C_BORDER, 1, AA)

    # Logo dot
    cv2.circle(frame, (14, TOP_H//2), 5, C_CYAN, -1, AA)
    cv2.circle(frame, (14, TOP_H//2), 5, C_BLACK, 1, AA)
    txt(frame, "GestureOS  Debugger", (26, TOP_H//2+6),
        0.52, C_PRI, bold=True)

    # Centre: "● LIVE  2 hands" chip
    live_c = C_GREEN if num_hands > 0 else C_DIM
    live_t = f"LIVE  {num_hands} hand{'s' if num_hands != 1 else ''}"
    (lw, _), _ = cv2.getTextSize(live_t, FONT, 0.44, 1)
    lx = (fw - lw) // 2 - 10
    cv2.circle(frame, (lx, TOP_H//2), 5, live_c, -1, AA)
    txt(frame, live_t, (lx+12, TOP_H//2+6), 0.44, live_c)

    # Right: FPS + debug toggle hint + clock
    fps_c   = C_GREEN if fps >= 25 else (C_AMBER if fps >= 15 else C_RED)
    clock   = datetime.now().strftime("%H:%M:%S")
    dbg_lbl = "[D] DEBUG ON " if debug_on else "[D] DEBUG OFF"
    dbg_c   = C_CYAN if debug_on else C_DIM

    right_items = [
        (f"FPS {fps:.1f}", fps_c,  fw - 220),
        (dbg_lbl,          dbg_c,  fw - 155),
        ("[Q] Quit",        C_DIM,  fw - 75 ),
    ]
    for label, color, rx in right_items:
        txt(frame, label, (rx, TOP_H//2+6), 0.40, color)


# ═══════════════════════════════════════════════════════════════════
# SECTION 9 — DEBUG PANEL (right side)
# ═══════════════════════════════════════════════════════════════════
#
# The debug panel is a fixed-width column on the right edge.
# It is composed of 5 independently-drawn sections, each with
# its own header, stacked vertically using a running y cursor.
#
# Sections:
#   ① SYSTEM     — FPS, frame ms, hands detected
#   ② HAND       — one card per hand: conf bar, bbox, centre
#   ③ FINGERS    — UP/DOWN state with colour dots + raised count
#   ④ LANDMARKS  — scrollable raw (x, y, z) values for all 21 pts
#   ⑤ DISTANCES  — thumb↔index primary + all 10 tip-pair combos
# ───────────────────────────────────────────────────────────────────

def draw_debug_panel(
    frame,
    hands:     list[HandDebugData],
    fps:       float,
    frame_ms:  float,
    fw:        int,
    fh:        int,
) -> None:
    """Draws the full debug panel on the right side of the frame."""

    px = fw - DBG_W             # panel left edge
    py = TOP_H                  # panel top edge
    ph = fh - TOP_H             # panel height

    # ── Panel background ──────────────────────────────────────────────
    alpha_fill(frame, px, py, fw, fh, C_PANEL, alpha=0.92)
    cv2.line(frame, (px, py), (px, fh), C_BORDER, 1, AA)

    lx  = px + PAD              # text left margin
    rw  = DBG_W - PAD * 2      # usable content width
    ry  = py + 14               # running y cursor

    # ─────────────────────────────────────────────────────────────────
    # ① SYSTEM
    # ─────────────────────────────────────────────────────────────────
    ry = section_header(frame, "① SYSTEM", lx, ry, DBG_W)

    fps_c = C_GREEN if fps >= 25 else (C_AMBER if fps >= 15 else C_RED)
    _dbg_row(frame, lx, ry, rw, "FPS",      f"{fps:.1f}",        fps_c);  ry += ROW
    _dbg_row(frame, lx, ry, rw, "Frame ms", f"{frame_ms:.1f}",   C_SEC);  ry += ROW
    _dbg_row(frame, lx, ry, rw, "Hands",    str(len(hands)),      C_PRI);  ry += ROW + 4

    # ─────────────────────────────────────────────────────────────────
    # ② HAND CARDS  (one per detected hand, max 2)
    # ─────────────────────────────────────────────────────────────────
    for i, hand in enumerate(hands[:2]):
        if ry > fh - 80:
            break

        ry = section_header(frame,
                            f"② {'RIGHT' if hand.label=='Right' else 'LEFT'} HAND",
                            lx, ry, DBG_W)

        # Confidence bar
        txt(frame, "Conf", (lx, ry), 0.38, C_SEC)
        bar_x = lx + 36
        bar_w = rw - 38
        progress_bar(frame, bar_x, ry-12, bar_w, 12,
                     hand.confidence, hand.conf_color,
                     label=f"{hand.confidence*100:.1f}%")
        ry += ROW - 2

        # BBox dimensions
        _dbg_row(frame, lx, ry, rw, "BBox",
                 f"{hand.bw} x {hand.bh} px", C_PRI);         ry += ROW
        _dbg_row(frame, lx, ry, rw, "Centre",
                 f"({hand.cx}, {hand.cy})",    C_CYAN);        ry += ROW
        _dbg_row(frame, lx, ry, rw, "Area",
                 f"{hand.bw * hand.bh} px²",   C_SEC);        ry += ROW + 4

    # ─────────────────────────────────────────────────────────────────
    # ③ FINGER STATES
    # ─────────────────────────────────────────────────────────────────
    if hands and ry < fh - 160:
        ry = section_header(frame, "③ FINGER STATES", lx, ry, DBG_W)
        hand = hands[0]

        # Two-column grid: left col fingers 0-2, right col 3-4
        col_w = rw // 2
        finger_list = hand.finger.as_list()
        for row_i in range(3):
            for col_i in range(2):
                fi = row_i * 2 + col_i
                if fi >= len(finger_list):
                    continue
                name, is_up = finger_list[fi]
                dot_c = C_GREEN if is_up else C_RED
                label = "UP" if is_up else "DN"
                fx = lx + col_i * col_w

                cv2.circle(frame, (fx+5, ry-4), 4, dot_c, -1, AA)
                cv2.circle(frame, (fx+5, ry-4), 4, C_BLACK, 1, AA)
                txt(frame, name,  (fx+14, ry), 0.36, C_PRI)
                txt(frame, label, (fx+col_w-22, ry), 0.36, dot_c)
            ry += ROW - 2

        # Raised count bar
        ry += 2
        raised = hand.finger.raised
        progress_bar(frame, lx, ry, rw, 10,
                     raised / 5.0, C_CYAN,
                     label=f"{raised}/5 raised")
        ry += 18

    # ─────────────────────────────────────────────────────────────────
    # ④ LANDMARKS  (raw x/y/z for all 21 points)
    # ─────────────────────────────────────────────────────────────────
    if hands and ry < fh - 100:
        ry = section_header(frame, "④ LANDMARKS (x / y / z)", lx, ry, DBG_W)
        hand   = hands[0]
        lm_lx  = lx
        col_id = lm_lx
        col_x  = lm_lx + 38
        col_y  = lm_lx + 98
        col_z  = lm_lx + 158

        # Header row
        for col, hdr in [(col_id,"ID"),(col_x,"X"),(col_y,"Y"),(col_z,"Z")]:
            txt(frame, hdr, (col, ry), 0.32, C_DIM)
        ry += ROW - 4
        cv2.line(frame, (lx, ry), (lx+rw, ry), C_DIVIDER, 1, AA)
        ry += 4

        # Show as many rows as space allows
        for idx, lm in enumerate(hand.landmarks.landmark):
            if ry > fh - 80:
                remaining = 21 - idx
                txt(frame, f"...+{remaining} more", (lx, ry), 0.32, C_DIM)
                ry += ROW - 6
                break

            # Fingertip rows get a colour tint
            row_c = C_CYAN if idx in FINGERTIP_IDS else C_PRI

            # Alternate row shading for readability
            if idx % 2 == 0:
                alpha_fill(frame, lx-2, ry-14, lx+rw+2, ry+4,
                           C_CARD, alpha=0.40)

            txt(frame, f"{idx:2d}", (col_id, ry), 0.32, row_c)
            txt(frame, f"{lm.x:.3f}", (col_x,  ry), 0.32, C_SEC)
            txt(frame, f"{lm.y:.3f}", (col_y,  ry), 0.32, C_SEC)
            txt(frame, f"{lm.z:.3f}", (col_z,  ry), 0.32, C_DIM)
            ry += ROW - 6

        ry += 4

    # ─────────────────────────────────────────────────────────────────
    # ⑤ DISTANCES
    # ─────────────────────────────────────────────────────────────────
    if hands and ry < fh - 40:
        ry = section_header(frame, "⑤ DISTANCES", lx, ry, DBG_W)
        hand = hands[0]
        d    = hand.dist

        # Primary distance (thumb ↔ index) shown large
        txt(frame, "Thumb ↔ Index", (lx, ry), 0.38, C_SEC);  ry += ROW - 4
        txt(frame, f"{d.px:.0f} px   {d.cm:.2f} cm",
            (lx, ry), 0.46, d.colour, bold=True);              ry += ROW

        # Calibration reference
        _dbg_row(frame, lx, ry, rw, "Ref span",
                 f"{d.ref_px:.0f} px", C_DIM);                 ry += ROW + 2

        # All 10 tip-pair distances in a compact 2-column grid
        col_w2 = rw // 2
        pairs  = list(d.tip_pairs.items())
        for row_i in range(0, len(pairs), 2):
            if ry > fh - 20:
                break
            for col_i in range(2):
                pi = row_i + col_i
                if pi >= len(pairs):
                    continue
                key, val = pairs[pi]
                fx  = lx + col_i * col_w2
                c   = dist_color(val)
                txt(frame, key,         (fx,    ry), 0.32, C_DIM)
                txt(frame, f"{val:.0f}", (fx+30, ry), 0.33, c)
            ry += ROW - 6


# ═══════════════════════════════════════════════════════════════════
# SECTION 10 — HELPER: key-value debug row
# ═══════════════════════════════════════════════════════════════════

def _dbg_row(frame, x: int, y: int, w: int,
             key: str, val: str, val_color: tuple) -> None:
    """
    Draws one key: value row inside the debug panel.
    Key is left-aligned in dim colour; value right-aligned in val_color.
    """
    txt(frame, f"{key}:", (x, y), 0.38, C_SEC)
    (vw, _), _ = cv2.getTextSize(val, FONT, 0.40, 1)
    txt(frame, val, (x + w - vw, y), 0.40, val_color)


# ═══════════════════════════════════════════════════════════════════
# SECTION 11 — FPS COUNTER
# ═══════════════════════════════════════════════════════════════════

class FPSCounter:
    """Rolling-average FPS counter that also tracks frame time in ms."""

    def __init__(self, window: int = 30) -> None:
        self._ts: deque = deque(maxlen=window)
        self.last_ms: float = 0.0

    def tick(self) -> float:
        now = time.monotonic()
        if self._ts:
            self.last_ms = (now - self._ts[-1]) * 1000
        self._ts.append(now)
        if len(self._ts) < 2:
            return 0.0
        elapsed = self._ts[-1] - self._ts[0]
        return (len(self._ts) - 1) / elapsed if elapsed > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════
# SECTION 12 — CAMERA SETUP
# ═══════════════════════════════════════════════════════════════════

def open_camera(index: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {index}.")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS,          30)
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"[INFO] Camera {index}: {w}x{h} @ {fps:.0f}fps")
    return cap


# ═══════════════════════════════════════════════════════════════════
# SECTION 13 — MAIN LOOP
# ═══════════════════════════════════════════════════════════════════
#
# Per-frame pipeline:
#
#   read → flip → BGR→RGB → MediaPipe inference
#     ↓
#   build list of HandDebugData (one per detected hand)
#     ↓
#   for each hand:
#     draw_skeleton()            → bone lines
#     draw_landmark_dots()       → numbered dots + tip rings
#     draw_bounding_box()        → corner brackets + crosshair
#     draw_distance_line()       → thumb↔index line + chip
#     ↓
#   draw_top_bar()               → full-width top bar
#   if debug_on:
#     draw_debug_panel()         → right-side panel (5 sections)
#     ↓
#   imshow → waitKey → D / Q
# ───────────────────────────────────────────────────────────────────

def run(camera_index: int = 0, max_hands: int = 2,
        flip: bool = True) -> None:
    """Main debugger loop."""

    cap         = open_camera(camera_index)
    fps_counter = FPSCounter(window=30)
    debug_on    = True     # D toggles this

    # ── Handedness smoother ───────────────────────────────────────────
    SMOOTH_N      = 7
    label_history = [deque(maxlen=SMOOTH_N), deque(maxlen=SMOOTH_N)]

    def stable_label(slot: int, raw: str) -> str:
        label_history[slot].append(raw)
        return max(set(label_history[slot]), key=label_history[slot].count)

    with mp_hands.Hands(
        static_image_mode        = False,
        max_num_hands            = max_hands,
        min_detection_confidence = 0.7,
        min_tracking_confidence  = 0.6,
    ) as hands_model:

        print("[INFO] Gesture Debugger running.")
        print("       D = toggle debug panel    Q = quit")

        while True:

            # ── 1. Capture ────────────────────────────────────────────
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Camera read failed.")
                break

            if flip:
                frame = cv2.flip(frame, 1)

            fh, fw = frame.shape[:2]

            # ── 2. MediaPipe inference ────────────────────────────────
            rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands_model.process(rgb)

            # Reset smoother when no hands visible
            if not results.multi_hand_landmarks:
                for h in label_history:
                    h.clear()

            # ── 3. Build debug data with smoothed labels ──────────────
            hands: list[HandDebugData] = []
            if results.multi_hand_landmarks:
                for slot, (lm, hd) in enumerate(zip(
                        results.multi_hand_landmarks,
                        results.multi_handedness)):
                    raw = hd.classification[0].label
                    hd.classification[0].label = stable_label(slot, raw)
                    hands.append(build_debug_data(lm, hd, fw, fh))

            # ── 4. Camera-feed overlays (always visible) ──────────────
            for hand in hands:
                draw_skeleton(frame, hand, fw, fh)
                draw_landmark_dots(frame, hand, fw, fh)
                draw_bounding_box(frame, hand)
                draw_distance_line(frame, hand, fw, fh)

            # ── 5. Top bar ────────────────────────────────────────────
            fps      = fps_counter.tick()
            frame_ms = fps_counter.last_ms
            draw_top_bar(frame, fps, debug_on, len(hands), fw)

            # ── 6. Debug panel (toggled by D) ─────────────────────────
            if debug_on:
                draw_debug_panel(frame, hands, fps, frame_ms, fw, fh)

            # ── 7. Display ────────────────────────────────────────────
            cv2.imshow("GestureOS AI — Gesture Debugger", frame)

            # ── 8. Key handling ───────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q")):
                print("[INFO] Quit.")
                break
            elif key in (ord("d"), ord("D")):
                debug_on = not debug_on
                print(f"[INFO] Debug panel {'ON' if debug_on else 'OFF'}")

    # ── Cleanup ───────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Done.")


# ═══════════════════════════════════════════════════════════════════
# SECTION 14 — CLI & ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GestureOS AI — Gesture Debugger"
    )
    p.add_argument("--camera",    type=int, default=0,
                   help="Camera index (default 0 = laptop built-in webcam)")
    p.add_argument("--max-hands", type=int, default=2, choices=[1, 2],
                   help="Max hands (default 2)")
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
