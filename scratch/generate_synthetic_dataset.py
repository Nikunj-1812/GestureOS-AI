import csv
import random
import numpy as np
from pathlib import Path

def generate_landmarks(gesture: str) -> list[float]:
    # Base landmarks for 21 points (x, y, z)
    # Wrist is (0.5, 0.8)
    lm = [(0.5, 0.8, 0.0) for _ in range(21)]
    
    # Define finger bases (MCP joints)
    # 0: wrist
    # 1-4: thumb
    # 5-8: index
    # 9-12: middle
    # 13-16: ring
    # 17-20: pinky
    
    # Default MCPs
    lm[5] = (0.4, 0.6, 0.0)
    lm[9] = (0.48, 0.58, 0.0)
    lm[13] = (0.55, 0.6, 0.0)
    lm[17] = (0.62, 0.62, 0.0)
    
    # Thumb base
    lm[1] = (0.43, 0.75, 0.0)
    lm[2] = (0.37, 0.72, 0.0)
    
    if gesture == "open_palm":
        # Thumb extended
        lm[3] = (0.3, 0.68, 0.0)
        lm[4] = (0.24, 0.65, 0.0)
        # All other fingers extended up (tip y < pip y < mcp y)
        # Index
        lm[6] = (0.38, 0.5, 0.0)
        lm[7] = (0.36, 0.42, 0.0)
        lm[8] = (0.34, 0.34, 0.0)
        # Middle
        lm[10] = (0.48, 0.48, 0.0)
        lm[11] = (0.48, 0.4, 0.0)
        lm[12] = (0.48, 0.32, 0.0)
        # Ring
        lm[14] = (0.56, 0.5, 0.0)
        lm[15] = (0.57, 0.42, 0.0)
        lm[16] = (0.58, 0.34, 0.0)
        # Pinky
        lm[18] = (0.64, 0.54, 0.0)
        lm[19] = (0.65, 0.48, 0.0)
        lm[20] = (0.66, 0.42, 0.0)
        
    elif gesture == "fist":
        # Thumb folded
        lm[3] = (0.42, 0.68, 0.0)
        lm[4] = (0.46, 0.65, 0.0)
        # All other fingers curled down (tip y > mcp y)
        # Index
        lm[6] = (0.39, 0.65, 0.0)
        lm[7] = (0.41, 0.7, 0.0)
        lm[8] = (0.43, 0.75, 0.0)
        # Middle
        lm[10] = (0.48, 0.63, 0.0)
        lm[11] = (0.48, 0.68, 0.0)
        lm[12] = (0.48, 0.73, 0.0)
        # Ring
        lm[14] = (0.56, 0.65, 0.0)
        lm[15] = (0.55, 0.7, 0.0)
        lm[16] = (0.54, 0.75, 0.0)
        # Pinky
        lm[18] = (0.63, 0.67, 0.0)
        lm[19] = (0.62, 0.71, 0.0)
        lm[20] = (0.61, 0.75, 0.0)
        
    elif gesture == "victory":
        # Thumb folded
        lm[3] = (0.42, 0.68, 0.0)
        lm[4] = (0.46, 0.65, 0.0)
        # Index extended
        lm[6] = (0.38, 0.5, 0.0)
        lm[7] = (0.36, 0.42, 0.0)
        lm[8] = (0.34, 0.34, 0.0)
        # Middle extended
        lm[10] = (0.48, 0.48, 0.0)
        lm[11] = (0.48, 0.4, 0.0)
        lm[12] = (0.48, 0.32, 0.0)
        # Ring curled
        lm[14] = (0.56, 0.65, 0.0)
        lm[15] = (0.55, 0.7, 0.0)
        lm[16] = (0.54, 0.75, 0.0)
        # Pinky curled
        lm[18] = (0.63, 0.67, 0.0)
        lm[19] = (0.62, 0.71, 0.0)
        lm[20] = (0.61, 0.75, 0.0)
        
    elif gesture == "thumbs_up":
        # Thumb extended outwards
        lm[3] = (0.32, 0.6, 0.0)
        lm[4] = (0.25, 0.52, 0.0)
        # All other fingers curled down
        # Index
        lm[6] = (0.39, 0.65, 0.0)
        lm[7] = (0.41, 0.7, 0.0)
        lm[8] = (0.43, 0.75, 0.0)
        # Middle
        lm[10] = (0.48, 0.63, 0.0)
        lm[11] = (0.48, 0.68, 0.0)
        lm[12] = (0.48, 0.73, 0.0)
        # Ring
        lm[14] = (0.56, 0.65, 0.0)
        lm[15] = (0.55, 0.7, 0.0)
        lm[16] = (0.54, 0.75, 0.0)
        # Pinky
        lm[18] = (0.63, 0.67, 0.0)
        lm[19] = (0.62, 0.71, 0.0)
        lm[20] = (0.61, 0.75, 0.0)

    # Add Gaussian noise
    features = []
    for x, y, z in lm:
        nx = x + random.normalvariate(0.0, 0.015)
        ny = y + random.normalvariate(0.0, 0.015)
        nz = z + random.normalvariate(0.0, 0.015)
        features.extend([nx, ny, nz])
        
    return features

def main():
    dest_file = Path("data/processed/landmarks_dataset.csv")
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    
    gestures = ["open_palm", "fist", "victory", "thumbs_up"]
    samples_per_gesture = 300
    
    header = [f"{axis}{i}" for i in range(21) for axis in ("x", "y", "z")] + ["label"]
    
    with open(dest_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for g in gestures:
            for _ in range(samples_per_gesture):
                row = generate_landmarks(g) + [g]
                writer.writerow(row)
                
    print(f"Generated {len(gestures) * samples_per_gesture} samples in {dest_file}")

if __name__ == "__main__":
    main()
