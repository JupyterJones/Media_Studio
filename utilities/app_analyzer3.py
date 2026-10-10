#!/usr/bin/env python3
"""
app_analyzer.py

Incremental Flask route analyzer with dependency tracking
and power-loss recovery.

Features:
- Extracts Flask @app.route endpoints
- Detects required helper functions, attributes, and decorators
- Generates AI docstrings via Ollama (non-streaming)
- Cleans docstrings and prints live preview before saving
- Saves EACH route immediately to SQLite and JSON
- Tracks completion state so restarts resume safely
"""

import ast
import os
import sqlite3
import json
import argparse
import requests
from icecream import ic
import gc
import hashlib
import re

# ---------------- CONFIG ----------------
DATABASE_FILE = "flask_routes3.db"
JSON_EXPORT_FILE = "flask_routes3.json"
OLLAMA_MODEL = "codellama:13b"
OLLAMA_TIMEOUT = 800

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    ic("Initializing database (safe mode, no destructive reset)...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route TEXT,
            function_name TEXT,
            docstring TEXT,
            template_file TEXT,
            required_functions TEXT,
            route_hash TEXT UNIQUE,
            status TEXT
        )
    """)

    conn.commit()
    return conn

# ---------------- JSON SAFE LOAD ----------------
def load_json():
    if not os.path.isfile(JSON_EXPORT_FILE):
        ic("No existing JSON file found, starting fresh.")
        return {}

    try:
        with open(JSON_EXPORT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        ic("JSON corrupted, starting new:", e)
        return {}

def save_json(data):
    tmp = JSON_EXPORT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp, JSON_EXPORT_FILE)

# ---------------- CLEAN DOCSTRING ----------------
def clean_docstring(doc: str) -> str:
    if not doc:
        return ""

    doc = doc.replace("```", "")
    doc = doc.replace("\n", " ")
    doc = re.sub(r"\s+", " ", doc).strip()

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

    doc = re.sub(r"(Args:)", r"\n\n\1\n", doc)
    doc = re.sub(r"(Returns:)", r"\n\n\1\n", doc)
    doc = re.sub(r"(Raises:)", r"\n\n\1\n", doc)

    return doc.strip()

# ---------------- DEPENDENCY COLLECTOR ----------------
class DependencyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.dependencies = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.dependencies.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            self.dependencies.add(".".join(reversed(parts)))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            self.dependencies.add(".".join(reversed(parts)))
        self.generic_visit(node)

# ---------------- AST ROUTE ANALYSIS ----------------
class FlaskRouteVisitor(ast.NodeVisitor):
    def __init__(self):
        self.routes = []

    def visit_FunctionDef(self, node):
        routes = []
        template_file = None
        dependencies = set()

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr == "route" and decorator.args:
                    arg = decorator.args[0]
                    if isinstance(arg, ast.Constant):
                        routes.append(arg.value)
                    elif isinstance(arg, ast.JoinedStr):
                        routes.append("<dynamic>")
            elif isinstance(decorator, ast.Name):
                dependencies.add(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                dependencies.add(decorator.attr)

        dep_visitor = DependencyVisitor()
        dep_visitor.visit(node)
        dependencies |= dep_visitor.dependencies

        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Call):
                if isinstance(stmt.func, ast.Name) and stmt.func.id == "render_template":
                    if stmt.args and isinstance(stmt.args[0], ast.Constant):
                        template_file = stmt.args[0].value

        if routes:
            cleaned_deps = sorted(d for d in dependencies if not d.startswith("__"))
            self.routes.append({
                "function_name": node.name,
                "routes": routes,
                "template_file": template_file,
                "docstring": ast.get_docstring(node) or "",
                "required_functions": cleaned_deps
            })
            ic("Discovered:", node.name)
            ic("  Routes:", routes)
            ic("  Dependencies:", cleaned_deps)

        self.generic_visit(node)

# ---------------- ROUTE HASH ----------------
def route_hash(route, function_name):
    raw = f"{route}:{function_name}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

# ---------------- AI DOCSTRING ----------------
def generate_docstring(route_info):
    ic("Generating docstring for:", route_info["function_name"])
    prompt = (
        f"Write a clean Python docstring for this Flask route.\n"
        f"Function: {route_info['function_name']}\n"
        f"Route paths: {route_info['routes']}\n"
        f"Dependencies: {route_info['required_functions']}\n"
        f"Existing docstring: {route_info['docstring']}"
    )

    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "temperature": 0,
                "max_tokens": 3000
            },
            timeout=OLLAMA_TIMEOUT
        )
        r.raise_for_status()
        chunks = []
        for line in r.text.splitlines():
            try:
                js = json.loads(line)
                if "response" in js:
                    chunks.append(js["response"])
            except Exception:
                pass
        result = "\n".join(chunks).strip()
        if not result:
            result = route_info["docstring"] or "AI generation failed."
        return result
    except Exception as e:
        ic("Ollama failure:", e)
        return route_info["docstring"] or "AI generation failed."
    finally:
        gc.collect()

# ---------------- CLEAN + LIVE PREVIEW ----------------
def preview_and_clean(doc: str, route: str):
    cleaned = clean_docstring(doc)
    ic(f"Route: {route}")
    ic("Cleaned docstring preview:\n", cleaned)
    return cleaned

# ---------------- MAIN PROCESS ----------------
def analyze_flask_app(filepath, use_ai):
    if not os.path.isfile(filepath):
        ic("File not found:", filepath)
        return

    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    visitor = FlaskRouteVisitor()
    visitor.visit(tree)

    conn = init_db()
    c = conn.cursor()
    json_data = load_json()

    for item in visitor.routes:
        for route in item["routes"]:
            h = route_hash(route, item["function_name"])

            c.execute("SELECT status FROM routes WHERE route_hash=?", (h,))
            row = c.fetchone()
            if row and row[0] == "done":
                ic("Skipping already processed:", route)
                continue

            ic("Processing route:", route)

            doc = item["docstring"]
            if use_ai:
                doc = generate_docstring(item)

            # CLEAN & PREVIEW LIVE
            doc = preview_and_clean(doc, route)

            deps_json = json.dumps(item["required_functions"])

            c.execute("""
                INSERT OR REPLACE INTO routes
                (route, function_name, docstring, template_file,
                 required_functions, route_hash, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                route,
                item["function_name"],
                doc,
                item["template_file"],
                deps_json,
                h,
                "done"
            ))
            conn.commit()

            json_data[h] = {
                "route": route,
                "function_name": item["function_name"],
                "docstring": doc,
                "template_file": item["template_file"],
                "required_functions": item["required_functions"]
            }
            save_json(json_data)
            ic("Saved route safely:", route)
            gc.collect()

    conn.close()
    ic("All routes processed safely.")

# ---------------- CLI ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    parser.add_argument("--ai-docstrings", action="store_true")
    args = parser.parse_args()

    analyze_flask_app(args.filepath, args.ai_docstrings)
