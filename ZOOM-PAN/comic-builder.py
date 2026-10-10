from flask import Flask, render_template_string, request, jsonify, send_from_directory
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template_string(INDEX)

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
    data = request.get_json()
    image_data = data.get('image')

    if not image_data:
        return jsonify({'error': 'No image data'}), 400

    # Remove data URL prefix
    header, encoded = image_data.split(',', 1)
    import base64
    image_bytes = base64.b64decode(encoded)

    filename = f"comic-page-{uuid.uuid4().hex}.png"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    return jsonify({'url': f'/static/uploads/{filename}', 'filename': filename}), 200

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
INDEX="""<!DOCTYPE html>
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
    max-width: 100%;
    margin: 0 auto;
    padding: 16px 24px;
}

/* ===== Header ===== */
.app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;
    padding: 12px 24px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 14px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.app-header h1 {
    font-family: 'Bangers', cursive;
    font-size: 2.2rem;
    color: #ff6b6b;
    text-shadow: 2px 2px 0px #c0392b, 4px 4px 0px rgba(0,0,0,0.3);
    letter-spacing: 1.5px;
    margin-bottom: 2px;
    line-height: 1.1;
}

.app-header p {
    color: #a0a0c0;
    font-size: 0.9rem;
}

/* ===== Main Three-Column Layout ===== */
.main-layout {
    display: grid;
    grid-template-columns: 320px 1fr 320px;
    gap: 20px;
    align-items: start;
}

@media (max-width: 1300px) {
    .main-layout {
        grid-template-columns: 280px 1fr 280px;
        gap: 14px;
    }
}

@media (max-width: 1024px) {
    .main-layout {
        grid-template-columns: 1fr;
    }
}

/* ===== Side Tool Columns (Left & Right) ===== */
.tool-column,
.toolbar {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    max-height: calc(100vh - 110px);
    overflow-y: auto;
    overflow-x: hidden;
    position: sticky;
    top: 16px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    margin-bottom: 0;
}

.tool-column-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 2px;
}

.tool-column-header h3 {
    font-family: 'Bangers', cursive;
    font-size: 1.35rem;
    color: #ff6b6b;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.tool-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    background: rgba(0, 0, 0, 0.25);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    width: 100%;
    min-width: 0;
    flex: 0 0 auto;
}

.tool-group label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #a0a0c0;
    font-weight: 700;
}

.tool-group select,
.tool-group input[type="number"] {
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(0, 0, 0, 0.35);
    color: #e0e0e0;
    font-size: 0.88rem;
    outline: none;
    width: 100%;
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

.custom-size button {
    padding: 6px 12px;
    border-radius: 6px;
    border: none;
    background: #667eea;
    color: white;
    font-weight: 600;
    cursor: pointer;
}

.custom-size button:hover {
    background: #764ba2;
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
    justify-content: center;
    gap: 6px;
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
.action-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    width: 100%;
}

.export-buttons {
    display: flex;
    flex-direction: column;
    gap: 6px;
    width: 100%;
}

/* ===== Right Column (Canvas Column) ===== */
.canvas-column {
    display: flex;
    flex-direction: column;
    gap: 14px;
    min-width: 0;
    flex: 1;
}

/* ===== Canvas Wrapper ===== */
.canvas-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 190px);
    padding: 24px;
    background: rgba(0, 0, 0, 0.28);
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: auto;
    position: relative;
    box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.4);
}

#canvas-container {
    position: relative;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.7), 0 0 0 2px rgba(99, 102, 241, 0.4);
    border-radius: 4px;
    overflow: hidden;
    background: #ffffff;
    transition: width 0.3s, height 0.3s;
}

#canvas-container.show-grid::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 10;
    background-image: 
        linear-gradient(to right, rgba(99, 102, 241, 0.22) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(99, 102, 241, 0.22) 1px, transparent 1px),
        linear-gradient(to right, rgba(99, 102, 241, 0.08) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(99, 102, 241, 0.08) 1px, transparent 1px);
    background-size: 100px 100px, 100px 100px, 20px 20px, 20px 20px;
}

/* ===== Info Panel ===== */
.info-panel {
    display: flex;
    gap: 24px;
    padding: 10px 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.08);
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

    .layer-buttons,
    .action-buttons,
    .export-buttons {
        flex-wrap: nowrap;
    }
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar {
    width: 8px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.4);
    border-radius: 6px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(90deg, #ff6b6b, #8b5cf6);
    border-radius: 6px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(90deg, #ff8e8e, #a78bfa);
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
        <header class="app-header">
            <div>
                <h1>💥 Comic Book Page Builder</h1>
                <p>Drag, resize, and layer your comic panels!</p>
            </div>
            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <a href="/" class="btn btn-secondary" style="text-decoration: none; padding: 8px 16px; font-weight: 700; border-radius: 8px; color: white;">🏠 Home</a>
                <button id="btn-toggle-model" onclick="toggleModelLoadStatus()" 
                        style="padding: 8px 18px; font-weight: 700; border-radius: 8px; border: none; color: white; cursor: pointer; transition: all 0.2s; font-family: inherit; font-size: 0.9rem; background: linear-gradient(135deg, #10b981 0%, #059669 100%); box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);">
                    🟢 Load/Unload models
                </button>
            </div>
        </header>

        <!-- Main Three-Column Layout -->
        <div class="main-layout">
            <!-- Left Column: Page, Canvas Settings & Text Overlay -->
            <aside class="tool-column toolbar">
                <div class="tool-column-header">
                    <h3>🛠️ Page & Elements</h3>
                </div>

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

                <!-- Background Color & Alignment -->
                <div class="tool-group">
                    <label>Background & Grid</label>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        <div id="color-picker"></div>
                        <button id="btn-toggle-grid" class="btn btn-secondary" onclick="toggleGridOverlay()" style="padding: 6px 12px; font-size: 0.8rem; font-weight: 600; border-radius: 6px; cursor: pointer; background: rgba(99, 102, 241, 0.3); border: 1px solid var(--primary); color: white; flex: 1;">🌐 Grid: ON</button>
                    </div>
                    <button id="btn-transparent-bg" class="btn-toggle-transparent" onclick="toggleTransparentBg()" style="margin-top: 4px; width: 100%;">✨ Transparent Canvas</button>
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
                    <button id="upload-btn" class="btn btn-primary" style="width: 100%;">📁 Upload Image(s)</button>
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
                            <input type="color" id="overlay-text-color" value="#ffffff" title="Text Color" style="width: 32px; height: 30px; border-radius: 4px; cursor: pointer; border: 1px solid rgba(255,255,255,0.2); background: transparent;">
                            <label style="font-size: 0.75rem;">Outline:</label>
                            <input type="color" id="overlay-text-stroke" value="#000000" title="Outline Color" style="width: 32px; height: 30px; border-radius: 4px; cursor: pointer; border: 1px solid rgba(255,255,255,0.2); background: transparent;">
                            <button onclick="addTextOverlay()" class="btn btn-primary" style="padding: 4px 8px; font-size: 0.8rem; flex-grow: 1;">➕ Add</button>
                        </div>
                    </div>
                </div>
            </aside>

            <!-- Middle Column: Canvas Column -->
            <main class="canvas-column">
                <!-- Canvas Area -->
                <div class="canvas-wrapper">
                    <div id="canvas-container" class="show-grid"></div>
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
            </main>

            <!-- Right Column: Panel Styling, Layers & Actions -->
            <aside class="tool-column">
                <div class="tool-column-header">
                    <h3>🎨 Panel & Export</h3>
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
                    <button id="open-crop-btn" class="btn btn-secondary" style="width: 100%;">✂️ Crop</button>
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
            </aside>
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
let nativeCanvasW = 512;
let nativeCanvasH = 768;

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
    nativeCanvasW = initialSize.width;
    nativeCanvasH = initialSize.height;

    stage = new Konva.Stage({
        container: 'canvas-container',
        width: nativeCanvasW,
        height: nativeCanvasH
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
    setCanvasZoom('auto');
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
    let currentVal = val || (zoomSelect ? zoomSelect.value : 'auto');

    let scale = 1.0;

    if (currentVal === 'auto') {
        const wrapper = container.parentElement;
        const availableW = wrapper ? Math.max(200, wrapper.clientWidth - 48) : (window.innerWidth - 420);
        const availableH = wrapper ? Math.max(300, wrapper.clientHeight - 48) : Math.max(300, window.innerHeight - 240);

        const scaleW = availableW / nativeCanvasW;
        const scaleH = (availableH > 50 ? availableH : Math.max(300, window.innerHeight - 240)) / nativeCanvasH;
        scale = Math.min(scaleW, scaleH);
        if (scale > 1) scale = 1.0;
    } else {
        scale = parseFloat(currentVal) / 100;
    }

    const scaledW = Math.round(nativeCanvasW * scale);
    const scaledH = Math.round(nativeCanvasH * scale);

    stage.scale({ x: scale, y: scale });
    stage.width(scaledW);
    stage.height(scaledH);

    container.style.width = scaledW + 'px';
    container.style.height = scaledH + 'px';
    container.style.transform = 'none';
    container.style.marginBottom = '0';

    layer.draw();
}

function toggleGridOverlay() {
    const container = document.getElementById('canvas-container');
    const btn = document.getElementById('btn-toggle-grid');
    if (!container) return;
    const isGridOn = container.classList.toggle('show-grid');
    if (btn) {
        btn.textContent = isGridOn ? '🌐 Grid: ON' : '🌐 Grid: OFF';
        btn.style.background = isGridOn ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255, 255, 255, 0.1)';
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
    nativeCanvasW = width;
    nativeCanvasH = height;

    backgroundRect.width(width);
    backgroundRect.height(height);

    setCanvasZoom();
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
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5100)
