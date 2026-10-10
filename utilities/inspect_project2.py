#!/usr/bin/env python3
import ast
import os
import datetime
import argparse
from icecream import ic
import textwrap

APP_FILE = "MediaStudio.py"
OUTPUT_FILE = "MediaStudio.txt"

def extract_routes_templates_docstrings(filename):
    with open(filename, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filename)

    routes = []
    templates = []

    for node in ast.walk(tree):
        # Flask route decorators
        if isinstance(node, ast.FunctionDef):
            route_paths = []
            template_file = None
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Attribute) and func.attr == "route":
                        if len(decorator.args) > 0 and isinstance(decorator.args[0], ast.Constant):
                            route_paths.append(decorator.args[0].value)

            # Check render_template() usage
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Call):
                    func_name = stmt.func.id if isinstance(stmt.func, ast.Name) else getattr(stmt.func, 'attr', '')
                    if func_name == "render_template" and stmt.args:
                        if isinstance(stmt.args[0], ast.Constant):
                            template_file = stmt.args[0].value

            if route_paths:
                routes.append({
                    "paths": route_paths,
                    "function": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "template": template_file
                })

        # render_template() calls (all templates)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "render_template":
                if len(node.args) > 0 and isinstance(node.args[0], ast.Constant):
                    templates.append(node.args[0].value)

    return routes, templates

def generate_report(routes, templates, show_templates=False):
    report_lines = []
    report_lines.append(f"=== 🧭 ROUTES FOUND ===")
    for r in routes:
        paths_str = ", ".join(r["paths"])
        report_lines.append(f"  {paths_str:<40} -> {r['function']}")
        if r["docstring"]:
            wrapped = textwrap.fill(r["docstring"], width=80, initial_indent="    ", subsequent_indent="    ")
            report_lines.append(f"    Docstring:\n{wrapped}")
        if show_templates and r["template"]:
            report_lines.append(f"    Template used: {r['template']}")

    report_lines.append("\n=== 🧩 HTML Templates Used ===")
    for tpl in templates:
        report_lines.append(f"  {tpl}")

    report_lines.append("\n=== 📁 Template Files Present ===")
    if os.path.exists("templates"):
        for file in sorted(os.listdir("templates")):
            if file.endswith(".html"):
                report_lines.append(f"  {file}")
    else:
        report_lines.append("  No 'templates' directory found!")

    return "\n".join(report_lines)

def main():
    parser = argparse.ArgumentParser(description="Inspect Flask app routes and generate a readable report")
    parser.add_argument("--show-templates", action="store_true", help="Show HTML template filenames used by each route")
    args = parser.parse_args()

    if not os.path.exists(APP_FILE):
        ic(f"Error: {APP_FILE} not found in current directory.")
        return

    ic(f"Inspecting {APP_FILE} ...")

    routes, templates = extract_routes_templates_docstrings(APP_FILE)
    report = generate_report(routes, templates, show_templates=args.show_templates)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"📋 Flask Project Inspection Report\nGenerated: {timestamp}\n{'='*50}\n\n"

    full_report = header + report + "\n\n✅ Inspection complete.\n"

    print(full_report)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_report)

    ic(f"Report saved as {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
