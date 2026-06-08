import cv2
import math
import numpy as np

# Color Palette (BGR format)
C_BLUE    = (255, 130, 0)
C_CYAN    = (255, 220, 0)
C_GREEN   = (80, 210, 80)
C_RED     = (60, 60, 220)
C_WHITE   = (240, 240, 240)
C_BLACK   = (10, 10, 10)
C_GREY    = (120, 120, 120)
C_PURPLE  = (200, 100, 180)
C_AMBER   = (0, 190, 255)

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20)
]

def draw_shadow_text(frame, text: str, pos: tuple, scale: float, color: tuple, thickness: int = 1):
    x, y = pos
    cv2.putText(frame, text, (x + 1, y + 1), cv2.FONT_HERSHEY_SIMPLEX, scale, C_BLACK, thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

def draw_alpha_rect(frame, x1: int, y1: int, x2: int, y2: int, color: tuple, alpha: float = 0.5):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1, cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

def draw_corner_bracket(frame, x1: int, y1: int, x2: int, y2: int, color: tuple, arm: int = 15, thick: int = 2):
    # Top-Left
    cv2.line(frame, (x1, y1), (x1 + arm, y1), color, thick, cv2.LINE_AA)
    cv2.line(frame, (x1, y1), (x1, y1 + arm), color, thick, cv2.LINE_AA)
    # Top-Right
    cv2.line(frame, (x2, y1), (x2 - arm, y1), color, thick, cv2.LINE_AA)
    cv2.line(frame, (x2, y1), (x2, y1 + arm), color, thick, cv2.LINE_AA)
    # Bottom-Left
    cv2.line(frame, (x1, y2), (x1 + arm, y2), color, thick, cv2.LINE_AA)
    cv2.line(frame, (x1, y2), (x1, y2 - arm), color, thick, cv2.LINE_AA)
    # Bottom-Right
    cv2.line(frame, (x2, y2), (x2 - arm, y2), color, thick, cv2.LINE_AA)
    cv2.line(frame, (x2, y2), (x2, y2 - arm), color, thick, cv2.LINE_AA)

def detect_fingers_state(landmarks) -> dict[str, bool]:
    lm = landmarks
    def _d(a_idx, b_idx):
        return math.hypot(lm[a_idx][0] - lm[b_idx][0], lm[a_idx][1] - lm[b_idx][1])
    
    # Thumb: Distance wrist-tip compared to wrist-IP
    tip_dist = _d(4, 0)
    ip_dist = _d(3, 0)
    tip_to_ip = _d(4, 3)
    thumb_up = (tip_dist > ip_dist + 0.04) and (tip_to_ip > 0.04)
    
    # Other 4 fingers
    def is_up(tip, pip, mcp):
        y_check = lm[tip][1] < lm[pip][1] - 0.01
        dist_check = _d(tip, mcp) > _d(mcp, 0) * 0.55
        return y_check and dist_check

    return {
        "Thumb": thumb_up,
        "Index": is_up(8, 6, 5),
        "Middle": is_up(12, 10, 9),
        "Ring": is_up(16, 14, 13),
        "Pinky": is_up(20, 18, 17)
    }

# Click state color palette
C_CLICK_GREEN = (0, 255, 100)     # Bright green for click indicator
C_CLICK_LINE  = (80, 255, 120)    # Connection line during pinch

def draw_visuals(frame, detected_hands, mp_results, config, fps: float, gesture: str, confidence: float, click_state: dict | None = None) -> np.ndarray:
    """
    Renders selected overlays in-place on the frame based on config switches.

    Parameters:
        click_state: Optional dict from VirtualMouse.process_hand() containing
                     click_status, click_counter, pinch_distance, current_action.
    """
    h, w = frame.shape[:2]

    # Extract click state fields with safe defaults
    cs_status   = click_state.get("click_status", "OPEN") if click_state else "OPEN"
    cs_counter  = click_state.get("click_counter", 0) if click_state else 0
    cs_action   = click_state.get("current_action", "None") if click_state else "None"
    cs_pinch    = click_state.get("pinch_distance", 0.0) if click_state else 0.0
    vm_enabled  = getattr(config, "virtual_mouse_enabled", False)
    
    # Render skeletons (connections and landmarks)
    for hand in detected_hands:
        lm_px = []
        for lm in hand.landmarks:
            cx = int(lm[0] * w)
            cy = int(lm[1] * h)
            lm_px.append((cx, cy))
            
        # 4. Connections Rendering
        if getattr(config, "show_connections", True):
            for s_id, e_id in CONNECTIONS:
                if s_id < len(lm_px) and e_id < len(lm_px):
                    cv2.line(frame, lm_px[s_id], lm_px[e_id], C_GREY, 2, cv2.LINE_AA)
                    
        # 3. Landmarks Rendering
        if getattr(config, "show_landmarks", True):
            for cx, cy in lm_px:
                cv2.circle(frame, (cx, cy), 4, C_WHITE, -1, cv2.LINE_AA)
                cv2.circle(frame, (cx, cy), 4, C_BLACK, 1, cv2.LINE_AA)
                
        # 5. Bounding Box Around Hand
        if getattr(config, "show_bounding_box", True):
            x, y, bw, bh = hand.bbox
            color = C_BLUE if hand.handedness == "Left" else C_AMBER
            draw_corner_bracket(frame, x, y, x + bw, y + bh, color, arm=18, thick=2)
            cv2.rectangle(frame, (x, y), (x + bw, y + bh), color, 1, cv2.LINE_AA)
            draw_shadow_text(frame, hand.handedness, (x, max(y - 8, 15)), 0.45, color, 1)

        # 7. Distance Measurement: Thumb tip (4) ↔ Index tip (8)
        if getattr(config, "show_distance_meter", True):
            if len(lm_px) > 8:
                p4 = lm_px[4]
                p8 = lm_px[8]
                dist_px = math.hypot(p4[0] - p8[0], p4[1] - p8[1])

                # Use green line/dots when pinching, cyan otherwise
                is_pinching = vm_enabled and cs_status in ("PINCH", "LEFT_CLICK")
                line_color = C_CLICK_LINE if is_pinching else C_CYAN
                dot_color  = C_CLICK_GREEN if is_pinching else C_CYAN

                cv2.line(frame, p4, p8, line_color, 2 if is_pinching else 1, cv2.LINE_AA)
                cv2.circle(frame, p4, 6 if is_pinching else 5, dot_color, -1, cv2.LINE_AA)
                cv2.circle(frame, p8, 6 if is_pinching else 5, dot_color, -1, cv2.LINE_AA)
                mid_x = (p4[0] + p8[0]) // 2
                mid_y = (p4[1] + p8[1]) // 2
                draw_shadow_text(frame, f"{int(dist_px)}px", (mid_x + 5, mid_y - 5), 0.35, line_color, 1)

        # 6. Finger State Details (colour-coded fingertip rings)
        if getattr(config, "show_finger_states", True):
            f_states = detect_fingers_state(hand.landmarks)
            tips = [("Thumb", 4), ("Index", 8), ("Middle", 12), ("Ring", 16), ("Pinky", 20)]
            for name, tip_idx in tips:
                if tip_idx < len(lm_px):
                    is_up = f_states[name]
                    color = C_GREEN if is_up else C_RED
                    cx, cy = lm_px[tip_idx]
                    cv2.circle(frame, (cx, cy), 12, color, 2, cv2.LINE_AA)
                    cv2.circle(frame, (cx, cy), 5, color, -1, cv2.LINE_AA)
                    cv2.circle(frame, (cx, cy), 5, C_BLACK, 1, cv2.LINE_AA)

        # Draw a cursor-tracking indicator on the index fingertip (landmark 8)
        if vm_enabled and len(lm_px) > 8:
            if cs_status == "LEFT_CLICK":
                # Flash a bright filled green circle on click
                cv2.circle(frame, lm_px[8], 20, C_CLICK_GREEN, -1, cv2.LINE_AA)
                cv2.circle(frame, lm_px[8], 20, C_WHITE, 2, cv2.LINE_AA)
            elif cs_status == "PINCH":
                # Filled smaller green dot during pinch hold
                cv2.circle(frame, lm_px[8], 15, C_CLICK_GREEN, -1, cv2.LINE_AA)
                cv2.circle(frame, lm_px[8], 15, C_WHITE, 1, cv2.LINE_AA)
            else:
                # Normal cursor ring
                cv2.circle(frame, lm_px[8], 15, C_PURPLE, 2, cv2.LINE_AA)
                cv2.circle(frame, lm_px[8], 4, C_PURPLE, -1, cv2.LINE_AA)

    # ── Virtual Mouse Active Zone Overlay ─────────────────────────
    if getattr(config, "virtual_mouse_enabled", False):
        pad_pct = getattr(config, "virtual_mouse_dead_zone", 0.15)
        px_x1 = int(pad_pct * w)
        px_y1 = int(pad_pct * h)
        px_x2 = int((1.0 - pad_pct) * w)
        px_y2 = int((1.0 - pad_pct) * h)
        cv2.rectangle(frame, (px_x1, px_y1), (px_x2, px_y2), C_CYAN, 1, cv2.LINE_AA)
        draw_shadow_text(frame, "Mouse Active Area", (px_x1 + 6, px_y1 - 6), 0.35, C_CYAN, 1)

    # 8. HUD Panel Overlay
    if getattr(config, "show_hud", True):
        # Expand panel height when virtual mouse click info is available
        has_click_info = vm_enabled and click_state is not None
        panel_w = 240
        panel_h = 200 if has_click_info else 160
        draw_alpha_rect(frame, 15, 15, 15 + panel_w, 15 + panel_h, (30, 20, 20), 0.8)
        cv2.rectangle(frame, (15, 15), (15 + panel_w, 15 + panel_h), C_GREY, 1, cv2.LINE_AA)
        
        # System Info
        draw_shadow_text(frame, "SYSTEM HUD OVERLAY", (25, 35), 0.42, C_WHITE, 1)
        cv2.line(frame, (25, 42), (15 + panel_w - 10, 42), C_GREY, 1)
        
        # FPS & Hand Count
        draw_shadow_text(frame, f"FPS: {fps:.1f}", (25, 60), 0.4, C_CYAN, 1)
        draw_shadow_text(frame, f"Hands: {len(detected_hands)}", (135, 60), 0.4, C_CYAN, 1)
        
        # Gesture & Confidence
        gest_name = gesture.replace('_', ' ').title() if gesture not in ("unknown", "None", "No Model") else gesture
        draw_shadow_text(frame, f"Gesture: {gest_name}", (25, 80), 0.4, C_WHITE, 1)
        conf_pct = f"{(confidence * 100):.0f}%" if confidence > 0 and gesture not in ("unknown", "None", "No Model") else "0%"
        draw_shadow_text(frame, f"Confidence: {conf_pct}", (25, 100), 0.4, C_WHITE, 1)
        
        # Finger States
        if getattr(config, "show_finger_states", True):
            if detected_hands:
                f_states = detect_fingers_state(detected_hands[0].landmarks)
                f_str = " ".join([f"{k[0]}:{'U' if v else 'D'}" for k, v in f_states.items()])
                draw_shadow_text(frame, f"Fingers: {f_str}", (25, 125), 0.35, C_GREEN, 1)
                raised = sum(f_states.values())
                draw_shadow_text(frame, f"Raised Fingers: {raised}/5", (25, 145), 0.35, C_GREEN, 1)
            else:
                draw_shadow_text(frame, "Fingers: No Hands Tracked", (25, 125), 0.35, C_RED, 1)
        else:
            draw_shadow_text(frame, "Fingers: Disabled", (25, 125), 0.35, C_GREY, 1)

        # Click telemetry (only when virtual mouse is active)
        if has_click_info:
            y_click = 165
            cv2.line(frame, (25, y_click - 5), (15 + panel_w - 10, y_click - 5), C_GREY, 1)
            status_color = C_CLICK_GREEN if cs_status in ("LEFT_CLICK", "PINCH") else C_CYAN
            draw_shadow_text(frame, f"Click: {cs_status}", (25, y_click + 10), 0.35, status_color, 1)
            draw_shadow_text(frame, f"Clicks: {cs_counter}", (145, y_click + 10), 0.35, C_CYAN, 1)
            draw_shadow_text(frame, f"Pinch: {cs_pinch:.4f}", (25, y_click + 28), 0.35, C_WHITE, 1)

    # 9. Gesture Debugger Overlay
    if getattr(config, "show_debug_panel", True):
        # Draw transparent background in top right
        panel_w, panel_h = 240, 140
        rx1 = w - 15 - panel_w
        rx2 = w - 15
        draw_alpha_rect(frame, rx1, 15, rx2, 15 + panel_h, (20, 20, 30), 0.8)
        cv2.rectangle(frame, (rx1, 15), (rx2, 15 + panel_h), C_GREY, 1, cv2.LINE_AA)
        
        # Header
        draw_shadow_text(frame, "PIPELINE DEBUGGER", (rx1 + 10, 35), 0.42, C_WHITE, 1)
        cv2.line(frame, (rx1 + 10, 42), (rx2 - 10, 42), C_GREY, 1)
        
        # Landmark count & settings
        lm_count = 21 * len(detected_hands)
        draw_shadow_text(frame, f"Landmarks Tracked: {lm_count}", (rx1 + 10, 60), 0.38, C_CYAN, 1)
        
        # MediaPipe confidence thresholds
        draw_shadow_text(frame, "Det. Conf: 0.50", (rx1 + 10, 80), 0.38, C_WHITE, 1)
        draw_shadow_text(frame, "Track. Conf: 0.50", (rx1 + 10, 100), 0.38, C_WHITE, 1)
        
        # Prediction status
        pred_val = gesture if gesture != "None" else "idle"
        draw_shadow_text(frame, f"Raw Pred: {pred_val}", (rx1 + 10, 125), 0.38, C_AMBER, 1)

    return frame
