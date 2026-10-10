#!/usr/bin/env python3
"""
chat_codebase.py - Codebase RAG Assistant for Media Studio
Powered by ChromaDB, Ollama (nomic-embed-text / local models), Gemini 2.5 Flash,
and direct integration with REMEMBER knowledge database.
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
import argparse
import chromadb
import ollama
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_media_studio")
META_FILE = os.path.join(CHROMA_DIR, "file_hashes.json")

REMEMBER_DB = os.path.join(BASE_DIR, "static", "REMEMBER.db")
REMEMBER_TEXT_DIR = os.path.join(BASE_DIR, "static", "TEXT")

DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_CHAT_MODEL = "gemini-2.5-flash" if (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")) else "deepseek-coder:1.3b"

IGNORED_DIRS = {
    "venv", ".git", "models", "chroma_media_studio", "__pycache__",
    ".Trash-1000", "node_modules", "static/novel_images", "static/temp_exp",
    "static/images", "static/results", "static/convert_uploads",
    "static/convert_results", "static/project_files", "cache", "trash",
    "versions_NO-agy", "btemp", "temp", "tempp", "temp_marine",
    "temp_staacor", "temp_v3", "output_videos", "static/temp"
}

IGNORED_FILE_PATTERNS = [
    "all_html.html", "all_code.html", "MediaStudioSD2-bak.py", "MediaStudioSD2_.py",
    "app_log.txt", "hammer.js", "jquery", ".min.js", "list.txt", "mylist.txt",
    "Media_Studio_Full.txt", "transcript", "gravity_talk", "pipfreeze.txt",
    "REMEMBER_log.txt", "-bak", "_bak", ".bak", "copy"
]

INCLUDED_EXTS = {".py", ".html", ".js", ".css", ".sh", ".md", ".txt"}

def save_to_remember(question, answer, sources=None):
    """Saves a Q&A entry into REMEMBER.db (table post) and static/TEXT/ markdown file."""
    os.makedirs(REMEMBER_TEXT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(REMEMBER_DB), exist_ok=True)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    title = f"[Media Studio] {question[:60]}"

    formatted_content = f"# {question}\n\n"
    formatted_content += f"**Date:** {timestamp} | **Saved from:** Media Studio AI Assistant\n\n"
    if sources:
        formatted_content += "### 📚 Code References:\n"
        for s in sorted(set(sources)):
            formatted_content += f"- `{s}`\n"
        formatted_content += "\n---\n\n"
    formatted_content += f"### 💡 Answer:\n\n{answer}\n"

    post_id = None
    try:
        conn = sqlite3.connect(REMEMBER_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO post (title, content, image, video_filename, audio) VALUES (?, ?, NULL, NULL, NULL)",
            (title, formatted_content)
        )
        post_id = c.lastrowid
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Warning: Could not write to REMEMBER.db: {e}")

    # Also save as markdown file in static/TEXT/
    clean_slug = "".join(c for c in question if c.isalnum() or c in (" ", "_", "-")).strip()[:40].replace(" ", "_")
    fn = f"codechat_{post_id or int(time.time())}_{clean_slug}.md"
    file_path = os.path.join(REMEMBER_TEXT_DIR, fn)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)
    except Exception as e:
        print(f"[!] Warning: Could not write to {file_path}: {e}")

    return post_id, fn

def file_hash(filepath):
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def chunk_file(filepath, chunk_lines=80, overlap_lines=20):
    """Chunks text files preserving line numbers and context."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []

    if not lines:
        return []

    chunks = []
    total_lines = len(lines)
    rel_path = os.path.relpath(filepath, BASE_DIR)

    i = 0
    while i < total_lines:
        end = min(i + chunk_lines, total_lines)
        chunk_text = "".join(lines[i:end])
        chunks.append({
            "rel_path": rel_path,
            "start_line": i + 1,
            "end_line": end,
            "text": chunk_text
        })
        if end == total_lines:
            break
        i += (chunk_lines - overlap_lines)

    return chunks

def get_chroma_collection():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name="media_studio_codebase",
        metadata={"hnsw:space": "cosine"}
    )

def index_codebase(force=False, embed_model=DEFAULT_EMBED_MODEL):
    print("=" * 65)
    print(f"[*] Indexing Media Studio codebase into ChromaDB...")
    print(f"[*] Embedding Model: {embed_model}")
    print(f"[*] Database Path:   {CHROMA_DIR}")
    print("=" * 65)

    collection = get_chroma_collection()

    old_hashes = {}
    if os.path.exists(META_FILE) and not force:
        try:
            with open(META_FILE, "r") as f:
                old_hashes = json.load(f)
        except Exception:
            old_hashes = {}

    new_hashes = {}
    files_to_index = []

    for root, dirs, files in os.walk(BASE_DIR):
        rel_root = os.path.relpath(root, BASE_DIR)
        dirs[:] = [
            d for d in dirs
            if not any(ig in d.lower() for ig in ["venv", ".git", "models", "chroma", "cache", "trash", "node_modules"])
            and not any(ig in os.path.join(rel_root, d) for ig in IGNORED_DIRS)
        ]

        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext in INCLUDED_EXTS:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, BASE_DIR)

                if any(ig in rel_path.lower() for ig in ["venv", ".git", "models", "chroma", "cache", "trash", "node_modules"]):
                    continue
                if any(rel_path.startswith(ig) for ig in IGNORED_DIRS):
                    continue
                if any(rel_path.endswith(ig) or ig in rel_path for ig in IGNORED_FILE_PATTERNS):
                    continue
                if "transcript" in f.lower() or "full_jsonl" in f.lower() or "gravity_talk" in f.lower() or f.endswith(".log"):
                    continue
                if "-bak" in f.lower() or "_bak" in f.lower() or f.endswith(".bak"):
                    continue
                if os.path.getsize(full_path) > 1024 * 1024:
                    continue

                f_hash = file_hash(full_path)
                new_hashes[rel_path] = f_hash

                if force or old_hashes.get(rel_path) != f_hash:
                    files_to_index.append(full_path)

    # Clean up deleted files from collection
    deleted_files = set(old_hashes.keys()) - set(new_hashes.keys())
    for d_file in deleted_files:
        try:
            collection.delete(where={"file": d_file})
            print(f"[-] Removed deleted file from index: {d_file}")
        except Exception:
            pass

    if not files_to_index:
        print("[✓] Codebase index is completely up to date! (0 files changed)")
        return

    print(f"[*] Found {len(files_to_index)} updated/new file(s) to index...")

    total_chunks = 0
    start_time = time.time()

    for idx, fpath in enumerate(files_to_index, 1):
        rel_p = os.path.relpath(fpath, BASE_DIR)
        chunks = chunk_file(fpath)
        if not chunks:
            continue

        try:
            collection.delete(where={"file": rel_p})
        except Exception:
            pass

        def _embed_item(c):
            doc_id = f"{rel_p}#L{c['start_line']}-L{c['end_line']}"
            context_header = f"# File: {rel_p} (Lines {c['start_line']}-{c['end_line']})\n"
            full_text = context_header + c["text"]
            try:
                emb = ollama.embeddings(model=embed_model, prompt=full_text)["embedding"]
                return {
                    "id": doc_id,
                    "doc": full_text,
                    "meta": {
                        "file": rel_p,
                        "start_line": c["start_line"],
                        "end_line": c["end_line"]
                    },
                    "embedding": emb
                }
            except Exception as e:
                print(f"    [!] Error embedding chunk {doc_id}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(_embed_item, chunks))

        valid = [r for r in results if r is not None]
        if valid:
            collection.add(
                ids=[r["id"] for r in valid],
                documents=[r["doc"] for r in valid],
                metadatas=[r["meta"] for r in valid],
                embeddings=[r["embedding"] for r in valid]
            )
            total_chunks += len(valid)

        print(f"    [{idx}/{len(files_to_index)}] Indexed {rel_p} ({len(chunks)} chunks)", flush=True)

    with open(META_FILE, "w") as f:
        json.dump(new_hashes, f, indent=2)

    dur = time.time() - start_time
    print(f"\n[✓] Successfully indexed {total_chunks} chunks in {dur:.1f}s!")

def ask_codebase(question, chat_model=DEFAULT_CHAT_MODEL, embed_model=DEFAULT_EMBED_MODEL, top_k=4, stream_stdout=True):
    collection = get_chroma_collection()

    try:
        q_emb = ollama.embeddings(model=embed_model, prompt=question)["embedding"]
    except Exception as e:
        err = f"[!] Error generating embedding for question: {e}"
        if stream_stdout: print(err)
        return err, []

    results = collection.query(
        query_embeddings=[q_emb],
        n_results=top_k
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        msg = "[!] No relevant code chunks found in ChromaDB."
        if stream_stdout: print(msg)
        return msg, []

    context_parts = []
    sources = []
    for doc, meta in zip(docs, metas):
        context_parts.append(doc)
        sources.append(f"{meta['file']}:{meta['start_line']}-{meta['end_line']}")

    system_prompt = (
        "You are Esperanza, Jack's expert AI pair programmer with deep knowledge of the Media Studio application.\n"
        "You answer questions accurately, quoting exact code, functions, routes, line numbers, and architectural patterns.\n"
        "Ground your answers directly in the provided code snippets. Be concise, sharp, and helpful."
    )

    user_prompt = (
        f"Media Studio Codebase Context:\n"
        f"====================================================\n"
        f"{'\n'.join(context_parts)}\n"
        f"====================================================\n\n"
        f"Question: {question}"
    )

    if stream_stdout:
        print("\n" + "—" * 65)
        print(f"[*] Model: {chat_model} | Question: {question}")
        print("—" * 65 + "\n")

    full_reply = []
    try:
        if "gemini" in chat_model.lower():
            from google import genai
            g_client = genai.Client()
            model_id = "gemini-2.5-flash" if "gemini" in chat_model.lower() else chat_model
            response = g_client.models.generate_content_stream(
                model=model_id,
                contents=f"{system_prompt}\n\n{user_prompt}"
            )
            for chunk in response:
                content = chunk.text or ""
                if stream_stdout:
                    sys.stdout.write(content)
                    sys.stdout.flush()
                full_reply.append(content)
            if stream_stdout: print("\n")
        else:
            response_stream = ollama.chat(
                model=chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True
            )

            for chunk in response_stream:
                content = chunk.get("message", {}).get("content", "")
                if stream_stdout:
                    sys.stdout.write(content)
                    sys.stdout.flush()
                full_reply.append(content)
            if stream_stdout: print("\n")

        answer_text = "".join(full_reply).strip()

        if stream_stdout:
            print("—" * 65)
            print("[*] Sources cited:")
            for s in sorted(set(sources)):
                print(f"    • {s}")
            print("—" * 65 + "\n")
            print("💡 Tip: Type '/save' to store this answer in REMEMBER!\n")

        return answer_text, sources

    except Exception as e:
        err_msg = f"[!] Error during chat completion: {e}"
        if stream_stdout: print(f"\n{err_msg}")
        return err_msg, sources

def interactive_chat(chat_model=DEFAULT_CHAT_MODEL, embed_model=DEFAULT_EMBED_MODEL):
    print("\n" + "=" * 65)
    print("🤖 Media Studio Codebase Chat (ChromaDB + Ollama / Gemini)")
    print(f"   Current Model: {chat_model}")
    print("   Type your questions about Media Studio below.")
    print("   Commands:")
    print("     /save     - Save the last answer to REMEMBER knowledge base")
    print("     /gemini   - Switch to Gemini 2.5 Flash")
    print("     /ollama   - Switch to local DeepSeek-Coder")
    print("     /reindex  - Re-scan and re-index the codebase")
    print("     exit / q  - Quit the chat")
    print("=" * 65 + "\n")

    current_model = chat_model
    last_qa = None

    while True:
        try:
            prompt_label = f"[{current_model}] MediaStudio ❯ "
            q = input(prompt_label).strip()
            if not q:
                continue
            if q.lower() in {"exit", "quit", "q"}:
                print("[*] Goodbye, Jack!")
                break
            if q.lower() == "/reindex":
                index_codebase(force=True, embed_model=embed_model)
                continue
            if q.lower() == "/gemini":
                current_model = "gemini-2.5-flash"
                print("[*] Switched to Gemini 2.5 Flash!")
                continue
            if q.lower() == "/ollama":
                current_model = "deepseek-coder:1.3b"
                print("[*] Switched to local Ollama (deepseek-coder:1.3b)!")
                continue
            if q.lower() == "/save":
                if not last_qa:
                    print("[!] No previous answer to save yet. Ask a question first!")
                else:
                    l_q, l_a, l_s = last_qa
                    pid, fname = save_to_remember(l_q, l_a, l_s)
                    print(f"[✓] Saved to REMEMBER! Post #{pid} | File: static/TEXT/{fname}")
                continue

            ans, srcs = ask_codebase(q, chat_model=current_model, embed_model=embed_model)
            last_qa = (q, ans, srcs)
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting chat.")
            break

# ==========================================================
# Embedded Web Interface (Flask)
# ==========================================================

WEB_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Studio – Codebase AI Assistant</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {
            --bg: #0b0f19;
            --panel: #131b2e;
            --panel-border: #1e293b;
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --user-bubble: #1e293b;
            --ai-bubble: #0f172a;
            --code-bg: #030712;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: var(--panel);
            border-bottom: 1px solid var(--panel-border);
            padding: 14px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header-title {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--accent);
        }
        .header-actions {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        select, button {
            background: #1e293b;
            color: var(--text-main);
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        select:focus, button:hover {
            border-color: var(--accent);
        }
        .btn-remember {
            background: #0284c7;
            color: #fff;
            border: none;
            text-decoration: none;
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .btn-remember:hover { background: #0369a1; }
        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 1000px;
            width: 100%;
            margin: 0 auto;
        }
        .message-row {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .message-row.user { align-items: flex-end; }
        .message-row.ai { align-items: flex-start; }
        .bubble {
            max-width: 85%;
            padding: 16px 20px;
            border-radius: 14px;
            line-height: 1.6;
            font-size: 0.98rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }
        .user .bubble {
            background: var(--user-bubble);
            border: 1px solid #334155;
            border-bottom-right-radius: 4px;
        }
        .ai .bubble {
            background: var(--ai-bubble);
            border: 1px solid var(--panel-border);
            border-bottom-left-radius: 4px;
            width: 100%;
            max-width: 95%;
        }
        .bubble pre {
            background: var(--code-bg);
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 14px;
            overflow-x: auto;
            margin: 12px 0;
            font-family: 'Fira Code', monospace;
            font-size: 0.88rem;
        }
        .bubble code {
            background: rgba(255,255,255,0.08);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .sources-box {
            margin-top: 14px;
            padding-top: 10px;
            border-top: 1px solid #1e293b;
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        .sources-box span {
            display: inline-block;
            background: #1e293b;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 3px;
            font-family: monospace;
            color: #38bdf8;
        }
        .action-bar {
            margin-top: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .save-btn {
            background: #0f766e;
            color: #fff;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.82rem;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
        }
        .save-btn:hover { background: #115e59; }
        .save-btn.saved {
            background: #166534;
            pointer-events: none;
        }
        footer {
            background: var(--panel);
            border-top: 1px solid var(--panel-border);
            padding: 16px 24px;
        }
        .input-bar {
            max-width: 1000px;
            margin: 0 auto;
            display: flex;
            gap: 12px;
        }
        #user-input {
            flex: 1;
            background: #0f172a;
            color: var(--text-main);
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 14px 18px;
            font-size: 1rem;
            outline: none;
        }
        #user-input:focus { border-color: var(--accent); }
        .send-btn {
            background: var(--accent);
            color: #0b0f19;
            font-weight: 700;
            border: none;
            border-radius: 10px;
            padding: 0 24px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .send-btn:hover { background: var(--accent-hover); }
        .loading { display: inline-block; animation: pulse 1.2s infinite; color: var(--accent); }
        @keyframes pulse { 0% { opacity: 0.2; } 50% { opacity: 1; } 100% { opacity: 0.2; } }
    </style>
</head>
<body>
    <header>
        <div class="header-title">
            <i class="fa-solid fa-brain"></i> Media Studio AI Assistant
        </div>
        <div class="header-actions">
            <select id="model-select">
                <option value="gemini-2.5-flash" selected>✨ Gemini 2.5 Flash</option>
                <option value="deepseek-coder:1.3b">💻 Local DeepSeek-Coder (1.3B)</option>
                <option value="qwen2.5-coder:7b">🧠 Local Qwen2.5-Coder (7B)</option>
                <option value="mistral:7b-instruct">⚡ Local Mistral (7B)</option>
            </select>
            <a href="http://localhost:5101" target="_blank" class="btn-remember">
                <i class="fa-solid fa-book-bookmark"></i> Open REMEMBER
            </a>
        </div>
    </header>

    <div id="chat-container">
        <div class="message-row ai">
            <div class="bubble">
                Hello Jack! I am <strong>Esperanza</strong>, your assistant connected to the entire <strong>Media Studio</strong> codebase via ChromaDB.
                <br><br>
                Ask me anything about routes, batch generators, CFG sweeps, video tools, or documentation! Every answer can be saved directly to your <strong>REMEMBER</strong> knowledge database with one click.
            </div>
        </div>
    </div>

    <footer>
        <div class="input-bar">
            <input type="text" id="user-input" placeholder="Ask anything about Media Studio (e.g., How does CFG sweep work?)..." autofocus autocomplete="off">
            <button class="send-btn" id="send-btn" onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i> Ask</button>
        </div>
    </footer>

    <script>
        const chatContainer = document.getElementById("chat-container");
        const userInput = document.getElementById("user-input");
        const modelSelect = document.getElementById("model-select");

        userInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendMessage();
        });

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;

            // 1. Append User Bubble
            appendMessage("user", text);
            userInput.value = "";

            // 2. Append Loading AI Bubble
            const aiRow = appendMessage("ai", '<span class="loading"><i class="fa-solid fa-circle-notch fa-spin"></i> Thinking and searching codebase...</span>');
            chatContainer.scrollTop = chatContainer.scrollHeight;

            const model = modelSelect.value;
            try {
                const res = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ question: text, model: model })
                });
                const data = await res.json();

                if (data.error) {
                    aiRow.querySelector(".bubble").innerHTML = `<span style="color: #f87171;">[!] Error: ${data.error}</span>`;
                    return;
                }

                // Render Markdown
                const parsedHtml = marked.parse(data.answer);
                let sourcesHtml = "";
                if (data.sources && data.sources.length) {
                    sourcesHtml = '<div class="sources-box"><strong>Sources Cited:</strong><br>' +
                        data.sources.map(s => `<span>${s}</span>`).join(" ") + '</div>';
                }

                const actionHtml = `
                    <div class="action-bar">
                        <button class="save-btn" onclick="saveAnswer(this, ${JSON.stringify(text)}, ${JSON.stringify(data.answer)}, ${JSON.stringify(data.sources)})">
                            <i class="fa-solid fa-bookmark"></i> 💾 Save to REMEMBER
                        </button>
                    </div>
                `;

                aiRow.querySelector(".bubble").innerHTML = parsedHtml + sourcesHtml + actionHtml;
            } catch (err) {
                aiRow.querySelector(".bubble").innerHTML = `<span style="color: #f87171;">[!] Request failed: ${err}</span>`;
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function appendMessage(sender, htmlContent) {
            const row = document.createElement("div");
            row.className = `message-row ${sender}`;
            const bubble = document.createElement("div");
            bubble.className = "bubble";
            bubble.innerHTML = htmlContent;
            row.appendChild(bubble);
            chatContainer.appendChild(row);
            return row;
        }

        async function saveAnswer(btn, question, answer, sources) {
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            try {
                const res = await fetch("/api/save_remember", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ question, answer, sources })
                });
                const data = await res.json();
                if (data.success) {
                    btn.className = "save-btn saved";
                    btn.innerHTML = `<i class="fa-solid fa-check"></i> Saved to REMEMBER (Post #${data.post_id})`;
                } else {
                    btn.innerHTML = 'Failed to save';
                }
            } catch (e) {
                btn.innerHTML = 'Save Error';
            }
        }
    </script>
</body>
</html>
"""

def run_web_server(port=5250, embed_model=DEFAULT_EMBED_MODEL):
    from flask import Flask, render_template_string, request, jsonify

    app = Flask(__name__)

    @app.route("/")
    def index_route():
        return render_template_string(WEB_HTML)

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data = request.get_json() or {}
        q = data.get("question", "").strip()
        m = data.get("model", DEFAULT_CHAT_MODEL)
        if not q:
            return jsonify({"error": "Empty question"}), 400

        ans, srcs = ask_codebase(q, chat_model=m, embed_model=embed_model, stream_stdout=False)
        return jsonify({"answer": ans, "sources": sorted(list(set(srcs)))})

    @app.route("/api/save_remember", methods=["POST"])
    def api_save_remember():
        data = request.get_json() or {}
        q = data.get("question", "")
        a = data.get("answer", "")
        s = data.get("sources", [])
        post_id, fn = save_to_remember(q, a, s)
        return jsonify({"success": True, "post_id": post_id, "filename": fn})

    print("=" * 65)
    print(f"🚀 Media Studio AI Web Assistant running at: http://localhost:{port}")
    print(f"💾 Connected to REMEMBER at: http://localhost:5101")
    print("=" * 65)
    app.run(host="0.0.0.0", port=port, debug=False)

def main():
    parser = argparse.ArgumentParser(description="Chat with Media Studio codebase via ChromaDB, Ollama, and Gemini.")
    parser.add_argument("-q", "--query", help="Ask a single question and exit")
    parser.add_argument("--index", action="store_true", help="Index/re-index codebase into ChromaDB")
    parser.add_argument("--force", action="store_true", help="Force re-indexing all files regardless of cache")
    parser.add_argument("--gemini", action="store_true", help="Use Gemini 2.5 Flash as the chat model")
    parser.add_argument("--web", action="store_true", help="Launch the Web Chat interface")
    parser.add_argument("--port", type=int, default=5250, help="Port for the web interface (default: 5250)")
    parser.add_argument("-m", "--model", default=None, help="Specific model name (Ollama or Gemini)")
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help=f"Ollama embedding model (default: {DEFAULT_EMBED_MODEL})")
    args = parser.parse_args()

    selected_model = DEFAULT_CHAT_MODEL
    if args.gemini:
        selected_model = "gemini-2.5-flash"
    elif args.model:
        selected_model = args.model

    # If database doesn't exist yet, auto-index
    if not os.path.exists(CHROMA_DIR) or args.index or args.force:
        index_codebase(force=args.force, embed_model=args.embed_model)

    if args.web:
        run_web_server(port=args.port, embed_model=args.embed_model)
    elif args.query:
        ans, srcs = ask_codebase(args.query, chat_model=selected_model, embed_model=args.embed_model)
    else:
        interactive_chat(chat_model=selected_model, embed_model=args.embed_model)

if __name__ == "__main__":
    main()
