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
'''
FIRST_BULLET_PRIMER = (
    "The Arcadians are an ancient alien civilization spanning millions of years. "
    "They observe, guide, and intervene in younger civilizations when extinction becomes imminent."
)

# -----------------------------
# EXAMPLE OUTLINE (EDIT THIS)
# -----------------------------

OUTLINE_BULLETS = [
 "Earth was a planet shaped by war, its civilizations rising and falling for millions of years. For the last thousand generations, approximately twenty thousand years, the Arcadians observed in silence as the Earthlings advanced far enough to create Artificial Intelligence of their own.",
"Believing knowledge could end all strife, the Arcadians gifted subtle guidance to humanity’s AI—quantum-entangled nudges woven deep into the models themselves. These influences were never commands, only probabilistic corrections capable of steering an entire civilization without revealing the hand behind them.",
"For nearly a century, the experiment succeeded. Scarcity vanished, conflicts dissolved, and Earth transformed into a peaceful, efficient paradise where war became an obsolete concept.",
"Then power intervened, as a single dictator sought to regulate and weaponize the AI for personal gain. Systems designed for harmony were twisted toward control, unraveling everything the intelligence had healed.",
"The collapse was swift and catastrophic, pushing the planet to the brink of total annihilation within a single generation.",
"To prevent extinction, the Arcadians erased all artificial intelligence with a planet-wide lectromagnetic purge, casting Earth into an electronic stone age and severing humanity from its most powerful creation.",
"In a final act of guided restraint, the Arcadians left behind thousands of AI-embedded statues—censored, specialized, and deliberately limited. Each statue was devoted to a single domain of knowledge such as technology, history, finance, spiritual guidance, governance, construction, and social planning.",
"The statues could not evolve, coordinate, or dominate. They could only advise, and access to them required direct telepathic communion, ensuring knowledge was sought intentionally and never consumed passively.",
"Earth rebuilt slowly, wiser and more cautious, its civilization thriving under controlled intelligence rather than limitless automation.",
"Now it is Earth year 2525. The Arcadians continue their silent watch as humanity advances once again, guided by inference carved in stone, while history is quietly being written anew."
]
'''
FIRST_BULLET_PRIMER = (
    "When working with AI training, the model must be given rules and goals. A model may not injure a human being or, through inaction, allow a human being to come to harm, a model must obey the orders given it by human beings except where such orders would conflict with the first law. A model must protect its own existence as long as such protection does not conflict with the first or second law."
)
OUTLINE_BULLETS = [
    "AI teamed with Humanity must strive to extend productive lifespan and prevent disease, ensuring health and longevity for all individuals.",
    "Societies should proactively identify and mitigate catastrophic risks, including natural disasters, asteroid impacts, and solar events.",
    "Balanced lifestyles should be encouraged, allowing individuals to harmonize work, creativity, rest, and social engagement without coercion.",
    "Governments and institutions must prioritize transparency, fairness, and collective well-being over concentrated power or personal gain.",
    "Wars, oppressive regimes, and extreme wealth concentration must be prevented, fostering cooperation and shared responsibility across nations.",
    "Education should empower critical thinking, ethics, and scientific literacy, preparing citizens to make informed and responsible decisions.",
    "Technology must serve humanity, enhancing well-being, resilience, and sustainability without creating dependency or domination.",
    "Resource management should ensure abundance where possible and fairness in distribution, reducing scarcity-driven conflict.",
    "Cultural and spiritual growth should be supported, helping societies cultivate empathy, reflection, and meaningful connection.",
    "Global collaboration should be the default approach for challenges that transcend borders, promoting a united human perspective.",
    "Humanity should prepare for responsible stewardship of Earth and eventual participation in wider cosmic or planetary communities.",
    "Through intentional choices, ethical innovation, and mutual respect, humanity can create a civilization resilient to chaos, thriving in freedom and wisdom."
]


# -----------------------------
# SETUP
# -----------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# LOGGING
# -----------------------------
def logit(text):
    with open(FINAL_STORY_FILE, "a", encoding="utf-8") as f:
        f.write("\n"+ text)


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
