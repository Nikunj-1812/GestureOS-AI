"""
GestureOS AI — Hand Tracking
==============================
Detects hands in real-time using MediaPipe and draws landmarks + connections
over a live webcam feed using OpenCV.

Features:
  - Detects up to 2 hands simultaneously
  - Draws all 21 landmarks per hand
  - Draws all bone connections between landmarks
  - Labels each hand as Left or Right
  - Shows a bounding box around each hand
  - Rolling-average FPS counter
  - Press Q to quit cleanly

Usage:
  python hand_tracking.py
  python hand_tracking.py --camera 1     # external/USB camera
  python hand_tracking.py --max-hands 1  # detect only one hand
  python hand_tracking.py --no-flip      # disable mirror mode
"""

# ═══════════════════════════════════════════════════════════════
# SECTION 1 — IMPORTS
# ═══════════════════════════════════════════════════════════════
#
# We need three libraries:
#   cv2        → OpenCV  : opens the webcam, reads frames, draws on screen
#   mediapipe  → Google's AI library for detecting hands and landmarks
#   time       → built-in Python module for measuring elapsed time (FPS)
#   collections→ built-in, gives us 'deque' (a fast rolling list for FPS)
#   argparse   → built-in, lets us pass options on the command line
#   sys        → built-in, lets us exit the program cleanly on errors
# ───────────────────────────────────────────────────────────────

import argparse
import sys
import time
from collections import deque

import cv2
import mediapipe as mp


# ═══════════════════════════════════════════════════════════════
# SECTION 2 — MEDIAPIPE SETUP
# ═══════════════════════════════════════════════════════════════
#
# MediaPipe organises its features into "solutions".
# We use two things from the hands solution:
#
#   mp_hands.Hands        → the AI model that detects hand landmarks
#   mp_drawing            → ready-made helper that draws those landmarks
#   mp_drawing_styles     → pre-built colour styles for landmarks/connections
#
# Think of mp_hands as the "brain" and mp_drawing as the "pen".
# ───────────────────────────────────────────────────────────────

mp_hands         = mp.solutions.hands
mp_drawing       = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


# ═══════════════════════════════════════════════════════════════
# SECTION 3 — CONSTANTS  (colours & fonts used throughout)
# ═══════════════════════════════════════════════════════════════
#
# OpenCV uses BGR colour order (Blue, Green, Red) — NOT the usual RGB.
# So  (0, 255, 0) is green,  (0, 0, 255) is red,  (255, 0, 0) is blue.
# ───────────────────────────────────────────────────────────────

COLOR_GREEN  = (0, 230, 0)      # FPS text
COLOR_WHITE  = (220, 220, 220)  # instruction text
COLOR_BLACK  = (0, 0, 0)        # shadow behind text
COLOR_LEFT   = (255, 100, 0)    # bounding box — left hand  (blue-ish)
COLOR_RIGHT  = (0, 100, 255)    # bounding box — right hand (orange-ish)

FONT       = cv2.FONT_HERSHEY_SIMPLEX
LINE_AA    = cv2.LINE_AA        # anti-aliased lines look smoother


# ═══════════════════════════════════════════════════════════════
# SECTION 4 — FPS COUNTER CLASS
# ═══════════════════════════════════════════════════════════════
#
# Problem: measuring FPS on a single frame is noisy and jumps around.
# Solution: keep a rolling list of the last 30 frame timestamps.
#   FPS = (number of gaps) / (time between oldest and newest timestamp)
#
# deque(maxlen=30) automatically drops the oldest entry when full —
# so we never need to manually trim the list.
# ───────────────────────────────────────────────────────────────

class FPSCounter:
    """Smooth rolling-average FPS counter."""

    def __init__(self, window: int = 30) -> None:
        # deque with a fixed max length — acts like a sliding window
        self._timestamps: deque[float] = deque(maxlen=window)

    def tick(self) -> float:
        """
        Call once per frame.
        Records the current time and returns the smoothed FPS.
        """
        self._timestamps.append(time.monotonic())  # monotonic = never goes backward

        if len(self._timestamps) < 2:
            return 0.0  # not enough data yet

        elapsed = self._timestamps[-1] - self._timestamps[0]
        if elapsed == 0:
            return 0.0

        return (len(self._timestamps) - 1) / elapsed


# ═══════════════════════════════════════════════════════════════
# SECTION 5 — DRAWING HELPERS
# ═══════════════════════════════════════════════════════════════
#
# These functions keep the main loop clean by isolating all the
# "how to draw X on screen" logic in one place.
#
# The "shadow trick": drawing text twice — first a dark copy
# shifted 1 pixel, then the bright copy on top — makes text
# readable on any background colour without needing a rectangle.
# ───────────────────────────────────────────────────────────────

def draw_text_with_shadow(frame, text: str, pos: tuple,
                          scale: float, color: tuple, thickness: int) -> None:
    """
    Draws text with a 1px dark shadow for readability on any background.

    Args:
        frame    : OpenCV image to draw on (modified in-place).
        text     : The string to render.
        pos      : (x, y) pixel position of the text baseline.
        scale    : Font size multiplier.
        color    : BGR text colour.
        thickness: Stroke thickness in pixels.
    """
    x, y = pos
    # Step 1 — draw black shadow at (x+1, y+1)
    cv2.putText(frame, text, (x + 1, y + 1),
                FONT, scale, COLOR_BLACK, thickness + 1, LINE_AA)
    # Step 2 — draw coloured text on top at (x, y)
    cv2.putText(frame, text, pos,
                FONT, scale, color, thickness, LINE_AA)


def draw_fps(frame, fps: float) -> None:
    """
    Draws the FPS counter in the top-left corner.

    Args:
        frame: OpenCV image (modified in-place).
        fps  : Current frames-per-second value.
    """
    draw_text_with_shadow(frame, f"FPS: {fps:.1f}",
                          pos=(16, 38), scale=0.8,
                          color=COLOR_GREEN, thickness=2)


def draw_instructions(frame) -> None:
    """
    Draws 'Press Q to quit' hint at the bottom of the frame.

    frame.shape returns (height, width, channels).
    We use height to pin the text to the bottom edge.
    """
    h = frame.shape[0]
    draw_text_with_shadow(frame, "Press Q to quit",
                          pos=(16, h - 16), scale=0.55,
                          color=COLOR_WHITE, thickness=1)


def draw_hand_info(frame, label: str, bbox: tuple) -> None:
    """
    Draws a bounding box and Left/Right label around a detected hand.

    Args:
        frame : OpenCV image (modified in-place).
        label : "Left" or "Right" — which hand MediaPipe detected.
        bbox  : (x, y, width, height) bounding box in pixels.
    """
    x, y, w, h = bbox

    # Choose colour based on which hand it is
    color = COLOR_LEFT if label == "Left" else COLOR_RIGHT

    # Draw the rectangle outline around the hand
    # (x, y) is top-left corner; (x+w, y+h) is bottom-right corner
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

    # Draw the label just above the box
    # We clamp y - 10 so the text doesn't go above the frame edge
    label_y = max(y - 10, 20)
    draw_text_with_shadow(frame, label,
                          pos=(x, label_y), scale=0.7,
                          color=color, thickness=2)


# ═══════════════════════════════════════════════════════════════
# SECTION 6 — CAMERA SETUP
# ═══════════════════════════════════════════════════════════════
#
# cv2.VideoCapture(index) opens a camera by index number.
#   index=0 → built-in laptop webcam
#   index=1 → first external/USB camera
#
# After opening, we set the resolution and FPS we'd like.
# The camera will use the closest values it actually supports.
# We then read back the real values to confirm.
# ───────────────────────────────────────────────────────────────

def open_camera(index: int) -> cv2.VideoCapture:
    """
    Opens the webcam at the given index and configures it.

    Returns:
        cv2.VideoCapture object, ready to read frames from.

    Raises:
        SystemExit if the camera cannot be opened.
    """
    cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera at index {index}.")
        print("        Try --camera 0, 1, or 2.")
        sys.exit(1)

    # Request 720p @ 30fps — camera uses nearest supported values
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS,          30)

    # Log what the camera actually accepted
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"[INFO] Camera {index} ready: {w}x{h} @ {fps:.0f}fps")

    return cap


# ═══════════════════════════════════════════════════════════════
# SECTION 7 — BOUNDING BOX HELPER
# ═══════════════════════════════════════════════════════════════
#
# MediaPipe gives us landmarks as normalised floats (0.0 → 1.0).
# To draw a box around the hand, we find the min/max x and y of
# all 21 landmarks, convert to pixel coordinates, then add a
# small padding so the box doesn't clip the fingertips.
# ───────────────────────────────────────────────────────────────

def get_bounding_box(hand_landmarks, frame_width: int, frame_height: int,
                     padding: int = 20) -> tuple[int, int, int, int]:
    """
    Calculates a padded bounding box from MediaPipe hand landmarks.

    MediaPipe landmark coordinates are normalised (0.0–1.0 relative to
    the frame size), so we multiply by width/height to get pixel coords.

    Args:
        hand_landmarks : MediaPipe NormalizedLandmarkList for one hand.
        frame_width    : Width of the frame in pixels.
        frame_height   : Height of the frame in pixels.
        padding        : Extra pixels to add around the tight box.

    Returns:
        (x, y, width, height) bounding box in pixels.
    """
    # Extract all x pixel coords across the 21 landmarks
    xs = [lm.x * frame_width  for lm in hand_landmarks.landmark]
    ys = [lm.y * frame_height for lm in hand_landmarks.landmark]

    x1 = max(0,            int(min(xs)) - padding)
    y1 = max(0,            int(min(ys)) - padding)
    x2 = min(frame_width,  int(max(xs)) + padding)
    y2 = min(frame_height, int(max(ys)) + padding)

    return (x1, y1, x2 - x1, y2 - y1)   # (x, y, w, h)


# ═══════════════════════════════════════════════════════════════
# SECTION 8 — MAIN HAND-TRACKING LOOP
# ═══════════════════════════════════════════════════════════════
#
# This is the heart of the program. Each iteration:
#
#   1. Read a raw BGR frame from the webcam
#   2. Flip it horizontally (mirror effect — feels natural)
#   3. Convert BGR → RGB  (MediaPipe requires RGB input)
#   4. Run MediaPipe hand detection
#   5. If hands found: draw landmarks, connections, box, label
#   6. Draw FPS and instructions
#   7. Show the finished frame
#   8. Check if Q was pressed → break and clean up
#
# Why BGR → RGB?
#   OpenCV reads cameras in BGR order (legacy from early cameras).
#   MediaPipe was designed for the more common RGB order.
#   We must convert before passing to MediaPipe, then work on
#   the original BGR frame for drawing (OpenCV expects BGR).
# ───────────────────────────────────────────────────────────────

def run_hand_tracking(camera_index: int = 0,
                      max_hands: int = 2,
                      flip: bool = True) -> None:
    """
    Main hand-tracking loop.

    Args:
        camera_index (int): Camera to open (0 = built-in webcam).
        max_hands    (int): Maximum number of hands to detect (1 or 2).
        flip         (bool): Mirror the frame left-right.
    """

    # ── Open camera ──────────────────────────────────────────────────
    cap = open_camera(camera_index)
    fps_counter = FPSCounter(window=30)

    # ── Initialise MediaPipe Hands ───────────────────────────────────
    #
    # Parameters explained:
    #   static_image_mode=False   → video mode: tracks hands between frames
    #                               (faster than re-detecting every frame)
    #   max_num_hands             → how many hands to track at once
    #   min_detection_confidence  → how confident the AI must be to detect a hand
    #                               (0.0–1.0; higher = fewer false positives)
    #   min_tracking_confidence   → confidence needed to keep tracking a hand
    #                               (lower than detection to avoid flickering)
    # ─────────────────────────────────────────────────────────────────
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=max_hands,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    ) as hands_model:

        print("[INFO] Hand tracking started. Press Q in the window to quit.")

        while True:

            # ── Step 1: Read frame ────────────────────────────────────
            #
            # cap.read() returns two values:
            #   ret   → True if a frame was successfully read
            #   frame → the image as a NumPy array of shape (H, W, 3)
            # If ret is False, the camera disconnected or the stream ended.
            # ──────────────────────────────────────────────────────────
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Failed to read frame — camera may be disconnected.")
                break

            # ── Step 2: Mirror the frame ──────────────────────────────
            #
            # cv2.flip(frame, 1) flips left-right (flipCode=1).
            # This makes the feed look like a mirror, which is more
            # intuitive when you're testing hand gestures.
            # ──────────────────────────────────────────────────────────
            if flip:
                frame = cv2.flip(frame, 1)

            # Grab frame dimensions for coordinate conversions later
            frame_h, frame_w = frame.shape[:2]

            # ── Step 3: BGR → RGB conversion ──────────────────────────
            #
            # MediaPipe expects RGB images. OpenCV gives us BGR.
            # We create a separate rgb_frame for inference but draw
            # on the original 'frame' (BGR) so OpenCV renders correctly.
            # ──────────────────────────────────────────────────────────
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # ── Step 4: Run MediaPipe hand detection ──────────────────
            #
            # hands_model.process() returns a Results object with:
            #   results.multi_hand_landmarks   → list of 21 landmarks per hand
            #                                    (None if no hands detected)
            #   results.multi_handedness       → list of Left/Right labels
            #
            # Each landmark has:
            #   .x  → normalised x position (0.0 = left edge, 1.0 = right edge)
            #   .y  → normalised y position (0.0 = top,       1.0 = bottom)
            #   .z  → approximate depth relative to the wrist
            # ──────────────────────────────────────────────────────────
            results = hands_model.process(rgb_frame)

            # ── Step 5: Draw landmarks & connections ──────────────────
            #
            # results.multi_hand_landmarks is None when no hands are found.
            # We use 'zip' to pair each hand's landmarks with its Left/Right label.
            # ──────────────────────────────────────────────────────────
            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness,
                ):
                    # ── Draw landmarks + connections ──────────────────
                    #
                    # mp_drawing.draw_landmarks() does two things at once:
                    #   1. Draws a filled circle at each of the 21 landmark points
                    #   2. Draws lines (connections) between landmarks
                    #      following the HAND_CONNECTIONS skeleton definition
                    #
                    # We pass drawing_specs to customise the visual style:
                    #   get_default_hand_landmarks_style() → coloured dots per finger
                    #   get_default_hand_connections_style() → coloured bone lines
                    # ──────────────────────────────────────────────────
                    mp_drawing.draw_landmarks(
                        image               = frame,
                        landmark_list       = hand_landmarks,
                        connections         = mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec = mp_drawing_styles
                                               .get_default_hand_landmarks_style(),
                        connection_drawing_spec = mp_drawing_styles
                                               .get_default_hand_connections_style(),
                    )

                    # ── Bounding box & label ──────────────────────────
                    #
                    # handedness.classification[0].label is "Left" or "Right".
                    # Note: because we mirrored the frame, MediaPipe's left/right
                    # matches what the user sees on screen.
                    # ──────────────────────────────────────────────────
                    label = handedness.classification[0].label
                    bbox  = get_bounding_box(hand_landmarks, frame_w, frame_h)
                    draw_hand_info(frame, label, bbox)

            # ── Step 6: Draw HUD overlays ─────────────────────────────
            fps = fps_counter.tick()
            draw_fps(frame, fps)
            draw_instructions(frame)

            # ── Step 7: Display the frame ─────────────────────────────
            #
            # cv2.imshow(window_name, image) opens a named window and
            # renders the frame. The window is created on first call and
            # reused on subsequent calls with the same name.
            # ──────────────────────────────────────────────────────────
            cv2.imshow("GestureOS AI — Hand Tracking", frame)

            # ── Step 8: Key detection ─────────────────────────────────
            #
            # cv2.waitKey(1) → wait 1 millisecond for a key press.
            #   Returning immediately keeps the loop fast (~30–60 FPS).
            #   waitKey(0) would pause until a key is pressed (not useful here).
            #
            # & 0xFF → bitwise AND with 0xFF (binary: 11111111).
            #   This masks out the upper bits which some platforms set
            #   for modifier keys like Num Lock, so 'q' always == 113.
            # ──────────────────────────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q"):
                print("[INFO] Q pressed — exiting.")
                break

    # ── Cleanup ───────────────────────────────────────────────────────
    #
    # Always release the camera hardware and destroy all OpenCV windows.
    # If we skip this, the camera light might stay on and the process
    # could hold the device lock, blocking other apps.
    # ──────────────────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Camera released. All windows closed. Goodbye.")


# ═══════════════════════════════════════════════════════════════
# SECTION 9 — CLI ARGUMENT PARSING & ENTRY POINT
# ═══════════════════════════════════════════════════════════════
#
# argparse lets us run the script with optional flags:
#   python hand_tracking.py --camera 1 --max-hands 1
#
# The  if __name__ == "__main__":  guard ensures this block only
# runs when we execute the file directly (not when it's imported
# as a module by another script).
# ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GestureOS AI — Real-time hand tracking with MediaPipe + OpenCV."
    )
    parser.add_argument(
        "--camera", type=int, default=0,
        help="Camera index (default: 0 = laptop built-in webcam)"
    )
    parser.add_argument(
        "--max-hands", type=int, default=2, choices=[1, 2],
        help="Maximum number of hands to detect (default: 2)"
    )
    parser.add_argument(
        "--no-flip", action="store_true",
        help="Disable horizontal mirror flip"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_hand_tracking(
        camera_index = args.camera,
        max_hands    = args.max_hands,
        flip         = not args.no_flip,
    )
