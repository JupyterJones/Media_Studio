#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
REMEMBER – Flask Knowledge & Media Database
-------------------------------------------

Architecture:
- remember.py → application logic, routing, persistence
- ui_html.py  → ALL HTML & CSS stored as Python strings
- SQLite DB   → searchable long-term memory
"""

# ==========================================================
# Standard Library
# ==========================================================
import os
import io
import html
import base64
import sqlite3
import datetime
import inspect
import importlib
import glob
import random

# ==========================================================
# Third-Party
# ==========================================================
from icecream import ic
from markupsafe import Markup
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ==========================================================
# Flask
# ==========================================================
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template_string,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

# ==========================================================
# Local UI Module
# ==========================================================
import ui_html

# ==========================================================
# Flask App Setup
# ==========================================================
app = Flask(__name__)
app.secret_key = "your_super_secret_key_here"

# ==========================================================
# Database & File System Configuration
# ==========================================================
DATABASE = "static/REMEMBER.db"
LOG_FILE_PATH = "static/REMEMBER_log.txt"
TEXT_FILES_DIR = "static/TEXT"
VUPLOAD_FOLDER = "static/videos"
AUPLOAD_FOLDER = "static/audio"
PLAY_FOLDER = "static/play"

app.config["VUPLOAD_FOLDER"] = VUPLOAD_FOLDER
app.config["AUPLOAD_FOLDER"] = AUPLOAD_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {
    "txt", "md", "py", "json", "pdf",
    "png", "jpg", "jpeg", "gif", "webp",
    "mp4", "mkv", "avi", "mp3", "mpeg"
}
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB max upload

# Ensure essential directories exist
os.makedirs("static", exist_ok=True)
os.makedirs(TEXT_FILES_DIR, exist_ok=True)
os.makedirs(VUPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLAY_FOLDER, exist_ok=True)

if not os.path.exists(LOG_FILE_PATH):
    open(LOG_FILE_PATH, "w", encoding="utf-8").close()


# ==========================================================
# Utility: File Logger
# ==========================================================
def logit(*args):
    """
    Lightweight file-based logger.
    Writes timestamped messages with file and line number.
    """
    try:
        timestr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        frame = inspect.stack()[1]
        location = f"{frame.filename}:{frame.lineno}"
        message = " ".join(map(str, args))

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{timestr} [{location}] {message}\n")
    except Exception as e:
        print("[LOG ERROR]", e)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


# ==========================================================
# Favicon Generator
# ==========================================================
@app.route("/favicon.ico")
def favicon():
    size = (32, 32)
    favicon_img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(favicon_img)

    # Draw rounded gradient/circle background
    draw.ellipse([(0, 0), size], fill=(99, 102, 241))

    # Load a TTF font if available
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

    try:
        font = ImageFont.truetype(font_path, 20)
    except Exception:
        font = ImageFont.load_default()

    text = "R"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_pos = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(text_pos, text, font=font, fill=(255, 255, 255))

    buf = BytesIO()
    favicon_img.save(buf, format="ICO")
    buf.seek(0)
    return Response(buf.getvalue(), content_type="image/x-icon")


# ==========================================================
# Database Helpers
# ==========================================================
def init_db():
    """Create DB tables if missing."""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS post (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                video_filename TEXT,
                image BLOB,
                audio TEXT
            )
        """)


def get_posts(limit=None):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        if limit:
            cur.execute(
                "SELECT id, title, content, image, video_filename, audio FROM post ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        else:
            cur.execute(
                "SELECT id, title, content, image, video_filename, audio FROM post ORDER BY id DESC"
            )
        return cur.fetchall()


def get_post(post_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, content, image, video_filename, audio FROM post WHERE id = ?",
            (post_id,),
        )
        return cur.fetchone()


def get_image(post_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM post WHERE id = ?", (post_id,))
        post = cursor.fetchone()
        if post and post[0]:
            return post[0]
        return None


def update_video_filename(post_id, filename):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE post SET video_filename = ? WHERE id = ?", (filename, post_id)
        )
        conn.commit()


def update_audio_filename(post_id, filename):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE post SET audio = ? WHERE id = ?", (filename, post_id)
        )
        conn.commit()


def update_image_data(post_id, image_data):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE post SET image = ? WHERE id = ?", (image_data, post_id)
        )
        conn.commit()


# ==========================================================
# UI / CSS Serving
# ==========================================================
@app.route("/_ui_css/<name>.css")
def ui_css(name):
    """Serves global CSS stored in ui_html.CSS."""
    return Response(ui_html.CSS, mimetype="text/css")


# ==========================================================
# UI HTML Live Editor
# ==========================================================
UI_HTML_PATH = "ui_html.py"

EDITABLE_VARS = [
    "CSS", "BASE1", "HOME", "NEW_POST", "CREATE_TEXT",
    "EDIT_TEXT", "EDIT", "CONTENTS", "VIEW_LOG",
    "SEARCH", "EDIT_POST", "READ_LOG", "POST"
]


@app.route("/edit_ui_html", methods=["GET", "POST"])
def edit_ui_html():
    selected_var = request.args.get("var", "CSS")
    if selected_var not in EDITABLE_VARS:
        selected_var = "CSS"

    if request.method == "POST":
        new_code = request.form.get("code", "")
        var_name = request.form.get("var_name", "")

        if new_code and var_name in EDITABLE_VARS:
            with open(UI_HTML_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

            start_idx = None
            end_idx = None
            quote_char = None

            # Locate variable definition
            for i, line in enumerate(lines):
                if line.startswith(f"{var_name}=") or line.startswith(f"{var_name} ="):
                    start_idx = i
                    stripped = line.strip()
                    if stripped.endswith("'''"):
                        quote_char = "'''"
                    elif stripped.endswith('"""'):
                        quote_char = '"""'
                    else:
                        quote_char = "'''"
                    break

            if start_idx is not None:
                end_idx = start_idx + 1
                while end_idx < len(lines):
                    if lines[end_idx].strip().endswith(quote_char):
                        break
                    end_idx += 1

                new_lines = [f"{var_name} = {quote_char}\n"]
                new_lines.extend(new_code.splitlines(keepends=True))
                if not new_code.endswith("\n"):
                    new_lines.append("\n")
                new_lines.append(f"{quote_char}\n")

                lines[start_idx:end_idx + 1] = new_lines

                with open(UI_HTML_PATH, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                importlib.reload(ui_html)
                logit(f"Updated UI template: {var_name}")
                flash(f"Template '{var_name}' updated and reloaded!", "success")

                return redirect(url_for("edit_ui_html", var=var_name))

    # Load current variable
    code = getattr(ui_html, selected_var, "")
    escaped_code = html.escape(code)

    # Build modern tab buttons
    tabs_html = "".join(
        f'<a href="{url_for("edit_ui_html", var=v)}" class="nav-link {"active" if v == selected_var else ""}">{v}</a>'
        for v in EDITABLE_VARS
    )

    # Preview logic
    if selected_var == "CSS":
        preview_html = """<!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="/_ui_css/dark.css">
        </head>
        <body style="padding: 24px;">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">🎨 Global CSS Live Preview</h2>
                    <span class="badge badge-primary">Active Stylesheet</span>
                </div>
                <p>This is a live preview showing typography, buttons, inputs, and dark theme elements.</p>
                <div class="d-flex gap-2 mb-3">
                    <button class="btn btn-primary">Primary Button</button>
                    <button class="btn btn-secondary">Secondary Button</button>
                    <button class="btn btn-success">Success</button>
                    <button class="btn btn-danger">Danger</button>
                </div>
                <div class="form-group">
                    <label class="form-label">Form Input Example</label>
                    <input type="text" class="form-control" value="Sample text preview">
                </div>
                <pre>pre { background: #070a12; color: #38bdf8; }</pre>
            </div>
        </body>
        </html>
        """
    else:
        preview_html = code

    safe_srcdoc = preview_html.replace('"', "&quot;")

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>REMEMBER - UI Code Editor</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <style>
        body {{ margin:0; padding:0; height:100vh; overflow:hidden; background: var(--bg-main); }}
        .editor-topbar {{
            background: var(--bg-glass);
            border-bottom: 1px solid var(--border-subtle);
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }}
        .editor-container {{ display: flex; height: calc(100vh - 120px); }}
        .editor-pane {{ width: 50%; height: 100%; border-right: 1px solid var(--border-subtle); display: flex; flex-direction: column; }}
        .preview-pane {{ width: 50%; height: 100%; }}
        textarea.ide-textarea {{
            width: 100%;
            height: 100%;
            background: #060911;
            color: #38bdf8;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 13.5px;
            line-height: 1.55;
            padding: 16px;
            border: none;
            outline: none;
            resize: none;
            box-sizing: border-box;
            tab-size: 4;
        }}
        iframe.preview-frame {{ width: 100%; height: 100%; border: none; background: #0b0f19; }}
        .tab-bar {{ display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 20px; background: #090d16; border-bottom: 1px solid var(--border-subtle); overflow-x: auto; }}
    </style>
</head>
<body>

<header class="sticky-header">
    <a href="{url_for('index')}" class="brand-wrapper">
        <div class="brand-icon">💾</div>
        <span class="brand-title">REMEMBER - UI Editor</span>
    </a>
    <div class="d-flex gap-2 align-center">
        <span class="badge badge-info">Editing: {selected_var}</span>
        <form method="POST" style="display:inline;">
            <input type="hidden" name="var_name" value="{selected_var}">
            <input type="hidden" name="code" id="hidden_code">
            <button class="btn btn-primary btn-sm" type="submit">💾 Save & Reload UI</button>
        </form>
        <a href="{url_for('index')}" class="btn btn-secondary btn-sm">🏠 App Home</a>
    </div>
</header>

<div class="tab-bar">
    {tabs_html}
</div>

<div class="editor-container">
    <div class="editor-pane">
        <div style="background: #090d16; padding: 6px 16px; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.8rem; color: var(--text-muted); font-family: monospace;">ui_html.py &gt; {selected_var}</span>
            <div class="d-flex gap-2">
                <input type="text" id="search_input" placeholder="Search code..." style="font-size: 0.8rem; padding: 2px 8px; width: 140px; background: #0f172a; color: #fff; border: 1px solid #334155; border-radius: 4px;">
                <button type="button" onclick="findNext()" class="btn btn-secondary btn-sm" style="padding: 2px 8px; font-size: 0.75rem;">Find Next</button>
            </div>
        </div>
        <textarea id="editor" class="ide-textarea">{escaped_code}</textarea>
    </div>
    <div class="preview-pane">
        <iframe class="preview-frame" srcdoc="{safe_srcdoc}"></iframe>
    </div>
</div>

<script>
const editor = document.getElementById("editor");
const hidden = document.getElementById("hidden_code");
hidden.value = editor.value;

editor.addEventListener("input", () => {{
    hidden.value = editor.value;
}});

// Tab key handling
editor.addEventListener("keydown", function(e) {{
    if (e.key === "Tab") {{
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
        hidden.value = this.value;
    }}
}});

let lastIndex = 0;
function findNext() {{
    const searchInput = document.getElementById("search_input");
    const term = searchInput.value;
    if (!term) return;

    const content = editor.value;
    const index = content.indexOf(term, lastIndex);

    if (index >= 0) {{
        editor.focus();
        editor.setSelectionRange(index, index + term.length);
        editor.scrollTop = editor.scrollHeight * (index / content.length);
        lastIndex = index + term.length;
    }} else {{
        lastIndex = 0;
        if (content.indexOf(term) >= 0) findNext();
    }}
}}
</script>

</body>
</html>
"""


# ==========================================================
# Core Routes - Home & Media
# ==========================================================
@app.route("/")
def index():
    posts = get_posts(limit=12)
    return render_template_string(ui_html.HOME, posts=posts)


def get_mp3():
    return glob.glob("static/play/*.mp3")


@app.route("/tube")
def tube():
    mp3s = get_mp3()
    return render_template_string(ui_html.BASE1, mp3s=mp3s)


# ==========================================================
# Search Route
# ==========================================================
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_terms = request.form.get("search_terms", "")
        ic(f"search_terms: {search_terms}")

        terms = [t.strip() for t in search_terms.split(",") if t.strip()]
        if not terms:
            return render_template_string(ui_html.SEARCH, results=[])

        where_conditions = ["(title LIKE ? OR content LIKE ?)" for _ in terms]
        where_clause = " OR ".join(where_conditions)

        search_params = []
        for term in terms:
            wildcard = f"%{term}%"
            search_params.extend([wildcard, wildcard])

        query = f"""
            SELECT id, title, content, image, video_filename, audio 
            FROM post 
            WHERE {where_clause} 
            ORDER BY id DESC
        """

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query, search_params).fetchall()

        return render_template_string(ui_html.SEARCH, results=rows)

    return render_template_string(ui_html.SEARCH, results=[])


# ==========================================================
# Database Post Management Routes
# ==========================================================
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    if request.method == "POST":
        if "videoFile" in request.files and request.files["videoFile"].filename != "":
            file = request.files["videoFile"]
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["VUPLOAD_FOLDER"], filename))
                update_video_filename(post_id, filename)
                flash(f"Video '{filename}' uploaded successfully!", "success")
            else:
                flash("Invalid video format.", "danger")

        if "audio" in request.files and request.files["audio"].filename != "":
            file = request.files["audio"]
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["AUPLOAD_FOLDER"], filename))
                update_audio_filename(post_id, filename)
                flash(f"Audio '{filename}' uploaded successfully!", "success")
            else:
                flash("Invalid audio format.", "danger")

        return redirect(url_for("show_post", post_id=post_id))

    post = get_post(post_id)
    if not post:
        flash("Post not found", "warning")
        return redirect(url_for("index"))

    return render_template_string(ui_html.POST, post=post)


@app.route("/post_view/<int:post_id>")
def post(post_id):
    """Alias for show_post."""
    return redirect(url_for("show_post", post_id=post_id))


@app.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        # Handle Image
        image = None
        if "image" in request.files and request.files["image"].filename != "":
            image_bytes = request.files["image"].read()
            if image_bytes:
                image = base64.b64encode(image_bytes).decode("utf-8")

        # Handle Video
        video_filename = None
        if "video" in request.files and request.files["video"].filename != "":
            vfile = request.files["video"]
            if allowed_file(vfile.filename):
                vname = secure_filename(vfile.filename)
                vfile.save(os.path.join(app.config["VUPLOAD_FOLDER"], vname))
                video_filename = vname

        # Handle Audio
        audio_filename = None
        if "audio" in request.files and request.files["audio"].filename != "":
            afile = request.files["audio"]
            if allowed_file(afile.filename):
                aname = secure_filename(afile.filename)
                afile.save(os.path.join(app.config["AUPLOAD_FOLDER"], aname))
                audio_filename = aname

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO post (title, content, image, video_filename, audio) VALUES (?, ?, ?, ?, ?)",
                (title, content, image, video_filename, audio_filename),
            )
            conn.commit()

        logit(f"Created new post: {title}")
        flash("Post created successfully!", "success")
        return redirect(url_for("index"))

    return render_template_string(ui_html.NEW_POST)


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = get_post(post_id)
    if not post:
        flash("Post not found.", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        image_data = post[3]
        video_filename = post[4]
        audio_filename = post[5]

        if "image" in request.files and request.files["image"].filename != "":
            img_bytes = request.files["image"].read()
            if img_bytes:
                image_data = base64.b64encode(img_bytes).decode("utf-8")

        if "video" in request.files and request.files["video"].filename != "":
            vfile = request.files["video"]
            if allowed_file(vfile.filename):
                video_filename = secure_filename(vfile.filename)
                vfile.save(os.path.join(app.config["VUPLOAD_FOLDER"], video_filename))

        if "audio" in request.files and request.files["audio"].filename != "":
            afile = request.files["audio"]
            if allowed_file(afile.filename):
                audio_filename = secure_filename(afile.filename)
                afile.save(os.path.join(app.config["AUPLOAD_FOLDER"], audio_filename))

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE post SET title = ?, content = ?, image = ?, video_filename = ?, audio = ? WHERE id = ?",
                (title, content, image_data, video_filename, audio_filename, post_id),
            )
            conn.commit()

        logit(f"Updated post #{post_id}: {title}")
        flash("Post updated successfully!", "success")
        return redirect(url_for("show_post", post_id=post_id))

    return render_template_string(ui_html.EDIT_POST, post=post)


@app.route("/contents")
def contents():
    posts = get_posts()
    contents_data = []
    for p in posts:
        excerpt = p[2][:300] + "..." if len(p[2]) > 300 else p[2]
        contents_data.append({"id": p[0], "title": p[1], "excerpt": excerpt})
    return render_template_string(ui_html.CONTENTS, contents_data=contents_data)


# ==========================================================
# Text Files & Text Creator Helpers & Routes
# ==========================================================
def get_text_file_info(filename):
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    if not os.path.exists(filepath):
        return None
    stat = os.stat(filepath)
    size_bytes = stat.st_size
    if size_bytes < 1024:
        size_str = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    preview = ""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            preview = f.read(140).strip()
    except Exception:
        preview = ""

    return {
        "filename": filename,
        "size": size_str,
        "mtime": mtime,
        "preview": preview,
    }


def read_text_from_file(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as file:
            return file.read()
    return ""


def save_text_to_file(filename, text):
    """
    Safely writes text to static/TEXT directory.
    Sanitizes filename and ensures an extension exists.
    """
    filename = secure_filename(filename).strip()
    if not filename:
        filename = f"note_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    if "." not in filename:
        filename += ".txt"

    filepath = os.path.join(TEXT_FILES_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(text)
    return filename


# Dedicated Text Creator Route
@app.route("/create_text", methods=["GET", "POST"])
def create_text():
    if request.method == "POST":
        filename = request.form.get("filename", "").strip()
        text = request.form.get("text", "")

        saved_filename = save_text_to_file(filename, text)
        logit(f"Created text file: {saved_filename}")
        flash(f"Text file '{saved_filename}' created successfully!", "success")
        return redirect(url_for("edit", filename=saved_filename))

    return render_template_string(ui_html.CREATE_TEXT)


# Text Files Manager / Directory
@app.route("/edit_text", methods=["GET", "POST"])
def edit_text():
    if request.method == "POST":
        filename = request.form.get("filename", "").strip()
        text = request.form.get("text", "")
        saved_filename = save_text_to_file(filename, text)
        logit(f"Created text file: {saved_filename}")
        flash(f"Text file '{saved_filename}' created successfully!", "success")
        return redirect(url_for("edit", filename=saved_filename))

    text_files = [
        f for f in os.listdir(TEXT_FILES_DIR)
        if os.path.isfile(os.path.join(TEXT_FILES_DIR, f))
    ]
    text_files.sort(
        key=lambda x: os.path.getmtime(os.path.join(TEXT_FILES_DIR, x)),
        reverse=True
    )
    files_info = [get_text_file_info(f) for f in text_files if get_text_file_info(f)]
    return render_template_string(ui_html.EDIT_TEXT, files=files_info)


# Text File Editor
@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    if not os.path.exists(filepath):
        flash(f"File '{filename}' does not exist.", "danger")
        return redirect(url_for("edit_text"))

    if request.method == "POST":
        text = request.form.get("text", "")
        save_text_to_file(filename, text)
        logit(f"Updated text file: {filename}")
        flash(f"File '{filename}' saved successfully!", "success")
        return redirect(url_for("edit", filename=filename))

    text = read_text_from_file(filename)
    file_info = get_text_file_info(filename)
    return render_template_string(
        ui_html.EDIT, filename=filename, text=text, file_info=file_info
    )


# Delete Text File
@app.route("/delete/<filename>")
def delete(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        logit(f"Deleted text file: {filename}")
        flash(f"File '{filename}' was deleted.", "info")
    else:
        flash(f"File '{filename}' not found.", "warning")
    return redirect(url_for("edit_text"))


# Download Text File
@app.route("/download/<filename>")
def download_text(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return Response(
            content,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    flash(f"File '{filename}' not found.", "warning")
    return redirect(url_for("edit_text"))


# ==========================================================
# Logs Management
# ==========================================================
@app.route("/view_log")
def view_log():
    data = []
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
            data = f.read().splitlines()
    return render_template_string(ui_html.VIEW_LOG, data=data)


@app.route("/readlog")
def readlog():
    logdatas = []
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
            logdatas = f.read().splitlines()
    return render_template_string(ui_html.READ_LOG, log_content=logdatas)


@app.route("/delete_log")
def delete_log():
    open(LOG_FILE_PATH, "w", encoding="utf-8").close()
    flash("Log file cleared successfully.", "info")
    return redirect(url_for("view_log"))


# ==========================================================
# Media Upload Direct Endpoints
# ==========================================================
@app.route("/upload_video/<int:post_id>", methods=["POST"])
def upload_video(post_id):
    if "videoFile" not in request.files:
        flash("No video file selected.", "warning")
        return redirect(url_for("show_post", post_id=post_id))

    file = request.files["videoFile"]
    if file.filename == "":
        flash("No selected video file.", "warning")
        return redirect(url_for("show_post", post_id=post_id))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["VUPLOAD_FOLDER"], filename))
        update_video_filename(post_id, filename)
        logit(f"Uploaded video '{filename}' to post #{post_id}")
        flash("Video uploaded successfully!", "success")
    else:
        flash("Allowed video file types: .mp4, .mkv, .avi", "danger")

    return redirect(url_for("show_post", post_id=post_id))


@app.route("/upload_audio/<int:post_id>", methods=["POST"])
def upload_audio(post_id):
    if "audio" not in request.files:
        flash("No audio file selected.", "warning")
        return redirect(url_for("show_post", post_id=post_id))

    file = request.files["audio"]
    if file.filename == "":
        flash("No selected audio file.", "warning")
        return redirect(url_for("show_post", post_id=post_id))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["AUPLOAD_FOLDER"], filename))
        update_audio_filename(post_id, filename)
        logit(f"Uploaded audio '{filename}' to post #{post_id}")
        flash("Audio uploaded successfully!", "success")
    else:
        flash("Allowed audio types: .mp3, .mpeg", "danger")

    return redirect(url_for("show_post", post_id=post_id))


@app.route("/upload_image/<int:post_id>", methods=["POST"])
def upload_image(post_id):
    if "imageFile" not in request.files:
        flash("No image file selected.", "warning")
        return redirect(url_for("show_post", post_id=post_id))

    file = request.files["imageFile"]
    if file.filename == "":
        flash("No selected image file.", "warning")
        return redirect(url_for("show_post", post_id=post_id))

    if file and allowed_file(file.filename):
        image_bytes = file.read()
        if image_bytes:
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            update_image_data(post_id, image_b64)
            logit(f"Uploaded image '{file.filename}' to post #{post_id}")
            flash(f"Image '{file.filename}' attached successfully!", "success")
    else:
        flash("Allowed image types: .png, .jpg, .jpeg, .webp, .gif", "danger")

    return redirect(url_for("show_post", post_id=post_id))


# ==========================================================
# App Entry
# ==========================================================
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5101)
