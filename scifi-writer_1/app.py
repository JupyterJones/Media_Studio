#!/usr/bin/env python3
"""
SciFi Vision Studio: Flask Application
Interactive UI to write/generate Sci-Fi Storyboards and render cinematic videos.
"""

import os
import sys
import time
import json
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file

import scifi_engine

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = 'scifi-vision-studio-2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True

WORKSPACE_DIR = Path(__file__).resolve().parent
TEMPLATE_MD = WORKSPACE_DIR / "template.md"
OUTPUT_VIDEO = WORKSPACE_DIR / "science_1.mp4"

# Render job tracking
render_job = {
    "status": "idle",
    "progress": 0,
    "message": "Ready to render",
    "output_file": "science_1.mp4",
    "error": None
}
render_lock = threading.Lock()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/load-markdown', methods=['GET'])
def load_markdown():
    filename = request.args.get('file', 'template.md')
    file_path = WORKSPACE_DIR / filename
    if not file_path.exists():
        file_path = TEMPLATE_MD
    content = file_path.read_text(encoding='utf-8')
    return jsonify({"success": True, "filename": file_path.name, "content": content})


@app.route('/api/list-storyboards', methods=['GET'])
def list_storyboards():
    """Returns all available markdown storyboards in the workspace."""
    files = []
    for f in sorted(WORKSPACE_DIR.glob("*.md")):
        if f.name.lower() in ["readme.md"]:
            continue
        files.append({
            "filename": f.name,
            "title": f.name.replace(".md", "").replace("_", " ").title()
        })
    return jsonify({"success": True, "files": files})


@app.route('/api/save-markdown', methods=['POST'])
def save_markdown():
    data = request.get_json() or {}
    content = data.get('content', '')
    filename = data.get('filename', 'template.md')
    # clean filename
    if not filename.endswith('.md'):
        filename += '.md'
    filename = os.path.basename(filename)
    file_path = WORKSPACE_DIR / filename
    file_path.write_text(content, encoding='utf-8')
    return jsonify({"success": True, "filename": filename, "message": f"Saved {file_path.name}"})


@app.route('/api/create-storyboard', methods=['POST'])
def create_storyboard():
    data = request.get_json() or {}
    title = data.get('title', 'NEW MISSION').strip()
    slug = scifi_engine.get_story_slug(title)
    filename = f"{slug}.md"
    file_path = WORKSPACE_DIR / filename
    
    # Starter template content
    template_content = f"""# 🎬 SCI-FI STORYBOARD SPECIFICATION
<!-- PROJECT: {title} -->
<!-- TARGET: {slug}.mp4 -->

---

🎬 **COMIC STORYBOARD: "{title.upper()}"**

🎵 **Recommended BGM**: Shadows-Anno_Domini_Beats.mp3 | Volume: 0.22

---

### 🖼️ PANEL 1: [Inception Point]

* 🔲 **Layout**: Full Banner (16:9 Widescreen) | Height: 1 Row
* 🎥 **Camera Motion**: Slow Zoom-In Center
* 🎙️ **Voice**: af_nova (Research Scientist)
* ⚡ **Voice Speed**: 0.95
* 🗣️ **Spoken Text (TTS Clean)**:
  Log date: twenty-one ninety-two point zero four. We have arrived at the designated coordinates. All primary telemetry confirms the signal source.
* 💬 **On-Screen Dialogue (HUD Display)**:
  SYSTEM INITIALIZED // LOG 2192.04
  "We have arrived at the designated coordinates. All primary telemetry confirms the signal source."
* 🎨 **Stable Diffusion Image Prompt**:
  cinematic sci-fi photo of a futuristic expedition spacecraft arriving at an enigmatic alien planetary structure, deep cosmic backdrop, glowing nebula, 8k, photorealistic
* ⚙️ **LCM Settings**: Steps: 4 | CFG: 1.5

---

### 🖼️ PANEL 2: [The Deep Encounter]

* 🔲 **Layout**: Full Banner (16:9 Widescreen) | Height: 1 Row
* 🎥 **Camera Motion**: Pan-Left-To-Right
* 🎙️ **Voice**: am_michael (Veteran Commander)
* ⚡ **Voice Speed**: 0.95
* 🗣️ **Spoken Text (TTS Clean)**:
  Sensors detect biological and synthetic signatures intertwined. Proceed with caution. Seal all bulkheads.
* 💬 **On-Screen Dialogue (HUD Display)**:
  TACTICAL ALERT // LEVEL 4
  "Sensors detect biological and synthetic signatures intertwined. Proceed with caution."
* 🎨 **Stable Diffusion Image Prompt**:
  dramatic interior view of a futuristic starship bridge, tactical commanders analyzing glowing holographic planetary scans, high tension, cinematic sci-fi lighting, 8k
* ⚙️ **LCM Settings**: Steps: 4 | CFG: 1.5

---

### 🖼️ PANEL 3: [Resolution / The Horizon]

* 🔲 **Layout**: Full Banner (16:9 Widescreen) | Height: 1 Row
* 🎥 **Camera Motion**: Slow-Drift-Forward
* 🎙️ **Voice**: af_heart (Ship AI Core)
* ⚡ **Voice Speed**: 0.95
* 🗣️ **Spoken Text (TTS Clean)**:
  The threshold is open. Transmission relay initiated across all interstellar frequencies.
* 💬 **On-Screen Dialogue (HUD Display)**:
  TRANSMISSION RELAY // GLOBAL BROADCAST
  "The threshold is open. Transmission relay initiated across all interstellar frequencies."
* 🎨 **Stable Diffusion Image Prompt**:
  wide angle shot of an awe-inspiring crystalline planetary monument activating with glowing beams of pure light into space, starry sky, cinematic sci-fi masterpiece, 8k
* ⚙️ **LCM Settings**: Steps: 4 | CFG: 1.5
"""
    file_path.write_text(template_content, encoding='utf-8')
    return jsonify({"success": True, "filename": filename, "title": title, "content": template_content})


@app.route('/api/get-snapshots', methods=['GET'])
def get_snapshots():
    slug = request.args.get('slug', 'science_1')
    snap_dir = scifi_engine.ASSETS_DIR / f"{slug}_snapshots"
    if not snap_dir.exists() or not list(snap_dir.glob("*.jpg")):
        snap_dir = scifi_engine.ASSETS_DIR / "snapshots"
    
    snaps = []
    if snap_dir.exists():
        for f in sorted(snap_dir.glob("*.jpg")):
            snaps.append({
                "url": f"/assets/{snap_dir.name}/{f.name}?t={int(time.time())}",
                "caption": f.name.replace(".jpg", "").replace("_", " ").upper()
            })
    return jsonify({"success": True, "snapshots": snaps})


@app.route('/api/parse-storyboard', methods=['POST'])
def parse_storyboard():
    data = request.get_json() or {}
    content = data.get('content', '')
    project_slug = data.get('project_slug')
    if not content:
        if TEMPLATE_MD.exists():
            content = TEMPLATE_MD.read_text(encoding='utf-8')
    parsed = scifi_engine.parse_storyboard_markdown(content, project_slug=project_slug)
    # Check if images / audio exist for each panel
    for p in parsed['panels']:
        p['image_exists'] = os.path.exists(p['image_path'])
        p['audio_exists'] = os.path.exists(p['audio_path'])
    return jsonify({"success": True, "storyboard": parsed})


@app.route('/api/generate-storyboard', methods=['POST'])
def generate_storyboard():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    model = (data.get('model') or 'scifi-writer:1').strip()
    try:
        timeout = int(data.get('timeout', 1000))
    except (ValueError, TypeError):
        timeout = 1000
    if timeout < 1000:
        timeout = 1000

    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400
    try:
        storyboard_md = scifi_engine.generate_storyboard_with_ollama(prompt, model=model, timeout=timeout)
        return jsonify({"success": True, "content": storyboard_md})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/synthesize-audio', methods=['POST'])
def synthesize_audio():
    data = request.get_json() or {}
    panel = data.get('panel', {})
    speed = float(data.get('speed', 0.95))
    try:
        audio_path = scifi_engine.synthesize_panel_audio(panel, speed=speed)
        dur = scifi_engine.get_audio_duration(audio_path)
        rel_url = panel.get("audio_url") or f"/assets/{Path(audio_path).parent.name}/{Path(audio_path).name}"
        return jsonify({
            "success": True,
            "audio_path": f"{rel_url}?t={int(time.time())}",
            "duration": dur
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    panel_idx = int(data.get('panel_index', 1))
    steps = int(data.get('steps', 4))
    out_path = data.get('image_path')
    if not out_path:
        project_slug = data.get('project_slug', 'science_1')
        target_dir = scifi_engine.ASSETS_DIR / ("panels" if project_slug == "science_1" else f"{project_slug}_panels")
        target_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(target_dir / f"panel_{panel_idx}.jpg")

    if not prompt:
        return jsonify({"success": False, "error": "Image prompt required"}), 400
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        scifi_engine.generate_panel_image_lcm(prompt, out_path, steps=steps)
        p = Path(out_path)
        rel_url = f"/assets/{p.parent.name}/{p.name}?t={int(time.time())}"
        return jsonify({
            "success": True,
            "image_url": rel_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/generate-image-gemini', methods=['POST'])
def generate_image_gemini():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    panel_idx = int(data.get('panel_index', 1))
    out_path = data.get('image_path')
    if not out_path:
        project_slug = data.get('project_slug', 'science_1')
        target_dir = scifi_engine.ASSETS_DIR / ("panels" if project_slug == "science_1" else f"{project_slug}_panels")
        target_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(target_dir / f"panel_{panel_idx}.jpg")

    if not prompt:
        return jsonify({"success": False, "error": "Image prompt required"}), 400
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        scifi_engine.generate_panel_image_gemini(prompt, out_path)
        p = Path(out_path)
        rel_url = f"/assets/{p.parent.name}/{p.name}?t={int(time.time())}"
        return jsonify({
            "success": True,
            "image_url": rel_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    file = request.files['image']
    panel_idx = request.form.get('panel_index', '1')
    target_path = request.form.get('image_path')
    if not target_path:
        project_slug = request.form.get('project_slug', 'science_1')
        target_dir = scifi_engine.ASSETS_DIR / ("panels" if project_slug == "science_1" else f"{project_slug}_panels")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = str(target_dir / f"panel_{panel_idx}.jpg")

    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400
    Path(target_path).parent.mkdir(parents=True, exist_ok=True)
    file.save(target_path)
    p = Path(target_path)
    rel_url = f"/assets/{p.parent.name}/{p.name}?t={int(time.time())}"
    return jsonify({
        "success": True,
        "image_url": rel_url
    })


@app.route('/api/bgm-list', methods=['GET'])
def list_bgm():
    tracks = scifi_engine.get_available_bgm()
    return jsonify({"success": True, "tracks": tracks})


@app.route('/api/render-video', methods=['POST'])
def start_render_video():
    global render_job
    with render_lock:
        if render_job["status"] == "rendering":
            return jsonify({"success": False, "error": "A render job is already in progress"}), 400

    data = request.get_json() or {}
    storyboard = data.get('storyboard')
    output_name = data.get('output_filename', 'science_1.mp4')
    bgm_name = data.get('bgm_track', '')
    bgm_volume = float(data.get('bgm_volume', 0.22))

    if not storyboard:
        # Fallback to current template.md
        content = TEMPLATE_MD.read_text(encoding='utf-8')
        storyboard = scifi_engine.parse_storyboard_markdown(content)

    # STRICT ZERO-OVERWRITE GUARANTEE:
    # Resolve to guaranteed unique filename so previous videos are never overwritten
    unique_out_path = scifi_engine.get_unique_video_path(output_name)
    output_name = unique_out_path.name

    bgm_path = None
    if bgm_name:
        candidate = scifi_engine.BGM_DIR / bgm_name
        if candidate.exists():
            bgm_path = str(candidate)

    def run_render():
        global render_job
        try:
            with render_lock:
                render_job["status"] = "rendering"
                render_job["progress"] = 5
                render_job["message"] = f"Initializing render pipeline for {output_name}..."
                render_job["error"] = None
                render_job["output_file"] = output_name

            def progress_cb(pct, msg):
                with render_lock:
                    render_job["progress"] = pct
                    render_job["message"] = msg

            out_file = scifi_engine.compile_full_video(
                storyboard,
                output_mp4=output_name,
                bgm_path=bgm_path,
                bgm_volume=bgm_volume,
                progress_cb=progress_cb
            )

            with render_lock:
                render_job["status"] = "completed"
                render_job["progress"] = 100
                render_job["message"] = f"Render complete: {os.path.basename(out_file)}"
        except Exception as e:
            with render_lock:
                render_job["status"] = "error"
                render_job["message"] = f"Render failed: {str(e)}"
                render_job["error"] = str(e)

    thread = threading.Thread(target=run_render, daemon=True)
    thread.start()

    return jsonify({"success": True, "message": "Render job started"})


@app.route('/api/render-status', methods=['GET'])
def get_render_status():
    with render_lock:
        return jsonify({
            "status": render_job["status"],
            "progress": render_job["progress"],
            "message": render_job["message"],
            "output_file": render_job["output_file"],
            "error": render_job["error"]
        })


@app.route('/assets/<path:subpath>')
def serve_assets(subpath):
    return send_from_directory(str(scifi_engine.ASSETS_DIR), subpath)


@app.route('/bgm/<path:filename>')
def serve_bgm(filename):
    return send_from_directory(str(scifi_engine.BGM_DIR), filename)


@app.route('/video/<path:filename>')
def serve_video(filename):
    file_path = WORKSPACE_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "Video file not found"}), 404
    return send_file(str(file_path), mimetype='video/mp4')


@app.route('/resources/<path:filename>')
def serve_resource(filename):
    return send_from_directory(str(scifi_engine.RESOURCES_DIR), filename)


@app.route('/api/resources', methods=['GET'])
def list_resources():
    resources = scifi_engine.get_available_resources()
    return jsonify({"success": True, "resources": resources})


@app.route('/api/assign-resource', methods=['POST'])
def assign_resource_to_panel():
    data = request.get_json() or {}
    filename = data.get('filename')
    panel_idx = int(data.get('panel_index', 1))
    project_slug = data.get('project_slug', 'science_1')
    target_path = data.get('target_path')

    if not filename:
        return jsonify({"success": False, "error": "No resource filename provided"}), 400

    src_file = scifi_engine.RESOURCES_DIR / filename
    if not src_file.exists():
        return jsonify({"success": False, "error": f"Resource not found: {filename}"}), 404

    if not target_path:
        target_dir = scifi_engine.ASSETS_DIR / ("panels" if project_slug == "science_1" else f"{project_slug}_panels")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"panel_{panel_idx}.jpg"
    else:
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy(str(src_file), str(target_path))
    rel_url = f"/assets/{target_path.parent.name}/{target_path.name}?t={int(time.time())}"
    return jsonify({
        "success": True,
        "image_url": rel_url,
        "image_path": str(target_path),
        "filename": filename
    })


# ==========================================
# VISUAL EFFECTS STUDIO ROUTES (SELF-CONTAINED)
# ==========================================

EXPORTS_DIR = WORKSPACE_DIR / "exports"
UPLOADS_DIR = WORKSPACE_DIR / "uploads"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/effects')
def visual_effects_studio():
    """Serves the integrated Visual Effects Studio."""
    return render_template('effects.html')


_video_duration_cache = {}

@app.route('/api/effects/videos', methods=['GET'])
def list_studio_videos():
    """Lists all master MP4 videos available in scifi-writer_1 for 1-click FX loading."""
    videos = []
    for ext in ["*.mp4", "*.webm"]:
        for f in WORKSPACE_DIR.glob(ext):
            try:
                mtime = f.stat().st_mtime
                cache_key = (str(f), mtime)
                if cache_key in _video_duration_cache:
                    dur = _video_duration_cache[cache_key]
                else:
                    dur = scifi_engine.get_audio_duration(str(f))
                    _video_duration_cache[cache_key] = dur
            except Exception:
                dur = 0.0
            videos.append({
                "filename": f.name,
                "url": f"/video/{f.name}",
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "duration_sec": round(dur, 2)
            })
    return jsonify({"success": True, "videos": sorted(videos, key=lambda x: x["filename"])})


@app.route('/api/effects/panels', methods=['GET'])
def list_studio_panels():
    """Lists all storyboard panels across panels, panels_v3, and staacor_panels."""
    panel_list = []
    for sub in ["panels", "panels_v3", "staacor_panels"]:
        pdir = WORKSPACE_DIR / "assets" / sub
        if pdir.exists():
            for img in sorted(pdir.glob("*.jpg")):
                panel_list.append({
                    "category": sub,
                    "filename": f"{sub}/{img.name}",
                    "url": f"/assets/{sub}/{img.name}"
                })
    return jsonify({"success": True, "panels": panel_list})


@app.route('/api/effects/save-export', methods=['POST'])
@app.route('/api/save-export', methods=['POST'])
def save_effects_export():
    """Saves canvas recordings or snapshots directly into exports/."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    filename = file.filename or f"export_{int(time.time())}.webm"
    filename = os.path.basename(filename)
    dest_path = EXPORTS_DIR / filename
    file.save(dest_path)
    return jsonify({
        'success': True,
        'filename': filename,
        'size': dest_path.stat().st_size,
        'url': f"/exports/{filename}"
    })


@app.route('/exports/<path:filename>')
def serve_effects_export(filename):
    return send_from_directory(str(EXPORTS_DIR), filename)


@app.route('/upload', methods=['POST'])
def upload_effects_media():
    """Uploads media for visual effects processing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = f"{int(time.time())}_{os.path.basename(file.filename)}"
    dest = UPLOADS_DIR / filename
    file.save(dest)
    return jsonify({
        'success': True,
        'filename': filename,
        'url': f"/uploads/{filename}"
    })


@app.route('/uploads/<path:filename>')
def serve_effects_uploads(filename):
    return send_from_directory(str(UPLOADS_DIR), filename)


@app.route('/api/presets', methods=['GET', 'POST'])
def handle_effects_presets():
    preset_file = WORKSPACE_DIR / "static" / "effects" / "presets" / "default-presets.json"
    if request.method == 'GET':
        if preset_file.exists():
            with open(preset_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({'presets': []})
    return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5055))
    print(f"🚀 SciFi Vision Studio starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
