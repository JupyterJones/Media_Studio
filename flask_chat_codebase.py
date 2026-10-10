#!/usr/bin/env python3
"""
flask_chat_codebase.py - Mobile-Friendly AI Assistant & Codebase Q&A Studio
Shares port 5200 with Media Studio (mounted at /chat) or runs standalone on port 5205.
Centered on asking dozens/hundreds of AI questions from mobile, tablet, or desktop,
reviewing and editing answers in a large <textarea>, and 1-click <Save2Remember>.
"""

import os
import re
import sys
import time
import json
import sqlite3
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REMEMBER_DB = os.path.join(BASE_DIR, "static", "REMEMBER.db")
REMEMBER_TEXT_DIR = os.path.join(BASE_DIR, "static", "TEXT")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_media_studio")

# Import optional LoRA extractor logic
try:
    import get_lora_keywords
except ImportError:
    get_lora_keywords = None

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


# ----------------------------------------------------------------------
# AI Query & RAG Helpers
# ----------------------------------------------------------------------

def query_gemini(system_prompt, user_prompt, model_name="gemini-2.5-flash"):
    """Query Gemini API with system instructions and user prompt."""
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY environment variable is not set."

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
        )
        return response.text if response and response.text else "No response generated."
    except Exception as e:
        return f"Gemini API Error: {e}"


def query_ollama(system_prompt, user_prompt, model_name="deepseek-coder:1.3b"):
    """Query local Ollama server."""
    try:
        import ollama
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        res = ollama.chat(model=model_name, messages=messages)
        return res.get("message", {}).get("content", "No response from Ollama.")
    except Exception as e:
        return f"Local Ollama Error: {e}"


def search_chroma_codebase(question, top_k=4):
    """Retrieve relevant code chunks from ChromaDB for grounding."""
    try:
        import chromadb
        import ollama

        if not os.path.exists(CHROMA_DIR):
            return [], []

        client = chromadb.PersistentClient(path=CHROMA_DIR)
        collection = client.get_or_create_collection(
            name="media_studio_codebase",
            metadata={"hnsw:space": "cosine"}
        )

        q_emb = ollama.embeddings(model="nomic-embed-text", prompt=question)["embedding"]
        results = collection.query(query_embeddings=[q_emb], n_results=top_k)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        context_parts = []
        sources = []
        for doc, meta in zip(docs, metas):
            context_parts.append(doc)
            sources.append(f"{meta['file']}:{meta['start_line']}-{meta['end_line']}")

        return context_parts, sources
    except Exception as e:
        print(f"Chroma search error: {e}")
        return [], []


def execute_ask(question, model="gemini-2.5-flash", use_rag=False):
    """Ask question either with codebase RAG or direct AI assistance."""
    sources = []
    system_prompt = (
        "You are Esperanza, Jack's expert AI pair programmer and technical assistant. "
        "You have deep knowledge of Python programming, Linux bash commands and system administration, "
        "Stable Diffusion and generative AI, multimedia pipelines, and the Media Studio application.\n"
        "Always be clear, accurate, concise, and provide practical code examples or commands where helpful."
    )

    if use_rag:
        contexts, sources = search_chroma_codebase(question)
        if contexts:
            user_prompt = (
                f"Media Studio Codebase Context:\n"
                f"====================================================\n"
                f"{'\n'.join(contexts)}\n"
                f"====================================================\n\n"
                f"Question: {question}"
            )
        else:
            user_prompt = question
    else:
        user_prompt = question

    if "gemini" in model.lower():
        answer = query_gemini(system_prompt, user_prompt, model_name=model)
    else:
        answer = query_ollama(system_prompt, user_prompt, model_name=model)

    return answer, sources


# ----------------------------------------------------------------------
# Optional LoRA Helper
# ----------------------------------------------------------------------

def get_lora_files_dict():
    """Retrieve dictionary of all available LoRA files."""
    if get_lora_keywords:
        return get_lora_keywords.find_lora_files()
    return {}


def format_single_lora_markdown(info):
    """Format single LoRA metadata into structured Markdown for review."""
    fn = info.get("filename", "Unknown LoRA")
    triggers = info.get("trigger_phrases", [])
    trigger_str = ", ".join(f"`{t}`" for t in triggers) if triggers else "*No specific trigger word required (Style LoRA)*"
    top_tags = info.get("top_tags", [])
    base_model = info.get("base_model", "Unknown")
    output_name = info.get("output_name", "")
    filepath = info.get("filepath", "")

    lora_tag_name = os.path.splitext(fn)[0]
    first_trigger = triggers[0] if triggers else ""
    sample_tags = ", ".join(top_tags[:6]) if top_tags else "masterpiece, highly detailed"

    sample_prompt = f"<lora:{lora_tag_name}:0.85>"
    if first_trigger:
        sample_prompt += f", {first_trigger}"
    if sample_tags:
        sample_prompt += f", {sample_tags}"

    md = []
    md.append(f"# 🎨 LoRA: {fn}\n")
    md.append(f"- **Base Model:** `{base_model}`")
    if output_name:
        md.append(f"- **Output Name:** `{output_name}`")
    md.append(f"- **File Path:** `{filepath}`\n")
    md.append(f"### ⚡ Activation / Trigger Keywords:\n{trigger_str}\n")

    if top_tags:
        md.append("### 🏷️ Top Training Tags:\n")
        tag_badges = " ".join(f"`{t}`" for t in top_tags)
        md.append(f"{tag_badges}\n")

    if info.get("companion_text_sample"):
        md.append(f"### 📝 Companion Prompt Sample:\n```text\n{info['companion_text_sample']}\n```\n")

    md.append("### 💡 Recommended Test Prompt:\n")
    md.append(f"```text\n{sample_prompt}\n```\n")
    md.append("### 📌 User Notes & Observations:\n")
    md.append("- Recommended Weight: 0.8 - 0.9\n- Compatible Checkpoints: \n- Notes: \n")

    return "\n".join(md)


# ----------------------------------------------------------------------
# Database & File Storage
# ----------------------------------------------------------------------

def save_post_to_remember(title, content):
    """Save content to REMEMBER.db and write a markdown backup."""
    os.makedirs(REMEMBER_TEXT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(REMEMBER_DB), exist_ok=True)

    post_id = None
    try:
        conn = sqlite3.connect(REMEMBER_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO post (title, content, image, video_filename, audio) VALUES (?, ?, NULL, NULL, NULL)",
            (title, content)
        )
        post_id = c.lastrowid
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving to REMEMBER.db: {e}")

    # Write backup markdown file
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", title.replace(" ", "_"))[:50]
    filename = f"qna_{post_id or int(time.time())}_{safe_slug}.md"
    filepath = os.path.join(REMEMBER_TEXT_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Error saving markdown backup: {e}")

    return post_id, filename


# ----------------------------------------------------------------------
# Mobile & Tablet First HTML Template
# ----------------------------------------------------------------------

MOBILE_CHAT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Esperanza • AI Studio & Remember</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="icon" href="/favicon.ico?v=1">

    <style>
        :root {
            --bg-body: #080b14;
            --bg-card: rgba(18, 24, 42, 0.92);
            --bg-card-hover: rgba(28, 36, 64, 0.98);
            --border-card: rgba(255, 255, 255, 0.09);
            --border-focus: #38bdf8;
            --accent: #38bdf8;
            --accent-purple: #c084fc;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --radius-md: 12px;
            --radius-lg: 16px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            background-color: var(--bg-body);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 15px;
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Sticky Header */
        .header-bar {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(8, 11, 20, 0.95);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid var(--border-card);
            padding: 12px 18px;
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }

        .header-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: 'Outfit', sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
        }

        .header-title i {
            color: var(--accent);
            text-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
        }

        .esperanza-badge {
            font-size: 0.75rem;
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(192, 132, 252, 0.2));
            color: var(--accent);
            border: 1px solid rgba(56, 189, 248, 0.35);
            padding: 2px 9px;
            border-radius: 12px;
            font-weight: 600;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .nav-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 12px;
            border-radius: var(--radius-md);
            font-size: 0.85rem;
            font-weight: 600;
            text-decoration: none;
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-card);
            transition: all 0.2s ease;
        }

        .nav-btn:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: var(--border-focus);
            color: #ffffff;
        }

        .nav-btn.primary {
            background: linear-gradient(135deg, #0284c7, #6366f1);
            border: none;
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
        }

        /* Container */
        .container {
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            padding: 16px;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* Glass Cards */
        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: var(--radius-lg);
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-card);
            flex-wrap: wrap;
            gap: 8px;
        }

        .panel-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.18rem;
            font-weight: 600;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Controls */
        .form-group {
            margin-bottom: 14px;
        }

        .form-label {
            display: block;
            font-size: 0.88rem;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 6px;
        }

        .form-input, .form-textarea, select.form-input {
            width: 100%;
            background: rgba(11, 15, 28, 0.95);
            border: 1px solid var(--border-card);
            border-radius: var(--radius-md);
            padding: 13px 15px;
            color: #ffffff;
            font-family: inherit;
            font-size: 1rem;
            transition: all 0.2s ease;
        }

        .form-input:focus, .form-textarea:focus, select.form-input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
            background: rgba(14, 20, 36, 0.98);
        }

        .query-textarea {
            height: 110px;
            resize: vertical;
        }

        .answer-textarea {
            height: 440px;
            font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
            font-size: 0.93rem;
            line-height: 1.6;
            color: #38bdf8 !important;
            background: #060913 !important;
            border-color: rgba(56, 189, 248, 0.3) !important;
            resize: vertical;
        }

        .options-row {
            display: grid;
            grid-template-columns: 1.3fr 1fr;
            gap: 12px;
            align-items: center;
            margin-bottom: 14px;
        }

        @media (max-width: 650px) {
            .options-row {
                grid-template-columns: 1fr;
            }
        }

        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 9px;
            font-size: 0.92rem;
            font-weight: 500;
            cursor: pointer;
            user-select: none;
            color: #cbd5e1;
        }

        .checkbox-label input {
            accent-color: #38bdf8;
            width: 19px;
            height: 19px;
            cursor: pointer;
        }

        /* Buttons */
        .btn-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .btn {
            padding: 13px 20px;
            border-radius: var(--radius-md);
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s ease;
        }

        .btn-ask {
            flex: 2;
            background: linear-gradient(135deg, #38bdf8, #0284c7);
            color: #040814;
            font-weight: 700;
            box-shadow: 0 4px 16px rgba(56, 189, 248, 0.35);
        }

        .btn-ask:hover {
            filter: brightness(1.1);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(56, 189, 248, 0.5);
        }

        .btn-clear {
            flex: 1;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-card);
            color: var(--text-muted);
        }

        .btn-clear:hover {
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }

        /* Primary Save to Remember Button */
        .btn-save-remember {
            background: linear-gradient(135deg, #10b981, #059669);
            color: #ffffff;
            font-size: 1.1rem;
            font-weight: 700;
            padding: 15px 24px;
            box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35);
            flex: 2;
        }

        .btn-save-remember:hover {
            background: linear-gradient(135deg, #059669, #047857);
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(16, 185, 129, 0.5);
        }

        .btn-copy {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border-card);
            color: var(--text-main);
            padding: 13px 20px;
            flex: 1;
        }

        .btn-copy:hover {
            background: rgba(255, 255, 255, 0.16);
            color: #ffffff;
        }

        /* Status Banners */
        .status-alert {
            padding: 13px 16px;
            border-radius: var(--radius-md);
            margin-top: 14px;
            display: none;
            align-items: center;
            gap: 10px;
            font-size: 0.95rem;
            animation: fadeIn 0.25s ease;
        }

        .status-success {
            background: rgba(16, 185, 129, 0.18);
            border: 1px solid rgba(16, 185, 129, 0.45);
            color: #a7f3d0;
        }

        .status-error {
            background: rgba(239, 68, 68, 0.18);
            border: 1px solid rgba(239, 68, 68, 0.45);
            color: #fca5a5;
        }

        .status-loading {
            background: rgba(56, 189, 248, 0.18);
            border: 1px solid rgba(56, 189, 248, 0.45);
            color: #bae6fd;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Chips */
        .chip-list {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 6px;
            margin-bottom: 12px;
            scrollbar-width: thin;
        }

        .chip {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-card);
            color: #cbd5e1;
            padding: 6px 13px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.15s;
        }

        .chip:hover {
            background: rgba(56, 189, 248, 0.15);
            border-color: var(--accent);
            color: #ffffff;
        }

        /* Optional Collapsible Tools Drawer */
        details.tools-drawer {
            background: rgba(12, 17, 30, 0.7);
            border: 1px dashed var(--border-card);
            border-radius: var(--radius-md);
            padding: 12px 16px;
            font-size: 0.9rem;
        }

        details.tools-drawer summary {
            cursor: pointer;
            color: var(--text-muted);
            font-weight: 600;
            outline: none;
            display: flex;
            align-items: center;
            gap: 8px;
            user-select: none;
        }

        details.tools-drawer summary:hover {
            color: var(--text-main);
        }

        .drawer-content {
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px solid var(--border-card);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
    </style>
</head>
<body>
    <!-- Sticky Header -->
    <header class="header-bar">
        <div class="header-content">
            <div class="header-title">
                <i class="fa-solid fa-brain"></i>
                <span>AI Q&A Studio</span>
                <span class="esperanza-badge">Esperanza</span>
            </div>
            <nav class="nav-links">
                <a href="/remember" class="nav-btn" target="_blank">
                    <i class="fa-solid fa-book-bookmark"></i> Remember DB
                </a>
                <a href="/add_novel_caption" class="nav-btn">
                    <i class="fa-solid fa-closed-captioning"></i> Caption Studio
                </a>
                <a href="/" class="nav-btn primary">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Media Studio
                </a>
            </nav>
        </div>
    </header>

    <main class="container">
        <!-- 1. Question Input Panel -->
        <section class="panel">
            <div class="panel-header">
                <h2 class="panel-title">
                    <i class="fa-solid fa-circle-question" style="color: var(--accent);"></i>
                    Ask Esperanza
                </h2>
                <span style="font-size: 0.8rem; color: var(--text-muted);">
                    Mobile & Tablet Friendly
                </span>
            </div>

            <!-- Quick Topic Chips -->
            <div class="chip-list">
                <span class="chip" onclick="setQuestion('Give me the top 10 most useful Linux bash commands for monitoring GPU, disk, and processes.')">💻 Bash Commands</span>
                <span class="chip" onclick="setQuestion('How is the CFG sweep implemented in Media Studio?')">⚡ CFG Sweep</span>
                <span class="chip" onclick="setQuestion('Explain how posts, audio, and videos are saved and queried in REMEMBER.db.')">💾 Remember DB</span>
                <span class="chip" onclick="setQuestion('Where are models located and how does dynamic MODELS_ROOTS work?')">📁 Model Paths</span>
                <span class="chip" onclick="setQuestion('How do novel captioning and MP4 creation with Kokoro TTS work?')">🎬 Novel Caption</span>
            </div>

            <!-- Question Input -->
            <div class="form-group">
                <label for="questionInput" class="form-label">
                    Ask any question (Python code, bash commands, models, prompts, ideas):
                </label>
                <textarea 
                    id="questionInput" 
                    class="form-input query-textarea" 
                    placeholder="Type your question here... e.g. How do I inspect a SQLite table from bash or python?" 
                    autofocus></textarea>
            </div>

            <!-- Controls Row -->
            <div class="options-row">
                <div>
                    <label for="modelSelect" class="form-label">Select AI Model:</label>
                    <select id="modelSelect" class="form-input">
                        <option value="gemini-2.5-flash" selected>✨ Gemini 2.5 Flash (Super Fast • Recommended)</option>
                        <option value="gemini-1.5-pro">🧠 Gemini 1.5 Pro (Deep Analysis)</option>
                        <option value="deepseek-coder:1.3b">💻 Local Ollama (DeepSeek-Coder)</option>
                    </select>
                </div>

                <div style="padding-top: 24px;">
                    <label class="checkbox-label">
                        <input type="checkbox" id="useRag">
                        <span>Search Media Studio Codebase (RAG)</span>
                    </label>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="btn-row">
                <button type="button" class="btn btn-ask" id="askBtn" onclick="submitQuestion()">
                    <i class="fa-solid fa-paper-plane"></i> 🚀 Ask Esperanza
                </button>
                <button type="button" class="btn btn-clear" onclick="clearQuestion()">
                    <i class="fa-solid fa-eraser"></i> Clear
                </button>
            </div>

            <!-- Query Status Banner -->
            <div id="queryStatus" class="status-alert"></div>
        </section>

        <!-- 2. Review, Edit & Save2Remember Panel -->
        <section class="panel">
            <div class="panel-header">
                <h2 class="panel-title">
                    <i class="fa-solid fa-pen-to-square" style="color: var(--accent-purple);"></i>
                    Review & Edit (Read Before Saving)
                </h2>
                <span style="font-size: 0.8rem; color: var(--text-muted);" id="wordCount">
                    0 characters
                </span>
            </div>

            <!-- Editable Title -->
            <div class="form-group">
                <label for="postTitle" class="form-label">
                    <i class="fa-solid fa-heading"></i> Title for REMEMBER:
                </label>
                <input 
                    type="text" 
                    id="postTitle" 
                    class="form-input" 
                    placeholder="Title will appear here based on your question...">
            </div>

            <!-- Editable Content Textarea -->
            <div class="form-group">
                <label for="answerTextarea" class="form-label">
                    <i class="fa-solid fa-align-left"></i> Answer & Notes (Freely read, edit, delete, or add your notes):
                </label>
                <textarea 
                    id="answerTextarea" 
                    class="form-input answer-textarea" 
                    placeholder="AI answer will appear here in full. You can read through it, edit code snippets, add your own test observations, and format it exactly how you want before tapping Save2Remember..."></textarea>
            </div>

            <!-- Save Actions -->
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <div class="btn-row">
                    <button type="button" class="btn btn-save-remember" id="save2rememberBtn" onclick="saveToRemember()">
                        <i class="fa-solid fa-floppy-disk"></i> 💾 Save2Remember
                    </button>
                    <button type="button" class="btn btn-copy" onclick="copyAnswer()">
                        <i class="fa-solid fa-copy"></i> 📋 Copy
                    </button>
                    <button type="button" class="btn btn-clear" onclick="clearAll()">
                        <i class="fa-solid fa-rotate-right"></i> Next Question
                    </button>
                </div>

                <!-- Save Confirmation Banner -->
                <div id="saveStatus" class="status-alert"></div>
            </div>
        </section>

        <!-- 3. Optional Helper Drawer (LoRA Keywords) -->
        <details class="tools-drawer">
            <summary>
                <i class="fa-solid fa-screwdriver-wrench"></i>
                <span>Optional Helper: LoRA Keywords Extractor (Click to expand)</span>
            </summary>
            <div class="drawer-content">
                <p style="color: var(--text-muted); font-size: 0.85rem;">
                    Quickly inspect trigger words and tags for any LoRA model directly into the editable textarea above:
                </p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <select id="drawerLoraSelect" class="form-input" style="flex: 2;">
                        <option value="">Select a LoRA model...</option>
                    </select>
                    <button type="button" class="btn" style="background: rgba(245, 158, 11, 0.2); border: 1px solid rgba(245, 158, 11, 0.4); color: #fde68a;" onclick="extractDrawerLora()">
                        <i class="fa-solid fa-bolt"></i> Load LoRA Info
                    </button>
                </div>
            </div>
        </details>
    </main>

    <script>
        const API_BASE = window.location.pathname.startsWith('/chat') ? '/chat' : '';
        const questionInput = document.getElementById('questionInput');
        const answerTextarea = document.getElementById('answerTextarea');
        const postTitle = document.getElementById('postTitle');
        const askBtn = document.getElementById('askBtn');
        const queryStatus = document.getElementById('queryStatus');
        const saveStatus = document.getElementById('saveStatus');
        const wordCount = document.getElementById('wordCount');
        const drawerLoraSelect = document.getElementById('drawerLoraSelect');

        answerTextarea.addEventListener('input', () => {
            wordCount.textContent = `${answerTextarea.value.length.toLocaleString()} characters`;
        });

        function setQuestion(txt) {
            questionInput.value = txt;
            questionInput.focus();
        }

        function clearQuestion() {
            questionInput.value = '';
            questionInput.focus();
        }

        function clearAll() {
            questionInput.value = '';
            postTitle.value = '';
            answerTextarea.value = '';
            wordCount.textContent = '0 characters';
            saveStatus.style.display = 'none';
            queryStatus.style.display = 'none';
            questionInput.focus();
        }

        // Submit Question to Esperanza
        async function submitQuestion() {
            const question = questionInput.value.trim();
            if (!question) {
                alert("Please enter a question first!");
                questionInput.focus();
                return;
            }

            const model = document.getElementById('modelSelect').value;
            const useRag = document.getElementById('useRag').checked;

            askBtn.disabled = true;
            askBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Consulting Esperanza...';

            queryStatus.className = 'status-alert status-loading';
            queryStatus.style.display = 'flex';
            queryStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Esperanza is formulating your response...';

            saveStatus.style.display = 'none';

            try {
                const res = await fetch(`${API_BASE}/api/ask`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question, model, use_rag: useRag })
                });

                const data = await res.json();

                if (data.status === 'ok') {
                    queryStatus.style.display = 'none';

                    postTitle.value = data.title || `[Q&A] ${question}`;

                    let fullText = data.answer;
                    if (data.sources && data.sources.length) {
                        fullText += '\\n\\n---\\n### 📚 Codebase Sources Cited:\\n';
                        data.sources.forEach(s => {
                            fullText += `- ${s}\\n`;
                        });
                    }

                    answerTextarea.value = fullText;
                    wordCount.textContent = `${fullText.length.toLocaleString()} characters`;

                    // Smooth scroll down to answer on mobile
                    if (window.innerWidth < 768) {
                        answerTextarea.scrollIntoView({ behavior: 'smooth' });
                    }
                } else {
                    queryStatus.className = 'status-alert status-error';
                    queryStatus.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Error: ${data.message || 'Unknown error'}`;
                }
            } catch (err) {
                queryStatus.className = 'status-alert status-error';
                queryStatus.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Request failed: ${err.message}`;
            } finally {
                askBtn.disabled = false;
                askBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> 🚀 Ask Esperanza';
            }
        }

        // Save to REMEMBER
        async function saveToRemember() {
            const content = answerTextarea.value.trim();
            if (!content) {
                alert("Textarea is empty! Ask a question or type some notes first.");
                return;
            }

            const title = postTitle.value.trim() || `Q&A - ${new Date().toLocaleString()}`;
            const saveBtn = document.getElementById('save2rememberBtn');

            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            saveStatus.style.display = 'none';

            try {
                const res = await fetch(`${API_BASE}/api/save_remember`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, content })
                });

                const data = await res.json();

                if (data.status === 'ok') {
                    saveStatus.className = 'status-alert status-success';
                    saveStatus.style.display = 'flex';
                    saveStatus.innerHTML = `
                        <i class="fa-solid fa-circle-check"></i>
                        <span>
                            <strong>✓ Successfully saved to REMEMBER!</strong> (Post #${data.post_id}) &bull; 
                            <a href="/remember/post/${data.post_id}" target="_blank" style="color: #6ee7b7; text-decoration: underline; font-weight: 600;">
                                Open in REMEMBER <i class="fa-solid fa-arrow-up-right-from-square"></i>
                            </a>
                        </span>
                    `;
                } else {
                    saveStatus.className = 'status-alert status-error';
                    saveStatus.style.display = 'flex';
                    saveStatus.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Failed to save: ${data.message}`;
                }
            } catch (err) {
                saveStatus.className = 'status-alert status-error';
                saveStatus.style.display = 'flex';
                saveStatus.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Save failed: ${err.message}`;
            } finally {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> 💾 Save2Remember';
            }
        }

        function copyAnswer() {
            const txt = answerTextarea.value;
            if (!txt) {
                alert("No content to copy yet.");
                return;
            }
            navigator.clipboard.writeText(txt).then(() => {
                alert("✓ Content copied to clipboard!");
            }).catch(() => {
                answerTextarea.select();
                document.execCommand('copy');
                alert("✓ Content copied to clipboard!");
            });
        }

        // Optional LoRA Drawer Loader
        async function loadDrawerLoras() {
            try {
                const res = await fetch(`${API_BASE}/api/loras`);
                const data = await res.json();
                if (data.status === 'ok' && data.loras) {
                    drawerLoraSelect.innerHTML = '<option value="">Select a LoRA model...</option>';
                    data.loras.forEach(l => {
                        const opt = document.createElement('option');
                        opt.value = l.filename;
                        opt.textContent = l.filename;
                        drawerLoraSelect.appendChild(opt);
                    });
                }
            } catch (e) {}
        }

        async function extractDrawerLora() {
            const selLora = drawerLoraSelect.value;
            if (!selLora) {
                alert("Please select a LoRA model first.");
                return;
            }
            try {
                const res = await fetch(`${API_BASE}/api/extract_lora`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ lora_name: selLora })
                });
                const data = await res.json();
                if (data.status === 'ok') {
                    postTitle.value = data.title;
                    answerTextarea.value = data.content;
                    wordCount.textContent = `${data.content.length.toLocaleString()} characters`;
                    answerTextarea.scrollIntoView({ behavior: 'smooth' });
                }
            } catch (e) {
                alert("Extraction failed: " + e.message);
            }
        }

        // Initialize LoRAs for optional drawer
        loadDrawerLoras();
    </script>
</body>
</html>
"""

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------

@app.route("/")
def index_route():
    return render_template_string(MOBILE_CHAT_HTML)


@app.route("/api/ask", methods=["POST"])
def api_ask():
    try:
        data = request.get_json() or {}
        question = data.get("question", "").strip()
        model = data.get("model", "gemini-2.5-flash")
        use_rag = data.get("use_rag", False)

        if not question:
            return jsonify({"status": "error", "message": "Question cannot be empty."}), 400

        answer, sources = execute_ask(question, model=model, use_rag=use_rag)
        clean_title = f"[Q&A] {question[:60]}"

        return jsonify({
            "status": "ok",
            "title": clean_title,
            "answer": answer,
            "sources": sorted(list(set(sources))),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/save_remember", methods=["POST"])
def api_save_remember():
    try:
        data = request.get_json() or {}
        title = data.get("title", "").strip() or f"Q&A - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        content = data.get("content", "").strip()

        if not content:
            return jsonify({"status": "error", "message": "Textarea content cannot be empty."}), 400

        post_id, filename = save_post_to_remember(title, content)

        return jsonify({
            "status": "ok",
            "post_id": post_id,
            "filename": filename,
            "title": title
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/loras", methods=["GET"])
def api_loras():
    try:
        loras = get_lora_files_dict()
        lora_list = [{"filename": fn, "path": path} for fn, path in sorted(loras.items())]
        return jsonify({"status": "ok", "loras": lora_list, "total": len(lora_list)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/extract_lora", methods=["POST"])
def api_extract_lora():
    try:
        data = request.get_json() or {}
        lora_name = data.get("lora_name", "").strip()
        if not lora_name:
            return jsonify({"status": "error", "message": "No LoRA specified."}), 400

        loras = get_lora_files_dict()
        filepath = loras.get(lora_name)
        if not filepath:
            for fn, path in loras.items():
                if lora_name.lower() in fn.lower():
                    filepath = path
                    lora_name = fn
                    break

        if not filepath or not os.path.exists(filepath):
            return jsonify({"status": "error", "message": f"LoRA file '{lora_name}' not found."}), 404

        info = get_lora_keywords.extract_lora_info(filepath)
        content = format_single_lora_markdown(info)
        clean_title = f"[LoRA] {info.get('output_name') or lora_name} Trigger Keywords"

        return jsonify({
            "status": "ok",
            "title": clean_title,
            "content": content,
            "info": info
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("CHAT_PORT", 5205))
    print("=" * 65)
    print(f"🚀 AI Assistant & Q&A Studio Starting on port {port}")
    print(f"   URL: http://localhost:{port}/")
    print("=" * 65)
    app.run(host="0.0.0.0", port=port, debug=True)
