# User Guide & Instructions - ZoomPan & Comic Studio (App v3)

Welcome to **ZoomPan & Comic Studio (App v3)** — an end-to-end creative suite for building comic pages, generating AI artwork, composing custom layouts, and producing animated motion videos with speech bubbles and audio tracks.

---

## 🧭 Navigation Overview

When running `appv3.py`, you can access all tools via the top navigation header:

| Page / Route | Feature | Description |
| :--- | :--- | :--- |
| **`/`** | **ZoomPan Studio** | Interactive keyframing tool for zooming, panning, and adding comic speech bubbles to render MP4 motion videos. |
| **`/comic`** | **Comic Book Builder** | Multi-panel page builder with Konva.js canvas, border styling, interactive cropping, and server exports. |
| **`/generation`** | **AI Generator** | Stable Diffusion & LoRA text-to-image engine for generating comic art and characters. |
| **`/image_gallery`** | **Image Gallery** | Browse, inspect dimensions/metadata, and manage uploaded or generated images. |
| **`/video_gallery`** | **Video Gallery** | Preview, download, frame, or delete rendered MP4 video files. |
| **`/frame_video`** | **Video Framer** | Overlay decorative title frames onto rendered videos. |
| **`/text_to_mp3`** | **Kokoro TTS** | Generate narration and dialogue audio clips for your videos. |

---

## 💥 1. Comic Book Page Builder (`/comic`)

The Comic Book Page Builder allows you to arrange panels, crop images, add borders, and save high-resolution comic pages.

### 📐 Preset Page Sizes
* Select from popular presets in the dropdown:
  * **Comic Book** ($512 \times 768$)
  * **Manga** ($600 \times 900$)
  * **Tablet** ($768 \times 1024$)
  * **Large** ($800 \times 1200$)
  * **Landscape** ($1024 \times 768$)
  * **Custom**: Enter custom width & height ($100\text{px} - 2000\text{px}$).

### 📁 Adding & Uploading Images
1. Click **📁 Upload** to select images from your computer.
2. Uploaded images are automatically added to the canvas and saved to `static/uploads/`.
3. Drag, rotate, or scale images using the corner anchors.

### 🖼️ Border Styling
Select an image on the canvas to adjust its borders in real-time:
* **Border Width**: Set stroke thickness from `0px` to `30px`.
* **Border Color**: Pick any color using the color picker (e.g. classic comic black `#000000`).
* **Corner Radius**: Round panel corners from `0px` to `50px`.

### ✂️ Interactive Image Cropping
1. Select an image on the canvas and click **✂️ Crop**.
2. An interactive modal opens showing a real-time dark overlay preview.
3. Adjust the **Top**, **Bottom**, **Left**, and **Right** sliders ($0\% - 45\%$) to crop the desired region.
4. Click **✅ Apply Crop** to update the canvas panel.
5. Click **🔄 Reset** anytime to revert to the full uncropped image.

### 🔝 Layer Control & Actions
* **⬆️ Front / ↑ Up / ↓ Down / ⬇️ Back**: Adjust z-index ordering of overlapping panels.
* **🗑️ Clear All**: Remove all panel elements.
* **❌ Delete**: Remove the currently selected image (or press `Delete` / `Backspace` key).

### 💾 Export Options
* **💾 Download PNG**: Downloads a high-resolution PNG image ($2\times$ pixel ratio) directly to your browser.
* **☁️ Save to Server**: Saves the comic page to `static/uploads/` so it can be immediately imported into ZoomPan Studio for video animation!

---

## 🎥 2. ZoomPan Motion Video Generator (`/`)

Animate comic pages or images into dynamic cinematic videos:

### 🎯 Setting Keyframe Points
1. Select a source image from `static/uploads/` (including saved comic pages).
2. Click anywhere on the image to set sequential keyframe focus points.
3. For each keyframe point, set:
   * **Zoom Level**: Scale factor ($1.0\times - 5.0\times$).
   * **Transition Duration**: Camera movement speed in seconds.
   * **Hold Duration**: Time to linger on the keyframe in seconds.

### 💬 Adding Speech & Thought Bubbles
Attach styled speech bubbles to any keyframe point:
* **Styles Available**:
  * `speech` / `speech_left` / `speech_right` (Classic speech bubble with directional tail)
  * `thought` / `thought_left` / `thought_right` (Cloud bubble with thought circles)
  * `caption` (Classic comic narration box)
  * `sfx` (High-contrast action sound effect box)
  * `manga` (Monochrome manga style box)
  * `noir` (Desaturated detective style)
  * `hero` (Action comic style)

### 🎬 Rendering MP4 Video
1. Select output resolution (**1080p**, **720p**, or **Native**).
2. Choose optional background audio track (`.mp3` / `.wav`).
3. Click **Generate MP4 Video** to compose smooth camera easing and text bubbles into a finished video file.

---

## 🎨 3. AI Image Generation (`/generation`)

Generate original comic panels using local Stable Diffusion checkpoints:

1. **Select Model Checkpoint**: Pick from detected `.safetensors` models.
2. **Select LoRA**: Optionally apply LoRA style weights and set scale ($0.0 - 1.0$).
3. **Prompting**:
   * **Positive Prompt**: Describe subject, style, lighting, framing.
   * **Negative Prompt**: Exclude unwanted artifacts (`blurry, low quality, etc.`).
4. **Parameters**: Set inference steps ($5 - 50$), CFG guidance ($1.0 - 15.0$), and image dimensions.
5. Generated images are saved directly to `static/uploads/` for use across all tools.

---

## 🔊 4. Kokoro TTS Audio Generator (`/text_to_mp3`)

Create voice narration or dialogue for your videos:

* **Regular Mode**: Convert text script to voice using Kokoro TTS voices (`am_adam`, `af_sarah`, `am_echo`, etc.).
* **Reflective Script Mode**: Automatically detects dialogue quotes (`"..."`) and switches between Narrator and Character voices with dynamic sentence pauses.

---

## 📁 5. Integrated Workflow Example

1. **Generate Artwork**: Go to `/generation` and generate character art.
2. **Build Comic Page**: Go to `/comic`, arrange your AI art into panels, apply borders and crops, then click **Save to Server**.
3. **Animate Page**: Go to `/` (ZoomPan Studio), select your saved comic page, set camera zoom points and speech bubbles, then click **Generate MP4 Video**.
