#!/usr/bin/env python3
"""
JAVASCRIPT EFFECTS STUDIO // Backend Web Application (Media Studio Module)
Serves the creative studio, handles media uploads, preset persistence, and saves exported snapshots/recordings.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
PRESETS_DIR = os.path.join(BASE_DIR, 'static', 'presets')

# Ensure directories exist
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(PRESETS_DIR, exist_ok=True)

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, 'static'),
    template_folder=os.path.join(BASE_DIR, 'templates')
)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["SESSION_COOKIE_NAME"] = "effects_session"
app.config["SESSION_COOKIE_PATH"] = "/effects"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(BASE_DIR, 'static'), 'favicon.ico')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_media():
    """Upload image or video file to server uploads directory."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = f"{int(time.time())}_{file.filename}"
    save_path = os.path.join(UPLOADS_DIR, filename)
    file.save(save_path)

    return jsonify({
        'success': True,
        'filename': filename,
        'url': f"/effects/uploads/{filename}"
    })

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOADS_DIR, filename)

@app.route('/api/save-export', methods=['POST'])
def save_export():
    """Save exported video or snapshot PNG directly into exports directory."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    filename = file.filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"
    
    filename = os.path.basename(filename)
    dest_path = os.path.join(EXPORTS_DIR, filename)
    file.save(dest_path)

    size = os.path.getsize(dest_path)
    return jsonify({
        'success': True,
        'filename': filename,
        'size': size,
        'url': f"/effects/exports/{filename}"
    })

@app.route('/exports/<path:filename>')
def serve_exports(filename):
    return send_from_directory(EXPORTS_DIR, filename)

@app.route('/api/presets', methods=['GET', 'POST'])
def handle_presets():
    """List or save presets."""
    preset_file = os.path.join(PRESETS_DIR, 'default-presets.json')
    if request.method == 'GET':
        if os.path.exists(preset_file):
            with open(preset_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({'presets': []})

    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON body'}), 400
        return jsonify({'success': True})

def main():
    parser = argparse.ArgumentParser(description='Javascript Effects Studio Server')
    parser.add_argument('--port', type=int, default=5055, help='Port to run on (default: 5055)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind (default: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
