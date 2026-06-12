import json
import os

log_path = r"C:\Users\nikun\.gemini\antigravity\brain\f71acb1b-ab5a-4de9-85a5-1a298f3c313a\.system_generated\logs\transcript.jsonl"

if not os.path.exists(log_path):
    print("Logs not found at:", log_path)
    exit(1)

print("Logs found. Searching for web_backend.py modifications...")

with open(log_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if "createRoot" in line or "ReactDOM" in line:
            print(f"Match found on line {i+1}!")
            # Print a portion of the line containing the term
            idx = line.find("createRoot")
            if idx != -1:
                start = max(0, idx - 100)
                end = min(len(line), idx + 200)
                print("Context:", line[start:end])
            else:
                idx = line.find("ReactDOM")
                start = max(0, idx - 100)
                end = min(len(line), idx + 200)
                print("Context:", line[start:end])
            print("-" * 60)
