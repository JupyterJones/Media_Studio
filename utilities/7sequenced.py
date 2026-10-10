from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    send_file,
    flash,
    url_for
)

import os
import requests
from random import randint

from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image
from pydub import AudioSegment
from werkzeug.utils import secure_filename
from icecream import ic

# --------------------------------------------------
# FLASK APP
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = "super_secret_key_here"

# --------------------------------------------------
# SINGLE SHARED PATH (REQUIRED BY EXTERNAL PROGRAM)
# --------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SHARED_PATH = os.path.join(
    BASE_DIR,
    "static",
    "images",
    "AI_images"
)

FRAME_PATH = os.path.join(BASE_DIR, "static", "assets", "talks.png")

TARGET_SIZE = (512, 768)
UNIQUE = str(randint(100000, 999999))

os.makedirs(SHARED_PATH, exist_ok=True)

ic("Using shared path:", SHARED_PATH)

# --------------------------------------------------
# IMAGE RESIZE (SAFE – IMAGES ONLY)
# --------------------------------------------------
def resize_ai_images():
    ic("Resizing images...")
    for f in os.listdir(SHARED_PATH):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            p = os.path.join(SHARED_PATH, f)
            try:
                with Image.open(p) as img:
                    img.resize(TARGET_SIZE, Image.LANCZOS).save(p)
            except Exception as e:
                ic("Resize error:", f, e)

resize_ai_images()

# --------------------------------------------------
# HTML UI
# --------------------------------------------------
HTML7 = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Video Builder</title>
<style>
body { background:#111; color:#eee; font-family:Arial; text-align:center; }
.box { display:inline-block; margin:10px; padding:10px; border:1px solid #333; }
img { width:150px; }
button { padding:10px 20px; margin-top:20px; }
a {font-size:2.5wv; color:orange;}
</style>
</head>
<body>

<h1>Shared Path Video Builder</h1>
<a href="/text_to_mp3">TEXTAREA TO MP3</a>
<p>{{ path }}</p>

<form method="post" action="/create_video">

<h2>Images</h2>
{% for img in images %}
<div class="box">
<img src="{{ url_for('static', filename='images/AI_images/' + img) }}"><br>
<input type="checkbox" name="images" value="{{ img }}"> use<br>
seq <input type="number" name="seq_{{ img }}" min="1" max="7">
</div>
{% endfor %}

<h2>Audio</h2>
{% for mp3 in mp3s %}
<div class="box">
<input type="radio" name="audio" value="{{ mp3 }}"><br>
{{ mp3 }}<br>
<audio controls>
<source src="{{ url_for('static', filename='images/AI_images/' + mp3) }}">
</audio>
</div>
{% endfor %}

<br>
<button type="submit">Create Video</button>
</form>

<hr>
<a href="/text_to_mp3">Text → MP3 (Kokoro)</a>

</body>
</html>
"""

# --------------------------------------------------
# HOME
# --------------------------------------------------
@app.route("/")
def index():
    images = []
    mp3s = []

    for f in os.listdir(SHARED_PATH):
        if f.lower().endswith((".jpg", ".png")):
            images.append(f)
        elif f.lower().endswith(".mp3"):
            mp3s.append(f)

    ic("Images:", images)
    ic("MP3s:", mp3s)

    return render_template_string(
        HTML7,
        images=images,
        mp3s=mp3s,
        path=SHARED_PATH
    )

# --------------------------------------------------
# IMAGE OVERLAY
# --------------------------------------------------
def overlay_frame(src, frame, out):
    base = Image.open(src).convert("RGBA")
    frame = Image.open(frame).convert("RGBA").resize(base.size)
    Image.alpha_composite(base, frame).convert("RGB").save(out)

# --------------------------------------------------
# AUDIO PAD
# --------------------------------------------------
def pad_audio(src, out, ms=250):
    ic("Padding audio:", src)
    audio = AudioSegment.from_mp3(src)
    silence = AudioSegment.silent(duration=ms)
    (silence + audio + silence).export(out, format="mp3")

# --------------------------------------------------
# CREATE VIDEO
# --------------------------------------------------
@app.route("/create_video", methods=["POST"])
def create_video():
    selected_images = request.form.getlist("images")
    selected_audio = request.form.get("audio")

    ic("Selected images:", selected_images)
    ic("Selected audio:", selected_audio)

    if len(selected_images) != 7:
        return "Select exactly 7 images", 400

    ordered = []
    for img in selected_images:
        seq = request.form.get(f"seq_{img}")
        if not seq:
            return f"Missing sequence for {img}", 400
        ordered.append((int(seq), img))

    ordered_images = [x[1] for x in sorted(ordered)]
    ic("Ordered images:", ordered_images)

    processed = []

    for i, img in enumerate(ordered_images):
        src = os.path.join(SHARED_PATH, img)
        out = os.path.join(SHARED_PATH, f"_frame_{i}.jpg")

        if os.path.exists(FRAME_PATH):
            overlay_frame(src, FRAME_PATH, out)
        else:
            Image.open(src).convert("RGB").save(out)

        processed.append(out)

    audio_src = os.path.join(SHARED_PATH, secure_filename(selected_audio))
    padded_audio = os.path.join(SHARED_PATH, "_audio_pad.mp3")

    pad_audio(audio_src, padded_audio)

    audio_clip = AudioFileClip(padded_audio)
    duration = audio_clip.duration / len(processed)

    clips = [ImageClip(p).set_duration(duration) for p in processed]
    final = concatenate_videoclips(clips).set_audio(audio_clip)

    final_video = os.path.join(
        SHARED_PATH,
        f"{UNIQUE}_final.mp4"
    )

    ic("Writing video:", final_video)

    final.write_videofile(
        final_video,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    return redirect(url_for(
        "serve_video",
        filename=os.path.basename(final_video)
    ))

# --------------------------------------------------
# SERVE VIDEO FROM SAME PATH
# --------------------------------------------------
@app.route("/video/<filename>")
def serve_video(filename):
    return send_file(
        os.path.join(SHARED_PATH, filename),
        mimetype="video/mp4"
    )

# --------------------------------------------------
# KOKORO TTS
# --------------------------------------------------
KOKORO_URL = "http://localhost:8880/v1/audio/speech"
VOICE = "af_bella"

def generate_kokoro_mp3(text, out):
    payload = {
        "model": "kokoro",
        "voice": VOICE,
        "format": "mp3",
        "input": text.strip()
    }

    ic("Kokoro payload:", payload)

    r = requests.post(KOKORO_URL, json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(r.text)

    with open(out, "wb") as f:
        f.write(r.content)

# --------------------------------------------------
# TEXT → MP3
# --------------------------------------------------
@app.route("/text_to_mp3", methods=["GET", "POST"])
def text_to_mp3():
    mp3 = None
    text = ""

    if request.method == "POST":
        text = request.form.get("text", "")
        safe = "_".join(text[:20].split())
        mp3 = f"{safe}.mp3"
        out = os.path.join(SHARED_PATH, mp3)
        generate_kokoro_mp3(text, out)

    return render_template_string("""
    <style>
    body { background:#111; color:#eee; font-family:Arial; text-align:center; }
    .box { display:inline-block; margin:10px; padding:10px; border:1px solid #333; }
    img { width:150px; }
    button { padding:10px 20px; margin-top:20px; }
    a {font-size:2.5wv; color:orange;}
    </style>
    <body>
    <h1>Kokoro TTS</h1>
    <a href="/">HOME</a>
    <form method="post">
    <textarea name="text" style="width:100%;height:200px;">{{text}}</textarea><br>
    <button>Generate</button>
    </form>

    {% if mp3 %}
    <audio controls>
    <source src="{{ url_for('static', filename='images/AI_images/' + mp3) }}">
    </audio>
    {% endif %}
    </body>
    """, mp3=mp3, text=text)

# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
