def run():
    # Read the current web_backend.py
    with open("web_backend.py", "r", encoding="utf-8") as f:
        code_lines = f.read().splitlines()
        
    # Find the start of HTML_CONTENT definition
    start_idx = -1
    for idx, line in enumerate(code_lines):
        if line.startswith('HTML_CONTENT = """'):
            start_idx = idx
            break
            
    if start_idx == -1:
        print("Could not find start of HTML_CONTENT in web_backend.py!")
        return
        
    print(f"HTML_CONTENT starts at line {start_idx + 1}")
    
    # Find the end of HTML_CONTENT string in the current file
    end_idx = -1
    for idx in range(start_idx, len(code_lines)):
        if code_lines[idx].rstrip().endswith('</html>"""') or code_lines[idx].rstrip() == '</html>"""':
            end_idx = idx
            break
            
    if end_idx == -1:
        print("Could not find end of HTML_CONTENT (</html>\"\"\") in current web_backend.py!")
        return
        
    print(f"HTML_CONTENT ends at line {end_idx + 1}")
    
    # Read the recovered HTML content
    with open("scratch/recovered_html_content.html", "r", encoding="utf-8") as f:
        recovered_html = f.read()
        
    # Reassemble the file
    prefix = "\n".join(code_lines[:start_idx])
    suffix = "\n".join(code_lines[end_idx + 1:])
    
    # Construct new file content
    new_content = prefix + '\nHTML_CONTENT = """' + recovered_html + '"""\n' + suffix
    
    # Write to web_backend.py
    with open("web_backend.py", "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Successfully restored web_backend.py!")

if __name__ == "__main__":
    run()
