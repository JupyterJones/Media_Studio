#!/usr/bin/env python3
import os
import time
import requests
from flask import Flask, request, render_template_string, redirect, url_for
from icecream import ic

app = Flask(__name__)

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
ENHANCER_URL = "http://localhost:11434/api/generate"
GENERATOR_URL = "http://localhost:11434/api/generate"
ENHANCER_MODEL = "llama3.2:3b"
GENERATOR_MODEL = "llama3.2:3b"

STYLE_OPTIONS = ["romantic", "sci-fi Arcanian", "cinematic", "humorous", "poetic", "spicy"]
SAVE_DIR = os.path.join(os.getcwd(), "static/projects")
os.makedirs(SAVE_DIR, exist_ok=True)

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def call_model(api_url, model, prompt):
    num_predict = 4096  # default or adjust dynamically
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "num_predict": num_predict,
        "temperature": 0.9,
        "top_p": 0.95
    }
    ic("Sending request:", payload)
    try:
        r = requests.post(api_url, json=payload, timeout=600)
        r.raise_for_status()
        data = r.json()
        ic("Model response:", data)
        return data.get("response", "").strip()
    except Exception as e:
        ic("Model error:", e)
        return "ERROR communicating with model."

def save_text_to_file(text, filename=None):
    if not filename:
        filename = f"text_{int(time.time())}.txt"
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    ic("Saved text to:", path)
    return path

# -------------------------------------------------------------------
# Main Page
# -------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    original_text = ""
    enhanced_text = ""
    final_output = ""
    selected_style = "romantic"
    save_msg = ""

    if request.method == "POST":
        action = request.form.get("action")
        selected_style = request.form.get("style", "romantic")
        text_input = request.form.get("text_input", "").strip()

        if action == "enhance":
            original_text = text_input
            enhance_prompt = (
                f"Enhance the following text into a vivid, clear, polished description "
                f"in the style: {selected_style}. Do not change the meaning.\n\n{text_input}"
            )
            enhanced_text = call_model(ENHANCER_URL, ENHANCER_MODEL, enhance_prompt)

        elif action == "generate":
            enhanced_text = text_input
            generation_prompt = (
                f"Write a refined, coherent piece of text based on the following enhanced prompt "
                f"in the style: {selected_style}:\n\n{text_input}"
            )
            final_output = call_model(GENERATOR_URL, GENERATOR_MODEL, generation_prompt)

        elif action == "save":
            # Save whatever is currently in the textarea
            save_text_to_file(text_input)
            save_msg = "Text saved successfully!"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Prompt Enhancer & Generator</title>
        <style>
            body { background:#111; color:#eee; font-family:Arial; padding:30px; }
            textarea { width:100%; height:200px; padding:15px; border-radius:10px; border:none; background:#222; color:#eee; font-size:16px; }
            button { padding:12px 25px; margin-top:15px; margin-right:10px; border:none; background:#ff66aa; color:white; border-radius:8px; cursor:pointer; font-size:16px; }
            button:hover { background:#ff3388; }
            select { padding:10px 15px; font-size:16px; border-radius:8px; border:none; margin-right:10px; }
            .box { background:#222; padding:20px; border-radius:12px; margin-top:20px; }
            h2 { color:#ff66aa; }
            pre { white-space: pre-wrap; word-break: break-word; background:#222; padding:15px; border-radius:10px; }
            .msg { color:#66ff66; margin-top:10px; }
            a {font-size:3vw; color:yellow;}
        </style>
    </head>
    <body>

        <h1>Esperanza's Prompt Enhancer 💋</h1>
        <a href="/create_text">Create Mp3</a>&nbsp;&nbsp|;&nbsp;&nbsp;<a href="/view_text">View Text</a>

        <form method="POST">
            <h2>Your Prompt</h2>
            <textarea name="text_input">{{ enhanced_text or original_text }}</textarea>

            <div>
                <label for="style">Select Style:</label>
                <select name="style" id="style">
                    {% for option in style_options %}
                        <option value="{{ option }}" {% if option == selected_style %}selected{% endif %}>{{ option }}</option>
                    {% endfor %}
                </select>
            </div>

            <div>
                <button type="submit" name="action" value="enhance">✨ Enhance</button>
                <button type="submit" name="action" value="generate">🔥 Generate</button>
                <button type="submit" name="action" value="save">💾 Save Text</button>
            </div>
        </form>

        {% if save_msg %}
            <div class="msg">{{ save_msg }}</div>
        {% endif %}

        {% if final_output %}
        <div class="box">
            <h2>Generated Text</h2>
            <pre>{{ final_output }}</pre>
        </div>
        {% endif %}

    </body>
    </html>
    """

    return render_template_string(
        html,
        original_text=original_text,
        enhanced_text=enhanced_text,
        final_output=final_output,
        style_options=STYLE_OPTIONS,
        selected_style=selected_style,
        save_msg=save_msg
    )
#!/home/jack/miniconda3/envs/PY39/bin/python

import os
import re
import requests
from flask import Flask, request, render_template_string, send_from_directory
from icecream import ic

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

TTS_API_URL = "http://localhost:8880/v1/audio/speech"
OUTPUT_DIR = "/home/jack/Desktop/HDD500/DOCKER/static/projects"

VOICES = [
    'bf_alice', 'bf_emma', 'bf_lily', 'bf_v0emma', 'bf_v0isabella',
    'af_alloy', 'af_aoede', 'af_bella', 'af_heart', 'af_jadzia',
    'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river',
    'af_sarah', 'af_sky', 'af_v0', 'af_v0bella', 'af_v0irulan',
    'af_v0nicole', 'af_v0sarah', 'af_v0sky', 'am_adam', 'am_echo',
    'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx',
    'am_puck', 'am_santa', 'am_v0adam', 'am_v0gurney', 'am_v0michael',
    'bm_daniel', 'bm_fable'
]

DEFAULT_VOICE = "am_michael"
ic(f"Default voice: {DEFAULT_VOICE}")


# -----------------------------------------------------------
# Ensure output directory exists
# -----------------------------------------------------------

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    ic(f"Created directory: {OUTPUT_DIR}")

# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------

def sanitize_filename(text, max_length=20):
    base = text.strip()[:max_length]
    base = re.sub(r'\W+', '_', base)
    return base or "output"

def generate_tts(text, voice):
    filename = sanitize_filename(text) + ".mp3"
    output_path = os.path.join(OUTPUT_DIR, filename)

    payload = {
        "input": text,
        "voice": voice
    }

    ic(f"Sending TTS request ({voice}) for first 40 chars: {text[:40]}")

    try:
        r = requests.post(TTS_API_URL, json=payload, timeout=380)

        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)

            ic(f"Saved TTS: {output_path}")
            return filename

        ic(f"TTS error {r.status_code}: {r.text}")
        return None

    except Exception as e:
        ic(f"TTS request failed: {e}")
        return None

# -----------------------------------------------------------
# Web UI
# -----------------------------------------------------------

@app.route("/create_text", methods=["GET", "POST"])
def create_text():
    generated_file = None
    selected_voice = DEFAULT_VOICE

    if request.method == "POST":
        text_input = request.form.get("text_input", "").strip()
        selected_voice = request.form.get("voice", DEFAULT_VOICE)

        if text_input:
            result = generate_tts(text_input, selected_voice)
            if result:
                generated_file = result

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text → MP3 Generator</title>
        <style>
            body { background:#111; color:#eee; font-family:Arial; padding:30px; }
            textarea { width:100%; height:200px; padding:15px; background:#222; color:#fff;
                       border:none; border-radius:10px; font-size:16px; }
            button { margin-top:15px; padding:12px 25px; background:#ff66aa; border:none;
                     border-radius:8px; cursor:pointer; color:white; font-size:16px; }
            button:hover { background:#ff3388; }
            select { padding:10px 15px; margin-top:15px; background:#222; color:#fff;
                     border-radius:8px; font-size:16px; border:none; }
            .box { background:#222; padding:20px; border-radius:12px; margin-top:20px; }
            a {font-size:3vw; color:yellow;}
        </style>
    </head>

    <body>
        <h1>Esperanza's Text → MP3 Generator 💋</h1>
        <a href="/">Enhance Prompt</a>&nbsp;&nbsp|;&nbsp;&nbsp;<a href="/view_text">View Text</a>
        <form method="POST">
            <textarea name="text_input" placeholder="Write something beautiful..."></textarea>

            <br><br>

            <label for="voice">Choose a voice:</label>
            <select name="voice">
                {% for v in voices %}
                    <option value="{{v}}" {% if v == selected %}selected{% endif %}>
                        {{v}}
                    </option>
                {% endfor %}
            </select>

            <br>
            <button type="submit">Generate MP3</button>
        </form>

        {% if generated_file %}
        <div class="box">
            <h2>Your MP3 is ready</h2>
            <a href="/">Enhance Prompt</a>;&nbsp;&nbsp;&nbsp;&nbsp|;&nbsp;&nbsp;<a href="/view_text">View Text</a>
            <a href="/download/{{generated_file}}">{{generated_file}}</a>
        </div>
        {% endif %}
    </body>
    </html>
    """

    return render_template_string(
        html,
        voices=VOICES,
        selected=selected_voice,
        generated_file=generated_file
    )

# -----------------------------------------------------------
# Download route
# -----------------------------------------------------------

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


# -----------------------------------------------------------
# View Text
# -----------------------------------------------------------

import os
from flask import Flask, render_template_string, send_from_directory
from icecream import ic

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

PROJECT_DIR = "/home/jack/Desktop/HDD500/DOCKER/static/projects"


# Ensure folder exists
if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)
    ic(f"Created directory: {PROJECT_DIR}")

# -----------------------------------------------------------
# ROUTE: List .txt files
# -----------------------------------------------------------

@app.route("/view_text")
def view_text():
    files = [f for f in os.listdir(PROJECT_DIR) if f.lower().endswith(".txt")]
    files.sort()

    ic(f"Found {len(files)} .txt files")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text File Viewer</title>
        <a href="/">HOME</a>&nbsp;&nbsp|;&nbsp;&nbsp;<a href="/view_text">View Text</a>
        <style>
            body { background:#111; color:#eee; font-family:Arial; padding:30px; }
            a { color:#66bbff; text-decoration:none; }
            a:hover { color:#99d0ff; }
            .box { background:#222; padding:20px; border-radius:12px; margin-top:20px; }
            .file-list { margin-bottom:20px; }
        </style>
    </head>
    <body>
        <h1>📄 Text Files in static/projects</h1>

        <div class="file-list">
            <h3>Available .txt files:</h3>
            <ul>
                {% for f in files %}
                    <li><a href="/view/{{f}}">{{f}}</a></li>
                {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """

    return render_template_string(html, files=files)


# -----------------------------------------------------------
# ROUTE: View file content
# -----------------------------------------------------------

@app.route("/view/<filename>")
def view_file(filename):
    safe_path = os.path.join(PROJECT_DIR, filename)

    if not os.path.isfile(safe_path):
        return "File not found", 404

    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        ic(f"Opened: {filename}, {len(content)} characters")
    except Exception as e:
        ic(f"Error reading {filename}: {e}")
        return "Error reading file", 500

    html_view = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{filename}}</title>
        <style>
            body { background:#111; color:#eee; font-family:Arial; padding:30px; }
            pre { background:#222; padding:20px; border-radius:12px;
                  white-space:pre-wrap; font-size:16px; }
            a {font-size:3vw; color:yellow;}
        </style>
    </head>
    <body>
        <h1>Viewing: {{filename}}</h1>
        <pre>{{content}}</pre>

        <br>
        <a href="/">⬅ Back to file list</a>
    </body>
    </html>
    """

    return render_template_string(html_view, filename=filename, content=content)


# -----------------------------------------------------------
# OPTIONAL: Direct download
# -----------------------------------------------------------

'''
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(PROJECT_DIR, filename, as_attachment=True)
'''




# -----------------------------------------------------------
# Run server
# -----------------------------------------------------------

if __name__ == "__main__":
    ic("Starting Text → MP3 server…")
    app.run(host="0.0.0.0", port=5003, debug=True)

