#!/usr/bin/env python3
import os
import base64
import requests
from flask import Flask, request, render_template_string, send_file
from werkzeug.utils import secure_filename
from icecream import ic
import subprocess
import re

app = Flask(__name__)

UPLOAD_FOLDER = 'static/projects'
TTS_OUTPUT = 'static/projects'
MKV_OUTPUT = 'static/projects'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TTS_OUTPUT, exist_ok=True)
os.makedirs(MKV_OUTPUT, exist_ok=True)

LLaVA_API_URL = "http://localhost:11434/api/generate"
LLaVA_MODEL_NAME = "LLaVA:latest"

TTS_API_URL = "http://localhost:8880/v1/audio/speech"
HEADERS = {"Content-Type": "application/json"}
VOICES=['bf_alice', 'bf_emma', 'bf_lily', 'bf_v0emma', 'bf_v0isabella', 'af_alloy', 'af_aoede', 'af_bella', 'af_heart', 'af_jadzia', 'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river', 'af_sarah', 'af_sky', 'af_v0', 'af_v0bella', 'af_v0irulan', 'af_v0nicole', 'af_v0sarah', 'af_v0sky', 'am_adam', 'am_echo', 'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx', 'am_puck', 'am_santa', 'am_v0adam', 'am_v0gurney', 'am_v0michael','bm_daniel', 'bm_fable']
ASSISTANT_VOICE = VOICES[28]

chat_history = []
last_image_path = None
last_text_path = None

# ----------------------
def sanitize_filename(text, max_length=20):
    base = text.strip()[:max_length]
    base = re.sub(r'\W+', '_', base)
    return base or "output"

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def describe_image(image_path, prompt="Describe this image"):
    try:
        image_base64 = image_to_base64(image_path)
        payload = {
            "model": LLaVA_MODEL_NAME,
            "prompt": prompt,
            "tokens": 4048,
            "stream": False,
            "images": [image_base64]
        }
        response = requests.post(LLaVA_API_URL, json=payload, timeout=900)
        response.raise_for_status()
        caption = response.json().get('response', 'No response field.')
        ic(f"CAPTION: {caption}")
        return caption
    except Exception as e:
        ic(f"LLaVA ERROR: {e}")
        return f"LLaVA Error: {e}"

def generate_tts(text):
    filename = sanitize_filename(text) + ".mp3"
    output_path = os.path.join(TTS_OUTPUT, filename)
    payload = {"input": text, "voice": ASSISTANT_VOICE}
    try:
        ic(f"Sending TTS request for first 40 chars: {text[:40]}...")
        response = requests.post(TTS_API_URL, json=payload, headers=HEADERS, timeout=900)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            ic(f"TTS audio saved: {output_path}")
            return output_path
        else:
            ic(f"TTS error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        ic(f"TTS request failed: {e}")
        return None

def get_audio_duration(audio_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        duration = float(result.stdout.strip())
        ic(f"Audio duration: {duration} seconds")
        return duration
    except Exception as e:
        ic(f"Failed to get duration: {e}")
        return 0

def create_mkv(image_path, audio_path):
    from icecream import ic
    import subprocess
    from PIL import Image
    import os

    audio_duration = get_audio_duration(audio_path)
    video_duration = audio_duration + 3.0   # padding for clean ending
    mkv_filename = os.path.basename(audio_path).replace(".mp3", ".mkv")
    mkv_path = os.path.join("static/projects", mkv_filename)

    # Load image size (portrait)
    img = Image.open(image_path)
    width, height = img.size
    ic(f"Original image size: {width}x{height}")

    # Total frames at 30 fps
    total_frames = int(video_duration * 30)

    # ✔️ Correct zoom expression — zoom in then out
    zoom_expr = f"1+0.05*sin(PI*on/{total_frames})"

    # ✔️ Correct zoompan syntax
    filter_complex = (
        f"[0:v]scale={width}:{height},"
        f"zoompan=z='{zoom_expr}':d={total_frames}:s={width}x{height},"
        f"format=yuv420p[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "libopus",
        "-t", str(video_duration),
        "-shortest",
        mkv_path
    ]

    ic(f"Running ffmpeg: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    ic(f"Ken Burns MKV (zoom in/out) created: {mkv_path}")
    return mkv_path

'''
def create_mkv(image_path, audio_path):
    audio_duration = get_audio_duration(audio_path)
    video_duration = audio_duration + 3.0  # 1 second padding
    mkv_filename = os.path.basename(audio_path).replace(".mp3", ".mkv")
    mkv_path = os.path.join(MKV_OUTPUT, mkv_filename)
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "libopus",
        "-t", str(video_duration),
        "-shortest",
        mkv_path
    ]
    ic(f"Running ffmpeg: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    ic(f"MKV created: {mkv_path}")
    return mkv_path
'''
# ----------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    global last_image_path, last_text_path

    response_text = ""
    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                last_image_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(last_image_path)
                chat_history.clear()
                last_text_path = None

        elif 'generate' in request.form:
            user_question = request.form['question']
            if last_image_path:
                response_text = describe_image(last_image_path, user_question)
            else:
                response_text = "Please upload an image first."
            chat_history.append(('user', user_question))
            chat_history.append(('assistant', response_text))
            last_text_path = os.path.join(TTS_OUTPUT, sanitize_filename(response_text)+".txt")
            with open(last_text_path, 'w', encoding='utf-8') as f:
                f.write(response_text)

        elif 'tts' in request.form:
            edited_text = request.form.get('edited_text', '').strip()
            if edited_text and last_image_path:
                tts_path = generate_tts(edited_text)
                mkv_path = create_mkv(last_image_path, tts_path)
                return send_file(mkv_path, as_attachment=True)

    image_html = f'<div class="image-container"><img src="/{last_image_path}"></div>' if last_image_path else ""

    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Esperanza Vision</title>
        <style>
            body { margin:0;font-family:'Segoe UI',sans-serif;background:#111;color:#f0f0f0;display:grid;grid-template-columns:1fr 1fr;height:100vh;}
            .left { padding:30px; overflow-y:auto; background:rgba(0,0,0,0.6); backdrop-filter:blur(10px);}
            .right { padding:20px; display:flex; align-items:center; justify-content:center; background:#111;}
            input, textarea { width:100%; padding:10px; margin-top:10px; border:none; border-radius:6px; background:#222; color:#eee;}
            button { margin-top:10px;padding:10px 20px;border:none;background:#c71585;color:white;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow:0 0 10px #c71585;}
            .image-container {border:4px solid #c71585;padding:10px;border-radius:20px;background:linear-gradient(135deg,#1c1c1c,#2a2a2a);box-shadow:0 0 20px #c71585;}
            .image-container img {max-width:100%; max-height:80vh; border-radius:12px;}
            .chat-box {background:#1e1e1e;margin-top:15px;padding:12px;border-radius:8px;}
            .chat-user {font-weight:bold;color:#9acd32;}
            .chat-assistant {color:#ff69b4;font-style:italic;}
        </style>
    </head>
    <body>
        <div class="left">
            <h1>💬 Esperanza Visual Chat</h1>

            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="image">
                <button type="submit">Upload Image</button>
            </form>

            <form method="POST">
                <input type="text" name="question" placeholder="Ask Esperanza about the image...">
                <button type="submit" name="generate">Generate Response</button>
            </form>

            {% if chat_history %}
            <form method="POST">
                <textarea name="edited_text" rows="8">{{ chat_history[-1][1] }}</textarea>
                <button type="submit" name="tts">Generate MKV</button>
            </form>
            {% endif %}

            <hr style="margin:20px 0; border-color:#444;">
            {% for role,msg in chat_history %}
            <div class="chat-box">
                <div class="chat-{{ role }}">{{ role }}: {{ msg }}</div>
            </div>
            {% endfor %}
        </div>

        <div class="right">
            {{ image_html|safe }}
        </div>
    </body>
    </html>
    '''

    return render_template_string(template, chat_history=chat_history, image_html=image_html)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5100)
