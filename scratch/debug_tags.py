with open("web_backend.py", "r", encoding="utf-8") as f:
    content = f.read()

start_marker = '<script type="text/babel">'
start_idx = content.find(start_marker)
end_idx = content.find('</html>"""', start_idx)
js_code = content[start_idx + len(start_marker):end_idx]

import re
clean_code = []
in_string = None
escape = False
in_line_comment = False
in_block_comment = False

lines = js_code.split('\n')
for line_num, line in enumerate(lines, 1):
    i = 0
    while i < len(line):
        char = line[i]
        if in_line_comment:
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
        
        if char == '/' and i + 1 < len(line):
            if line[i+1] == '/':
                in_line_comment = True
                i += 2
                continue
            elif line[i+1] == '*':
                in_block_comment = True
                i += 2
                continue
        if char in ("'", '"', '`'):
            in_string = char
            i += 1
            continue
        
        clean_code.append((char, line_num, line))
        i += 1
    in_line_comment = False
    clean_code.append(('\n', line_num, line))

tags_found = []
i = 0
while i < len(clean_code):
    char, line_num, line = clean_code[i]
    if char == '<':
        if i + 1 < len(clean_code):
            next_char = clean_code[i+1][0]
            if next_char.isalpha() or next_char in ('/', '>'):
                tag_chars = []
                j = i
                closed_correctly = False
                brace_depth = 0
                while j < len(clean_code):
                    c = clean_code[j][0]
                    tag_chars.append(c)
                    if c == '{':
                        brace_depth += 1
                    elif c == '}':
                        brace_depth -= 1
                    elif c == '>' and brace_depth == 0:
                        closed_correctly = True
                        break
                    j += 1
                if closed_correctly:
                    tag_str = "".join(tag_chars)
                    is_closing = tag_str.startswith('</')
                    is_self_closing = tag_str.endswith('/>')
                    
                    name = ""
                    if tag_str == '<>':
                        name = 'fragment'
                    elif tag_str == '</>':
                        name = 'fragment'
                        is_closing = True
                    else:
                        m = re.match(r'^</?([a-zA-Z0-9:-]+)', tag_str)
                        if m:
                            name = m.group(1)
                            
                    if name:
                        tags_found.append({
                            'name': name,
                            'is_closing': is_closing,
                            'is_self_closing': is_self_closing,
                            'line_num': line_num,
                            'tag_str': tag_str
                        })
                    i = j + 1
                    continue
    i += 1

for tag in tags_found:
    # 2825 to 2845
    if 2825 <= tag['line_num'] <= 2845:
        print(f"Line {tag['line_num']}: {tag['tag_str']} -> name={tag['name']} is_closing={tag['is_closing']} is_self_closing={tag['is_self_closing']}")
