"""
GestureOS AI — Data Collection Script
Records hand landmark samples from webcam and saves them to a CSV for training.

Usage:
    python scripts/collect_data.py --gesture open_palm --samples 200
"""

import argparse
import csv
from pathlib import Path

import cv2
from loguru import logger

from modules.camera import CameraStream
from modules.hand_detector import HandDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect gesture landmark data.")
    parser.add_argument("--gesture", required=True, help="Gesture label to record")
    parser.add_argument("--samples", type=int, default=200, help="Number of samples")
    parser.add_argument("--output", default="data/processed/landmarks_dataset.csv")
    parser.add_argument("--camera", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = output_path.exists()
    camera = CameraStream(index=args.camera).start()
    detector = HandDetector(max_hands=1)

    collected = 0
    logger.info(f"Collecting {args.samples} samples for gesture: '{args.gesture}'")
    logger.info("Press SPACE to capture a frame, Q to quit.")

    with output_path.open("a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            header = [f"{axis}{i}" for i in range(21) for axis in ("x", "y", "z")] + ["label"]
            writer.writerow(header)

        while collected < args.samples:
            frame = camera.read()
            if frame is None:
                continue

            display = frame.copy()
            hands = detector.detect(display)
            for hand in hands:
                detector.draw(display, hands)

            cv2.putText(display, f"Gesture: {args.gesture} | Collected: {collected}/{args.samples}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Data Collection", display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord(" ") and hands:
                row = [v for lm in hands[0].landmarks for v in lm] + [args.gesture]
                writer.writerow(row)
                collected += 1
                logger.info(f"Captured sample {collected}/{args.samples}")

    camera.stop()
    cv2.destroyAllWindows()
    logger.info(f"Done. {collected} samples saved to {output_path}")


if __name__ == "__main__":
    main()
