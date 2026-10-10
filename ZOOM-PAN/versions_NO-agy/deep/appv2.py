import os
import json
import time
import math
import cv2
import inspect
import numpy as np
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory
from random import randint
import os
import json
import argparse
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler, LCMScheduler
from flask import Flask, render_template_string, request, redirect, send_file, session, render_template_string, Response, flash, url_for
import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image
from pydub import AudioSegment
from icecream import ic
from werkzeug.utils import secure_filename
from random import randint
import signal
import re
import inspect

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['EXPORT_FOLDER'] = os.path.join(app.root_path, 'static', 'exports')
app.config['PROJECT_FOLDER'] = os.path.join(app.root_path, 'static', 'projects')
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}
for folder in [app.config['UPLOAD_FOLDER'], app.config['EXPORT_FOLDER'], app.config['PROJECT_FOLDER']]:
    os.makedirs(folder, exist_ok=True)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def UID():
    rid=str(randint(1111111,9999999))
    return rid
# Define the log file path
LOG_FILE_PATH = "static/app_log.txt"

# Ensure the log file exists or create it
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, "w"):
        pass  # Create an empty log file if it doesn't exist

def logit(*args):
    """
    Lightweight file-based logging utility for debugging and runtime diagnostics.
    Accepts ANY number of positional arguments and safely joins them into a
    single log message.

    Examples:
        logit("Hello world")
        logit("x:", x, "y:", y)
        logit("Paths:", image_paths)
        logit(["list", "of", "values"])
    """

    try:
        # --- timestamp ---
        timestr = datetime.now().strftime("%A_%b-%d-%Y_%H-%M-%S")

        # --- caller info ---
        frame = inspect.stack()[1]
        filename = frame.filename
        lineno = frame.lineno

        # --- normalize all inputs ---
        parts = []
        for arg in args:
            if isinstance(arg, (list, tuple, set)):
                parts.append(" ".join(map(str, arg)))
            else:
                parts.append(str(arg))

        message_str = " ".join(parts)

        # --- final log line ---
        log_message = f"{timestr} - File: {filename}, Line: {lineno}: {message_str}\n"

        # --- write log ---
        with open(LOG_FILE_PATH, "a") as f:
            f.write(log_message)

        # Optional console echo (leave commented if you want quiet logs)
        # print(log_message, end="")

    except Exception as e:
        print(f"[LOGIT ERROR] {e}")




@app.route('/')
def index():
    return render_template('index.html')
@app.route('/api/upload', methods=['POST'])
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        logit("line 104 no image")
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        logit(f"filename:{filename}")
        # Add timestamp to avoid cache collision
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{int(time.time())}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logit(f"filepath:{filepath}")
        # Get dimensions using OpenCV
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
    # Smoothstep easing (0 to 1)
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
    
    # Auto-wrap text into balanced lines
    lines = wrap_text_to_lines(text, max_chars=26)
    char_count = sum(len(l) for l in lines)
    
    # Dynamic font scaling based on text length & style
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
    
    # Bounding positioning on frame
    box_x = max(10, min(px - box_w // 2, frame.shape[1] - box_w - 10))
    box_y = max(10, py - box_h - 25)
    if box_y < 10:
        box_y = py + 25
        
    center_box_x = box_x + box_w // 2
    if bubble_style in ('speech', 'speech_left'):  # White Speech Bubble (Left Tail)
        tail_x = box_x + 20
        tail_pts = np.array([[tail_x - 10, box_y + box_h], [tail_x + 10, box_y + box_h], [px, py]], np.int32)
        cv2.fillPoly(frame, [tail_pts], (255, 255, 255), lineType=cv2.LINE_AA)
        cv2.polylines(frame, [tail_pts], True, (0, 0, 0), 2, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 2, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'speech_right':  # White Speech Bubble (Right Tail)
        tail_x = box_x + box_w - 20
        tail_pts = np.array([[tail_x - 10, box_y + box_h], [tail_x + 10, box_y + box_h], [px, py]], np.int32)
        cv2.fillPoly(frame, [tail_pts], (255, 255, 255), lineType=cv2.LINE_AA)
        cv2.polylines(frame, [tail_pts], True, (0, 0, 0), 2, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 2, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style in ('thought', 'thought_left'):  # Thought Bubble (Left Tail)
        t_x = box_x + 20
        cv2.circle(frame, (int(px * 0.6 + t_x * 0.4), int(py * 0.6 + (box_y + box_h) * 0.4)), 4, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.6 + t_x * 0.4), int(py * 0.6 + (box_y + box_h) * 0.4)), 4, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.2 + t_x * 0.8), int(py * 0.2 + (box_y + box_h) * 0.8)), 7, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.2 + t_x * 0.8), int(py * 0.2 + (box_y + box_h) * 0.8)), 7, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 2, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'thought_right':  # Thought Bubble (Right Tail)
        t_x = box_x + box_w - 20
        cv2.circle(frame, (int(px * 0.6 + t_x * 0.4), int(py * 0.6 + (box_y + box_h) * 0.4)), 4, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.6 + t_x * 0.4), int(py * 0.6 + (box_y + box_h) * 0.4)), 4, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.2 + t_x * 0.8), int(py * 0.2 + (box_y + box_h) * 0.8)), 7, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (int(px * 0.2 + t_x * 0.8), int(py * 0.2 + (box_y + box_h) * 0.8)), 7, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 2, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'idea':  # Light Bulb Idea Eureka Bubble
        bg_gold = (0, 229, 255) # Glowing Cyan Gold
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), bg_gold, 3, lineType=cv2.LINE_AA)
        # Draw small yellow light bulb icon dot above box
        cv2.circle(frame, (center_box_x, box_y - 8), 6, bg_gold, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (center_box_x, box_y - 8), 8, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)
    elif bubble_style == 'caption':  # Classic Yellow Narration Box
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (102, 240, 255), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), 3, lineType=cv2.LINE_AA)
        text_color = (0, 0, 0)

    elif bubble_style == 'sfx':  # Crimson Comic Action SFX
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (40, 50, 240), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), 2, lineType=cv2.LINE_AA)
        text_color = (255, 255, 255)
    elif bubble_style == 'manga':  # High-Contrast Manga Black Box
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (10, 10, 10), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), 3, lineType=cv2.LINE_AA)
        text_color = (255, 255, 255)
    elif bubble_style == 'noir':  # Vintage Parchment Box
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (194, 236, 244), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (19, 32, 45), 2, lineType=cv2.LINE_AA)
        text_color = (19, 32, 45)
    elif bubble_style == 'hero':  # Superhero Navy & Gold
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (138, 58, 30), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (11, 158, 245), 3, lineType=cv2.LINE_AA)
        text_color = (255, 255, 255)
    else:  # Cyber Neon Dark Glass
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (25, 20, 15), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 229, 0), 2, lineType=cv2.LINE_AA)
        text_color = (255, 255, 255)

    # Render Centered Lines
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
    
    # Calculate target viewport width and height in original image coordinates
    crop_w = img_w / zoom
    crop_h = img_h / zoom
    
    target_aspect = out_w / out_h
    current_aspect = crop_w / crop_h
    
    if current_aspect > target_aspect:
        crop_h = crop_w / target_aspect
    else:
        crop_w = crop_h * target_aspect
    # For subtle zoom levels (e.g. 1.05x to 1.5x), weight camera center smoothly towards image center
    # to prevent hard edge clamping from yanking view to corners
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
        
        # Map original point coordinates to current frame coordinates
        pt_screen = M @ np.array([pt_x, pt_y, 1.0])
        px, py = int(pt_screen[0]), int(pt_screen[1])
        
        # Render ONLY the comic bubble / text caption (No dot markers)
        label_text = point_obj.get('label', '')
        style = point_obj.get('bubble_style', 'speech')
        draw_comic_bubble(frame, px, py, label_text, bubble_style=style)
    UNUM=UID()
    cv2.imwrite(f"junk/{UNUM}junk.png",frame)    
    return frame

#@app.route('/api/generate_mp4', methods=['POST'])
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
    output_res = data.get('resolution', '1080p') # 1080p, 720p, or original
    
    if output_res == '1080p':
        out_w, out_h = 1920, 1080
    elif output_res == '720p':
        out_w, out_h = 1280, 720
    else:
        out_w, out_h = img_w, img_h
        
    # Ensure dimensions are even (required for H.264 / MP4 encoders)
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
    # Build sequence of keyframes
    keyframes = []
    
    # Start keyframe: Clean full image overview (No text bubble)
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
        # Explicit check for zoom_enabled: true or boolean true
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
            # NO CHECK = NO ZOOM: Stay at full image overview (zoom=1.0, centered)
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
        
    # Render video
    total_frames_rendered = 0
    
    for i in range(len(keyframes)):
        curr_kf = keyframes[i]
        
        # Transition from previous keyframe to current
        if i > 0:
            prev_kf = keyframes[i - 1]
            trans_sec = curr_kf['transition_duration']
            num_trans_frames = max(1, int(trans_sec * fps))
            
            for f in range(num_trans_frames):
                t = f / float(num_trans_frames)
                ease_t = cubic_easing(t)
                
                # Interpolate camera view center & zoom
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
        # Hold on current keyframe
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
    
    # Transcode using FFmpeg to H.264 (yuv420p) for 100% HTML5 browser playback
    try:
        import subprocess
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
        print(f"FFmpeg transcode warning: {e}")
        if os.path.exists(raw_path) and not os.path.exists(video_path):
            os.rename(raw_path, video_path)
    return jsonify({
        'success': True,
        'video_url': f'/static/exports/{video_filename}',
        'filename': video_filename,
        'total_frames': total_frames_rendered,
        'duration_seconds': round(total_frames_rendered / fps, 2)
    })
#Image Generation

# Global pipeline (loaded once at startup)
pipe = None
current_device = None
current_model_path = None

def get_device(preference="auto"):
    if preference == "auto":
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    return preference

def load_pipeline(model_path, device_pref="auto"):
    global pipe, current_device, current_model_path
    device = get_device(device_pref)
    current_device = device
    print(f"[*] Target generation device: {device.upper()}")
    if device == "cpu":
        print("[!] WARNING: Running on CPU will be extremely slow.")
    is_lcm = "lcm" in model_path.lower()
    print(f"[*] Detected model type: {'LCM' if is_lcm else 'Standard SD 1.5'}")
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"[*] Loading model from: {model_path}")
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
    print("[+] Pipeline ready.")
ic("I AM AT 586")
def apply_lora(lora_path, lora_scale=0.15):
    if lora_path and os.path.exists(lora_path):
        print(f"[*] Loading LoRA: {lora_path} (scale={lora_scale})")
        pipe.load_lora_weights(lora_path, adapter_name="custom_lora")
        pipe.fuse_lora(lora_scale=lora_scale)
    elif lora_path:
        print(f"[!] LoRA not found: {lora_path}")

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
    # Reverse so newest first
    runs = list(reversed(history.get("runs", [])))
    return render_template('generation.html', history=runs, model_path=current_model_path, device=current_device)

@app.route('/api/generate_image', methods=['POST','GET'])
def generate_image():
    if pipe is None:
        return jsonify({"error": "Model not loaded. Check server startup logs."}), 500
    data = request.get_json() or {}
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
    model_name = os.path.basename(current_model_path).replace(".", "_")
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
            "model": current_model_path
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
        "model_path": current_model_path
    })
#Sequenced Videos
from flask import Flask, render_template_string, request, redirect, send_file, session, Response, flash, url_for
import os
import uuid
import shutil
import subprocess
import requests
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image
from pydub import AudioSegment
from icecream import ic
from werkzeug.utils import secure_filename
from random import randint
IMAGE_FOLDER = 'static/uploads'
AUDIO_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/uploads'
FRAME_PATH = 'static/assets/ZOOMPAN.png'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
UNIQUE = str(randint(111111, 999999))
TARGET_SIZE = (512, 768)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
UNIQUE =str(randint(111111,999999))
TARGET_SIZE = (512, 768)
# Resize all images
def resize_all_images():
    ic("Starting image resizing...")
    if not os.path.exists(IMAGE_FOLDER):
        ic(f"Image folder not found: {IMAGE_FOLDER}")
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
resize_all_images()

#@app.route('/')
#def index():
@app.route('/sequenced_video')
def sequenced_video():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg','.jpeg','.png'))]
    mp3s = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.mp3')]
    mp4s = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.mp4')]    
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
    image_sequence = []
    for img in selected_images:
        seq_val = request.form.get(f"sequence_{img}")
        if not seq_val:
            return f"Missing sequence number for {img}", 400
        image_sequence.append((int(seq_val), img))
    sorted_images = [img for _, img in sorted(image_sequence, key=lambda x: x[0])]
    ic(sorted_images)
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
    video_filename = f"{UNIQUE}final_video.mp4"
    output_video_path = os.path.join(OUTPUT_FOLDER, video_filename)
    try:
        final_video.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24
        )
        return redirect(url_for("serve_video", filename=video_filename))
    except Exception as e:
        ic(e)
        return "Error creating video.", 500

@app.route('/video/<filename>')
def serve_video(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        mimetype='video/mp4',
        conditional=True
    )
# --------------------------------------------------
# IMAGE RESIZE
# --------------------------------------------------
def resize_all_images():
    ic("Starting image resizing...")
    if not os.path.exists(IMAGE_FOLDER):
        return
    for f in os.listdir(IMAGE_FOLDER):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            p = os.path.join(IMAGE_FOLDER, f)
            try:
                with Image.open(p) as img:
                    if img.size != TARGET_SIZE:
                        img.resize(TARGET_SIZE, Image.LANCZOS).save(p)
            except Exception as e:
                ic("Resize error:", e)
resize_all_images()
# --------------------------------------------------
# KOKORO TTS CONFIG
# --------------------------------------------------
TTS_voices=['af_alloy','af_aoede','af_bella','af_heart','af_jessica','af_kore',
'af_nicole','af_nova','af_river','af_sarah','af_sky','am_adam','am_echo','am_eric',
'am_fenrir','am_liam','am_michael','am_onyx','am_puck','am_santa','bf_alice','bf_emma',
'bf_isabella','bf_lily','bm_daniel','bm_fable','bm_george','bm_lewis','ef_dora',
'em_alex','em_santa','ff_siwis','hf_alpha','hf_beta','hm_omega','hm_psi','if_sara',
'im_nicola','jf_alpha','jf_gongitsune','jf_nezumi','jf_tebukuro','jm_kumo','pf_dora',
'pm_alex','pm_santa','zf_xiaobei','zf_xiaoni','zf_xiaoxiao','zf_xiaoyi']
KOKORO_TTS_URL = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE = "am_echo"
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
# --------------------------------------------------
# SERVE GENERATED MP3
# --------------------------------------------------
@app.route('/audio/<filename>')
def serve_file(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        mimetype="audio/mpeg",
        conditional=True
    )
@app.route("/text_to_mp3", methods=["GET", "POST"])
def text_to_mp3():
    mp3_file = None
    text = ""
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Enter text")
            return redirect(url_for("text_to_mp3"))
        safe = "_".join(text[:20].split())
        mp3_file = f"{safe}.mp3"
        mp3_path = os.path.join(OUTPUT_FOLDER, mp3_file)
        result, error = generate_mp3_with_kokoro_tts(text, mp3_path)
        if error:
            flash(error)
            mp3_file = None
    return render_template('html_mp3.html', mp3_file=mp3_file, text=text)

#Using Kokoro TTS with reflection
# ------------------------------------------------------------
# 🎛 PAUSE PROFILE — EASY TO TUNE
# ------------------------------------------------------------
COMMA_PAUSE = 0.5           # pause at comma
SENTENCE_PAUSE = 1.0        # end of normal sentence
QUESTION_PAUSE = 1.2        # end of question
PARAGRAPH_PAUSE = 1.75       # between paragraphs
SHORT_SENTENCE_THRESHOLD = 6
SHORT_SENTENCE_MULTIPLIER = 1.4
DRAMATIC_KEYWORDS = ["but", "however", "until", "except", "though", "suddenly", "then", "yet"]
DRAMATIC_MULTIPLIER = 1.2
DIALOGUE_SENTENCE_PAUSE = 0.95
NARRATOR_RETURN_PAUSE = 2.0  # after dialogue ends

# ------------------------------------------------------------
# 🎭 UTILITY FUNCTIONS
# ------------------------------------------------------------
def is_dialogue(line):
    s = line.strip()
    return (s.startswith('"') and s.endswith('"')) or (s.startswith('“') and s.endswith('”')) or (s.startswith("'") and s.endswith("'"))

def count_words(text):
    return len(text.strip().split())

def contains_dramatic_word(text):
    lower = text.lower()
    return any(word in lower for word in DRAMATIC_KEYWORDS)

def split_into_sentences(paragraph):
    # Split on sentence-ending punctuation (., ?, !) while keeping punctuation and any closing quotes
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
    # Remove leading bullets *, hyphens, and spaces
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

# ------------------------------------------------------------
# 🎬 REFLECTIVE SCRIPT GENERATION
# ------------------------------------------------------------
def generate_script(text_file):
    if not os.path.exists(text_file):
        print("File not found.")
        sys.exit(1)

    base_name = os.path.splitext(text_file)[0]
    script_name = base_name + ".sh"

    with open(text_file, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # Remove empty lines and preserve paragraphs
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

    ic("Total paragraphs:", len(paragraphs))

    script = []
    script.append("#!/bin/bash")
    script.append("# Auto-generated compassionate narrator script")
    script.append('echo "Generating narration..."')
    script.append("mkdir -p output")
    script.append("")

    seg_index = 1
    all_segments = []

    # --------------------------
    # 1️⃣ Generate sentence-level segments
    # --------------------------
    for para_index, paragraph in enumerate(paragraphs):
        sentences = split_into_sentences(paragraph)
        for sentence in sentences:
            dialogue = is_dialogue(sentence)
            clean_text = clean_line(sentence)
            script.append(f"echo {repr(clean_text)} > seg{seg_index}.txt")

            # Voice selection
            if dialogue:
                voice = "af_sarah"
                speed = "1.0"
            else:
                voice = "am_adam"
                speed = "0.95"

            # Generate wav
            script.append(f"echo 'Generating segment {seg_index}...'")
            script.append(
                f"kokoro-tts seg{seg_index}.txt seg{seg_index}.wav "
                f"--voice {voice} --speed {speed} --lang en-us"
            )
            script.append("sleep 0.5")
            all_segments.append((f"seg{seg_index}.wav", clean_text, dialogue))
            seg_index += 1

        # Paragraph pause
        if para_index < len(paragraphs) - 1:
            script.append(f"# Paragraph pause of {PARAGRAPH_PAUSE}s")
            script.append(f"python utils/add_silence_between.py seg{seg_index-1}.wav seg{seg_index-1}.wav temp_para{para_index}.wav --pause {PARAGRAPH_PAUSE}")
            script.append(f"mv temp_para{para_index}.wav seg{seg_index-1}.wav")
            script.append("sleep 0.1")

    # --------------------------
    # 2️⃣ Merge all segments sequentially
    # --------------------------
    script.append("echo 'Merging segments with pauses...'")
    merged_file = "output/story.wav"

    if len(all_segments) == 1:
        script.append(f"cp {all_segments[0][0]} {merged_file}")
    else:
        current_file = all_segments[0][0]
        for i in range(1, len(all_segments)):
            next_file = all_segments[i][0]
            prev_sentence, prev_dialogue = all_segments[i-1][1], all_segments[i-1][2]

            pause = calculate_pause(prev_sentence, prev_dialogue)
            pause += calculate_comma_pauses(prev_sentence)
            pause = min(pause, 3.0)

            if prev_dialogue and not all_segments[i][2]:
                pause = NARRATOR_RETURN_PAUSE

            temp_file = f"temp{i}.wav"
            script.append(
                f"python utils/add_silence_between.py {current_file} {next_file} {temp_file} --pause {pause}"
            )
            script.append("sleep 0.1")
            current_file = temp_file

        script.append(f"cp {current_file} {merged_file}")

    # --------------------------
    # 3️⃣ Cleanup
    # --------------------------
    script.append("rm seg*.txt seg*.wav temp*.wav || true")
    script.append('echo "Done: output/story.wav"')

    # --------------------------
    # 4️⃣ Create timestamped MP4
    # --------------------------
    script.append("")
    script.append('# Create final MP4 with timestamped filename')
    script.append('file="output/$(date +%Y-%m-%d_%H-%M-%S).mp3"')
    script.append('ffmpeg -i output/story.wav -y "$file"')
    script.append('echo "✅ Final video created: $file"')

    with open(script_name, "w", encoding="utf-8") as f:
        f.write("\n".join(script))

    os.chmod(script_name, 0o755)
    print(f"Generated: {script_name}")

# 🎬 END OF REFLECTIVE SCRIPT GENERATION


# --------------------------
#Add a frame to a video
# --------------------------
def add_title_image(video_path, hex_color="#f9f0b4"):
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
    title_image_path = "static/assets/ZOOMPAN.png"
    # Set the desired size of the padded video (e.g., video width + padding, video height + padding)
    padded_size = (width + 20, height + 20)

    # Calculate the position for centering the video within the larger frame
    x_position = (padded_size[0] - video_clip.size[0]) / 2
    y_position = (padded_size[1] - video_clip.size[1]) / 2
    # hex_color = "#09723c"
    # Remove the '#' and split the hex code into R, G, and B components
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Create an RGB tuple
    rgb_tuple = (240, 240, 180)

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
    output_path = 'temp/final_output3.mp4'
    # Export the final video with the background music
    composite_clip.write_videofile(output_path)
    uid = str(uuid.uuid4())  # Generate a unique ID using uuid
    mp4_file = f"/home/jack/Desktop/HDD500/DOCKER/static/results/Ready_Post_{uid}.mp4"
    shutil.copyfile(output_path, mp4_file)
    print(mp4_file)
    VIDEO = output_path
    return VIDEO


# add_title_image(video_path, hex_color="#f9f0b4")



if __name__ == '__main__':
    def exit_gracefully(signum, frame):
        print("\n[*] Ctrl+C / termination signal received. Shutting down Latent Horizon server instantly...")
        os._exit(0)
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    
    parser = argparse.ArgumentParser(description="Stable Diffusion Web GUI")
    parser.add_argument("--model", default="/home/jack/Desktop/Comfy-UI/models/checkpoints/comiccraftLCM_beta4.safetensors", help="Path to .safetensors model")
    parser.add_argument("--lora", type=str, default=None, help="Path to LoRA file")
    parser.add_argument("--lora_scale", type=float, default=0.15, help="LoRA scale")
    parser.add_argument("--device", type=str, default="auto", help="Device: auto, cuda, mps, cpu")
    parser.add_argument("--port", type=int, default=5000, help="Flask port")
    args = parser.parse_args()
    load_pipeline(args.model, args.device)
    if args.lora:
        apply_lora(args.lora, args.lora_scale)
    app.run(host='0.0.0.0', port=args.port, debug=False)
