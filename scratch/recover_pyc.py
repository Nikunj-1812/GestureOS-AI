import marshal
import os

def run():
    pyc_path = r".\__pycache__\web_backend.cpython-312.pyc"
    if not os.path.exists(pyc_path):
        print("Compiled file not found!")
        return

    with open(pyc_path, "rb") as f:
        # Read header (16 bytes in Python 3.12)
        header = f.read(16)
        magic = header[:4]
        print("Magic:", magic)
        # Load the code object
        try:
            code_obj = marshal.load(f)
            print("Successfully loaded code object!")
        except Exception as e:
            print("Error loading with marshal:", e)
            return
            
    # Look at constants in the module code object
    # HTML_CONTENT should be one of the constants
    print(f"Number of constants: {len(code_obj.co_consts)}")
    html_content = None
    for idx, const in enumerate(code_obj.co_consts):
        if isinstance(const, str) and "<!DOCTYPE html>" in const:
            print(f"Found HTML_CONTENT at constant index {idx}!")
            html_content = const
            break
            
    if html_content:
        # Save recovered HTML_CONTENT to a file
        out_path = "scratch/recovered_html_content.html"
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(html_content)
        print(f"Saved recovered HTML content to {out_path} (length {len(html_content)} characters)")
    else:
        print("HTML_CONTENT not found in module constants.")

if __name__ == "__main__":
    run()
