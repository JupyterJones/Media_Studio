import os
import subprocess
import threading
import json
from flask import Flask, render_template, render_template_string, url_for, abort, Blueprint
from flask_sqlalchemy import SQLAlchemy

gallery_bp = Blueprint("gallery", __name__)
db = SQLAlchemy()

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

SKIP_DIRS = set()            # folder names to ignore, e.g. {"masks", "temp"}
SKIP_NAME_CONTAINS = ("mask",)  # skip files whose name contains any of these
                                # (binary_mask.png, greyscale_mask.png, ...)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
static_folder = os.path.join(BASE_DIR, "static")

# --------------------------------------------------
# MODELS
# --------------------------------------------------
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False, unique=True)  # path relative to static/
    title = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(500), nullable=False, default="")

    @property
    def full_path(self):
        # Computed, not stored: survives moving the project folder.
        return os.path.join(static_folder, self.image)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video = db.Column(db.String(255), nullable=False, unique=True)  # path relative to static/
    title = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(500), nullable=False, default="")

    @property
    def full_path(self):
        return os.path.join(static_folder, self.video)


class Sound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audio = db.Column(db.String(255), nullable=False, unique=True)  # path relative to static/
    title = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(500), nullable=False, default="")  # folder name

    @property
    def full_path(self):
        return os.path.join(static_folder, self.audio)


# --------------------------------------------------
# FOLDER -> DB SYNC
# --------------------------------------------------
def sync_images():
    """Make the DB mirror static/ image files: add new files, remove missing rows."""
    db.create_all()
    on_disk = {}
    for root, dirs, files in os.walk(static_folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            stem, ext = os.path.splitext(name)
            if ext.lower() not in IMAGE_EXTS:
                continue
            if any(s in name.lower() for s in SKIP_NAME_CONTAINS):
                continue
            rel = os.path.relpath(os.path.join(root, name), static_folder)
            rel = rel.replace(os.sep, "/")
            on_disk[rel] = (stem, os.path.dirname(rel))

    known = {row.image: row for row in Image.query.all()}

    for rel, (stem, folder) in on_disk.items():
        if rel not in known:
            db.session.add(Image(image=rel, title=stem, caption=folder))

    for rel, row in known.items():
        if rel not in on_disk:
            db.session.delete(row)

    db.session.commit()


_VERIFIED_VIDEOS = set()
_CONVERSION_LOCK = threading.Lock()

def probe_video_web_compatibility(path):
    """Checks if a video is web-compatible H.264 yuv420p."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,pix_fmt",
        "-of", "json", path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            if streams:
                c = streams[0].get("codec_name")
                p = streams[0].get("pix_fmt")
                if c in ["h264", "avc1"] and p in ["yuv420p", "yuvj420p"]:
                    return True
                return False
    except Exception:
        pass
    return True

def convert_to_web_compatible_video(file_path):
    """Converts a video in-place to web-compatible H.264 yuv420p with faststart."""
    tmp_path = file_path + ".tmp_web.mp4"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", file_path,
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        tmp_path
    ]
    try:
        res = subprocess.run(cmd, timeout=120)
        if res.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            os.replace(tmp_path, file_path)
            print(f"[✓] Auto-transcoded to web-compatible H.264: {file_path}", flush=True)
            return True
        elif os.path.exists(tmp_path):
            os.remove(tmp_path)
    except Exception as e:
        print(f"[!] Transcode error on {file_path}: {e}", flush=True)
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return False

def ensure_web_compatible_videos():
    """Background task: scans for incompatible videos and auto-converts them without blocking requests."""
    if not _CONVERSION_LOCK.acquire(blocking=False):
        return  # already actively transcoding in background
    try:
        for root, dirs, files in os.walk(static_folder):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(files):
                stem, ext = os.path.splitext(name)
                if ext.lower() not in VIDEO_EXTS:
                    continue
                full_path = os.path.join(root, name)
                if full_path in _VERIFIED_VIDEOS or os.path.getsize(full_path) == 0:
                    continue
                if not probe_video_web_compatibility(full_path):
                    print(f"[*] Found incompatible video: {full_path}. Auto-converting for web...", flush=True)
                    if convert_to_web_compatible_video(full_path):
                        _VERIFIED_VIDEOS.add(full_path)
                else:
                    _VERIFIED_VIDEOS.add(full_path)
    finally:
        _CONVERSION_LOCK.release()


def sync_videos():
    """Make the DB mirror static/ video files, and trigger background web-compatibility ensure."""
    db.create_all()
    # Trigger background auto-transcoder so page load is never blocked
    threading.Thread(target=ensure_web_compatible_videos, daemon=True).start()

    on_disk = {}
    for root, dirs, files in os.walk(static_folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            stem, ext = os.path.splitext(name)
            if ext.lower() not in VIDEO_EXTS:
                continue
            if any(s in name.lower() for s in SKIP_NAME_CONTAINS):
                continue
            rel = os.path.relpath(os.path.join(root, name), static_folder)
            rel = rel.replace(os.sep, "/")
            on_disk[rel] = (stem, os.path.dirname(rel))

    known = {row.video: row for row in Video.query.all()}

    for rel, (stem, folder) in on_disk.items():
        if rel not in known:
            db.session.add(Video(video=rel, title=stem, caption=folder))

    for rel, row in known.items():
        if rel not in on_disk:
            db.session.delete(row)

    db.session.commit()


def sync_sounds():
    """Make the DB mirror static/ audio files: add new files, remove missing rows."""
    db.create_all()
    on_disk = {}
    for root, dirs, files in os.walk(static_folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            stem, ext = os.path.splitext(name)
            if ext.lower() not in AUDIO_EXTS:
                continue
            if any(s in name.lower() for s in SKIP_NAME_CONTAINS):
                continue
            rel = os.path.relpath(os.path.join(root, name), static_folder)
            rel = rel.replace(os.sep, "/")
            on_disk[rel] = (stem, os.path.dirname(rel))

    known = {row.audio: row for row in Sound.query.all()}

    for rel, (stem, folder) in on_disk.items():
        if rel not in known:
            db.session.add(Sound(audio=rel, title=stem, caption=folder))

    for rel, row in known.items():
        if rel not in on_disk:
            db.session.delete(row)

    db.session.commit()






# --------------------------------------------------
# TEMPLATES (move to templates/*.html + render_template() when it grows)
# --------------------------------------------------
GALLERY = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Gallery</title>
  <style>
    body { font-family: sans-serif; margin: 1rem 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }
    figure { margin: 0; }
    img { width: 100%; height: 220px; object-fit: cover; border-radius: 6px; }
    figcaption { font-size: .75rem; word-break: break-all; }
    code { cursor: pointer; color: #555; }
  </style>
</head>
<body>
  <h1>Gallery ({{ images|length }})</h1>
  <div class="grid">
    {% for img in images %}
      <figure>
        <a href="{{ url_for('gallery.show_image', id=img.id) }}">
          <img src="{{ url_for('static', filename=img.image) }}"
               alt="{{ img.title }}" loading="lazy">
        </a>
        <figcaption>
          <strong>{{ img.title }}</strong><br>
          <code title="Click to copy"
                onclick="navigator.clipboard.writeText('{{ img.full_path|e }}')">{{ img.full_path }}</code>
        </figcaption>
      </figure>
    {% endfor %}
  </div>
</body>
</html>
"""

DETAIL = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{ img.title }}</title>
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
    body { font-family: sans-serif; margin: 1rem 2rem; }
    .nav { display: flex; justify-content: space-between; margin: 1rem 0; }
    code { background: #eee; padding: 2px 5px; border-radius: 4px; }
  </style>
</head>
<body>
  <p><a href="{{ url_for('gallery.static_images') }}">&larr; Back to gallery</a></p>
  <h2>{{ img.title }}</h2>
  <img src="{{ url_for('static', filename=img.image) }}" style="max-width:100%;">
  <p><strong>File:</strong> <code>{{ img.full_path }}</code></p>
  <p><strong>URL:</strong> <code>{{ url_for('static', filename=img.image) }}</code></p>
  <div class="nav">
    <span>
      {% if prev_id %}
        <a href="{{ url_for('gallery.show_image', id=prev_id) }}"><i class="fas fa-angle-left"></i> Prev</a>
      {% endif %}
    </span>
    <span>
      {% if next_id %}
        <a href="{{ url_for('gallery.show_image', id=next_id) }}">Next <i class="fas fa-angle-right"></i></a>
      {% endif %}
    </span>
  </div>
</body>
</html>
"""


# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@gallery_bp.route("/static_images")
def static_images():
    sync_images()  # picks up new/removed files without a restart
    images = Image.query.order_by(Image.image).all()
    return render_template("static_gallery.html", images=images)


@gallery_bp.route("/static_images/<int:id>")
def show_image(id):
    img = db.get_or_404(Image, id)
    # Same ordering as the grid (by path), so Prev/Next matches what you see
    prev_img = (Image.query.filter(Image.image < img.image)
                .order_by(Image.image.desc()).first())
    next_img = (Image.query.filter(Image.image > img.image)
                .order_by(Image.image).first())
    return render_template(
        "static_image_detail.html",
        img=img,
        prev_id=prev_img.id if prev_img else None,
        next_id=next_img.id if next_img else None,
    )


# --------------------------------------------------
# ROUTES - VIDEOS
# --------------------------------------------------
@gallery_bp.route("/static_videos")
def static_videos():
    sync_videos()  # picks up new/removed video files without a restart
    videos = Video.query.order_by(Video.video).all()
    return render_template("static_videos.html", videos=videos)


@gallery_bp.route("/static_videos/<int:id>")
def show_video(id):
    vid = db.get_or_404(Video, id)
    # Same ordering as the video list (by path), so Prev/Next matches what you see
    prev_vid = (Video.query.filter(Video.video < vid.video)
                .order_by(Video.video.desc()).first())
    next_vid = (Video.query.filter(Video.video > vid.video)
                .order_by(Video.video).first())
    return render_template(
        "static_video_detail.html",
        vid=vid,
        prev_id=prev_vid.id if prev_vid else None,
        next_id=next_vid.id if next_vid else None,
    )


# --------------------------------------------------
# ROUTES - SOUNDS
# --------------------------------------------------
@gallery_bp.route("/static_sounds")
def static_sounds():
    sync_sounds()  # picks up new/removed audio files without a restart
    sounds = Sound.query.order_by(Sound.audio).all()
    return render_template("static_sounds.html", sounds=sounds)


@gallery_bp.route("/static_sounds/<int:id>")
def show_sound(id):
    snd = db.get_or_404(Sound, id)
    # Same ordering as the sound list (by path), so Prev/Next matches what you see
    prev_snd = (Sound.query.filter(Sound.audio < snd.audio)
                .order_by(Sound.audio.desc()).first())
    next_snd = (Sound.query.filter(Sound.audio > snd.audio)
                .order_by(Sound.audio).first())
    return render_template(
        "static_sound_detail.html",
        snd=snd,
        prev_id=prev_snd.id if prev_snd else None,
        next_id=next_snd.id if next_snd else None,
    )


if __name__ == "__main__":
    standalone_app = Flask(__name__)
    standalone_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gallery.db"
    db.init_app(standalone_app)
    standalone_app.register_blueprint(gallery_bp)
    with standalone_app.app_context():
        db.create_all()
        sync_images()
        sync_videos()
        sync_sounds()
    print("Static Images Gallery running at http://127.0.0.1:5400/static_images")
    print("Static Videos Gallery running at http://127.0.0.1:5400/static_videos")
    print("Static Sounds Gallery running at http://127.0.0.1:5400/static_sounds")
    standalone_app.run(debug=True, host="127.0.0.1", port=5400)

