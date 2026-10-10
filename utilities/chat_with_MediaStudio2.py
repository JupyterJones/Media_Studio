import requests
import json
from icecream import ic
from chromadb.utils import embedding_functions
import chromadb

# --- Config ---
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
TIMEOUT_SECONDS = 600

COLLECTION_NAME = "docstrings_ollama"

# --- Connect to ChromaDB ---
client = chromadb.Client()
collection = client.get_collection(COLLECTION_NAME)
ic("Connected to ChromaDB", COLLECTION_NAME)

# --- Helper to query Ollama ---
def query_ollama(prompt: str) -> str:
    ic("Querying Ollama...", prompt)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": 512
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        text = data.get("completion") or data.get("response") or ""
        ic("Ollama response:", text)
        return text
    except Exception as e:
        ic("Ollama query failed:", e)
        return f"Error contacting Ollama: {e}"

# --- Helper to query ChromaDB ---
def query_chroma(keyword: str) -> str:
    try:
        results = collection.query(query_texts=[keyword], n_results=1)
        if results and results['documents'][0]:
            doc = results['documents'][0][0]
            ic("Found in ChromaDB:", doc)
            return doc
        else:
            ic("No results found in ChromaDB for:", keyword)
            return ""
    except Exception as e:
        ic("ChromaDB query failed:", e)
        return ""

# --- Main chat loop ---
print("=== ChromaDB + Ollama Chat ===")
print("Type a function, class, keyword, or any question.")
print("Type 'exit' to quit.")

while True:
    query = input("\nQuery> ").strip()
    if query.lower() == "exit":
        break

    # First check ChromaDB
    answer = query_chroma(query)

    # If nothing found, fallback to Ollama
    if not answer:
        answer = query_ollama(query)

    print("\nAnswer:\n", answer)
