import os
import json
import time
import math
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory
from random import randint
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid cache collision
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{int(time.time())}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)

