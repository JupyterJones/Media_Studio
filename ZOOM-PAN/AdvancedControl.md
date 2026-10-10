# 🚀 Advanced Control & Creative Workflow Guide
### *ZoomPan Studio, Comic Builder & AI Generation Engine*

This guide covers advanced techniques for professional AI comic production, non-destructive asset management, multi-model blending, and decoupled keyframe animation.

---

## 📸 1. The "Dream & Restyle" Workflow (Image-to-Image)

Decoupling your **Comic Story Metadata (JSON)** from your **Artwork (Images)** allows you to restyle or upgrade your comic pages infinitely without losing a single camera zoom point or speech bubble.

### How Image-to-Image (img2img) Works

When you feed a rendered comic page or layout sketch into the AI generator with **Image-to-Image mode**, the **Denoising Strength** slider controls how much the AI modifies the original artwork:

| Denoising Strength | Mode & Purpose | What Happens | Keyframe Alignment |
| :--- | :--- | :--- | :--- |
| **0.15 – 0.35** | **Enhance & Restyle** | Keeps **75%–85%** of exact panel lines & layout; adds rich lighting, comic shading, & textures. | **100% Perfect Alignment** with JSON camera keyframes. |
| **0.40 – 0.60** | **Refine & Evolve** | Retains character poses & composition while updating background detail & line art. | High Alignment; minor tweaks may be needed. |
| **0.70 – 0.90** | **Re-Imagine** | Uses the source image only as a loose color/shape guide for a fresh interpretation. | Fresh canvas layout. |

### Step-by-Step "Dreaming" Process
1. **Layout & Draft**: Create your comic page layout in the Comic Builder (`/comic`) or upload a rough sketch.
2. **Keyframe Camera Motion**: Open ZoomPan Studio (`/`), place your camera zoom points on panels, add speech bubbles, and save your project JSON.
3. **Dream & Restyle**:
   * Open the AI Generator (`/generation`).
   * Select **`🖼️ Image-to-Image`** mode.
   * Enter your base page filename (e.g. `comic-page-abc123.png`).
   * Set Denoising Strength to **`0.25`**.
   * Enter your art style prompt (e.g. *"dark superhero comic, dramatic rim lighting, ink hatching, masterpiece"*).
4. **Swap & Re-Render**: Replace the background image with your newly dreamed image. Your JSON camera pans, zooms, and speech bubbles will automatically snap onto the new artwork!

---

## 🎭 2. Multi-LoRA Blending & Weight Tuning

Combining multiple LoRAs (Low-Rank Adaptations) allows you to maintain **character consistency** across different **artistic styles**.

### The Multi-LoRA Formula
* **LoRA 1 — Subject / Character** (Controls *WHO* is in the panel).
* **LoRA 2 — Art Style / Linework** (Controls *HOW* the panel is drawn).

### Recommended Weight Ratios

```text
Character LoRA Scale  : 0.60 – 0.75  (Keeps facial features & costume recognizable)
Style LoRA Scale      : 0.35 – 0.50  (Applies linework & shading without distorting anatomy)
```

---

## 🎨 3. Project Color Palette & Visual Consistency

Maintaining color consistency across multi-page comic issues is essential.

### Unified Color Swatches
* The Comic Builder features a persistent **Project Palette** toolbar next to the Pickr color wheel.
* Color swatches are automatically saved in browser persistent storage (`localStorage`).
* Navigating from **Page 1 $\rightarrow$ Page 2 $\rightarrow$ Page 3** preserves your exact color palette.

### 1-Click Color Application
* **Click any Swatch**: Instantly applies that exact color to the active page background or selected panel border.
* **`+` Button**: Adds your current background/border color to your permanent project palette.

---

## 📁 4. Non-Destructive Project Structure

To prevent accidental file loss or destructive overwriting, projects are structured into clear sub-folders:

```text
projects/Issue_01_The_Beginning/
├── originals/   <-- Master un-cropped source images (Untouched)
├── pages/       <-- Rendered comic page compositions
├── audio/       <-- Kokoro TTS voice clips & BGM tracks
└── videos/      <-- Final rendered MP4 motion videos
```

### Virtual Cropping vs Physical Exports
* **Virtual Cropping**: When you crop an image on the canvas, the app records the crop boundaries non-destructively in data. Your original high-resolution master image in `originals/` is never altered.

---

## 🗑️ 5. App Trash Can (Soft-Delete Safety Net)

Accidentally deleting a panel or image will never destroy your work.

### Two-Stage Deletion Architecture
1. **Stage 1 (Soft Delete)**: Clicking **Delete** anywhere in the app moves the target file into `static/trash/` and records original path metadata.
2. **Stage 2 (App Trash Can UI)**: Visit **`/trash`** anytime to view trashed items:
   * **🔄 Restore**: Moves the file back to its original location instantly.
   * **❌ Delete Forever**: Permanently removes the file from disk (**GONE FOREVER**).
   * **🧹 Empty Trash Can**: Purges all soft-deleted items to free disk space.

---

## 🛠️ Summary Checklist for Production

- [x] **Project Workspace Created** (`/projects`)
- [x] **Page Layout Assembled** (`/comic`)
- [x] **Colors Saved to Swatches** (Project Palette)
- [x] **JSON Motion Keyframes Placed** (`/`)
- [x] **Page Restyled via img2img (0.25 Denoise)** (`/generation`)
- [x] **Trash Can Available for Instant Recovery** (`/trash`)
