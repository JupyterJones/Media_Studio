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

app = Flask(__name__)

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

@app.route("/", methods=["GET", "POST"])
def index():
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
            a { color:#66bbff; }
        </style>
    </head>

    <body>
        <h1>Esperanza's Text → MP3 Generator 💋</h1>

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
# Run server
# -----------------------------------------------------------

if __name__ == "__main__":
    ic("Starting Text → MP3 server…")
    app.run(host="0.0.0.0", port=5003, debug=True)
