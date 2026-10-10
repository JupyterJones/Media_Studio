from flask import Flask, render_template_string, request, redirect, send_file, session, Response, flash, url_for
import os
import uuid
import shutil
import subprocess
import requests
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image
from pydub import AudioSegment
from icecream import ic
from werkzeug.utils import secure_filename
from random import randint

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'

#IMAGE_FOLDER = 'static/images/AI_images'
#AUDIO_FOLDER = 'static/images/AI_images'
#OUTPUT_FOLDER = 'static/images/AI_images'

IMAGE_FOLDER = 'static/stitch'
AUDIO_FOLDER = 'static/images/AI_images'
OUTPUT_FOLDER = 'static/images/AI_images'
FRAME_PATH = 'static/assets/talks.png'

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

UNIQUE = str(randint(111111, 999999))
TARGET_SIZE = (512, 768)
from flask import Flask, render_template_string, request, redirect, send_file, session, render_template_string, Response, flash, url_for
import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image
from pydub import AudioSegment
from icecream import ic
from werkzeug.utils import secure_filename
from random import randint
app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'
#IMAGE_FOLDER = 'static/images/AI_images'
#AUDIO_FOLDER = 'static/images/AI_images'
#OUTPUT_FOLDER = 'static/images/AI_images'
#FRAME_PATH = 'static/assets/talks.png'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
UNIQUE =str(randint(111111,999999))
TARGET_SIZE = (512, 768)

# Resize all images
def resize_all_images():
    ic("Starting image resizing...")
    if not os.path.exists(IMAGE_FOLDER):
        ic(f"Image folder not found: {IMAGE_FOLDER}")
        return

    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for filename in image_files:
        image_path = os.path.join(IMAGE_FOLDER, filename)
        try:
            with Image.open(image_path) as img:
                resized_img = img.resize(TARGET_SIZE, Image.LANCZOS)
                resized_img.save(image_path)
        except Exception as e:
            ic(f"Error processing {filename}: {e}")

resize_all_images()

# HTML template with numbered inputs for ordering
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Create Video</title>
<style>
body { font-family: Arial; background-color: #1e1e1e; color: white; text-align: center; }
.images-container, .audio-container { margin-top: 20px; }
.image-option, .audio-option { display: inline-block; margin: 10px; border: 2px solid #333; padding: 5px; transition: transform 0.3s ease; }
.image-option img { width: 150px; height: auto; object-fit: cover; }
.image-option:hover, .audio-option:hover { transform: scale(1.05); }
button { background-color: #4CAF50; color: white; padding: 10px 20px; margin-top: 20px; border: none; cursor: pointer; font-size: 16px; }
.button { background-color: #4CAF50; color: white; padding: 10px 20px; margin-top: 20px; border: none; cursor: pointer; font-size: 16px; }
button:hover { background-color: #45a049; }
.audio-player { margin: 10px; padding: 10px; background-color: #333; border-radius: 5px; display: inline-block; text-align: center; }
</style>
</head>
<body>
<div class="container">
<h1>Select Images and Audio</h1>
<a href = "/text_to_mp3" class="button">Create MP2</a>
<p>File Location: /static/images/AI_images/</p>
<form action="/create_video" method="POST" enctype="multipart/form-data">
<div class="images-container">
<h3>Select exactly 7 images and specify their sequence (1-7):</h3>
{% for image in images %}
<label class="image-option">
<img src="{{ url_for('static', filename='/stitch/' + image) }}" alt="{{ image }}">
<br>
<input type="checkbox" name="images" value="{{ image }}"> Select
<br>
Sequence:
<input type="number" name="sequence_{{ image }}" min="1" max="7">
</label>
{% endfor %}
</div>
<div class="audio-container">
<h3>Select audio:</h3>
{% for mp3 in mp3s %}
<label class="audio-option">
<input type="radio" name="audio" value="{{ mp3 }}">
<div class="audio-player">
<p>{{ mp3 }}</p>
<audio controls>
<source src="{{ url_for('static', filename='images/AI_images/' + mp3) }}" type="audio/mp3">
Your browser does not support audio.
</audio>
</div>
</label>
{% endfor %}
</div>
<button type="submit">Create Video</button>
</form>
</div>
</body>
</html>
"""

@app.route('/')
def index():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg','.jpeg','.png'))]
    mp3s = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.mp3')]
    return render_template_string(HTML, images=images, mp3s=mp3s)

def overlay_frame(image_path, frame_path, output_path):
    base = Image.open(image_path).convert("RGBA")
    frame = Image.open(frame_path).convert("RGBA").resize(base.size)
    combined = Image.alpha_composite(base, frame)
    combined.convert("RGB").save(output_path, "JPEG")

def pad_audio_with_silence(audio_path, output_path, pad_duration_ms=250):
    original = AudioSegment.from_mp3(audio_path)
    silence = AudioSegment.silent(duration=pad_duration_ms)
    padded = silence + original + silence
    padded.export(output_path, format="mp3")

@app.route('/create_video', methods=['POST'])
def create_video():
    selected_images = request.form.getlist('images')
    selected_audio = request.form.get('audio')
    ic(selected_images, selected_audio)

    if len(selected_images) != 7:
        return "Please select exactly 7 images.", 400

    # Order images by the sequence input
    image_sequence = []
    for img in selected_images:
        seq_val = request.form.get(f"sequence_{img}")
        if not seq_val:
            return f"Missing sequence number for {img}", 400
        image_sequence.append((int(seq_val), img))

    # Sort images by sequence number
    sorted_images = [img for _, img in sorted(image_sequence, key=lambda x: x[0])]
    ic(sorted_images)

    frame_exists = os.path.exists(FRAME_PATH)
    processed_paths = []

    for i, image_name in enumerate(sorted_images):
        src = os.path.join(IMAGE_FOLDER, image_name)
        output_img = os.path.join(OUTPUT_FOLDER, f"processed_{i}.jpg")
        if frame_exists:
            overlay_frame(src, FRAME_PATH, output_img)
        else:
            Image.open(src).convert("RGB").save(output_img, "JPEG")
        processed_paths.append(output_img)

    original_audio_path = os.path.join(AUDIO_FOLDER, secure_filename(selected_audio))
    padded_audio_path = os.path.join(OUTPUT_FOLDER, "temp_audio.mp3")
    pad_audio_with_silence(original_audio_path, padded_audio_path)

    audio_clip = AudioFileClip(padded_audio_path)
    total_duration = audio_clip.duration
    image_duration = total_duration / len(processed_paths)

    clips = [ImageClip(path).set_duration(image_duration) for path in processed_paths]
    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)

    output_video_path = os.path.join(f"{OUTPUT_FOLDER}/{UNIQUE}final_video.mp4")
    try:
        final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac', fps=24)
        return redirect(f"/{output_video_path}")
    except Exception as e:
        ic(e)
        return "Error creating video."

@app.route('/static/f"{OUTPUT_FOLDER}/{UNIQUE}{final_video.mp4}"')
def serve_video():
    return send_file(os.path.join(f"{OUTPUT_FOLDER}/{UNIQUE}final_video.mp4"), mimetype='video/mp4')


# --------------------------------------------------
# IMAGE RESIZE
# --------------------------------------------------
def resize_all_images():
    ic("Starting image resizing...")
    if not os.path.exists(IMAGE_FOLDER):
        return

    for f in os.listdir(IMAGE_FOLDER):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            p = os.path.join(IMAGE_FOLDER, f)
            try:
                with Image.open(p) as img:
                    img.resize(TARGET_SIZE, Image.LANCZOS).save(p)
            except Exception as e:
                ic("Resize error:", e)

resize_all_images()

# --------------------------------------------------
# KOKORO TTS CONFIG
# --------------------------------------------------
KOKORO_TTS_URL = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE = "af_bella"

def generate_mp3_with_kokoro_tts(text_to_speak, output_mp3_path, voice=ASSISTANT_VOICE):
    try:
        os.makedirs(os.path.dirname(output_mp3_path), exist_ok=True)

        clean_text = (
            text_to_speak.replace("*", "")
            .replace("…", ", ")
            .strip()
        )

        payload = {
            "model": "kokoro",
            "voice": voice,
            "format": "mp3",
            "input": clean_text
        }

        ic("Sending to Kokoro:", payload)

        r = requests.post(KOKORO_TTS_URL, json=payload, timeout=60)

        if r.status_code != 200:
            return None, f"Kokoro error {r.status_code}: {r.text}"

        with open(output_mp3_path, "wb") as f:
            f.write(r.content)

        ic("MP3 saved:", output_mp3_path)
        return output_mp3_path, None

    except Exception as e:
        ic("Kokoro exception:", e)
        return None, str(e)

# --------------------------------------------------
# SERVE GENERATED MP3
# --------------------------------------------------
@app.route('/audio/<filename>')
def serve_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), mimetype="audio/mpeg")

# --------------------------------------------------
# TEXT → MP3 PAGE
# --------------------------------------------------
HTML_MP3 = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Kokoro TTS</title>
<style>
body { background:#121212; color:#eee; font-family:Arial; padding:20px; }
textarea { width:100%; height:200px; background:#222; color:#fff; padding:10px; }
button { padding:10px 20px; margin-top:10px; }
a { color:orange; font-size:18px; }
</style>
</head>
<body>

<h1>🗣️ Kokoro TTS — Text to MP3</h1>
<a href="/">HOME</a>

<form method="post">
<textarea name="text">{{ text }}</textarea><br>
<button type="submit">Generate MP3</button>
</form>

{% if mp3_file %}
<hr>
<audio controls>
<source src="{{ url_for('serve_file', filename=mp3_file) }}" type="audio/mpeg">
</audio>
<p>{{ mp3_file }}</p>
{% endif %}

</body>
</html>
"""

@app.route("/text_to_mp3", methods=["GET", "POST"])
def text_to_mp3():
    mp3_file = None
    text = ""

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Enter text")
            return redirect(url_for("text_to_mp3"))

        safe = "_".join(text[:20].split())
        mp3_file = f"{safe}.mp3"
        mp3_path = os.path.join(OUTPUT_FOLDER, mp3_file)

        result, error = generate_mp3_with_kokoro_tts(text, mp3_path)
        if error:
            flash(error)
            mp3_file = None

    return render_template_string(HTML_MP3, mp3_file=mp3_file, text=text)

# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5100)
