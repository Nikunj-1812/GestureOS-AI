import re
import sys

def analyze():
    with open("web_backend.py", "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = '<script type="text/babel">'
    end_marker = '</script>'
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Start marker not found")
        sys.exit(1)
    
    # Since end marker might be missing currently, we scan till HTMLResponse definition or file end
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print("End marker not found, parsing until HTMLResponse route or end of HTML string")
        end_idx = content.find('</html>"""', start_idx)
        if end_idx == -1:
            print("Could not find end of HTML string either!")
            sys.exit(1)
            
    js_code = content[start_idx + len(start_marker):end_idx]
    
    # Basic tokenization of tags: find all <something> and </something>
    # Be careful of JavaScript comparisons (e.g. i < 10) and self-closing tags
    # Let's remove comments and strings first for safety
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
        
    # Reassemble code
    flat_code = "".join(x[0] for x in clean_code)
    
    # Simple regex to find JSX tags:
    # We look for <[a-zA-Z0-9_]+ or </[a-zA-Z0-9_]+ or <> or </>
    # Self-closing tags end with />
    # Let's write a scanner for < and >
    tags_found = []
    i = 0
    while i < len(clean_code):
        char, line_num, line = clean_code[i]
        if char == '<':
            # Check if this is a tag or a comparison
            # JSX tags must start with a letter, /, or > (fragment start/end)
            if i + 1 < len(clean_code):
                next_char = clean_code[i+1][0]
                if next_char.isalpha() or next_char in ('/', '>'):
                    # Scan tag until '>'
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
                        # Check if it is a tag (exclude things like < 5 or expressions like i < len)
                        # Let's parse tag name
                        is_closing = tag_str.startswith('</')
                        is_self_closing = tag_str.endswith('/>') and not is_closing
                        
                        # Extract tag name: e.g. <div class="..." -> div
                        name = ""
                        if tag_str == '<>':
                            name = 'fragment'
                        elif tag_str == '</>':
                            name = 'fragment'
                            is_closing = True
                        else:
                            # matches name
                            m = re.match(r'^</?([a-zA-Z0-9:-]+)', tag_str)
                            if m:
                                name = m.group(1)
                                
                        if name:
                            tags_found.append({
                                'name': name,
                                'is_closing': is_closing,
                                'is_self_closing': is_self_closing,
                                'line_num': line_num,
                                'line': line,
                                'tag_str': tag_str
                            })
                        i = j + 1
                        continue
        i += 1
        
    # Stack verification
    stack = []
    for tag in tags_found:
        if tag['is_self_closing']:
            continue
        if tag['is_closing']:
            if not stack:
                print(f"Unmatched closing tag: </{tag['name']}> at line {tag['line_num']}")
                print(f"Line: {tag['line'].strip()}")
                return False
            top = stack.pop()
            print(f"POP: closed </{tag['name']}> (matched <{top['name']}> opened at {top['line_num']}) at line {tag['line_num']}")
            if top['name'] != tag['name']:
                print(f"Mismatch: opened <{top['name']}> at line {top['line_num']} but closed </{tag['name']}> at line {tag['line_num']}")
                print(f"Opened: {top['line'].strip()}")
                print(f"Closed: {tag['line'].strip()}")
                return False
        else:
            print(f"PUSH: opened <{tag['name']}> at line {tag['line_num']}")
            stack.append(tag)
            
    if stack:
        print(f"Unclosed tags left: {len(stack)}")
        for tag in stack[-10:]:
            print(f"Opened <{tag['name']}> at line {tag['line_num']}")
            print(f"Line: {tag['line'].strip()}")
        return False
        
    print("Success: All JSX tags are perfectly matched!")
    return True

if __name__ == "__main__":
    analyze()
