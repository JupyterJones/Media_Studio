#!/usr/bin/env python3
"""
PRO++ Ollama Docstring Generator (Fixed JSON Handling)
- Handles weak/missing docstrings intelligently
- Writes to Markdown incrementally
- Stores all docstrings in ChromaDB
- Robust against Ollama multi-JSON responses
"""

import ast
import os
import sys
import json
import uuid
import requests
import chromadb
from icecream import ic

# -------------------------
# CONFIG
# -------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
TIMEOUT_SECONDS = 600  # NEVER LESS
CHROMA_DIR = "./chromadb"
COLLECTION_NAME = "docstrings_ollama"
WEAK_DOC_THRESHOLD = 40  # characters

# -------------------------
# ChromaDB init
# -------------------------
chroma_client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    )
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)
ic("ChromaDB initialized", COLLECTION_NAME)

# -------------------------
# PROMPTS
# -------------------------
def module_prompt(filename):
    return f"""
Generate a Python module docstring.
STRICT RULES:
- Output ONLY the docstring text, NO quotes
- NO explanations or markdown
Filename: {filename}
Docstring:
"""

def class_prompt(name):
    return f"""
Generate a Python class docstring.
STRICT RULES:
- Output ONLY the docstring text, NO quotes
- NO explanations or markdown
Class name: {name}
Docstring:
"""

def function_prompt(name, args, scope):
    args_text = ", ".join(args) if args else "none"
    return f"""
Generate a Python function docstring.
STRICT RULES:
- Output ONLY the docstring text, NO quotes
- NO explanations or markdown
Context: {scope}
Function name: {name}
Arguments: {args_text}
Docstring:
"""

# -------------------------
# Helper functions
# -------------------------
def clean_text(text):
    banned = ("```", '"""', "Here is", "Below is", "Example")
    for b in banned:
        text = text.replace(b, "")
    return text.strip()

def is_weak(doc):
    if not doc:
        return True
    doc_lower = doc.lower()
    if len(doc.strip()) < WEAK_DOC_THRESHOLD:
        return True
    if any(k in doc_lower for k in ("todo", "...", "pass", "temporary")):
        return True
    return False

def call_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt
    }
    ic("Calling Ollama")
    resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()

    # --- Robust JSON handling ---
    docstring_text = ""
    for line in resp.text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if "response" in data:
                docstring_text += data["response"]
        except json.JSONDecodeError:
            # Skip any non-JSON lines
            continue

    return clean_text(docstring_text)

def generate_and_store(md, title, prompt, meta, existing_doc=None):
    if existing_doc and not is_weak(existing_doc):
        # Strong docstring, keep as-is
        docstring_text = clean_text(existing_doc)
        md.write(f"\n## {title}\n\n\"\"\"\n{docstring_text}\n\"\"\"\n")
        md.flush()
        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[docstring_text],
            metadatas=[meta]
        )
        ic("Existing strong docstring stored", meta)
        return

    # Missing or weak → generate
    docstring_text = call_ollama(prompt)
    md.write(f"\n## {title}\n\n\"\"\"\n{docstring_text}\n\"\"\"\n")
    md.flush()
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[docstring_text],
        metadatas=[meta]
    )
    ic("Generated docstring stored in ChromaDB", meta)

# -------------------------
# Process Python file
# -------------------------
def process_file(py_file, output_md):
    ic("Analyzing file", py_file)
    with open(py_file, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)

    mode = "a" if os.path.exists(output_md) else "w"
    with open(output_md, mode, encoding="utf-8") as md:
        if mode == "w":
            md.write(f"# Generated Docstrings for `{py_file}`\n")

        # Module
        module_doc = ast.get_docstring(tree)
        generate_and_store(
            md,
            "Module Docstring",
            module_prompt(os.path.basename(py_file)),
            {"symbol": "module", "symbol_type": "module", "source_file": py_file},
            existing_doc=module_doc
        )

        # Classes & Methods
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_doc = ast.get_docstring(node)
                generate_and_store(
                    md,
                    f"Class `{node.name}`",
                    class_prompt(node.name),
                    {"symbol": node.name, "symbol_type": "class", "source_file": py_file},
                    existing_doc=class_doc
                )

                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef):
                        method_doc = ast.get_docstring(sub)
                        args = [a.arg for a in sub.args.args if a.arg not in ("self", "cls")]
                        generate_and_store(
                            md,
                            f"Method `{node.name}.{sub.name}`",
                            function_prompt(sub.name, args, f"method of class {node.name}"),
                            {"symbol": f"{node.name}.{sub.name}", "symbol_type": "method", "source_file": py_file},
                            existing_doc=method_doc
                        )

            elif isinstance(node, ast.FunctionDef):
                func_doc = ast.get_docstring(node)
                args = [a.arg for a in node.args.args]
                generate_and_store(
                    md,
                    f"Function `{node.name}`",
                    function_prompt(node.name, args, "top-level function"),
                    {"symbol": node.name, "symbol_type": "function", "source_file": py_file},
                    existing_doc=func_doc
                )

# -------------------------
# Main entry
# -------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python ollama_generate_docstring2.py <file.py> [-o output.md]")
        sys.exit(1)

    py_file = sys.argv[1]
    if "-o" in sys.argv:
        output_md = sys.argv[sys.argv.index("-o") + 1]
    else:
        output_md = os.path.splitext(py_file)[0] + ".md"

    if not os.path.exists(py_file):
        print("ERROR: File not found:", py_file)
        sys.exit(1)

    process_file(py_file, output_md)
    ic("DONE — Docstrings generated AND stored in ChromaDB")

if __name__ == "__main__":
    main()
