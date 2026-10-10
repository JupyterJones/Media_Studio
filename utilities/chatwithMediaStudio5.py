#!/usr/bin/env python3
"""
chatwithMediaStudio5.py
Chat with MediaStudio ChromaDB safely
- Retrieves relevant code, routes, HTML, paths
- Enhances answers using Ollama
- Ensures embeddings exist without altering your database
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

TOP_K = 6  # number of Chroma documents to retrieve per query

# -------------------------
# INIT CHROMA
# -------------------------
client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    )
)

# Use get_or_create_collection to avoid NotFoundError
collection = client.get_or_create_collection(name=COLLECTION_NAME)
ic("Connected to ChromaDB (existing or created)", COLLECTION_NAME)

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
# ENSURE EMBEDDINGS (no persist call)
# -------------------------
def ensure_embeddings():
    ic("Ensuring documents exist in the collection...")
    results = collection.get(include=["documents", "metadatas", "embeddings"])
    if not results["documents"]:
        ic("No documents found in collection!")
    else:
        ic(f"{len(results['documents'][0])} documents loaded in collection.")
    return results

# -------------------------
# BUILD FINAL PROMPT
# -------------------------
def build_prompt(question, docs):
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
    print("\n=== MediaStudio Chroma Chat ===")
    print("Ask about routes, functions, imports, HTML, paths.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Query> ").strip()
        if question.lower() in ("exit", "quit"):
            break

        ic("User question:", question)

        # Query Chroma
        results = collection.query(
            query_texts=[question],
            n_results=TOP_K,
            include=["documents", "metadatas", "embeddings"]
        )

        docs = []
        if results and results.get("documents"):
            for d in results["documents"][0]:
                if d:
                    docs.append(d)

        ic("Chroma results found:", len(docs))

        # Build prompt
        prompt = build_prompt(question, docs)

        # Ask Ollama only if Chroma returned nothing
        if not docs:
            ic("No Chroma matches, calling Ollama...")
            answer = call_ollama(prompt)
        else:
            ic("Using Chroma context, calling Ollama for refinement...")
            answer = call_ollama(prompt)

        print("\n--- Answer ---")
        print(answer)
        print("\n")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    ensure_embeddings()
    chat()
