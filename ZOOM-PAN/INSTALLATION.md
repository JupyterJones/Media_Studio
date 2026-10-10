# Installation Guide - ZoomPan & Comic Studio

This document provides step-by-step instructions for installing dependencies, setting up model directories, and running **ZoomPan & Comic Studio (App v3)**.

---

## 📋 System Requirements

* **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows.
* **Python**: Version 3.10 or higher.
* **FFmpeg**: Required for video rendering and audio processing.
* **Hardware**:
  * **GPU (Recommended)**: NVIDIA GPU with CUDA support for fast Stable Diffusion image generation.
  * **CPU**: Supported for video rendering, TTS, and core comic editing (SD generation on CPU will be slower).

---

## ⚙️ 1. Install System Dependencies

### Linux (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg libgl1-mesa-glx libglib2.0-0
```

### macOS
```bash
brew install python ffmpeg
```

---

## 🐍 2. Python Environment Setup

Create and activate a Python virtual environment:

```bash
cd /path/to/ZOOM-PAN

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

---

## 📦 3. Install Required Python Libraries

Install all core Python packages:

```bash
pip install --upgrade pip
pip install flask opencv-python pillow moviepy pydub requests icecream werkzeug
```

### PyTorch & Diffusers (for AI Image Generation)

* **CUDA (NVIDIA GPU)**:
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
  pip install diffusers transformers accelerate safetensors
  ```

* **CPU Only**:
  ```bash
  pip install torch torchvision
  pip install diffusers transformers accelerate safetensors
  ```

---

## 📂 4. AI Model Checkpoints & LoRA Setup (Optional)

App v3 automatically detects Stable Diffusion checkpoint models and LoRA weights in your ComfyUI or local model directories:

Default Checkpoint Directory:
```
~/Desktop/Comfy-UI/models/checkpoints/
```

Default LoRA Directory:
```
~/Desktop/Comfy-UI/models/loras/
```

> **Note**: If no local checkpoints are found, you can pass a path to any `.safetensors` model via command line:
> ```bash
> python3 appv3.py --model /path/to/your_model.safetensors
> ```

---

## 🌐 5. Offline Assets Verification

App v3 is configured to work **100% offline** without needing an active internet connection. Ensure the following assets exist in your project directory:

```
static/
├── js/
│   ├── konva.min.js       (Canvas Layout Engine)
│   └── pickr.min.js       (Color Picker)
└── css/
    └── classic.min.css    (Color Picker Styling)
```

If these files are missing, download them locally:
```bash
mkdir -p static/js static/css
curl -sL https://unpkg.com/konva@9.2.0/konva.min.js -o static/js/konva.min.js
curl -sL https://cdn.jsdelivr.net/npm/@simonwep/pickr/dist/themes/classic.min.css -o static/css/classic.min.css
curl -sL https://cdn.jsdelivr.net/npm/@simonwep/pickr/dist/pickr.min.js -o static/js/pickr.min.js
```

---

## 🚀 6. Launching the Server

Run **`appv3.py`** to start the complete studio server:

```bash
python3 appv3.py --port 5000
```

### Command Line Options

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--port` | Port number to run the Flask web app | `5000` |
| `--model` | Path to default `.safetensors` model checkpoint | `comiccraftLCM_beta4.safetensors` |
| `--lora` | Path to default `.safetensors` LoRA file | `None` |
| `--lora_scale` | LoRA blending scale | `0.15` |
| `--device` | Compute device (`cuda`, `mps`, `cpu`, `auto`) | `auto` |

Once started, open your browser and navigate to:
```
http://localhost:5000
```
