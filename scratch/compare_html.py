with open("scratch/recovered_html_content.html", "r", encoding="utf-8") as f:
    content = f.read()

checks = [
    ("drawing-canvas", "drawing-canvas" in content),
    ("virtualMouseEnabled", "virtualMouseEnabled" in content),
    ("handleWebUndo", "handleWebUndo" in content),
    ("handleWebRedo", "handleWebRedo" in content),
    ("handleWebClear", "handleWebClear" in content),
    ("handleWebSave", "handleWebSave" in content),
    ("systemTypingEnabled", "systemTypingEnabled" in content),
    ("keyboard_autocomplete_enabled", "keyboard_autocomplete_enabled" in content),
    ("Emoji", "emoji" in content.lower()),
    ("HUD Mode Pill", "drawing-hud-pill" in content or "hud-pill" in content),
    ("Tool Settings Menu", "drawing-tool-menu" in content or "tool-menu" in content)
]

print("Checking recovered HTML Content:")
for name, found in checks:
    print(f" - {name}: {'FOUND' if found else 'NOT FOUND'}")

print("Total length:", len(content))
