# deepseek_analyze.py
import os
import sys
from icecream import ic
import requests

# ---------------------------------------
# CONFIGURATION
# ---------------------------------------
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-coder:1.3b"
MAX_TOKENS = 3000

# ---------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------
def read_py_file(file_path):
    ic("Reading Python file:", file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def call_deepseek_coder(prompt):
    """
    Send a prompt to the deepseek-coder model and collect streamed output.
    Handles NDJSON line-by-line parsing.
    """
    ic("Sending prompt to deepseek-coder...")

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "max_tokens": MAX_TOKENS,
        "stream": True
    }

    response = requests.post(OLLAMA_API_URL, json=payload, stream=True)
    ic("Status code:", response.status_code)

    if response.status_code != 200:
        ic("Error:", response.text)
        return ""

    final_text = ""

    for line in response.iter_lines():
        if not line:
            continue

        try:
            decoded = line.decode("utf-8")
            ic("Raw line:", decoded)
            obj = requests.utils.json.loads(decoded)

            if "response" in obj:
                final_text += obj["response"]

            if obj.get("done"):
                break

        except Exception as e:
            ic("JSON parse error:", e)
            continue

    return final_text

def create_readme(py_file, analysis_text):
    readme_file = os.path.splitext(py_file)[0] + "_README.md"
    ic("Creating README.md at:", readme_file)

    content = f"# {os.path.basename(py_file)}\n\n"
    content += "## Overview\n"
    content += analysis_text + "\n\n"
    content += "## Usage Instructions\n"
    content += f"Run the script with:\n```\npython {py_file}\n```\n"
    content += "\n## Capabilities\n"
    content += "- Full function and class breakdown\n"
    content += "- Usage examples\n"
    content += "- Suggested improvements\n"

    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(content)

    ic("README.md created successfully!")

# ---------------------------------------
# MAIN
# ---------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        ic("Usage: python deepseek_analyze.py <python_file.py>")
        sys.exit(1)

    py_file = sys.argv[1]

    if not os.path.isfile(py_file):
        ic(f"Python file '{py_file}' does not exist.")
        sys.exit(1)

    code_content = read_py_file(py_file)

    prompt = f"""
You are a highly intelligent AI Python analyst.

Analyze the following Python script and generate a detailed explanation including:
- Overall purpose
- Function-by-function and class-by-class breakdown
- Dependencies and requirements
- Suggested improvements
- How to run and example usage

Python script:
{code_content}

Output as detailed Markdown for README.md.
"""

    analysis = call_deepseek_coder(prompt)

    create_readme(py_file, analysis)

    ic("All done! README.md is ready.")
