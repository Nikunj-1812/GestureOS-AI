import re

with open("web_backend.py", "r", encoding="utf-8") as f:
    content = f.read()

# Extract script content
start_marker = '<script type="text/babel">'
end_marker = '</script>'

start_idx = content.find(start_marker)
if start_idx == -1:
    print("Could not find start marker")
    exit(1)
start_idx += len(start_marker)

end_idx = content.find(end_marker, start_idx)
if end_idx == -1:
    print("Could not find end marker")
    exit(1)

js_code = content[start_idx:end_idx]

# Strip strings and comments from js_code for accurate bracket matching
# We will do a character-by-character scan to construct a version with only non-string, non-comment characters.
clean_chars = []
in_string = None  # None, "'", '"', '`'
escape = False
in_line_comment = False
in_block_comment = False

# For error reporting, keep matching lists of (char, line, col, original_line)
for line_num, line in enumerate(js_code.split('\n'), 1):
    i = 0
    while i < len(line):
        char = line[i]
        
        if in_line_comment:
            # Line comment ends at newline, which happens outside this loop
            i += 1
            continue
        if in_block_comment:
            if char == '*' and i + 1 < len(line) and line[i+1] == '/':
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue
            
        if in_string:
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == in_string:
                in_string = None
            i += 1
            continue
            
        # Check comments
        if char == '/' and i + 1 < len(line):
            if line[i+1] == '/':
                in_line_comment = True
                i += 2
                continue
            elif line[i+1] == '*':
                in_block_comment = True
                i += 2
                continue
                
        # Check string starts
        if char in ("'", '"', '`'):
            in_string = char
            i += 1
            continue
            
        # Normal character
        clean_chars.append((char, line_num, i, line))
        i += 1
    # Line comment ends at newline
    in_line_comment = False

stack = []
mapping = {')': '(', '}': '{', ']': '['}

for char, line_num, char_idx, line in clean_chars:
    if char in '({[':
        stack.append((char, line_num, char_idx, line))
    elif char in ')}]':
        if not stack:
            print(f"Unmatched closing char '{char}' at line {line_num}:{char_idx}")
            print(f"Line content: {line.strip()}")
            exit(1)
        top_char, top_line, top_char_idx, top_line_content = stack.pop()
        if top_char != mapping[char]:
            print(f"Mismatch: opened '{top_char}' at line {top_line}:{top_char_idx} but closed '{char}' at line {line_num}:{char_idx}")
            print(f"Opening line: {top_line_content.strip()}")
            print(f"Closing line: {line.strip()}")
            exit(1)

if stack:
    print(f"Unclosed braces/brackets left: {len(stack)}")
    for char, line_num, char_idx, line in stack[-5:]:
        print(f"Opened '{char}' at line {line_num}:{char_idx}")
        print(f"Line: {line.strip()}")
else:
    print("All brackets/braces/parentheses match perfectly!")
