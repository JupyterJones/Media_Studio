from flask import Flask, render_template, request, jsonify, send_from_directory,render_template_string
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
    <!-- Konva.js -->
    <script src="https://unpkg.com/konva@9.2.0/konva.min.js"></script>
    <!-- Pickr Color Picker -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@simonwep/pickr/dist/themes/classic.min.css">
    <script src="https://cdn.jsdelivr.net/npm/@simonwep/pickr/dist/pickr.min.js"></script>
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
</style>
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="app-header">
            <h1>💥 Comic Book Page Builder</h1>
            <p>Drag, resize, and layer your comic panels!</p>
        </header>

        <!-- Toolbar -->
        <div class="toolbar">
            <!-- Page Size Selector -->
            <div class="tool-group">
                <label for="page-size">Page Size</label>
                <select id="page-size">
                    <option value="512x768">Comic Book (512×768)</option>
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

            <!-- Background Color -->
            <div class="tool-group">
                <label>Background</label>
                <div id="color-picker"></div>
            </div>

            <!-- Image Upload -->
            <div class="tool-group">
                <label for="image-upload">Add Image</label>
                <input type="file" id="image-upload" accept="image/*" multiple>
                <button id="upload-btn" class="btn btn-primary">📁 Upload</button>
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

    // Transformer for resizing
    transformer = new Konva.Transformer({
        keepRatio: true,
        enabledAnchors: ['top-left', 'top-right', 'bottom-left', 'bottom-right'],
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

// ===== Pickr Color Picker =====
function initPickr() {
    const pickr = Pickr.create({
        el: '#color-picker',
        theme: 'classic',
        default: '#ffffff',
        components: {
            preview: true,
            opacity: true,
            hue: true,
            interaction: {
                hex: true,
                rgba: true,
                hsla: true,
                hsva: true,
                cmyk: true,
                input: true,
                clear: false,
                save: true
            }
        }
    });

    pickr.on('change', (color) => {
        const hex = color.toHEXA().toString();
        backgroundRect.fill(hex);
        layer.draw();
    });
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

// ===== Selection =====
function selectNode(node) {
    selectedNode = node;
    transformer.nodes([node]);
    layer.draw();
    updateSelectedInfo();
}

function deselectAll() {
    selectedNode = null;
    transformer.nodes([]);
    layer.draw();
    updateSelectedInfo();
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
</script>
</body>
</html>
"""
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5100)
