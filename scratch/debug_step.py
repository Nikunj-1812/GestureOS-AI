import json
import sys

def run():
    path = r"C:\Users\nikun\.gemini\antigravity\brain\f71acb1b-ab5a-4de9-85a5-1a298f3c313a\.system_generated\logs\transcript.jsonl"
    with open(path, "r", encoding="utf-8") as f:
        lines = list(f)
    
    item = json.loads(lines[3723])
    tc = item['tool_calls'][0]
    chunks = tc['args']['ReplacementChunks']
    if isinstance(chunks, str):
        chunks = json.loads(chunks, strict=False)
    
    print(f"Total chunks: {len(chunks)}")
    for i, c in enumerate(chunks):
        start = c.get('StartLine')
        end = c.get('EndLine')
        target = c.get('TargetContent')
        repl = c.get('ReplacementContent')
        print(f"\n--- CHUNK {i} (lines {start}-{end}) ---")
        print(f"Target length: {len(target)} chars, Replacement length: {len(repl)} chars")
        print("Target Content preview:")
        print("\n".join(target.splitlines()[:5]))
        print("Replacement Content preview:")
        print("\n".join(repl.splitlines()[:5]))

if __name__ == "__main__":
    run()
