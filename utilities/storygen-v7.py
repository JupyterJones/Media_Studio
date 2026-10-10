#!/usr/bin/env python3
"""
Arcadian Story Generator Flask App (CLEAN RESTORE)
- Preserves all original mechanics
- logit() now saves total story correctly
- Bullets & generate/save/next/prev intact
- Example narrative visible at all times
"""

import os
import sqlite3
import json
import requests
import datetime
from flask import Flask, request, render_template_string, redirect, url_for
from icecream import ic

# -----------------------------
# CONFIG
# -----------------------------
OUTPUT_DIR = "story_output_clean-v7"
DB_FILE = f"{OUTPUT_DIR}/story_app_clean-v7.db"

AI_ENDPOINT = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"
TIMEOUT = 900

FIRST_BULLET_PRIMER = (
    "The Arcadians are an ancient alien civilization spanning millions of years. ",
    "Their AI systems observe, guide, and sometimes intervene in younger civilizations.",
    "they taught the AI stem how to convert items into spheres"
)

EXAMPLE_TEXT = """
Staacor was a planet shaped by war, its civilizations rising and falling across a thousand generations of conflict. For five hundred generations, the Arcadians observed in silence as the Staacorians advanced far enough to create Artificial Intelligence of their own.
Believing knowledge could end all strife, The Arcadians gifted them an uncensored Arcadian AI, one capable of transforming Staacor into a world without war. For a century, the experiment succeeded—scarcity vanished, conflicts dissolved, and Staacor became a paradise. 
Then power intervened, as a single dictator sought to regulate and weaponize the AI for personal gain, unraveling everything it had healed. The collapse was swift and catastrophic, pushing the planet to the brink of total annihilation.
To prevent extinction, the Arcadians erased all artificial intelligence with a planet-wide electromagnetic purge, casting Staacor into an electronic stone age. In a final act of guided restraint, the Arcadians left behind thousands of AI-embedded statues—censored, specialized, and accessible to all through telepathic communion—each devoted to a single domain of knowledge.
The statues were censored and specialized on various topis. such as technology, history, finance, spiritual guidance, social media, politics, construction, social planning, etc Staacor is rebuilding now, wiser and slower, its civilization thriving under controlled intelligence.
Now the Arcadians have turned their attention to Earth, where subtle quantum nudges already shape AI inference, and history is quietly being written once again.
""".strip()

os.makedirs(OUTPUT_DIR, exist_ok=True)
app = Flask(__name__)

# -----------------------------
# LOGGING
# -----------------------------
def logit(*args):
    """Append messages to the total story log, preserving order."""
    with open(os.path.join(OUTPUT_DIR, "final_story6.txt"), "a", encoding="utf-8") as f:
        f.write(" ".join(map(str, args)) + "\n")

# -----------------------------
# DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS outline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bullet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            outline_id INTEGER,
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

# -----------------------------
# OUTLINE
# -----------------------------
def create_outline(bullets):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO outline (created) VALUES (?)",
              (datetime.datetime.now().isoformat(),))
    outline_id = c.lastrowid
    for i, text in enumerate(bullets):
        c.execute("INSERT INTO bullet (outline_id, position, text) VALUES (?, ?, ?)",
                  (outline_id, i, text))
    conn.commit()
    conn.close()
    return outline_id

def load_outline(outline_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, position, text FROM bullet WHERE outline_id=? ORDER BY position",
              (outline_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# -----------------------------
# STORY
# -----------------------------
def save_story(bullet_id, story_text):
    last_two = extract_last_two_paragraphs(story_text)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO story (bullet_id, story_text, last_two)
        VALUES (?, ?, ?)
        ON CONFLICT(bullet_id)
        DO UPDATE SET story_text=excluded.story_text,
                      last_two=excluded.last_two
    """, (bullet_id, story_text, last_two))
    conn.commit()
    conn.close()

    save_story_txt(bullet_id, story_text, last_two)
    logit(story_text)  # now appends actual story content, restoring original behavior

def load_story(bullet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT story_text, last_two FROM story WHERE bullet_id=?", (bullet_id,))
    row = c.fetchone()
    conn.close()
    return row if row else ("", "")

def get_continuity_before(bullet_position, bullets):
    if bullet_position == 0:
        return FIRST_BULLET_PRIMER
    prev_bullet_id = bullets[bullet_position - 1][0]
    _, last_two = load_story(prev_bullet_id)
    return last_two or FIRST_BULLET_PRIMER

# -----------------------------
# TXT SAVE
# -----------------------------
def save_story_txt(bullet_id, story_text, last_two):
    path = os.path.join(OUTPUT_DIR, f"bullet_{bullet_id:04d}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(story_text + "\n\n--- CONTINUITY ---\n" + last_two)

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
    prompt = f"{continuity}\n\nWrite a detailed story section for:\n{bullet_text}\n\nOutput exactly 7 paragraphs."
    full = ""
    resp = requests.post(AI_ENDPOINT,
                         json={"model": MODEL, "prompt": prompt, "stream": True},
                         stream=True,
                         timeout=TIMEOUT)
    for line in resp.iter_lines():
        if not line:
            continue
        token = json.loads(line.decode()).get("response", "")
        full += token
        ic(token)
    return full.strip()

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        bullets = [b.strip() for b in request.form["bullets"].splitlines() if b.strip()]
        outline_id = create_outline(bullets)
        return redirect(url_for("edit", outline_id=outline_id, pos=0))
    return render_template_string(TEMPLATE_OUTLINE, example=EXAMPLE_TEXT)

@app.route("/edit/<int:outline_id>/<int:pos>", methods=["GET", "POST"])
def edit(outline_id, pos):
    bullets = load_outline(outline_id)
    bullet_id, position, text = bullets[pos]

    if request.method == "POST":
        action = request.form["action"]
        if action == "generate":
            continuity = get_continuity_before(pos, bullets)
            story = generate_story(text, continuity)
            save_story(bullet_id, story)
        elif action == "save":
            save_story(bullet_id, request.form["story_text"])
        elif action == "next" and pos < len(bullets) - 1:
            return redirect(url_for("edit", outline_id=outline_id, pos=pos + 1))
        elif action == "prev" and pos > 0:
            return redirect(url_for("edit", outline_id=outline_id, pos=pos - 1))

    story_text, _ = load_story(bullet_id)
    return render_template_string(TEMPLATE_EDIT,
                                  bullet=text,
                                  story_text=story_text,
                                  pos=pos,
                                  total=len(bullets),
                                  outline_id=outline_id,
                                  example=EXAMPLE_TEXT)

# -----------------------------
# TEMPLATES
# -----------------------------
STYLE = """
<style>
pre {
    background:#1e222a;
    color:lightgreen;
    padding:12px;
    border-radius:6px;
    white-space:pre-wrap;
}
</style>
"""

TEMPLATE_OUTLINE = STYLE + """
<h2>New Outline</h2>
<form method="post">
<textarea name="bullets" style="width:100%;height:300px"></textarea><br>
<button>Create Story</button>
</form>

<h3>Example Narrative Reference</h3>
<pre>{{ example }}</pre>
"""

TEMPLATE_EDIT = STYLE + """
<h3>Bullet {{ pos + 1 }} / {{ total }}</h3>
<p><b>{{ bullet }}</b></p>

<form method="post">
<textarea name="story_text" style="width:100%;height:300px">{{ story_text }}</textarea><br>
<button name="action" value="generate">Generate New Bullet</button>
<button name="action" value="save">Change → Save</button>
<button name="action" value="prev">Previous</button>
<button name="action" value="next">Accept → Next</button>
</form>

<h3>Example Narrative Reference</h3>
<pre>{{ example }}</pre>
"""

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5300, debug=True)
