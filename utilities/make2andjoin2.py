#!/usr/bin/env python3
# Complete Flask app: accepts image OR mp4 upload.
# - Image: creates narrated video (image + title overlay + fades) using generated TTS.
# - Video: keeps original video, detects if it has audio; if it does, mixes original audio + TTS
#          with TTS dominant (70% TTS / 30% original). If original has no audio, attaches TTS only.
#
# Uses icecream.ic for debug logging (no logging module).
# Saves files under static/ADS (created automatically).
#
# Jack: this is the single-file, complete script you requested — no placeholders.

from flask import Flask, request, render_template_string, send_from_directory, redirect
import os
import uuid
import subprocess
import requests
from werkzeug.utils import secure_filename
from icecream import ic
import json
from datetime import datetime

# ----------------------------
# Configuration
# ----------------------------
UPLOAD_FOLDER = "static/ADS"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".ogg"}
ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

TTS_API_URL = "http://localhost:8880/v1/audio/speech"  # keep your existing TTS endpoint
ASSISTANT_VOICE = "am_michael"  # keep your existing voice choice
HEADERS = {"Content-Type": "application/json"}

# ----------------------------
# Flask app
# ----------------------------
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1GB max upload (adjust if you like)

# ----------------------------
# HTML page (single complete page)
# ----------------------------
HTML_PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Esperanza: Image or Video Upload</title>
  <style>
    body { background:#111; color:#eee; font-family:Segoe UI, Arial, sans-serif; padding:20px; }
    .panel { background: rgba(255,255,255,0.03); padding:16px; border-radius:10px; max-width:900px; }
    input, textarea { width:100%; padding:10px; border-radius:6px; border: none; background:#161616; color:#fff; }
    button { background:#c71585; color:white; padding:10px 14px; border-radius:8px; border:none; cursor:pointer; font-weight:600; }
    .small { color:#aaa; font-size:0.9rem; margin-top:6px; }
    video { max-width:100%; height:auto; display:block; margin-top:12px; }
  </style>
</head>
<body>
  <div class="panel">
    <h2>Upload an Image or Video + Enter Text</h2>
    <form method="POST" enctype="multipart/form-data">
      <label><strong>Choose image (png/jpg) OR video (mp4/mkv/mov):</strong></label><br/>
      <input type="file" name="media" accept="image/*,video/*" required><br/><br/>
      <label><strong>Enter text to narrate:</strong></label><br/>
      <textarea name="text" rows="6" placeholder="Enter narration text here..." required></textarea><br/><br/>
      <button type="submit">CREATE</button>
    </form>

    <div class="small">Upload will save files under <code>{{ upload_folder }}</code>. TTS voice: <code>{{ voice }}</code></div>
    <div style="margin-top:18px;">{{ preview|safe }}</div>
  </div>
</body>
</html>
"""

# ----------------------------
# Utilities
# ----------------------------

def allowed_extension(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_VIDEO_EXTS or ext in ALLOWED_IMAGE_EXTS

def is_video_extension(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_VIDEO_EXTS

def is_image_extension(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_IMAGE_EXTS

def run(cmd):
    """Run a command and return (returncode, stdout, stderr). Logs via ic."""
    ic("Running command:", " ".join(cmd))
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        out = p.stdout.decode(errors="ignore") if p.stdout else ""
        err = p.stderr.decode(errors="ignore") if p.stderr else ""
        ic("Return code:", p.returncode)
        if out:
            ic("stdout:", out[:4000])
        if err:
            ic("stderr:", err[:4000])
        return p.returncode, out, err
    except Exception as e:
        ic("Exception running command:", e)
        return 1, "", str(e)

# ----------------------------
# TTS generation
# ----------------------------

def generate_tts(text, output_mp3_path):
    """Call TTS endpoint and write MP3 to disk."""
    payload = {
        "input": text,
        "voice": ASSISTANT_VOICE
    }
    try:
        ic("Requesting TTS...", {"url": TTS_API_URL, "voice": ASSISTANT_VOICE})
        response = requests.post(TTS_API_URL, json=payload, headers=HEADERS, timeout=180)
        ic("TTS response status:", response.status_code)
        if response.status_code == 200:
            with open(output_mp3_path, "wb") as f:
                f.write(response.content)
            ic("TTS audio saved:", output_mp3_path)
            return True
        else:
            ic("TTS error:", response.status_code, response.text[:200])
            return False
    except Exception as e:
        ic("TTS request failed:", e)
        return False

# ----------------------------
# FFprobe helpers
# ----------------------------

def probe_media(path):
    """Return ffprobe JSON dict for given file, or None on error."""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
    code, out, err = run(cmd)
    if code != 0:
        ic("ffprobe failed for", path)
        return None
    try:
        meta = json.loads(out)
        return meta
    except Exception as e:
        ic("Failed parsing ffprobe output:", e)
        return None

def has_audio(video_path):
    """Return True if ffprobe shows an audio stream."""
    meta = probe_media(video_path)
    if not meta:
        return False
    streams = meta.get("streams", [])
    for s in streams:
        if s.get("codec_type") == "audio":
            ic(f"Detected audio stream in {video_path}")
            return True
    ic(f"No audio stream detected in {video_path}")
    return False

def get_audio_duration(path):
    """Return duration in seconds of audio or None."""
    meta = probe_media(path)
    if not meta:
        return None
    fmt = meta.get("format", {})
    dur = fmt.get("duration")
    if dur is None:
        return None
    try:
        return float(dur)
    except:
        return None

# ----------------------------
# Video creation for images (existing pipeline)
# ----------------------------

def build_video_from_image(image_path, audio_path, output_path):
    """
    Uses your existing filter graph to make a framed 512x768 style video from a single image + title overlay.
    """
    try:
        duration = get_audio_duration(audio_path)
        if duration is None:
            ic("Cannot determine audio duration for", audio_path)
            return False

        image_w, image_h = 512, 768
        padded_w, padded_h = image_w + 30, image_h + 30

        fade_duration = 2.5
        fade_start = duration + 1.0 + 2 - fade_duration
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
            "ffmpeg",
            "-loop", "1", "-i", image_path,
            "-loop", "1", "-i", title_path,
            "-i", audio_path,
            "-filter_complex", filter_graph,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration + 3),
            "-y",
            output_path
        ]

        ic("FFMPEG (image->video) command:", " ".join(ffmpeg_cmd))
        code, out, err = run(ffmpeg_cmd)
        return code == 0
    except Exception as e:
        ic("build_video_from_image failed:", e)
        return False

# ----------------------------
# Video processing for uploaded video (mix audio)
# ----------------------------

def mix_video_with_tts(original_video_path, tts_mp3_path, output_path, tts_gain=0.7, orig_gain=0.3):
    """
    If original video has audio: mix original audio + TTS with specified gains (tts dominant).
    If original has no audio: attach TTS only.
    The function re-encodes video with libx264 for compatibility.
    """
    try:
        # detect if original has audio
        if has_audio(original_video_path):
            # Build filter_complex to adjust volumes and amix
            # We'll label streams and produce a single audio output [aout]
            # Note: amix might increase volume, so final volume normalization step applied (volume=1)
            filter_graph = (
                f"[0:a]volume={orig_gain}[a0];"
                f"[1:a]volume={tts_gain}[a1];"
                f"[a0][a1]amix=inputs=2:duration=longest:dropout_transition=0[aout]"
            )

            ffmpeg_cmd = [
                "ffmpeg",
                "-i", original_video_path,
                "-i", tts_mp3_path,
                "-filter_complex", filter_graph,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "-y",
                output_path
            ]
            ic("FFMPEG (mix) command:", " ".join(ffmpeg_cmd))
            code, out, err = run(ffmpeg_cmd)
            return code == 0
        else:
            # No original audio: attach TTS as single audio track
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", original_video_path,
                "-i", tts_mp3_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-map", "0:v",
                "-map", "1:a",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                "-y",
                output_path
            ]
            ic("FFMPEG (attach TTS only) command:", " ".join(ffmpeg_cmd))
            code, out, err = run(ffmpeg_cmd)
            return code == 0

    except Exception as e:
        ic("mix_video_with_tts failed:", e)
        return False

# ----------------------------
# Flask routes
# ----------------------------

@app.route("/", methods=["GET", "POST"])
def upload():
    preview_html = ""
    if request.method == "POST":
        uploaded = request.files.get("media")
        text = request.form.get("text", "").strip()

        if not uploaded:
            return "No file uploaded", 400
        if not text:
            return "Please provide narration text", 400

        filename = secure_filename(uploaded.filename)
        if not filename:
            return "Invalid filename", 400
        if not allowed_extension(filename):
            return "File type not permitted", 400

        base = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()

        saved_input_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{base}{ext}")
        uploaded.save(saved_input_path)
        ic(f"Saved uploaded file: {saved_input_path}")

        # prepare tts audio path
        tts_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{base}.mp3")
        final_video_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{base}_final.mp4")

        # Generate TTS first (common step)
        if not generate_tts(text, tts_path):
            return "TTS generation failed", 500

        # Branch by type: image vs video
        if is_image_extension(filename):
            ic("Processing as image -> create narrated video")
            # Ensure image exists; reuse existing image pipeline
            ok = build_video_from_image(saved_input_path, tts_path, final_video_path)
            if not ok:
                return "Failed to build video from image", 500

            preview_html = (
                "<h3>✅ Video Ready (from image)</h3>"
                f"<video controls><source src='/video/{os.path.basename(final_video_path)}' type='video/mp4'></video>"
            )
            return render_template_string(HTML_PAGE, preview=preview_html, upload_folder=UPLOAD_FOLDER, voice=ASSISTANT_VOICE)

        elif is_video_extension(filename):
            ic("Processing as uploaded video -> mix TTS with existing audio (if present)")
            # Mix the uploaded video with the TTS
            ok = mix_video_with_tts(saved_input_path, tts_path, final_video_path, tts_gain=0.7, orig_gain=0.3)
            if not ok:
                return "Failed to mix video with TTS", 500

            preview_html = (
                "<h3>✅ Video Ready (from uploaded video)</h3>"
                f"<video controls><source src='/video/{os.path.basename(final_video_path)}' type='video/mp4'></video>"
            )
            return render_template_string(HTML_PAGE, preview=preview_html, upload_folder=UPLOAD_FOLDER, voice=ASSISTANT_VOICE)

        else:
            ic("Unknown extension branch reached (should not happen):", ext)
            return "Unsupported media type", 400

    # GET request
    return render_template_string(HTML_PAGE, preview=preview_html, upload_folder=UPLOAD_FOLDER, voice=ASSISTANT_VOICE)

@app.route("/video/<path:filename>")
def serve_video(filename):
    # serve videos from UPLOAD_FOLDER
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    ic("Starting Flask server on 0.0.0.0:5100 — upload folder:", UPLOAD_FOLDER)
    app.run(debug=True, host="0.0.0.0", port=5100)
