"""
GestureOS AI — Thumb-to-Index Distance Meter
==============================================
Measures the real-time pixel distance between the thumb tip (ID 4)
and index fingertip (ID 8) using MediaPipe hand landmarks.

WHAT IS DISPLAYED
──────────────────
  On the camera feed:
    • Hand skeleton + landmark dots
    • A measurement line connecting thumb tip → index tip
      - Colour changes: GREEN (close) → AMBER (mid) → RED (far)
      - Animated dashes along the line show the measurement is live
    • A filled circle on each endpoint (thumb = cyan, index = amber)
    • A distance label floating at the midpoint of the line
    • A midpoint dot on the line

  Info panel (top-right):
    • Current pixel distance
    • Current cm distance (calibrated)
    • Min / Max / Avg distances this session
    • Real-time mini sparkline graph of recent distances
    • Calibration hint

  HUD (top-left):
    • FPS counter

HOW PIXEL → CM CONVERSION WORKS
──────────────────────────────────
  We don't have a real depth sensor, so we use a simple reference
  calibration:  the distance between INDEX MCP (knuckle, ID 5) and
  PINKY MCP (ID 17) is approximately 7 cm on an average adult hand.

  ref_px  = pixel distance between landmark 5 and 17 (measured live)
  ref_cm  = REFERENCE_CM  (constant = 7.0 cm)
  cm_per_px = ref_cm / ref_px
  result_cm = measured_px * cm_per_px

  This self-calibrates every frame based on how close the hand is
  to the camera — no manual setup needed.

CONTROLS
  Q  → Quit
  R  → Reset session min/max/avg

Usage:
  python distance_meter.py
  python distance_meter.py --camera 1
  python distance_meter.py --no-flip
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

import cv2
import mediapipe as mp
import numpy as np


# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — MEDIAPIPE SETUP
# ═══════════════════════════════════════════════════════════════════

mp_hands = mp.solutions.hands


# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — CONSTANTS
# ═══════════════════════════════════════════════════════════════════

# MediaPipe landmark IDs we care about
THUMB_TIP  = 4    # tip of thumb
INDEX_TIP  = 8    # tip of index finger
INDEX_MCP  = 5    # index finger base knuckle  } used for
PINKY_MCP  = 17   # pinky finger base knuckle  } cm calibration

# Calibration: real-world distance between INDEX_MCP and PINKY_MCP
# on an average adult hand is ~7 cm
REFERENCE_CM = 7.0

# Distance thresholds for colour coding the measurement line (pixels)
# These are relative; actual pixel counts depend on camera distance.
# Tune these to taste.
DIST_CLOSE   = 80    # <= 80 px → green
DIST_MID     = 200   # 80–200 px → amber
# > 200 px → red

# ── Colour palette (BGR) ──────────────────────────────────────────
C_THUMB       = (255, 220, 0  )   # cyan-yellow  — thumb tip dot
C_INDEX       = (0,   190, 255)   # amber        — index tip dot
C_CLOSE       = (80,  210, 80 )   # green        — line when close
C_MID         = (0,   200, 255)   # amber        — line at mid range
C_FAR         = (60,  60,  220)   # red          — line when far
C_MIDPOINT    = (255, 255, 255)   # white        — midpoint dot
C_LABEL_BG    = (18,  18,  36 )   # dark navy    — label background
C_LABEL_TEXT  = (235, 235, 245)   # near-white   — label text
C_PANEL_BG    = (22,  24,  44 )   # panel background
C_PANEL_BDR   = (55,  60,  100)   # panel border
C_CARD_BG     = (30,  32,  56 )   # card interior
C_DIVIDER     = (40,  44,  72 )   # row divider
C_TEXT_PRI    = (235, 235, 245)   # primary text
C_TEXT_SEC    = (140, 145, 175)   # secondary text
C_TEXT_DIM    = (80,  84,  120)   # dim text
C_FPS         = (80,  210, 80 )   # FPS counter
C_BLACK       = (0,   0,   0  )
C_SKELETON    = (100, 105, 150)   # bone lines
C_DOT         = (210, 215, 240)   # landmark dots

FONT    = cv2.FONT_HERSHEY_SIMPLEX
FONT_BD = cv2.FONT_HERSHEY_DUPLEX
LINE_AA = cv2.LINE_AA


# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — SESSION STATS
# ═══════════════════════════════════════════════════════════════════
#
# Tracks minimum, maximum, and a rolling average of pixel distances
# across the entire session so we can display them in the panel.
#
# history deque feeds the sparkline graph in the panel.
# ───────────────────────────────────────────────────────────────────

@dataclass
class SessionStats:
    """Accumulates distance measurements for the current session."""
    min_px:  float = float("inf")
    max_px:  float = 0.0
    history: deque = field(default_factory=lambda: deque(maxlen=80))

    def update(self, px: float) -> None:
        self.min_px = min(self.min_px, px)
        self.max_px = max(self.max_px, px)
        self.history.append(px)

    @property
    def avg_px(self) -> float:
        return sum(self.history) / len(self.history) if self.history else 0.0

    def reset(self) -> None:
        self.min_px  = float("inf")
        self.max_px  = 0.0
        self.history.clear()


# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — DISTANCE COMPUTATION
# ═══════════════════════════════════════════════════════════════════
#
# Euclidean distance in pixel space:
#   d = √( (x2−x1)² + (y2−y1)² )
#
# We use math.hypot(dx, dy) which is equivalent to the above but
# is slightly faster and avoids overflow for large values.
#
# All landmark coordinates from MediaPipe are normalised (0.0–1.0).
# We multiply by frame dimensions to get pixel coordinates before
# passing them here.
# ───────────────────────────────────────────────────────────────────

def pixel_distance(p1: tuple[int, int], p2: tuple[int, int]) -> float:
    """
    Returns the Euclidean distance between two pixel points.

    Args:
        p1: (x, y) of the first point in pixels.
        p2: (x, y) of the second point in pixels.

    Returns:
        Distance as a float in pixels.
    """
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def px_to_cm(px_dist: float, ref_px: float) -> float:
    """
    Converts a pixel distance to centimetres using a live reference.

    The reference is the pixel distance between INDEX_MCP (landmark 5)
    and PINKY_MCP (landmark 17), which is ~7 cm on an average hand.

    Args:
        px_dist : The distance to convert, in pixels.
        ref_px  : Current pixel span of the reference segment.

    Returns:
        Estimated distance in cm, or 0.0 if ref_px is too small.
    """
    if ref_px < 1.0:
        return 0.0
    cm_per_px = REFERENCE_CM / ref_px
    return px_dist * cm_per_px


def get_line_color(px_dist: float) -> tuple:
    """
    Returns the BGR colour for the measurement line based on distance.
    Green = close, Amber = mid, Red = far.
    """
    if px_dist <= DIST_CLOSE:
        return C_CLOSE
    if px_dist <= DIST_MID:
        return C_MID
    return C_FAR


def landmark_px(lm_list, idx: int, frame_w: int, frame_h: int) -> tuple[int, int]:
    """
    Converts a normalised landmark to pixel coordinates.

    Args:
        lm_list : hand_landmarks.landmark  (list of 21 normalised points)
        idx     : Landmark index (0–20)
        frame_w : Frame width in pixels
        frame_h : Frame height in pixels

    Returns:
        (x, y) in pixels as integers.
    """
    lm = lm_list[idx]
    return (int(lm.x * frame_w), int(lm.y * frame_h))


# ═══════════════════════════════════════════════════════════════════
# SECTION 6 — MEASUREMENT LINE DRAWING
# ═══════════════════════════════════════════════════════════════════
#
# The measurement line has several visual layers drawn in order:
#
#   1. Faint shadow line  — thick dark line for contrast
#   2. Solid colour line  — colour-coded by distance
#   3. Animated dashes    — shows the measurement is live/updating
#   4. Endpoint dots      — filled circles at thumb and index tips
#   5. Midpoint dot       — white dot at the line centre
#   6. Distance label     — floating chip at the midpoint
#
# ANIMATED DASHES:
#   We use a dash offset that increments each frame.
#   By drawing alternating filled/empty segments offset by
#   `dash_offset % dash_period`, the dashes appear to march along
#   the line — a classic technique to show a measurement is live.
#
#   The offset is passed in from the main loop and incremented there.
# ───────────────────────────────────────────────────────────────────

def draw_measurement_line(
    frame,
    p_thumb: tuple[int, int],
    p_index: tuple[int, int],
    px_dist: float,
    cm_dist: float,
    dash_offset: int,
) -> None:
    """
    Draws the full measurement line from thumb tip to index tip.

    Args:
        frame       : BGR image (in-place).
        p_thumb     : (x, y) pixel position of the thumb tip.
        p_index     : (x, y) pixel position of the index tip.
        px_dist     : Current distance in pixels.
        cm_dist     : Current distance in centimetres.
        dash_offset : Frame counter used to animate the dashes.
    """
    line_color = get_line_color(px_dist)
    tx, ty = p_thumb
    ix, iy = p_index

    # ── Layer 1: Shadow (thick, dark) ────────────────────────────────
    # Drawn behind everything to give the line depth and separation
    # from the camera feed background.
    cv2.line(frame, (tx, ty), (ix, iy), C_BLACK, 7, LINE_AA)

    # ── Layer 2: Solid colour line ────────────────────────────────────
    cv2.line(frame, (tx, ty), (ix, iy), line_color, 3, LINE_AA)

    # ── Layer 3: Animated dashes ─────────────────────────────────────
    #
    # We parametrise the line as a set of points at regular intervals,
    # then draw alternating thick/thin segments offset by dash_offset.
    #
    # How it works:
    #   total_len = pixel length of the line
    #   n_steps   = number of dash-sized intervals along the line
    #   For each step i, compute the point at parameter t = i / n_steps
    #     x = tx + t*(ix-tx)
    #     y = ty + t*(iy-ty)
    #   If (i + dash_offset) is even, draw a bright white dot there.
    # ─────────────────────────────────────────────────────────────────
    DASH_SPACING = 12   # pixels between each potential dash dot
    if px_dist > 0:
        n_steps = max(1, int(px_dist / DASH_SPACING))
        for i in range(n_steps + 1):
            t  = i / n_steps
            dx = int(tx + t * (ix - tx))
            dy = int(ty + t * (iy - ty))
            if (i + dash_offset // 2) % 3 == 0:   # every 3rd dash is lit
                cv2.circle(frame, (dx, dy), 2, (255, 255, 255), -1, LINE_AA)

    # ── Layer 4: Endpoint dots ────────────────────────────────────────
    #
    # Draw a filled circle at each tip:
    #   Thumb → cyan-yellow   (C_THUMB)
    #   Index → amber         (C_INDEX)
    # Each dot has a black outline ring for contrast against any background.
    # ─────────────────────────────────────────────────────────────────

    # Thumb tip dot
    cv2.circle(frame, (tx, ty), 12, C_BLACK, -1, LINE_AA)   # outline
    cv2.circle(frame, (tx, ty), 9,  C_THUMB, -1, LINE_AA)   # fill
    cv2.circle(frame, (tx, ty), 4,  C_BLACK, -1, LINE_AA)   # inner pupil

    # Index tip dot
    cv2.circle(frame, (ix, iy), 12, C_BLACK, -1, LINE_AA)
    cv2.circle(frame, (ix, iy), 9,  C_INDEX, -1, LINE_AA)
    cv2.circle(frame, (ix, iy), 4,  C_BLACK, -1, LINE_AA)

    # Endpoint labels: tiny "T" and "I" above each dot
    cv2.putText(frame, "T", (tx - 4, ty - 15), FONT, 0.38, C_THUMB, 1, LINE_AA)
    cv2.putText(frame, "I", (ix - 4, iy - 15), FONT, 0.38, C_INDEX, 1, LINE_AA)

    # ── Layer 5: Midpoint dot ─────────────────────────────────────────
    mx = (tx + ix) // 2
    my = (ty + iy) // 2
    cv2.circle(frame, (mx, my), 6, C_BLACK,     -1, LINE_AA)
    cv2.circle(frame, (mx, my), 4, C_MIDPOINT,  -1, LINE_AA)

    # ── Layer 6: Distance label chip ─────────────────────────────────
    #
    # A filled rounded-ish rectangle floats at the line midpoint.
    # It shows both the pixel distance and the cm estimate.
    #
    # Layout:  "128 px  |  4.2 cm"
    #
    # We measure the text width with cv2.getTextSize() to centre
    # the chip over the midpoint dot.
    # ─────────────────────────────────────────────────────────────────
    draw_distance_label(frame, mx, my, px_dist, cm_dist, line_color)


def draw_distance_label(
    frame,
    mx: int, my: int,
    px_dist: float,
    cm_dist: float,
    accent: tuple,
) -> None:
    """
    Draws a floating info chip at (mx, my) showing pixel + cm values.

    The chip sits ABOVE the midpoint dot, connected by a small stem line.

    Args:
        frame   : BGR image (in-place).
        mx, my  : Midpoint pixel coordinates.
        px_dist : Distance in pixels.
        cm_dist : Distance in centimetres.
        accent  : Border colour matching the line colour.
    """
    px_str = f"{px_dist:.0f} px"
    cm_str = f"{cm_dist:.1f} cm"

    # Measure both text strings to size the chip
    (pw, ph), _ = cv2.getTextSize(px_str, FONT,   0.52, 1)
    (cw, ch), _ = cv2.getTextSize(cm_str, FONT_BD, 0.58, 1)

    chip_w  = max(pw, cw) + 24
    chip_h  = ph + ch + 20
    pad     = 8

    # Position chip above the midpoint
    chip_x  = mx - chip_w // 2
    chip_y  = my - chip_h - 20

    # Clamp so it stays in frame
    frame_h, frame_w = frame.shape[:2]
    chip_x = max(4, min(chip_x, frame_w - chip_w - 4))
    chip_y = max(4, min(chip_y, frame_h - chip_h - 4))

    # Stem line from midpoint dot up to chip bottom
    stem_x = chip_x + chip_w // 2
    cv2.line(frame, (mx, my - 6), (stem_x, chip_y + chip_h),
             accent, 1, LINE_AA)

    # Chip background (semi-transparent)
    ov = frame.copy()
    cv2.rectangle(ov, (chip_x, chip_y),
                  (chip_x + chip_w, chip_y + chip_h),
                  C_LABEL_BG, -1, LINE_AA)
    cv2.addWeighted(ov, 0.82, frame, 0.18, 0, frame)

    # Chip border in accent colour
    cv2.rectangle(frame, (chip_x, chip_y),
                  (chip_x + chip_w, chip_y + chip_h),
                  accent, 1, LINE_AA)

    # Divider between px and cm rows
    mid_line_y = chip_y + pad + ph + 4
    cv2.line(frame, (chip_x + 6, mid_line_y),
             (chip_x + chip_w - 6, mid_line_y),
             C_DIVIDER, 1, LINE_AA)

    # Pixel row (smaller, secondary)
    cv2.putText(frame, px_str,
                (chip_x + (chip_w - pw) // 2, chip_y + pad + ph),
                FONT, 0.52, C_TEXT_SEC, 1, LINE_AA)

    # cm row (larger, primary — this is the headline number)
    cv2.putText(frame, cm_str,
                (chip_x + (chip_w - cw) // 2, chip_y + chip_h - pad),
                FONT_BD, 0.58, C_TEXT_PRI, 1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 7 — INFO PANEL  (top-right corner)
# ═══════════════════════════════════════════════════════════════════
#
# Shows:
#   • Current pixel distance  (large, colour-coded)
#   • Current cm distance     (large, primary)
#   • Session min / max / avg
#   • Sparkline graph of recent px distances
#   • Colour legend for the line
#   • Calibration note
# ───────────────────────────────────────────────────────────────────

PANEL_W = 230
PANEL_H = 310

def draw_info_panel(
    frame,
    px_dist: float,
    cm_dist: float,
    stats: SessionStats,
    frame_w: int,
    frame_h: int,
) -> None:
    """
    Draws the distance stats panel in the top-right corner.

    Args:
        frame   : BGR image (in-place).
        px_dist : Current distance in pixels.
        cm_dist : Current distance in cm.
        stats   : SessionStats accumulator.
        frame_w : Frame width.
        frame_h : Frame height.
    """
    px = frame_w - PANEL_W - 10
    py = 10

    # ── Panel background ──────────────────────────────────────────────
    ov = frame.copy()
    cv2.rectangle(ov, (px, py), (px + PANEL_W, py + PANEL_H),
                  C_PANEL_BG, -1, LINE_AA)
    cv2.addWeighted(ov, 0.88, frame, 0.12, 0, frame)
    cv2.rectangle(frame, (px, py), (px + PANEL_W, py + PANEL_H),
                  C_PANEL_BDR, 1, LINE_AA)

    lx  = px + 12       # left text x
    ry  = py + 22       # running y cursor
    rw  = PANEL_W - 24  # usable row width

    # ── Section header ────────────────────────────────────────────────
    cv2.putText(frame, "DISTANCE METER", (lx, ry),
                FONT, 0.42, C_TEXT_DIM, 1, LINE_AA)
    ry += 6
    cv2.line(frame, (lx, ry), (px + PANEL_W - 12, ry), C_DIVIDER, 1, LINE_AA)
    ry += 18

    # ── Current pixel distance ────────────────────────────────────────
    line_c = get_line_color(px_dist)
    cv2.putText(frame, "Distance", (lx, ry), FONT, 0.42, C_TEXT_SEC, 1, LINE_AA)
    ry += 4

    # Large pixel value
    px_label = f"{px_dist:.0f} px"
    (tw, th), _ = cv2.getTextSize(px_label, FONT_BD, 0.80, 2)
    cv2.putText(frame, px_label, (lx + 1, ry + th + 1),
                FONT_BD, 0.80, C_BLACK, 3, LINE_AA)
    cv2.putText(frame, px_label, (lx, ry + th),
                FONT_BD, 0.80, line_c, 2, LINE_AA)
    ry += th + 10

    # Large cm value
    cm_label = f"{cm_dist:.1f} cm"
    (cw, ch), _ = cv2.getTextSize(cm_label, FONT_BD, 0.75, 2)
    cv2.putText(frame, cm_label, (lx + 1, ry + ch + 1),
                FONT_BD, 0.75, C_BLACK, 3, LINE_AA)
    cv2.putText(frame, cm_label, (lx, ry + ch),
                FONT_BD, 0.75, C_TEXT_PRI, 2, LINE_AA)
    ry += ch + 14

    cv2.line(frame, (lx, ry), (px + PANEL_W - 12, ry), C_DIVIDER, 1, LINE_AA)
    ry += 14

    # ── Session statistics ────────────────────────────────────────────
    cv2.putText(frame, "SESSION", (lx, ry), FONT, 0.40, C_TEXT_DIM, 1, LINE_AA)
    ry += 18

    min_val = stats.min_px if stats.min_px != float("inf") else 0.0
    stat_rows = [
        ("Min",  f"{min_val:.0f} px"),
        ("Max",  f"{stats.max_px:.0f} px"),
        ("Avg",  f"{stats.avg_px:.0f} px"),
    ]
    for label, value in stat_rows:
        cv2.putText(frame, f"{label}:", (lx, ry), FONT, 0.42, C_TEXT_SEC, 1, LINE_AA)
        (vw, _), _ = cv2.getTextSize(value, FONT, 0.44, 1)
        cv2.putText(frame, value, (px + PANEL_W - 12 - vw, ry),
                    FONT, 0.44, C_TEXT_PRI, 1, LINE_AA)
        ry += 20

    ry += 4
    cv2.line(frame, (lx, ry), (px + PANEL_W - 12, ry), C_DIVIDER, 1, LINE_AA)
    ry += 12

    # ── Sparkline graph ───────────────────────────────────────────────
    #
    # Draws a small waveform of recent pixel distance history.
    # Y-axis: 0 at bottom, max_dist at top (auto-scaled to session max).
    # Each sample is a vertical bar 1px wide.
    # ─────────────────────────────────────────────────────────────────
    cv2.putText(frame, "History", (lx, ry), FONT, 0.40, C_TEXT_DIM, 1, LINE_AA)
    ry += 10

    graph_h  = 36
    graph_w  = rw
    graph_x  = lx
    graph_yb = ry + graph_h  # bottom of graph

    # Graph background
    ov2 = frame.copy()
    cv2.rectangle(ov2, (graph_x, ry), (graph_x + graph_w, graph_yb),
                  C_CARD_BG, -1, LINE_AA)
    cv2.addWeighted(ov2, 0.70, frame, 0.30, 0, frame)

    samples = list(stats.history)
    if len(samples) > 1:
        max_val = max(max(samples), 1.0)
        bar_w   = max(1, graph_w // len(samples))
        for i, s in enumerate(samples):
            bar_h = int((s / max_val) * graph_h)
            bx_   = graph_x + i * bar_w
            by_   = graph_yb - bar_h
            bar_c = get_line_color(s)
            cv2.rectangle(frame, (bx_, by_), (bx_ + bar_w - 1, graph_yb),
                          bar_c, -1, LINE_AA)

    cv2.rectangle(frame, (graph_x, ry), (graph_x + graph_w, graph_yb),
                  C_PANEL_BDR, 1, LINE_AA)
    ry = graph_yb + 14

    # ── Colour legend ─────────────────────────────────────────────────
    legend = [
        (C_CLOSE, f"<= {DIST_CLOSE}px"),
        (C_MID,   f"<= {DIST_MID}px"),
        (C_FAR,   f"> {DIST_MID}px"),
    ]
    lx2 = lx
    for dot_c, lbl in legend:
        cv2.circle(frame, (lx2 + 5, ry - 3), 4, dot_c, -1, LINE_AA)
        cv2.putText(frame, lbl, (lx2 + 14, ry), FONT, 0.32, C_TEXT_SEC, 1, LINE_AA)
        lx2 += PANEL_W // 3

    ry += 14
    cv2.putText(frame, "[R] Reset  [Q] Quit", (lx, ry),
                FONT, 0.35, C_TEXT_DIM, 1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 8 — HAND SKELETON DRAWING
# ═══════════════════════════════════════════════════════════════════

def draw_skeleton(frame, hand_landmarks, frame_w: int, frame_h: int) -> None:
    """Draws the grey bone skeleton for one hand."""
    for s_id, e_id in mp_hands.HAND_CONNECTIONS:
        s = hand_landmarks.landmark[s_id]
        e = hand_landmarks.landmark[e_id]
        x1, y1 = int(s.x * frame_w), int(s.y * frame_h)
        x2, y2 = int(e.x * frame_w), int(e.y * frame_h)
        cv2.line(frame, (x1, y1), (x2, y2), C_SKELETON, 2, LINE_AA)


def draw_dots(frame, hand_landmarks, frame_w: int, frame_h: int) -> None:
    """Draws small white circles on all 21 landmark positions."""
    for lm in hand_landmarks.landmark:
        cx_ = int(lm.x * frame_w)
        cy_ = int(lm.y * frame_h)
        cv2.circle(frame, (cx_, cy_), 4, C_DOT,   -1, LINE_AA)
        cv2.circle(frame, (cx_, cy_), 4, C_BLACK,  1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 9 — FPS COUNTER
# ═══════════════════════════════════════════════════════════════════

class FPSCounter:
    """Rolling-average FPS counter."""

    def __init__(self, window: int = 30) -> None:
        self._ts: deque = deque(maxlen=window)

    def tick(self) -> float:
        self._ts.append(time.monotonic())
        if len(self._ts) < 2:
            return 0.0
        elapsed = self._ts[-1] - self._ts[0]
        return (len(self._ts) - 1) / elapsed if elapsed > 0 else 0.0


def draw_fps(frame, fps: float) -> None:
    """FPS badge pinned to the top-left corner."""
    label = f"FPS: {fps:.1f}"
    cv2.putText(frame, label, (17, 39), FONT, 0.7, C_BLACK, 4, LINE_AA)
    cv2.putText(frame, label, (16, 38), FONT, 0.7, C_FPS,   2, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 10 — NO HAND HINT
# ═══════════════════════════════════════════════════════════════════

def draw_no_hand(frame) -> None:
    """Centred hint when no hand is detected."""
    h, w = frame.shape[:2]
    lines = ["Show your hand", "to the camera"]
    for i, line in enumerate(lines):
        (tw, th), _ = cv2.getTextSize(line, FONT, 0.7, 2)
        tx = (w - tw) // 2
        ty = h // 2 + i * (th + 14) - 10
        cv2.putText(frame, line, (tx+1, ty+1), FONT, 0.7, C_BLACK,    3, LINE_AA)
        cv2.putText(frame, line, (tx,   ty  ), FONT, 0.7, C_TEXT_SEC, 2, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 11 — CAMERA SETUP
# ═══════════════════════════════════════════════════════════════════

def open_camera(index: int) -> cv2.VideoCapture:
    """Opens the webcam at `index`, requests 720p @ 30fps."""
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
    print(f"[INFO] Camera {index} ready: {w}x{h} @ {fps:.0f}fps")
    return cap


# ═══════════════════════════════════════════════════════════════════
# SECTION 12 — MAIN LOOP
# ═══════════════════════════════════════════════════════════════════
#
# Per-frame pipeline:
#
#   read → flip → BGR→RGB → MediaPipe inference
#     ↓
#   hand detected?
#     YES:
#       1. Get pixel coords of thumb tip (4) and index tip (8)
#       2. Get pixel coords of INDEX_MCP (5) and PINKY_MCP (17)
#          → compute reference span for cm calibration
#       3. Compute px distance between thumb and index
#       4. Convert px → cm using live calibration
#       5. Update SessionStats
#       6. draw_skeleton()
#       7. draw_dots()
#       8. draw_measurement_line()  ← the animated line + label
#       9. draw_info_panel()
#     NO:
#       draw_no_hand()
#     ↓
#   draw_fps()
#   increment dash_offset for animation
#   imshow → waitKey → Q / R
# ───────────────────────────────────────────────────────────────────

def run(camera_index: int = 0, flip: bool = True) -> None:
    """
    Main distance-measurement loop.

    Args:
        camera_index : Webcam index (0 = laptop built-in).
        flip         : Mirror the frame (recommended).
    """
    cap         = open_camera(camera_index)
    fps_counter = FPSCounter(window=30)
    stats       = SessionStats()
    dash_offset = 0   # incremented each frame to animate dashes

    with mp_hands.Hands(
        static_image_mode        = False,
        max_num_hands            = 1,          # only 1 hand needed
        min_detection_confidence = 0.7,
        min_tracking_confidence  = 0.6,
    ) as hands_model:

        print("[INFO] Distance meter running. Hold up one hand.")
        print("       Q=Quit  R=Reset stats")

        while True:

            # ── 1. Capture frame ──────────────────────────────────────
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Camera read failed.")
                break

            if flip:
                frame = cv2.flip(frame, 1)

            frame_h, frame_w = frame.shape[:2]

            # ── 2. MediaPipe inference ────────────────────────────────
            rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands_model.process(rgb)

            if results.multi_hand_landmarks:
                hand_lm = results.multi_hand_landmarks[0]   # first hand only
                lm_list = hand_lm.landmark

                # ── 3. Landmark pixel positions ───────────────────────
                p_thumb = landmark_px(lm_list, THUMB_TIP, frame_w, frame_h)
                p_index = landmark_px(lm_list, INDEX_TIP, frame_w, frame_h)

                # Reference segment for cm calibration
                p_idx_mcp  = landmark_px(lm_list, INDEX_MCP, frame_w, frame_h)
                p_pnk_mcp  = landmark_px(lm_list, PINKY_MCP, frame_w, frame_h)
                ref_px     = pixel_distance(p_idx_mcp, p_pnk_mcp)

                # ── 4. Compute distances ──────────────────────────────
                px_dist = pixel_distance(p_thumb, p_index)
                cm_dist = px_to_cm(px_dist, ref_px)

                # ── 5. Update session stats ───────────────────────────
                stats.update(px_dist)

                # ── 6. Draw skeleton + dots ───────────────────────────
                draw_skeleton(frame, hand_lm, frame_w, frame_h)
                draw_dots(frame,     hand_lm, frame_w, frame_h)

                # ── 7. Draw animated measurement line + label ─────────
                draw_measurement_line(
                    frame, p_thumb, p_index,
                    px_dist, cm_dist, dash_offset,
                )

                # ── 8. Draw info panel ────────────────────────────────
                draw_info_panel(frame, px_dist, cm_dist, stats,
                                frame_w, frame_h)

            else:
                draw_no_hand(frame)

            # ── 9. FPS + dash animation tick ──────────────────────────
            fps = fps_counter.tick()
            draw_fps(frame, fps)
            dash_offset += 1   # increment every frame → dashes march

            # ── 10. Display ───────────────────────────────────────────
            cv2.imshow("GestureOS AI — Distance Meter", frame)

            # ── 11. Key handling ──────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q")):
                print("[INFO] Quit.")
                break
            elif key in (ord("r"), ord("R")):
                stats.reset()
                print("[INFO] Session stats reset.")

    # ── Cleanup ───────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Done.")


# ═══════════════════════════════════════════════════════════════════
# SECTION 13 — CLI & ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GestureOS AI — Thumb-to-Index Distance Meter"
    )
    p.add_argument("--camera",  type=int, default=0,
                   help="Camera index (default 0 = laptop built-in webcam)")
    p.add_argument("--no-flip", action="store_true",
                   help="Disable horizontal mirror mode")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        camera_index = args.camera,
        flip         = not args.no_flip,
    )
