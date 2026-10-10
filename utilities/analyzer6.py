#!/usr/bin/env python3
"""
Single-file analyzer with Ollama integration
FIXED for large real-world Python codebases (10k+ lines)
"""

import ast
import hashlib
import json
import os
import sqlite3
import sys
import time
import inspect
from datetime import datetime
import requests
from icecream import ic

# -----------------------------
# CONFIG
# -----------------------------

ANALYZER_VERSION = "1.0.9"

PROGRESS_FILE = "analysis_progress5.json"
DB_FILE = "analysis_results6.sqlite3"
LOG_FILE_PATH = "analysis6.log"

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "codellama:13b"
OLLAMA_TIMEOUT = 1000

# -----------------------------
# LOGGING
# -----------------------------

def logit(*args):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        frame = inspect.stack()[1]
        fname = os.path.basename(frame.filename)
        lineno = frame.lineno
        msg = " ".join(str(a) for a in args)

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{ts} | {fname}:{lineno} | {msg}\n")
    except Exception as e:
        print("[LOG ERROR]", e, file=sys.stderr)

# -----------------------------
# UTILITIES
# -----------------------------

def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

def atomic_write_json(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def now_ts():
    return time.time()

# -----------------------------
# PROGRESS TRACKER (FIXED)
# -----------------------------

class ProgressTracker:
    def __init__(self, path):
        self.path = path
        self.data = self._load()

    def _default(self):
        return {
            "analyzer_version": ANALYZER_VERSION,
            "current_file": None,
            "phase": "init",
            "started_at": now_ts(),
            "last_update": None,
            "indexed_units": [],
            "analyzed_units": [],
            "failed_units": {}
        }

    def _load(self):
        if not os.path.exists(self.path):
            return self._default()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self._default()

    def mark_indexed(self, unit_id):
        if unit_id not in self.data["indexed_units"]:
            self.data["indexed_units"].append(unit_id)
        self._commit()

    def mark_analyzed(self, unit_id):
        if unit_id not in self.data["analyzed_units"]:
            self.data["analyzed_units"].append(unit_id)
        self._commit()

    def mark_failed(self, unit_id, error):
        self.data["failed_units"][unit_id] = {
            "error": str(error),
            "time": now_ts()
        }
        self._commit()

    def update_phase(self, phase, current_file=None):
        self.data["phase"] = phase
        if current_file:
            self.data["current_file"] = current_file
        self._commit()

    def _commit(self):
        self.data["last_update"] = now_ts()
        atomic_write_json(self.path, self.data)
        ic("PROGRESS", {
            "phase": self.data["phase"],
            "indexed": len(self.data["indexed_units"]),
            "analyzed": len(self.data["analyzed_units"]),
            "failed": len(self.data["failed_units"])
        })

# -----------------------------
# DATABASE
# -----------------------------

class AnalysisDB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS units (
            unit_id TEXT PRIMARY KEY,
            file_path TEXT,
            unit_type TEXT,
            name TEXT,
            lineno INTEGER,
            end_lineno INTEGER,
            file_hash TEXT,
            status TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis (
            unit_id TEXT PRIMARY KEY,
            summary TEXT,
            raw_output TEXT,
            status TEXT
        )
        """)

        self.conn.commit()

    def insert_unit(self, u):
        self.conn.execute("""
        INSERT OR IGNORE INTO units VALUES (?,?,?,?,?,?,?,?)
        """, (
            u["unit_id"], u["file_path"], u["unit_type"],
            u["name"], u["lineno"], u["end_lineno"],
            u["file_hash"], "indexed"
        ))
        self.conn.commit()

    def mark_analyzed(self, uid, summary, raw):
        self.conn.execute("""
        INSERT OR REPLACE INTO analysis VALUES (?,?,?,?)
        """, (uid, summary, raw, "ok"))
        self.conn.execute(
            "UPDATE units SET status='analyzed' WHERE unit_id=?",
            (uid,)
        )
        self.conn.commit()

# -----------------------------
# AST INDEXING
# -----------------------------

class UnitIndexer(ast.NodeVisitor):
    def __init__(self, file_path, file_hash):
        self.file_path = file_path
        self.file_hash = file_hash
        self.units = []

    def _add(self, node, typ, name):
        src = f"{self.file_path}:{typ}:{name}:{node.lineno}:{node.end_lineno}"
        self.units.append({
            "unit_id": stable_hash(src),
            "file_path": self.file_path,
            "unit_type": typ,
            "name": name,
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
            "file_hash": self.file_hash,
        })

    def visit_FunctionDef(self, node):
        self._add(node, "function", node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._add(node, "async_function", node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._add(node, "class", node.name)
        self.generic_visit(node)

# -----------------------------
# OLLAMA
# -----------------------------

def call_ollama(prompt: str) -> str:
    ic("PROMPT →", prompt[:400])

    r = requests.post(
        OLLAMA_ENDPOINT,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=OLLAMA_TIMEOUT,
    )
    r.raise_for_status()

    result = r.json().get("response", "").strip()
    ic("RESPONSE ←", result[:400])
    return result

# -----------------------------
# ANALYZER
# -----------------------------

class Analyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.progress = ProgressTracker(PROGRESS_FILE)
        self.db = AnalysisDB(DB_FILE)

        self.progress.update_phase("started", self.file_path)

    def run(self):
        with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        file_hash = stable_hash(text)
        tree = ast.parse(text)
        lines = text.splitlines()

        indexer = UnitIndexer(self.file_path, file_hash)
        indexer.visit(tree)

        for u in indexer.units:
            uid = u["unit_id"]
            try:
                self.progress.mark_indexed(uid)
                self.db.insert_unit(u)

                snippet = "\n".join(lines[u["lineno"] - 1: u["end_lineno"]])

                prompt = f"""
You are a senior Python static analyzer.

Return VALID JSON ONLY.

Required keys:
- function_name
- routes
- template_file
- docstring
- required_functions

RULES:
- If docstring is missing, GENERATE ONE.
- docstring must NEVER be empty.

CODE:
{snippet}
""".strip()

                raw = call_ollama(prompt)
                summary = raw[:300]

                self.db.mark_analyzed(uid, summary, raw)
                self.progress.mark_analyzed(uid)

                logit("Analyzed", u["unit_type"], u["name"])

            except Exception as e:
                self.progress.mark_failed(uid, e)
                logit("FAILED", u["name"], e)

        self.progress.update_phase("complete")

# -----------------------------
# ENTRY
# -----------------------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: analyzer5.py <file.py>")
        sys.exit(1)

    Analyzer(os.path.abspath(sys.argv[1])).run()
