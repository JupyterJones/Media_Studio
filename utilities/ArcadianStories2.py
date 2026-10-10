#!/usr/bin/env python3
"""
Arcadian Story Generator (FULL AUTO MODE)
- One-run automatic story generation
- Preserves continuity using last two paragraphs
- Generates entire outline without user interaction
- Writes per-bullet files and a final combined story
"""

import os
import sqlite3
import json
import requests
import datetime
from icecream import ic
from random import randint
STORY = str(randint(111111,999999))
# -----------------------------
# CONFIG
# -----------------------------
OUTPUT_DIR = f"static/{STORY}_output_clean-v6"
DB_FILE = f"{OUTPUT_DIR}/{STORY}_app_clean-v6.db"
# -----------------------------


AI_ENDPOINT = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"
TIMEOUT = 900

FINAL_STORY_FILE = os.path.join(OUTPUT_DIR, "final_story_auto.txt")

FIRST_BULLET_PRIMER = (
    "The Arcadians are an ancient alien civilization spanning millions of years. "
    "They observe, guide, and intervene in younger civilizations when extinction becomes imminent."
)

text = open("static/564408_output_clean-v6/final_story_auto.txt").read()
# Option 1: Keep the paragraphs as bullets (careful with explosion)
#OUTLINE_BULLETS = [p.strip() for p in text.split("\n\n") if p.strip()]

# Option 2 (safer): Only take first sentences or key summary lines per bullet
# e.g., if your paragraphs start with a clear summary
OUTLINE_BULLETS = [p.split(".")[0].strip() for p in text.split("\n\n") if p.strip()]

# -----------------------------
# SETUP
# -----------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# LOGGING
# -----------------------------
def logit(text):
    with open(FINAL_STORY_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

# -----------------------------
# DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bullet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position INTEGER,
            text TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS story (
            bullet_id INTEGER PRIMARY KEY,
            story_text TEXT,
            last_two TEXT
        )
    """)
    conn.commit()
    conn.close()

def seed_outline():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for i, text in enumerate(OUTLINE_BULLETS):
        c.execute("INSERT INTO bullet (position, text) VALUES (?, ?)", (i, text))
    conn.commit()
    conn.close()

def load_bullets():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, position, text FROM bullet ORDER BY position")
    rows = c.fetchall()
    conn.close()
    return rows

# -----------------------------
# CONTINUITY
# -----------------------------
def extract_last_two_paragraphs(text):
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(parts) >= 2:
        return "\n\n".join(parts[-2:])
    return parts[-1] if parts else ""

# -----------------------------
# AI GENERATION
# -----------------------------
def generate_story(bullet_text, continuity):
    prompt = (
        f"{continuity}\n\n"
        f"Write a detailed science fiction story section for the following outline item:\n"
        f"{bullet_text}\n\n"
        f"Output exactly 7 paragraphs."
    )

    ic("PROMPT", prompt)

    full = ""
    resp = requests.post(
        AI_ENDPOINT,
        json={"model": MODEL, "prompt": prompt, "stream": True},
        stream=True,
        timeout=TIMEOUT
    )

    for line in resp.iter_lines():
        if not line:
            continue
        token = json.loads(line.decode()).get("response", "")
        full += token
        ic(token)

    return full.strip()

# -----------------------------
# SAVE STORY
# -----------------------------
def save_story(bullet_id, story_text):
    last_two = extract_last_two_paragraphs(story_text)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO story (bullet_id, story_text, last_two)
        VALUES (?, ?, ?)
    """, (bullet_id, story_text, last_two))
    conn.commit()
    conn.close()

    with open(os.path.join(OUTPUT_DIR, f"bullet_{bullet_id:04d}.txt"), "w", encoding="utf-8") as f:
        f.write(story_text + "\n\n--- CONTINUITY ---\n" + last_two)

    logit(story_text)
    return last_two

# -----------------------------
# MAIN AUTO LOOP
# -----------------------------
def run_auto_story():
    bullets = load_bullets()
    continuity = FIRST_BULLET_PRIMER

    for bullet_id, position, text in bullets:
        ic("GENERATING BULLET", position, text)
        story = generate_story(text, continuity)
        continuity = save_story(bullet_id, story)

    ic("STORY COMPLETE")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    init_db()
    seed_outline()
    run_auto_story()
