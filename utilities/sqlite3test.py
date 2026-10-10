#!/usr/bin/env python3
"""
MediaStudio SQLite Chat
- Uses your existing SQLite DB (chroma.sqlite3)
- Searches Markdown/code entries for queries
- Always prints DB results immediately
- Calls Ollama for enhanced answers
"""

import sqlite3
import requests
import json
from icecream import ic

# -------------------------
# CONFIG
# -------------------------
DB_FILE = "chroma_databases/studio_final/chroma.sqlite3"  # correct path to your DB
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
TIMEOUT_SECONDS = 900
TOP_K = 6  # number of DB results to use in Ollama prompt

# -------------------------
# INIT SQLITE CONNECTION
# -------------------------
conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
c = conn.cursor()
ic(f"Connected to SQLite DB: {DB_FILE}")

# -------------------------
# SEARCH FUNCTION
# -------------------------
def search_db(query: str):
    """
    Searches embedding_fulltext_search_content for query using LIKE.
    Returns a list of content strings.
    """
    sql = """
    SELECT c0
    FROM embedding_fulltext_search_content
    WHERE c0 LIKE ?
    LIMIT ?
    """
    c.execute(sql, (f"%{query}%", TOP_K))
    results = [row["c0"] for row in c.fetchall()]
    return results

# -------------------------
# OLLAMA CALL
# -------------------------
def call_ollama(prompt: str) -> str:
    """
    Calls Ollama API to get enhanced answer.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": 2048,
        "temperature": 0.2
    }

    ic("Calling Ollama...")
    resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()

    text = ""
    for line in resp.text.splitlines():
        try:
            data = json.loads(line)
            text += data.get("response", "")
        except Exception:
            continue

    return text.strip()

# -------------------------
# PROMPT BUILDER
# -------------------------
def build_prompt(question, docs):
    """
    Builds prompt for Ollama using question and DB context.
    """
    context = "\n\n".join(docs) if docs else "No relevant code found."
    return f"""
You are an expert Python developer assistant.

Use the following application context to answer the question.
If the context is insufficient, answer using your own knowledge,
but prefer the application's structure when possible.

====================
APPLICATION CONTEXT
====================
{context}

====================
QUESTION
====================
{question}

====================
ANSWER
====================
"""

# -------------------------
# CHAT LOOP
# -------------------------
def chat():
    print("\n=== MediaStudio SQLite Chat ===")
    print("Ask about routes, functions, imports, HTML, paths.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Query> ").strip()
        if question.lower() in ("exit", "quit"):
            break

        ic("User question:", question)

        # Search SQLite DB first
        docs = search_db(question)

        # Print DB results immediately
        if docs:
            ic("SQLite DB results found:", len(docs))
            print("\n--- Database Matches ---")
            for i, d in enumerate(docs, 1):
                snippet = d[:500].replace("\n", " ")
                print(f"{i}. {snippet}{'...' if len(d)>500 else ''}")
        else:
            ic("No SQLite DB matches found.")
            print("\n--- Database Matches ---")
            print("No matches found in SQLite DB.")

        # Call Ollama for enhanced info
        try:
            prompt = build_prompt(question, docs)
            answer = call_ollama(prompt)
            print("\n--- Ollama Answer ---")
            print(answer)
        except Exception as e:
            print("\n--- Ollama Error ---")
            print(e)
            print("\nUsing only DB results above.")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    chat()
