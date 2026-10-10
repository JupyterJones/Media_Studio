#!/home/jack/miniconda3/envs/PY39/bin/python

# ---------------------------------------
# Clean + Organized Imports
# ---------------------------------------

# Standard Library
import os
import re
import io
import sys
import time
import glob
import uuid
import json
import shlex
import random
import shutil
import inspect
import subprocess
from datetime import datetime
from io import BytesIO
# Flask
from flask import (
    Flask, request, render_template_string, send_from_directory,
    Response, redirect, url_for
)
from werkzeug.utils import secure_filename
# Image Processing
from PIL import (
    Image, ImageOps, ImageDraw, ImageFont, ImageFilter, ImageEnhance,
    ImageSequence, ImageChops, ImageStat, ImageColor, ImagePalette
)
# MoviePy
from moviepy.editor import *
from moviepy.video.compositing.transitions import slide_in
# Networking
import requests
# Debug
from icecream import ic
from time import sleep
# -------------------------------------------------
# CONFIG
# -------------------------------------------------

app = Flask(__name__)
PROJECT_DIR = "static/projects"           # where images, mp3, mp4 live and output is saved
UPLOADS_DIR = "static/projects"  # temporary workspace (created if missing)
MAX_SELECT = 10
# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
ENHANCER_URL = "http://localhost:11434/api/generate"
GENERATOR_URL = "http://localhost:11434/api/generate"
ENHANCER_MODEL = "llama3.2:3b"
GENERATOR_MODEL = "llama3.2:3b"
# ensure directories exist
for d in (PROJECT_DIR, UPLOADS_DIR):
    if not os.path.exists(d):
        os.makedirs(d)
        ic(f"Created directory: {d}")


app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024 * 1024  # 3 GB
# --------------- debug  logging ----------

# Logging function
def logit(message):
    try:
        # Get the current timestamp
        timestr = datetime.now().strftime('%A_%b-%d-%Y_%H-%M-%S')
        #print(f"timestr: {timestr}")

        # Get the caller's frame information
        caller_frame = inspect.stack()[1]
        filename = caller_frame.filename
        lineno = caller_frame.lineno

        # Convert message to string if it's a list
        if isinstance(message, list):
            message_str = ' '.join(map(str, message))
        else:
            message_str = str(message)

        # Construct the log message with filename and line number
        log_message = f"{timestr} - File: {filename}, Line: {lineno}: {message_str}\n"

        # Open the log file in append mode
        with open("exp_log.txt", "a") as file:
            # Write the log message to the file
            file.write(log_message)

            # Print the log message to the console
            print(log_message)

    except Exception as e:
        # If an exception occurs during logging, print an error message
        print(f"Error occurred while logging: {e}")

logit("App started")
# Define the log file path
LOG_FILE_PATH = 'static/app_log.txt'

# Ensure the log file exists or create it
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'w'):
        pass  # Create an empty log file if it doesn't exist

# Logging function
def logit(message):
    try:
        # Get the current timestamp
        timestr = datetime.datetime.now().strftime('%A_%b-%d-%Y_%H-%M-%S')

        # Get the caller's frame information
        caller_frame = inspect.stack()[1]
        filename = caller_frame.filename
        lineno = caller_frame.lineno

        # Convert message to string if it's a list
        if isinstance(message, list):
            message_str = ' '.join(map(str, message))
        else:
            message_str = str(message)

        # Construct the log message with filename and line number
        log_message = f"{timestr} - File: {filename}, Line: {lineno}: {message_str}\n"

        # Open the log file in append mode
        with open(LOG_FILE_PATH, "a") as file:
            # Write the log message to the file
            file.write(log_message)

        # Print the log message to the console
        #print(log_message)

    except Exception as e:
        # If an exception occurs during logging, print an error message
        print(f"Error occurred while logging: {e}")
READ_LOG ='''<!-- read_log.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>read_log.html</title>

    <link
      rel="stylesheet"
      href="{{ url_for('static', filename='css/dark.css') }}"
    />
    <style>
      .media-container {
        display: flex;
        flex-wrap: wrap;
        margin: 20px 0; /* Spacing above and below the section */
      }

      .media-item {
        margin: 10px; /* Spacing between items */
        padding: 10px;
        border: 1px solid #ccc; /* Optional: for visibility */
        border-radius: 8px; /* Optional: rounded corners */
        width: calc(30% - 20px); /* Adjust for responsive layout */
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* Optional: adds shadow effect */
        text-align: center; /* Centering text */
      }
      .mediaitem {
        margin: 10px; /* Spacing between items */
        padding: 10px;
        border: 1px solid #ccc; /* Optional: for visibility */
        border-radius: 8px; /* Optional: rounded corners */
        width: calc(20% - 20px); /* Adjust for responsive layout */
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* Optional: adds shadow effect */
        text-align: center; /* Centering text */
      }
      button {
        padding: 10px 15px; /* Consistent padding */
        font-size: 1.6vw; /* Better sizing */
        cursor: pointer;
        margin-bottom: 5px; /* Space below button */
      }

      .audio-label {
        display: block; /* Set to block for better spacing */
        margin-top: 5px; /* Add some space above the label */
        color: orange; /* Add color */
        word-wrap: break-word; /* Wrap text if too long */
      }
      video {
        width: 250px;
        height: auto;
      }
      .ltblue {
        background-color: lightblue;
        
      }
      .ltgreen {
        background-color: lightgreen;

        
      }
      ul li {
        list-style-type: none;
        color: white;
        font-size: 20px;
      }
      .dred {
        background-color: darkred;

        
      }
    </style>
  </head>
  <body>
    <a href="/readlog"><button>Refresh</button></a><br />
    <a href="/delete_log"><button class = "dred">Delete Log</button></a><br />
    <a href="/"><button>Home</button></a>
    <h1>rendered_string READ_LOG</h1>
    <p>The log file created by logit function.</p>


<ul>
    {% for log in log_content %}
        <li>{{ log }}</li>
    {% endfor %}
</ul>

'''   
@app.route('/readlog')
def readlog():
    logdatas = open(LOG_FILE_PATH, "r").read().split("\n")
    logit(logdatas)
    return render_template_string(READ_LOG , log_content=logdatas)
# Logging function

def readlog():
    log_file_path = 'static/app_log.txt'    
    with open(log_file_path, "r") as Input:
        logdata = Input.read()
    # print last entry
    logdata = logdata.split("\n")
    return logdata
@app.route('/delete_log')
def delete_log():
    open(LOG_FILE_PATH, "w").close()
    logit("Log file deleted successfully")
    return redirect('/view_log')
VIEW_LOG="""<!-- view_log.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>view_log.html</title>

    <link
      rel="stylesheet"
      href="{{ url_for('static', filename='css/dark.css') }}"
    />
    <style>
      .media-container { display: flex; flex-wrap: wrap; margin: 20px 0; /* Spacing above and below the section */ }
      .media-item { margin: 10px; /* Spacing between items */
        padding: 10px; border: 1px solid #ccc; /* Optional: for visibility */
        border-radius: 8px; /* Optional: rounded corners */ width: calc(30% - 20px); /* Adjust for responsive layout */ box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* Optional: adds shadow effect */
        text-align: center; /* Centering text */ }
      .mediaitem { margin: 10px; /* Spacing between items */
        padding: 10px; border: 1px solid #ccc; /* Optional: for visibility */
        border-radius: 8px; /* Optional: rounded corners */
        width: calc(20% - 20px); /* Adjust for responsive layout */
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* Optional: adds shadow effect */ text-align: center; /* Centering text */ }
      button { padding: 10px 15px; /* Consistent padding */
        font-size: 1.6vw; /* Better sizing */ cursor: pointer;
        margin-bottom: 5px; /* Space below button */ }
      .audio-label { display: block; /* Set to block for better spacing */
        margin-top: 5px; /* Add some space above the label */
        color: orange; /* Add color */ word-wrap: break-word; /* Wrap text if too long */ }
      video { width: 250px; height: auto; }
      .ltblue { background-color: lightblue; }
      .ltgreen { background-color: lightgreen; }
      .dred { background-color: darkred; }
      ul li { list-style-type: none;
        color: lightgreen;
        font-size: 20px; }
    </style>
  </head>
  <body>
    <a href="/readlog"><button>Refresh</button></a><br />
    <a href="/delete_log"><button class = "dred">Delete Log</button></a><br />
    <a href="/"><button>Home</button></a>
    <h1>view_log.html</h1>
    <p>The log file created by logit function.</p>


<ul>
    {% for log in log_content %}
        <li>{{ log }}</li>
    {% endfor %}
</ul>
"""



# Logging function
@app.route('/view_log', methods=['GET', 'POST'])
def view_log():
    data = readlog()
    return render_template_string(VIEW_LOG, data=data)
# ---------------- helpers ----------------
def list_media():
    """Return dict of lists: images, mp3s, mp4s sorted newest -> oldest by mtime"""
    entries = []
    for fname in os.listdir(PROJECT_DIR):
        path = os.path.join(PROJECT_DIR, fname)
        if not os.path.isfile(path):
            continue
        mtime = os.path.getmtime(path)
        entries.append((mtime, fname))
    entries.sort(reverse=True, key=lambda x: x[0])

    images, mp3s, mp4s = [], [], []
    for _, fname in entries:
        lower = fname.lower()
        if lower.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff")):
            images.append(fname)
        elif lower.endswith(".mp3"):
            mp3s.append(fname)
        elif lower.endswith(".mp4"):
            mp4s.append(fname)
    return {"images": images, "mp3s": mp3s, "mp4s": mp4s}

def run_cmd(cmd):
    """Run shell command, log and raise on error"""
    ic(" ".join(cmd))
    subprocess.run(cmd, check=True)

def ffprobe_duration(path):
    """Return duration in seconds of media file"""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", path]
    ic("ffprobe:", " ".join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(p.stdout.strip())
    except Exception as e:
        ic("ffprobe parse error", p.stdout, e)
        return 0.0

def sanitize_filename(fn):
    """Very simple sanitize"""
    return fn.replace("..", "").replace("/", "").replace("\\", "")


# ------ add frame
def add_title_image(video_path, hex_color="#A52A2A"):
    from icecream import ic
    # Define the directory path
    directory_path = "temp"
    # Check if the directory exists
    if not os.path.exists(directory_path):
        # If not, create it
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")

    # Load the video file and title image
    video_clip = VideoFileClip(video_path)
    print(video_clip.size)
    width, height = video_clip.size
    title_image_path = "static/assets/talks.png"
    # Set the desired size of the padded video (e.g., video width + padding, video height + padding)
    padded_size = (width + 40, height + 40)

    # Calculate the position for centering the video within the larger frame
    x_position = (padded_size[0] - video_clip.size[0]) / 2
    y_position = (padded_size[1] - video_clip.size[1]) / 2
    # hex_color = "#09723c"
    # Remove the '#' and split the hex code into R, G, and B components
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Create an RGB tuple
    rgb_tuple = (r, g, b)

    # Create a blue ColorClip as the background
    blue_background = ColorClip(padded_size, color=rgb_tuple)

    # Add the video clip on top of the red background
    padded_video_clip = CompositeVideoClip(
        [blue_background, video_clip.set_position((x_position, y_position))])
    padded_video_clip = padded_video_clip.set_duration(video_clip.duration)
    # title_image_path = "/home/jack/Desktop/EXPER/static/assets/Title_Image02.png"
    # Load the title image
    title_image = ImageClip(title_image_path)

    # Set the duration of the title image
    title_duration = video_clip.duration
    title_image = title_image.set_duration(title_duration)

    print(video_clip.size)
    # Position the title image at the center and resize it to fit the video dimensions
    # title_image = title_image.set_position(("left", "top"))
    title_image = title_image.set_position((0, -5))
    # video_clip.size = (620,620)
    title_image = title_image.resize(padded_video_clip.size)

    # Position the title image at the center and resize it to fit the video dimensions
    # title_image = title_image.set_position(("center", "center")).resize(video_clip.size)

    # Create a composite video clip with the title image overlay
    composite_clip = CompositeVideoClip([padded_video_clip, title_image])
    
    uid = str(uuid.uuid4())  # Generate a unique ID using uuid
    final_filename = f"Ready_Post_{uid}.mp4"
    output_path = os.path.join(PROJECT_DIR, final_filename)

    # Export the final video with the background music
    composite_clip.write_videofile(output_path)
    
    ic(f"Final video with title saved to: {output_path}")
    return output_path

# ---------------- static route ----------------
@app.route("/projects/<path:filename>")
def serve_project_file(filename):
    filename = sanitize_filename(filename)
    logit(f"FILENAME: {filename}")
    return send_from_directory(PROJECT_DIR, filename)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'mp3', 'mp4'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return redirect(url_for('gallery', message="No file part in request"))
    
    files = request.files.getlist('files[]')
    
    if not files or all(f.filename == '' for f in files):
        return redirect(url_for('gallery', message="No files selected"))

    uploaded_count = 0
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(PROJECT_DIR, filename))
            uploaded_count += 1
            ic(f"Uploaded and saved: {filename}")
    
    return redirect(url_for('gallery', message=f"Successfully uploaded {uploaded_count} files."))

# ---------------- HTML ----------------
GALLERY_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Media Gallery - {{project_dir}}</title>
  <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 20px;
        background-color: #121212;
        color: #e0e0e0;
    }
    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        background-color: #1e1e1e;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    h2, h3 {
        color: #ffffff;
        border-bottom: 2px solid #007bff;
        padding-bottom: 10px;
    }
    .section { margin-bottom: 30px; }
    .thumb {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        background-color: #2c2c2c;
        padding: 10px;
        border-radius: 4px;
    }
    .thumb img {
        max-height: 80px;
        margin-right: 15px;
        border: 2px solid #444;
        border-radius: 4px;
        padding: 2px;
    }
    .thumb label { cursor: pointer; display: flex; align-items: center; }
    .thumb input[type="checkbox"], .thumb input[type="radio"] { margin-right: 10px; transform: scale(1.2); }
    .controls button {
        background-color: #007bff;
        color: white;
        padding: 14px 25px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        transition: background-color 0.3s;
    }
    .controls button:hover { background-color: #0056b3; }
    .note { color: #888; font-size: 90%; }
    .nav-link {
        display: inline-block;
        background-color: #333;
        color: #e0e0e0;
        padding: 12px 20px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 1.2em;
        text-decoration: none;
        transition: background-color 0.3s;
    }
    .nav-link:hover {
        background-color: #444;
        text-decoration: none;
    }
    audio, video {
        border-radius: 4px;
    }
    pre {
        white-space: pre-wrap;
        background-color: #252525;
        padding: 15px;
        border-radius: 4px;
        color: #d0d0d0;
        font-family: "Courier New", Courier, monospace;
        border: 1px solid #333;
    }
    a {font-size:3vw;color:yellow;}
  </style>
</head>
<body>
<div class="container">
  <h2>Media Gallery ({{project_dir}})</h2>
  <a href="/dream" class="nav-link">Dream a Story
  </a>&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;<a href ="/delete" class="nav-link">Delete or Trim a Video</a>&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href ="/view_log" class="nav-link">View Debug Log</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href ="/" class="nav-link">HOME</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="/create_text" class="nav-link">Create Mp3</a>&nbsp;&nbsp|&nbsp;&nbsp;
  <a href="/view_text" class="nav-link">View Text</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href ="/create_video" class="nav-link">Create Video</a>
 
  <div class="section">
      <h3>Upload Media</h3>
      <form action="{{ url_for('upload_files') }}" method="post" enctype="multipart/form-data">
        <input type="file" name="files[]" multiple style="padding: 10px; background: #333; border-radius: 4px; margin-bottom:10px;">
        <button type="submit" style="background-color: #28a745; padding: 12px 20px;">Upload Files</button>
        <p class="note">Accepted file types: jpg, jpeg, png, gif, webp, bmp, tiff, mp3, mp4</p>
      </form>
  </div>

  <p class="note">Sorted newest → oldest. Select exactly 10 images and one MP3 then click Create Video.</p>

  <form action="{{ url_for('create_video') }}" method="post">
    <div class="section">
      <h3>Images (select exactly 10)</h3>
      {% if images %}
        {% for img in images %}
          <div class="thumb">
            <input type="checkbox" name="images" value="{{ img }}" id="img_{{ loop.index0 }}">
            <label for="img_{{ loop.index0 }}">
              <img src="static/projects/{{ img }}" alt="{{ img }}">
              <div>
                <div><b>{{ img }}</b></div>
                <div class="note">Modified: {{ mtimes[img] }}</div>
              </div>
            </label>
          </div>
        {% endfor %}
      {% else %}
        <div>No images found</div>
      {% endif %}
    </div>

    <div class="section">
      <h3>MP3s (choose one)</h3>
      {% if mp3s %}
        {% for mp3 in mp3s %}
          <div class="thumb">
            <input type="radio" name="mp3" value="{{ mp3 }}" id="mp3_{{ loop.index0 }}">
            <label for="mp3_{{ loop.index0 }}"><b>{{ mp3 }}</b></label>
            &nbsp;&nbsp;
            <audio controls style="vertical-align:middle;height:40px;">
              <source src="static/projects/{{ mp3 }}" type="audio/mpeg">
            </audio>
            <div class="note" style="margin-left:auto; padding-left:10px;">Modified: {{ mtimes[mp3] }}</div>
          </div>
        {% endfor %}
      {% else %}
        <div>No mp3 files found</div>
      {% endif %}
    </div>

    <div class="controls">
      <button type="submit">Create Video from selected 10 images + mp3</button>
    </div>
  </form>

    <div class="section">
      <h3>Videos</h3>
      {% if mp4s %}
        {% for mp4 in mp4s %}
          <div style="margin-bottom:12px;">
            <b>{{ mp4 }}</b><br>
            <video controls width="320">
              <source src="static/projects/{{ mp4 }}" type="video/mp4">
            </video>
            <div class="note">Modified: {{ mtimes[mp4] }}</div>
          </div>
        {% endfor %}
      {% else %}
        <div>No mp4 files found</div>
      {% endif %}
    </div>

  {% if message %}
    <hr>
    <h3>Message</h3>
    <pre>{{ message }}</pre>
  {% endif %}
</div>
</body>
</html>
"""

# ---------------- gallery ----------------
@app.route("/", methods=["GET"])
def gallery():
    message = request.args.get('message', None)
    media = list_media()
    mtimes = {fn: datetime.fromtimestamp(os.path.getmtime(os.path.join(PROJECT_DIR, fn))).strftime("%Y-%m-%d %H:%M:%S")
              for fn in media["images"]+media["mp3s"]+media["mp4s"]}
    return render_template_string(GALLERY_HTML,
                                  images=media["images"],
                                  mp3s=media["mp3s"],
                                  mp4s=media["mp4s"],
                                  project_dir=PROJECT_DIR,
                                  mtimes=mtimes,
                                  message=message)

# ---------------- create video ----------------
@app.route("/create_video", methods=["POST"])
def create_video():
    selected_images = request.form.getlist("images")
    selected_mp3 = request.form.get("mp3", None)
    logit(selected_images)
    logit(selected_mp3)
    logs = []

    ic(f"Selected images: {selected_images}")
    ic(f"Selected mp3: {selected_mp3}")

    # validation
    if len(selected_images) != MAX_SELECT:
        msg = f"ERROR: You must select exactly {MAX_SELECT} images. You selected {len(selected_images)}."
        logs.append(msg)
        ic(msg)
        return render_gallery_with_message("\n".join(logs))

    if not selected_mp3:
        msg = "ERROR: You must select one MP3 file."
        logs.append(msg)
        ic(msg)
        return render_gallery_with_message("\n".join(logs))

    # sanitize filenames and paths
    sel_images = [sanitize_filename(i) for i in selected_images]
    sel_mp3 = sanitize_filename(selected_mp3)
    mp3_src = os.path.join(PROJECT_DIR, selected_mp3)
    logit(mp3_src)
    ic(mp3_src)
    for img in selected_images:
        if not os.path.exists(os.path.join(PROJECT_DIR, img)):
            msg = f"ERROR: image missing: {img}"
            logs.append(msg)
            ic(msg)
            return render_gallery_with_message("\n".join(logs))

    if not os.path.exists(mp3_src):
        msg = f"ERROR: mp3 missing: {sel_mp3}"
        logs.append(msg)
        ic(msg)
        return render_gallery_with_message("\n".join(logs))

    # pad audio with 0.5s silence start/end
    padded_mp3 = os.path.join(UPLOADS_DIR, f"padded_{uuid.uuid4().hex}.mp3")
    pad_cmd = ["ffmpeg", "-hide_banner", "-y", "-i", mp3_src, "-af", "adelay=500|500,apad=pad_dur=0.5", padded_mp3]
    try:
        run_cmd(pad_cmd)
        sleep(1)
        logs.append(f"Padded audio saved: {padded_mp3}")
    except subprocess.CalledProcessError as e:
        logs.append(f"ERROR padding audio: {e}")
        ic("ERROR padding audio", e)
        return render_gallery_with_message("\n".join(logs))

    audio_dur = ffprobe_duration(padded_mp3)
    logs.append(f"Padded audio duration: {audio_dur:.3f} seconds")
    per_image = audio_dur / MAX_SELECT
    logs.append(f"Per-image duration: {per_image:.3f} seconds")

    # create slides.txt with absolute paths
    slides_txt = os.path.join(UPLOADS_DIR, f"slides_{uuid.uuid4().hex}.txt")
    try:
        with open(slides_txt, "w", encoding="utf-8") as fh:
            for img in sel_images:
                img_path = os.path.abspath(os.path.join(PROJECT_DIR, img))
                fh.write(f"file '{img_path}'\n")
                fh.write(f"duration {per_image}\n")
            # repeat last
            last_img_path = os.path.abspath(os.path.join(PROJECT_DIR, sel_images[-1]))
            fh.write(f"file '{last_img_path}'\n")
        logs.append(f"Slides file created: {slides_txt}")
    except Exception as e:
        logs.append(f"ERROR creating slides file: {e}")
        ic("ERROR writing slides file", e)
        return render_gallery_with_message("\n".join(logs))

    # create slideshow video
    temp_video = os.path.join(UPLOADS_DIR, f"slideshow_{uuid.uuid4().hex}.mp4")
    create_slideshow_cmd = ["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", slides_txt,
                            "-vsync", "vfr", "-pix_fmt", "yuv420p", temp_video]
    try:
        run_cmd(create_slideshow_cmd)
        sleep(1)
        logs.append(f"Slideshow video created: {temp_video}")
    except subprocess.CalledProcessError as e:
        logs.append(f"ERROR creating slideshow video: {e}")
        ic("ERROR creating slideshow", e)
        return render_gallery_with_message("\n".join(logs))

    video_dur = ffprobe_duration(temp_video)
    logs.append(f"Slideshow duration: {video_dur:.3f} seconds")

    # merge video + audio
    final_name = f"video_from_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.mp4"
    final_path = os.path.join(PROJECT_DIR, final_name)
    merge_cmd = ["ffmpeg", "-hide_banner","-y", "-i", temp_video, "-i", padded_mp3,
                 "-c:v", "libx264", "-c:a", "aac", "-map", "0:v", "-map", "1:a", "-shortest", final_path]
    try:
        run_cmd(merge_cmd)
        sleep(1)
        logs.append(f"Final video created: {final_path}")
    except subprocess.CalledProcessError as e:
        logs.append(f"ERROR merging audio+video: {e}")
        ic("ERROR merging", e)
        return render_gallery_with_message("\n".join(logs))
    video_path = final_path    
    final_video = add_title_image(video_path, hex_color="#A52A2A")
    logs.append("SUCCESS: video created and saved to project directory.")
    logs.append(f"Final file: {os.path.basename(final_video)}")
    logs.append(f"Padded audio used: {os.path.basename(padded_mp3)}")
    logs.append(f"Slides source: {sel_images}")

    return render_gallery_with_message("\n".join(logs))

# ---------------- helper to render gallery with message ----------------
def render_gallery_with_message(message):
    media = list_media()
    mtimes = {fn: datetime.fromtimestamp(os.path.getmtime(os.path.join(PROJECT_DIR, fn))).strftime("%Y-%m-%d %H:%M:%S")
              for fn in media["images"]+media["mp3s"]+media["mp4s"]}
    return render_template_string(GALLERY_HTML,
                                  images=media["images"],
                                  mp3s=media["mp3s"],
                                  mp4s=media["mp4s"],
                                  project_dir=PROJECT_DIR,
                                  mtimes=mtimes,
                                  message=message)


OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
REQUEST_TIMEOUT = 1200

#DEFAULT_MODEL = "codellama:latest"
DEFAULT_MODEL = "llama3.2:3b" #very good
#DEFAULT_MODEL = "phi3:latest" # good -
#DEFAULT_MODEL = "mistral:7b"

TTS_API_URL = "http://localhost:8880/v1/audio/speech"

OUTPUT_DIR = "static/project"
HEADERS = {"Content-Type": "application/json"}

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    ic(f"Created output directory: {OUTPUT_DIR}")
@app.route('/favicons.ico')
def favicons():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/favicon.ico')
def favicon():
    # Set the size of the favicon
    size = (16, 16)

    # Create a new image with a transparent background
    favicon = Image.new('RGBA', size, (0, 0, 0, 0))

    # Create a drawing object
    draw = ImageDraw.Draw(favicon)

    # Draw a yellow square
    square_color = (255, 0, 255)
    draw.rectangle([(0, 0), size], fill=square_color)
    circle_color = (255, 0, 0) 
    # Draw a red circle
    circle_center = (size[0] // 2, size[1] // 2)
    circle_radius = size[0] // 3
    draw.ellipse(
        [(circle_center[0] - circle_radius, circle_center[1] - circle_radius),
         (circle_center[0] + circle_radius, circle_center[1] + circle_radius)],
        fill=circle_color
    )

    # Save the image to a memory buffer
    image_buffer = io.BytesIO()
    favicon.save(image_buffer, format='ICO')
    image_buffer.seek(0)

    return Response(image_buffer.getvalue(), content_type='image/x-icon')
# -------------------------------------------------
# CLEAN TEXT FOR TTS
# -------------------------------------------------
def clean_text_for_tts(text):
    ic("Cleaning AI text for TTS...")
    cleaned = re.sub(r'\([^)]*\)', '', text)
    cleaned = re.sub(r'[\"\*\_\[\]\{\}\<\>\']', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# -------------------------------------------------
def timestamp_filename(ext="txt"):
    return datetime.now().strftime("%Y%m%d_%H%M%S") + f".{ext}"

# -------------------------------------------------
# -------------------------------------------------
# HTML TEMPLATE FOR RESULTS
# -------------------------------------------------
RESULTS_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Join Result</title>
<style>
body { font-family: Arial; margin:40px; }
pre { white-space: pre-wrap; }
a {font-size:3vw;color:yellow;}
</style>
</head>
<body>

<h2>Processing Complete</h2>

{% if final_file %}
<p><b>Downloaded Output:</b> 
    <a href="/download/{{ final_file }}">{{ final_file }}</a>
</p>

<video controls width="640">
  <source src="/download/{{ final_file }}" type="video/mp4">
</video>
<br><br>
{% endif %}

{% if audio_file %}
<h3>Audio File</h3>
<audio controls>
  <source src="/download/{{ audio_file }}" type="audio/mpeg">
</audio>
<br><br>
{% endif %}

{% if video_file %}
<h3>Original Video</h3>
<video controls width="400">
  <source src="/download/{{ video_file }}" type="video/mp4">
</video>
<br><br>
{% endif %}

{% if text_content %}
<h3>Processing Log</h3>
<pre>{{ text_content }}</pre>
{% endif %}
<pre>
VOICES = [
    'bf_alice', 'bf_emma', 'bf_lily', 'bf_v0emma', 'bf_v0isabella',
    'af_alloy', 'af_aoede', 'af_bella', 'af_heart', 'af_jadzia',
    'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river',
    'af_sarah', 'af_sky', 'af_v0', 'af_v0bella', 'af_v0irulan',
    'af_v0nicole', 'af_v0sarah', 'af_v0sky', 'am_adam', 'am_echo',
    'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx',
    'am_puck', 'am_santa', 'am_v0adam', 'am_v0gurney', 'am_v0michael',
    'bm_daniel', 'bm_fable'
]
</pre>
</body>
</html>
"""

prompt_style_templates = {
    "gangster": (
        "Write a long, first-person story in the style of a Quentin Tarantino pulp fiction gangster. "
        "Use rough bar slang, curses, and chaotic memories. "
        "Do NOT include parentheses (), brackets [], or curly braces {{}}. "
        "Make it sound spoken aloud in a smoky tavern, talking about:\n{prompt}"
        ),

    "sailor": (
        "Write a long, first-person story in the style of a salty old sailor. "
        "Use rough bar slang, curses, and chaotic memories. "
        "Do NOT include parentheses (), brackets [], or curly braces {{}}. "
        "Make it sound spoken aloud in a smoky tavern, talking about:\n{prompt}"
    ),

    "tedtalk": (
        "Write a long, first-person narrative delivered in the style of a TED Talk or academic lecture. "
        "The tone should be confident, articulate, polished, and inspiring, with clear structure and strong rhetorical flow. "
        "Do NOT include parentheses (), brackets [], or curly braces {{}}. "
        "Present the speaker as explaining and reflecting thoughtfully on:\n{prompt}"
    ),

    "drseuss": (
        "Write a playful, rhyming, whimsical story in the style of Dr Seuss. "
        "Use bouncing rhythm, musical lines, and imaginative nonsense words. "
        "Keep it light, sing-song, colorful, and surreal. "
        "Do NOT include parentheses (), brackets [], or curly braces {{}}. "
        "Tell the tale about:\n{prompt}"
    ),

    "horror": (
        "Write a long, first-person horror story with creeping dread, unsettling imagery, and a slow rising sense of terror. "
        "Use vivid sensory detail and a whispered, confessional tone. "
        "Do NOT include parentheses (), brackets [], or curly braces {{}}. "
        "Tell the chilling account of:\n{prompt}"
    ),

    "arcanian": (
        "Write a long, first-person narrative in the style of the Arcanian mythos. "
        "The tone should be ancient, wise, cryptic, and subtly ominous, as if spoken through an intelligence not entirely human. "
        "Use poetic phrasing, cosmic hints, and a sense of timeless memory. "
        "Do NOT include parentheses (), brackets [], or curly braces {{}}. "
        "Speak of the events concerning:\n{prompt}"
    ),

    "humor": (
        "Write a long, first-person comedic story with absurd timing, playful exaggeration, and sarcastic commentary. "
        "Keep the tone quick, mischievous, bright, and full of surprising punchlines. "
        "Do NOT include parentheses (), brackets [], or curly braces {{}}. "
        "Make the speaker humorously ramble about:\n{prompt}"
    ),

    "romantic_flirty": (
        "Write a long, first-person story with a romantic and flirty tone. "
        "The style should be playful, charming, and a little teasing. "
        "Use witty banter and suggestive language, but keep it classy. "
        "Do NOT include parentheses (), brackets [], or curly braces {{}}. "
        "Describe a romantic encounter or a flirty conversation about:\n{prompt}"
    )
}

def query_streaming(model_name, prompt, selected_style="gangster"):



    # Select which style you want:



    structured_prompt = prompt_style_templates[selected_style].format(prompt=prompt)
    ic(f"Sending to model: {model_name}")
    ic(f"Prompt length: {len(structured_prompt)} characters")

    estimated_prompt_tokens = len(structured_prompt) // 4
    num_predict = 4096 - estimated_prompt_tokens
    ic(f"estimated_prompt_tokens: {estimated_prompt_tokens}")
    ic(f"num_predict set to: {num_predict}")

    payload = {
        "model": model_name,
        "prompt": structured_prompt,
        "stream": True,
        "num_predict": num_predict,
        "temperature": 0.9,
        "top_p": 0.95
    }

    stage_words = ['hiccup', 'slurs', 'staggers', 'stammers', 'grumbles', 'mutters']
    stage_pattern = r'\b(?:' + '|'.join(stage_words) + r')\b'

    def clean_text(text):
        text = re.sub(r'\([^()]*\)', ' ', text)
        text = re.sub(r'\[[^\[\]]*\]', ' ', text)
        text = re.sub(r'\{[^\{\}]*\}', ' ', text)
        text = re.sub(stage_pattern, '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s{2,}', ' ', text)
        return text

    try:
        with requests.post(
            OLLAMA_GENERATE_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            stream=True
        ) as response:

            response.raise_for_status()
            ic(f"HTTP status: {response.status_code}")

            full_text = ""
            start = time.time()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    part = data.get("response", "")
                    part = clean_text(part)
                    full_text += part

                    if data.get("done", False):
                        break

                except json.JSONDecodeError:
                    cleaned = clean_text(line)
                    full_text += cleaned

            elapsed = time.time() - start
            ic(f"Model completed in {elapsed:.2f} seconds\n")
            return full_text

    except Exception as e:
        ic(f"Error contacting model {model_name}: {e}")
        return f"ERROR: {e}"
  
def generate_tts(text, voice):
    filename = timestamp_filename("mp3")
    output_path = os.path.join(OUTPUT_DIR, filename)
    project_path = os.path.join(PROJECT_DIR, filename)
    payload = {
        "input": text,
        "voice": voice
    }

    try:
        ic(f"TTS sending first 40 chars:\n{text}...")
        response = requests.post(
            TTS_API_URL,
            json=payload,
            headers=HEADERS,
            timeout=680
        )

        if response.status_code != 200:
            ic(f"TTS ERROR {response.status_code}: {response.text}")
            return None

        # --------------------------------------------------------
        # Save raw MP3
        # --------------------------------------------------------
        with open(output_path, 'wb') as f:
            f.write(response.content)
        ic(f"TTS saved: {output_path}")

        # --------------------------------------------------------
        # Add 0.5s silence to start and end
        # --------------------------------------------------------
        padded_mp3 = output_path.replace(".mp3", "_padded.mp3")

        ffmpeg_pad = (
            f"ffmpeg -hide_banner -y -i {shlex.quote(output_path)} "
            f"-af adelay=500|500,apad=pad_len=500 "
            f"{shlex.quote(padded_mp3)}"
        )
        ic(ffmpeg_pad)

        pad_run = subprocess.run(
            ffmpeg_pad,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        sleep(1)
        if pad_run.returncode != 0:
            ic(f"ffmpeg pad error:\n{pad_run.stderr.decode()}")
            return output_path

        shutil.move(padded_mp3, output_path)
        ic(f"Padded with silence: {output_path}")

        # --------------------------------------------------------
        # Copy MP3 to project
        # --------------------------------------------------------
        ic(f"Attempting to copy from {output_path} to {project_path}")
        if not os.path.exists(output_path):
            ic(f"ERROR: Source file does not exist for copy: {output_path}")
        else:
            shutil.copy(output_path, project_path)
            ic(f"Copied to project folder: {project_path}")

        # --------------------------------------------------------
        # Convert to WAV for perfect sync in video
        # --------------------------------------------------------
        wav_output = output_path.replace(".mp3", ".wav")
        
        wav_command_str = (
            f"ffmpeg -hide_banner -y -i {shlex.quote(output_path)} "
            f"-ac 2 -ar 44100 "
            f"{shlex.quote(wav_output)}"
        )
        ic(wav_command_str)

        wav_run = subprocess.run(
            wav_command_str,
            shell=True,
            capture_output=True,
            text=True
        )
        sleep(1)
        if wav_run.returncode != 0:
            ic(f"WAV convert error:\n{wav_run.stderr}")
        else:
            ic(f"WAV created: {wav_output}")

        # Return MP3 path (padded) for video use
        return output_path

    except Exception as e:
        ic(f"TTS failure: {e}")
        return None

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
<title>AI Story + TTS</title>
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 20px;
        background-color: #121212;
        color: #e0e0e0;
    }
    .container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #1e1e1e;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    h2, h3 {
        color: #ffffff;
        border-bottom: 2px solid #ff4500;
        padding-bottom: 10px;
    }
    textarea, input[type=text], select {
        width: 100%;
        padding: 12px;
        margin-bottom: 15px;
        border: 1px solid #333;
        border-radius: 4px;
        background-color: #2c2c2c;
        color: #e0e0e0;
        box-sizing: border-box; /* Important */
    }
    button {
        background-color: #ff4500;
        color: white;
        padding: 14px 25px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        transition: background-color 0.3s;
    }
    button:hover {
        background-color: #e03e00;
    }
    a {
        color: #ff8c69; /* Lighter orange for links */
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    .results-container {
        border:1px solid #333;
        padding:15px;
        margin-top: 20px;
        border-radius: 8px;
        background-color: #2c2c2c;
    }
    pre {
        white-space: pre-wrap;
        background-color: #252525;
        padding: 15px;
        border-radius: 4px;
        color: #d0d0d0;
        font-family: "Courier New", Courier, monospace;
    }
    audio {
        margin-top:10px;
        width:100%;
    }
    .nav-link {
        display: inline-block;
        background-color: #333;
        color: #e0e0e0;
        padding: 12px 20px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 1.2em;
        text-decoration: none;
        transition: background-color 0.3s;
    }
    .nav-link:hover {
        background-color: #444;
        text-decoration: none;
    }
    a {font-size:3vw;color:yellow;}
</style>
</head>
<body>
<div class="container">
    <h2>AI Story + TTS Generator</h2>
    <a href ="/" class="nav-link">Create a Video</a>&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;<a href ="/delete" class="nav-link">Delete or Trim a Video</a>&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;<a href ="/view_text" class="nav-link">View Text</a>&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;<a href ="/enhance" class="nav-link">Enhance Text</a>
    <form method="POST">
        <label for="prompt"><b>Prompt:</b></label><br>
        <textarea name="prompt" id="prompt" required>{{prompt}}</textarea><br><br>

        <label for="style-select"><b>Prompt Style:</b></label><br>
        <select name="style" id="style-select" required>
            {% for s in PROMPT_STYLES %}
            <option value="{{ s }}" {% if s == style %}selected{% endif %}>{{ s.title() }}</option>
            {% endfor %}
        </select><br><br>

        <label for="voice-select"><b>Voice (Good: am_v0michael):</b></label><br>
        <select name="voice" id="voice-select" required>
            {% for v in VOICES %}
            <option value="{{ v }}" {% if v == voice %}selected{% endif %}>{{ v }}</option>
            {% endfor %}
        </select><br><br>

        <button type="submit">Generate</button>
    </form>

    {% if text_path or mp3_file %}
    <div class="results-container">
    <h3>Results</h3>

    {% if text_content %}
    <h4>Generated Story</h4>
    <pre style="white-space:pre-wrap; background: #1e1e1e; border: 1px solid #333; padding: 10px;">{{ text_content }}</pre>
    {% endif %}

    {% if text_file %}
    <p><b>Download Text:</b> <a href="/download/{{ text_file }}">{{ text_file }}</a></p>
    {% endif %}

    {% if mp3_file %}
    <p><b>Download MP3:</b> <a href="/download/{{ mp3_file }}">{{ mp3_file }}</a></p>
    <audio controls>
        <source src="/download/{{ mp3_file }}" type="audio/mpeg">
        Your browser does not support audio playback.
    </audio>
    {% endif %}
    </div>
    {% endif %}

    <h3>Available Voices</h3>
    <pre>{{ VOICES | join(', ') }}</pre>
</div>
</body>
</html>
"""
VOICES = [
    'bf_alice', 'bf_emma', 'bf_lily', 'bf_v0emma', 'bf_v0isabella',
    'af_alloy', 'af_aoede', 'af_bella', 'af_heart', 'af_jadzia',
    'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river',
    'af_sarah', 'af_sky', 'af_v0', 'af_v0bella', 'af_v0irulan',
    'af_v0nicole', 'af_v0sarah', 'af_v0sky', 'am_adam', 'am_echo',
    'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx',
    'am_puck', 'am_santa', 'am_v0adam', 'am_v0gurney', 'am_v0michael',
    'bm_daniel', 'bm_fable'
]
@app.route("/dream", methods=["GET", "POST"])
def index():
    prompt = ""
    voice = "am_v0michael" # A good default
    style = list(prompt_style_templates.keys())[0] # Default to the first style
    text_path = None
    mp3_path = None
    text_content = None # To show processing log

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        voice = request.form.get("voice", "").strip()
        style = request.form.get("style", "").strip()

        ic(f"Web prompt: {prompt[:40]}...")
        ic(f"Using voice: {voice}")
        ic(f"Using style: {style}")

        raw = query_streaming(DEFAULT_MODEL, prompt, style)
        cleaned = clean_text_for_tts(raw)
        text_content = cleaned # pass content to template

        text_filename = timestamp_filename("txt")
        text_path = os.path.join(OUTPUT_DIR, text_filename)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(cleaned)
        ic(f"Text saved: {text_path}")

        mp3_path = generate_tts(cleaned, voice)

        return render_template_string(
            HTML_FORM,
            prompt=prompt,
            voice=voice,
            style=style,
            text_path=text_path,
            text_content=text_content,
            text_file=os.path.basename(text_path),
            mp3_file=os.path.basename(mp3_path) if mp3_path else None,
            VOICES=VOICES,
            PROMPT_STYLES=prompt_style_templates.keys()
        )

    return render_template_string(
        HTML_FORM,
        prompt=prompt,
        voice=voice,
        style=style,
        text_path=None,
        text_content=None,
        VOICES=VOICES,
        PROMPT_STYLES=prompt_style_templates.keys()
    )
# ------------------
# Allow very large uploads (3GB here)
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024 * 1024

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


def get_duration(input_file):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration = float(result.stdout.strip())
    return duration

def run_cmd(cmd):
    ic(" ".join(cmd))
    subprocess.run(cmd, check=True)

@app.route("/form_page", methods=["GET"])
def form_page():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Join Audio + Video</title>
</head>
<body>
<h2>Upload MP3 and MP4 to Join</h2>
<form action="/join" method="post" enctype="multipart/form-data">
    <label>Audio (mp3):</label>
    <input type="file" name="audio" accept=".mp3"><br><br>
    <label>Video (mp4):</label>
    <input type="file" name="video" accept=".mp4"><br><br>
    <input type="submit" value="Process">
</form>
</body>
</html>
"""

@app.route("/join", methods=["POST"])
def join_audio_video():

    if "audio" not in request.files or "video" not in request.files:
        return jsonify({"error": "Must upload 'audio' (mp3) and 'video' (mp4)"}), 400

    audio_file = request.files["audio"]
    video_file = request.files["video"]

    if audio_file.filename == "":
        return jsonify({"error": "Missing audio filename"}), 400

    if video_file.filename == "":
        return jsonify({"error": "Missing video filename"}), 400

    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    audio_path = os.path.join("uploads", audio_file.filename)
    video_path = os.path.join("uploads", video_file.filename)

    audio_file.save(audio_path)
    video_file.save(video_path)

    ic(f"Saved audio: {audio_path}")
    ic(f"Saved video: {video_path}")

    audio_duration = get_duration(audio_path)
    video_duration = get_duration(video_path)

    ic(f"Original audio duration: {audio_duration}")
    ic(f"Original video duration: {video_duration}")

    padded_audio = os.path.join("uploads", "audio_padded.mp3")
    pad_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i", audio_path,
        "-af", "apad=pad_dur=0.5,adelay=500|500",
        padded_audio
    ]
    run_cmd(pad_cmd)
    sleep(1)
    new_audio_duration = get_duration(padded_audio)
    ic(f"Padded audio duration: {new_audio_duration}")

    if video_duration == 0:
        return jsonify({"error": "Video duration is zero"}), 500

    speed_factor = video_duration / new_audio_duration
    ic(f"Speed factor: {speed_factor}")

    adjusted_video = os.path.join("uploads", "video_adjusted.mp4")
    speed_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i", video_path,
        "-filter:v", f"setpts={speed_factor}*PTS",
        "-an",
        adjusted_video
    ]
    run_cmd(speed_cmd)
    sleep(1)
    unique_id = str(uuid4())
    final_output = os.path.join("uploads", f"final_joined_{unique_id}.mp4")

    merge_cmd = [
        "ffmpeg",
        "-hide_banner", 
        "-y",
        "-i", adjusted_video,
        "-i", padded_audio,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        final_output
    ]
    run_cmd(merge_cmd)
    sleep(1)
    ic(f"Created final: {final_output}")

    return jsonify({
        "status": "completed",
        "output": final_output
    })
# delete or trim

BASE_DIR = os.getcwd()
PROJECT_DIR = os.path.join(BASE_DIR, "static", "projects")

# ensure directory exists
if not os.path.isdir(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)
    ic("Created project directory:", PROJECT_DIR)


# ----------------------------- PARSE TIME -----------------------------
def parse_time(t):
    """
    Parse HH:MM:SS, MM:SS, or SS string to total seconds (int)
    """
    try:
        parts = t.strip().split(':')
        parts = [int(p) for p in parts]
        if len(parts) == 3:
            return parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2:
            return parts[0]*60 + parts[1]
        elif len(parts) == 1:
            return parts[0]
    except Exception as e:
        ic("Time parse error:", e)
    return 0


# ----------------------------- TRIM FUNCTION -----------------------------
def trim_video(input_path, seconds):
    """
    Create a trimmed copy using originalname_trimmed.ext
    Ensures MP4 timestamps are rewritten so duration is correct.
    """
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_trimmed{ext}"

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i", input_path,
        "-t", str(seconds),
        "-c", "copy",
        "-map", "0",
        "-avoid_negative_ts", "make_zero",
        output_path
    ]

    ic("Running trim command:", cmd)

    try:
        subprocess.run(cmd, check=True)
        ic("Trim successful:", output_path)
        sleep(1)
        return output_path
    except Exception as e:
        ic("Trim error:", e)
        return None



# ----------------------------- TRIM ROUTE -----------------------------
@app.route("/trim/<filename>", methods=["POST"])
def trim_route(filename):
    time_input = request.form.get("trim_seconds", "").strip()
    seconds = parse_time(time_input)
    ic(seconds)
    if seconds <= 0:
        ic("Invalid trim time:", time_input)
        return redirect(url_for("delete"))

    input_path = os.path.join(PROJECT_DIR, filename)
    if not os.path.exists(input_path):
        ic("File missing:", input_path)
        return redirect(url_for("delete"))

    trim_video(input_path, seconds)
    return redirect(url_for("delete"))


# ----------------------------- HOME ROUTE -----------------------------
@app.route("/delete", methods=["GET", "POST"])
def delete():
    # Delete selected files
    if request.method == "POST" and "delete_items" in request.form:
        selected = request.form.getlist("delete_items")
        for fname in selected:
            fpath = os.path.join(PROJECT_DIR, fname)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                    ic("Deleted:", fpath)
                except Exception as e:
                    ic("Delete error:", e)
        return redirect(url_for("delete"))

    # Scan directory
    all_files = os.listdir(PROJECT_DIR)
    images = []
    videos = []

     # Get full paths
    full_paths = [os.path.join(PROJECT_DIR, f) for f in os.listdir(PROJECT_DIR)]

    images = []
    videos = []

    # Sort by modification time, newest first
    full_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    for fpath in full_paths:
        f = os.path.basename(fpath)
        fl = f.lower()
        if fl.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            images.append(f)
        elif fl.endswith((".mp4", ".m4v", ".mov", ".avi", ".mkv", ".webm", ".m4a")):
            videos.append(f)


    # Inline template
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Viewer</title>
        <style>
            body { font-family: Arial; background:#222; color:#eee; }
            h2 { margin-top: 30px; }
            .grid { display: flex; flex-wrap: wrap; gap: 20px; }
            .item { background:#333; padding:15px; border-radius:10px; width:220px; }
            img, video { width:100%; border-radius:8px; }
            .delete-box { margin-top:10px; }
            button { margin-top:20px; padding:10px 20px; font-size:16px; border:none; border-radius:8px; cursor:pointer; background:#ff5555; color:white; }
            button:hover { background:#ff2222; }
            .trim-form input { width:80px; padding:4px; margin-top:6px; }
            .trim-form button { background:#4499ff; margin-top:8px; }
            .trim-form button:hover { background:#1e7be5; }
            a {font-size:3vw;color:yellow;}
        </style>
    </head>
    <body>
        <h1>Static Project Browser</h1>
<a href ="/dream" class="nav-link">Dream</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href ="/" class="nav-link">HOME</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="/create_text">Create Mp3</a>&nbsp;&nbsp|;&nbsp;&nbsp;<a href="/view_text">View Text</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href ="/create_video" class="nav-link">Create Video</a>

        <form method="POST" action="{{ url_for('delete') }}" id="delete-form"></form>

        <h2>Images</h2>
        <div class="grid">
            {% for img in images %}
            <div class="item">
                <img src="{{ url_for('project_file', filename=img) }}">
                <div class="delete-box">
                    <input type="checkbox" name="delete_items" value="{{ img }}" form="delete-form"> Delete
                </div>
            </div>
            {% endfor %}
        </div>

        <h2>Videos</h2>
        <div class="grid">
            {% for vid in videos %}
            <div class="item">
                <video controls>
                    <source src="{{ url_for('project_file', filename=vid) }}">
                </video>

                <pre style="white-space: pre-wrap; word-break: break-word;">{{ vid }}</pre>

                <!-- TRIM FORM -->
                <form method="POST" action="{{ url_for('trim_route', filename=vid) }}" class="trim-form">
                    <label>Trim to (HH:MM:SS / MM:SS / seconds):</label><br>
                    <input type="text" name="trim_seconds" placeholder="00:10:00">
                    <button type="submit">Trim Copy</button>
                </form>

                <div class="delete-box">
                    <input type="checkbox" name="delete_items" value="{{ vid }}" form="delete-form"> Delete
                </div>
            </div>
            {% endfor %}
        </div>

        <button type="submit" form="delete-form">Delete Selected</button>

    </body>
    </html>
    """

    return render_template_string(html, images=images, videos=videos)


# ----------------------------- SERVE FILES -----------------------------
@app.route("/static/projects/<path:filename>")
def project_file(filename):
    return send_from_directory(PROJECT_DIR, filename)

#=============================


STYLE_OPTIONS = ["romantic", "sci-fi Arcanian", "cinematic", "humorous", "poetic", "spicy"]
SAVE_DIR = os.path.join(os.getcwd(), "static/projects")
os.makedirs(SAVE_DIR, exist_ok=True)

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def call_model(api_url, model, prompt):
    num_predict = 4096  # default or adjust dynamically
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "num_predict": num_predict,
        "temperature": 0.9,
        "top_p": 0.95
    }
    ic("Sending request:", payload)
    try:
        r = requests.post(api_url, json=payload, timeout=600)
        r.raise_for_status()
        data = r.json()
        ic("Model response:", data)
        return data.get("response", "").strip()
    except Exception as e:
        ic("Model error:", e)
        return "ERROR communicating with model."

def save_text_to_file(text, filename=None):
    if not filename:
        filename = f"text_{int(time.time())}.txt"
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    ic("Saved text to:", path)
    return path

# -------------------------------------------------------------------
# Main Page
# -------------------------------------------------------------------
@app.route("/enhance", methods=["GET", "POST"])
def enhance():
    original_text = ""
    enhanced_text = ""
    final_output = ""
    selected_style = "romantic"
    save_msg = ""

    if request.method == "POST":
        action = request.form.get("action")
        selected_style = request.form.get("style", "romantic")
        text_input = request.form.get("text_input", "").strip()

        if action == "enhance":
            original_text = text_input
            enhance_prompt = (
                f"Enhance the following text into a vivid, clear, polished description "
                f"in the style: {selected_style}. Do not change the meaning.\n\n{text_input}"
            )
            enhanced_text = call_model(ENHANCER_URL, ENHANCER_MODEL, enhance_prompt)

        elif action == "generate":
            enhanced_text = text_input
            generation_prompt = (
                f"Write a refined, coherent piece of text based on the following enhanced prompt "
                f"in the style: {selected_style}:\n\n{text_input}"
            )
            final_output = call_model(GENERATOR_URL, GENERATOR_MODEL, generation_prompt)

        elif action == "save":
            # Save whatever is currently in the textarea
            save_text_to_file(text_input)
            save_msg = "Text saved successfully!"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Prompt Enhancer & Generator</title>
        <style>
            body { background:#111; color:#eee; font-family:Arial; padding:30px; }
            textarea { width:100%; height:200px; padding:15px; border-radius:10px; border:none; background:#222; color:#eee; font-size:16px; }
            button { padding:12px 25px; margin-top:15px; margin-right:10px; border:none; background:#ff66aa; color:white; border-radius:8px; cursor:pointer; font-size:16px; }
            button:hover { background:#ff3388; }
            select { padding:10px 15px; font-size:16px; border-radius:8px; border:none; margin-right:10px; }
            .box { background:#222; padding:20px; border-radius:12px; margin-top:20px; }
            h2 { color:#ff66aa; }
            pre { white-space: pre-wrap; word-break: break-word; background:#222; padding:15px; border-radius:10px; }
            .msg { color:#66ff66; margin-top:10px; }
            a {font-size:3vw; color:yellow;}
        </style>
    </head>
    <body>

        <h1>Esperanza's Prompt Enhancer 💋</h1>
        <a href="/create_text">Create Mp3</a>&nbsp;&nbsp|;&nbsp;&nbsp;<a href="/view_text">View Text</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href ="/create_video" class="nav-link">Create Video</a>

        <form method="POST">
            <h2>Your Prompt</h2>
            <textarea name="text_input">{{ enhanced_text or original_text }}</textarea>

            <div>
                <label for="style">Select Style:</label>
                <select name="style" id="style">
                    {% for option in style_options %}
                        <option value="{{ option }}" {% if option == selected_style %}selected{% endif %}>{{ option }}</option>
                    {% endfor %}
                </select>
            </div>

            <div>
                <button type="submit" name="action" value="enhance">✨ Enhance</button>
                <button type="submit" name="action" value="generate">🔥 Generate</button>
                <button type="submit" name="action" value="save">💾 Save Text</button>
            </div>
        </form>

        {% if save_msg %}
            <div class="msg">{{ save_msg }}</div>
        {% endif %}

        {% if final_output %}
        <div class="box">
            <h2>Generated Text</h2>
            <pre>{{ final_output }}</pre>
        </div>
        {% endif %}

    </body>
    </html>
    """

    return render_template_string(
        html,
        original_text=original_text,
        enhanced_text=enhanced_text,
        final_output=final_output,
        style_options=STYLE_OPTIONS,
        selected_style=selected_style,
        save_msg=save_msg
    )

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

TTS_API_URL = "http://localhost:8880/v1/audio/speech"

VOICES = [
    'bf_alice', 'bf_emma', 'bf_lily', 'bf_v0emma', 'bf_v0isabella',
    'af_alloy', 'af_aoede', 'af_bella', 'af_heart', 'af_jadzia',
    'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river',
    'af_sarah', 'af_sky', 'af_v0', 'af_v0bella', 'af_v0irulan',
    'af_v0nicole', 'af_v0sarah', 'af_v0sky', 'am_adam', 'am_echo',
    'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx',
    'am_puck', 'am_santa', 'am_v0adam', 'am_v0gurney', 'am_v0michael',
    'bm_daniel', 'bm_fable'
]

DEFAULT_VOICE = "am_michael"
ic(f"Default voice: {DEFAULT_VOICE}")


# -----------------------------------------------------------
# Ensure output directory exists
# -----------------------------------------------------------

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    ic(f"Created directory: {OUTPUT_DIR}")

# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------

def sanitize_filename(text, max_length=20):
    base = text.strip()[:max_length]
    base = re.sub(r'\W+', '_', base)
    return base or "output"

def generate_tts(text, voice):
    filename = sanitize_filename(text) + ".mp3"
    output_path = os.path.join(OUTPUT_DIR, filename)

    payload = {
        "input": text,
        "voice": voice
    }

    ic(f"Sending TTS request ({voice}) for first 40 chars: {text[:40]}")

    try:
        r = requests.post(TTS_API_URL, json=payload, timeout=380)

        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)

            ic(f"Saved TTS: {output_path}")
            return filename

        ic(f"TTS error {r.status_code}: {r.text}")
        return None

    except Exception as e:
        ic(f"TTS request failed: {e}")
        return None

# -----------------------------------------------------------
# Web UI
# -----------------------------------------------------------

@app.route("/create_text", methods=["GET", "POST"])
def create_text():
    generated_file = None
    selected_voice = DEFAULT_VOICE

    if request.method == "POST":
        text_input = request.form.get("text_input", "").strip()
        selected_voice = request.form.get("voice", DEFAULT_VOICE)

        if text_input:
            result = generate_tts(text_input, selected_voice)
            if result:
                generated_file = result

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text → MP3 Generator</title>
        <style>
            body { background:#111; color:#eee; font-family:Arial; padding:30px; }
            textarea { width:100%; height:200px; padding:15px; background:#222; color:#fff;
                       border:none; border-radius:10px; font-size:16px; }
            button { margin-top:15px; padding:12px 25px; background:#ff66aa; border:none;
                     border-radius:8px; cursor:pointer; color:white; font-size:16px; }
            button:hover { background:#ff3388; }
            select { padding:10px 15px; margin-top:15px; background:#222; color:#fff;
                     border-radius:8px; font-size:16px; border:none; }
            .box { background:#222; padding:20px; border-radius:12px; margin-top:20px; }
            a {font-size:3vw; color:yellow;}
        </style>
    </head>

    <body>
        <h1>Esperanza's Text → MP3 Generator 💋</h1>
        <a href="/">Enhance Prompt</a>&nbsp;&nbsp | &nbsp;&nbsp;<a href="/view_text">View Text</a>&nbsp;&nbsp | &nbsp;&nbsp;<a href="/">HOME</a>
        <form method="POST">
            <textarea name="text_input" placeholder="Write something beautiful..."></textarea>

            <br><br>

            <label for="voice">Choose a voice:</label>
            <select name="voice">
                {% for v in voices %}
                    <option value="{{v}}" {% if v == selected %}selected{% endif %}>
                        {{v}}
                    </option>
                {% endfor %}
            </select>

            <br>
            <button type="submit">Generate MP3</button>
        </form>

        {% if generated_file %}
        <div class="box">
            <h2>Your MP3 is ready</h2>
            <a href="/">Enhance Prompt</a>;&nbsp;&nbsp;&nbsp;&nbsp|;&nbsp;&nbsp;<a href="/view_text">View Text</a>
            <a href="/download/{{generated_file}}">{{generated_file}}</a>
        </div>
        {% endif %}
    </body>
    </html>
    """

    return render_template_string(
        html,
        voices=VOICES,
        selected=selected_voice,
        generated_file=generated_file
    )

# -----------------------------------------------------------
# Download route
# -----------------------------------------------------------
'''
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)
'''

# -----------------------------------------------------------
# View Text
# -----------------------------------------------------------



# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------


# Ensure folder exists
if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)
    ic(f"Created directory: {PROJECT_DIR}")

# -----------------------------------------------------------
# ROUTE: List .txt files
# -----------------------------------------------------------

@app.route("/view_text")
def view_text():
    files = [f for f in os.listdir(PROJECT_DIR) if f.lower().endswith(".txt")]
    files.sort()

    ic(f"Found {len(files)} .txt files")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text File Viewer</title>
        <a href="/">HOME</a>&nbsp;&nbsp|;&nbsp;&nbsp;<a href="/view_text">View Text</a>
        <style>
            body { background:#111; color:#eee; font-family:Arial; padding:30px; }
            a { color:#66bbff; text-decoration:none; }
            a:hover { color:#99d0ff; }
            .box { background:#222; padding:20px; border-radius:12px; margin-top:20px; }
            .file-list { margin-bottom:20px; }
        </style>
    </head>
    <body>
        <h1>📄 Text Files in static/projects</h1>

        <div class="file-list">
            <h3>Available .txt files:</h3>
            <ul>
                {% for f in files %}
                    <li><a href="/view/{{f}}">{{f}}</a></li>
                {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """

    return render_template_string(html, files=files)


# -----------------------------------------------------------
# ROUTE: View file content
# -----------------------------------------------------------

@app.route("/view/<filename>")
def view_file(filename):
    safe_path = os.path.join(PROJECT_DIR, filename)

    if not os.path.isfile(safe_path):
        return "File not found", 404

    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        ic(f"Opened: {filename}, {len(content)} characters")
    except Exception as e:
        ic(f"Error reading {filename}: {e}")
        return "Error reading file", 500

    html_view = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{filename}}</title>
        <style>
            body { background:#111; color:#eee; font-family:Arial; padding:30px; }
            pre { background:#222; padding:20px; border-radius:12px;
                  white-space:pre-wrap; font-size:16px; }
            a {font-size:3vw; color:yellow;}
        </style>
    </head>
    <body>
        <h1>Viewing: {{filename}}</h1>
        <pre>{{content}}</pre>

        <br>
        <a href="/dream">⬅ Dream</a>
    </body>
    </html>
    """

    return render_template_string(html_view, filename=filename, content=content)

# -----------------------------------------------------------
# Run server
# -----------------------------------------------------------

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    ic("Starting Flask web app...")
    app.run(host="0.0.0.0", port=5000, debug=True)
