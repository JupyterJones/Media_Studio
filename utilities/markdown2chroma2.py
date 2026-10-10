#!/usr/bin/env python3
"""
markdown2chromadb.py

Incrementally ingest a large Markdown file into ChromaDB.
SAFE for power loss, SAFE for long runs.
"""

import os
import uuid
import hashlib
from icecream import ic
import chromadb

# -------------------------
# CONFIG
# -------------------------
MARKDOWN_FILE = "MediaStudio_docstrings_complete.md"

CHROMA_DIR = "chroma_databases/studio_final"
COLLECTION_NAME = "mediastudio_markdown"

# -------------------------
# ENSURE DIRECTORY EXISTS
# -------------------------
os.makedirs(CHROMA_DIR, exist_ok=True)
ic("Chroma directory ensured:", CHROMA_DIR)

# -------------------------
# CHROMADB (PERSISTENT)
# -------------------------
client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)

ic("Connected to persistent ChromaDB")
ic("Current collection count:", collection.count())

# -------------------------
# HELPERS
# -------------------------
def stable_id(text: str) -> str:
    """Deterministic ID so reruns do not duplicate"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# -------------------------
# PARSE MARKDOWN
# -------------------------
def ingest_markdown():
    ic("Loading Markdown:", MARKDOWN_FILE)

    with open(MARKDOWN_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sections = []
    current_title = None
    current_buffer = []

    for line in lines:
        if line.startswith("## "):
            if current_title and current_buffer:
                sections.append((current_title, "".join(current_buffer)))
            current_title = line.strip()[3:]
            current_buffer = []
        else:
            current_buffer.append(line)

    if current_title and current_buffer:
        sections.append((current_title, "".join(current_buffer)))

    ic("Total sections found:", len(sections))

    stored = 0

    for title, content in sections:
        content = content.strip()
        if not content:
            continue

        section_id = stable_id(title + content)

        collection.add(
            ids=[section_id],
            documents=[content],
            metadatas=[{
                "title": title,
                "source": MARKDOWN_FILE,
                "type": (
                    "html" if title.lower().startswith("template file")
                    else "route" if title.lower().startswith("route")
                    else "function" if title.lower().startswith("function")
                    else "class" if title.lower().startswith("class")
                    else "app_declarations" if "app declarations" in title.lower()
                    else "imports" if "imports" in title.lower()
                    else "general"
                )
            }]
        )

        stored += 1
        if stored % 25 == 0:
            ic("Stored sections:", stored, "| Chroma count:", collection.count())

    ic("Markdown processing complete")
    ic("Final Chroma count:", collection.count())

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    ingest_markdown()
    ic("DONE — Markdown fully indexed into ChromaDB (PERSISTENT)")
