#!/usr/bin/env python3
"""
Filename: docstring_generator.py
Flask Docstring Generator using Ollama (Local LLM)

Evaluates user-submitted Python functions or HTML blocks,
generates high-quality docstrings, displays them live,
and persists results to JSON and TXT collections.
"""

import os
import json
import time
import requests
import traceback
from datetime import datetime
from icecream import ic
from flask import Flask, request, render_template_string

# -----------------------------
# CONFIG
# -----------------------------


#MODEL = "qwen3:8b"           
#MODEL = "deepseek-r1:1.5b"
#MODEL = "deepseek-coder:1.3b"     

MODEL = "llama3.2:3b"
#MODEL = "codellama:13b"
ENDPOINT = "http://localhost:11434/api/generate"
TIMEOUT = 900

JSON_COLLECTION = "docs.json"
TXT_COLLECTION = "docs.txt"
LOG_FILE_PATH = "static/doc_log.txt"

os.makedirs("static", exist_ok=True)

# -----------------------------
# APP
# -----------------------------
app = Flask(__name__)

# -----------------------------
# LOGGING
# -----------------------------
def logit(*args):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = " ".join(str(a) for a in args)
        with open(LOG_FILE_PATH, "a") as f:
            f.write(f"{ts} | {msg}\n")
    except Exception as e:
        print("LOG ERROR:", e)

# -----------------------------
# OLLAMA
# -----------------------------
def call_ollama(prompt: str) -> str:
    ic("OLLAMA PROMPT", prompt)

    r = requests.post(
        ENDPOINT,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "max_tokens": 800,
        },
        timeout=TIMEOUT,
    )

    r.raise_for_status()
    response = r.json().get("response", "").strip()
    response = response.replace("\n\n","\n")
    ic("OLLAMA RESPONSE", response)
    return response

# -----------------------------
# STORAGE
# -----------------------------
def append_results(source: str, docstring: str):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "docstring": docstring,
    }

    try:
        if os.path.exists(JSON_COLLECTION):
            with open(JSON_COLLECTION, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.append(entry)

        with open(JSON_COLLECTION, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        with open(TXT_COLLECTION, "a", encoding="utf-8") as f:
            f.write(docstring + "\n\n")

        logit("Saved docstring entry")

    except Exception:
        logit("SAVE ERROR")
        traceback.print_exc()

# -----------------------------
# DOCSTRING GENERATION
# -----------------------------
def generate_docstring(code: str) -> str:
    prompt = f"""
You are a senior Python developer.

Generate a CLEAN, PROFESSIONAL Python docstring.

Rules:
- Output ONLY the docstring
- Triple-quoted
- No markdown
- No explanations
- Max 125 words
- Describe purpose, arguments, and return value if applicable

CODE:
{code}
""".strip()

    return call_ollama(prompt)

# -----------------------------
# UI
# -----------------------------
PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Docstring Generator</title>
    <style>
        body {
            background: #111;
            color: #9fef00;
            font-family: monospace;
            padding: 20px;
        }
        textarea {
            width: 100%;
            height: 220px;
            background: #000;
            color: #9fef00;
            border: 1px solid #555;
            padding: 10px;
            font-size: 15px;
        }
        button {
            padding: 10px 20px;
            background: #9fef00;
            border: none;
            font-weight: bold;
            cursor: pointer;
        }
    </style>
</head>
<body>

<h2>Docstring Generator (Ollama)</h2>

<form method="POST">
    <h3>Input Code</h3>
    <textarea name="code">{{ code }}</textarea><br><br>
    <button type="submit">Generate Docstring</button>
</form>

{% if docstring %}
<h3>Generated Docstring</h3>
<textarea readonly>{{ docstring }}</textarea>
{% endif %}

</body>
</html>
"""

# -----------------------------
# ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    code = ""
    docstring = ""

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if code:
            try:
                docstring = generate_docstring(code)
                append_results(code, docstring)
            except Exception:
                docstring = "ERROR generating docstring"
                traceback.print_exc()

    return render_template_string(PAGE, code=code, docstring=docstring)

# -----------------------------
# ENTRY
# -----------------------------
if __name__ == "__main__":
    logit("Docstring Generator Started")
    app.run(host="0.0.0.0", port=5400, debug=True)
