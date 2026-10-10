import os
import json
import time
import math
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory

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

def render_frame(img, center_x, center_y, zoom, out_w, out_h, label=None, render_labels=False, point_num=None):
    img_h, img_w, _ = img.shape
    
    # Calculate target viewport width and height in original image coordinates
    crop_w = img_w / zoom
    crop_h = img_h / zoom
    
    # Maintain output aspect ratio
    target_aspect = out_w / out_h
    current_aspect = crop_w / crop_h
    
    if current_aspect > target_aspect:
        crop_h = crop_w / target_aspect
    else:
        crop_w = crop_h * target_aspect
        
    # Bound top-left corner
    left = center_x - crop_w / 2.0
    top = center_y - crop_h / 2.0
    
    # Clamp bounds while preserving size where possible
    left = max(0, min(left, img_w - crop_w))
    top = max(0, min(top, img_h - crop_h))
    
    right = left + crop_w
    bottom = top + crop_h
    
    # Map coordinates to integers for slicing or sub-pixel warp
    # Use cv2.getRectSubPix or cv2.warpAffine for sub-pixel accuracy
    src_pts = np.float32([[left, top], [right, top], [left, bottom]])
    dst_pts = np.float32([[0, 0], [out_w, 0], [0, out_h]])
    M = cv2.getAffineTransform(src_pts, dst_pts)
    
    frame = cv2.warpAffine(img, M, (out_w, out_h), flags=cv2.INTER_CUBIC)
    
    if render_labels and label:
        # Calculate screen coordinates of the point on the rendered frame
        # (center_x, center_y) mapped by transform M
        pt_screen = M @ np.array([center_x, center_y, 1.0])
        px, py = int(pt_screen[0]), int(pt_screen[1])
        
        # Draw glowing marker & text box
        cv2.circle(frame, (px, py), 12, (0, 220, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (px, py), 16, (255, 255, 255), 2, lineType=cv2.LINE_AA)
        
        display_text = f"#{point_num}: {label}" if point_num else label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        (text_w, text_h), baseline = cv2.getTextSize(display_text, font, font_scale, thickness)
        
        box_x = max(10, px - text_w // 2 - 10)
        box_y = max(10, py - 30 - text_h)
        
        # Draw semi-transparent background box for label
        overlay = frame.copy()
        cv2.rectangle(overlay, (box_x, box_y), (box_x + text_w + 20, box_y + text_h + 16), (20, 24, 33), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(frame, (box_x, box_y), (box_x + text_w + 20, box_y + text_h + 16), (0, 220, 255), 1)
        
        cv2.putText(frame, display_text, (box_x + 10, box_y + text_h + 6), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        
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
    
    # Start keyframe: Full image view
    start_kf = {
        'x': img_w / 2.0,
        'y': img_h / 2.0,
        'zoom': 1.0,
        'label': 'Overview',
        'transition_duration': 1.5,
        'hold_duration': 1.0
    }
    keyframes.append(start_kf)
    
    for idx, p in enumerate(points):
        keyframes.append({
            'num': idx + 1,
            'x': float(p['x']),
            'y': float(p['y']),
            'zoom': float(p.get('zoom', 2.5)),
            'label': p.get('label', f'Point {idx+1}'),
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
                
                # Interpolate parameters
                curr_x = prev_kf['x'] + (curr_kf['x'] - prev_kf['x']) * ease_t
                curr_y = prev_kf['y'] + (curr_kf['y'] - prev_kf['y']) * ease_t
                curr_zoom = prev_kf['zoom'] + (curr_kf['zoom'] - prev_kf['zoom']) * ease_t
                
                active_label = curr_kf['label'] if (ease_t > 0.5 and 'num' in curr_kf) else (prev_kf['label'] if 'num' in prev_kf else None)
                active_num = curr_kf.get('num') if (ease_t > 0.5) else prev_kf.get('num')
                
                frame = render_frame(
                    img, curr_x, curr_y, curr_zoom, out_w, out_h,
                    label=active_label, render_labels=render_labels, point_num=active_num
                )
                out.write(frame)
                total_frames_rendered += 1

        # Hold on current keyframe
        hold_sec = curr_kf['hold_duration']
        num_hold_frames = max(1, int(hold_sec * fps))
        
        hold_frame = render_frame(
            img, curr_kf['x'], curr_kf['y'], curr_kf['zoom'], out_w, out_h,
            label=curr_kf.get('label'), render_labels=render_labels, point_num=curr_kf.get('num')
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

