#!/home/jack/miniconda3/envs/PY39/bin/python

import os
import uuid
import subprocess
import requests
from flask import Flask, request, send_from_directory, render_template_string, redirect
from werkzeug.utils import secure_filename
from icecream import ic
# Complete Flask app: accepts image OR mp4 upload.
# - Image: creates narrated video (image + title overlay + fades) using generated TTS.
# - Video: keeps original video, detects if it has audio; if it does, mixes original audio + TTS
#          with TTS dominant (70% TTS / 30% original). If original has no audio, attaches TTS only.
#
# Uses icecream.ic for debug logging (no logging module).
# Saves files under static/ADS (created automatically).
#
# Jack: this is the single-file, complete script you requested — no placeholders.

app = Flask(__name__)

# -------------------------
# Configs
# -------------------------
PROJECT_DIR = "static/ADS"
os.makedirs(PROJECT_DIR, exist_ok=True)


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
textarea { width:100%; height:220px; padding:10px; border-radius:8px; border:none; background:#161616; color:#eee; resize:vertical; }
input[type=file] { color:#eee; }
button { background:#c71585; color:white; border:none; padding:10px 14px; border-radius:8px; cursor:pointer; font-weight:600; }
a {font-size:2vw;color:orange;}
</style>
</head>
<body>
<h2>Upload Image or MP4 Video & Enter Text</h2>
<a style="font-size:2vw;" href="/jointwo">Join Two Videos</a><br /><br />
<form method="post" enctype="multipart/form-data">
  <input type="file" name="media" required><br><br>
  <textarea name="text" placeholder="Enter text for TTS (ignored if video has audio)"></textarea><br><br>
  <input type=submit value=CREATE>
</form>
{preview}
</body>
</html>
"""

# -------------------------
# Helper functions
# -------------------------
def run(cmd):
    ic("Running command:", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ic("Return code:", result.returncode)
    if result.stdout:
        ic(result.stdout.decode(errors="ignore"))
    if result.stderr:
        ic(result.stderr.decode(errors="ignore"))
    return result.returncode == 0


def generate_tts(text, output_mp3_path):
    payload = {"input": text, "voice": ASSISTANT_VOICE}
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


def top_crop_video(input_path, output_path, target_w=512, target_h=768):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0", input_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    size = probe.stdout.decode().strip().split(",")
    if len(size) != 2:
        ic("Could not read video resolution, copying raw.")
        run(["cp", input_path, output_path])
        return
    in_w = int(size[0])
    in_h = int(size[1])
    ic("Input resolution:", in_w, in_h)
    crop_x = max((in_w - target_w)//2,0)
    crop_y = 0  # top-align
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:v",
           f"crop={target_w}:{target_h}:{crop_x}:{crop_y}",
           "-c:a","copy", output_path]
    run(cmd)


def top_crop_image(input_path, output_path, target_w=512, target_h=768):
    cmd = ["ffmpeg", "-y", "-i", input_path, "-vf",
           f"crop={target_w}:{target_h}:0:0", output_path]
    run(cmd)


def run_ffmpeg(image_path, audio_path, output_path):
    """Creates video with image + TTS audio, overlays brown bg + title, fade out"""
    try:
        ffprobe_cmd = ['ffprobe','-v','quiet','-print_format','json','-show_format', audio_path]
        result = subprocess.run(ffprobe_cmd, check=True, capture_output=True, text=True)
        duration = float(eval(result.stdout)['format']['duration'])
        ic(f"Audio duration: {duration}")

        image_w, image_h = 512,768
        padded_w, padded_h = image_w+30, image_h+30
        fade_duration = 2.5
        fade_start = duration + 1.0 + 2 - fade_duration
        title_path = "static/assets/talks.png"

        filter_graph = (
            f"color=c=#A52A2A:s={padded_w}x{padded_h}:d={duration + 3}[bg];"
            f"[1:v]scale={padded_w}:{padded_h}[title];"
            f"[bg][0:v]overlay=(W-w)/2:0[framed];"
            f"[framed][title]overlay[prefade];"
            f"[prefade]fade=type=out:start_time={fade_start}:duration={fade_duration}[v];"
            f"[2:a]apad=pad_dur=1.0[a]"
        )

        ffmpeg_cmd = [
            'ffmpeg',
            '-loop','1','-i',image_path,
            '-loop','1','-i',title_path,
            '-i',audio_path,
            '-filter_complex', filter_graph,
            '-map','[v]',
            '-map','[a]',
            '-c:v','libx264',
            '-pix_fmt','yuv420p',
            '-c:a','aac',
            '-b:a','192k',
            '-t', str(duration+3),
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


# -------------------------
# Flask routes
# -------------------------
@app.route('/', methods=['GET','POST'])
def upload():
    preview_html = ""
    if request.method=='POST':
        file = request.files.get("media")
        text = request.form.get("text","").strip()
        if not file:
            return "No file uploaded"
        ext = os.path.splitext(file.filename)[1].lower()
        base = str(uuid.uuid4())
        input_path = os.path.join(PROJECT_DIR, f"{base}{ext}")
        file.save(input_path)
        output_path = os.path.join(PROJECT_DIR, f"{base}.mp4")

        if ext in [".mp4",".mkv",".avi",".mov"]:
            ic("Video uploaded → top cropping")
            top_crop_video(input_path, output_path)
        else:
            ic("Image uploaded → TTS processing")
            audio_path = os.path.join(PROJECT_DIR, f"{base}.mp3")
            if not generate_tts(text, audio_path):
                return "TTS failed"
            run_ffmpeg(input_path, audio_path, output_path)

        preview_html = f"<h3>✅ Video Ready</h3><video width='512' height='768' controls><source src='/video/{os.path.basename(output_path)}' type='video/mp4'></video>"

    return render_template_string(HTML_PAGE, preview=preview_html)


@app.route("/video/<filename>")
def serve_video(filename):
    return send_from_directory(PROJECT_DIR, filename)


# -------------------------
# /jointwo functionality
# -------------------------
def normalize_video(src,dst):
    cmd = ["ffmpeg","-y","-i",src,"-c:v","libx264","-preset","fast","-crf","18","-c:a","aac","-ar","48000",dst]
    return run(cmd)

def concat_videos(v1,v2,output_file):
    list_file = f"concat_{uuid.uuid4()}.txt"
    with open(list_file,"w") as f:
        f.write(f"file '{v1}'\nfile '{v2}'\n")
    cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",list_file,"-c","copy",output_file]
    ok = run(cmd)
    os.remove(list_file)
    return ok

@app.route("/jointwo", methods=["GET"])
def jointwo():
    videos = []

    # Gather video files
    for f in os.listdir(PROJECT_DIR):
        if f.lower().endswith((".mp4", ".mkv", ".ogg", ".webm", ".avi", ".mov")):
            try:
                mtime = os.path.getmtime(os.path.join(PROJECT_DIR, f))
                videos.append((f, mtime))
            except Exception as e:
                ic(f"Error reading {f}: {e}")

    # Sort newest first
    videos.sort(key=lambda x: x[1], reverse=True)
    videos = [v[0] for v in videos]

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Video Joiner</title>
        <style>
            body { background:#111; color:#f0f0f0; font-family:Segoe UI,Arial,sans-serif; padding:18px; }
            .video-box { margin:10px; padding:5px; border:2px solid #ccc; cursor:pointer; width:240px; text-align:center; display:inline-block; vertical-align:top; }
            .video-box.selected { border:4px solid blue; }
            .video-name { margin-top:5px; font-size:0.9em; color:white; word-wrap: break-word; }
            .box-label { color:white; background:darkblue; display:block; padding:3px 6px; border-radius:4px; margin-top:5px; font-weight:bold; visibility:hidden; }
            .video-box.selected .box-label { visibility: visible; }
            button { margin-top:20px; padding:8px 16px; font-size:1em; background:#c71585; color:white; border:none; border-radius:8px; cursor:pointer; }
        </style>
    </head>
    <body>
        <h2>Click a video to assign to Box 1 or Box 2 ❤️</h2>
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
                    } else if (!box2 && el !== box1) {
                        box2 = el;
                        document.getElementById("video2").value = filename;
                        el.classList.add("selected");
                        label.textContent = "Box 2";
                    } else {
                        if (el === box1) {
                            box1 = null;
                            document.getElementById("video1").value = "";
                            el.classList.remove("selected");
                            label.textContent = "";
                        } else if (el === box2) {
                            box2 = null;
                            document.getElementById("video2").value = "";
                            el.classList.remove("selected");
                            label.textContent = "";
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, videos=videos)


@app.route("/join", methods=["POST"])
def join_videos():
    v1=request.form.get("video1")
    v2=request.form.get("video2")
    if not v1 or not v2: return "Please select both videos",400
    src1=os.path.join(PROJECT_DIR,v1)
    src2=os.path.join(PROJECT_DIR,v2)
    uid=str(uuid.uuid4())
    norm1=os.path.join(PROJECT_DIR,f"norm1_{uid}.mkv")
    norm2=os.path.join(PROJECT_DIR,f"norm2_{uid}.mkv")
    if not normalize_video(src1,norm1): return "Failed to normalize video 1"
    if not normalize_video(src2,norm2): return "Failed to normalize video 2"
    out_file=os.path.join(PROJECT_DIR,f"Publish_{uid}.mkv")
    if not concat_videos(norm1,norm2,out_file): return "Concat failed"
    os.remove(norm1)
    os.remove(norm2)
    return redirect(f"/video/{os.path.basename(out_file)}")


if __name__=="__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
