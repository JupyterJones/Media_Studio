#!/usr/bin/env python3

import os
import uuid
import subprocess
import requests
from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename
from icecream import ic

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'ADS'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

TTS_API_URL = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE = "am_michael"
HEADERS = {"Content-Type": "application/json"}

HTML_PAGE = """
<!doctype html>
<title>Image to Video</title>
<h2>Upload Image and Enter Text</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=image><br><br>
  <textarea name=text rows=10 cols=60 placeholder="Enter your sales ad here..."></textarea><br><br>
  <input type=submit value=CREATE>
</form>
{preview}
"""

def generate_tts(text, output_mp3_path):
    payload = {
        "input": text,
        "voice": ASSISTANT_VOICE
    }
    try:
        response = requests.post(TTS_API_URL, json=payload, headers=HEADERS, timeout=180)
        if response.status_code == 200:
            with open(output_mp3_path, 'wb') as f:
                f.write(response.content)
            ic(f"TTS audio saved: {output_mp3_path}")
            return True
        else:
            ic(f"TTS error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        ic(f"TTS request failed: {e}")
        return False

def run_ffmpeg(image_path, audio_path, output_path):
    try:
        ffprobe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', audio_path]
        result = subprocess.run(ffprobe_cmd, check=True, capture_output=True, text=True)
        duration = float(eval(result.stdout)['format']['duration'])
        ic(f"Audio duration: {duration}")

        image_w, image_h = 512, 768  # You can extract this with Pillow if needed
        padded_w, padded_h = image_w + 30, image_h + 30
        fade_duration = 2.5
        fade_start = duration + 1.0 + 2 - fade_duration  # match your formula
        title_path = "static/assets/talks.png"

        filter_graph = (
            f"color=c=#A52A2A:s={padded_w}x{padded_h}:d={duration + 3}[bg];"
            f"[1:v]scale={padded_w}:{padded_h}[title];"
            f"[bg][0:v]overlay=(W-w)/2:(H-h)/2[framed];"
            f"[framed][title]overlay[prefade];"
            f"[prefade]fade=type=out:start_time={fade_start}:duration={fade_duration}[v];"
            f"[2:a]apad=pad_dur=1.0[a]"
        )

        ffmpeg_cmd = [
            'ffmpeg',
            '-loop', '1', '-i', image_path,
            '-loop', '1', '-i', title_path,
            '-i', audio_path,
            '-filter_complex', filter_graph,
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-t', str(duration + 3),
            '-y',
            output_path
        ]

        ic("Running FFMPEG command...")
        subprocess.run(ffmpeg_cmd, check=True)
        ic(f"Video created: {output_path}")
        return True
    except Exception as e:
        ic(f"FFMPEG failed: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def upload():
    preview_html = ""
    if request.method == 'POST':
        image = request.files['image']
        text = request.form.get('text', '').strip()

        if image and text:
            filename = secure_filename(image.filename)
            base = str(uuid.uuid4())
            img_ext = os.path.splitext(filename)[1].lower()
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base}{img_ext}")
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base}.mp3")
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base}.mp4")

            image.save(image_path)
            ic(f"Image saved: {image_path}")
            ic(f"Entered text: {text[:80]}...")

            if generate_tts(text, audio_path):
                if run_ffmpeg(image_path, audio_path, video_path):
                    preview_html = f"<h3>✅ Video Ready</h3><video width='512' height='768' controls><source src='/video/{os.path.basename(video_path)}' type='video/mp4'></video>"

    return HTML_PAGE.format(preview=preview_html)

@app.route('/video/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5200)
