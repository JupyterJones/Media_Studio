#!/usr/bin/env python3
"""
Chat with MediaStudio ChromaDB (safe)
- Queries your existing database without altering it
- Falls back to Ollama only if Chroma has no matches
"""

import chromadb
import requests
import json
from icecream import ic

# -------------------------
# CONFIG
# -------------------------
CHROMA_DIR = "chroma_databases/studio_final/"
COLLECTION_NAME = "mediastudio_markdown"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
TIMEOUT_SECONDS = 600

TOP_K = 6

# -------------------------
# INIT CHROMA
# -------------------------
client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    )
)

# Safe get or create: does NOT overwrite your database
try:
    collection = client.get_collection(name=COLLECTION_NAME)
    ic("Connected to ChromaDB (existing or created)", COLLECTION_NAME)
except chromadb.errors.NotFoundError:
    ic("Collection not found, creating empty collection (won't erase database)")
    collection = client.create_collection(name=COLLECTION_NAME)
    ic("Created empty collection:", COLLECTION_NAME)

# -------------------------
# OLLAMA CALL
# -------------------------
def call_ollama(prompt: str) -> str:
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
# BUILD PROMPT
# -------------------------
def build_prompt(question, docs):
    context = "\n\n".join(docs) if docs else "No relevant code found."
    return f"""
You are an expert Python developer assistant.

Use the following application context to answer the question.
If the context is insufficient, answer using your own knowledge.

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
    print("\n=== MediaStudio Chroma Chat ===")
    print("Ask about routes, functions, imports, HTML, paths.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Query> ").strip()
        if question.lower() in ("exit", "quit"):
            break

        ic("User question:", question)

        # -------------------------
        # QUERY CHROMA
        # -------------------------
        docs = []
        try:
            results = collection.query(
                query_texts=[question],
                n_results=TOP_K,
                include=["documents", "metadatas"]
            )
            if results and results.get("documents"):
                for d in results["documents"][0]:
                    if d:
                        docs.append(d)
            ic("Chroma results found:", len(docs))
        except Exception as e:
            ic("Chroma query failed:", e)

        # -------------------------
        # FALLBACK TO OLLAMA
        # -------------------------
        if not docs:
            ic("No Chroma matches, calling Ollama...")
            prompt = build_prompt(question, docs)
            answer = call_ollama(prompt)
        else:
            answer = build_prompt(question, docs)

        print("\n--- Answer ---")
        print(answer)
        print("\n")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    chat()
