#!/usr/bin/env python3
from flask import Flask, render_template_string
import sqlite3
import json
from icecream import ic
import re

app = Flask(__name__)

# ---------------- CONFIG ----------------
DB_FILE = "flask_routes1.db"
JSON_FILE = "flask_routes1.json"

# ---------------- DOCSTRING CLEANING ----------------
def clean_docstring(doc: str) -> str:
    """
    Repair severely tokenized AI-generated docstrings.
    Handles token-per-line output, broken identifiers, and punctuation.
    """
    if not doc:
        return ""

    # ---------------- REMOVE CODE FENCES ----------------
    doc = doc.replace("```", "")

    # ---------------- FLATTEN EVERYTHING ----------------
    # This is the key fix: treat it as a token stream, not text
    doc = doc.replace("\n", " ")
    doc = re.sub(r"\s+", " ", doc).strip()

    # ---------------- FIX COMMON TOKEN SPLITS ----------------
    fixes = {
        r"\bM\s*P\s*3\b": "MP3",
        r"\bV\s*a\s*l\s*u\s*e\s*E\s*r\s*r\s*o\s*r\b": "ValueError",
        r"\bR\s*a\s*i\s*s\s*e\s*s\b": "Raises",
        r"\bA\s*r\s*g\s*s\b": "Args",
        r"\bD\s*e\s*f\s*a\s*u\s*l\s*t\s*s\b": "Defaults",
        r"_\s+": "_",
        r"\s+_": "_",
        r"\s+\(": "(",
        r"\(\s+": "(",
        r"\s+\)": ")",
        r"\s+:\s*": ": ",
        r"\s+,": ",",
        r"\s+->\s+": " -> ",
        r"\"\s*en\s*-\s*US\s*\"": "\"en-US\"",
    }

    for pattern, replacement in fixes.items():
        doc = re.sub(pattern, replacement, doc, flags=re.IGNORECASE)

    # ---------------- REFORMAT STRUCTURE ----------------
    # Restore docstring-like spacing
    doc = re.sub(r"(Args:)", r"\n\n\1\n", doc)
    doc = re.sub(r"(Returns:)", r"\n\n\1\n", doc)
    doc = re.sub(r"(Raises:)", r"\n\n\1\n", doc)

    ic("CLEANED DOCSTRING:\n", doc)
    return doc.strip()


# ---------------- HTML TEMPLATE ----------------
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Flask Routes Viewer</title>
<style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
    h1, h2 { margin-bottom: 15px; }
    .route-container { display: flex; flex-direction: column; gap: 15px; }
    .route-card { display: flex; background: #fff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow: hidden; }
    .route-info { flex: 0 0 300px; padding: 15px; background: #e9ecef; border-right: 1px solid #ddd; word-break: break-word; }
    .route-info strong { display: block; margin-bottom: 5px; }
    .docstring { flex: 1; padding: 15px; white-space: pre-wrap; word-wrap: break-word; overflow-x: auto; }
    .section { margin-bottom: 40px; }
</style>
</head>
<body>
    <h1>Flask Routes Viewer</h1>

    <div class="section">
        <h2>Routes from SQLite</h2>
        <div class="route-container">
        {% for row in sqlite_routes %}
            <div class="route-card">
                <div class="route-info">
                    <strong>ID:</strong> {{ row['id'] }}<br>
                    <strong>Route:</strong> {{ row['route'] }}<br>
                    <strong>Function:</strong> {{ row['function_name'] }}<br>
                    <strong>Template:</strong> {{ row['template_file'] or '' }}
                </div>
                <div class="docstring">{{ clean_docstring(row['docstring']) }}</div>
            </div>
        {% endfor %}
        </div>
    </div>

    <div class="section">
        <h2>Routes from JSON</h2>
        <div class="route-container">
        {% for r in json_routes %}
            <div class="route-card">
                <div class="route-info">
                    <strong>Function:</strong> {{ r['function_name'] }}<br>
                    <strong>Routes:</strong> {{ r['route_paths'] | join(", ") }}<br>
                    <strong>Template:</strong> {{ r['template_file'] or '' }}
                </div>
                <div class="docstring">{{ clean_docstring(r['docstring']) }}</div>
            </div>
        {% endfor %}
        </div>
    </div>

</body>
</html>
"""

# ---------------- ROUTE ----------------
@app.route("/")
def view_routes():
    # Load SQLite
    sqlite_routes = []
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM routes")
        sqlite_routes = [dict(row) for row in c.fetchall()]
        conn.close()
        ic(f"Loaded {len(sqlite_routes)} routes from SQLite.")
    except Exception as e:
        ic(f"Error loading SQLite: {e}")

    # Load JSON
    json_routes = []
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            json_routes = json.load(f)
        ic(f"Loaded {len(json_routes)} routes from JSON.")
    except Exception as e:
        ic(f"Error loading JSON: {e}")

    return render_template_string(
        HTML_TEMPLATE,
        sqlite_routes=sqlite_routes,
        json_routes=json_routes,
        clean_docstring=clean_docstring  # pass function to Jinja
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100, debug=True)
