import json
import os

def run():
    path = r"C:\Users\nikun\.gemini\antigravity\brain\f71acb1b-ab5a-4de9-85a5-1a298f3c313a\.system_generated\logs\transcript.jsonl"
    with open(path, "r", encoding="utf-8") as f:
        lines = list(f)
        
    print(f"Total steps in log: {len(lines)}")
    os.makedirs("scratch/recovered", exist_ok=True)
    matches_count = 0
    for idx, line in enumerate(lines):
        item = json.loads(line)
        step_type = item.get('type')
        if step_type == 'VIEW_FILE' and item.get('status') == 'DONE':
            content = item.get('content', '')
            if 'web_backend.py' in content:
                # Find line range if printed in the header
                # e.g., "Showing lines 2161 to 2200"
                header_line = ""
                for l in content.splitlines()[:15]:
                    if "showing lines" in l.lower() or "showing line" in l.lower() or "total lines" in l.lower():
                        header_line += l + " | "
                print(f"Step {idx}: {header_line}")
                with open(f"scratch/recovered/step_{idx}.txt", "w", encoding="utf-8") as out:
                    out.write(content)
                matches_count += 1
    print(f"Saved {matches_count} files to scratch/recovered/")

if __name__ == "__main__":
    run()
