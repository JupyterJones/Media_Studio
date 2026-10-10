#!/usr/bin/env python3
import json
import textwrap

SAFE_JSON_FILE = "flask_routes_safe.json"

def clean_docstring(ds):
    """Remove weird line breaks and excessive spaces."""
    if not ds:
        return "(No docstring)"
    # Remove backticks and newlines, then wrap text nicely
    cleaned = ds.replace("`", "").replace("\n", " ").replace("  ", " ").strip()
    return textwrap.fill(cleaned, width=80)

with open(SAFE_JSON_FILE, "r", encoding="utf-8") as f:
    routes = json.load(f)

print(f"Total routes in safe JSON: {len(routes)}\n")

# Preview first 5 routes
for r in routes:
    print(f"Function: {r['function_name']}")
    print(f"Route paths: {r['route_paths']}")
    print(f"Template: {r['template_file']}")
    print(f"Docstring:\n{clean_docstring(r['docstring'])}\n")
    print("-" * 80)
'''
#!/usr/bin/env python3
import json

SAFE_JSON_FILE = "flask_routes_safe.json"

with open(SAFE_JSON_FILE, "r", encoding="utf-8") as f:
    routes = json.load(f)

print(f"Total routes in safe JSON: {len(routes)}\n")

# Preview first 5 routes
for r in routes[:5]:
    print("Function:", r["function_name"])
    print("Route paths:", r["route_paths"])
    print("Template:", r["template_file"])
    print("Docstring preview:", r["docstring"][:300], "...\n")
'''