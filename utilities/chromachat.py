#!/usr/bin/env python3
"""
MediaStudio Semantic Chat
- Queries your existing ChromaDB vector collection
- Prints semantic matches
- Calls Ollama for enhanced answer
"""

import chromadb
from chromadb.utils import embedding_functions
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

# -------------------------
# SETUP Chroma
# -------------------------
client = chromadb.PersistentClient(path=CHROMA_DIR)
try:
    collection = client.get_collection(name=COLLECTION_NAME)
    ic("Connected to ChromaDB (existing or created)", COLLECTION_NAME)
except Exception as e:
    ic("Error connecting to ChromaDB:", e)
    raise SystemExit

# Use default OpenAI embedding function if needed; here we assume vectors already exist
ef = embedding_functions.DefaultEmbeddingFunction()

# -------------------------
# Helper Functions
# -------------------------
def search_chroma(query, n_results=5):
    """
    Search the Chroma collection for semantic matches
    """
    ic("Searching ChromaDB for query:", query)
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
    except Exception as e:
        ic("Error during Chroma query:", e)
        return []

    # Collect documents and metadata
    docs = []
    for idx, doc_list in enumerate(results['documents']):
        for doc in doc_list:
            docs.append(doc)
    ic("Chroma DB results found:", len(docs))
    return docs

def query_ollama(user_question, db_matches_text):
    """
    Call Ollama safely and correctly handle streamed JSON responses.
    """
    structured_prompt = f"""
You are a helpful assistant for the MediaStudio application.

Here are relevant function summaries from the database:

{db_matches_text}

Question: {user_question}

Instructions:
- Give a clear, step-by-step answer
- Use only functions that exist in MediaStudio.py
- Include Python examples when helpful
- Do NOT invent imports or files

Answer:
"""

    ic("Calling Ollama with structured prompt...")

    data = {
        "model": OLLAMA_MODEL,
        "prompt": structured_prompt,
        "temperature": 0.2
    }

    try:
        resp = requests.post(OLLAMA_URL, json=data, timeout=600, stream=True)
        resp.raise_for_status()

        full_response = []

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue

            if "response" in chunk:
                full_response.append(chunk["response"])

            if chunk.get("done") is True:
                break

        final_text = "".join(full_response).strip()
        return final_text if final_text else None

    except requests.exceptions.Timeout:
        ic("Ollama timed out")
        return None
    except Exception as e:
        ic("Ollama error:", e)
        return None

# -------------------------
# Chat Loop
# -------------------------
def chat():
    print("\n=== MediaStudio Semantic Chat ===")
    print("Ask about routes, functions, imports, HTML, paths.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Query> ").strip()
        if question.lower() == "exit":
            break

        ic("User question:", question)

        # Step 1: ChromaDB semantic search
        docs = search_chroma(question)
        db_matches_text = ""
        if docs:
            print("\n--- Database Matches ---")
            doc_texts = []
            for i, d in enumerate(docs, 1):
                doc_content = d if isinstance(d, str) else str(d)
                doc_texts.append(doc_content.strip())
                print(f"{i}. {doc_content}\n")
            db_matches_text = "\n\n".join(doc_texts)

        # Step 2: Ollama enhanced answer
        answer = query_ollama(question, db_matches_text)
        if answer:
            print("\n--- Ollama Answer ---")
            print(answer)
        else:
            ic("No Ollama answer, database matches shown above.")

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    chat()
