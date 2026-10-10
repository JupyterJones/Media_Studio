#!/usr/bin/env python3
import os
import requests
import random
from random import randint
from flask import (
    Flask,
    render_template_string,
    request,
    send_file,
    url_for
)

from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, vfx
from PIL import Image
from pydub import AudioSegment
from werkzeug.utils import secure_filename
from icecream import ic

app = Flask(__name__)
app.secret_key = "super_secret_key_here"

VOICES = [
    'bf_alice','bf_emma','bf_lily','bf_v0emma','bf_v0isabella',
    'af_alloy','af_aoede','af_bella','af_heart','af_jadzia',
    'af_jessica','af_kore','af_nicole','af_nova','af_river',
    'af_sarah','af_sky','af_v0','af_v0bella','af_v0irulan',
    'af_v0nicole','af_v0sarah','af_v0sky',
    'am_adam','am_echo','am_eric','am_fenrir','am_liam',
    'am_michael','am_onyx','am_puck','am_santa',
    'am_v0adam','am_v0gurney','am_v0michael',
    'bm_daniel','bm_fable','bm_george','bm_lewis',
    'bm_v0george','bm_v0lewis',
    'ef_dora','em_alex','em_santa'
]

DEFAULT_VOICE = "am_echo"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SHARED_PATH = os.path.join(BASE_DIR, "static", "images")
FRAME_PATH = os.path.join(BASE_DIR, "static", "assets", "talks.png")
VIDEO_DIR = os.path.join(BASE_DIR,  "static", "videos")
MP3_DIR = os.path.join(BASE_DIR,  "static", "mp3s")

os.makedirs(SHARED_PATH, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(MP3_DIR, exist_ok=True)

UNIQUE = str(randint(100000, 999999))

def get_subdirs():
    dirs = []
    for d in os.listdir(SHARED_PATH):
        full = os.path.join(SHARED_PATH, d)
        if os.path.isdir(full):
            dirs.append(d)
    return sorted(dirs)

# --------------------------------------------------
# HTML TEMPLATE
# --------------------------------------------------
HTML_TEMPLATE = """
<!doctype html>
<html>
<body style="background:#111;color:#eee;text-align:center; font-family: sans-serif;">

<h2>Select Folder</h2>
<a href="/text_to_mp3" style="color:orange;font-size:20px;">TEXT → MP3</a>
<form method="get">
<select name="folder">
{% for d in dirs %}
<option value="{{d}}" {% if d == current %}selected{% endif %}>{{d}}</option>
{% endfor %}
</select>
<button>LOAD</button>
</form>

<form method="post" action="/create_video">
<h2>Step 1: Select Images & Sequence</h2>
<div style="display:flex; flex-wrap:wrap; gap:10px; justify-content:center;">
{% for img in images %}
    <div style="width:180px; border:1px solid #444; padding:10px; background:#222; border-radius:8px;">
        <img src="{{ url_for('static', filename='images/' + current + '/' + img) }}" style="width:100%; border-radius:4px;">
        <div style="margin-top:8px;">
            <input type="checkbox" name="images" value="{{ img }}"> Use
            <br>
            Seq: <input type="number" name="seq_{{ img }}" style="width:50px;" placeholder="0">
        </div>
    </div>
{% endfor %}
</div>

<h2>Step 2: Select Audio</h2>
<div style="background:#222; padding:20px; display:inline-block; border-radius:8px;">
{% for mp3 in mp3s %}
<div style="text-align:left; margin-bottom:5px;">
    <input type="radio" name="audio" value="{{ mp3 }}" required> {{ mp3 }}
</div>
{% endfor %}
</div>

<input type="hidden" name="folder" value="{{current}}">
<br><br>
<button style="padding:15px 30px; font-size:18px; background:green; color:white; border:none; border-radius:5px; cursor:pointer;">
    Create Video with Random Transitions
</button>
</form>
</body>
</html>
"""

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def overlay_frame(src, frame, out):
    base = Image.open(src).convert("RGBA")
    frame = Image.open(frame).convert("RGBA").resize(base.size)
    Image.alpha_composite(base, frame).convert("RGB").save(out)

def pad_audio(src, out, ms=250):
    audio = AudioSegment.from_mp3(src)
    silence = AudioSegment.silent(duration=ms)
    (silence + audio + silence).export(out, format="mp3")

# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.route("/mp3/<filename>")
def serve_mp3(filename):
    return send_file(os.path.join(MP3_DIR, filename), mimetype="audio/mpeg")

@app.route("/")
def index():
    dirs = get_subdirs()
    current = request.args.get("folder", dirs[0] if dirs else "")
    folder_path = os.path.join(SHARED_PATH, current)
    images = []
    mp3s = []
    if os.path.exists(folder_path):
        for f in os.listdir(folder_path):
            if f.lower().endswith((".png",".jpg",".jpeg")):
                images.append(f)
    for f in os.listdir(MP3_DIR):
        if f.lower().endswith(".mp3"):
            mp3s.append(f)
    return render_template_string(HTML_TEMPLATE, dirs=dirs, images=images, mp3s=mp3s, current=current)

@app.route("/create_video", methods=["POST"])
def create_video():
    folder = request.form.get("folder")
    base_path = os.path.join(SHARED_PATH, folder)
    selected_images = request.form.getlist("images")
    selected_audio = request.form.get("audio")

    if not selected_images or not selected_audio:
        return "Please select at least one image and one audio file.", 400

    # Sort images by sequence
    ordered = []
    for img in selected_images:
        seq = request.form.get(f"seq_{img}")
        val = int(seq) if seq and seq.isdigit() else 0
        ordered.append((val, img))
    ordered_images = [x[1] for x in sorted(ordered)]

    # Prepare Image Paths
    processed_paths = []
    for i, img in enumerate(ordered_images):
        src = os.path.join(base_path, img)
        out = os.path.join(base_path, f"_tmp_{i}.jpg")
        if os.path.exists(FRAME_PATH):
            overlay_frame(src, FRAME_PATH, out)
        else:
            Image.open(src).convert("RGB").save(out)
        processed_paths.append(out)

    # Audio Logic
    audio_src = os.path.join(MP3_DIR, secure_filename(selected_audio))
    padded_audio_path = os.path.join(MP3_DIR, f"temp_pad_{UNIQUE}.mp3")
    pad_audio(audio_src, padded_audio_path)
    audio_clip = AudioFileClip(padded_audio_path)

    # TRANSITION SETTINGS
    # Crossfade duration
    cross_dur = 0.6 
    num_clips = len(processed_paths)
    
    # Calculate duration per clip so the total video matches audio length
    # Total Video Duration = (clip_dur * num_clips) - (cross_dur * (num_clips - 1))
    # Solving for clip_dur:
    clip_dur = (audio_clip.duration + (cross_dur * (num_clips - 1))) / num_clips

    clips = []
    for i, path in enumerate(processed_paths):
        clip = ImageClip(path).set_duration(clip_dur)
        
        # 1. Apply Random "Flavor" Effects to the clip itself
        flavor = random.choice(['none', 'mirror', 'invert'])
        if flavor == 'mirror':
            clip = clip.fx(vfx.mirror_x)
        
        # 2. Apply Random Entry Transitions
        # Note: Transitions are applied to all clips except the first
        if i > 0:
            trans_type = random.choice(['crossfade', 'slide_in'])
            if trans_type == 'crossfade':
                clip = clip.crossfadein(cross_dur)
            else:
                # Basic slide animation (from left)
                clip = clip.set_position(lambda t: (min(0, -100 + (100/cross_dur)*t), 'center'))
                clip = clip.crossfadein(cross_dur)

        clips.append(clip)

    # Combine with Padding (negative padding creates the overlap for crossfades)
    # method="compose" is vital for transparency and overlaps
    final_video_clip = concatenate_videoclips(clips, method="compose", padding=-cross_dur)
    
    # Final cleanup to ensure length matches audio exactly
    final_video_clip = final_video_clip.set_duration(audio_clip.duration).set_audio(audio_clip)

    final_output_name = f"video_{UNIQUE}.mp4"
    final_video_path = os.path.join(VIDEO_DIR, final_output_name)

    final_video_clip.write_videofile(
        final_video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=f'temp-audio-{UNIQUE}.m4a',
        remove_temp=True
    )

    return send_file(final_video_path, mimetype="video/mp4")

# --------------------------------------------------
# TTS LOGIC
# --------------------------------------------------
KOKORO_URL = "http://localhost:8880/v1/audio/speech"

def generate_kokoro_mp3(text, out, voice=DEFAULT_VOICE):
    payload = {"model": "kokoro", "voice": voice, "format": "mp3", "input": text.strip()}
    try:
        r = requests.post(KOKORO_URL, json=payload, timeout=800)
        with open(out, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"TTS Error: {e}")

@app.route("/text_to_mp3", methods=["GET","POST"])
def text_to_mp3():
    mp3 = None
    text = ""
    selected_voice = DEFAULT_VOICE
    if request.method == "POST":
        text = request.form.get("text","")
        selected_voice = request.form.get("voice",DEFAULT_VOICE)
        safe = "_".join(text[:20].split())
        mp3_name = f"{safe}_{randint(100,999)}.mp3"
        out = os.path.join(MP3_DIR, mp3_name)
        generate_kokoro_mp3(text, out, selected_voice)
        mp3 = mp3_name

    return render_template_string("""
    <body style="background:#111;color:#eee;text-align:center; font-family:sans-serif;">
    <h2>Kokoro TTS</h2>
    <a href="/" style="color:orange;">← Back to Video Creator</a><br><br>
    <form method="post">
        <textarea name="text" style="width:60%;height:120px; background:#222; color:white; border:1px solid #444;">{{text}}</textarea><br><br>
        <select name="voice">
        {% for v in voices %}
            <option value="{{v}}" {% if v == selected_voice %}selected{% endif %}>{{v}}</option>
        {% endfor %}
        </select>
        <br><br>
        <button style="padding:10px 20px;">Generate MP3</button>
    </form>
    {% if mp3 %}
        <h3>Preview</h3>
        <audio controls autoplay>
            <source src="/mp3/{{mp3}}">
        </audio>
    {% endif %}
    </body>
    """, text=text, voices=VOICES, selected_voice=selected_voice, mp3=mp3)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
"""

### Key Changes Made:
1.  **Math for Transitions:** Added a formula to calculate `clip_dur`. Because transitions "overlap" clips, each individual clip needs to be slightly longer than the simple math of `audio / count` to avoid the video ending too early.
2.  **`concatenate_videoclips(padding=-cross_dur, method="compose")`:** 
    *   **Padding:** A negative value tells MoviePy to start the next clip *before* the previous one ends.
    *   **Method:** "compose" allows clips to be layered (essential for the fade-in effect to work over the top of the previous image).
3.  **Randomization:** 
    *   The code now randomly chooses between a standard **Crossfade** and a **Slide-in** (using a lambda function for position) for every image change.
    *   It also randomly mirrors some images to make the visual flow feel more dynamic.
4.  **UI Improvements:** Added a bit of styling to the HTML template so the image grid and selection buttons are easier to use.
"""