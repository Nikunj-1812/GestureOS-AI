"""
GestureOS AI — Environment & Function Checker
Verifies every installed package and tests each project script for import errors.
"""

import sys
import importlib

PASS = "  [PASS]"
FAIL = "  [FAIL]"
SEP  = "-" * 55

def check(label, fn):
    try:
        result = fn()
        print(f"{PASS}  {label}{':  ' + str(result) if result else ''}")
        return True
    except Exception as e:
        print(f"{FAIL}  {label}  →  {e}")
        return False

print(SEP)
print("  GestureOS AI — Environment Check")
print(SEP)
print(f"  Python: {sys.version.split()[0]}")
print()

# ── Core packages ─────────────────────────────────────────────────
print("PACKAGES")
print(SEP)

checks = [
    ("OpenCV",        lambda: __import__("cv2").__version__),
    ("MediaPipe",     lambda: __import__("mediapipe").__version__),
    ("NumPy",         lambda: __import__("numpy").__version__),
    ("PyTorch",       lambda: __import__("torch").__version__),
    ("TorchVision",   lambda: __import__("torchvision").__version__),
    ("ONNXRuntime",   lambda: __import__("onnxruntime").__version__),
    ("Pandas",        lambda: __import__("pandas").__version__),
    ("Scikit-learn",  lambda: __import__("sklearn").__version__),
    ("SciPy",         lambda: __import__("scipy").__version__),
    ("Matplotlib",    lambda: __import__("matplotlib").__version__),
    ("Seaborn",       lambda: __import__("seaborn").__version__),
    ("PyQt6",         lambda: __import__("PyQt6.QtCore", fromlist=["PYQT_VERSION_STR"]).PYQT_VERSION_STR),
    ("Pyqtgraph",     lambda: __import__("pyqtgraph").__version__),
    ("PyAutoGUI",     lambda: __import__("pyautogui").__version__),
    ("Pynput",        lambda: str(__import__("pynput"))),
    ("Keyboard",      lambda: str(__import__("keyboard")) and "installed"),
    ("PyYAML",        lambda: __import__("yaml").__version__),
    ("python-dotenv", lambda: str(__import__("dotenv")) and "installed"),
    ("Loguru",        lambda: __import__("loguru").__version__),
    ("Rich",          lambda: str(__import__("rich")) and "installed"),
    ("TQDM",          lambda: __import__("tqdm").__version__),
    ("Pillow",        lambda: __import__("PIL").__version__),
    ("Pytest",        lambda: __import__("pytest").__version__),
]

passed = sum(check(label, fn) for label, fn in checks)
print(f"\n  {passed}/{len(checks)} packages OK\n")

# ── Project scripts ────────────────────────────────────────────────
print("PROJECT SCRIPTS (import check)")
print(SEP)

scripts = [
    "webcam_preview",
    "hand_tracking",
    "hand_tracking_enhanced",
    "finger_state_detector",
    "hand_bounding_box",
    "gesture_hud",
    "distance_meter",
    "gesture_debugger",
]

script_passed = 0
for name in scripts:
    try:
        spec = importlib.util.spec_from_file_location(
            name, f"{name}.py"
        )
        mod = importlib.util.module_from_spec(spec)
        # Don't exec — just check syntax by compiling
        with open(f"{name}.py", "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, f"{name}.py", "exec")
        print(f"{PASS}  {name}.py")
        script_passed += 1
    except Exception as e:
        print(f"{FAIL}  {name}.py  →  {e}")

print(f"\n  {script_passed}/{len(scripts)} scripts OK\n")

# ── Camera check ───────────────────────────────────────────────────
print("CAMERA")
print(SEP)
try:
    import cv2
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        if ret:
            print(f"{PASS}  Camera 0 opened — {w}x{h} frame captured")
        else:
            print(f"  [WARN]  Camera 0 opened but no frame returned")
    else:
        print(f"  [WARN]  Camera 0 not available (no webcam connected?)")
except Exception as e:
    print(f"{FAIL}  Camera check  →  {e}")

# ── MediaPipe hand detection smoke test ───────────────────────────
print()
print("MEDIAPIPE HAND DETECTION")
print(SEP)
try:
    import cv2, mediapipe as mp, numpy as np
    mp_hands = mp.solutions.hands
    with mp_hands.Hands(static_image_mode=True, max_num_hands=1) as hands:
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        rgb   = cv2.cvtColor(blank, cv2.COLOR_BGR2RGB)
        res   = hands.process(rgb)
    print(f"{PASS}  MediaPipe Hands model loaded and ran inference")
except Exception as e:
    print(f"{FAIL}  MediaPipe smoke test  →  {e}")

# ── Summary ────────────────────────────────────────────────────────
print()
print(SEP)
print("  Environment check complete.")
print(f"  Run any script with:  .venv\\Scripts\\python.exe <script>.py")
print(SEP)
