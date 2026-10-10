#!/usr/bin/env python3
"""
app_analyzer.py

Analyze a Flask application, extract all @app.route endpoints,
generate AI docstrings for each route using Ollama asynchronously,
and save the results in SQLite and JSON for future reference.
"""

import ast
import os
import sqlite3
import json
import argparse
import requests
from icecream import ic
import concurrent.futures

# ---------------- CONFIG ----------------
DATABASE_FILE = "flask_routes.db"
JSON_EXPORT_FILE = "flask_routes.json"
OLLAMA_MODEL = "codellama:13b"  # or "llama3", "mistral", etc.
OLLAMA_TIMEOUT = 600            # Increased for larger models/functions
MAX_WORKERS = 1                 # Concurrent Ollama requests

# ---------------- DATABASE SETUP ----------------
def init_db():
    """
    Initialize SQLite database: drop previous routes table and create fresh.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    ic("Dropping old routes table (if exists)...")
    c.execute('DROP TABLE IF EXISTS routes')
    ic("Creating fresh routes table...")
    c.execute('''
        CREATE TABLE routes (
            id INTEGER PRIMARY KEY,
            route TEXT,
            function_name TEXT,
            docstring TEXT,
            template_file TEXT
        )
    ''')
    conn.commit()
    return conn

# ---------------- AST ANALYSIS ----------------
class FlaskRouteVisitor(ast.NodeVisitor):
    """
    AST visitor that finds all @app.route or @blueprint.route decorated functions.
    Now extracts source code for AI context.
    """
    def __init__(self, source_code):
        self.routes = []
        self.source_code = source_code

    def visit_FunctionDef(self, node):
        route_paths = []
        template_file = None

        # Detect @route decorators
        for decorator in node.decorator_list:
            # Matches @app.route(...) or @blueprint.route(...)
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr.lower() == 'route':
                    if decorator.args:
                        value = decorator.args[0]
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            route_paths.append(value.value)

        # Detect template usage (render_template('index.html'))
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Call):
                func_name = ''
                if isinstance(stmt.func, ast.Name):
                    func_name = stmt.func.id
                elif isinstance(stmt.func, ast.Attribute):
                    func_name = stmt.func.attr
                
                if func_name in ('render_template', 'render_template_string'):
                    if stmt.args:
                        arg0 = stmt.args[0]
                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            template_file = arg0.value

        if route_paths:
            # Extract the raw source code of the function for the AI
            raw_source = ast.get_source_segment(self.source_code, node)
            
            route_info = {
                'function_name': node.name,
                'route_paths': route_paths,
                'template_file': template_file,
                'existing_docstring': ast.get_docstring(node) or "",
                'docstring': "", # Will be filled by AI
                'source_code': raw_source
            }
            self.routes.append(route_info)
            ic(f"📍 Discovered: {node.name} at {route_paths}")

        self.generic_visit(node)

# ---------------- AI DOCSTRING ----------------
def generate_docstring_for_route(route):
    """
    Send a request to Ollama to generate a docstring based on function source.
    Returns the raw 'response' field from the AI.
    """
    func_name = route['function_name']
    source = route['source_code']
    
    ic(f"🤖 Calling Ollama for: {func_name}")
    
    prompt = (
        f"Generate a professional Python docstring for the following Flask route function. "
        f"Describe what the route does, the parameters it might take, and what it returns.\n\n"
        f"SOURCE CODE:\n{source}\n\n"
        f"Return ONLY the docstring text."
    )

    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,  # Crucial: Get one JSON object instead of a stream
                "options": {
                    "temperature": 0.3
                }
            },
            timeout=OLLAMA_TIMEOUT
        )
        r.raise_for_status()
        
        # Get the full raw response text from the JSON object
        full_json = r.json()
        ai_text = full_json.get("response", "").strip()
        
        ic(f"✅ AI Response for {func_name} received ({len(ai_text)} chars)")
        return ai_text

    except Exception as e:
        ic(f"❌ Ollama error for {func_name}: {e}")
        return route['existing_docstring'] or "AI docstring generation failed."

# ---------------- MAIN ANALYSIS ----------------
def analyze_flask_app(filepath, use_ai_docstrings=False):
    if not os.path.isfile(filepath):
        ic(f"File not found: {filepath}")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        source_code = f.read()
        try:
            tree = ast.parse(source_code, filename=filepath)
        except SyntaxError as e:
            ic(f"Syntax error in {filepath}: {e}")
            return []

    # 1. Discover routes
    visitor = FlaskRouteVisitor(source_code)
    visitor.visit(tree)
    routes = visitor.routes

    # 2. Generate Docstrings Asynchronously
    if use_ai_docstrings and routes:
        ic(f"Generating docstrings for {len(routes)} routes using {OLLAMA_MODEL}...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Map futures to route objects
            future_to_route = {executor.submit(generate_docstring_for_route, r): r for r in routes}
            for future in concurrent.futures.as_completed(future_to_route):
                r = future_to_route[future]
                try:
                    r['docstring'] = future.result()
                except Exception as e:
                    ic(f"Thread error for {r['function_name']}: {e}")
                    r['docstring'] = "Error during processing."
    else:
        # Fallback if AI is off
        for r in routes:
            r['docstring'] = r['existing_docstring']

    # 3. Save to SQLite
    conn = init_db()
    c = conn.cursor()
    for route in routes:
        # One function might have multiple @app.route decorators
        for path in route['route_paths']:
            c.execute('''
                INSERT INTO routes (route, function_name, docstring, template_file)
                VALUES (?, ?, ?, ?)
            ''', (path, route['function_name'], route['docstring'], route['template_file']))
    
    conn.commit()
    conn.close()

    # 4. Save to JSON
    # Remove 'source_code' from export to keep JSON clean
    export_data = []
    for r in routes:
        clean_entry = {k: v for k, v in r.items() if k != 'source_code'}
        export_data.append(clean_entry)

    with open(JSON_EXPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=4)
    
    ic(f"Analysis complete. DB: {DATABASE_FILE}, JSON: {JSON_EXPORT_FILE}")
    return routes

# ---------------- CLI ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Flask app routes and generate docstrings using Ollama.")
    parser.add_argument("filepath", help="Path to Flask application Python file")
    parser.add_argument("--ai-docstrings", action="store_true", help="Use Ollama to generate docstrings")
    args = parser.parse_args()

    analyze_flask_app(args.filepath, use_ai_docstrings=args.ai_docstrings)