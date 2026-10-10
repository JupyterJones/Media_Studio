#!/home/jack/miniconda3/envs/PY39/bin/python

import os
import uuid
import subprocess
import requests
from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename
from icecream import ic
from flask import Flask, request, render_template_string
from flask import send_from_directory, redirect
import os
import uuid
import subprocess
from icecream import ic

app = Flask(__name__)

PROJECT_DIR = "static/ADS"
os.makedirs(PROJECT_DIR, exist_ok=True)
'''
https://gist.github.com/JupyterJones/0aea5806a684a661d50922d46c7452f4
This is a Flask Application That can join multiplt video formats:
What formats this FFmpeg script can decode from in practice
Even though this UI only lists a few extensions, FFmpeg can decode:
Many containers it can handle
MP4, MKV, MOV, AVI, WEBM, OGG, M4V, FLV, TS, MPEG, many more\n, Video 
codecs it can decode
H.264 / AVC, HEVC / H.265, VP8, VP9, AV1, MPEG-2, MPEG-4 ASP (DivX, XviD),
WMV, Theora, ProRes, DNxHD/DNxHR, MJPEG,
Many others (FFmpeg supports hundreds)
Audio codecs it can decode, AAC, MP3, Opus, Vorbis, AC-3, PCM, FLAC, ALAC,
DTS, WMA, Many more
'''

def run(cmd):
    ic("Running command:", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ic("Return code:", result.returncode)
    if result.stdout:
        ic(result.stdout.decode(errors="ignore"))
    if result.stderr:
        ic(result.stderr.decode(errors="ignore"))
    return result.returncode == 0


def normalize_video(src, dst):
    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-ar", "48000",
        dst
    ]
    return run(cmd)


def concat_videos(v1, v2, output_file):
    list_file = f"concat_{uuid.uuid4()}.txt"
    with open(list_file, "w") as f:
        f.write(f"file '{v1}'\n")
        f.write(f"file '{v2}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_file
    ]

    ok = run(cmd)
    os.remove(list_file)
    return ok

@app.route("/jointwo", methods=["GET"])
def jointwo():
    videos = []

    # Ensure project directory exists
    if not os.path.isdir(PROJECT_DIR):
        ic(f"Directory not found: {PROJECT_DIR}")
        return "<h2>Project directory does not exist.</h2>"

    for f in os.listdir(PROJECT_DIR):
        if f.lower().endswith((".mp4", ".mkv", ".ogg", ".webm", ".avi", ".mov")):
            full_path = os.path.join(PROJECT_DIR, f)
            try:
                mtime = os.path.getmtime(full_path)
                videos.append((f, mtime))
                ic(f"Found video: {f} | mtime: {mtime}")
            except Exception as e:
                ic(f"Error reading file time for {f}: {e}")

    videos.sort(key=lambda x: x[1], reverse=True)
    videos = [v[0] for v in videos]

    ic("Sorted videos newest-first:")
    ic(videos)

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Esperanza Full Pipeline</title>
      <style>
        body { background:#111; color:#f0f0f0; font-family:Segoe UI,system-ui,Arial; padding:18px; }
        .container { display:grid; grid-template-columns: 1fr 420px; gap:18px; align-items:start; }
        .panel { background:rgba(255,255,255,0.03); padding:14px; border-radius:10px; }
        textarea { width:100%; height:220px; padding:10px; border-radius:8px; border:none; background:#161616; color:#eee; resize:vertical; }
        input[type=file] { color:#eee; }
        button { background:#c71585; color:white; border:none; padding:10px 14px; border-radius:8px; cursor:pointer; font-weight:600; }
        .small { font-size:0.9rem; color:#bbb; margin-top:8px; }
        a {font-size:2vw;color:orange;}
      </style>
    </head>
    <body>
    <h2 style="font-family:Arial; color:white;">Video Joiner — Click to 
    Select Boxes ❤️</h2>
    <a style = "font-size:2vw;" href = "/">Create a Video</a><br /><br />
    <p style="color:white;">Click a video to assign it to Box 1 or Box 2.
    Selected videos are highlighted in blue.</p>

    <style>
    html, body { background-color: slategray; font-family: Arial; }
    .video-box {
        margin: 10px;
        padding: 5px;
        border: 2px solid #ccc;
        cursor: pointer;
        width: 240px;
        word-wrap: break-word;
        text-align: center;
        display: inline-block;
        vertical-align: top;
    }
    .video-name {
        margin-top: 5px;
        font-size: 0.9em;
        word-wrap: break-word;
        color: white;
    }
    .box-label {
        color: white;
        background-color: darkblue;
        display: block;
        padding: 3px 6px;
        border-radius: 4px;
        margin-top: 5px;
        text-align: center;
        font-weight: bold;
        visibility: hidden;
    }
    .video-box.selected .box-label {
        visibility: visible;
    }
    .video-box:hover { border-color: green; }
    button { margin-top: 20px; padding: 8px 16px; font-size: 1em; }
    </style>

    <form method="POST" action="/join" id="joinForm">
        <input type="hidden" name="video1" id="video1">
        <input type="hidden" name="video2" id="video2">
        <button type="submit">Join Videos</button>
    </form>

    <div>
    {% for v in videos %}
        <div class="video-box" data-filename="{{v}}">
            <video width="240" controls>
                <source src="/video/{{v}}" type="video/mp4">
                <source src="/video/{{v}}" type="video/webm">
                <source src="/video/{{v}}" type="video/mkv">
                Your browser does not support HTML5 video.
            </video>
            <div class="video-name">{{v}}</div>
            <div class="box-label"></div>
        </div>
    {% endfor %}
    </div>

    <script>
    let box1 = null;
    let box2 = null;

    document.querySelectorAll(".video-box").forEach(function(el){
        el.addEventListener("click", function(){
            const filename = el.getAttribute("data-filename");
            const label = el.querySelector(".box-label");

            if (!box1) {
                box1 = el;
                document.getElementById("video1").value = filename;
                el.classList.add("selected");
                label.textContent = "Box 1";
                el.style.border = "4px solid blue";
            } else if (!box2 && el !== box1) {
                box2 = el;
                document.getElementById("video2").value = filename;
                el.classList.add("selected");
                label.textContent = "Box 2";
                el.style.border = "4px solid blue";
            } else {
                if (el === box1) {
                    box1 = null;
                    document.getElementById("video1").value = "";
                    el.classList.remove("selected");
                    label.textContent = "";
                    el.style.border = "2px solid #ccc";
                } else if (el === box2) {
                    box2 = null;
                    document.getElementById("video2").value = "";
                    el.classList.remove("selected");
                    label.textContent = "";
                    el.style.border = "2px solid #ccc";
                }
            }
        });
    });
    </script>
    </body>
    '''

    return render_template_string(html, videos=videos)

'''
@app.route("/video/<path:filename>")
def serve_video(filename):
    return send_from_directory(PROJECT_DIR, filename)
'''

@app.route("/join", methods=["POST"])
def join_videos():
    v1 = request.form.get("video1")
    v2 = request.form.get("video2")

    if not v1 or not v2:
        return "Please select both Box 1 and Box 2", 400

    src1 = os.path.join(PROJECT_DIR, v1)
    src2 = os.path.join(PROJECT_DIR, v2)

    ic("Selected video 1:", src1)
    ic("Selected video 2:", src2)

    uid = str(uuid.uuid4())
    norm1 = os.path.join(PROJECT_DIR, f"norm1_{uid}.mkv")
    norm2 = os.path.join(PROJECT_DIR, f"norm2_{uid}.mkv")

    if not normalize_video(src1, norm1):
        return "Failed to normalize video 1"

    if not normalize_video(src2, norm2):
        return "Failed to normalize video 2"

    out_file = f"Publish_{uid}.mkv"
    out_path = os.path.join(PROJECT_DIR, out_file)

    if not concat_videos(norm1, norm2, out_path):
        return "Concat failed"

    os.remove(norm1)
    os.remove(norm2)

    return redirect(f"/video/{out_file}")


app.config['UPLOAD_FOLDER'] = 'static/ADS'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

TTS_API_URL = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE = "am_michael"
HEADERS = {"Content-Type": "application/json"}

HTML_PAGE = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Esperanza Full Pipeline</title>
      <style>
        body { background:#111; color:#f0f0f0; font-family:Segoe UI,system-ui,Arial; padding:18px; }
        .container { display:grid; grid-template-columns: 1fr 420px; gap:18px; align-items:start; }
        .panel { background:rgba(255,255,255,0.03); padding:14px; border-radius:10px; }
        textarea { width:100%; height:220px; padding:10px; border-radius:8px; border:none; background:#161616; color:#eee; resize:vertical; }
        input[type=file] { color:#eee; }
        button { background:#c71585; color:white; border:none; padding:10px 14px; border-radius:8px; cursor:pointer; font-weight:600; }
        .small { font-size:0.9rem; color:#bbb; margin-top:8px; }
        a {font-size:2vw;color:orange;}
      </style>
    </head>
    <body>
<h2>Upload Image and Enter Text</h2>
<a style = "font-size:2vw;" href = "/jointwo">Join Two Videos</a><br /><br />
<form method=post enctype=multipart/form-data>
  <input type=file name=image><br><br>
  <textarea name=text rows=10 cols=60 placeholder="Enter your image here..."></textarea><br><br>
  <input type=submit value=CREATE>
</form>
{preview}
</body>
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

    return render_template_string(HTML_PAGE, preview=preview_html)

@app.route('/video/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5100)
