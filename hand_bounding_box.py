"""
GestureOS AI — Hand Bounding Box
==================================
Draws a detailed bounding box around each detected hand with:

  ✦ Cornered rectangle (professional tracker style)
  ✦ Hand center crosshair + dot
  ✦ Width and height dimensions in pixels
  ✦ Confidence score from MediaPipe
  ✦ Left / Right hand label chip
  ✦ Info panel: W × H, center coords, confidence, hand label
  ✦ Hand skeleton + landmark dots underneath
  ✦ FPS counter
  ✦ Press Q to quit

HOW EACH FEATURE WORKS
───────────────────────

  BOUNDING BOX
    We iterate all 21 landmarks, collect their (x, y) pixel
    coordinates, then take min/max to get the tightest box.
    A padding value is added so fingertips are never clipped.

  CENTER POINT
    center_x = box_x + box_width  / 2
    center_y = box_y + box_height / 2
    Drawn as a filled circle + crosshair lines.

  WIDTH & HEIGHT
    Directly from the box dimensions in pixels.
    Displayed as dimension labels on the box edges.

  CONFIDENCE SCORE
    MediaPipe returns a score (0.0–1.0) per hand via:
      handedness.classification[0].score
    Shown as a percentage in the info panel.

Usage:
  python hand_bounding_box.py
  python hand_bounding_box.py --camera 1
  python hand_bounding_box.py --max-hands 1 --no-flip
"""

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — IMPORTS
# ═══════════════════════════════════════════════════════════════════

import argparse
import sys
import time
from collections import deque
from dataclasses import dataclass

import cv2
import mediapipe as mp


# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — MEDIAPIPE SETUP
# ═══════════════════════════════════════════════════════════════════

mp_hands = mp.solutions.hands


# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — COLOUR PALETTE  (all BGR — not RGB)
# ═══════════════════════════════════════════════════════════════════
#
# Every colour constant is defined here once.
# BGR means the channel order is (Blue, Green, Red).
# ───────────────────────────────────────────────────────────────────

# Bounding box colours — different per hand for instant identification
CLR_RIGHT_BOX   = (0,   200, 255)   # amber/gold  — right hand
CLR_LEFT_BOX    = (255, 160, 0  )   # cyan/blue   — left hand

# Center point and crosshair
CLR_CENTER_DOT  = (0,   255, 255)   # bright yellow
CLR_CROSSHAIR   = (0,   255, 255)   # same yellow — crosshair lines

# Dimension labels on box edges
CLR_DIMENSION   = (200, 255, 200)   # light green

# Info panel
CLR_PANEL_BG    = (10,  10,  28 )   # very dark navy
CLR_PANEL_BORDER= (60,  60,  110)   # dim purple
CLR_LABEL_KEY   = (130, 130, 160)   # dim grey — key text
CLR_LABEL_VAL   = (230, 230, 230)   # bright white — value text
CLR_CONF_HIGH   = (80,  210, 80 )   # green  — confidence >= 90 %
CLR_CONF_MED    = (0,   200, 255)   # amber  — confidence 75–90 %
CLR_CONF_LOW    = (60,  60,  220)   # red    — confidence < 75 %

# Skeleton & dots
CLR_SKELETON    = (140, 140, 140)   # grey bone lines
CLR_DOT_FILL    = (255, 255, 255)   # white dots
CLR_DOT_BORDER  = (0,   0,   0  )   # black dot outline

# HUD
CLR_FPS         = (0,   230, 0  )   # bright green
CLR_HINT        = (200, 200, 200)   # soft white
CLR_BLACK       = (0,   0,   0  )   # shadow

FONT   = cv2.FONT_HERSHEY_SIMPLEX
LINE_AA = cv2.LINE_AA


# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — HandBox DATACLASS
# ═══════════════════════════════════════════════════════════════════
#
# A typed container that stores everything we compute about one hand's
# bounding box.  Separating computation (Section 5) from drawing
# (Sections 6–9) keeps the code easier to read and test.
#
# Fields:
#   x, y        — top-left corner of the box in pixels
#   w, h        — width and height of the box in pixels
#   cx, cy      — center pixel of the box
#   confidence  — MediaPipe detection score (0.0 – 1.0)
#   label       — "Left" or "Right"
# ───────────────────────────────────────────────────────────────────

@dataclass
class HandBox:
    """All computed bounding-box properties for one detected hand."""
    x:          int     # top-left x
    y:          int     # top-left y
    w:          int     # width  in pixels
    h:          int     # height in pixels
    cx:         int     # center x
    cy:         int     # center y
    confidence: float   # MediaPipe score  0.0–1.0
    label:      str     # "Left" | "Right"

    @property
    def x2(self) -> int:
        """Bottom-right x corner."""
        return self.x + self.w

    @property
    def y2(self) -> int:
        """Bottom-right y corner."""
        return self.y + self.h

    @property
    def color(self) -> tuple:
        """Box colour chosen by hand label."""
        return CLR_RIGHT_BOX if self.label == "Right" else CLR_LEFT_BOX

    @property
    def conf_color(self) -> tuple:
        """Confidence value colour: green / amber / red based on score."""
        if self.confidence >= 0.90:
            return CLR_CONF_HIGH
        if self.confidence >= 0.75:
            return CLR_CONF_MED
        return CLR_CONF_LOW


# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — BOUNDING BOX COMPUTATION
# ═══════════════════════════════════════════════════════════════════
#
# MediaPipe landmark coordinates are NORMALISED floats (0.0 → 1.0).
# To get pixel positions:
#   pixel_x = landmark.x * frame_width
#   pixel_y = landmark.y * frame_height
#
# Steps:
#   1. Extract pixel x and y values for all 21 landmarks.
#   2. Find min/max to get the tight bounding extents.
#   3. Add a padding margin so the box isn't flush with the fingertips.
#   4. Clamp to frame boundaries so the box never goes off-screen.
#   5. Compute center = (x + w/2, y + h/2).
#   6. Read confidence from MediaPipe's handedness classification.
# ───────────────────────────────────────────────────────────────────

def compute_hand_box(
    hand_landmarks,
    handedness,
    frame_w: int,
    frame_h: int,
    padding: int = 28,
) -> HandBox:
    """
    Computes the HandBox for one detected hand.

    Args:
        hand_landmarks : MediaPipe NormalizedLandmarkList (21 points).
        handedness     : MediaPipe Classification object (label + score).
        frame_w        : Frame width  in pixels.
        frame_h        : Frame height in pixels.
        padding        : Extra pixels to expand the box on all sides.

    Returns:
        A HandBox dataclass with all geometric and metadata fields filled.
    """
    # ── Step 1: Convert normalised → pixel coordinates ───────────────
    #
    # landmark.x and .y are 0.0–1.0; we scale to pixel space.
    # We collect all 21 x-coords and 21 y-coords separately.
    # ─────────────────────────────────────────────────────────────────
    xs = [lm.x * frame_w for lm in hand_landmarks.landmark]
    ys = [lm.y * frame_h for lm in hand_landmarks.landmark]

    # ── Step 2: Tight bounding extents ────────────────────────────────
    raw_x1 = min(xs)
    raw_y1 = min(ys)
    raw_x2 = max(xs)
    raw_y2 = max(ys)

    # ── Step 3: Add padding ────────────────────────────────────────────
    x1 = raw_x1 - padding
    y1 = raw_y1 - padding
    x2 = raw_x2 + padding
    y2 = raw_y2 + padding

    # ── Step 4: Clamp to frame (can't draw outside the image) ─────────
    x1 = max(0,       int(x1))
    y1 = max(0,       int(y1))
    x2 = min(frame_w, int(x2))
    y2 = min(frame_h, int(y2))

    w = x2 - x1
    h = y2 - y1

    # ── Step 5: Center of the box ─────────────────────────────────────
    #
    # The center is the midpoint of the box, not the wrist landmark.
    # This gives a stable geometric center that doesn't jump with pose.
    # ─────────────────────────────────────────────────────────────────
    cx = x1 + w // 2
    cy = y1 + h // 2

    # ── Step 6: Confidence score ──────────────────────────────────────
    #
    # MediaPipe exposes a per-hand detection confidence via:
    #   handedness.classification[0].score  (float 0.0–1.0)
    #   handedness.classification[0].label  ("Left" or "Right")
    #
    # This is the model's certainty that it correctly detected a hand,
    # NOT a pose or gesture confidence — just "is there a hand here?".
    # ─────────────────────────────────────────────────────────────────
    confidence = handedness.classification[0].score
    label      = handedness.classification[0].label

    return HandBox(
        x=x1, y=y1, w=w, h=h,
        cx=cx, cy=cy,
        confidence=confidence,
        label=label,
    )


# ═══════════════════════════════════════════════════════════════════
# SECTION 6 — CORNERED RECTANGLE DRAWING
# ═══════════════════════════════════════════════════════════════════
#
# Instead of a plain rectangle we draw only the four corner brackets.
# This is a common style in object detection UIs — it looks cleaner
# than a full outline and keeps the hand visible inside the box.
#
# Each corner is two short lines:
#   Top-left:     horizontal right  +  vertical down
#   Top-right:    horizontal left   +  vertical down
#   Bottom-left:  horizontal right  +  vertical up
#   Bottom-right: horizontal left   +  vertical up
#
# corner_len controls how long each bracket arm is.
# We clamp it to 25% of the smaller box dimension so it always
# looks proportional regardless of hand size.
# ───────────────────────────────────────────────────────────────────

def draw_cornered_rect(frame, box: HandBox, corner_len: int = 28,
                       thickness: int = 3) -> None:
    """
    Draws a corner-bracket style bounding box (no full outline).

    Args:
        frame      : BGR image (in-place).
        box        : HandBox with position and colour.
        corner_len : Length of each bracket arm in pixels.
        thickness  : Line thickness.
    """
    x1, y1, x2, y2 = box.x, box.y, box.x2, box.y2
    c   = box.color
    th  = thickness

    # Clamp corner length so it never exceeds half the shortest side
    cl = min(corner_len, box.w // 4, box.h // 4)

    # ── Top-left corner ───────────────────────────────────────────────
    cv2.line(frame, (x1,      y1), (x1 + cl, y1),      c, th, LINE_AA)  # →
    cv2.line(frame, (x1,      y1), (x1,      y1 + cl),  c, th, LINE_AA)  # ↓

    # ── Top-right corner ──────────────────────────────────────────────
    cv2.line(frame, (x2,      y1), (x2 - cl, y1),      c, th, LINE_AA)  # ←
    cv2.line(frame, (x2,      y1), (x2,      y1 + cl),  c, th, LINE_AA)  # ↓

    # ── Bottom-left corner ────────────────────────────────────────────
    cv2.line(frame, (x1,      y2), (x1 + cl, y2),      c, th, LINE_AA)  # →
    cv2.line(frame, (x1,      y2), (x1,      y2 - cl),  c, th, LINE_AA)  # ↑

    # ── Bottom-right corner ───────────────────────────────────────────
    cv2.line(frame, (x2,      y2), (x2 - cl, y2),      c, th, LINE_AA)  # ←
    cv2.line(frame, (x2,      y2), (x2,      y2 - cl),  c, th, LINE_AA)  # ↑

    # ── Faint full outline (thin, low opacity via draw trick) ─────────
    #
    # A very thin semi-transparent rectangle gives spatial context
    # without distracting from the corner brackets.
    # Achieved by drawing on a copy then blending at low weight.
    # ─────────────────────────────────────────────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), c, 1, LINE_AA)
    cv2.addWeighted(overlay, 0.30, frame, 0.70, 0, frame)


# ═══════════════════════════════════════════════════════════════════
# SECTION 7 — CENTER POINT + CROSSHAIR
# ═══════════════════════════════════════════════════════════════════
#
# The center point is drawn as:
#   1. A small filled circle (the dot)
#   2. Four short lines radiating outward (the crosshair arms)
#
# The crosshair arms have a gap between them and the dot so it
# looks like a targeting reticle rather than a plain plus sign.
#
# We also print the pixel coordinates just below the dot so the
# user can see where the center is numerically.
# ───────────────────────────────────────────────────────────────────

def draw_center_point(frame, box: HandBox) -> None:
    """
    Draws the hand center as a crosshair + dot with coordinate label.

    Args:
        frame : BGR image (in-place).
        box   : HandBox — we use box.cx, box.cy for the center.
    """
    cx, cy = box.cx, box.cy
    arm    = 16    # length of each crosshair arm (pixels)
    gap    = 6     # gap between dot edge and arm start

    # ── Crosshair arms ────────────────────────────────────────────────
    #   Draw shadow first, then coloured line on top
    for pts in [
        ((cx - arm, cy), (cx - gap, cy)),   # left  arm
        ((cx + gap, cy), (cx + arm, cy)),   # right arm
        ((cx, cy - arm), (cx, cy - gap)),   # top   arm
        ((cx, cy + gap), (cx, cy + arm)),   # bottom arm
    ]:
        cv2.line(frame, pts[0], pts[1], CLR_BLACK,      3, LINE_AA)  # shadow
        cv2.line(frame, pts[0], pts[1], CLR_CROSSHAIR,  1, LINE_AA)  # colour

    # ── Center dot ────────────────────────────────────────────────────
    cv2.circle(frame, (cx, cy), 6, CLR_BLACK,      -1, LINE_AA)   # outline
    cv2.circle(frame, (cx, cy), 4, CLR_CENTER_DOT, -1, LINE_AA)   # fill

    # ── Coordinate label ─────────────────────────────────────────────
    #
    # Print "(cx, cy)" just below the crosshair.
    # Shadow pass first, then coloured text.
    # ─────────────────────────────────────────────────────────────────
    coord_text = f"({cx}, {cy})"
    lx = cx - 28
    ly = cy + 24
    cv2.putText(frame, coord_text, (lx + 1, ly + 1),
                FONT, 0.42, CLR_BLACK, 2, LINE_AA)
    cv2.putText(frame, coord_text, (lx, ly),
                FONT, 0.42, CLR_CENTER_DOT, 1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 8 — DIMENSION LABELS ON BOX EDGES
# ═══════════════════════════════════════════════════════════════════
#
# Width label  → printed centred on the TOP edge of the box
# Height label → printed centred on the RIGHT edge, rotated 90°
#
# For the width label we use cv2.putText at the midpoint of the
# top edge, offset upward so it doesn't sit on the corner brackets.
#
# For the height label, OpenCV putText can't natively rotate text,
# so we write it horizontally on the RIGHT side of the box, slightly
# outside it, which is readable and unambiguous.
# ───────────────────────────────────────────────────────────────────

def draw_dimensions(frame, box: HandBox) -> None:
    """
    Draws width and height pixel labels on the bounding box edges.

    Width  label → centred above the top edge.
    Height label → centred to the right of the right edge.

    Args:
        frame : BGR image (in-place).
        box   : HandBox with x, y, w, h, x2, y2.
    """
    color = CLR_DIMENSION

    # ── Width label (top edge, centred) ──────────────────────────────
    w_text = f"W: {box.w}px"
    (tw, _), _ = cv2.getTextSize(w_text, FONT, 0.48, 1)
    wx = box.x + (box.w - tw) // 2   # horizontally centred
    wy = box.y - 8                    # 8px above the top edge

    # Keep label inside the frame top
    wy = max(wy, 14)

    cv2.putText(frame, w_text, (wx + 1, wy + 1), FONT, 0.48, CLR_BLACK, 2, LINE_AA)
    cv2.putText(frame, w_text, (wx,     wy    ), FONT, 0.48, color,     1, LINE_AA)

    # ── Height label (right edge, centred vertically) ─────────────────
    h_text = f"H: {box.h}px"
    (th, _), _ = cv2.getTextSize(h_text, FONT, 0.48, 1)
    hx = box.x2 + 8                       # 8px to the right of the box
    hy = box.y + (box.h + th) // 2        # vertically centred

    # Clamp so label doesn't go off the right edge
    frame_w = frame.shape[1]
    if hx + th > frame_w:
        hx = box.x - th - 8              # flip to the left side if needed

    cv2.putText(frame, h_text, (hx + 1, hy + 1), FONT, 0.48, CLR_BLACK, 2, LINE_AA)
    cv2.putText(frame, h_text, (hx,     hy    ), FONT, 0.48, color,     1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 9 — INFO PANEL (confidence + stats)
# ═══════════════════════════════════════════════════════════════════
#
# A small semi-transparent panel anchored to the top-left corner
# of the bounding box shows:
#
#   Hand:        Right / Left
#   Confidence:  97.3 %       ← colour-coded green/amber/red
#   Size:        W × H
#   Center:      (cx, cy)
#
# CONFIDENCE COLOUR CODING:
#   ≥ 90%  → green  (very confident)
#   75–90% → amber  (confident)
#   < 75%  → red    (uncertain)
#
# The panel is drawn ABOVE the box top edge.
# If there's no room above (box near the top of the frame),
# it shifts to appear inside the box at the top instead.
# ───────────────────────────────────────────────────────────────────

def draw_info_panel(frame, box: HandBox) -> None:
    """
    Draws the information panel above the bounding box.

    Args:
        frame : BGR image (in-place).
        box   : HandBox — all fields are used.
    """
    PANEL_W  = 200
    PANEL_H  = 96
    PADDING  = 8
    ROW_H    = 20

    frame_h, frame_w = frame.shape[:2]

    # Anchor: top-left corner of the box, shifted upward
    px = box.x
    py = box.y - PANEL_H - 6

    # If panel would go off the top, place it inside the box instead
    if py < 0:
        py = box.y + 6

    # Clamp horizontally
    px = max(0, min(px, frame_w - PANEL_W - 2))

    # ── Semi-transparent background ───────────────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay,
                  (px, py), (px + PANEL_W, py + PANEL_H),
                  CLR_PANEL_BG, -1, LINE_AA)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # ── Border ────────────────────────────────────────────────────────
    cv2.rectangle(frame,
                  (px, py), (px + PANEL_W, py + PANEL_H),
                  box.color, 1, LINE_AA)

    # ── Data rows ────────────────────────────────────────────────────
    #
    # Each row: left-side key label (dim)  +  right-side value (bright).
    # We define rows as (key_text, value_text, value_colour) tuples.
    # ─────────────────────────────────────────────────────────────────
    conf_pct   = box.confidence * 100
    rows = [
        ("Hand",       box.label,                            box.color),
        ("Confidence", f"{conf_pct:.1f}%",                   box.conf_color),
        ("Size",       f"{box.w} x {box.h} px",             CLR_LABEL_VAL),
        ("Center",     f"({box.cx}, {box.cy})",              CLR_CENTER_DOT),
    ]

    ry = py + PADDING + ROW_H - 2   # starting y for first row

    for key, val, val_color in rows:
        # Key text (dim)
        cv2.putText(frame, f"{key}:",
                    (px + PADDING, ry),
                    FONT, 0.42, CLR_LABEL_KEY, 1, LINE_AA)
        # Value text (bright, right-aligned in panel)
        cv2.putText(frame, val,
                    (px + PADDING + 88, ry),
                    FONT, 0.44, val_color, 1, LINE_AA)
        ry += ROW_H


# ═══════════════════════════════════════════════════════════════════
# SECTION 10 — HAND SKELETON DRAWING
# ═══════════════════════════════════════════════════════════════════

def draw_skeleton(frame, hand_landmarks, frame_w: int, frame_h: int) -> None:
    """Draws grey bone connections between all 21 landmark points."""
    for start_id, end_id in mp_hands.HAND_CONNECTIONS:
        s = hand_landmarks.landmark[start_id]
        e = hand_landmarks.landmark[end_id]
        x1, y1 = int(s.x * frame_w), int(s.y * frame_h)
        x2, y2 = int(e.x * frame_w), int(e.y * frame_h)
        cv2.line(frame, (x1, y1), (x2, y2), CLR_SKELETON, 2, LINE_AA)


def draw_dots(frame, hand_landmarks, frame_w: int, frame_h: int) -> None:
    """Draws a small white circle at each of the 21 landmark positions."""
    for lm in hand_landmarks.landmark:
        cx = int(lm.x * frame_w)
        cy = int(lm.y * frame_h)
        cv2.circle(frame, (cx, cy), 5, CLR_DOT_FILL,   -1, LINE_AA)
        cv2.circle(frame, (cx, cy), 5, CLR_DOT_BORDER,  1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 11 — FPS COUNTER
# ═══════════════════════════════════════════════════════════════════

class FPSCounter:
    """Rolling-average FPS using a sliding window of timestamps."""

    def __init__(self, window: int = 30) -> None:
        self._ts: deque[float] = deque(maxlen=window)

    def tick(self) -> float:
        self._ts.append(time.monotonic())
        if len(self._ts) < 2:
            return 0.0
        elapsed = self._ts[-1] - self._ts[0]
        return (len(self._ts) - 1) / elapsed if elapsed > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════
# SECTION 12 — HUD HELPERS
# ═══════════════════════════════════════════════════════════════════

def draw_fps(frame, fps: float) -> None:
    """FPS badge in the top-left corner."""
    cv2.putText(frame, f"FPS: {fps:.1f}", (17, 39),
                FONT, 0.8, CLR_BLACK, 4, LINE_AA)
    cv2.putText(frame, f"FPS: {fps:.1f}", (16, 38),
                FONT, 0.8, CLR_FPS,   2, LINE_AA)


def draw_instructions(frame) -> None:
    """Quit hint pinned to the bottom-left corner."""
    h = frame.shape[0]
    cv2.putText(frame, "Press Q to quit", (17, h - 15),
                FONT, 0.55, CLR_BLACK, 3, LINE_AA)
    cv2.putText(frame, "Press Q to quit", (16, h - 16),
                FONT, 0.55, CLR_HINT,  1, LINE_AA)


def draw_no_hand_hint(frame) -> None:
    """
    Shown when no hand is detected — prompts the user to show their hand.
    Centred vertically and horizontally in the frame.
    """
    h, w = frame.shape[:2]
    text  = "Show your hand to the camera"
    (tw, th), _ = cv2.getTextSize(text, FONT, 0.7, 2)
    tx = (w - tw) // 2
    ty = (h + th) // 2

    cv2.putText(frame, text, (tx + 1, ty + 1), FONT, 0.7, CLR_BLACK,    3, LINE_AA)
    cv2.putText(frame, text, (tx,     ty    ), FONT, 0.7, CLR_HINT,     2, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 13 — CAMERA SETUP
# ═══════════════════════════════════════════════════════════════════

def open_camera(index: int) -> cv2.VideoCapture:
    """Opens webcam at `index`, requests 720p @ 30fps."""
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
# SECTION 14 — MAIN LOOP
# ═══════════════════════════════════════════════════════════════════
#
# Per-frame pipeline:
#
#   read → flip → BGR→RGB → MediaPipe inference
#     ↓
#   hands found?
#     YES → for each hand:
#       compute_hand_box()       ← Section 5  (geometry + confidence)
#       draw_skeleton()          ← Section 10 (bone lines)
#       draw_dots()              ← Section 10 (landmark dots)
#       draw_cornered_rect()     ← Section 6  (bracket-style box)
#       draw_center_point()      ← Section 7  (crosshair + coords)
#       draw_dimensions()        ← Section 8  (W/H labels on edges)
#       draw_info_panel()        ← Section 9  (confidence + stats)
#     NO → draw_no_hand_hint()
#     ↓
#   draw_fps()
#   draw_instructions()
#   imshow → waitKey → Q?
# ───────────────────────────────────────────────────────────────────

def run(camera_index: int = 0, max_hands: int = 2, flip: bool = True) -> None:
    """
    Main bounding-box detection loop.

    Args:
        camera_index : Webcam index (0 = laptop built-in).
        max_hands    : 1 or 2 hands detected simultaneously.
        flip         : Mirror the frame (recommended).
    """
    cap         = open_camera(camera_index)
    fps_counter = FPSCounter(window=30)

    with mp_hands.Hands(
        static_image_mode        = False,
        max_num_hands            = max_hands,
        min_detection_confidence = 0.7,
        min_tracking_confidence  = 0.6,
    ) as hands_model:

        print("[INFO] Hand bounding box running. Press Q to quit.")

        while True:

            # ── Read + pre-process ────────────────────────────────────
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Camera read failed — exiting.")
                break

            if flip:
                frame = cv2.flip(frame, 1)

            frame_h, frame_w = frame.shape[:2]

            # BGR → RGB for MediaPipe
            rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands_model.process(rgb)

            # ── Per-hand rendering ────────────────────────────────────
            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness,
                ):
                    # 1. Compute all bounding-box geometry + confidence
                    box = compute_hand_box(
                        hand_landmarks, handedness, frame_w, frame_h
                    )

                    # 2. Draw skeleton and dots UNDER the box visuals
                    draw_skeleton(frame, hand_landmarks, frame_w, frame_h)
                    draw_dots(frame, hand_landmarks, frame_w, frame_h)

                    # 3. Cornered bounding rectangle
                    draw_cornered_rect(frame, box)

                    # 4. Center crosshair + coordinate label
                    draw_center_point(frame, box)

                    # 5. Width / Height dimension labels on edges
                    draw_dimensions(frame, box)

                    # 6. Info panel: hand label, confidence, size, center
                    draw_info_panel(frame, box)

            else:
                # No hand detected — show a helpful prompt
                draw_no_hand_hint(frame)

            # ── HUD ───────────────────────────────────────────────────
            fps = fps_counter.tick()
            draw_fps(frame, fps)
            draw_instructions(frame)

            # ── Display ───────────────────────────────────────────────
            cv2.imshow("GestureOS AI — Hand Bounding Box", frame)

            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                print("[INFO] Quit.")
                break

    # ── Cleanup ───────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Done.")


# ═══════════════════════════════════════════════════════════════════
# SECTION 15 — CLI & ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GestureOS AI — Hand Bounding Box with center, dimensions, confidence"
    )
    p.add_argument("--camera",    type=int, default=0,
                   help="Camera index (default 0 = laptop built-in webcam)")
    p.add_argument("--max-hands", type=int, default=2, choices=[1, 2],
                   help="Max simultaneous hands (default 2)")
    p.add_argument("--no-flip",   action="store_true",
                   help="Disable horizontal mirror mode")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        camera_index = args.camera,
        max_hands    = args.max_hands,
        flip         = not args.no_flip,
    )
