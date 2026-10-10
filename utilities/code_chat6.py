#!/home/jack/miniconda3/envs/PY39/bin/python

import os
import sys
import argparse
import datetime
import hashlib
import json
import aiohttp
import asyncio
from icecream import ic
from sentence_transformers import SentenceTransformer
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ==============================
# --- Configuration ---
# ==============================
ic.disable()  # Disable icecream during normal chat

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
GENERATION_MODEL_NAME = "deepseek-coder:1.3b"
DOCKER_GENERATE_URL = "http://localhost:11434/api/generate"
CHROMA_COLLECTION_DIR = "chroma_databases"
HASH_TRACK_FILE = "chroma_hashes.json"
HISTORY_FILE = "history.txt"

# Load sentence-transformers
ic("Loading sentence-transformers model for embeddings...")
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

RAG_PROMPT_TEMPLATE = """
You are a senior software developer and expert Python coding assistant. Answer concisely and clearly.
If possible, provide corrected or improved code snippets. Include line numbers if possible.
Provide verbose explanation of fixes and processes.

CONTEXT:
---
{context}
---

QUESTION:
{question}

ANSWER:
"""

README_PROMPT_TEMPLATE = """
You are a senior Python developer. Using the following code context, generate a detailed README.md for the file.
Include: file description, functions/classes overview, usage example, and any notes for developers.

CONTEXT:
---
{context}
---

GENERATE README.md:
"""

# ==============================
# --- Helper Functions ---
# ==============================

def load_hashes():
    if os.path.exists(HASH_TRACK_FILE):
        with open(HASH_TRACK_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_hashes(hashes):
    with open(HASH_TRACK_FILE, 'w') as f:
        json.dump(hashes, f, indent=2)

def compute_chunk_hash(chunk: str):
    return hashlib.sha256(chunk.encode("utf-8")).hexdigest()

def embed_text(text):
    return embedder.encode(text).tolist()

def append_history(entry: str):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + "\n" + "-"*60 + "\n")

# ==============================
# --- Async Functions ---
# ==============================

async def generate_codellama_answer(prompt: str) -> str:
    """Send prompt to Deepseek Docker API (async streaming) and return full text."""
    payload = {
        "model": GENERATION_MODEL_NAME,
        "prompt": prompt,
        "max_tokens": 1024,
        "temperature": 0.2,
        "stream": True
    }
    answer_parts = []

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(DOCKER_GENERATE_URL, json=payload, timeout=900) as resp:
                async for chunk_bytes in resp.content.iter_chunked(1024):
                    line = chunk_bytes.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    for part in line.splitlines():
                        try:
                            data = json.loads(part)
                            if "response" in data:
                                answer_parts.append(data["response"])
                                # Stream print
                                print(data["response"], end='', flush=True)
                        except json.JSONDecodeError:
                            continue
                        if data.get("done", False):
                            return "".join(answer_parts)
        except asyncio.TimeoutError:
            print("⚠️  Streaming timed out. Returning partial response.")
    return "".join(answer_parts)

# ==============================
# --- Core Functions ---
# ==============================

def create_code_database(file_path: str) -> chromadb.Collection:
    os.makedirs(CHROMA_COLLECTION_DIR, exist_ok=True)
    filename = os.path.splitext(os.path.basename(file_path))[0]
    chroma_client = chromadb.PersistentClient(path=os.path.join(CHROMA_COLLECTION_DIR, filename))
    collection = chroma_client.get_or_create_collection(name=filename)

    hashes = load_hashes()
    file_hashes = hashes.get(filename, [])

    print(f"-> Creating/updating database for: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        code_content = f.read()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(code_content)
    ic(f"Total code chunks: {len(chunks)}")

    new_hashes = []
    for chunk in chunks:
        chunk_hash = compute_chunk_hash(chunk)
        if chunk_hash in file_hashes:
            continue
        emb = embed_text(chunk)
        collection.add(
            embeddings=[emb],
            documents=[chunk],
            ids=[chunk_hash]
        )
        new_hashes.append(chunk_hash)

    hashes[filename] = list(set(file_hashes + new_hashes))
    save_hashes(hashes)

    print("-> Code database created/updated successfully.")
    return collection

async def chat_with_code(collection: chromadb.Collection):
    print("\n--- Code Chat Initialized ---")
    print("Ask questions about your code. Type 'quit' or 'exit' to end.")
    print("-" * 40)

    while True:
        user_question = input("You: ")
        if user_question.lower() in ['quit', 'exit']:
            print("Goodbye!")
            break

        question_embedding = embed_text(user_question)
        results = collection.query(query_embeddings=[question_embedding], n_results=5)
        retrieved_chunks = results['documents'][0]
        retrieved_context = "\n---\n".join(retrieved_chunks)

        if "readme" in user_question.lower():
            final_prompt = README_PROMPT_TEMPLATE.format(
                context=retrieved_context
            )
        else:
            final_prompt = RAG_PROMPT_TEMPLATE.format(
                context=retrieved_context,
                question=user_question
            )

        print("\nDeepseek:\n")
        answer = await generate_codellama_answer(final_prompt)
        print("\n")  # Newline after streaming

        timestamp = datetime.datetime.now().isoformat()
        history_entry = f"[{timestamp}] User: {user_question}\n[{timestamp}] Deepseek: {answer}"
        append_history(history_entry)

# ==============================
# --- Main ---
# ==============================

async def main():
    parser = argparse.ArgumentParser(
        description="Offline RAG code chat with Deepseek-Coder and sentence-transformers."
    )
    parser.add_argument("file_path", help="Path to the Python file to chat about")
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        sys.exit(1)

    collection = create_code_database(args.file_path)
    await chat_with_code(collection)

if __name__ == "__main__":
    asyncio.run(main())
