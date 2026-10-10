#!/home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/python
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


IMAGE_FOLDER = 'static/junk'
AUDIO_FOLDER = 'static/junk'
OUTPUT_FOLDER = 'static/junk'
FRAME_PATH = 'static/assets/ZOOMPAN.png'
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
                if img.size != TARGET_SIZE:
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
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --bg-base: #080b11;
            --bg-surface: #0f1524;
            --bg-card: rgba(22, 30, 49, 0.7);
            --bg-card-hover: rgba(29, 40, 65, 0.85);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(99, 102, 241, 0.15);
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --primary-glow: rgba(99, 102, 241, 0.4);
            
            --secondary: #8b5cf6;
            --secondary-hover: #7c3aed;
            
            --accent: #14b8a6;
            --accent-glow: rgba(20, 184, 166, 0.3);
            
            --success: #10b981;
            --danger: #ef4444;
            
            --radius-sm: 8px;
            --radius-md: 14px;
            --radius-lg: 20px;
            
            --shadow-sm: 0 2px 8px -2px rgba(0,0,0,0.5);
            --shadow-md: 0 10px 25px -5px rgba(0,0,0,0.6);
            --shadow-lg: 0 20px 40px -10px rgba(0,0,0,0.8);
            
            --transition-fast: 0.15s ease;
            --transition-normal: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 40%);
            background-attachment: fixed;
        }

        h1, h2, h3, h4 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        header {
            max-width: 440px; 
            width: 100%;
            margin-right: auto;
            margin-left: auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.25rem 2rem;
            background-color: rgba(15, 21, 36, 0.5);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            width: 2.25rem;
            height: 2.25rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            box-shadow: 0 0 15px var(--primary-glow);
        }

        .logo-text {
            font-size: 0.75rem;
            font-weight: 400;
            background: linear-gradient(to right, #ffffff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-badge {
            font-size: 0.60rem;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: rgba(99, 102, 241, 0.15);
            color: #a5b4fc;
            padding: 0.2rem 0.5rem;
            border-radius: 25px;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }

        main {
            display: flex;
            flex-direction: column;
            flex-grow: 1;
            max-width: 440px; 
            width: 100%;
            margin: 0 auto;
            gap: 1.5rem;
            padding: 1.5rem;
            height: auto;
            overflow-y: auto;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.25rem;
            box-shadow: var(--shadow-sm);
            transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            text-align: left;
        }

        .card:hover {
            border-color: var(--border-glow);
            box-shadow: var(--shadow-md);
        }

        .card-title {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: var(--text-primary);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.5rem;
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.75rem 1.25rem;
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 700;
            cursor: pointer;
            text-decoration: none;
            box-shadow: 0 4px 15px var(--primary-glow);
            transition: all var(--transition-normal);
            text-align: center;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }

        .btn:active {
            transform: translateY(1px);
        }
        
        .btn-accent {
            background: linear-gradient(135deg, var(--accent) 0%, #0d9488 100%);
            box-shadow: 0 4px 15px var(--accent-glow);
        }
        
        .btn-accent:hover {
            box-shadow: 0 6px 20px rgba(20, 184, 166, 0.5);
        }

        .btn-block {
            display: flex;
            width: 100%;
        }

        /* Image selection grids */
        .images-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-top: 1rem;
        }

        .image-card {
            display: flex;
            align-items: center;
            gap: 1rem;
            background: rgba(15, 21, 36, 0.6);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 0.75rem;
            cursor: pointer;
            transition: all var(--transition-fast);
        }

        .image-card:hover {
            border-color: var(--primary);
            background: rgba(29, 40, 65, 0.5);
        }

        .image-card img {
            width: 80px;
            height: 120px;
            object-fit: cover;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .image-controls {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .checkbox-container input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
            accent-color: var(--accent);
        }

        .sequence-input-container {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .sequence-input-container input[type="number"] {
            width: 60px;
            background-color: rgba(15, 21, 36, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            color: var(--text-primary);
            padding: 0.25rem 0.5rem;
            font-family: inherit;
            font-size: 0.85rem;
            outline: none;
            text-align: center;
        }

        .sequence-input-container input[type="number"]:focus {
            border-color: var(--primary);
        }

        /* Audio items */
        .audio-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .audio-card {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            background: rgba(15, 21, 36, 0.6);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 0.75rem;
            cursor: pointer;
            transition: all var(--transition-fast);
        }

        .audio-card:hover {
            border-color: var(--primary);
            background: rgba(29, 40, 65, 0.5);
        }

        .audio-card input[type="radio"] {
            margin-top: 0.25rem;
            width: 18px;
            height: 18px;
            cursor: pointer;
            accent-color: var(--primary);
        }

        .audio-info {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            min-width: 0;
        }

        .audio-name {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .audio-player audio {
            width: 100%;
            height: 32px;
            border-radius: 4px;
        }

        .video-card {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            background: rgba(15, 21, 36, 0.6);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 1rem;
            transition: all var(--transition-fast);
        }

        .video-card:hover {
            border-color: var(--primary);
            background: rgba(29, 40, 65, 0.5);
        }

        /* Scrollbars */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 99px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo-icon">🎬</div>
            <div>
                <h1 class="logo-text" style="font-size: 0.95rem; font-weight:700;">Video Sequencer</h1>
                <span class="logo-badge">MoviePy</span>
            </div>
        </div>
        <a href="/text_to_mp3" class="btn btn-accent" style="padding: 0.5rem 1rem; font-size: 0.8rem;">Kokoro TTS</a>
    </header>

    <main>
        <form action="/create_video" method="POST" enctype="multipart/form-data">
            <!-- Images Panel -->
            <div class="card" style="margin-bottom: 1.5rem;">
                <div class="card-title">
                    <span>Select Images</span>
                    <span style="font-size: 0.75rem; color: var(--accent); font-weight: 500;">Exactly 7 Required</span>
                </div>
                <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">Choose 7 images and set sequence (1-7):</p>
                <div class="images-list">
                    {% for image in images %}
                    <div class="image-card" onclick="const chk = document.getElementById('chk_{{ image }}'); chk.checked = !chk.checked; event.stopPropagation();">
                        <img src="{{ url_for('static', filename='/junk/' + image) }}" alt="{{ image }}">
                        <div class="image-controls" onclick="event.stopPropagation();">
                            <label class="checkbox-container">
                                <input type="checkbox" id="chk_{{ image }}" name="images" value="{{ image }}">
                                <span>Select Image</span>
                            </label>
                            <div class="sequence-input-container">
                                <span>Sequence:</span>
                                <input type="number" name="sequence_{{ image }}" min="1" max="100" placeholder="-">
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Audio Panel -->
            <div class="card" style="margin-bottom: 1.5rem;">
                <div class="card-title">
                    <span>Select Audio Track</span>
                </div>
                <div class="audio-list">
                    {% for mp3 in mp3s %}
                    <div class="audio-card" onclick="document.getElementById('rad_{{ mp3 }}').click();">
                        <input type="radio" id="rad_{{ mp3 }}" name="audio" value="{{ mp3 }}">
                        <div class="audio-info" onclick="event.stopPropagation();">
                            <span class="audio-name" title="{{ mp3 }}">{{ mp3 }}</span>
                            <div class="audio-player">
                                <audio controls>
                                    <source src="{{ url_for('static', filename='junk/' + mp3) }}" type="audio/mp3">
                                    Your browser does not support audio.
                                </audio>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            <!-- Video Panel -->
            <div class="card" style="margin-bottom: 1.5rem;">
                <div class="card-title">
                    <span>Available Videos</span>
                </div>
                <div class="audio-list">
                    {% for mp4 in mp4s %}
                    <div class="video-card">
                        <div class="audio-info">
                            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 1rem;">
                                <span class="audio-name" title="{{ mp4 }}" style="flex-grow: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ mp4 }}</span>
                                <a href="{{ url_for('serve_video', filename=mp4) }}" target="_blank" class="btn btn-accent" style="padding: 0.35rem 0.7rem; font-size: 0.75rem; border-radius: var(--radius-sm); box-shadow: none; white-space: nowrap; text-decoration: none;">
                                    ↗ Open in New Tab
                                </a>
                            </div>
                            <div style="margin-top: 0.5rem; width: 100%;">
                                <video controls style="width: 100%; border-radius: var(--radius-sm); border: 1px solid var(--border-color); display: block; position: relative; z-index: 10; pointer-events: auto;">
                                    <source src="{{ url_for('serve_video', filename=mp4) }}" type="video/mp4">
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            <!-- Create Button -->
            <button type="submit" class="btn btn-block" style="padding: 1.1rem;">
                <span>Assemble & Create Video</span>
            </button>
        </form>
    </main>
</body>
</html>
"""

@app.route('/')
def index():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg','.jpeg','.png'))]
    mp3s = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.mp3')]
    mp4s = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.mp4')]    
    return render_template_string(HTML, images=images, mp3s=mp3s, mp4s=mp4s)

def overlay_frame(image_path, frame_path, output_path):
    base = Image.open(image_path).convert("RGBA")
    frame = Image.open(frame_path).convert("RGBA").resize(base.size)
    combined = Image.alpha_composite(base, frame)
    combined.convert("RGB").save(output_path, "JPEG")

def pad_audio_with_silence(audio_path, output_path, pad_duration_ms=500):
    original = AudioSegment.from_mp3(audio_path)
    silence = AudioSegment.silent(duration=pad_duration_ms)
    padded = silence + original + silence
    padded.export(output_path, format="mp3")

@app.route('/create_video', methods=['POST'])
def create_video():
    selected_images = request.form.getlist('images')
    selected_audio = request.form.get('audio')
    ic(selected_images, selected_audio)

    image_sequence = []
    for img in selected_images:
        seq_val = request.form.get(f"sequence_{img}")
        if not seq_val:
            return f"Missing sequence number for {img}", 400
        image_sequence.append((int(seq_val), img))

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

    clips = [
        ImageClip(path).set_duration(image_duration)
        for path in processed_paths
    ]

    final_video = concatenate_videoclips(
        clips,
        method="compose"
    ).set_audio(audio_clip)

    video_filename = f"{UNIQUE}final_video.mp4"
    output_video_path = os.path.join(OUTPUT_FOLDER, video_filename)

    try:
        final_video.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24
        )

        return redirect(url_for("serve_video", filename=video_filename))

    except Exception as e:
        ic(e)
        return "Error creating video.", 500


@app.route('/video/<filename>')
def serve_video(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        mimetype='video/mp4',
        conditional=True
    )
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
                    if img.size != TARGET_SIZE:
                        img.resize(TARGET_SIZE, Image.LANCZOS).save(p)
            except Exception as e:
                ic("Resize error:", e)

resize_all_images()

# --------------------------------------------------
# KOKORO TTS CONFIG
# --------------------------------------------------

TTS_voices=['af_alloy','af_aoede','af_bella','af_heart','af_jessica','af_kore',
'af_nicole','af_nova','af_river','af_sarah','af_sky','am_adam','am_echo','am_eric',
'am_fenrir','am_liam','am_michael','am_onyx','am_puck','am_santa','bf_alice','bf_emma',
'bf_isabella','bf_lily','bm_daniel','bm_fable','bm_george','bm_lewis','ef_dora',
'em_alex','em_santa','ff_siwis','hf_alpha','hf_beta','hm_omega','hm_psi','if_sara',
'im_nicola','jf_alpha','jf_gongitsune','jf_nezumi','jf_tebukuro','jm_kumo','pf_dora',
'pm_alex','pm_santa','zf_xiaobei','zf_xiaoni','zf_xiaoxiao','zf_xiaoyi']

KOKORO_TTS_URL = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE = "am_echo"

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
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        mimetype="audio/mpeg",
        conditional=True
    )

# --------------------------------------------------
# TEXT → MP3 PAGE
# --------------------------------------------------
HTML_MP3 = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kokoro TTS</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --bg-base: #080b11;
            --bg-surface: #0f1524;
            --bg-card: rgba(22, 30, 49, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(99, 102, 241, 0.15);
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --primary-glow: rgba(99, 102, 241, 0.4);
            
            --secondary: #8b5cf6;
            
            --accent: #14b8a6;
            
            --radius-sm: 8px;
            --radius-md: 14px;
            
            --shadow-sm: 0 2px 8px -2px rgba(0,0,0,0.5);
            --shadow-md: 0 10px 25px -5px rgba(0,0,0,0.6);
            
            --transition-normal: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 40%);
            background-attachment: fixed;
        }

        h1, h2 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        header {
            max-width: 440px; 
            width: 100%;
            margin-right: auto;
            margin-left: auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.25rem 2rem;
            background-color: rgba(15, 21, 36, 0.5);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            width: 2.25rem;
            height: 2.25rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            box-shadow: 0 0 15px var(--primary-glow);
        }

        .logo-text {
            font-size: 0.75rem;
            font-weight: 400;
            background: linear-gradient(to right, #ffffff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-badge {
            font-size: 0.60rem;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: rgba(20, 184, 166, 0.15);
            color: #2dd4bf;
            padding: 0.2rem 0.5rem;
            border-radius: 25px;
            border: 1px solid rgba(20, 184, 166, 0.3);
        }

        main {
            display: flex;
            flex-direction: column;
            flex-grow: 1;
            max-width: 440px; 
            width: 100%;
            margin: 0 auto;
            gap: 1.5rem;
            padding: 1.5rem;
            height: auto;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.25rem;
            box-shadow: var(--shadow-sm);
            transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }

        .card:hover {
            border-color: var(--border-glow);
            box-shadow: var(--shadow-md);
        }

        .card-title {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: var(--text-primary);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.5rem;
        }

        /* Form Inputs */
        textarea {
            width: 100%;
            background-color: rgba(15, 21, 36, 0.8);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            padding: 0.75rem;
            font-family: inherit;
            font-size: 0.9rem;
            transition: all var(--transition-normal);
            outline: none;
            resize: vertical;
            min-height: 120px;
            line-height: 1.4;
        }

        textarea:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
            background-color: rgba(15, 21, 36, 0.95);
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.75rem 1.25rem;
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 700;
            cursor: pointer;
            text-decoration: none;
            box-shadow: 0 4px 15px var(--primary-glow);
            transition: all var(--transition-normal);
            text-align: center;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }

        .btn:active {
            transform: translateY(1px);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            box-shadow: none;
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
            border-color: var(--text-muted);
            box-shadow: none;
        }

        .btn-block {
            display: flex;
            width: 100%;
        }

        /* Result display */
        .result-container {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px dashed rgba(255,255,255,0.05);
        }

        audio {
            width: 100%;
            height: 40px;
            border-radius: var(--radius-sm);
        }

        .result-filename {
            font-family: monospace;
            font-size: 0.8rem;
            color: var(--accent);
            background: rgba(20, 184, 166, 0.1);
            border: 1px solid rgba(20, 184, 166, 0.2);
            padding: 0.4rem 0.6rem;
            border-radius: 6px;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo-icon">🗣️</div>
            <div>
                <h1 class="logo-text" style="font-size: 0.95rem; font-weight:700;">Kokoro TTS</h1>
                <span class="logo-badge">am_onyx</span>
            </div>
        </div>
        <a href="/" class="btn btn-secondary" style="padding: 0.5rem 1rem; font-size: 0.8rem;">Home</a>
    </header>

    <main>
        <div class="card">
            <div class="card-title">
                <span>Text to Speech</span>
            </div>
            
            <form method="post">
                <textarea name="text" placeholder="Enter the script text you want to synthesize into speech...">{{ text }}</textarea>
                
                <button type="submit" class="btn btn-block" style="margin-top: 1rem; padding: 0.9rem;">
                    Generate MP3 Audio
                </button>
            </form>

            {% if mp3_file %}
            <div class="result-container">
                <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary);">Generated Track:</span>
                <audio controls autoplay>
                    <source src="{{ url_for('serve_file', filename=mp3_file) }}" type="audio/mpeg">
                    Your browser does not support audio.
                </audio>
                <div class="result-filename">{{ mp3_file }}</div>
            </div>
            {% endif %}
        </div>
    </main>
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
