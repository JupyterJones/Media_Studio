#!/usr/bin/env python3
"""
Full Flask App: Image Upload -> Caption -> TTS -> Video Generation
"""

import os
import json
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from icecream import ic
import requests

# -----------------------------
# CONFIG
# -----------------------------
UPLOAD_FOLDER = "./uploads"
AUDIO_FOLDER = "./tts"
VIDEO_FOLDER = "./videos"
DESCRIPTION_API = "http://localhost:5100/describe"
TTS_API = "http://localhost:5100/tts"
MAX_IMAGES = 50

for folder in [UPLOAD_FOLDER, AUDIO_FOLDER, VIDEO_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# -----------------------------
# HELPERS
# -----------------------------
def allowed_file(filename):
    return filename.lower().endswith((".png", ".jpg", ".jpeg"))

def generate_tts(text, filename):
    ic(f"Generating TTS for: {text[:30]}...")
    response = requests.post(
        TTS_API, json={"text": text, "filename": filename}
    )
    if response.status_code == 200:
        ic(f"TTS saved: {filename}")
        return os.path.join(AUDIO_FOLDER, filename)
    else:
        ic("TTS generation failed")
        return None

def create_video(images, audios, output_file):
    ic(f"Creating video with {len(images)} images")
    # Build ffmpeg input file
    with open("input.txt", "w") as f:
        for img, aud in zip(images, audios):
            duration = float(subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of",
                 "default=noprint_wrappers=1:nokey=1", aud]
            ).decode().strip())
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration}\n")
    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", "input.txt",
        "-i", "+".join(audios), "-c:v", "libx264", "-c:a", "aac",
        "-strict", "experimental", output_file
    ]
    ic("Running ffmpeg...")
    subprocess.run(cmd, check=True)
    ic(f"Video saved: {output_file}")
    os.remove("input.txt")

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload_files():
    if "images" not in request.files:
        return jsonify({"error": "No files part"}), 400
    files = request.files.getlist("images")
    saved_files = []
    for f in files[:MAX_IMAGES]:
        if allowed_file(f.filename):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], f.filename)
            f.save(filepath)
            saved_files.append(filepath)
            ic(f"Saved file: {filepath}")
    return jsonify({"saved": saved_files})

@app.route("/process", methods=["POST"])
def process_images():
    files = sorted(os.listdir(UPLOAD_FOLDER))
    images = [os.path.join(UPLOAD_FOLDER, f) for f in files if allowed_file(f)]
    if not images:
        return jsonify({"error": "No images to process"}), 400

    captions = []
    audios = []

    # Generate descriptions and TTS
    for img in images:
        ic(f"Processing image: {img}")
        desc_resp = requests.post(DESCRIPTION_API, files={"image": open(img, "rb")})
        caption = desc_resp.json().get("description", "No description")
        captions.append(caption)

        audio_filename = os.path.basename(img).rsplit(".", 1)[0] + ".mp3"
        audio_path = generate_tts(caption, audio_filename)
        audios.append(audio_path)

    video_filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    video_path = os.path.join(VIDEO_FOLDER, video_filename)
    create_video(images, audios, video_path)

    return jsonify({"captions": captions, "video": video_path})

@app.route("/videos/<filename>")
def get_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    ic("Starting Flask App...")
    app.run(host="0.0.0.0", port=5101, debug=True)
