#!/usr/bin/env python3
"""
Safe Flask Route Analyzer with Dry-Run Mode

- Merges new routes into an existing JSON collection safely
- Uses a new SQLite DB so nothing is overwritten
- Optional AI docstring generation for new routes
- Dry-run mode shows how many new routes would be added without saving
  Example: python app_analyzer_safe.py studioflaskback.py --ai-docstrings
"""

import ast
import os
import sqlite3
import json
import argparse
import requests
from icecream import ic
import concurrent.futures
import gc

# ---------------- CONFIG ----------------
OLD_JSON_FILE = "flask_routes1.json"
SAFE_JSON_FILE = "flask_routes_safe.json"
SAFE_DB_FILE = "flask_routes_safe.db"
OLLAMA_MODEL = "codellama:13b"
OLLAMA_TIMEOUT = 800
MAX_WORKERS = 2

# ---------------- DATABASE ----------------
def init_db(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY,
            route TEXT,
            function_name TEXT,
            docstring TEXT,
            template_file TEXT,
            UNIQUE(route,function_name)
        )
    ''')
    conn.commit()
    return conn

# ---------------- AST ANALYSIS ----------------
class FlaskRouteVisitor(ast.NodeVisitor):
    def __init__(self):
        self.routes = []

    def visit_FunctionDef(self, node):
        route_paths = []
        template_file = None

        # Detect @app.route decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr.lower() == 'route' and decorator.args:
                    value = decorator.args[0]
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        route_paths.append(value.value)
                    elif isinstance(value, ast.JoinedStr):
                        joined = "".join(v.s if isinstance(v, ast.Str) else "<dynamic>" for v in value.values)
                        route_paths.append(joined)

        # Detect template usage
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Call):
                func_name = stmt.func.id if isinstance(stmt.func, ast.Name) else getattr(stmt.func, 'attr', '')
                if func_name in ('render_template', 'render_template_string') and stmt.args:
                    arg0 = stmt.args[0]
                    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                        template_file = arg0.value

        if route_paths:
            self.routes.append({
                'function_name': node.name,
                'route_paths': route_paths,
                'template_file': template_file,
                'docstring': ast.get_docstring(node) or ""
            })

        self.generic_visit(node)

# ---------------- AI DOCSTRING ----------------
def generate_docstring_for_route(route):
    prompt = f"Generate a clear Python docstring for the Flask route function '{route['function_name']}'. Existing docstring: '{route['docstring']}'"
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "max_tokens":3000, "temperature":0},
            timeout=OLLAMA_TIMEOUT
        )
        r.raise_for_status()
        resp_text = r.text.strip()
        doc_parts = []
        for line in resp_text.splitlines():
            try:
                js = json.loads(line)
                if 'response' in js:
                    doc_parts.append(js['response'])
            except json.JSONDecodeError:
                continue
        doc = "\n".join(doc_parts).strip()
        if not doc:
            doc = route['docstring'] or "AI docstring failed."
        del r, resp_text, doc_parts
        gc.collect()
        return doc
    except Exception as e:
        ic(f"Ollama error for {route['function_name']}: {e}")
        return route['docstring'] or "AI docstring failed."

# ---------------- MAIN ----------------
def analyze_flask_app(filepath, use_ai_docstrings=False, dry_run=False):
    if not os.path.isfile(filepath):
        ic(f"File not found: {filepath}")
        return []

    # Load existing routes
    if os.path.isfile(OLD_JSON_FILE):
        with open(OLD_JSON_FILE, 'r', encoding='utf-8') as f:
            existing_routes = json.load(f)
    else:
        existing_routes = []

    existing_keys = {(r['function_name'], tuple(r['route_paths'])) for r in existing_routes}

    # AST parse
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filepath)
    visitor = FlaskRouteVisitor()
    visitor.visit(tree)
    new_routes = visitor.routes

    # Filter new routes
    filtered_routes = [r for r in new_routes if (r['function_name'], tuple(r['route_paths'])) not in existing_keys]
    ic(f"New routes found: {len(filtered_routes)}")

    if dry_run:
        ic("Dry-run mode: nothing will be saved.")
        for r in filtered_routes:
            ic(r['function_name'], "->", r['route_paths'])
        return filtered_routes

    # AI docstrings
    if use_ai_docstrings and filtered_routes:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_route = {executor.submit(generate_docstring_for_route, r): r for r in filtered_routes}
            for future in concurrent.futures.as_completed(future_to_route):
                r = future_to_route[future]
                try:
                    r['docstring'] = future.result()
                except Exception:
                    r['docstring'] = r['docstring'] or "AI docstring failed."
        gc.collect()

    # Merge
    merged_routes = existing_routes + filtered_routes

    # Save JSON
    with open(SAFE_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged_routes, f, indent=4)
    ic(f"Saved merged JSON to {SAFE_JSON_FILE}")

    # Save to SQLite
    conn = init_db(SAFE_DB_FILE)
    c = conn.cursor()
    for route in merged_routes:
        for path in route['route_paths']:
            c.execute('''
                INSERT OR IGNORE INTO routes (route, function_name, docstring, template_file)
                VALUES (?, ?, ?, ?)
            ''', (path, route['function_name'], route['docstring'], route['template_file']))
    conn.commit()
    conn.close()
    gc.collect()
    ic("SQLite DB saved to", SAFE_DB_FILE)

    return merged_routes

# ---------------- CLI ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Safe Flask Route Analyzer with Dry-Run Mode")
    parser.add_argument("filepath", help="Path to Flask Python file")
    parser.add_argument("--ai-docstrings", action="store_true", help="Generate AI docstrings for new routes")
    parser.add_argument("--dry-run", action="store_true", help="Show new routes without saving")
    args = parser.parse_args()

    analyze_flask_app(args.filepath, use_ai_docstrings=args.ai_docstrings, dry_run=args.dry_run)
