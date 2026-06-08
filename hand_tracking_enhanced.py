"""
GestureOS AI — Enhanced Hand Tracking
=======================================
Builds on hand_tracking.py with a richer per-landmark visualisation:

  ✦ Every landmark dot is drawn manually with its own colour
  ✦ Landmark ID number is printed beside each dot
  ✦ Fingertips (IDs 4, 8, 12, 16, 20) are highlighted in a bright accent colour
  ✦ Palm / knuckle joints use a separate colour
  ✦ Wrist (ID 0) gets its own distinct colour
  ✦ Bounding box + Left / Right label per hand
  ✦ HUD panel showing total landmarks detected this frame
  ✦ Rolling-average FPS counter
  ✦ Press Q to quit

Usage:
  python hand_tracking_enhanced.py
  python hand_tracking_enhanced.py --camera 1
  python hand_tracking_enhanced.py --max-hands 1 --no-flip
"""

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — IMPORTS
# ═══════════════════════════════════════════════════════════════════

import argparse
import sys
import time
from collections import deque

import cv2
import mediapipe as mp


# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — MEDIAPIPE SETUP
# ═══════════════════════════════════════════════════════════════════

mp_hands          = mp.solutions.hands
mp_drawing        = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — LANDMARK ANATOMY  (the 21 MediaPipe hand points)
# ═══════════════════════════════════════════════════════════════════
#
# MediaPipe numbers every joint 0–20.  The map below lets us look up
# the human-readable name for any ID — useful for the legend panel.
#
#   0          → WRIST
#   1– 4       → THUMB  (CMC → MCP → IP → TIP)
#   5– 8       → INDEX  (MCP → PIP → DIP → TIP)
#   9–12       → MIDDLE (MCP → PIP → DIP → TIP)
#  13–16       → RING   (MCP → PIP → DIP → TIP)
#  17–20       → PINKY  (MCP → PIP → DIP → TIP)
#
# FINGERTIP IDs — the outermost point on each finger:
#   Thumb=4  Index=8  Middle=12  Ring=16  Pinky=20
# ───────────────────────────────────────────────────────────────────

LANDMARK_NAMES: dict[int, str] = {
    0:  "WRIST",
    1:  "THUMB_CMC",  2:  "THUMB_MCP",  3:  "THUMB_IP",   4:  "THUMB_TIP",
    5:  "INDEX_MCP",  6:  "INDEX_PIP",  7:  "INDEX_DIP",  8:  "INDEX_TIP",
    9:  "MID_MCP",   10:  "MID_PIP",   11:  "MID_DIP",   12:  "MID_TIP",
    13: "RING_MCP",  14: "RING_PIP",   15: "RING_DIP",   16: "RING_TIP",
    17: "PINKY_MCP", 18: "PINKY_PIP",  19: "PINKY_DIP",  20: "PINKY_TIP",
}

# IDs of the five fingertips — drawn in a special accent colour
FINGERTIP_IDS: frozenset[int] = frozenset({4, 8, 12, 16, 20})

# IDs of the four knuckle bases (MCP joints) — drawn in a mid colour
KNUCKLE_IDS: frozenset[int] = frozenset({1, 5, 9, 13, 17})


# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — COLOUR PALETTE
# ═══════════════════════════════════════════════════════════════════
#
# All OpenCV colours are (Blue, Green, Red) tuples — NOT (R, G, B).
#
# We define one colour per landmark "role" so it's easy to tweak
# the whole look by changing values here rather than hunting
# through drawing code.
# ───────────────────────────────────────────────────────────────────

# ── Landmark dot colours ────────────────────────────────────────────
CLR_WRIST       = (0,   200, 255)   # yellow-ish  — wrist (ID 0)
CLR_FINGERTIP   = (0,   80,  255)   # vivid red   — fingertips (4,8,12,16,20)
CLR_KNUCKLE     = (255, 180, 0  )   # cyan-blue   — MCP knuckles
CLR_JOINT       = (180, 255, 100)   # light green — all other joints

# ── Landmark ID text colours ────────────────────────────────────────
CLR_ID_WRIST    = (0,   220, 255)   # matches wrist dot
CLR_ID_FINGERTIP= (0,   100, 255)   # matches fingertip dot
CLR_ID_DEFAULT  = (255, 255, 255)   # white for everything else

# ── HUD / UI colours ───────────────────────────────────────────────
CLR_FPS         = (0,   230, 0  )   # green
CLR_WHITE       = (220, 220, 220)   # soft white
CLR_BLACK       = (0,   0,   0  )   # shadow
CLR_PANEL_BG    = (20,  20,  40 )   # dark navy HUD background
CLR_LEFT_BOX    = (255, 100, 0  )   # blue-ish  bounding box — left hand
CLR_RIGHT_BOX   = (0,   100, 255)   # orange    bounding box — right hand
CLR_CONNECTIONS = (180, 180, 180)   # light grey skeleton lines

FONT     = cv2.FONT_HERSHEY_SIMPLEX
LINE_AA  = cv2.LINE_AA

# Dot sizes
RADIUS_WRIST     = 8
RADIUS_FINGERTIP = 9
RADIUS_KNUCKLE   = 7
RADIUS_JOINT     = 6


# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — FPS COUNTER
# ═══════════════════════════════════════════════════════════════════
#
# Keeps the last 30 frame timestamps in a sliding window.
# FPS = (number of intervals) / (elapsed seconds).
# Using time.monotonic() guarantees the clock never goes backwards.
# ───────────────────────────────────────────────────────────────────

class FPSCounter:
    """Rolling-average FPS counter."""

    def __init__(self, window: int = 30) -> None:
        self._ts: deque[float] = deque(maxlen=window)

    def tick(self) -> float:
        self._ts.append(time.monotonic())
        if len(self._ts) < 2:
            return 0.0
        elapsed = self._ts[-1] - self._ts[0]
        return (len(self._ts) - 1) / elapsed if elapsed > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════
# SECTION 6 — LANDMARK DOT & ID DRAWING
# ═══════════════════════════════════════════════════════════════════
#
# This is the core new feature.  For each of the 21 landmarks we:
#
#   1. Convert the normalised (x, y) coords to pixel coords
#      by multiplying by the frame width and height.
#
#   2. Choose the dot colour and radius based on the landmark's role:
#        ID 0         → WRIST     colour
#        ID in 4,8… → FINGERTIP colour + larger radius
#        ID in 1,5… → KNUCKLE   colour
#        everything else → plain JOINT colour
#
#   3. Draw a filled circle at the pixel position.
#      cv2.circle(frame, center, radius, colour, thickness)
#      thickness=-1 means "filled".
#
#   4. Draw the ID number just above and to the right of the dot.
#      We offset by (+12, -10) so the number doesn't sit on the dot.
#      ID text uses the same accent colour as the dot.
# ───────────────────────────────────────────────────────────────────

def draw_landmarks_with_ids(
    frame,
    hand_landmarks,
    frame_w: int,
    frame_h: int,
) -> None:
    """
    Draws every landmark as a colour-coded dot with its ID beside it.

    Args:
        frame          : BGR image to draw on (in-place).
        hand_landmarks : MediaPipe NormalizedLandmarkList for one hand.
        frame_w        : Frame width in pixels.
        frame_h        : Frame height in pixels.
    """
    for idx, lm in enumerate(hand_landmarks.landmark):

        # ── Convert normalised → pixel coordinates ───────────────────
        #
        # lm.x and lm.y are floats between 0.0 and 1.0.
        # Multiplying by the frame size gives the pixel position.
        # int() truncates the float to a whole-number pixel index.
        # ─────────────────────────────────────────────────────────────
        cx = int(lm.x * frame_w)
        cy = int(lm.y * frame_h)

        # ── Pick colour and size based on joint role ─────────────────
        if idx == 0:
            dot_color  = CLR_WRIST
            txt_color  = CLR_ID_WRIST
            radius     = RADIUS_WRIST

        elif idx in FINGERTIP_IDS:
            dot_color  = CLR_FINGERTIP
            txt_color  = CLR_ID_FINGERTIP
            radius     = RADIUS_FINGERTIP

        elif idx in KNUCKLE_IDS:
            dot_color  = CLR_KNUCKLE
            txt_color  = CLR_ID_DEFAULT
            radius     = RADIUS_KNUCKLE

        else:
            dot_color  = CLR_JOINT
            txt_color  = CLR_ID_DEFAULT
            radius     = RADIUS_JOINT

        # ── Draw the landmark dot ─────────────────────────────────────
        #
        # First draw a slightly larger black ring for contrast,
        # then the coloured filled circle on top.
        # This gives the dots a clean outlined look.
        # ─────────────────────────────────────────────────────────────
        cv2.circle(frame, (cx, cy), radius + 2, CLR_BLACK, -1, LINE_AA)   # outline
        cv2.circle(frame, (cx, cy), radius,     dot_color, -1, LINE_AA)   # fill

        # ── Draw the landmark ID number ───────────────────────────────
        #
        # Offset the text (+12px right, -10px up) so it doesn't
        # overlap the dot.  We use a small font scale (0.38) so the
        # numbers stay compact even when many landmarks are close together.
        # Shadow behind the text keeps it readable on busy backgrounds.
        # ─────────────────────────────────────────────────────────────
        text_pos = (cx + 12, cy - 10)

        # Shadow pass
        cv2.putText(frame, str(idx), (text_pos[0] + 1, text_pos[1] + 1),
                    FONT, 0.38, CLR_BLACK, 2, LINE_AA)
        # Coloured text pass
        cv2.putText(frame, str(idx), text_pos,
                    FONT, 0.38, txt_color, 1, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 7 — SKELETON (CONNECTIONS) DRAWING
# ═══════════════════════════════════════════════════════════════════
#
# mp_hands.HAND_CONNECTIONS is a frozenset of (start_id, end_id) pairs
# that define the 21 bone connections in a hand skeleton.
#
# We draw each connection manually (rather than using mp_drawing) so
# we can set our own connection colour and line thickness.
#
# The drawing order matters: draw connections BEFORE dots so the dots
# sit on top of the lines and aren't obscured.
# ───────────────────────────────────────────────────────────────────

def draw_connections(frame, hand_landmarks, frame_w: int, frame_h: int) -> None:
    """
    Draws all 21 bone connections as grey lines between landmark dots.

    Args:
        frame          : BGR image to draw on (in-place).
        hand_landmarks : MediaPipe NormalizedLandmarkList for one hand.
        frame_w / frame_h : Frame dimensions in pixels.
    """
    for start_id, end_id in mp_hands.HAND_CONNECTIONS:
        start = hand_landmarks.landmark[start_id]
        end   = hand_landmarks.landmark[end_id]

        # Convert both endpoints from normalised to pixel coords
        x1, y1 = int(start.x * frame_w), int(start.y * frame_h)
        x2, y2 = int(end.x   * frame_w), int(end.y   * frame_h)

        cv2.line(frame, (x1, y1), (x2, y2), CLR_CONNECTIONS, 2, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 8 — BOUNDING BOX
# ═══════════════════════════════════════════════════════════════════

def get_bounding_box(
    hand_landmarks, frame_w: int, frame_h: int, padding: int = 24
) -> tuple[int, int, int, int]:
    """
    Returns (x, y, width, height) bounding box from landmark extents.

    Pads by `padding` pixels on all sides so fingertips aren't clipped.
    Clamps the box so it never goes outside the frame boundaries.
    """
    xs = [lm.x * frame_w for lm in hand_landmarks.landmark]
    ys = [lm.y * frame_h for lm in hand_landmarks.landmark]

    x1 = max(0,       int(min(xs)) - padding)
    y1 = max(0,       int(min(ys)) - padding)
    x2 = min(frame_w, int(max(xs)) + padding)
    y2 = min(frame_h, int(max(ys)) + padding)

    return (x1, y1, x2 - x1, y2 - y1)


def draw_bounding_box(frame, label: str, bbox: tuple) -> None:
    """
    Draws a rounded bounding box and a Left / Right label chip.

    Left hands use CLR_LEFT_BOX (blue), Right use CLR_RIGHT_BOX (orange).
    The label chip is a filled rectangle so the text has a clean background.
    """
    x, y, w, h = bbox
    color = CLR_LEFT_BOX if label == "Left" else CLR_RIGHT_BOX

    # Box outline
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2, LINE_AA)

    # Label chip: filled rect + white text
    chip_w, chip_h = 60, 22
    chip_y = max(y - chip_h, 0)
    cv2.rectangle(frame, (x, chip_y), (x + chip_w, chip_y + chip_h), color, -1)
    cv2.putText(frame, label, (x + 5, chip_y + 15),
                FONT, 0.55, CLR_BLACK, 2, LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 9 — HUD PANEL  (landmark stats + legend)
# ═══════════════════════════════════════════════════════════════════
#
# A semi-transparent dark panel drawn in the top-right corner
# shows a live readout of:
#   • FPS
#   • Total landmark points detected this frame
#   • Number of hands detected
#   • A three-dot colour legend for Fingertip / Joint / Wrist
#
# HOW the transparency works:
#   OpenCV doesn't support alpha blending natively for drawing.
#   The workaround is:
#     1. Copy the region we want to dim into a temporary overlay image.
#     2. Draw the filled rectangle onto the overlay.
#     3. Blend overlay back into the frame using cv2.addWeighted().
#
#   cv2.addWeighted(src1, α, src2, β, γ) computes:
#       output = src1 * α + src2 * β + γ
#   Setting α=0.6 makes our panel 60% opaque (40% of original shows through).
# ───────────────────────────────────────────────────────────────────

def draw_hud_panel(
    frame,
    fps: float,
    num_hands: int,
    total_landmarks: int,
) -> None:
    """
    Draws a stats HUD panel in the top-right corner of the frame.

    Args:
        frame           : BGR image (in-place).
        fps             : Current frames-per-second.
        num_hands       : How many hands were detected this frame.
        total_landmarks : Total landmark points detected (num_hands × 21).
    """
    frame_h, frame_w = frame.shape[:2]

    # Panel dimensions and position (top-right corner)
    panel_w, panel_h = 230, 160
    px = frame_w - panel_w - 12   # 12px from right edge
    py = 12                        # 12px from top edge

    # ── Semi-transparent background ──────────────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (px, py), (px + panel_w, py + panel_h),
                  CLR_PANEL_BG, -1, LINE_AA)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    # ── Panel border ─────────────────────────────────────────────────
    cv2.rectangle(frame, (px, py), (px + panel_w, py + panel_h),
                  (60, 60, 100), 1, LINE_AA)

    # ── Text rows ────────────────────────────────────────────────────
    #
    # We define a list of (label, value, colour) tuples and render
    # them in a loop with a fixed row spacing.  This keeps the layout
    # easy to extend — just append a new tuple to add a new row.
    # ─────────────────────────────────────────────────────────────────
    rows = [
        ("FPS",         f"{fps:.1f}",          CLR_FPS),
        ("Hands",       str(num_hands),         CLR_WHITE),
        ("Landmarks",   str(total_landmarks),   CLR_WHITE),
        ("Per hand",    "21",                   (150, 150, 150)),
    ]

    row_h  = 28   # vertical spacing between rows
    text_x = px + 12
    text_y = py + 28

    for label, value, color in rows:
        # Label in dim white
        cv2.putText(frame, f"{label}:", (text_x, text_y),
                    FONT, 0.48, (160, 160, 160), 1, LINE_AA)
        # Value in accent colour, right-aligned in the panel
        cv2.putText(frame, value, (text_x + 110, text_y),
                    FONT, 0.52, color, 1, LINE_AA)
        text_y += row_h

    # ── Colour legend ─────────────────────────────────────────────────
    #
    # Three small dots + labels to explain the colour coding.
    # ─────────────────────────────────────────────────────────────────
    legend = [
        (CLR_FINGERTIP, "Fingertip"),
        (CLR_WRIST,     "Wrist"),
        (CLR_JOINT,     "Joint"),
    ]
    legend_y = py + panel_h - 38
    legend_x = px + 12

    for dot_color, dot_label in legend:
        cv2.circle(frame, (legend_x + 6, legend_y + 1), 5, dot_color, -1, LINE_AA)
        cv2.putText(frame, dot_label, (legend_x + 16, legend_y + 5),
                    FONT, 0.38, CLR_WHITE, 1, LINE_AA)
        legend_x += 75   # space legend items horizontally


# ═══════════════════════════════════════════════════════════════════
# SECTION 10 — HELPER OVERLAYS  (FPS corner + instructions)
# ═══════════════════════════════════════════════════════════════════

def draw_text_shadowed(frame, text: str, pos: tuple,
                       scale: float, color: tuple, thickness: int) -> None:
    """Draws text with a 1-pixel black shadow for contrast on any background."""
    x, y = pos
    cv2.putText(frame, text, (x + 1, y + 1), FONT, scale, CLR_BLACK, thickness + 1, LINE_AA)
    cv2.putText(frame, text, pos,             FONT, scale, color,     thickness,     LINE_AA)


def draw_instructions(frame) -> None:
    """'Press Q to quit' hint pinned to the bottom-left corner."""
    h = frame.shape[0]
    draw_text_shadowed(frame, "Press Q to quit",
                       (16, h - 16), 0.55, CLR_WHITE, 1)


# ═══════════════════════════════════════════════════════════════════
# SECTION 11 — CAMERA SETUP
# ═══════════════════════════════════════════════════════════════════

def open_camera(index: int) -> cv2.VideoCapture:
    """Opens the webcam, requests 720p@30fps, logs the actual accepted settings."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera at index {index}. Try --camera 0, 1, or 2.")
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
# SECTION 12 — MAIN LOOP
# ═══════════════════════════════════════════════════════════════════
#
# Each frame goes through this pipeline:
#
#   read  →  flip  →  BGR→RGB  →  MediaPipe
#     ↓
#   for each hand:
#     draw_connections()           ← lines first (behind dots)
#     draw_landmarks_with_ids()    ← coloured dots + ID numbers on top
#     draw_bounding_box()          ← box + Left/Right chip
#     accumulate total_landmarks
#     ↓
#   draw_hud_panel()               ← stats in top-right corner
#   draw_instructions()            ← quit hint bottom-left
#     ↓
#   imshow  →  waitKey  →  Q? exit
# ───────────────────────────────────────────────────────────────────

def run(camera_index: int = 0, max_hands: int = 2, flip: bool = True) -> None:
    """
    Enhanced hand-tracking main loop.

    Args:
        camera_index : Which camera to open (0 = laptop built-in webcam).
        max_hands    : How many hands to track simultaneously (1 or 2).
        flip         : Mirror the frame horizontally (recommended for gestures).
    """
    cap         = open_camera(camera_index)
    fps_counter = FPSCounter(window=30)

    with mp_hands.Hands(
        static_image_mode        = False,
        max_num_hands            = max_hands,
        min_detection_confidence = 0.7,
        min_tracking_confidence  = 0.6,
    ) as hands_model:

        print("[INFO] Enhanced hand tracking started. Press Q to quit.")

        while True:

            # ── Read & pre-process frame ──────────────────────────────
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Camera read failed — exiting.")
                break

            if flip:
                frame = cv2.flip(frame, 1)   # mirror — feels like a selfie camera

            frame_h, frame_w = frame.shape[:2]

            # BGR → RGB because MediaPipe expects RGB input
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # ── Run MediaPipe inference ───────────────────────────────
            results = hands_model.process(rgb)

            # ── Draw per-hand visuals ─────────────────────────────────
            total_landmarks = 0   # accumulate across all detected hands

            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness,
                ):
                    # 1. Connections (lines) drawn BEFORE dots so dots sit on top
                    draw_connections(frame, hand_landmarks, frame_w, frame_h)

                    # 2. Landmark dots + ID numbers on top of the lines
                    draw_landmarks_with_ids(frame, hand_landmarks, frame_w, frame_h)

                    # 3. Bounding box + Left/Right label
                    label = handedness.classification[0].label
                    bbox  = get_bounding_box(hand_landmarks, frame_w, frame_h)
                    draw_bounding_box(frame, label, bbox)

                    # Each hand always has exactly 21 landmarks
                    total_landmarks += 21

            # ── HUD panel + instructions ──────────────────────────────
            num_hands = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
            fps       = fps_counter.tick()

            draw_hud_panel(frame, fps, num_hands, total_landmarks)
            draw_instructions(frame)

            # ── Display ───────────────────────────────────────────────
            cv2.imshow("GestureOS AI — Enhanced Hand Tracking", frame)

            # Q or q to quit; waitKey(1) keeps the loop near full speed
            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                print("[INFO] Q pressed — stopping.")
                break

    # ── Cleanup ───────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Done.")


# ═══════════════════════════════════════════════════════════════════
# SECTION 13 — CLI & ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GestureOS AI — Enhanced Hand Tracking (landmark IDs + colours)"
    )
    p.add_argument("--camera",    type=int, default=0,
                   help="Camera index (default 0 = laptop built-in webcam)")
    p.add_argument("--max-hands", type=int, default=2, choices=[1, 2],
                   help="Max hands to detect (default 2)")
    p.add_argument("--no-flip",   action="store_true",
                   help="Disable horizontal mirror")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        camera_index = args.camera,
        max_hands    = args.max_hands,
        flip         = not args.no_flip,
    )
