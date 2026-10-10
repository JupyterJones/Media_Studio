import argparse
from datetime import datetime
import json
import math
import os
from random import randint
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
import zipfile
import inspect
import cv2
from diffusers import DPMSolverMultistepScheduler, LCMScheduler, StableDiffusionPipeline
from flask import (
    Flask, Response, flash, jsonify, redirect, render_template,
    render_template_string, request, send_file, send_from_directory, url_for
)
from icecream import ic
from moviepy.editor import (
    AudioFileClip, ColorClip, CompositeVideoClip, ImageClip,
    VideoFileClip, concatenate_videoclips
)
import numpy as np
from PIL import Image
from pydub import AudioSegment
import requests
import torch
from werkzeug.utils import secure_filename

# --------------------------------------------------
# APP INITIALIZATION & PATH CONFIGURATION
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'zoompan_studio_secret_key_889977_secure_token')
app.config['JUNK_FOLDER'] = os.path.join(app.root_path, 'static', 'junk')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['EXPORT_FOLDER'] = os.path.join(app.root_path, 'static', 'exports')
app.config['PROJECT_FOLDER'] = os.path.join(app.root_path, 'static', 'projects')
app.config['VIDEO_FOLDER'] = os.path.join(app.root_path, 'static', 'videos')
app.config['ASSET_FOLDER'] = os.path.join(app.root_path, 'static', 'assets')
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max upload

CHECKPOINT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Comfy-UI", "models", "checkpoints")
LORA_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Comfy-UI", "models", "loras")

app.config['JUNK_FOLDER'] = os.path.join(app.root_path, 'static', 'junk')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif'}

for folder in [app.config['UPLOAD_FOLDER'], app.config['EXPORT_FOLDER'], 
               app.config['PROJECT_FOLDER'], app.config['VIDEO_FOLDER'], 
               app.config['ASSET_FOLDER'], app.config['JUNK_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

JUNK_FOLDER = app.config['JUNK_FOLDER']
IMAGE_FOLDER = app.config['UPLOAD_FOLDER']
AUDIO_FOLDER = os.path.join(app.root_path, 'static', 'audio')
os.makedirs(AUDIO_FOLDER, exist_ok=True)
OUTPUT_FOLDER = app.config['EXPORT_FOLDER']
FRAME_PATH = os.path.join(app.config['ASSET_FOLDER'], 'ZOOMPAN.png')
TARGET_SIZE = (512, 768)
LOG_FILE_PATH = os.path.join(app.root_path, "static", "app_log.txt")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def UID():
    return str(randint(1111111, 9999999))

def get_available_checkpoints():
    if not os.path.exists(CHECKPOINT_DIR):
        return []
    return sorted([f for f in os.listdir(CHECKPOINT_DIR) if f.endswith(('.safetensors', '.ckpt'))])

def get_available_loras():
    if not os.path.exists(LORA_DIR):
        return []
    return sorted([f for f in os.listdir(LORA_DIR) if f.endswith(('.safetensors', '.ckpt'))])

def logit(*args):
    try:
        timestr = datetime.now().strftime("%A_%b-%d-%Y_%H-%M-%S")
        frame = inspect.stack()[1]
        filename = os.path.basename(frame.filename)
        lineno = frame.lineno
        parts = []
        for arg in args:
            if isinstance(arg, (list, tuple, set)):
                parts.append(" ".join(map(str, arg)))
            else:
                parts.append(str(arg))
        message_str = " ".join(parts)
        log_message = f"{timestr} - File: {filename}, Line: {lineno}: {message_str}\n"
        with open(LOG_FILE_PATH, "a") as f:
            f.write(log_message)
    except Exception as e:
        ic("LOGIT ERROR:", e)

# --------------------------------------------------
# ZOOMPAN CORE & PROJECT MANAGEMENT
# --------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image_gallery')
def image_gallery():
    upload_dir = app.config['UPLOAD_FOLDER']
    image_files = []
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            if allowed_file(f):
                full_path = os.path.join(upload_dir, f)
                try:
                    stat = os.stat(full_path)
                    size_mb = round(stat.st_size / (1024 * 1024), 2)
                    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    
                    w, h = 0, 0
                    img_data = cv2.imread(full_path)
                    if img_data is not None:
                        h, w, _ = img_data.shape

                    image_files.append({
                        'filename': f,
                        'size_mb': size_mb,
                        'modified': mod_time,
                        'width': w,
                        'height': h,
                        'mtime': stat.st_mtime
                    })
                except Exception as e:
                    ic(f"Error reading image metadata for {f}:", e)

    image_files.sort(key=lambda x: x['mtime'], reverse=True)
    return render_template('image_gallery.html', images=image_files)

@app.route('/api/delete_image', methods=['POST'])
def api_delete_image():
    data = request.json or {}
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400

    safe_name = secure_filename(filename)
    target_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)

    if not os.path.exists(target_path):
        return jsonify({'error': 'Image file not found'}), 404

    try:
        os.remove(target_path)
        return jsonify({'success': True, 'message': f'Deleted {safe_name}'})
    except Exception as e:
        ic("Error deleting image:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@app.route('/upload', methods=['POST'])
def upload_image():
    logit("Received /api/upload request")
    if 'image' not in request.files:
        logit("Error: No 'image' in request.files")
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files['image']
    if file.filename == '':
        logit("Error: Empty filename selected")
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        logit(f"Received file: {filename}")
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{int(time.time())}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logit(f"Saved file to: {filepath}")
        img = cv2.imread(filepath)
        if img is None:
            logit(f"Error: cv2.imread failed on {filepath}")
            return jsonify({'error': 'Could not read uploaded image'}), 400
        h, w, _ = img.shape
        logit(f"Success upload {filename}: {w}x{h}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/static/uploads/{filename}',
            'width': w,
            'height': h
        })
    logit(f"Error: Invalid file type extension: {file.filename}")
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/save_json', methods=['POST'])
def save_json():
    data = request.json
    if not data or 'points' not in data or 'filename' not in data:
        return jsonify({'error': 'Invalid payload'}), 400
    
    project_name = data.get('project_name', 'points_project')
    project_filename = secure_filename(f"{project_name}.json")
    if not project_filename.endswith('.json'):
        project_filename += '.json'
        
    save_path = os.path.join(app.config['PROJECT_FOLDER'], project_filename)
    
    payload = {
        'project_name': project_name,
        'image_filename': data.get('filename'),
        'image_url': data.get('image_url'),
        'image_width': data.get('image_width'),
        'image_height': data.get('image_height'),
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'points': data.get('points', [])
    }
    
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
        
    return jsonify({
        'success': True,
        'project_filename': project_filename,
        'message': f'Saved successfully as {project_filename}'
    })

@app.route('/api/export_project_zip', methods=['POST'])
def export_project_zip():
    data = request.json or {}
    if not data or 'filename' not in data:
        return jsonify({'error': 'Source image filename is required'}), 400

    project_name = secure_filename(data.get('project_name', 'zoompan_project'))
    if not project_name:
        project_name = "zoompan_project"

    timestamp = int(time.time())
    zip_filename = f"{project_name}_{timestamp}.zip"
    zip_path = os.path.join(app.config['EXPORT_FOLDER'], zip_filename)

    image_filename = secure_filename(data.get('filename', ''))
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)

    audio_filename = data.get('audio_filename')
    audio_path = None
    if audio_filename and audio_filename.lower() != 'none':
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(audio_filename))
        if not os.path.exists(audio_path):
            audio_path = None

    video_filename = data.get('video_filename')
    video_path = None
    if video_filename and video_filename.lower() != 'none':
        v_test = os.path.join(app.config['VIDEO_FOLDER'], secure_filename(video_filename))
        if os.path.exists(v_test):
            video_path = v_test
        else:
            v_test2 = os.path.join(app.config['EXPORT_FOLDER'], secure_filename(video_filename))
            if os.path.exists(v_test2):
                video_path = v_test2

    project_payload = {
        'project_name': project_name,
        'image_filename': image_filename,
        'audio_filename': audio_filename if audio_path else None,
        'video_filename': video_filename if video_path else None,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'points': data.get('points', [])
    }

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('project.json', json.dumps(project_payload, indent=2))
            if os.path.exists(image_path):
                zipf.write(image_path, arcname=f"assets/{image_filename}")
            if audio_path and os.path.exists(audio_path):
                zipf.write(audio_path, arcname=f"assets/{os.path.basename(audio_path)}")
            if video_path and os.path.exists(video_path):
                zipf.write(video_path, arcname=f"video/{os.path.basename(video_path)}")

            readme_text = f"ZoomPan Studio Project Backup\n===============================\nProject Name: {project_name}\nExport Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            zipf.writestr('README.txt', readme_text)

        return jsonify({
            'success': True,
            'zip_filename': zip_filename,
            'zip_url': f'/static/exports/{zip_filename}',
            'message': f'Exported project backup: {zip_filename}'
        })

    except Exception as e:
        ic("Error creating project ZIP:", e)
        return jsonify({'error': str(e)}), 500

PROJECT_ROOT = os.path.join(app.root_path, 'projects')
if not os.path.exists(PROJECT_ROOT):
    os.makedirs(PROJECT_ROOT)

@app.route('/api/projects', methods=['GET', 'POST'])
def api_projects():
    if request.method == 'POST':
        data = request.get_json() or {}
        raw_name = data.get('name', '').strip()
        if not raw_name:
            return jsonify({'error': 'Project name is required'}), 400
        p_name = secure_filename(raw_name) or 'new_project'
        p_dir = os.path.join(PROJECT_ROOT, p_name)
        if not os.path.exists(p_dir):
            os.makedirs(p_dir)
            for sub in ['originals', 'pages', 'audio', 'videos']:
                os.makedirs(os.path.join(p_dir, sub), exist_ok=True)
            with open(os.path.join(p_dir, 'project.json'), 'w') as f:
                json.dump({'name': p_name, 'created_at': time.time()}, f)
        return jsonify({'status': 'success', 'name': p_name}), 200

    # GET method
    projects_list = []
    if os.path.exists(PROJECT_ROOT):
        for item in sorted(os.listdir(PROJECT_ROOT)):
            p_dir = os.path.join(PROJECT_ROOT, item)
            if os.path.isdir(p_dir):
                counts = {'originals': 0, 'pages': 0, 'audio': 0, 'videos': 0}
                for sub in counts.keys():
                    sub_path = os.path.join(p_dir, sub)
                    if os.path.exists(sub_path):
                        counts[sub] = len([f for f in os.listdir(sub_path) if not f.startswith('.')])
                projects_list.append({
                    'name': item,
                    'path': p_dir,
                    'counts': counts
                })
    return jsonify({'projects': projects_list}), 200

@app.route('/projects')
def projects_page():
    return render_template('projects.html')

@app.route('/api/list_json', methods=['GET'])
def list_json():
    files = [f for f in os.listdir(app.config['PROJECT_FOLDER']) if f.endswith('.json')]
    return jsonify({'projects': files})

@app.route('/api/load_json/<filename>', methods=['GET'])
def load_json(filename):
    safe_filename = secure_filename(filename)
    file_path = os.path.join(app.config['PROJECT_FOLDER'], safe_filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Project file not found'}), 404
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

def cubic_easing(t):
    return t * t * (3 - 2 * t)

def wrap_text_to_lines(text, max_chars=28):
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split()
        if not words:
            continue
        curr_line = []
        curr_len = 0
        for w in words:
            if curr_len + len(w) + 1 > max_chars and curr_line:
                lines.append(" ".join(curr_line))
                curr_line = [w]
                curr_len = len(w)
            else:
                curr_line.append(w)
                curr_len += len(w) + (1 if curr_len > 0 else 0)
        if curr_line:
            lines.append(" ".join(curr_line))
    return lines if lines else [text]

def draw_comic_bubble(frame, px, py, text, bubble_style='speech'):
    if not text or not str(text).strip():
        return
    
    lines = wrap_text_to_lines(text, max_chars=26)
    char_count = sum(len(l) for l in lines)
    
    if bubble_style == 'sfx':
        font_scale = 1.0 if char_count <= 8 else 0.75
        thickness = 3
    elif char_count <= 10:
        font_scale = 0.85
        thickness = 2
    elif char_count <= 50:
        font_scale = 0.65
        thickness = 2
    elif char_count <= 120:
        font_scale = 0.55
        thickness = 1
    else:
        font_scale = 0.45
        thickness = 1
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    line_sizes = [cv2.getTextSize(l, font, font_scale, thickness)[0] for l in lines]
    max_w = max(sz[0] for sz in line_sizes) if line_sizes else 100
    total_h = sum(sz[1] + 8 for sz in line_sizes)
    
    pad_x, pad_y = 16, 14
    box_w = max_w + pad_x * 2
    box_h = total_h + pad_y * 2
    
    box_x = max(10, min(px - box_w // 2, frame.shape[1] - box_w - 10))
    box_y = max(10, py - box_h - 25)
    if box_y < 10:
        box_y = py + 25
        
    center_box_x = box_x + box_w // 2
    if bubble_style in ('speech', 'speech_left'):
        tail_x = box_x + 20
        tail_pts = np.array([[tail_x - 10, box_y + box_h], [tail_x + 10, box_y + box_h], [px, py]], np.int32)
        cv2.fillPoly(frame, [tail_pts], (255, 255, 255), lineType=cv2.LINE_AA)
        cv2.polylines(frame, [tail_pts], True, (0, 0, 0), 2, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 2, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'speech_right':
        tail_x = box_x + box_w - 20
        tail_pts = np.array([[tail_x - 10, box_y + box_h], [tail_x + 10, box_y + box_h], [px, py]], np.int32)
        cv2.fillPoly(frame, [tail_pts], (255, 255, 255), lineType=cv2.LINE_AA)
        cv2.polylines(frame, [tail_pts], True, (0, 0, 0), 2, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 2, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style in ('thought', 'thought_left'):
        t_x = box_x + 20
        cv2.circle(frame, (int(px * 0.6 + t_x * 0.4), int(py * 0.6 + (box_y + box_h) * 0.4)), 4, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.6 + t_x * 0.4), int(py * 0.6 + (box_y + box_h) * 0.4)), 4, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.2 + t_x * 0.8), int(py * 0.2 + (box_y + box_h) * 0.8)), 7, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.2 + t_x * 0.8), int(py * 0.2 + (box_y + box_h) * 0.8)), 7, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 2, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'thought_right':
        t_x = box_x + box_w - 20
        cv2.circle(frame, (int(px * 0.6 + t_x * 0.4), int(py * 0.6 + (box_y + box_h) * 0.4)), 4, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.6 + t_x * 0.4), int(py * 0.6 + (box_y + box_h) * 0.4)), 4, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.2 + t_x * 0.8), int(py * 0.2 + (box_y + box_h) * 0.8)), 7, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.2 + t_x * 0.8), int(py * 0.2 + (box_y + box_h) * 0.8)), 7, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 2, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'idea':
        bg_gold = (0, 229, 255)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), bg_gold, 3, lineType=cv2.LINE_AA)
        cv2.circle(frame, (center_box_x, box_y - 8), 6, bg_gold, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (center_box_x, box_y - 8), 8, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'caption':
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (102, 240, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 3, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'sfx':
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (40, 50, 240), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), 2, lineType=cv2.LINE_AA)
        text_color = (255, 255, 255)
    elif bubble_style == 'manga':
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (10, 10, 10), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), 3, lineType=cv2.LINE_AA)
        text_color = (255, 255, 255)
    elif bubble_style == 'noir':
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (194, 236, 244), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (19, 32, 45), 2, lineType=cv2.LINE_AA)
        text_color = (19, 32, 45)
    elif bubble_style == 'hero':
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (138, 58, 30), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (11, 158, 245), 3, lineType=cv2.LINE_AA)
        text_color = (255, 255, 255)
    else:
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (25, 20, 15), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 229, 0), 2, lineType=cv2.LINE_AA)
        text_color = (255, 255, 255)

    curr_y = box_y + pad_y + line_sizes[0][1]
    for idx, l in enumerate(lines):
        line_w = line_sizes[idx][0]
        tx = box_x + (box_w - line_w) // 2
        cv2.putText(frame, l, (tx, curr_y), font, font_scale, text_color, thickness, cv2.LINE_AA)
        if idx < len(lines) - 1:
            curr_y += line_sizes[idx + 1][1] + 8

def render_frame(img, center_x, center_y, zoom, out_w, out_h, point_obj=None, render_labels=False):
    if len(img.shape) == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    img_h, img_w, _ = img.shape[:3]
    zoom = max(1.0, float(zoom))
    
    crop_w = img_w / zoom
    crop_h = img_h / zoom
    
    target_aspect = out_w / out_h
    current_aspect = crop_w / crop_h
    
    if current_aspect > target_aspect:
        crop_h = crop_w / target_aspect
    else:
        crop_w = crop_h * target_aspect

    t_zoom = min(1.0, max(0.0, (zoom - 1.0) / 0.8))
    eff_center_x = (img_w / 2.0) + (center_x - (img_w / 2.0)) * t_zoom
    eff_center_y = (img_h / 2.0) + (center_y - (img_h / 2.0)) * t_zoom
    
    left = eff_center_x - crop_w / 2.0
    top = eff_center_y - crop_h / 2.0
    
    left = max(0, min(left, img_w - crop_w))
    top = max(0, min(top, img_h - crop_h))
    
    right = left + crop_w
    bottom = top + crop_h
    
    src_pts = np.float32([[left, top], [right, top], [left, bottom]])
    dst_pts = np.float32([[0, 0], [out_w, 0], [0, out_h]])
    M = cv2.getAffineTransform(src_pts, dst_pts)
    
    frame = cv2.warpAffine(img, M, (out_w, out_h), flags=cv2.INTER_CUBIC)
    
    if render_labels and point_obj:
        pt_x = float(point_obj['x'])
        pt_y = float(point_obj['y'])
        pt_screen = M @ np.array([pt_x, pt_y, 1.0])
        px, py = int(pt_screen[0]), int(pt_screen[1])
        
        label_text = point_obj.get('label', '')
        style = point_obj.get('bubble_style', 'speech')
        draw_comic_bubble(frame, px, py, label_text, bubble_style=style)
        
    return frame

@app.route('/api/list_audio', methods=['GET'])
def api_list_audio():
    audio_files = set()
    for search_dir in [app.config['UPLOAD_FOLDER'], app.config['EXPORT_FOLDER']]:
        if os.path.exists(search_dir):
            for f in os.listdir(search_dir):
                if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac')) and not f.startswith('temp_'):
                    audio_files.add(f)
    return jsonify({'audio_files': sorted(list(audio_files))})

@app.route('/api/audio_info/<filename>', methods=['GET'])
def api_audio_info(filename):
    safe_name = secure_filename(filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    if not os.path.exists(audio_path):
        audio_path = os.path.join(app.config['EXPORT_FOLDER'], safe_name)
    if not os.path.exists(audio_path):
        return jsonify({'error': f'Audio file {safe_name} not found'}), 404
    try:
        audio = AudioSegment.from_file(audio_path)
        duration_sec = round(len(audio) / 1000.0, 2)
        return jsonify({
            'success': True,
            'filename': safe_name,
            'duration_seconds': duration_sec
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_mp4', methods=['POST'])
def generate_mp4():
    data = request.json
    if not data or 'points' not in data or 'filename' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
        
    points = data['points']
    if not points:
        return jsonify({'error': 'At least 1 point is required to generate video'}), 400
        
    img_filename = secure_filename(data['filename'])
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
    if not os.path.exists(img_path):
        return jsonify({'error': f'Source image {img_filename} not found'}), 404
        
    img = cv2.imread(img_path)
    if img is None:
        return jsonify({'error': 'Failed to load source image'}), 400
        
    img_h, img_w, _ = img.shape
    fps = int(data.get('fps', 30))
    render_labels = bool(data.get('render_labels', True))
    output_res = data.get('resolution', '1080p')
    audio_filename = data.get('audio_filename')
    
    if output_res == '1080p':
        out_w, out_h = 1920, 1080
    elif output_res == '720p':
        out_w, out_h = 1280, 720
    else:
        out_w, out_h = img_w, img_h
        
    out_w = out_w if out_w % 2 == 0 else out_w - 1
    out_h = out_h if out_h % 2 == 0 else out_h - 1
    video_filename = f"zoom_pan_{int(time.time())}.mp4"
    video_path = os.path.join(app.config['EXPORT_FOLDER'], video_filename)
    raw_filename = f"raw_{video_filename}"
    raw_path = os.path.join(app.config['EXPORT_FOLDER'], raw_filename)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(raw_path, fourcc, fps, (out_w, out_h))
    
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(raw_path, fourcc, fps, (out_w, out_h))

    keyframes = []
    start_kf = {
        'x': img_w / 2.0,
        'y': img_h / 2.0,
        'zoom': 1.0,
        'label': None,
        'bubble_style': 'speech',
        'transition_duration': 1.5,
        'hold_duration': 1.0
    }
    keyframes.append(start_kf)
    
    for idx, p in enumerate(points):
        zoom_enabled = p.get('zoom_enabled', True)
        if zoom_enabled is False or str(zoom_enabled).lower() == 'false':
            is_zoom = False
        else:
            is_zoom = True
        if is_zoom:
            target_x = float(p['x'])
            target_y = float(p['y'])
            target_zoom = float(p.get('zoom', 2.5))
        else:
            target_x = img_w / 2.0
            target_y = img_h / 2.0
            target_zoom = 1.0
        keyframes.append({
            'num': idx + 1,
            'x': target_x,
            'y': target_y,
            'zoom': target_zoom,
            'pt_x': float(p['x']),
            'pt_y': float(p['y']),
            'label': p.get('label', f'Point {idx+1}'),
            'bubble_style': p.get('bubble_style', 'speech'),
            'transition_duration': float(p.get('transition_duration', 2.0)),
            'hold_duration': float(p.get('hold_duration', 1.5))
        })
        
    total_frames_rendered = 0
    
    for i in range(len(keyframes)):
        curr_kf = keyframes[i]
        
        if i > 0:
            prev_kf = keyframes[i - 1]
            trans_sec = curr_kf['transition_duration']
            num_trans_frames = max(1, int(trans_sec * fps))
            
            for f in range(num_trans_frames):
                t = f / float(num_trans_frames)
                ease_t = cubic_easing(t)
                
                curr_x = prev_kf['x'] + (curr_kf['x'] - prev_kf['x']) * ease_t
                curr_y = prev_kf['y'] + (curr_kf['y'] - prev_kf['y']) * ease_t
                curr_zoom = prev_kf['zoom'] + (curr_kf['zoom'] - prev_kf['zoom']) * ease_t
                
                active_kf = curr_kf if ease_t > 0.5 else prev_kf
                active_point = {
                    'x': active_kf.get('pt_x', active_kf['x']),
                    'y': active_kf.get('pt_y', active_kf['y']),
                    'label': active_kf.get('label'),
                    'bubble_style': active_kf.get('bubble_style', 'speech')
                }
                
                frame = render_frame(
                    img, curr_x, curr_y, curr_zoom, out_w, out_h,
                    point_obj=active_point, render_labels=render_labels
                )
                out.write(frame)
                total_frames_rendered += 1

        hold_sec = curr_kf['hold_duration']
        num_hold_frames = max(1, int(hold_sec * fps))
        
        active_point = {
            'x': curr_kf.get('pt_x', curr_kf['x']),
            'y': curr_kf.get('pt_y', curr_kf['y']),
            'label': curr_kf.get('label'),
            'bubble_style': curr_kf.get('bubble_style', 'speech')
        }
        
        hold_frame = render_frame(
            img, curr_kf['x'], curr_kf['y'], curr_kf['zoom'], out_w, out_h,
            point_obj=active_point, render_labels=render_labels
        )
        
        for _ in range(num_hold_frames):
            out.write(hold_frame)
            total_frames_rendered += 1

    out.release()
    
    audio_path = None
    if audio_filename and audio_filename.lower() != 'none':
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(audio_filename))
        if not os.path.exists(audio_path):
            audio_path = None

    try:
        if audio_path:
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', raw_path,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                '-pix_fmt', 'yuv420p',
                '-preset', 'fast',
                '-crf', '22',
                '-movflags', '+faststart',
                video_path
            ]
        else:
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', raw_path,
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'fast',
                '-crf', '22',
                '-movflags', '+faststart',
                video_path
            ]
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(raw_path):
            os.remove(raw_path)
    except Exception as e:
        ic("FFmpeg transcode warning:", e)
        if os.path.exists(raw_path) and not os.path.exists(video_path):
            os.rename(raw_path, video_path)

    try:
        shutil.copyfile(video_path, os.path.join(app.config['VIDEO_FOLDER'], video_filename))
    except Exception as e:
        ic("Copy to videos folder warning:", e)

    return jsonify({
        'success': True,
        'video_url': f'/static/exports/{video_filename}',
        'filename': video_filename,
        'total_frames': total_frames_rendered,
        'duration_seconds': round(total_frames_rendered / fps, 2)
    })

# --------------------------------------------------
# IMAGE GENERATION (STABLE DIFFUSION & LORA ENGINE)
# --------------------------------------------------
pipe = None
current_device = None
current_model_path = None
current_lora_path = None
current_lora_scale = 0.15

def get_device(preference="auto"):
    if preference == "auto":
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    return preference

def load_pipeline(model_path, device_pref="auto"):
    global pipe, current_device, current_model_path, current_lora_path
    device = get_device(device_pref)
    current_device = device
    print(f"[*] Target generation device: {device.upper()}")
    if device == "cpu":
        print("[!] WARNING: Running on CPU will be extremely slow.")
    is_lcm = "lcm" in model_path.lower()
    print(f"[*] Detected model type: {'LCM' if is_lcm else 'Standard SD 1.5'}")
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"[*] Loading model checkpoint: {model_path}")
    
    if pipe is not None:
        try:
            del pipe
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    pipeline = StableDiffusionPipeline.from_single_file(
        model_path,
        torch_dtype=torch_dtype,
        use_safetensors=True,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipeline = pipeline.to(device)
    if device == "cpu":
        pipeline.enable_attention_slicing()
    elif device == "cuda":
        if hasattr(pipeline, "enable_xformers_memory_efficient_attention"):
            pipeline.enable_xformers_memory_efficient_attention()
        else:
            pipeline.enable_attention_slicing()
    if is_lcm:
        pipeline.scheduler = LCMScheduler.from_config(pipeline.scheduler.config)
    else:
        pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
            pipeline.scheduler.config,
            use_karras_sigmas=True
        )
    pipe = pipeline
    current_model_path = model_path
    current_lora_path = None
    print("[+] Pipeline ready.")

def apply_lora(lora_path, lora_scale=0.15):
    global pipe, current_lora_path, current_lora_scale
    if pipe is None:
        return
    
    if hasattr(pipe, "unfuse_lora"):
        try:
            pipe.unfuse_lora()
            pipe.unload_lora_weights()
        except Exception as e:
            ic("Unfuse LoRA note:", e)

    if lora_path and os.path.exists(lora_path):
        print(f"[*] Loading LoRA: {lora_path} (scale={lora_scale})")
        pipe.load_lora_weights(lora_path, adapter_name="custom_lora")
        pipe.fuse_lora(lora_scale=lora_scale)
        current_lora_path = lora_path
        current_lora_scale = lora_scale
        print("[+] LoRA weights loaded and fused successfully.")
    else:
        current_lora_path = None
        current_lora_scale = 0.15
        print("[*] Cleared LoRA weights.")

def get_generation_history(output_dir="static/uploads/"):
    db_path = os.path.join(output_dir, "generations.json")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"next_image_id": 1, "runs": []}

@app.route('/generation')
def generation():
    history = get_generation_history()
    runs = list(reversed(history.get("runs", [])))
    checkpoints = get_available_checkpoints()
    loras = get_available_loras()
    current_model_name = os.path.basename(current_model_path) if current_model_path else ""
    current_lora_name = os.path.basename(current_lora_path) if current_lora_path else ""

    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'static', 'uploads'))
    uploads = sorted([f for f in os.listdir(upload_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))], reverse=True) if os.path.exists(upload_folder) else []

    return render_template(
        'generation.html',
        history=runs,
        model_path=current_model_path,
        current_model_name=current_model_name,
        current_lora_name=current_lora_name,
        device=current_device,
        checkpoints=checkpoints,
        loras=loras,
        uploads=uploads
    )

@app.route('/api/models', methods=['GET'])
def api_models():
    return jsonify({
        'checkpoints': get_available_checkpoints(),
        'loras': get_available_loras(),
        'current_model': current_model_path,
        'current_model_name': os.path.basename(current_model_path) if current_model_path else "",
        'current_lora': current_lora_path,
        'current_lora_name': os.path.basename(current_lora_path) if current_lora_path else "",
        'current_lora_scale': current_lora_scale,
        'is_loaded': (pipe is not None)
    })

@app.route('/api/model_status', methods=['GET'])
def api_model_status():
    global pipe, current_model_path
    loaded = (pipe is not None)
    model_name = os.path.basename(current_model_path) if current_model_path else ""
    return jsonify({"loaded": loaded, "model_name": model_name})

@app.route('/api/toggle_model', methods=['POST'])
def api_toggle_model():
    global pipe, current_model_path, current_device
    if pipe is not None:
        print("[*] Unloading model pipeline to free memory...")
        try:
            del pipe
            pipe = None
        except Exception as e:
            print(f"[!] Error deleting pipe: {e}")
            pipe = None
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        try:
            import ctypes
            libc = ctypes.CDLL('libc.so.6')
            libc.malloc_trim(0)
            print("[+] malloc_trim(0) called: freed RAM back to OS kernel for htop.")
        except Exception as ex:
            print(f"[!] malloc_trim note: {ex}")

        return jsonify({"loaded": False, "status": "unloaded", "message": "Stable Diffusion model unloaded and memory freed!"})
    else:
        print("[*] Reloading model pipeline...")
        checkpoints = get_available_checkpoints()
        model_to_load = current_model_path
        if not model_to_load and checkpoints:
            model_to_load = os.path.join(CHECKPOINT_DIR, checkpoints[0])
        
        if model_to_load and os.path.exists(model_to_load):
            load_pipeline(model_to_load, current_device or "auto")
            model_name = os.path.basename(model_to_load)
            return jsonify({"loaded": True, "status": "loaded", "model_name": model_name, "message": f"Loaded model: {model_name}"})
        else:
            return jsonify({"loaded": False, "status": "error", "message": "No valid model checkpoint found to load."}), 400

@app.route('/api/generate_image', methods=['POST', 'GET'])
def generate_image():
    global pipe, current_model_path, current_lora_path, current_lora_scale
    data = request.get_json() or {}
    
    requested_model = data.get('model')
    if requested_model:
        if not os.path.isabs(requested_model):
            requested_model = os.path.join(CHECKPOINT_DIR, requested_model)
        if os.path.exists(requested_model) and requested_model != current_model_path:
            print(f"[*] Switching model checkpoint to: {requested_model}")
            load_pipeline(requested_model, current_device or "auto")

    if pipe is None:
        checkpoints = get_available_checkpoints()
        if checkpoints:
            default_path = os.path.join(CHECKPOINT_DIR, checkpoints[0])
            load_pipeline(default_path, current_device or "auto")
        else:
            return jsonify({"error": "No SD model loaded and no checkpoints found."}), 500

    requested_lora = data.get('lora')
    requested_lora_scale = float(data.get('lora_scale', 0.15))

    if requested_lora:
        if requested_lora.lower() in ('none', '', 'null'):
            if current_lora_path is not None:
                apply_lora(None)
        else:
            if not os.path.isabs(requested_lora):
                requested_lora = os.path.join(LORA_DIR, requested_lora)
            if requested_lora != current_lora_path or requested_lora_scale != current_lora_scale:
                apply_lora(requested_lora, requested_lora_scale)

    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({"error": "Missing required field: prompt"}), 400
    negative_prompt = data.get('negative_prompt', "blurry, out of focus, text, captions, low quality, pixelated, worst quality")
    steps = int(data.get('steps', 5))
    guidance = float(data.get('guidance', 1.5))
    width = int(data.get('width', 512))
    height = int(data.get('height', 768))
    seed = int(data.get('seed', -1))
    if seed < 0:
        seed = int(datetime.now().timestamp()) % 1000000
    num_images = min(max(int(data.get('num_images', 1)), 1), 8)
    output_dir = data.get('output_dir', 'static/uploads/')
    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(output_dir, "generations.json")
    db = get_generation_history(output_dir)
    results = []
    current_seed = seed
    model_name = os.path.basename(current_model_path).replace(".", "_") if current_model_path else "sd_model"
    
    for i in range(num_images):
        print(f"[*] Run {i+1}/{num_images}: seed={current_seed}, steps={steps}, CFG={guidance}")
        generator = torch.Generator(device=current_device).manual_seed(current_seed)
        try:
            with torch.inference_mode():
                output = pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    width=width,
                    height=height,
                    generator=generator
                )
                image = output.images[0]
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return jsonify({"error": str(e), "partial_results": results}), 500
        img_id = db.get("next_image_id", 1)
        filename = f"{model_name}_img_{img_id:06d}.png"
        save_path = os.path.join(output_dir, filename)
        image.save(save_path)
        print(f"[+] Saved: {save_path}")
        entry = {
            "image_id": img_id,
            "file": filename,
            "url": f"/static/uploads/{filename}",
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "guidance_scale": guidance,
            "seed": current_seed,
            "width": width,
            "height": height,
            "model": current_model_path,
            "lora": current_lora_path,
            "lora_scale": current_lora_scale
        }
        db["runs"].append(entry)
        db["next_image_id"] = img_id + 1
        results.append(entry)
        with open(db_path, "w") as f:
            json.dump(db, f, indent=4)
        current_seed += 1
    return jsonify({
        "success": True,
        "images": results,
        "output_dir": os.path.abspath(output_dir)
    })

@app.route('/static/uploads/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/uploads', filename)

@app.route('/api/history', methods=['GET'])
def api_history():
    history = get_generation_history()
    return jsonify(history)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "device": current_device,
        "model_loaded": pipe is not None,
        "model_path": current_model_path,
        "lora_path": current_lora_path
    })

# --------------------------------------------------
# SEQUENCED VIDEOS & MOVIEPY COMPOSITOR
# --------------------------------------------------
def resize_all_images():
    ic("Checking image dimensions...")
    if not os.path.exists(JUNK_FOLDER):
        return
    image_files = [f for f in os.listdir(JUNK_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for filename in image_files:
        image_path = os.path.join(JUNK_FOLDER, filename)
        try:
            with Image.open(image_path) as img:
                if img.size != TARGET_SIZE:
                    resized_img = img.resize(TARGET_SIZE, Image.LANCZOS)
                    resized_img.save(image_path)
        except Exception as e:
            ic(f"Error processing {filename}: {e}")

@app.route('/sequenced_video')
def sequenced_video():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg','.jpeg','.png'))] if os.path.exists(IMAGE_FOLDER) else []
    mp3s = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.mp3')] if os.path.exists(AUDIO_FOLDER) else []
    mp4s = [f for f in os.listdir(app.config['VIDEO_FOLDER']) if f.lower().endswith('.mp4')] if os.path.exists(app.config['VIDEO_FOLDER']) else []
    return render_template('sequence.html', images=images, mp3s=mp3s, mp4s=mp4s)

def overlay_frame(image_path, frame_path, output_path):
    base = Image.open(image_path).convert("RGBA")
    frame = Image.open(frame_path).convert("RGBA").resize(base.size)
    combined = Image.alpha_composite(base, frame)
    combined.convert("RGB").save(output_path, "JPEG")

def pad_audio_with_silence(audio_path, output_path, pad_duration_ms=500):
    original = AudioSegment.from_mp3(audio_path)
    silence = AudioSegment.silent(duration=pad_duration_ms)
    padded = silence + original + silence
    padded.export(output_path, format="mp3")

@app.route('/create_video', methods=['POST'])
def create_video():
    selected_images = request.form.getlist('images')
    selected_audio = request.form.get('audio')
    ic(selected_images, selected_audio)
    if not selected_images:
        return "No images selected.", 400
    if not selected_audio:
        return "No audio selected.", 400

    image_sequence = []
    for img in selected_images:
        seq_val = request.form.get(f"sequence_{img}")
        if not seq_val:
            return f"Missing sequence number for {img}", 400
        image_sequence.append((int(seq_val), img))
    sorted_images = [img for _, img in sorted(image_sequence, key=lambda x: x[0])]
    
    frame_exists = os.path.exists(FRAME_PATH)
    processed_paths = []
    for i, image_name in enumerate(sorted_images):
        src = os.path.join(IMAGE_FOLDER, image_name)
        output_img = os.path.join(OUTPUT_FOLDER, f"processed_{i}.jpg")
        if frame_exists:
            overlay_frame(src, FRAME_PATH, output_img)
        else:
            Image.open(src).convert("RGB").save(output_img, "JPEG")
        processed_paths.append(output_img)
        
    original_audio_path = os.path.join(AUDIO_FOLDER, secure_filename(selected_audio))
    padded_audio_path = os.path.join(OUTPUT_FOLDER, "temp_audio.mp3")
    pad_audio_with_silence(original_audio_path, padded_audio_path)
    audio_clip = AudioFileClip(padded_audio_path)
    total_duration = audio_clip.duration
    image_duration = total_duration / len(processed_paths)
    clips = [
        ImageClip(path).set_duration(image_duration)
        for path in processed_paths
    ]
    final_video = concatenate_videoclips(
        clips,
        method="compose"
    ).set_audio(audio_clip)
    
    video_filename = f"{UID()}final_video.mp4"
    output_video_path = os.path.join(app.config['VIDEO_FOLDER'], video_filename)
    try:
        final_video.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24
        )
        return redirect(url_for("serve_video", filename=video_filename))
    except Exception as e:
        ic("Error creating video:", e)
        return "Error creating video.", 500

@app.route('/video/<filename>')
def serve_video(filename):
    v_path = os.path.join(app.config['VIDEO_FOLDER'], filename)
    if not os.path.exists(v_path):
        v_path = os.path.join(app.config['EXPORT_FOLDER'], filename)
    if not os.path.exists(v_path):
        v_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(
        v_path,
        mimetype='video/mp4',
        conditional=True
    )

# --------------------------------------------------
# VIDEO TITLE FRAME OVERLAY & VIDEO GALLERY ROUTES
# --------------------------------------------------
def add_title_image(video_path, hex_color="#f9f0b4", frame_path=None, output_filename=None):
    if not frame_path or not os.path.exists(frame_path):
        frame_path = os.path.join(app.config['ASSET_FOLDER'], 'ZOOMPAN.png')
        if not os.path.exists(frame_path):
            raise FileNotFoundError(f"Frame overlay image not found: {frame_path}")

    if not os.path.exists(video_path):
        alt_path = os.path.join(app.config['VIDEO_FOLDER'], os.path.basename(video_path))
        if os.path.exists(alt_path):
            video_path = alt_path
        else:
            raise FileNotFoundError(f"Source video not found: {video_path}")

    clean_hex = hex_color.lstrip('#')
    if len(clean_hex) == 6:
        r = int(clean_hex[0:2], 16)
        g = int(clean_hex[2:4], 16)
        b = int(clean_hex[4:6], 16)
        rgb_tuple = (r, g, b)
    else:
        rgb_tuple = (249, 240, 180)

    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size

    padded_size = (width + 20, height + 20)
    x_position = (padded_size[0] - width) / 2.0
    y_position = (padded_size[1] - height) / 2.0

    background = ColorClip(padded_size, color=rgb_tuple).set_duration(video_clip.duration)
    padded_video_clip = CompositeVideoClip(
        [background, video_clip.set_position((x_position, y_position))]
    ).set_duration(video_clip.duration)


    title_image = ImageClip(frame_path).set_duration(video_clip.duration).set_position((0, -5)).resize(padded_video_clip.size)
    composite_clip = CompositeVideoClip([padded_video_clip, title_image])

    if not output_filename:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_filename = f"framed_{base_name}_{int(time.time())}.mp4"

    output_path = os.path.join(app.config['VIDEO_FOLDER'], output_filename)

    composite_clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=video_clip.fps or 24,
        verbose=False,
        logger=None
    )

    composite_clip.close()
    padded_video_clip.close()
    title_image.close()
    background.close()
    video_clip.close()

    return output_filename, output_path

@app.route('/frame_video')
def frame_video():
    videos = [f for f in os.listdir(app.config['VIDEO_FOLDER']) if f.lower().endswith(('.mp4', '.webm', '.mov'))]
    selected = request.args.get('video', '')
    return render_template('frame_video.html', videos=videos, selected_video=selected)

@app.route('/video_gallery')
def video_gallery():
    video_dir = app.config['VIDEO_FOLDER']
    video_files = []
    if os.path.exists(video_dir):
        for f in os.listdir(video_dir):
            if f.lower().endswith(('.mp4', '.webm', '.mov')):
                full_path = os.path.join(video_dir, f)
                stat = os.stat(full_path)
                size_mb = round(stat.st_size / (1024 * 1024), 2)
                mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                video_files.append({
                    'filename': f,
                    'size_mb': size_mb,
                    'modified': mod_time,
                    'is_framed': f.startswith('framed_'),
                    'mtime': stat.st_mtime
                })
    video_files.sort(key=lambda x: x['mtime'], reverse=True)
    return render_template('video_gallery.html', videos=video_files)

@app.route('/api/delete_video', methods=['POST'])
def api_delete_video():
    data = request.json or {}
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400

    safe_name = secure_filename(filename)
    target_path = os.path.join(app.config['VIDEO_FOLDER'], safe_name)

    if not os.path.exists(target_path):
        return jsonify({'error': 'Video file not found'}), 404

    try:
        os.remove(target_path)
        return jsonify({'success': True, 'message': f'Deleted {safe_name}'})
    except Exception as e:
        ic("Error deleting video:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_title_image', methods=['POST'])
def api_add_title_image():
    data = request.json or {}
    video_filename = data.get('video_filename')
    if not video_filename:
        return jsonify({'error': 'No video_filename provided'}), 400

    hex_color = data.get('hex_color', '#f9f0b4')
    frame_path = data.get('frame_path')

    video_path = os.path.join(app.config['VIDEO_FOLDER'], secure_filename(video_filename))

    try:
        out_filename, out_path = add_title_image(video_path, hex_color=hex_color, frame_path=frame_path)
        return jsonify({
            'success': True,
            'filename': out_filename,
            'video_url': f'/static/videos/{out_filename}',
            'message': 'Title image frame applied successfully!'
        })
    except Exception as e:
        ic("Error adding title frame:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/list_videos', methods=['GET'])
def api_list_videos():
    videos = [f for f in os.listdir(app.config['VIDEO_FOLDER']) if f.lower().endswith(('.mp4', '.webm', '.mov'))]
    return jsonify({'videos': videos})

# --------------------------------------------------
# KOKORO TTS & REFLECTIVE SCRIPT GENERATION
# --------------------------------------------------
TTS_voices = [
    'af_alloy','af_aoede','af_bella','af_heart','af_jessica','af_kore',
    'af_nicole','af_nova','af_river','af_sarah','af_sky','am_adam','am_echo','am_eric',
    'am_fenrir','am_liam','am_michael','am_onyx','am_puck','am_santa','bf_alice','bf_emma',
    'bf_isabella','bf_lily','bm_daniel','bm_fable','bm_george','bm_lewis','ef_dora',
    'em_alex','em_santa','ff_siwis','hf_alpha','hf_beta','hm_omega','hm_psi','if_sara',
    'im_nicola','jf_alpha','jf_gongitsune','jf_nezumi','jf_tebukuro','jm_kumo','pf_dora',
    'pm_alex','pm_santa','zf_xiaobei','zf_xiaoni','zf_xiaoxiao','zf_xiaoyi'
]
KOKORO_TTS_URL = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE = "am_echo"

COMMA_PAUSE = 0.5           # pause at comma
SENTENCE_PAUSE = 1.0        # end of normal sentence
QUESTION_PAUSE = 1.2        # end of question
PARAGRAPH_PAUSE = 1.75      # between paragraphs
SHORT_SENTENCE_THRESHOLD = 6
SHORT_SENTENCE_MULTIPLIER = 1.4
DRAMATIC_KEYWORDS = ["but", "however", "until", "except", "though", "suddenly", "then", "yet"]
DRAMATIC_MULTIPLIER = 1.2
DIALOGUE_SENTENCE_PAUSE = 0.95
NARRATOR_RETURN_PAUSE = 2.0  # after dialogue ends

def is_dialogue(line):
    s = line.strip()
    return (s.startswith('"') and s.endswith('"')) or (s.startswith('“') and s.endswith('”')) or (s.startswith("'") and s.endswith("'"))

def count_words(text):
    return len(text.strip().split())

def contains_dramatic_word(text):
    lower = text.lower()
    return any(word in lower for word in DRAMATIC_KEYWORDS)

def split_into_sentences(paragraph):
    sentence_end_re = re.compile(r'([.!?]["\'”’]*)')
    parts = sentence_end_re.split(paragraph)
    sentences = []
    for i in range(0, len(parts)-1, 2):
        sentence = parts[i].strip() + parts[i+1]
        if sentence.strip():
            sentences.append(sentence.strip())
    if len(parts) % 2 != 0 and parts[-1].strip():
        sentences.append(parts[-1].strip())
    return sentences

def segment_paragraph(paragraph):
    pattern = re.compile(r'("[^"]+"|\“[^\”]+\”|\'[^\']+\')')
    raw_parts = pattern.split(paragraph)
    segments = []
    for part in raw_parts:
        text = part.strip()
        if not text:
            continue
        is_quote = (
            (text.startswith('"') and text.endswith('"')) or
            (text.startswith('“') and text.endswith('”')) or
            (text.startswith("'") and text.endswith("'"))
        )
        segments.append({
            'text': text,
            'is_dialogue': is_quote
        })
    return segments

def clean_line(line):
    line = line.lstrip("*").lstrip("-").lstrip()
    return line

def calculate_pause(sentence, is_dialogue_line):
    word_count = count_words(sentence)
    if is_dialogue_line:
        pause = DIALOGUE_SENTENCE_PAUSE
    else:
        clean_end = sentence.strip(' "\'”’')
        pause = QUESTION_PAUSE if clean_end.endswith("?") else SENTENCE_PAUSE
    if word_count <= SHORT_SENTENCE_THRESHOLD:
        pause *= SHORT_SENTENCE_MULTIPLIER
    if contains_dramatic_word(sentence):
        pause *= DRAMATIC_MULTIPLIER
    return round(min(pause, 3.0), 2)

def calculate_comma_pauses(sentence):
    return sentence.count(",") * COMMA_PAUSE

def generate_mp3_with_kokoro_tts(text_to_speak, output_mp3_path, voice=ASSISTANT_VOICE):
    try:
        os.makedirs(os.path.dirname(output_mp3_path), exist_ok=True)
        clean_text = (
            text_to_speak.replace("*", "")
            .replace("…", ", ")
            .strip()
        )
        payload = {
            "model": "kokoro",
            "voice": voice,
            "format": "mp3",
            "input": clean_text
        }
        ic("Sending to Kokoro:", payload)
        r = requests.post(KOKORO_TTS_URL, json=payload, timeout=(30, 600))
        if r.status_code != 200:
            return None, f"Kokoro error {r.status_code}: {r.text}"
        with open(output_mp3_path, "wb") as f:
            f.write(r.content)
        ic("MP3 saved:", output_mp3_path)
        return output_mp3_path, None
    except Exception as e:
        ic("Kokoro exception:", e)
        return None, str(e)

def generate_reflective_script_mp3(text_content, output_mp3_path, narrator_voice="am_adam", dialogue_voice="af_sarah"):
    raw_lines = text_content.split('\n')
    paragraphs = []
    current_para = []
    for line in raw_lines:
        if line.strip():
            current_para.append(line.strip())
        else:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
    if current_para:
        paragraphs.append(" ".join(current_para))

    if not paragraphs:
        return None, "No valid text found to generate speech."

    combined_audio = AudioSegment.silent(duration=100)
    temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], "temp_reflective")
    os.makedirs(temp_dir, exist_ok=True)

    errors = []

    try:
        all_segments = []
        for para_index, paragraph in enumerate(paragraphs):
            para_segments = segment_paragraph(paragraph)
            if not any(s['is_dialogue'] for s in para_segments):
                sentences = split_into_sentences(paragraph)
                para_segments = [{'text': s, 'is_dialogue': False} for s in sentences]

            for seg_idx, seg in enumerate(para_segments):
                clean_txt = clean_line(seg['text'])
                if not clean_txt:
                    continue
                    
                voice = dialogue_voice if seg['is_dialogue'] else narrator_voice
                temp_seg_path = os.path.join(temp_dir, f"seg_{len(all_segments)}.mp3")
                
                res_path, err = generate_mp3_with_kokoro_tts(clean_txt, temp_seg_path, voice=voice)
                if err or not res_path or not os.path.exists(res_path):
                    errors.append(f"Segment '{clean_txt[:20]}...': {err or 'File not created'}")
                    continue

                seg_audio = AudioSegment.from_mp3(res_path)
                all_segments.append({
                    'audio': seg_audio,
                    'text': clean_txt,
                    'dialogue': seg['is_dialogue'],
                    'para_end': (seg_idx == len(para_segments) - 1)
                })

        if not all_segments:
            err_msg = "Failed to generate audio segments from Kokoro TTS service."
            if errors:
                err_msg += " Details: " + "; ".join(errors[:3])
            return None, err_msg

        for i, seg in enumerate(all_segments):
            combined_audio += seg['audio']

            if i < len(all_segments) - 1:
                prev_sentence = seg['text']
                prev_dialogue = seg['dialogue']
                next_dialogue = all_segments[i+1]['dialogue']

                pause_sec = calculate_pause(prev_sentence, prev_dialogue)
                pause_sec += calculate_comma_pauses(prev_sentence)
                pause_sec = min(pause_sec, 3.0)

                if prev_dialogue and not next_dialogue:
                    pause_sec = NARRATOR_RETURN_PAUSE

                if seg['para_end']:
                    pause_sec = max(pause_sec, PARAGRAPH_PAUSE)

                silence_ms = int(pause_sec * 1000)
                combined_audio += AudioSegment.silent(duration=silence_ms)

        combined_audio += AudioSegment.silent(duration=300)
        combined_audio.export(output_mp3_path, format="mp3")

        shutil.rmtree(temp_dir, ignore_errors=True)
        return output_mp3_path, None

    except Exception as e:
        ic("Reflective script exception:", e)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None, str(e)

@app.route('/audio/<filename>')
def serve_audio_file(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        mimetype="audio/mpeg",
        conditional=True
    )

@app.route("/text_to_mp3", methods=["GET", "POST"])
def text_to_mp3():
    mp3_file = None
    text = ""
    mode = "regular"
    selected_voice = "am_echo"
    narrator_voice = "am_adam"
    dialogue_voice = "af_sarah"
    generation_info = None

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        mode = request.form.get("mode", "regular")
        selected_voice = request.form.get("voice", "am_echo")
        narrator_voice = request.form.get("narrator_voice", "am_adam")
        dialogue_voice = request.form.get("dialogue_voice", "af_sarah")

        if not text:
            flash("Please enter script text.")
            return redirect(url_for("text_to_mp3"))

        safe = "_".join(text[:20].split())
        safe = re.sub(r'[^a-zA-Z0-9_]', '', safe)
        if not safe:
            safe = "tts_output"

        mp3_file = f"{safe}_{int(time.time())}.mp3"
        mp3_path = os.path.join(OUTPUT_FOLDER, mp3_file)

        if mode == "reflective":
            result, error = generate_reflective_script_mp3(
                text, mp3_path, narrator_voice=narrator_voice, dialogue_voice=dialogue_voice
            )
            generation_info = f"Reflective Script mode (Narrator: {narrator_voice}, Dialogue: {dialogue_voice})"
        else:
            result, error = generate_mp3_with_kokoro_tts(text, mp3_path, voice=selected_voice)
            generation_info = f"Regular TTS mode (Voice: {selected_voice})"

        if error:
            flash(error)
            mp3_file = None

    return render_template(
        'html_mp3.html', 
        mp3_file=mp3_file, 
        text=text, 
        mode=mode,
        selected_voice=selected_voice,
        narrator_voice=narrator_voice,
        dialogue_voice=dialogue_voice,
        voices=TTS_voices,
        generation_info=generation_info
    )

# --------------------------------------------------
# COMIC BOOK PAGE BUILDER MODULE (INTEGRATED)
# --------------------------------------------------
@app.route('/comic')
@app.route('/comic_builder')
def comic_builder():
    return render_template_string(COMIC_BUILDER_INDEX)

@app.route('/uploadz', methods=['POST'])
def uploadz():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'url': f'/static/uploads/{filename}'}), 200

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/save-page', methods=['POST'])
def save_page():
    data = request.get_json() or {}
    image_data = data.get('image')

    if not image_data:
        return jsonify({'error': 'No image data'}), 400

    header, encoded = image_data.split(',', 1)
    import base64
    image_bytes = base64.b64decode(encoded)

    filename = f"comic-page-{uuid.uuid4().hex}.png"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    return jsonify({'url': f'/static/uploads/{filename}', 'filename': filename}), 200


COMIC_BUILDER_INDEX="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comic Book Page Builder</title>
    <!-- Konva.js (Offline Local) -->
    <script src="/static/js/konva.min.js"></script>
    <!-- Pickr Color Picker (Offline Local) -->
    <link rel="stylesheet" href="/static/css/classic.min.css">
    <script src="/static/js/pickr.min.js"></script>
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Bangers&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <!-- Custom CSS -->
    <style>/* ===== Reset & Base ===== */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Roboto', sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    min-height: 100vh;
    color: #e0e0e0;
}

/* ===== App Container ===== */
.app-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* ===== Header ===== */
.app-header {
    text-align: center;
    margin-bottom: 20px;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.app-header h1 {
    font-family: 'Bangers', cursive;
    font-size: 3rem;
    color: #ff6b6b;
    text-shadow: 3px 3px 0px #c0392b, 6px 6px 0px rgba(0,0,0,0.3);
    letter-spacing: 2px;
    margin-bottom: 8px;
}

.app-header p {
    color: #a0a0c0;
    font-size: 1rem;
}

/* ===== Toolbar ===== */
.toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    margin-bottom: 20px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    align-items: flex-start;
}

.tool-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 140px;
}

.tool-group label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #8888aa;
    font-weight: 700;
}

.tool-group select,
.tool-group input[type="number"] {
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(0, 0, 0, 0.3);
    color: #e0e0e0;
    font-size: 0.9rem;
    outline: none;
    transition: border-color 0.2s;
}

.tool-group select:focus,
.tool-group input[type="number"]:focus {
    border-color: #ff6b6b;
}

.tool-group input[type="file"] {
    display: none;
}

/* Custom Size */
.custom-size {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 4px;
}

.custom-size input {
    width: 70px;
    padding: 6px;
}

.custom-size span {
    color: #8888aa;
}

.hidden {
    display: none !important;
}

/* ===== Buttons ===== */
.btn {
    padding: 8px 14px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.btn:active {
    transform: translateY(0);
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #e0e0e0;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.2);
}

.btn-success {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: white;
}

.btn-danger {
    background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
    color: white;
}

.btn-warning {
    background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
    color: #1a1a2e;
}

.btn-info {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
}

.layer-buttons,
.action-buttons,
.export-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

/* ===== Canvas Wrapper ===== */
.canvas-wrapper {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 600px;
    padding: 30px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: auto;
}

#canvas-container {
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    border-radius: 4px;
    overflow: hidden;
    background: #ffffff;
    transition: width 0.3s, height 0.3s;
}

/* ===== Info Panel ===== */
.info-panel {
    display: flex;
    gap: 24px;
    padding: 12px 20px;
    margin-top: 16px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    justify-content: center;
    flex-wrap: wrap;
}

.info-item {
    display: flex;
    gap: 6px;
    align-items: center;
}

.info-label {
    color: #8888aa;
    font-size: 0.85rem;
}

.info-item span:last-child {
    color: #ff6b6b;
    font-weight: 700;
    font-family: 'Bangers', cursive;
    letter-spacing: 1px;
}

/* ===== Status Message ===== */
.status-message {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 14px 24px;
    border-radius: 10px;
    font-weight: 500;
    animation: slideIn 0.3s ease;
    z-index: 1000;
    backdrop-filter: blur(10px);
}

.status-message.success {
    background: rgba(17, 153, 142, 0.9);
    color: white;
}

.status-message.error {
    background: rgba(235, 51, 73, 0.9);
    color: white;
}

.status-message.info {
    background: rgba(79, 172, 254, 0.9);
    color: white;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* ===== Pickr Customization ===== */
.pcr-button {
    width: 36px !important;
    height: 36px !important;
    border-radius: 8px !important;
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
    .app-header h1 {
        font-size: 2rem;
    }

    .toolbar {
        flex-direction: column;
    }

    .tool-group {
        width: 100%;
    }

    .layer-buttons,
    .action-buttons,
    .export-buttons {
        flex-wrap: wrap;
    }
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
}

/* ===== Border Controls ===== */
.border-controls {
    display: flex;
    gap: 6px;
    align-items: center;
}

.border-controls input[type="number"] {
    width: 60px;
    padding: 6px;
}

.border-controls input[type="color"] {
    width: 36px;
    height: 34px;
    padding: 2px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(0, 0, 0, 0.3);
    cursor: pointer;
}

/* ===== Saved Color Palette Swatches ===== */
.palette-swatches-container {
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
    max-width: 220px;
}

.swatch-pill {
    width: 26px;
    height: 26px;
    border-radius: 6px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    cursor: pointer;
    transition: transform 0.15s, border-color 0.15s;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
}

.swatch-pill:hover {
    transform: scale(1.15);
    border-color: #ff6b6b;
}

.add-swatch-btn {
    width: 26px;
    height: 26px;
    border-radius: 6px;
    border: 1px dashed rgba(255, 255, 255, 0.4);
    background: rgba(255, 255, 255, 0.05);
    color: #ff6b6b;
    font-weight: bold;
    font-size: 0.9rem;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
}

.add-swatch-btn:hover {
    background: rgba(255, 255, 255, 0.15);
}

/* ===== Modal Backdrop & Dialog ===== */
.modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(5px);
    z-index: 2000;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
}

.modal-content {
    background: #1a1a2e;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 16px;
    width: 100%;
    max-width: 550px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
}

.modal-header h3 {
    color: #ff6b6b;
    font-family: 'Bangers', cursive;
    font-size: 1.5rem;
    letter-spacing: 1px;
}

.close-btn {
    background: transparent;
    border: none;
    color: #a0a0c0;
    font-size: 1.8rem;
    cursor: pointer;
    line-height: 1;
}

.close-btn:hover {
    color: #ffffff;
}

.modal-body {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.crop-preview-container {
    display: flex;
    justify-content: center;
    align-items: center;
    background: #0d0d1a;
    border-radius: 10px;
    padding: 16px;
    max-height: 280px;
    overflow: hidden;
}

#crop-box-wrapper {
    position: relative;
    display: inline-block;
    max-width: 100%;
    max-height: 240px;
}

#crop-target-img {
    max-width: 100%;
    max-height: 240px;
    display: block;
    object-fit: contain;
    border-radius: 4px;
}

#crop-overlay {
    position: absolute;
    border: 2px dashed #ff6b6b;
    box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.65);
    pointer-events: none;
}

.crop-controls-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.crop-control-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.crop-control-item label {
    font-size: 0.75rem;
    color: #8888aa;
    text-transform: uppercase;
    font-weight: 700;
}

.crop-control-item input[type="range"] {
    accent-color: #ff6b6b;
    cursor: pointer;
}

.crop-control-item span {
    font-size: 0.8rem;
/* ===== Custom Fonts ===== */
@font-face { font-family: 'Lato-Bold'; src: url('/static/fonts/Lato-Bold.ttf'); }
@font-face { font-family: 'Lato-Black'; src: url('/static/fonts/Lato-Black.ttf'); }
@font-face { font-family: 'Quicksand-Bold'; src: url('/static/fonts/Quicksand-Bold.ttf'); }
@font-face { font-family: 'DejaVuSans-Bold'; src: url('/static/fonts/DejaVuSans-Bold.ttf'); }

.btn-toggle-transparent {
    background: rgba(255, 255, 255, 0.1);
    color: #4facfe;
    border: 1px solid #4facfe;
    padding: 4px 8px;
    font-size: 0.75rem;
    border-radius: 6px;
    cursor: pointer;
    margin-top: 4px;
}

.text-control-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.text-control-group input[type="text"] {
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.2);
    background: rgba(0,0,0,0.3);
    color: white;
    font-size: 0.85rem;
}

.modal-footer {
    padding: 14px 20px;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
}
</style>
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="app-header" style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>💥 Comic Book Page Builder</h1>
                <p>Drag, resize, and layer your comic panels!</p>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <a href="/" class="btn btn-secondary" style="text-decoration: none; padding: 8px 14px; font-weight: 700; border-radius: 8px; color: white;">🏠 Home</a>
                <button id="btn-toggle-model" onclick="toggleModelLoadStatus()" 
                        style="padding: 10px 20px; font-weight: 700; border-radius: 8px; border: none; color: white; cursor: pointer; transition: all 0.2s; font-family: inherit; font-size: 0.95rem; background: linear-gradient(135deg, #10b981 0%, #059669 100%); box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);">
                    🟢 Load/Unload models
                </button>
            </div>
        </header>

        <!-- Toolbar -->
        <div class="toolbar">
            <!-- Page Size Selector -->
            <div class="tool-group">
                <label for="page-size">Page Size</label>
                <select id="page-size">
                    <option value="512x768" selected>Comic Book (512×768)</option>
                    <option value="720x1280">📱 Vertical YouTube Shorts (720×1280)</option>
                    <option value="600x900">Manga (600×900)</option>
                    <option value="768x1024">Tablet (768×1024)</option>
                    <option value="800x1200">Large (800×1200)</option>
                    <option value="1024x768">Landscape (1024×768)</option>
                    <option value="custom">Custom...</option>
                </select>
                <div id="custom-size" class="custom-size hidden">
                    <input type="number" id="custom-width" placeholder="Width" min="100" max="2000" value="512">
                    <span>×</span>
                    <input type="number" id="custom-height" placeholder="Height" min="100" max="2000" value="768">
                    <button id="apply-custom">Apply</button>
                </div>
            </div>

            <!-- View Zoom Level -->
            <div class="tool-group">
                <label for="zoom-level">Zoom View</label>
                <select id="zoom-level" onchange="setCanvasZoom(this.value)">
                    <option value="auto" selected>🔍 Auto Fit Screen</option>
                    <option value="100">100% Full Resolution</option>
                    <option value="75">75% Zoom</option>
                    <option value="50">50% Medium</option>
                    <option value="35">35% Compact</option>
                </select>
            </div>

            <!-- Background Color -->
            <div class="tool-group">
                <label>Background</label>
                <div id="color-picker"></div>
                <button id="btn-transparent-bg" class="btn-toggle-transparent" onclick="toggleTransparentBg()">✨ Transparent Canvas</button>
            </div>

            <!-- Saved Color Palette -->
            <div class="tool-group">
                <label>Project Palette</label>
                <div id="palette-swatches" class="palette-swatches-container"></div>
            </div>

            <!-- Image Upload -->
            <div class="tool-group">
                <label for="image-upload">Add Image</label>
                <input type="file" id="image-upload" accept="image/*" multiple>
                <button id="upload-btn" class="btn btn-primary">📁 Upload</button>
            </div>

            <!-- Typography & Text Overlay -->
            <div class="tool-group">
                <label>Add Text / Title Overlay</label>
                <div class="text-control-group">
                    <input type="text" id="overlay-text-input" placeholder="e.g. ISSUE #1: COVER">
                    <div style="display: flex; gap: 4px;">
                        <select id="overlay-font-family" style="flex-grow: 1;">
                            <option value="Bangers">Bangers (Comic Title)</option>
                            <option value="Lato-Black">Lato Black</option>
                            <option value="Lato-Bold">Lato Bold</option>
                            <option value="Quicksand-Bold">Quicksand Bold</option>
                            <option value="DejaVuSans-Bold">DejaVu Sans Bold</option>
                            <option value="Impact">Impact</option>
                            <option value="Arial">Arial</option>
                        </select>
                        <input type="number" id="overlay-font-size" value="48" min="12" max="200" style="width: 55px;" title="Font Size (px)">
                    </div>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        <label style="font-size: 0.75rem;">Color:</label>
                        <input type="color" id="overlay-text-color" value="#ffffff" title="Text Color">
                        <label style="font-size: 0.75rem;">Outline:</label>
                        <input type="color" id="overlay-text-stroke" value="#000000" title="Outline Color">
                        <button onclick="addTextOverlay()" class="btn btn-primary" style="padding: 4px 8px; font-size: 0.8rem; flex-grow: 1;">➕ Add Text</button>
                    </div>
                </div>
            </div>

            <!-- Border Style Controls -->
            <div class="tool-group">
                <label>Border Style</label>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                        <label style="font-size: 0.75rem; color: #a0a0c0; min-width: 80px;">Border Width:</label>
                        <input type="range" id="border-width-range" min="0" max="30" value="0" style="flex: 1;" oninput="syncBorderWidth(this.value)">
                        <input type="number" id="border-width" min="0" max="30" value="0" style="width: 45px; padding: 3px; font-size: 0.8rem;" oninput="syncBorderWidth(this.value)">
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                        <label style="font-size: 0.75rem; color: #a0a0c0; min-width: 80px;">Border Color:</label>
                        <input type="color" id="border-color" value="#000000" style="flex: 1; height: 26px; padding: 1px; border-radius: 4px; cursor: pointer;">
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                        <label style="font-size: 0.75rem; color: #a0a0c0; min-width: 80px;">Corner Radius:</label>
                        <input type="range" id="border-radius-range" min="0" max="250" value="0" style="flex: 1;" oninput="syncBorderRadius(this.value)">
                        <input type="number" id="border-radius" min="0" max="250" value="0" style="width: 45px; padding: 3px; font-size: 0.8rem;" oninput="syncBorderRadius(this.value)">
                    </div>
                </div>
            </div>

            <!-- Panel Shape & Aspect Ratio -->
            <div class="tool-group">
                <label>Panel Shape & Aspect Ratio</label>
                <select id="panel-shape-select" onchange="changePanelShape(this.value)">
                    <option value="rectangle" selected>⬜ Rectangle</option>
                    <option value="circle">⭕ Circle</option>
                    <option value="ellipse">🥚 Ellipse / Oval</option>
                </select>
                <label style="display: flex; align-items: center; gap: 6px; font-size: 0.8rem; margin-top: 6px; cursor: pointer; color: #e0e0e0;">
                    <input type="checkbox" id="toggle-keep-ratio" onchange="toggleKeepRatio(this.checked)">
                    🔒 Lock Aspect Ratio (8 Handles)
                </label>
            </div>

            <!-- Crop Image -->
            <div class="tool-group">
                <label>Crop Image</label>
                <button id="open-crop-btn" class="btn btn-secondary">✂️ Crop</button>
            </div>

            <!-- Layer Controls -->
            <div class="tool-group">
                <label>Layer Order</label>
                <div class="layer-buttons">
                    <button id="move-top" class="btn btn-secondary" title="Bring to Front">⬆️ Front</button>
                    <button id="move-up" class="btn btn-secondary" title="Move Up">↑ Up</button>
                    <button id="move-down" class="btn btn-secondary" title="Move Down">↓ Down</button>
                    <button id="move-bottom" class="btn btn-secondary" title="Send to Back">⬇️ Back</button>
                </div>
            </div>

            <!-- Actions -->
            <div class="tool-group">
                <label>Actions</label>
                <div class="action-buttons">
                    <button id="clear-all" class="btn btn-danger">🗑️ Clear All</button>
                    <button id="delete-selected" class="btn btn-warning">❌ Delete</button>
                </div>
            </div>

            <!-- Export -->
            <div class="tool-group">
                <label>Export</label>
                <div class="export-buttons">
                    <button id="download-png" class="btn btn-success">💾 Download PNG</button>
                    <button id="save-server" class="btn btn-info">☁️ Save to Server</button>
                    <button id="export-transparent-overlay" onclick="exportTransparentOverlay()" class="btn btn-primary" style="background: linear-gradient(135deg, #00c6ff, #0072ff);">✨ Export Transparent PNG</button>
                </div>
            </div>
        </div>

        <!-- Canvas Area -->
        <div class="canvas-wrapper">
            <div id="canvas-container"></div>
        </div>

        <!-- Info Panel -->
        <div class="info-panel">
            <div class="info-item">
                <span class="info-label">Images:</span>
                <span id="image-count">0</span>
            </div>
            <div class="info-item">
                <span class="info-label">Selected:</span>
                <span id="selected-info">None</span>
            </div>
            <div class="info-item">
                <span class="info-label">Canvas:</span>
                <span id="canvas-dims">512 × 768</span>
            </div>
        </div>

        <!-- Status Message -->
        <div id="status-message" class="status-message hidden"></div>
    </div>

    <!-- Crop Modal -->
    <div id="crop-modal" class="modal-backdrop hidden">
        <div class="modal-content">
            <div class="modal-header">
                <h3>✂️ Crop Image</h3>
                <button id="close-crop-modal" class="close-btn">&times;</button>
            </div>
            <div class="modal-body">
                <div class="crop-preview-container">
                    <div id="crop-box-wrapper">
                        <img id="crop-target-img" src="" alt="Crop target">
                        <div id="crop-overlay"></div>
                    </div>
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="font-weight: 600; font-size: 0.85rem; margin-bottom: 4px; display: block;">Crop Shape</label>
                    <div style="display: flex; gap: 8px;">
                        <button type="button" id="crop-shape-rect" class="btn btn-secondary btn-sm" onclick="setCropModalShape('rectangle')" style="flex: 1;">⬜ Rectangle</button>
                        <button type="button" id="crop-shape-circle" class="btn btn-secondary btn-sm" onclick="setCropModalShape('circle')" style="flex: 1;">⭕ Circle</button>
                        <button type="button" id="crop-shape-ellipse" class="btn btn-secondary btn-sm" onclick="setCropModalShape('ellipse')" style="flex: 1;">🥚 Ellipse</button>
                    </div>
                </div>

                <div class="crop-controls-grid">
                    <div class="crop-control-item">
                        <label for="crop-top">Top Crop</label>
                        <input type="range" id="crop-top" min="0" max="45" value="0">
                        <span id="crop-top-val">0%</span>
                    </div>
                    <div class="crop-control-item">
                        <label for="crop-bottom">Bottom Crop</label>
                        <input type="range" id="crop-bottom" min="0" max="45" value="0">
                        <span id="crop-bottom-val">0%</span>
                    </div>
                    <div class="crop-control-item">
                        <label for="crop-left">Left Crop</label>
                        <input type="range" id="crop-left" min="0" max="45" value="0">
                        <span id="crop-left-val">0%</span>
                    </div>
                    <div class="crop-control-item">
                        <label for="crop-right">Right Crop</label>
                        <input type="range" id="crop-right" min="0" max="45" value="0">
                        <span id="crop-right-val">0%</span>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button id="reset-crop-btn" class="btn btn-secondary">🔄 Reset</button>
                <button id="cancel-crop-btn" class="btn btn-secondary">Cancel</button>
                <button id="apply-crop-btn" class="btn btn-success">✅ Apply Crop</button>
            </div>
        </div>
    </div>

    <!-- Hidden file input trigger -->
    <script>
        document.getElementById('upload-btn').addEventListener('click', () => {
            document.getElementById('image-upload').click();
        });
    </script>

<script>
let stage, layer, backgroundRect;
let selectedNode = null;
let transformer = null;
let imageCount = 0;

// Page size presets
const PAGE_SIZES = {
    '512x768': { width: 512, height: 768 },
    '600x900': { width: 600, height: 900 },
    '768x1024': { width: 768, height: 1024 },
    '800x1200': { width: 800, height: 1200 },
    '1024x768': { width: 1024, height: 768 }
};

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    initStage();
    initPickr();
    initEventListeners();
    initKeyboardShortcuts();
});

// ===== Stage Setup =====
function initStage() {
    const container = document.getElementById('canvas-container');
    const initialSize = PAGE_SIZES['512x768'];

    stage = new Konva.Stage({
        container: 'canvas-container',
        width: initialSize.width,
        height: initialSize.height
    });

    layer = new Konva.Layer();
    stage.add(layer);

    // Background rectangle (the "page")
    backgroundRect = new Konva.Rect({
        x: 0,
        y: 0,
        width: initialSize.width,
        height: initialSize.height,
        fill: '#ffffff',
        name: 'background'
    });
    layer.add(backgroundRect);

    // Transformer for resizing (8 handles)
    transformer = new Konva.Transformer({
        keepRatio: false,
        enabledAnchors: ['top-left', 'top-center', 'top-right', 'middle-left', 'middle-right', 'bottom-left', 'bottom-center', 'bottom-right'],
        borderStroke: '#ff6b6b',
        borderStrokeWidth: 2,
        anchorStroke: '#ff6b6b',
        anchorFill: '#ffffff',
        anchorSize: 10
    });
    layer.add(transformer);

    // Click on empty space deselects
    stage.on('click tap', (e) => {
        if (e.target === stage || e.target === backgroundRect) {
            deselectAll();
        }
    });

    updateCanvasDims();
}

let pickrInstance = null;
let projectPalette = JSON.parse(localStorage.getItem('comic_project_palette')) || [
    '#ffffff', '#000000', '#ff6b6b', '#10b981', '#4facfe', '#ffd200', '#8b5cf6'
];

function saveProjectPalette() {
    localStorage.setItem('comic_project_palette', JSON.stringify(projectPalette));
    renderPaletteSwatches();
}

function renderPaletteSwatches() {
    const container = document.getElementById('palette-swatches');
    if (!container) return;

    let html = '';
    projectPalette.forEach((hex) => {
        html += `<div class="swatch-pill" style="background: ${hex};" title="Click to apply ${hex}" onclick="applyPaletteColor('${hex}')"></div>`;
    });
    html += `<div class="add-swatch-btn" title="Add background color to palette" onclick="addCurrentColorToPalette()">+</div>`;
    container.innerHTML = html;
}

function applyPaletteColor(colorHex) {
    if (selectedNode && selectedNode.className === 'Image') {
        selectedNode.stroke(colorHex);
        selectedNode.strokeScaleEnabled(false);
        document.getElementById('border-color').value = colorHex;
        layer.draw();
        showStatus(`Applied ${colorHex} to panel border`, 'info');
    } else {
        backgroundRect.fill(colorHex);
        layer.draw();
        if (pickrInstance) pickrInstance.setColor(colorHex);
        showStatus(`Applied ${colorHex} to page background`, 'info');
    }
}

let isTransparentBg = false;

function toggleTransparentBg() {
    isTransparentBg = !isTransparentBg;
    if (isTransparentBg) {
        backgroundRect.fill(null);
        showStatus('Canvas set to Transparent Background', 'info');
    } else {
        backgroundRect.fill('#ffffff');
        showStatus('Canvas set to White Background', 'info');
    }
    layer.draw();
}

function addTextOverlay() {
    const textVal = document.getElementById('overlay-text-input').value.trim() || 'NEW COVER TITLE';
    const fontFamily = document.getElementById('overlay-font-family').value;
    const fontSize = parseInt(document.getElementById('overlay-font-size').value) || 48;
    const textColor = document.getElementById('overlay-text-color').value;
    const strokeColor = document.getElementById('overlay-text-stroke').value;

    const textNode = new Konva.Text({
        x: stage.width() / 2 - 100,
        y: stage.height() / 2 - 25,
        text: textVal,
        fontSize: fontSize,
        fontFamily: fontFamily,
        fill: textColor,
        stroke: strokeColor,
        strokeWidth: 2,
        draggable: true,
        padding: 10
    });

    layer.add(textNode);
    layer.draw();
    selectNode(textNode);
    showStatus(`Added text overlay: "${textVal}"`, 'success');
}

async function exportTransparentOverlay() {
    const wasSelected = selectedNode;
    deselectAll();

    const originalFill = backgroundRect.fill();
    backgroundRect.fill(null);
    layer.draw();

    setTimeout(async () => {
        const dataURL = stage.toDataURL({ pixelRatio: 2, mimeType: 'image/png' });
        
        // Download directly
        const link = document.createElement('a');
        link.download = `transparent-overlay-${Date.now()}.png`;
        link.href = dataURL;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Also save to server
        try {
            const activeProject = new URLSearchParams(window.location.search).get('project');
            await fetch('/save-page', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: dataURL, project: activeProject })
            });
            showStatus('Exported & Saved Transparent PNG Overlay!', 'success');
        } catch (err) {
            console.error(err);
        }

        // Restore fill
        backgroundRect.fill(originalFill);
        layer.draw();
        if (wasSelected) selectNode(wasSelected);
    }, 100);
}

// ===== Pickr Color Picker =====
function initPickr() {
    pickrInstance = Pickr.create({
        el: '#color-picker',
        theme: 'classic',
        default: '#ffffff',
        swatches: projectPalette,
        components: {
            preview: true,
            opacity: true,
            hue: true,
            interaction: {
                hex: true,
                rgba: true,
                hsla: true,
                input: true,
                save: true
            }
        }
    });

    pickrInstance.on('change', (color) => {
        const hex = color.toHEXA().toString();
        backgroundRect.fill(hex);
        layer.draw();
    });

    pickrInstance.on('save', (color) => {
        if (!color) return;
        const hex = color.toHEXA().toString();
        if (!projectPalette.includes(hex)) {
            projectPalette.push(hex);
            saveProjectPalette();
            showStatus(`Added ${hex} to project palette`, 'success');
        }
    });

    renderPaletteSwatches();
}

// ===== Event Listeners =====
function initEventListeners() {
    // Page size selector
    const pageSizeSelect = document.getElementById('page-size');
    const customSizeDiv = document.getElementById('custom-size');

    pageSizeSelect.addEventListener('change', (e) => {
        const value = e.target.value;

        if (value === 'custom') {
            customSizeDiv.classList.remove('hidden');
        } else {
            customSizeDiv.classList.add('hidden');
            const size = PAGE_SIZES[value];
            if (size) {
                resizeStage(size.width, size.height);
            }
        }
    });

    // Apply custom size
    document.getElementById('apply-custom').addEventListener('click', () => {
        const width = parseInt(document.getElementById('custom-width').value);
        const height = parseInt(document.getElementById('custom-height').value);

        if (width >= 100 && width <= 2000 && height >= 100 && height <= 2000) {
            resizeStage(width, height);
        } else {
            showStatus('Please enter dimensions between 100 and 2000', 'error');
        }
    });

    // Image upload
    const imageUpload = document.getElementById('image-upload');
    imageUpload.addEventListener('change', handleImageUpload);

    // Layer controls
    document.getElementById('move-top').addEventListener('click', () => moveLayer('top'));
    document.getElementById('move-up').addEventListener('click', () => moveLayer('up'));
    document.getElementById('move-down').addEventListener('click', () => moveLayer('down'));
    document.getElementById('move-bottom').addEventListener('click', () => moveLayer('bottom'));

    // Actions
    document.getElementById('clear-all').addEventListener('click', clearAllImages);
    document.getElementById('delete-selected').addEventListener('click', deleteSelected);

    // Export
    document.getElementById('download-png').addEventListener('click', downloadPNG);
    document.getElementById('save-server').addEventListener('click', saveToServer);

    // Border controls
    document.getElementById('border-color').addEventListener('input', (e) => {
        if (!selectedNode || selectedNode.className !== 'Image') return;
        selectedNode.stroke(e.target.value);
        selectedNode.strokeScaleEnabled(false);
        layer.draw();
    });

    // Crop Modal Listeners
    document.getElementById('open-crop-btn').addEventListener('click', openCropModal);
    document.getElementById('close-crop-modal').addEventListener('click', closeCropModal);
    document.getElementById('cancel-crop-btn').addEventListener('click', closeCropModal);
    document.getElementById('apply-crop-btn').addEventListener('click', applyCrop);
    document.getElementById('reset-crop-btn').addEventListener('click', resetCrop);

    ['crop-top', 'crop-bottom', 'crop-left', 'crop-right'].forEach(id => {
        document.getElementById(id).addEventListener('input', updateCropOverlay);
    });

    checkModelStatus();
}

async function checkModelStatus() {
    try {
        const res = await fetch('/api/model_status');
        const data = await res.json();
        updateModelButtonUI(data.loaded, data.model_name);
    } catch(e) {
        console.error("Error checking model status:", e);
    }
}

async function toggleModelLoadStatus() {
    const btn = document.getElementById('btn-toggle-model');
    if (btn) {
        btn.disabled = true;
        btn.textContent = "⏳ Processing...";
    }
    try {
        const res = await fetch('/api/toggle_model', { method: 'POST' });
        const data = await res.json();
        updateModelButtonUI(data.loaded, data.model_name);
        showStatus(data.message || (data.loaded ? "Models loaded!" : "Models unloaded!"), data.loaded ? "info" : "warning");
    } catch(e) {
        showStatus("Error toggling model state", "error");
    } finally {
        if (btn) btn.disabled = false;
    }
}

function updateModelButtonUI(isLoaded, modelName) {
    const btn = document.getElementById('btn-toggle-model');
    if (!btn) return;
    if (isLoaded) {
        btn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        btn.style.boxShadow = '0 4px 15px rgba(16, 185, 129, 0.4)';
        btn.textContent = '🟢 Load/Unload models';
        btn.title = `Model loaded in memory: ${modelName || 'Active'}. Click to unload & free memory.`;
    } else {
        btn.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        btn.style.boxShadow = '0 4px 15px rgba(239, 68, 68, 0.4)';
        btn.textContent = '🔴 Load/Unload models';
        btn.title = 'Model unloaded (Memory freed for TTS/Video). Click to reload model.';
    }
}

// ===== Keyboard Shortcuts =====
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            // Don't delete if typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            deleteSelected();
        }

        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'a') {
                e.preventDefault();
                // Select all images
                const images = layer.find('Image');
                if (images.length > 0) {
                    transformer.nodes(images);
                    selectedNode = images[images.length - 1];
                    updateSelectedInfo();
                    layer.draw();
                }
            }
        }
    });
}

function setCanvasZoom(val) {
    const container = document.getElementById('canvas-container');
    if (!container || typeof stage === 'undefined' || !stage) return;
    const zoomSelect = document.getElementById('zoom-level');
    const currentVal = val || (zoomSelect ? zoomSelect.value : 'auto');

    if (currentVal === 'auto') {
        const availableH = Math.max(350, window.innerHeight - 280);
        const stageH = stage.height();
        if (stageH > availableH) {
            const scale = availableH / stageH;
            container.style.transform = `scale(${scale})`;
            container.style.transformOrigin = 'top center';
            container.style.marginBottom = `-${(1 - scale) * stageH}px`;
        } else {
            container.style.transform = 'none';
            container.style.marginBottom = '0';
        }
    } else {
        const scale = parseFloat(currentVal) / 100;
        if (scale === 1) {
            container.style.transform = 'none';
            container.style.marginBottom = '0';
        } else {
            container.style.transform = `scale(${scale})`;
            container.style.transformOrigin = 'top center';
            const stageH = stage.height();
            container.style.marginBottom = `-${(1 - scale) * stageH}px`;
        }
    }
}

window.addEventListener('resize', () => {
    const zoomSelect = document.getElementById('zoom-level');
    if (zoomSelect && zoomSelect.value === 'auto') {
        setCanvasZoom('auto');
    }
});

// ===== Resize Stage =====
function resizeStage(width, height) {
    stage.width(width);
    stage.height(height);

    backgroundRect.width(width);
    backgroundRect.height(height);

    // Update container CSS
    const container = document.getElementById('canvas-container');
    container.style.width = width + 'px';
    container.style.height = height + 'px';

    setCanvasZoom();
    layer.draw();
    updateCanvasDims();
    showStatus(`Canvas resized to ${width}×${height}`, 'success');
}

// ===== Image Upload =====
async function handleImageUpload(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    for (const file of files) {
        const formData = new FormData();
        formData.append('image', file);

        try {
            showStatus(`Uploading ${file.name}...`, 'info');

            const response = await fetch('/uploadz', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                addImageToCanvas(data.url);
                showStatus(`${file.name} uploaded successfully!`, 'success');
            } else {
                showStatus(data.error || 'Upload failed', 'error');
            }
        } catch (err) {
            showStatus('Network error during upload', 'error');
            console.error(err);
        }
    }

    // Reset input
    e.target.value = '';
}

// ===== Add Image to Canvas =====
function addImageToCanvas(src) {
    Konva.Image.fromURL(src, (img) => {
        // Set initial position (centered with slight offset for stacking)
        const offset = (imageCount % 5) * 20;
        const centerX = (stage.width() - img.width()) / 2 + offset;
        const centerY = (stage.height() - img.height()) / 2 + offset;

        img.setAttrs({
            x: centerX,
            y: centerY,
            draggable: true,
            name: 'image-' + imageCount
        });

        // Scale down if image is larger than canvas
        const scaleX = stage.width() / img.width();
        const scaleY = stage.height() / img.height();
        const scale = Math.min(scaleX, scaleY, 1) * 0.8;

        if (scale < 1) {
            img.scale({ x: scale, y: scale });
        }

        // Enable border scale independence & default border
        img.strokeScaleEnabled(false);

        // Add click handler for selection
        img.on('click tap', (e) => {
            e.cancelBubble = true;
            selectNode(img);
        });

        // Add hover effect
        img.on('mouseenter', () => {
            document.body.style.cursor = 'move';
        });
        img.on('mouseleave', () => {
            document.body.style.cursor = 'default';
        });

        // Insert before transformer so transformer stays on top
        img.moveToTop();
        transformer.moveToTop();

        layer.add(img);
        layer.draw();

        imageCount++;
        updateImageCount();

        // Auto-select the new image
        selectNode(img);
    });
}

function syncBorderWidth(val) {
    const numVal = parseInt(val) || 0;
    const wInput = document.getElementById('border-width');
    const wRange = document.getElementById('border-width-range');
    if (wInput) wInput.value = numVal;
    if (wRange) wRange.value = numVal;

    if (selectedNode && selectedNode.className === 'Image') {
        selectedNode.strokeWidth(numVal);
        selectedNode.strokeScaleEnabled(false);
        layer.draw();
    }
}

function syncBorderRadius(val) {
    const numVal = parseInt(val) || 0;
    const rInput = document.getElementById('border-radius');
    const rRange = document.getElementById('border-radius-range');
    if (rInput) rInput.value = numVal;
    if (rRange) rRange.value = numVal;

    if (selectedNode && selectedNode.className === 'Image') {
        selectedNode.cornerRadius(numVal);
        layer.draw();
    }
}

function changePanelShape(shapeType) {
    if (!selectedNode || selectedNode.className !== 'Image') {
        showStatus('Please select an image panel first', 'error');
        return;
    }

    selectedNode.setAttr('panelShape', shapeType);
    selectedNode.sceneFunc(null);
    selectedNode.clipFunc(null);

    if (shapeType === 'circle') {
        const curW = selectedNode.width();
        const curH = selectedNode.height();
        const circleSize = Math.min(curW, curH);
        selectedNode.width(circleSize);
        selectedNode.height(circleSize);

        const radius = circleSize / 2;
        selectedNode.cornerRadius(radius);

        const radiusInput = document.getElementById('border-radius');
        if (radiusInput) radiusInput.value = Math.round(radius);

        showStatus('Applied Circle Panel shape (Corner Radius 50%)', 'info');
    } else if (shapeType === 'ellipse') {
        const radius = Math.min(selectedNode.width(), selectedNode.height()) / 2;
        selectedNode.cornerRadius(radius);

        const radiusInput = document.getElementById('border-radius');
        if (radiusInput) radiusInput.value = Math.round(radius);

        showStatus('Applied Ellipse / Oval Panel shape', 'info');
    } else {
        selectedNode.cornerRadius(0);

        const radiusInput = document.getElementById('border-radius');
        if (radiusInput) radiusInput.value = 0;

        showStatus('Applied Rectangle Panel shape', 'info');
    }

    layer.draw();
}

function toggleKeepRatio(keepRatio) {
    if (transformer) {
        transformer.keepRatio(keepRatio);
        layer.draw();
        showStatus(keepRatio ? 'Aspect Ratio Locked (1:1 Proportional Scale)' : 'Aspect Ratio Unlocked (Free 8-Handle Stretch)', 'info');
    }
}
function selectNode(node) {
    deselectAll();
    selectedNode = node;
    transformer.nodes([node]);

    const shapeSelect = document.getElementById('panel-shape-select');
    if (shapeSelect && node.className === 'Image') {
        shapeSelect.value = node.getAttr('panelShape') || 'rectangle';
    }

    layer.draw();
    updateSelectedInfo();

    if (node && node.className === 'Image') {
        syncBorderWidth(node.strokeWidth() || 0);
        syncBorderRadius(node.cornerRadius() || 0);
        const colInput = document.getElementById('border-color');
        if (colInput) colInput.value = node.stroke() || '#000000';
    }
}

function deselectAll() {
    selectedNode = null;
    transformer.nodes([]);
    layer.draw();
    updateSelectedInfo();

    syncBorderWidth(0);
    syncBorderRadius(0);
    const colInput = document.getElementById('border-color');
    if (colInput) colInput.value = '#000000';
}

// ===== Layer Ordering =====
function moveLayer(direction) {
    if (!selectedNode) {
        showStatus('No image selected', 'error');
        return;
    }

    switch (direction) {
        case 'top':
            selectedNode.moveToTop();
            break;
        case 'up':
            selectedNode.moveUp();
            break;
        case 'down':
            selectedNode.moveDown();
            break;
        case 'bottom':
            selectedNode.moveToBottom();
            // Keep background at the very bottom
            backgroundRect.moveToBottom();
            break;
    }

    // Keep transformer on top
    transformer.moveToTop();
    layer.draw();

    showStatus(`Moved ${direction}`, 'success');
}

// ===== Delete =====
function deleteSelected() {
    if (!selectedNode) {
        showStatus('No image selected', 'error');
        return;
    }

    selectedNode.destroy();
    transformer.nodes([]);
    selectedNode = null;
    layer.draw();

    imageCount = Math.max(0, imageCount - 1);
    updateImageCount();
    updateSelectedInfo();
    showStatus('Image deleted', 'success');
}

function clearAllImages() {
    const images = layer.find('Image');
    images.forEach(img => img.destroy());

    transformer.nodes([]);
    selectedNode = null;
    layer.draw();

    imageCount = 0;
    updateImageCount();
    updateSelectedInfo();
    showStatus('All images cleared', 'success');
}

// ===== Export =====
function downloadPNG() {
    // Deselect before export for clean image
    const wasSelected = selectedNode;
    deselectAll();

    setTimeout(() => {
        const dataURL = stage.toDataURL({
            pixelRatio: 2, // High quality export
            mimeType: 'image/png'
        });

        const link = document.createElement('a');
        link.download = `comic-page-${Date.now()}.png`;
        link.href = dataURL;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showStatus('Page downloaded!', 'success');

        // Restore selection
        if (wasSelected) {
            selectNode(wasSelected);
        }
    }, 100);
}

async function saveToServer() {
    // Deselect before export
    const wasSelected = selectedNode;
    deselectAll();

    setTimeout(async () => {
        const dataURL = stage.toDataURL({
            pixelRatio: 2,
            mimeType: 'image/png'
        });

        try {
            showStatus('Saving to server...', 'info');

            const response = await fetch('/save-page', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: dataURL })
            });

            const data = await response.json();

            if (response.ok) {
                showStatus(`Saved as ${data.filename}`, 'success');
            } else {
                showStatus(data.error || 'Save failed', 'error');
            }
        } catch (err) {
            showStatus('Network error during save', 'error');
            console.error(err);
        }

        // Restore selection
        if (wasSelected) {
            selectNode(wasSelected);
        }
    }, 100);
}

// ===== UI Updates =====
function updateImageCount() {
    document.getElementById('image-count').textContent = imageCount;
}

function updateSelectedInfo() {
    const info = document.getElementById('selected-info');
    if (selectedNode) {
        const name = selectedNode.name() || 'Image';
        const x = Math.round(selectedNode.x());
        const y = Math.round(selectedNode.y());
        info.textContent = `${name} at (${x}, ${y})`;
    } else {
        info.textContent = 'None';
    }
}

function updateCanvasDims() {
    document.getElementById('canvas-dims').textContent = `${stage.width()} × ${stage.height()}`;
}

// ===== Status Messages =====
function showStatus(message, type) {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;

    setTimeout(() => {
        statusEl.classList.add('hidden');
    }, 3000);

    // Remove hidden immediately to show
    statusEl.classList.remove('hidden');
}

// ===== Crop Modal Logic =====
function getValidCropDimensions(node) {
    const nativeImg = node.image();
    const natW = (nativeImg && nativeImg.naturalWidth && nativeImg.naturalWidth > 0) 
        ? nativeImg.naturalWidth 
        : (node.width() || 500);
    const natH = (nativeImg && nativeImg.naturalHeight && nativeImg.naturalHeight > 0) 
        ? nativeImg.naturalHeight 
        : (node.height() || 500);
    return { natW, natH };
}

let selectedCropModalShape = 'rectangle';

function setCropModalShape(shape) {
    selectedCropModalShape = shape;
    ['rect', 'circle', 'ellipse'].forEach(s => {
        const btn = document.getElementById('crop-shape-' + s);
        if (btn) {
            if (s === shape || (s === 'rect' && shape === 'rectangle')) {
                btn.style.background = 'var(--accent-primary)';
                btn.style.color = '#fff';
            } else {
                btn.style.background = '';
                btn.style.color = '';
            }
        }
    });
    updateCropOverlay();
}

function openCropModal() {
    if (!selectedNode || selectedNode.className !== 'Image') {
        showStatus('Please select an image to crop', 'error');
        return;
    }

    const nativeImg = selectedNode.image();
    if (!nativeImg || !nativeImg.src) {
        showStatus('Image source not available', 'error');
        return;
    }

    const targetImg = document.getElementById('crop-target-img');

    const savedCrop = selectedNode.getAttr('cropPct') || { top: 0, bottom: 0, left: 0, right: 0 };
    document.getElementById('crop-top').value = savedCrop.top;
    document.getElementById('crop-bottom').value = savedCrop.bottom;
    document.getElementById('crop-left').value = savedCrop.left;
    document.getElementById('crop-right').value = savedCrop.right;

    const currentPanelShape = selectedNode.getAttr('panelShape') || 'rectangle';
    setCropModalShape(currentPanelShape);

    document.getElementById('crop-modal').classList.remove('hidden');

    targetImg.onload = () => {
        updateCropOverlay();
    };
    targetImg.src = nativeImg.src;
    updateCropOverlay();
}

function closeCropModal() {
    document.getElementById('crop-modal').classList.add('hidden');
}

function updateCropOverlay() {
    const top = parseInt(document.getElementById('crop-top').value) || 0;
    const bottom = parseInt(document.getElementById('crop-bottom').value) || 0;
    const left = parseInt(document.getElementById('crop-left').value) || 0;
    const right = parseInt(document.getElementById('crop-right').value) || 0;

    document.getElementById('crop-top-val').textContent = `${top}%`;
    document.getElementById('crop-bottom-val').textContent = `${bottom}%`;
    document.getElementById('crop-left-val').textContent = `${left}%`;
    document.getElementById('crop-right-val').textContent = `${right}%`;

    const targetImg = document.getElementById('crop-target-img');
    const overlay = document.getElementById('crop-overlay');

    if (!targetImg.offsetWidth || !targetImg.offsetHeight) return;

    const imgW = targetImg.offsetWidth;
    const imgH = targetImg.offsetHeight;

    const overlayLeft = (left / 100) * imgW;
    const overlayTop = (top / 100) * imgH;
    const overlayWidth = imgW * (1 - (left + right) / 100);
    const overlayHeight = imgH * (1 - (top + bottom) / 100);

    overlay.style.left = `${overlayLeft}px`;
    overlay.style.top = `${overlayTop}px`;
    overlay.style.width = `${Math.max(0, overlayWidth)}px`;
    overlay.style.height = `${Math.max(0, overlayHeight)}px`;

    if (selectedCropModalShape === 'circle' || selectedCropModalShape === 'ellipse') {
        overlay.style.borderRadius = '50%';
    } else {
        overlay.style.borderRadius = '0px';
    }
}

function applyCrop() {
    if (!selectedNode || selectedNode.className !== 'Image') return;

    const nativeImg = selectedNode.image();
    if (!nativeImg) {
        showStatus('Image source missing', 'error');
        return;
    }

    const { natW, natH } = getValidCropDimensions(selectedNode);

    const topPct = Math.min(45, Math.max(0, parseInt(document.getElementById('crop-top').value) || 0));
    const bottomPct = Math.min(45, Math.max(0, parseInt(document.getElementById('crop-bottom').value) || 0));
    const leftPct = Math.min(45, Math.max(0, parseInt(document.getElementById('crop-left').value) || 0));
    const rightPct = Math.min(45, Math.max(0, parseInt(document.getElementById('crop-right').value) || 0));

    const cropX = Math.round((leftPct / 100) * natW);
    const cropY = Math.round((topPct / 100) * natH);
    const cropW = Math.round(natW * (1 - (leftPct + rightPct) / 100));
    const cropH = Math.round(natH * (1 - (topPct + bottomPct) / 100));

    if (cropW <= 0 || cropH <= 0) {
        showStatus('Invalid crop area', 'error');
        return;
    }

    const shape = selectedCropModalShape || 'rectangle';

    // Build 32-bit RGBA PNG Canvas
    const offCanvas = document.createElement('canvas');
    let outW = cropW;
    let outH = cropH;

    if (shape === 'circle') {
        const circleSize = Math.min(cropW, cropH);
        outW = circleSize;
        outH = circleSize;
    }

    offCanvas.width = outW;
    offCanvas.height = outH;
    const ctx = offCanvas.getContext('2d');
    ctx.clearRect(0, 0, outW, outH);

    if (shape === 'circle') {
        ctx.beginPath();
        ctx.arc(outW / 2, outH / 2, outW / 2, 0, Math.PI * 2, false);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(nativeImg, cropX, cropY, cropW, cropH, 0, 0, outW, outH);
    } else if (shape === 'ellipse') {
        ctx.beginPath();
        ctx.ellipse(outW / 2, outH / 2, outW / 2, outH / 2, 0, 0, Math.PI * 2, false);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(nativeImg, cropX, cropY, cropW, cropH, 0, 0, outW, outH);
    } else {
        ctx.drawImage(nativeImg, cropX, cropY, cropW, cropH, 0, 0, outW, outH);
    }

    const rgbaDataUrl = offCanvas.toDataURL('image/png');

    const croppedImgEl = new Image();
    croppedImgEl.onload = () => {
        const curScaleX = selectedNode.scaleX() || 1;
        const curScaleY = selectedNode.scaleY() || 1;
        const curDisplayW = (selectedNode.width() || natW) * curScaleX;
        const curDisplayH = (selectedNode.height() || natH) * curScaleY;

        let displayW = Math.max(10, Math.round(outW * (curDisplayW / natW)));
        let displayH = Math.max(10, Math.round(outH * (curDisplayH / natH)));

        if (shape === 'circle') {
            const size = Math.min(displayW, displayH);
            displayW = size;
            displayH = size;
        }

        selectedNode.image(croppedImgEl);
        selectedNode.crop({ x: 0, y: 0, width: outW, height: outH });
        selectedNode.clipFunc(null);
        selectedNode.scaleX(1);
        selectedNode.scaleY(1);
        selectedNode.width(displayW);
        selectedNode.height(displayH);
        selectedNode.setAttr('panelShape', shape);
        selectedNode.setAttr('cropPct', { top: topPct, bottom: bottomPct, left: leftPct, right: rightPct });

        const shapeSelect = document.getElementById('panel-shape-select');
        if (shapeSelect) shapeSelect.value = shape;

        layer.draw();
        if (transformer) transformer.forceUpdate();

        closeCropModal();
        showStatus('Image cropped to RGBA shape successfully!', 'success');
    };
    croppedImgEl.src = rgbaDataUrl;
}

function resetCrop() {
    if (!selectedNode || selectedNode.className !== 'Image') return;

    const { natW, natH } = getValidCropDimensions(selectedNode);

    const curScaleX = selectedNode.scaleX() || 1;
    const curScaleY = selectedNode.scaleY() || 1;
    const curDisplayW = (selectedNode.width() || natW) * curScaleX;
    const curDisplayH = (selectedNode.height() || natH) * curScaleY;

    const existingCrop = selectedNode.crop();
    const prevCropW = (existingCrop && existingCrop.width > 0) ? existingCrop.width : natW;
    const prevCropH = (existingCrop && existingCrop.height > 0) ? existingCrop.height : natH;

    let ratioW = curDisplayW / prevCropW;
    let ratioH = curDisplayH / prevCropH;

    if (!isFinite(ratioW) || ratioW <= 0) ratioW = 1;
    if (!isFinite(ratioH) || ratioH <= 0) ratioH = 1;

    const newDisplayW = Math.max(10, Math.round(natW * ratioW));
    const newDisplayH = Math.max(10, Math.round(natH * ratioH));

    selectedNode.crop({
        x: 0,
        y: 0,
        width: natW,
        height: natH
    });

    selectedNode.scaleX(1);
    selectedNode.scaleY(1);
    selectedNode.width(newDisplayW);
    selectedNode.height(newDisplayH);

    selectedNode.setAttr('cropPct', { top: 0, bottom: 0, left: 0, right: 0 });

    layer.draw();
    if (transformer) transformer.forceUpdate();

    closeCropModal();
    showStatus('Crop reset to full image', 'success');
}
</script>
</body>
</html>
"""

# --------------------------------------------------
# SERVER ENTRY POINT
# --------------------------------------------------
if __name__ == '__main__':
    def exit_gracefully(signum, frame):
        print("\n[*] Ctrl+C / termination signal received. Shutting down server...")
        os._exit(0)
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    
    parser = argparse.ArgumentParser(description="ZoomPan & Comic Studio App v3 Server")
    parser.add_argument("--model", default="/home/jack/Desktop/Comfy-UI/models/checkpoints/comiccraftLCM_beta4.safetensors", help="Path to .safetensors model")
    parser.add_argument("--lora", type=str, default=None, help="Path to LoRA file")
    parser.add_argument("--lora_scale", type=float, default=0.15, help="LoRA scale")
    parser.add_argument("--device", type=str, default="auto", help="Device: auto, cuda, mps, cpu")
    parser.add_argument("--port", type=int, default=5000, help="Flask port")
    args = parser.parse_args()
    
    initial_model = args.model
    checkpoints_found = get_available_checkpoints()
    if not os.path.exists(initial_model) and checkpoints_found:
        initial_model = os.path.join(CHECKPOINT_DIR, checkpoints_found[0])

    print("[*] Server starting in Lazy Model Mode (Model unloaded).")
    print("[*] Stable Diffusion model will only load on demand when requested.")

    app.run(host='0.0.0.0', port=args.port, debug=False)
