#!/usr/bin/env python3
"""
Flask-based Code Suggestion and Completion Engine
Improved stability, logging, and UI theme
Author: Jack
"""

# -----------------------------
# IMPORTS
# -----------------------------
import os
import sys
import json
import time
import inspect
import sqlite3
import traceback
import requests
import subprocess
from datetime import datetime
from icecream import ic

from flask import (
    Flask,
    request,
    redirect,
    render_template_string,
    url_for,
)

# -----------------------------
# CONFIG
# -----------------------------
app = Flask(__name__)
app.secret_key = "local-dev-only"

DATABASEF = "static/functions.db"
LOG_FILE_PATH = "static/doc_log.txt"

MODEL = "codellama:13b"
ENDPOINT = "http://localhost:11434/api/generate"
TIMEOUT = 900

DEFAULT_VARIATIONS = 3

# Ensure directories exist
os.makedirs("static", exist_ok=True)

# -----------------------------
# LOGGING
# -----------------------------
def logit(*args):
    try:
        timestr = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        frame = inspect.stack()[1]
        filename = os.path.basename(frame.filename)
        lineno = frame.lineno

        msg = " ".join(str(a) for a in args)

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{timestr} | {filename}:{lineno} | {msg}\n")

    except Exception as e:
        print("[LOGIT ERROR]", e)


# -----------------------------
# DATABASE
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASEF)
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS functions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_text TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_function(text):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO functions (function_text) VALUES (?)",
        (text,)
    )
    conn.commit()
    conn.close()


def read_functions():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT function_text FROM functions"
    ).fetchall()
    conn.close()
    return [r["function_text"] for r in rows]


def get_last_function():
    conn = get_db_connection()
    row = conn.execute(
        "SELECT function_text FROM functions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["function_text"] if row else ""


def insert_functions_once():
    conn = get_db_connection()
    cur = conn.cursor()

    flag = cur.execute(
        "SELECT value FROM metadata WHERE key='initialized'"
    ).fetchone()

    if flag:
        conn.close()
        return

    path = "static/TEXT/appbp_all_html.txt"
    if not os.path.exists(path):
        logit("Seed file missing:", path)
        conn.close()
        return

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        blocks = f.read().split("@app")

    for b in blocks:
        if b.strip():
            cur.execute(
                "INSERT INTO functions (function_text) VALUES (?)",
                (b.strip(),)
            )

    cur.execute(
        "INSERT INTO metadata (key, value) VALUES ('initialized', 'true')"
    )

    conn.commit()
    conn.close()


# -----------------------------
# SUGGESTION ENGINE
# -----------------------------
def generate_suggestions(code):
    functions = read_functions()
    if not functions:
        return []

    last_line = code.strip().splitlines()[-1]
    words = last_line.split()
    needle = " ".join(words[-2:]) if len(words) >= 2 else last_line

    matches = []

    for i, fn in enumerate(functions, 1):
        if needle in fn:
            idx = fn.rfind(needle)
            snippet = fn[idx + len(needle):].strip()
            snippet = snippet[:400]
            matches.append(f"<pre>{i}: {snippet}</pre>")
        if len(matches) >= 5:
            break

    return matches


# -----------------------------
# OLLAMA
# -----------------------------
def call_ollama(prompt):
    ic("PROMPT", prompt[:120])

    r = requests.post(
        ENDPOINT,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=TIMEOUT
    )
    r.raise_for_status()
    return r.json().get("response", "").lstrip()


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML, last=get_last_function())


@app.route("/save", methods=["POST"])
def save():
    code = request.form["code"]
    suggestions = generate_suggestions(code)
    return {"suggestions": suggestions}


@app.route("/save_code", methods=["POST"])
def save_code():
    code = request.data.decode("utf-8")
    if code.strip():
        insert_function(code)
        logit("Saved code block")
        return "OK", 200
    return "EMPTY", 400


@app.route("/readlog")
def readlog():
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "<pre>" + "".join(lines[-500:]) + "</pre>"


# -----------------------------
# HTML (THEMED)
# -----------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Local Code Memory</title>

<style>
:root {
  --bg-main: #0b0f14;
  --bg-panel: #111823;
  --accent: #3cff8f;
  --text-main: #c7d0d9;
  --text-dim: #7a8899;
  --border: #1e2a3a;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg-main);
  color: var(--text-main);
  font-family: Consolas, monospace;
}

header {
  padding: 12px 20px;
  background: linear-gradient(90deg, #0f2027, #203a43);
  border-bottom: 1px solid var(--border);
  font-size: 20px;
  color: var(--accent);
}

main {
  display: flex;
  height: calc(100vh - 50px);
}

.panel {
  flex: 1;
  padding: 15px;
  border-right: 1px solid var(--border);
}

.panel:last-child {
  border-right: none;
}

textarea {
  width: 100%;
  height: 200px;
  background: #05080d;
  color: var(--accent);
  border: 1px solid var(--border);
  padding: 10px;
  font-size: 15px;
}

button {
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 6px 12px;
  cursor: pointer;
  margin-top: 8px;
}

button:hover {
  background: var(--accent);
  color: black;
}

pre {
  background: #05080d;
  padding: 10px;
  border: 1px solid var(--border);
  color: #9ad1ff;
}
</style>
</head>

<body>
<header>
  Local Code Suggestion Engine — GPU Dark
</header>

<main>
  <div class="panel">
    <h3>Input Code</h3>
    <textarea id="code"></textarea>
    <br>
    <button onclick="go()">Suggest</button>
  </div>

  <div class="panel">
    <h3>Suggestions</h3>
    <div id="out"></div>
  </div>
</main>

<script>
function go() {
  let fd = new FormData();
  fd.append("code", document.getElementById("code").value);

  fetch("/save", {method:"POST", body:fd})
    .then(r => r.json())
    .then(d => {
      let o = document.getElementById("out");
      o.innerHTML = "";
      d.suggestions.forEach(s => o.innerHTML += s);
    });
}
</script>
</body>
</html>
"""

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    create_db()
    insert_functions_once()
    app.run(host="0.0.0.0", port=5300, debug=True)
