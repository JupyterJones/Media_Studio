# codellama_analyze.py
import os
import sys
import requests
from icecream import ic

# -----------------------------
# CONFIGURATION
# -----------------------------
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL = "codellama:13b"
MAX_TOKENS = 3000
CHUNK_SIZE_LINES = 200  # Split large scripts into 200-line chunks

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def read_py_file(file_path):
    ic("Reading Python file:", file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()

def call_codellama(prompt):
    ic("Sending prompt to codellama...")
    payload = {"model": MODEL, "prompt": prompt, "max_tokens": MAX_TOKENS}
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        ic("Status code:", response.status_code)
        if response.status_code == 200:
            full_text = ""
            for line in response.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    # Each line is a JSON object with a 'response' field
                    import json
                    data = json.loads(line)
                    full_text += data.get("response", "")
                except Exception:
                    full_text += line
            return full_text
        else:
            ic("Error:", response.text)
            return ""
    except Exception as e:
        ic("Request failed:", e)
        return ""


def chunk_lines(lines, chunk_size=CHUNK_SIZE_LINES):
    for i in range(0, len(lines), chunk_size):
        yield lines[i:i+chunk_size]

def create_readme(py_file, analysis_chunks):
    readme_file = os.path.splitext(py_file)[0] + "_README.md"
    ic("Creating README.md at:", readme_file)

    content = f"# {os.path.basename(py_file)}\n\n"
    if not analysis_chunks:
        content += "⚠️ Codellama did not return a valid analysis. Try again or increase MAX_TOKENS.\n\n"
    else:
        for idx, chunk_text in enumerate(analysis_chunks, start=1):
            content += f"## Chunk {idx}\n"
            content += chunk_text + "\n\n"

    content += "## Usage Instructions\n"
    content += "1. Make sure you have Python 3 installed.\n"
    content += f"2. Run the script using:\n```\npython {py_file}\n```\n"
    content += "3. Follow any instructions or prompts inside the script.\n"
    content += "\n## Capabilities\n"
    content += "- Full function and class descriptions\n"
    content += "- Usage examples extracted from the code\n"
    content += "- Notes on potential improvements or considerations\n"

    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(content)
    ic("README.md created successfully!")

# -----------------------------
# MAIN SCRIPT
# -----------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        ic("Usage: python codellama_analyze.py <python_file.py>")
        sys.exit(1)

    py_file = sys.argv[1]
    if not os.path.isfile(py_file):
        ic(f"Python file '{py_file}' does not exist.")
        sys.exit(1)

    code_lines = read_py_file(py_file)
    ic(f"Total lines in script: {len(code_lines)}")

    analysis_chunks = []
    for idx, chunk in enumerate(chunk_lines(code_lines)):
        ic(f"Processing chunk {idx + 1}")
        chunk_text = "".join(chunk)
        prompt = f"""
You are a highly intelligent AI Python analyst.

Analyze the following Python script chunk and generate a detailed explanation including:
- Overall purpose
- Function-by-function and class-by-class breakdown
- Dependencies or requirements
- Suggested improvements or best practices
- How to run the code with example usage

Python chunk:
{chunk_text}

Output in detailed markdown format suitable for a README.md.
"""
        chunk_analysis = call_codellama(prompt)
        analysis_chunks.append(chunk_analysis)

    create_readme(py_file, analysis_chunks)
    ic("All done! README.md is ready.")
