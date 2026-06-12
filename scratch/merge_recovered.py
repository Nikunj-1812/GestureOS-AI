import glob
import os
import re

def run():
    files = glob.glob("scratch/recovered/step_*.txt")
    print(f"Found {len(files)} files to merge.")
    
    line_map = {}
    total_lines_recorded = 0
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        
        # We parse the file to find lines matching "<line_number>: <content>"
        # Note: the view_file tool formats them as "123: content"
        for line in lines:
            m = re.match(r"^(\d+):\s?(.*)$", line)
            if m:
                line_num = int(m.group(1))
                content = m.group(2)
                line_map[line_num] = content
                total_lines_recorded = max(total_lines_recorded, line_num)
                
    print(f"Max line number found: {total_lines_recorded}")
    print(f"Total unique lines successfully recovered: {len(line_map)}")
    
    # Check for gaps
    gaps = []
    in_gap = False
    gap_start = 0
    for idx in range(1, total_lines_recorded + 1):
        if idx not in line_map:
            if not in_gap:
                in_gap = True
                gap_start = idx
        else:
            if in_gap:
                in_gap = False
                gaps.append((gap_start, idx - 1))
    if in_gap:
        gaps.append((gap_start, total_lines_recorded))
        
    print(f"Total gaps: {len(gaps)}")
    for g in gaps:
        print(f"Gap: lines {g[0]} to {g[1]} (length {g[1] - g[0] + 1})")
        
    # Let's save the reconstructed file (with gaps marked)
    with open("scratch/reconstructed_web_backend.py", "w", encoding="utf-8") as out:
        for idx in range(1, total_lines_recorded + 1):
            if idx in line_map:
                out.write(line_map[idx] + "\n")
            else:
                out.write(f"# === GAP: MISSING LINE {idx} ===\n")
                
    print("Saved reconstructed file with gaps to scratch/reconstructed_web_backend.py")

if __name__ == "__main__":
    run()
