#!/usr/bin/env python3
from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    send_file,
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
#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify
from icecream import ic
import os
import tempfile
from datetime import datetime
import speech_recognition as sr
app = Flask(__name__)
# ----------------------------------------------------
# Config
# ----------------------------------------------------
DEFAULT_VOICE = "am_echo"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SHARED_PATH = os.path.join(BASE_DIR, "static", "images")
FRAME_PATH = os.path.join(BASE_DIR, "static", "assets", "talks.png")
VIDEO_DIR = os.path.join(BASE_DIR,  "static", "videos")
MP3_DIR = os.path.join(BASE_DIR,  "static", "mp3s")
LOG_PATH = os.path.join(BASE_DIR, "static", "logs")
os.makedirs(SHARED_PATH, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(MP3_DIR, exist_ok=True)
os.makedirs(LOG_PATH, exist_ok=True)
UNIQUE = str(randint(100000, 999999))

def logit(*args):
    msg = " ".join(map(str, args))
    #ts = datetime.now().strftime("%H:%M:%S")
    #line = f"[{ts}] {msg}"
    line = f"{msg}"
    print(line, flush=True)
    try:
        with open(os.path.join(LOG_PATH, "debug_log.txt"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except: pass

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Flask Mic Recorder</title>
    <style>
        body{
            background:#1e1e1e;
            color:white;
            font-family:Arial;
            padding:30px;
        }
        h1{
            color:#00ffaa;
        }
        button{
            padding:12px 20px;
            margin-right:10px;
            margin-top:10px;
            border:none;
            border-radius:8px;
            font-size:16px;
            cursor:pointer;
        }
        #recordBtn{
            background:#cc3333;
            color:white;
        }
        #stopBtn{
            background:#3366cc;
            color:white;
        }
        #sendBtn{
            background:#009966;
            color:white;
        }
        textarea{
            width:100%;
            height:300px;
            margin-top:20px;
            background:#2b2b2b;
            color:#00ff99;
            border:1px solid #555;
            border-radius:10px;
            padding:15px;
            font-size:16px;
            resize:vertical;
        }
        #status{
            margin-top:20px;
            color:#ffaa00;
            font-size:18px;
        }
        audio{
            width:100%;
            margin-top:20px;
        }
    </style>
</head>
<body>
<h1>🎤 Flask Microphone Recorder</h1>
<a href="/text_to_mp3" style="color:orange;font-size:20px;">TEXT → MP3</a>&nbsp;&nbsp;&nbsp;&nbsp;<a href="/" style="color:orange;font-size:20px;">HOME</a><br />
<button id="recordBtn">Start Recording</button>
<button id="stopBtn" disabled>Stop Recording</button>
<button id="sendBtn" disabled>Transcribe</button>
<div id="status">Idle</div>
<audio id="audioPlayback" controls></audio>
<textarea id="resultText" placeholder="Speech recognition results appear here..."></textarea>
<script>
let mediaRecorder;
let audioChunks = [];
const recordBtn = document.getElementById("recordBtn");
const stopBtn = document.getElementById("stopBtn");
const sendBtn = document.getElementById("sendBtn");
const statusDiv = document.getElementById("status");
const resultText = document.getElementById("resultText");
const audioPlayback = document.getElementById("audioPlayback");
recordBtn.onclick = async () => {
    audioChunks = [];
    const stream = await navigator.mediaDevices.getUserMedia({
        audio: true
    });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    statusDiv.innerHTML = "🎙️ Recording...";
    recordBtn.disabled = true;
    stopBtn.disabled = false;
    sendBtn.disabled = true;
    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };
    mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, {
            type: "audio/webm"
        });
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPlayback.src = audioUrl;
        window.recordedBlob = audioBlob;
        statusDiv.innerHTML = "✅ Recording Finished";
        sendBtn.disabled = false;
    };
};
stopBtn.onclick = () => {
    mediaRecorder.stop();
    recordBtn.disabled = false;
    stopBtn.disabled = true;
};
sendBtn.onclick = async () => {
    statusDiv.innerHTML = "⏳ Uploading Audio...";
    const formData = new FormData();
    formData.append(
        "audio",
        window.recordedBlob,
        "recording.webm"
    );
    const response = await fetch("/transcribe", {
        method: "POST",
        body: formData
    });
    const data = await response.json();
    resultText.value = data.text;
    statusDiv.innerHTML = "✅ Transcription Complete";
};
</script>
</body>
</html>
"""
@app.route("/voice")
def voice():
    return render_template_string(HTML)
@app.route("/transcribe", methods=["POST"])
def transcribe():
    uploaded_file = request.files["audio"]
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    webm_path = os.path.join(
        temp_dir, f"recording_{timestamp}.webm")
    wav_path = os.path.join(temp_dir, f"recording_{timestamp}.wav")
    mp3_path = os.path.join(MP3_DIR, f"recording_{timestamp}.mp3")
    logit(mp3_path)
    
    uploaded_file.save(webm_path)
    logit("WEBM:", webm_path)
    logit("MP3 :", mp3_path)
    logit("WAV :", wav_path)
    # ------------------------------------------
    # SAVE MP3 PERMANENTLY
    # ------------------------------------------
    ffmpeg_mp3 = (
        f'ffmpeg -ss 2 -y -i "{webm_path}" '
        f'"{mp3_path}"'
    )
    logit(ffmpeg_mp3)
    os.system(ffmpeg_mp3)
    # ------------------------------------------
    # CREATE WAV FOR SPEECH RECOGNITION
    # ------------------------------------------
    ffmpeg_wav = (
        f'ffmpeg -y -i "{webm_path}" '
        f'-ar 16000 -ac 1 "{wav_path}"'
    )
    logit(ffmpeg_wav)
    os.system(ffmpeg_wav)
    recognizer = sr.Recognizer()
    text = ""
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            logit(text)
    except Exception as e:
        logit(e)
        text = f"ERROR: {str(e)}"
    # ------------------------------------------
    # CLEAN TEMP FILES ONLY
    # ------------------------------------------
    if os.path.exists(webm_path):
        os.remove(webm_path)
    if os.path.exists(wav_path):
        os.remove(wav_path)
    return jsonify({
        "text": text,
        "saved_mp3": os.path.basename(mp3_path)
    })
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

# --------------------------------------------------
# GET SUBDIRECTORIES
# --------------------------------------------------
def get_subdirs():
    dirs = []
    for d in os.listdir(SHARED_PATH):
        full = os.path.join(SHARED_PATH, d)
        if os.path.isdir(full):
            dirs.append(d)
    return sorted(dirs)
# --------------------------------------------------
# HTML
# --------------------------------------------------
HTML7 = """
<!doctype html>
<html>
<body style="background:#111;color:#eee;text-align:center">
<h2>Select Folder</h2>
<a href="/text_to_mp3" style="color:orange;font-size:20px;">TEXT → MP3</a>&nbsp;&nbsp;&nbsp;&nbsp;
<a href="/voice" style="color:orange;font-size:20px;">VOICE → MP3</a>
<form method="get">
<select name="folder">
{% for d in dirs %}
<option value="{{d}}" {% if d == current %}selected{% endif %}>{{d}}</option>
{% endfor %}
</select>
<button>LOAD</button>
</form>
<form method="post" action="/create_video">
<h2>Images</h2>
<div style="display:flex; flex-wrap:wrap; gap:10px; justify-content:center;">
{% for img in images %}
    <div style="width:180px; border:1px solid #333; padding:5px;">
        <img src="{{ url_for('static', filename='images/' + current + '/' + img) }}" style="width:100%;">
        <input type="checkbox" name="images" value="{{ img }}"><br>
        seq <input type="number" name="seq_{{ img }}" style="width:60px;">
    </div>
{% endfor %}
</div>
<h2>Audio</h2>
<div style="display:flex; flex-wrap:wrap; gap:15px; justify-content:center;">
{% for mp3 in mp3s %}
    <div style="width:250px; border:1px solid #333; padding:10px;">
        <input type="radio" name="audio" value="{{ mp3 }}"><br>
        <div style="font-size:12px; margin-bottom:5px;">{{ mp3 }}</div>
        <audio controls style="width:100%;">
            <source src="/mp3/{{ mp3 }}" type="audio/mpeg">
        </audio>
    </div>
{% endfor %}
</div>
<input type="hidden" name="folder" value="{{current}}">
<br><br>
<button>Create Video</button>
</form>
</body>
</html>
"""
# --------------------------------------------------
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
    return render_template_string(
        HTML7,
        dirs=dirs,
        images=images,
        mp3s=mp3s,
        current=current
    )
# --------------------------------------------------
def overlay_frame(src, frame, out):
    base = Image.open(src).convert("RGBA")
    frame = Image.open(frame).convert("RGBA").resize(base.size)
    Image.alpha_composite(base, frame).convert("RGB").save(out)
# --------------------------------------------------
def pad_audio(src, out, ms=250):
    audio = AudioSegment.from_mp3(src)
    silence = AudioSegment.silent(duration=ms)
    (silence + audio + silence).export(out, format="mp3")
# --------------------------------------------------
@app.route("/mp3/<filename>")
def serve_mp3(filename):
    path = os.path.join(MP3_DIR, filename)
    logit("Serving MP3:", path)
    return send_file(path, mimetype="audio/mpeg")
# --------------------------------------------------
@app.route("/create_video", methods=["POST"])
def create_video():
    folder = request.form.get("folder")
    base_path = os.path.join(SHARED_PATH, folder)
    selected_images = request.form.getlist("images")
    selected_audio = request.form.get("audio")
    ordered = []
    for img in selected_images:
        seq = request.form.get(f"seq_{img}")
        ordered.append((int(seq), img))
    ordered_images = [x[1] for x in sorted(ordered)]
    processed = []
    for i, img in enumerate(ordered_images):
        src = os.path.join(base_path, img)
        out = os.path.join(base_path, f"_frame_{i}.jpg")
        if os.path.exists(FRAME_PATH):
            overlay_frame(src, FRAME_PATH, out)
        else:
            Image.open(src).convert("RGB").save(out)
        processed.append(out)
    audio_src = os.path.join(MP3_DIR, secure_filename(selected_audio))
    padded_audio = os.path.join(MP3_DIR, "_audio_pad.mp3")
    pad_audio(audio_src, padded_audio)
    audio_clip = AudioFileClip(padded_audio)
    duration = audio_clip.duration / len(processed)
    clips = [ImageClip(p).set_duration(duration) for p in processed]
    final = concatenate_videoclips(clips).set_audio(audio_clip)
    final_video = os.path.join(VIDEO_DIR, f"{UNIQUE}_final.mp4")
    final.write_videofile(
        final_video,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )
    return send_file(final_video, mimetype="video/mp4")
# --------------------------------------------------
KOKORO_URL = "http://localhost:8880/v1/audio/speech"
def generate_kokoro_mp3(text, out, voice=DEFAULT_VOICE):
    payload = {
        "model": "kokoro",
        "voice": voice,
        "format": "mp3",
        "input": text.strip()
    }
    r = requests.post(KOKORO_URL, json=payload, timeout=800)
    with open(out, "wb") as f:
        f.write(r.content)
# --------------------------------------------------
@app.route("/text_to_mp3", methods=["GET","POST"])
def text_to_mp3():
    mp3 = None
    text = ""
    selected_voice = DEFAULT_VOICE
    if request.method == "POST":
        text = request.form.get("text","")
        selected_voice = request.form.get("voice",DEFAULT_VOICE)
        safe = "_".join(text[:20].split())
        mp3_name = f"{safe}.mp3"
        out = os.path.join(MP3_DIR, mp3_name)
        generate_kokoro_mp3(text, out, selected_voice)
        mp3 = mp3_name
    return render_template_string("""
    <body style="background:#111;color:#eee;text-align:center">
    <h2>Kokoro TTS</h2>
    <a href="/">HOME</a>
    <form method="post">
        <textarea name="text" style="width:60%;height:120px">{{text}}</textarea><br><br>
        <select name="voice">
        {% for v in voices %}
            <option value="{{v}}" {% if v == selected_voice %}selected{% endif %}>{{v}}</option>
        {% endfor %}
        </select>
        <br><br>
        <button>Generate MP3</button>
    </form>
    {% if mp3 %}
        <h3>Preview</h3>
        <audio controls>
            <source src="/mp3/{{mp3}}">
        </audio>
    {% endif %}
    </body>
    """, text=text, voices=VOICES, selected_voice=selected_voice, mp3=mp3)
# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)