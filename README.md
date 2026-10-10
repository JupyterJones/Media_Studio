# Media Studio

A high-performance media processing and video composition suite built with **Flask**, **MoviePy**, **OpenCV**, and **FFmpeg**. Features a sleek, modern dark-space glassmorphic UI styled after the *Latent-Horizon* design system.

---

## Highlights & Features

* **Multi-Transition Engine:**
  * **Directional Slides (`slide`):** Random and directed multi-axis slide-in transitions with customizable duration and padding.
  * **Multi-Zoom (`zoomX4`, `zoomY4`, `square_zoomY4`):** Dynamic scale zooms across horizontal, vertical, and square viewports.
  * **Smooth Cross-Fades (`fadem`):** Configurable frame durations with seamless in/out fade dissolves.
  * **Diagonal Slits (`diagonal_transition`):** Sweeping diagonal wipe transitions.
  * **Geometric Mask Reveals (`circular_transition.py`, `square_transition.py`):** Expanding radial and rectangular mask reveals.
  * **Seamless Scrolling (`vertical_scroll.py`):** Creates feathered vertical panoramas and continuous scrolling video streams.
  * **Door & Portal Reveals (`open_door_directory.py`):** Splitting foregrounds and animated dual-door transitions.
  * **FlipBook Sequencer (`Best_FlipBook`):** Rapid-frame animated montage generation.
  * **Blender & Concatenator (`blendem`, `join_all_videos`):** Batch stitching and overlay blending into final production-ready MP4s.
* **Automated Audio Syncing:** Automatic background audio fading, audio trimming, and AAC/M4A/WAV to MP3 transcoding.
* **Completely Standalone:** No external server or daemon required. All video rendering and transitions run directly in-process or via portable local Python scripts.
* **Modern Cyber-Glass UI:** Deep space (`#080812`) backdrop, glowing cyan (`#00f0ff`) and magenta (`#b800ff`) accents, responsive glass cards, and custom controls.

---

## Prerequisites

Ensure you have **Python 3.10+** and **FFmpeg** installed on your system.

### Ubuntu / Debian:
```bash
sudo apt update
sudo apt install -y ffmpeg imagemagick
```

### macOS (Homebrew):
```bash
brew install ffmpeg imagemagick
```

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Media_Studio.git
   cd Media_Studio
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure transition scripts are executable (Linux/macOS):**
   ```bash
   chmod +x slide zoomX4 zoomY4 square_zoomY4 Best_FlipBook blendem diagonal_transition fadem vertical_scroll.py join_all_videos circular_transition.py square_transition.py open_door_directory.py refresh_video.py
   ```

---

## Quickstart

Start the application:
```bash
python MediaStudioSD2.py
```

Then open your browser and navigate to:
```
http://127.0.0.1:5200
```

---

## Directory Structure

```
Media_Studio/
├── MediaStudioSD2.py       # Main Flask web application
├── Best_FlipBook           # Flipbook montage generator
├── blendem                 # Blend and overlay video compositor
├── circular_transition.py  # Circular mask wipe generator
├── diagonal_transition     # Diagonal wipe transition script
├── fadem                   # Cross-fade dissolve generator
├── generate.py             # Optional offline Diffusers image generator
├── join_all_videos         # Video concatenation utility
├── open_door_directory.py  # Dual-door opening effect generator
├── refresh_video.py        # Video asset refresh and sequence pipeline
├── slide                   # Multi-directional sliding transitions
├── square_transition.py    # Square mask wipe generator
├── vertical_scroll.py      # Seamless vertical panoramic scroll generator
├── zoomX4 / zoomY4         # Horizontal / vertical zoom transitions
├── overlays/               # Overlay frames and mask templates
├── static/
│   ├── css/
│   │   ├── themed.css      # Latent-Horizon design system
│   │   ├── dark.css        # Dark theme stylesheet
│   │   └── style.css       # Controls and media player styling
│   ├── output_videos/      # Rendered videos output directory
│   ├── temp_exp/           # Temporary processing video storage
│   ├── novel_images/       # Input images directory
│   ├── audio_mp3/          # Audio tracks directory
│   └── music/              # Background music pool
├── templates/              # Jinja2 HTML templates
├── requirements.txt        # Python package dependencies
├── .gitignore              # Git ignore rules for clean commits
└── README.md               # Documentation
```

---

## How Transitions Work

1. **Input Images:** Place your `.jpg` or `.png` images in `static/novel_images/` or select them directly via the Web UI.
2. **Audio Pool:** Place background `.mp3` tracks into `static/music/`.
3. **Trigger Transitions:**
   * In the Web UI under **Video Processing** (`/mk_videos`), click any transition (Slide, Fade, Zoom, Flipbook, Diagonal, etc.).
   * The studio executes the transition script using the active Python interpreter, mixes in background music with smooth audio fades, applies title banners and borders, and deposits the final video into `static/output_videos/` and `static/temp_exp/`.
4. **Stitch / Concatenate:** Use **Join Videos** (`/join-video`) to merge all transition clips into a single continuous video.

---

## Stable Diffusion Image Synthesis (`/stable_diffusion`)

Media Studio includes a fully offline, standalone Stable Diffusion generation studio. It does not require any external servers or background daemons.

### Features
* **Modes:** 
  * **Text to Image (`txt2img`):** Synthesizes new frames directly from creative positive and negative prompts.
  * **Image to Image (`img2img`):** Upload an initial reference image or click **"Use Last Generated"** / **"Send to Image to Image"** to guide generation with custom **Denoising Strength** (0.05 to 1.0).
* **Live Model Discovery:** Scans `/home/jack/Desktop/Comfy-UI/models/` (or any custom directory set by `COMFY_MODELS_DIR`) dynamically:
  * Checkpoints (`checkpoints/`): SD 1.5, LCM models, etc.
  * LoRAs (`loras/`): Dual simultaneous LoRA stacking with independent strength sliders.
  * Custom VAEs (`vae/`): Automatically loads and hooks custom VAEs for enhanced latent encoding/decoding.
* **Metadata & Gallery Logging:** Saves outputs to `static/novel_images/` and catalogs generation seed, prompt, model, steps, CFG scale, and timestamps in `generations.json`.

---

## License

This project is licensed under the MIT License.

