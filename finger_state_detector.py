"""
GestureOS AI — Finger State Detector
======================================
Detects whether each of the 5 fingers is UP or DOWN in real time
using MediaPipe hand landmarks and OpenCV.

HOW FINGER STATE IS DETERMINED
───────────────────────────────
MediaPipe gives us 21 landmarks per hand, each with (x, y, z) coords
normalised to the range 0.0–1.0 relative to the frame size.

  y = 0.0  →  top of frame
  y = 1.0  →  bottom of frame

So a SMALLER y value means HIGHER on screen (closer to the top).

For the 4 fingers (index, middle, ring, pinky):
  ┌─────────────────────────────────────────────────────────────┐
  │  Finger is UP   → fingertip y  <  PIP joint y              │
  │  Finger is DOWN → fingertip y  >= PIP joint y              │
  └─────────────────────────────────────────────────────────────┘
  The PIP joint is the second knuckle from the base.
  When a finger is extended, the tip rises above the PIP joint.
  When curled, the tip drops below or stays level with the PIP.

For the THUMB (special case):
  The thumb moves horizontally, not vertically.
  ┌─────────────────────────────────────────────────────────────┐
  │  RIGHT hand: thumb UP → tip x  >  IP joint x  (tip to right)│
  │  LEFT  hand: thumb UP → tip x  <  IP joint x  (tip to left) │
  └─────────────────────────────────────────────────────────────┘
  We compare the x-axis (horizontal) instead of y-axis, and we
  flip the logic depending on which hand we're looking at.

Landmark IDs used:
  THUMB:  TIP=4   IP=3
  INDEX:  TIP=8   PIP=6
  MIDDLE: TIP=12  PIP=10
  RING:   TIP=16  PIP=14
  PINKY:  TIP=20  PIP=18

Features:
  ✦ Per-finger UP/DOWN state with emoji indicator
  ✦ Count of fingers currently raised
  ✦ Supports 2 hands simultaneously
  ✦ Hand skeleton + landmark dots overlay
  ✦ Semi-transparent finger-state panel per hand
  ✦ FPS counter
  ✦ Press Q to quit

Usage:
  python finger_state_detector.py
  python finger_state_detector.py --camera 1
  python finger_state_detector.py --max-hands 1 --no-flip
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
# SECTION 2 — MEDIAPIPE INITIALISATION
# ═══════════════════════════════════════════════════════════════════

mp_hands          = mp.solutions.hands
mp_drawing        = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — LANDMARK ID REFERENCE MAP
# ═══════════════════════════════════════════════════════════════════
#
# These are the exact landmark indices MediaPipe uses.
# Each finger has 4 joints: MCP → PIP → DIP → TIP
#
#   ID  Joint name
#    0  WRIST
#    1  THUMB_CMC   2  THUMB_MCP   3  THUMB_IP    4  THUMB_TIP
#    5  INDEX_MCP   6  INDEX_PIP   7  INDEX_DIP   8  INDEX_TIP
#    9  MID_MCP    10  MID_PIP    11  MID_DIP    12  MID_TIP
#   13  RING_MCP   14  RING_PIP   15  RING_DIP   16  RING_TIP
#   17  PINKY_MCP  18  PINKY_PIP  19  PINKY_DIP  20  PINKY_TIP
#
# For UP/DOWN detection we only need TIP and PIP (or IP for thumb).
# ───────────────────────────────────────────────────────────────────

# (tip_id, pip_id) for the four non-thumb fingers
FINGER_JOINTS: dict[str, tuple[int, int]] = {
    "Index":  (8,  6),
    "Middle": (12, 10),
    "Ring":   (16, 14),
    "Pinky":  (20, 18),
}

# Thumb uses its own IDs (tip and IP joint)
THUMB_TIP_ID = 4
THUMB_IP_ID  = 3


# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — COLOUR PALETTE  (BGR order for OpenCV)
# ═══════════════════════════════════════════════════════════════════

CLR_UP       = (80,  210, 80 )   # green  — finger is UP
CLR_DOWN     = (60,  60,  220)   # red    — finger is DOWN
CLR_FPS      = (0,   230, 0  )   # bright green — FPS text
CLR_WHITE    = (230, 230, 230)   # soft white
CLR_BLACK    = (0,   0,   0  )   # shadow / outline
CLR_PANEL    = (15,  15,  35 )   # very dark navy — panel background
CLR_BORDER   = (60,  60,  110)   # dim purple — panel border
CLR_SKELETON = (180, 180, 180)   # light grey — bone lines
CLR_DOT      = (255, 255, 255)   # white — landmark dots
CLR_TIP_UP   = (80,  210, 80 )   # green dot on raised fingertip
CLR_TIP_DOWN = (60,  60,  220)   # red dot on curled fingertip

FONT    = cv2.FONT_HERSHEY_SIMPLEX
LINE_AA = cv2.LINE_AA


# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — FINGER STATE DATACLASS
# ═══════════════════════════════════════════════════════════════════
#
# A simple container that holds the UP/DOWN state of all 5 fingers
# for one hand, plus a helper property that counts raised fingers.
#
# Using a dataclass (Python 3.7+) gives us:
#   • Auto-generated __init__, __repr__, __eq__
#   • Clean, typed attribute access  (state.index, state.thumb, etc.)
# ───────────────────────────────────────────────────────────────────

@dataclass
class FingerState:
    """Stores the UP/DOWN boolean state for each finger on one hand."""
    thumb:  bool = False   # True = UP / extended
    index:  bool = False
    middle: bool = False
    ring:   bool = False
    pinky:  bool = False

    @property
    def raised_count(self) -> int:
        """Returns how many fingers are currently UP."""
        return sum([self.thumb, self.index, self.middle, self.ring, self.pinky])

    def as_list(self) -> list[tuple[str, bool]]:
        """Returns ordered list of (finger_name, is_up) for easy iteration."""
        return [
            ("Thumb",  self.thumb),
            ("Index",  self.index),
            ("Middle", self.middle),
            ("Ring",   self.ring),
            ("Pinky",  self.pinky),
        ]


# ═══════════════════════════════════════════════════════════════════
# SECTION 6 — FINGER STATE DETECTION LOGIC
# ═══════════════════════════════════════════════════════════════════
#
# This is the core algorithm.  All landmark coordinates are
# normalised floats: x goes left→right (0.0→1.0),
#                    y goes top→bottom (0.0→1.0).
#
# ── Non-thumb fingers (Index, Middle, Ring, Pinky) ──────────────────
#
#   Compare TIP y vs PIP y:
#     tip.y < pip.y  →  tip is ABOVE pip on screen  →  finger is UP
#     tip.y >= pip.y →  tip is AT or BELOW pip       →  finger is DOWN
#
#   Why PIP and not MCP?
#     MCP is the base knuckle — it barely moves.
#     PIP is the middle knuckle — it bends significantly when curling,
#     making it a reliable reference point for UP/DOWN classification.
#
# ── Thumb (special case) ────────────────────────────────────────────
#
#   The thumb abducts (moves) sideways, not vertically.
#   So we compare x coordinates instead of y.
#
#   For a RIGHT hand (as seen in mirrored/selfie view):
#     thumb is UP (open/extended) → TIP is to the RIGHT of IP joint
#     tip.x > ip.x  →  True (thumb extended)
#
#   For a LEFT hand the logic is mirrored:
#     thumb is UP → TIP is to the LEFT of IP joint
#     tip.x < ip.x  →  True (thumb extended)
#
#   The `handedness` parameter ("Left"/"Right") selects the right rule.
# ───────────────────────────────────────────────────────────────────

def _dist2d(a, b) -> float:
    """
    Euclidean distance between two normalised landmarks (x, y only).
    z is ignored because it's unreliable from a single RGB camera.
    """
    import math
    return math.hypot(a.x - b.x, a.y - b.y)


def detect_finger_states(hand_landmarks, handedness: str) -> FingerState:
    """
    Analyses landmark positions and returns the UP/DOWN state per finger.

    THUMB  : Distance-based. TIP must be far from WRIST and from IP.
             Handles front palm, back palm, fist, thumbs-up correctly.

    FINGERS: Dual-condition — tip must be ABOVE pip (y-axis, with small
             hysteresis) AND tip-to-mcp distance > mcp-to-wrist * 0.55.
             Prevents false UP when finger is bent sideways or partially curled.
    """
    lm = hand_landmarks.landmark

    # ── Thumb (distance-based, orientation-independent) ───────────────
    tip_dist  = _dist2d(lm[THUMB_TIP_ID], lm[0])   # TIP  → WRIST
    ip_dist   = _dist2d(lm[THUMB_IP_ID],  lm[0])   # IP   → WRIST
    tip_to_ip = _dist2d(lm[THUMB_TIP_ID], lm[THUMB_IP_ID])
    thumb_up = (tip_dist > ip_dist + 0.04) and (tip_to_ip > 0.04)

    # ── Four fingers — dual condition for accuracy ────────────────────
    def finger_up(tip_id: int, pip_id: int, mcp_id: int) -> bool:
        y_check    = lm[tip_id].y < lm[pip_id].y - 0.01    # hysteresis
        dist_check = _dist2d(lm[tip_id], lm[mcp_id]) > \
                     _dist2d(lm[mcp_id], lm[0]) * 0.55
        return y_check and dist_check

    return FingerState(
        thumb  = thumb_up,
        index  = finger_up(8,  6,  5),
        middle = finger_up(12, 10, 9),
        ring   = finger_up(16, 14, 13),
        pinky  = finger_up(20, 18, 17),
    )


# ═══════════════════════════════════════════════════════════════════
# SECTION 7 — FINGER STATE PANEL DRAWING
# ═══════════════════════════════════════════════════════════════════
#
# Draws a semi-transparent panel showing each finger's state.
# The panel is anchored below the hand's bounding box so it doesn't
# overlap the skeleton.
#
# Each row shows:
#   [●] FingerName   UP  ▲        ← green dot, "UP", up-arrow
#   [●] FingerName   DOWN ▼       ← red dot, "DOWN", down-arrow
#
# The raised-finger count is shown at the bottom of the panel.
#
# TRANSPARENCY:
#   We use the same addWeighted trick as before:
#     overlay = frame.copy()
#     draw rectangle on overlay
#     blend: output = overlay * 0.7 + frame * 0.3
# ───────────────────────────────────────────────────────────────────

def draw_finger_panel(
    frame,
    state: FingerState,
    hand_label: str,
    anchor_x: int,
    anchor_y: int,
) -> None:
    """
    Draws the finger-state info panel for one hand.

    Args:
        frame     : BGR image (modified in-place).
        state     : FingerState for this hand.
        hand_label: "Left" or "Right".
        anchor_x  : Left edge of the panel in pixels.
        anchor_y  : Top edge of the panel in pixels.
    """
    PANEL_W   = 200
    ROW_H     = 32      # vertical spacing between finger rows
    PADDING   = 12      # inner padding
    N_ROWS    = 5       # one per finger
    PANEL_H   = PADDING + N_ROWS * ROW_H + 40   # +40 for header + count row

    frame_h, frame_w = frame.shape[:2]

    # Clamp panel so it stays inside the frame
    px = max(0, min(anchor_x, frame_w - PANEL_W - 4))
    py = max(0, min(anchor_y, frame_h - PANEL_H - 4))

    # ── Semi-transparent background ───────────────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay,
                  (px, py), (px + PANEL_W, py + PANEL_H),
                  CLR_PANEL, -1, LINE_AA)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

    # ── Panel border ──────────────────────────────────────────────────
    cv2.rectangle(frame,
                  (px, py), (px + PANEL_W, py + PANEL_H),
                  CLR_BORDER, 1, LINE_AA)

    # ── Header row: "Left Hand" / "Right Hand" ────────────────────────
    header_color = (255, 140, 0) if hand_label == "Left" else (0, 140, 255)
    cv2.putText(frame, f"{hand_label} Hand",
                (px + PADDING, py + 22),
                FONT, 0.6, header_color, 2, LINE_AA)

    # ── Divider line below header ─────────────────────────────────────
    cv2.line(frame,
             (px + PADDING, py + 28),
             (px + PANEL_W - PADDING, py + 28),
             CLR_BORDER, 1, LINE_AA)

    # ── One row per finger ────────────────────────────────────────────
    #
    # state.as_list() returns:
    #   [("Thumb", True), ("Index", False), ("Middle", True), …]
    #
    # For each finger we draw:
    #   • A coloured filled circle (green=UP, red=DOWN)
    #   • The finger name in white
    #   • "UP ▲" or "DOWN ▼" in the matching colour
    # ─────────────────────────────────────────────────────────────────
    row_y = py + 28 + ROW_H - 6   # starting y for first data row

    for finger_name, is_up in state.as_list():
        dot_color  = CLR_UP   if is_up else CLR_DOWN
        state_text = "UP"     if is_up else "DOWN"
        arrow      = " ^"     if is_up else " v"   # ASCII arrows (font has no emoji)

        # Dot indicator
        cv2.circle(frame, (px + PADDING + 6, row_y - 4), 6, dot_color, -1, LINE_AA)
        cv2.circle(frame, (px + PADDING + 6, row_y - 4), 6, CLR_BLACK, 1,  LINE_AA)

        # Finger name (white)
        cv2.putText(frame, finger_name,
                    (px + PADDING + 18, row_y),
                    FONT, 0.5, CLR_WHITE, 1, LINE_AA)

        # State text + arrow (coloured)
        cv2.putText(frame, state_text + arrow,
                    (px + PANEL_W - 72, row_y),
                    FONT, 0.5, dot_color, 1, LINE_AA)

        row_y += ROW_H

    # ── Footer: raised count ──────────────────────────────────────────
    count_text = f"Raised: {state.raised_count} / 5"
    cv2.line(frame,
             (px + PADDING, row_y - 10),
             (px + PANEL_W - PADDING, row_y - 10),
             CLR_BORDER, 1, LINE_AA)
    cv2.putText(frame, count_text,
                (px + PADDING, row_y + 12),
                FONT, 0.52, CLR_FPS, 1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 8 — FINGERTIP COLOUR-CODED DOTS
# ═══════════════════════════════════════════════════════════════════
#
# Overlays a green dot on UP fingertips and a red dot on DOWN fingertips
# directly on the hand skeleton, so you can see state at a glance
# without looking at the panel.
# ───────────────────────────────────────────────────────────────────

# Maps each finger name to its (tip_id, pip_id) for drawing
_FINGER_TIP_IDS: list[tuple[str, int]] = [
    ("Thumb",  THUMB_TIP_ID),
    ("Index",  FINGER_JOINTS["Index"][0]),
    ("Middle", FINGER_JOINTS["Middle"][0]),
    ("Ring",   FINGER_JOINTS["Ring"][0]),
    ("Pinky",  FINGER_JOINTS["Pinky"][0]),
]

def draw_fingertip_states(frame, hand_landmarks, state: FingerState,
                          frame_w: int, frame_h: int) -> None:
    """
    Draws a colour-coded dot on each fingertip:
      Green ring = finger UP
      Red ring   = finger DOWN

    The ring is drawn around the existing landmark dot for visual clarity.
    """
    state_values = [state.thumb, state.index, state.middle, state.ring, state.pinky]

    for (name, tip_id), is_up in zip(_FINGER_TIP_IDS, state_values):
        lm  = hand_landmarks.landmark[tip_id]
        cx  = int(lm.x * frame_w)
        cy  = int(lm.y * frame_h)
        color = CLR_TIP_UP if is_up else CLR_TIP_DOWN

        # Outer ring (larger, coloured)
        cv2.circle(frame, (cx, cy), 14, color,    2, LINE_AA)
        # Inner dot (filled)
        cv2.circle(frame, (cx, cy), 7,  color,   -1, LINE_AA)
        cv2.circle(frame, (cx, cy), 7,  CLR_BLACK, 1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 9 — HAND SKELETON DRAWING
# ═══════════════════════════════════════════════════════════════════

def draw_skeleton(frame, hand_landmarks, frame_w: int, frame_h: int) -> None:
    """Draws grey bone lines between all landmark connections."""
    for start_id, end_id in mp_hands.HAND_CONNECTIONS:
        s = hand_landmarks.landmark[start_id]
        e = hand_landmarks.landmark[end_id]
        x1, y1 = int(s.x * frame_w), int(s.y * frame_h)
        x2, y2 = int(e.x * frame_w), int(e.y * frame_h)
        cv2.line(frame, (x1, y1), (x2, y2), CLR_SKELETON, 2, LINE_AA)


def draw_all_dots(frame, hand_landmarks, frame_w: int, frame_h: int) -> None:
    """Draws small white dots on all 21 landmarks (under the fingertip rings)."""
    for lm in hand_landmarks.landmark:
        cx = int(lm.x * frame_w)
        cy = int(lm.y * frame_h)
        cv2.circle(frame, (cx, cy), 4, CLR_DOT,   -1, LINE_AA)
        cv2.circle(frame, (cx, cy), 4, CLR_BLACK,  1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 10 — BOUNDING BOX HELPER
# ═══════════════════════════════════════════════════════════════════

def get_bounding_box(hand_landmarks, frame_w: int, frame_h: int,
                     padding: int = 24) -> tuple[int, int, int, int]:
    """Returns (x, y, w, h) bounding box from landmark min/max extents."""
    xs = [lm.x * frame_w for lm in hand_landmarks.landmark]
    ys = [lm.y * frame_h for lm in hand_landmarks.landmark]
    x1 = max(0,       int(min(xs)) - padding)
    y1 = max(0,       int(min(ys)) - padding)
    x2 = min(frame_w, int(max(xs)) + padding)
    y2 = min(frame_h, int(max(ys)) + padding)
    return (x1, y1, x2 - x1, y2 - y1)


# ═══════════════════════════════════════════════════════════════════
# SECTION 11 — FPS COUNTER
# ═══════════════════════════════════════════════════════════════════

class FPSCounter:
    """Rolling-average FPS counter using a sliding timestamp window."""

    def __init__(self, window: int = 30) -> None:
        self._ts: deque[float] = deque(maxlen=window)

    def tick(self) -> float:
        self._ts.append(time.monotonic())
        if len(self._ts) < 2:
            return 0.0
        elapsed = self._ts[-1] - self._ts[0]
        return (len(self._ts) - 1) / elapsed if elapsed > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════
# SECTION 12 — SMALL HUD HELPERS
# ═══════════════════════════════════════════════════════════════════

def draw_fps(frame, fps: float) -> None:
    """FPS counter in top-left corner with shadow."""
    cv2.putText(frame, f"FPS: {fps:.1f}", (17, 39),
                FONT, 0.8, CLR_BLACK, 4, LINE_AA)
    cv2.putText(frame, f"FPS: {fps:.1f}", (16, 38),
                FONT, 0.8, CLR_FPS, 2, LINE_AA)


def draw_instructions(frame) -> None:
    """'Press Q to quit' pinned to the bottom-left corner."""
    h = frame.shape[0]
    cv2.putText(frame, "Press Q to quit", (17, h - 15),
                FONT, 0.55, CLR_BLACK, 3, LINE_AA)
    cv2.putText(frame, "Press Q to quit", (16, h - 16),
                FONT, 0.55, CLR_WHITE, 1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 13 — CAMERA SETUP
# ═══════════════════════════════════════════════════════════════════

def open_camera(index: int) -> cv2.VideoCapture:
    """Opens the webcam at `index`, requests 720p@30fps."""
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
#   for each detected hand:
#     1. detect_finger_states()         ← UP/DOWN logic (Section 6)
#     2. draw_skeleton()                ← grey bone lines
#     3. draw_all_dots()                ← white joint dots
#     4. draw_fingertip_states()        ← green/red rings on tips
#     5. draw_finger_panel()            ← info panel below hand
#     ↓
#   draw_fps()
#   draw_instructions()
#   imshow → waitKey → Q?
# ───────────────────────────────────────────────────────────────────

def run(camera_index: int = 0, max_hands: int = 2, flip: bool = True) -> None:
    """
    Main finger-state detection loop.

    Args:
        camera_index : Webcam index (0 = laptop built-in).
        max_hands    : 1 or 2 simultaneous hands.
        flip         : Mirror the frame horizontally.
    """
    cap         = open_camera(camera_index)
    fps_counter = FPSCounter(window=30)

    # ── Handedness smoother ───────────────────────────────────────────
    # MediaPipe flickers Left/Right when the hand moves fast.
    # We keep a rolling deque of the last SMOOTH_N labels per hand slot
    # (slot 0 = first detected hand, slot 1 = second).
    # The majority label in the deque is used instead of the raw one.
    SMOOTH_N = 15
    label_history = [deque(maxlen=SMOOTH_N), deque(maxlen=SMOOTH_N)]

    def stable_label(slot: int, raw: str) -> str:
        label_history[slot].append(raw)
        return max(set(label_history[slot]),
                   key=label_history[slot].count)

    with mp_hands.Hands(
        static_image_mode        = False,
        max_num_hands            = max_hands,
        min_detection_confidence = 0.75,
        min_tracking_confidence  = 0.65,
    ) as hands_model:

        print("[INFO] Finger state detector running. Press Q to quit.")

        while True:

            # ── 1. Capture frame ──────────────────────────────────────
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Camera read failed — exiting.")
                break

            if flip:
                frame = cv2.flip(frame, 1)   # mirror mode

            frame_h, frame_w = frame.shape[:2]

            # ── 2. MediaPipe inference (needs RGB) ────────────────────
            rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands_model.process(rgb)

            # Reset smoother slots when hand count changes
            num_detected = len(results.multi_hand_landmarks) \
                           if results.multi_hand_landmarks else 0
            if num_detected == 0:
                for h in label_history:
                    h.clear()

            # ── 3. Per-hand processing ────────────────────────────────
            if results.multi_hand_landmarks:
                for slot, (hand_landmarks, handedness) in enumerate(zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness,
                )):
                    raw_label  = handedness.classification[0].label
                    hand_label = stable_label(slot, raw_label)   # smoothed

                    # ── Core detection ────────────────────────────────
                    state = detect_finger_states(hand_landmarks, hand_label)

                    # ── Draw skeleton (lines first, dots on top) ──────
                    draw_skeleton(frame, hand_landmarks, frame_w, frame_h)
                    draw_all_dots(frame, hand_landmarks, frame_w, frame_h)

                    # ── Colour-coded fingertip rings ──────────────────
                    draw_fingertip_states(frame, hand_landmarks, state,
                                          frame_w, frame_h)

                    # ── Finger state info panel ───────────────────────
                    bbox    = get_bounding_box(hand_landmarks, frame_w, frame_h)
                    panel_x = bbox[0]
                    panel_y = bbox[1] + bbox[3] + 8

                    draw_finger_panel(frame, state, hand_label, panel_x, panel_y)

            # ── 4. HUD overlays ───────────────────────────────────────
            fps = fps_counter.tick()
            draw_fps(frame, fps)
            draw_instructions(frame)

            # ── 5. Display ────────────────────────────────────────────
            cv2.imshow("GestureOS AI — Finger State Detector", frame)

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
        description="GestureOS AI — Finger State Detector (UP/DOWN per finger)"
    )
    p.add_argument("--camera",    type=int, default=0,
                   help="Camera index (default 0 = laptop built-in webcam)")
    p.add_argument("--max-hands", type=int, default=2, choices=[1, 2],
                   help="Max hands to detect simultaneously (default 2)")
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
