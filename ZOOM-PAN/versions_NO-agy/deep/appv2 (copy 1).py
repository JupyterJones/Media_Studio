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
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['EXPORT_FOLDER'] = os.path.join(app.root_path, 'static', 'exports')
app.config['PROJECT_FOLDER'] = os.path.join(app.root_path, 'static', 'projects')
app.config['VIDEO_FOLDER'] = os.path.join(app.root_path, 'static', 'videos')
app.config['ASSET_FOLDER'] = os.path.join(app.root_path, 'static', 'assets')
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max upload

CHECKPOINT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Comfy-UI", "models", "checkpoints")
LORA_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Comfy-UI", "models", "loras")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}

for folder in [app.config['UPLOAD_FOLDER'], app.config['EXPORT_FOLDER'], 
               app.config['PROJECT_FOLDER'], app.config['VIDEO_FOLDER'], 
               app.config['ASSET_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

IMAGE_FOLDER = app.config['UPLOAD_FOLDER']
AUDIO_FOLDER = app.config['UPLOAD_FOLDER']
OUTPUT_FOLDER = app.config['UPLOAD_FOLDER']
FRAME_PATH = os.path.join(app.config['ASSET_FOLDER'], 'ZOOMPAN.png')
TARGET_SIZE = (512, 768)

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
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{int(time.time())}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        img = cv2.imread(filepath)
        if img is None:
            return jsonify({'error': 'Could not read uploaded image'}), 400
        h, w, _ = img.shape
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/static/uploads/{filename}',
            'width': w,
            'height': h
        })
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
    line_h = max(sz[1] for sz in line_sizes) if line_sizes else 20
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
    img_h, img_w, _ = img.shape
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
    upload_dir = app.config['UPLOAD_FOLDER']
    audio_files = []
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                audio_files.append(f)
    return jsonify({'audio_files': sorted(audio_files)})

@app.route('/api/audio_info/<filename>', methods=['GET'])
def api_audio_info(filename):
    safe_name = secure_filename(filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    if not os.path.exists(audio_path):
        return jsonify({'error': 'Audio file not found'}), 404
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
    return render_template(
        'generation.html',
        history=runs,
        model_path=current_model_path,
        current_model_name=current_model_name,
        current_lora_name=current_lora_name,
        device=current_device,
        checkpoints=checkpoints,
        loras=loras
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
        'current_lora_scale': current_lora_scale
    })

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
    if not os.path.exists(IMAGE_FOLDER):
        return
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for filename in image_files:
        image_path = os.path.join(IMAGE_FOLDER, filename)
        try:
            with Image.open(image_path) as img:
                if img.size != TARGET_SIZE:
                    resized_img = img.resize(TARGET_SIZE, Image.LANCZOS)
                    resized_img.save(image_path)
        except Exception as e:
            ic(f"Error processing {filename}: {e}")

@app.route('/sequenced_video')
def sequenced_video():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg','.jpeg','.png'))]
    mp3s = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.mp3')]
    mp4s = [f for f in os.listdir(app.config['VIDEO_FOLDER']) if f.lower().endswith('.mp4')]    
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
        r = requests.post(KOKORO_TTS_URL, json=payload, timeout=60)
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

    try:
        all_segments = []
        for para_index, paragraph in enumerate(paragraphs):
            sentences = split_into_sentences(paragraph)
            for sentence in sentences:
                dialogue = is_dialogue(sentence)
                clean_txt = clean_line(sentence)
                voice = dialogue_voice if dialogue else narrator_voice
                
                temp_seg_path = os.path.join(temp_dir, f"seg_{len(all_segments)}.mp3")
                res_path, err = generate_mp3_with_kokoro_tts(clean_txt, temp_seg_path, voice=voice)
                if err or not res_path or not os.path.exists(res_path):
                    continue

                seg_audio = AudioSegment.from_mp3(res_path)
                all_segments.append({
                    'audio': seg_audio,
                    'text': clean_txt,
                    'dialogue': dialogue,
                    'para_end': False
                })

            if all_segments:
                all_segments[-1]['para_end'] = True

        if not all_segments:
            return None, "Failed to generate audio segments from Kokoro TTS service."

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
# SERVER ENTRY POINT
# --------------------------------------------------
if __name__ == '__main__':
    def exit_gracefully(signum, frame):
        print("\n[*] Ctrl+C / termination signal received. Shutting down server...")
        os._exit(0)
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    
    parser = argparse.ArgumentParser(description="ZoomPan Studio Server")
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

    if os.path.exists(initial_model):
        load_pipeline(initial_model, args.device)
        if args.lora:
            lora_p = args.lora
            if not os.path.isabs(lora_p):
                lora_p = os.path.join(LORA_DIR, lora_p)
            apply_lora(lora_p, args.lora_scale)
    else:
        print(f"[!] Note: Model checkpoint '{initial_model}' not found. Select a model via UI when generating.")

    app.run(host='0.0.0.0', port=args.port, debug=False)
