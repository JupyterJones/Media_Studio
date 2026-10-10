#!/usr/bin/env python3
"""
Sci-Fi Vision Engine: Storyboard Parser, Ollama AI, Kokoro TTS, SD LCM, & Video Composer
Transforms Markdown Sci-Fi Storyboards into Cinematic MP4 Videos.
"""

import os
import re
import sys
import json
import time
import shutil
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# System paths - Fully portable and dynamic for USB / SSD / external copying
WORKSPACE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = WORKSPACE_DIR / "assets"
PANELS_DIR = ASSETS_DIR / "panels"
AUDIO_DIR = ASSETS_DIR / "audio"
TEMP_DIR = WORKSPACE_DIR / "temp"
RESOURCES_DIR = WORKSPACE_DIR / "resources"

HOME_DIR = Path.home()
DESKTOP_DIR = HOME_DIR / "Desktop"

# BGM: check local workspace first, then Desktop/mp3, then Old_Drive_Files, then OLD_HDD, then default
if (WORKSPACE_DIR / "mp3").exists():
    BGM_DIR = WORKSPACE_DIR / "mp3"
elif (DESKTOP_DIR / "mp3").exists():
    BGM_DIR = DESKTOP_DIR / "mp3"
elif (DESKTOP_DIR / "Old_Drive_Files" / "Desktop" / "mp3").exists():
    BGM_DIR = DESKTOP_DIR / "Old_Drive_Files" / "Desktop" / "mp3"
elif Path("/media/jack/OLD_HDD/home/jack/Desktop/mp3").exists():
    BGM_DIR = Path("/media/jack/OLD_HDD/home/jack/Desktop/mp3")
else:
    BGM_DIR = Path("/home/jack/Desktop/mp3")

# Kokoro TTS: dynamic fallback
KOKORO_DIR = DESKTOP_DIR / "Kokoro-TTS-Pause" if (DESKTOP_DIR / "Kokoro-TTS-Pause").exists() else Path("/home/jack/Desktop/Kokoro-TTS-Pause")
KOKORO_BIN = KOKORO_DIR / "venv" / "bin" / "kokoro-tts"
KOKORO_MODEL = KOKORO_DIR / "kokoro-v1.0.onnx"
KOKORO_VOICES = KOKORO_DIR / "voices-v1.0.bin"
PYTHON_VENV = KOKORO_DIR / "venv" / "bin" / "python3"

# ComfyUI checkpoints: dynamic fallback
if (DESKTOP_DIR / "Comfy-UI").exists():
    COMFY_DIR = DESKTOP_DIR / "Comfy-UI"
elif (DESKTOP_DIR / "Old_Drive_Files" / "Desktop" / "Comfy-UI").exists():
    COMFY_DIR = DESKTOP_DIR / "Old_Drive_Files" / "Desktop" / "Comfy-UI"
elif Path("/media/jack/OLD_HDD/home/jack/Desktop/Comfy-UI").exists():
    COMFY_DIR = Path("/media/jack/OLD_HDD/home/jack/Desktop/Comfy-UI")
else:
    COMFY_DIR = Path("/home/jack/Desktop/Comfy-UI")
COMFY_CHECKPOINTS_DIR = COMFY_DIR / "models" / "checkpoints"

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

for d in [ASSETS_DIR, PANELS_DIR, AUDIO_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Global model cache for SD
_sd_pipe = None


def sanitize_text_for_display(text: str) -> str:
    """
    Strips emojis and unsupported unicode glyphs for PIL DejaVu fonts,
    replacing them with clean sci-fi ASCII symbols.
    """
    if not text:
        return ""
    # Remove emoji characters (unicode surrogate / emoji blocks)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE
    )
    clean = emoji_pattern.sub("", text)
    # Fix comma spacing
    clean = re.sub(r"\s*,\s*", ", ", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def get_story_slug(title: str) -> str:
    """Derives a clean safe project slug for isolated asset directories."""
    clean = re.sub(r'[^a-zA-Z0-9]+', '_', (title or "").lower()).strip('_')
    if not clean or clean in ["untitled_sci_fi_story", "template"]:
        return "science_1"
    if "staacor" in clean:
        return "staacor"
    if "marine" in clean:
        return "cybernetic_marine"
    if "kepler" in clean:
        return "kepler"
    if "aurora" in clean:
        return "science_1"
    return clean


def parse_storyboard_markdown(md_content: str, project_slug: str = None):
    """
    Parses storyboard markdown into structured panels and metadata.
    Automatically routes assets to dedicated project folders to prevent overwriting.
    """
    story = {
        "title": "Untitled Sci-Fi Story",
        "bgm": "Deep Mystery & Tension",
        "panels": []
    }

    # Extract title
    title_match = re.search(r"COMIC STORYBOARD:\s*[\"']?([^\"'\n]+)[\"']?", md_content, re.IGNORECASE)
    if title_match:
        t = title_match.group(1).strip()
        t = re.sub(r"[\"'\*]+$", "", t).strip()
        t = re.sub(r"^[\"'\*]+", "", t).strip()
        story["title"] = sanitize_text_for_display(t)

    # Derive or use project slug
    if not project_slug:
        project_slug = get_story_slug(story["title"])
    story["project_slug"] = project_slug
    
    if project_slug == "science_1":
        story["output_filename"] = "science_1.mp4"
        story_panels_dir = ASSETS_DIR / "panels"
        story_audio_dir = ASSETS_DIR / "audio"
    elif project_slug == "staacor":
        story["output_filename"] = "staacor_news.mp4"
        story_panels_dir = ASSETS_DIR / "staacor_panels"
        story_audio_dir = ASSETS_DIR / "staacor_audio"
    elif project_slug in ["marine", "cybernetic_marine"]:
        story["output_filename"] = "cybernetic_marine.mp4"
        story_panels_dir = ASSETS_DIR / "marine_panels"
        story_audio_dir = ASSETS_DIR / "marine_audio"
    else:
        story["output_filename"] = f"{project_slug}.mp4"
        story_panels_dir = ASSETS_DIR / f"{project_slug}_panels"
        story_audio_dir = ASSETS_DIR / f"{project_slug}_audio"

    story_panels_dir.mkdir(parents=True, exist_ok=True)
    story_audio_dir.mkdir(parents=True, exist_ok=True)

    # Extract BGM
    bgm_match = re.search(r"Recommended BGM\*\*:\s*([^\n]+)", md_content, re.IGNORECASE)
    if bgm_match:
        story["bgm"] = sanitize_text_for_display(bgm_match.group(1).strip())

    # Split into panel blocks
    panel_pattern = re.compile(r"###\s*🖼️?\s*([^\n]+)", re.IGNORECASE)
    splits = list(panel_pattern.finditer(md_content))

    for i, match in enumerate(splits):
        header = sanitize_text_for_display(match.group(1).strip())
        start = match.end()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(md_content)
        panel_body = md_content[start:end]

        panel_info = {
            "index": i + 1,
            "header": header,
            "voice": "af_nova",
            "voice_role": "",
            "layout": "Width: 1/2 Row | Height: 1 Row",
            "raw_text": "",
            "spoken_text": "",
            "image_prompt": "",
            "image_path": str(story_panels_dir / f"panel_{i+1}.jpg"),
            "audio_path": str(story_audio_dir / f"panel_{i+1}.wav"),
            "image_url": f"/assets/{story_panels_dir.name}/panel_{i+1}.jpg",
            "audio_url": f"/assets/{story_audio_dir.name}/panel_{i+1}.wav"
        }

        # Layout
        layout_match = re.search(r"\*\s*🔲\s*\*\*Layout\*\*:\s*([^\n]+)", panel_body)
        if layout_match:
            panel_info["layout"] = sanitize_text_for_display(layout_match.group(1).strip())

        # Camera Motion (v2)
        motion_match = re.search(r"\*\s*🎥\s*\*\*Camera Motion\*\*:\s*([^\n]+)", panel_body)
        if motion_match:
            panel_info["camera_motion"] = motion_match.group(1).strip()

        # Voice
        voice_match = re.search(r"\*\s*🎙️?\s*\*\*Voice\*\*:\s*`?([a-zA-Z0-9_]+)`?\s*(?:\((.*?)\))?", panel_body)
        if voice_match:
            panel_info["voice"] = voice_match.group(1).strip()
            if voice_match.group(2):
                panel_info["voice_role"] = sanitize_text_for_display(voice_match.group(2).strip())

        # Voice Speed (v2)
        speed_match = re.search(r"\*\s*⚡\s*\*\*Voice Speed\*\*:\s*([0-9.]+)", panel_body)
        if speed_match:
            try:
                panel_info["speed"] = float(speed_match.group(1).strip())
            except ValueError:
                pass

        # Image Prompt
        prompt_match = re.search(r"\*\s*🎨\s*\*\*Stable Diffusion Image Prompt\*\*:\s*`?([^`*]+)`?", panel_body)
        if prompt_match:
            panel_info["image_prompt"] = prompt_match.group(1).strip().replace("\n", " ")

        # On-Screen Speech (Markdown / Display)
        speech_match = re.search(r"\*\s*💬\s*\*\*On-Screen Dialogue.*?\*\*:\s*(.*?)(?=\*\s*[🎨🎥⚡⚙️🗣️🎵]|\Z)", panel_body, re.DOTALL)
        if not speech_match:
            speech_match = re.search(r"\*\s*💬\s*\*\*Narration\s*/\s*Dialogue.*?\*\*:\s*(.*?)(?=\*\s*[🎨🎥⚡⚙️🗣️🎵]|\Z)", panel_body, re.DOTALL)
        if not speech_match:
            speech_match = re.search(r"\*\s*💬\s*\*\*Speech.*?\*\*:\s*(.*?)(?=\*\s*[🎨🎥⚡⚙️🗣️🎵]|\Z)", panel_body, re.DOTALL)
        if not speech_match:
            speech_match = re.search(r"\*\s*💬.*?\*\*:\s*(.*?)(?=\*\s*[🎨🎥⚡⚙️🗣️🎵]|\Z)", panel_body, re.DOTALL)

        if speech_match:
            raw_text = speech_match.group(1).strip()
            panel_info["raw_text"] = raw_text
            panel_info["spoken_text"] = clean_for_speech(raw_text)

        # Spoken Text Clean (v2 explicit override for phonetic perfection)
        spoken_match = re.search(r"\*\s*🗣️?\s*\*\*Spoken Text.*?\*\*:\s*(.*?)(?=\*\s*[🎨🎥⚡⚙️💬🎵]|\Z)", panel_body, re.DOTALL)
        if spoken_match:
            panel_info["spoken_text"] = clean_for_speech(spoken_match.group(1).strip())

        story["panels"].append(panel_info)

    return story


def clean_for_speech(text: str) -> str:
    """
    Cleans markdown formatting into natural flowing spoken dialogue for TTS.
    """
    t = text
    t = re.sub(r"^>\s*", "", t, flags=re.MULTILINE)
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.MULTILINE)
    t = re.sub(r"LOG DATE:\s*(\d{4})\.(\d{2})", r"Log date: \1 point \2.", t)
    t = re.sub(r"//\s*ORBITAL SECTOR\s*(\d+)", r"Orbital Sector \1.", t)
    t = t.replace("**", "").replace("*", "").replace("`", "")
    t = t.replace('"', '')
    t = t.replace("...", ", ").replace("…", ", ")
    t = t.replace("//", ", ")
    lines = [line.strip() for line in t.splitlines() if line.strip()]
    spoken = " ".join(lines)
    spoken = re.sub(r"\s*,\s*", ", ", spoken)
    spoken = re.sub(r"\s+", " ", spoken).strip()
    return spoken


def generate_storyboard_with_ollama(prompt: str, model: str = "scifi-writer:1", timeout: int = 1000) -> str:
    """
    Calls local Ollama server with streaming tokens and enforced minimum 1000s timeout (NEVER under 500s).
    """
    # Enforce strict minimum timeout policy: NEVER under 1000s
    if not timeout or timeout < 1000:
        timeout = 1000

    # Director Rule: NEVER just one sentence; 2-4 sentences provide enough time for Ken Burns motion
    timing_guidance = (
        "\n\n[DIRECTOR INSTRUCTION]:\n"
        "- NEVER write only 1 sentence for a panel! For EVERY panel, write 2 to 4 full, vivid sentences of narration/dialogue.\n"
        "- Provide 30-50 words per panel so the spoken voice lasts 10 to 18 seconds, giving ample time for the cinematic Ken Burns camera motion to be fully visible.\n"
        "- Explicitly include a '* 🎥 **Camera Motion**: [Zoom-In Center | Pan Left to Right | Zoom-Out Wide]' line for every panel.\n"
    )
    full_prompt = prompt.strip() + timing_guidance

    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True
    }
    try:
        print(f"[*] Calling Ollama model '{model}' with timeout={timeout}s (streaming tokens)...")
        response_chunks = []
        with requests.post(url, json=payload, stream=True, timeout=timeout) as r:
            if r.status_code != 200:
                raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")
            for line in r.iter_lines(decode_unicode=True):
                if line:
                    chunk = json.loads(line)
                    response_chunks.append(chunk.get("response", ""))
                    if chunk.get("done", False):
                        break
        result = "".join(response_chunks).strip()
        if not result:
            raise RuntimeError("Ollama returned an empty response.")
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Ollama ({url}) [timeout={timeout}s]: {e}")


def synthesize_panel_audio(panel: dict, speed: float = 0.95):
    """
    Synthesizes speech audio using Kokoro TTS CLI.
    """
    spoken_text = panel.get("spoken_text", "").strip()
    if not spoken_text:
        spoken_text = clean_for_speech(panel.get("raw_text", "Entering sector."))

    voice = panel.get("voice", "af_nova")
    audio_path = Path(panel["audio_path"])
    audio_path.parent.mkdir(parents=True, exist_ok=True)

    temp_txt = TEMP_DIR / f"tts_{panel.get('index', 1)}.txt"
    temp_txt.write_text(spoken_text, encoding="utf-8")

    cmd = [
        str(KOKORO_BIN),
        str(temp_txt),
        str(audio_path),
        "--voice", voice,
        "--model", str(KOKORO_MODEL),
        "--voices", str(KOKORO_VOICES),
        "--speed", str(speed)
    ]
    print(f"[*] Kokoro TTS: Synthesizing voice '{voice}' -> {audio_path.name}...")
    subprocess.run(cmd, check=True)
    return str(audio_path)


def generate_panel_image_lcm(prompt: str, output_path: str, model_name: str = "dreamshaper_8LCM.safetensors", steps: int = 4):
    """
    Generates an image using local Stable Diffusion LCM checkpoint on CPU/GPU.
    """
    global _sd_pipe
    from diffusers import StableDiffusionPipeline, LCMScheduler
    import torch

    checkpoint_path = COMFY_CHECKPOINTS_DIR / model_name
    if not checkpoint_path.exists():
        checkpoints = list(COMFY_CHECKPOINTS_DIR.glob("*.safetensors"))
        if checkpoints:
            checkpoint_path = checkpoints[0]
        else:
            raise FileNotFoundError(f"No safetensors checkpoint found in {COMFY_CHECKPOINTS_DIR}")

    if _sd_pipe is None:
        print(f"[*] Loading Stable Diffusion LCM checkpoint: {checkpoint_path.name}...")
        _sd_pipe = StableDiffusionPipeline.from_single_file(
            str(checkpoint_path),
            torch_dtype=torch.float32,
            safety_checker=None
        )
        _sd_pipe.scheduler = LCMScheduler.from_config(_sd_pipe.scheduler.config)
        _sd_pipe.to("cpu")
        _sd_pipe.enable_attention_slicing()

    print(f"[*] Generating image for prompt: '{prompt[:60]}...' ({steps} steps)")
    image = _sd_pipe(
        prompt=prompt,
        negative_prompt="blurry, low quality, deformed, artifacts, text, watermark",
        num_inference_steps=steps,
        guidance_scale=1.5,
        width=512,
        height=512
    ).images[0]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    return output_path


def generate_panel_image_gemini(prompt: str, output_path: str):
    """
    Generates an image via the user's GEMINI_API_KEY (gemini-2.5-flash-image / Nano Banana).
    """
    import base64
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    models_to_try = ["gemini-2.5-flash-image", "gemini-3.1-flash-image"]
    last_err = None

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"Generate an image: {prompt}"}]
            }]
        }
        try:
            r = requests.post(url, json=payload, timeout=300)
            if r.status_code == 200:
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        if "inlineData" in part:
                            img_bytes = base64.b64decode(part["inlineData"]["data"])
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "wb") as f:
                                f.write(img_bytes)
                            return output_path
            elif r.status_code == 429:
                raise RuntimeError("Google Gemini API Quota Exceeded (429). Enable billing at https://ai.google.dev to unlock image generation quota on your API key.")
            else:
                last_err = f"Gemini API returned {r.status_code}: {r.text[:200]}"
        except requests.exceptions.RequestException as e:
            last_err = str(e)

    raise RuntimeError(last_err or "Failed to generate image via Gemini API.")


def get_audio_duration(audio_path: str) -> float:
    """
    Returns the duration of an audio file in seconds via ffprobe.
    """
    cmd = [
        "ffprobe", "-i", str(audio_path),
        "-show_entries", "format=duration",
        "-v", "quiet", "-of", "csv=p=0"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def generate_panel_overlay(width: int, height: int, story_title: str, panel: dict, output_png: str):
    """
    Draws a sleek cyberpunk sci-fi HUD frame and comic dialogue overlay with clean text.
    """
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_header = ImageFont.truetype(FONT_BOLD, 22)
    font_badge = ImageFont.truetype(FONT_BOLD, 18)
    font_body = ImageFont.truetype(FONT_BOLD, 27)

    # Clean strings
    clean_title = sanitize_text_for_display(story_title)
    clean_header = sanitize_text_for_display(panel.get("header", ""))

    # 1. Top HUD Bar
    draw.rectangle([(0, 0), (width, 54)], fill=(6, 12, 22, 210))
    draw.line([(0, 54), (width, 54)], fill=(0, 220, 255, 230), width=2)
    top_title = f">> {clean_title.upper()} // {clean_header.upper()}"
    draw.text((40, 15), top_title, fill=(0, 240, 255), font=font_header)
    draw.text((width - 360, 16), "STATUS: RECON ACTIVE // 1080P", fill=(170, 195, 220), font=font_badge)

    # 2. Bottom Dialogue Box
    box_x1 = 120
    box_y1 = height - 210
    box_x2 = width - 120
    box_y2 = height - 50

    draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], fill=(6, 12, 22, 225))
    draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], outline=(0, 195, 245, 170), width=2)

    # Corner brackets in neon amber
    corner = 24
    for cx, cy, dx, dy in [
        (box_x1, box_y1, 1, 1),
        (box_x2, box_y1, -1, 1),
        (box_x1, box_y2, 1, -1),
        (box_x2, box_y2, -1, -1)
    ]:
        draw.line([(cx, cy), (cx + dx * corner, cy)], fill=(255, 204, 0, 255), width=4)
        draw.line([(cx, cy), (cx, cy + dy * corner)], fill=(255, 204, 0, 255), width=4)

    # 3. Speaker Badge
    voice = panel.get("voice", "af_nova")
    role = panel.get("voice_role", "")
    badge_text = f":: TRANSMISSION // {voice.upper()}" + (f" ({role.upper()})" if role else "")
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0] + 36
    bh = 32
    bx = box_x1 + 30
    by = box_y1 - 16
    draw.rectangle([(bx, by), (bx + bw, by + bh)], fill=(0, 180, 240, 245))
    draw.text((bx + 18, by + 6), badge_text, fill=(4, 12, 20), font=font_badge)

    # 4. Dialogue Text
    raw_content = panel.get("spoken_text", panel.get("raw_text", ""))
    clean_content = sanitize_text_for_display(raw_content)
    max_w = (box_x2 - box_x1) - 60
    lines = wrap_text(clean_content, font_body, max_w, draw)
    text_y = box_y1 + 32
    for line in lines[:3]:
        draw.text((box_x1 + 32, text_y + 2), line, fill=(0, 0, 0, 240), font=font_body)
        draw.text((box_x1 + 30, text_y), line, fill=(245, 250, 255), font=font_body)
        text_y += 38

    overlay.save(output_png)
    return output_png


def render_panel_clip(panel: dict, story_title: str, output_clip_path: str, fps: int = 30):
    """
    Renders a single video clip for a panel with Ken Burns motion, HUD overlay, and voice audio.
    """
    image_path = panel.get("image_path")
    audio_path = panel.get("audio_path")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found for panel {panel.get('index')}: {image_path}")

    if not os.path.exists(audio_path):
        synthesize_panel_audio(panel)

    audio_dur = get_audio_duration(audio_path)
    # Ensure minimum 6.0s clip duration so Ken Burns camera motion is always clearly visible
    clip_dur = max(6.0, round(audio_dur + 1.2, 2))

    overlay_png = str(TEMP_DIR / f"overlay_{panel.get('index', 1)}.png")
    generate_panel_overlay(1920, 1080, story_title, panel, overlay_png)

    # Motion styles: calculate frame count for consistent, noticeable Ken Burns motion
    total_frames = max(30, int(clip_dur * fps))
    tf = total_frames
    motion_raw = (panel.get("camera_motion") or "").lower()
    idx = panel.get("index", 1)

    if "pan" in motion_raw and ("right" in motion_raw or "east" in motion_raw):
        # Pan Left to Right across frame
        zp_filter = f"zoompan=z=1.22:x='(iw-iw/zoom)*(on/{tf})':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps={fps}"
    elif "pan" in motion_raw and ("left" in motion_raw or "west" in motion_raw):
        # Pan Right to Left across frame
        zp_filter = f"zoompan=z=1.22:x='(iw-iw/zoom)*(1-on/{tf})':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps={fps}"
    elif "zoom-out" in motion_raw or "zoom out" in motion_raw or "wide" in motion_raw:
        # Cinematic Zoom-Out (reveals wide scene)
        zp_filter = f"zoompan=z='max(1.30-0.25*(on/{tf}),1.05)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps={fps}"
    elif "zoom-in" in motion_raw or "zoom in" in motion_raw or "close" in motion_raw or "push" in motion_raw:
        # Cinematic Zoom-In (draws into focal point)
        zp_filter = f"zoompan=z='min(1.05+0.25*(on/{tf}),1.35)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps={fps}"
    else:
        # Beautiful rotating Ken Burns pattern per panel:
        pattern = idx % 5
        if pattern == 1:
            # Dynamic Zoom-In toward center
            zp_filter = f"zoompan=z='min(1.05+0.25*(on/{tf}),1.32)':x='(iw-iw/zoom)*0.45':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps={fps}"
        elif pattern == 2:
            # Pan Left-to-Right with slight vertical drift
            zp_filter = f"zoompan=z=1.22:x='(iw-iw/zoom)*(on/{tf})':y='(ih-ih/zoom)*(0.3+0.4*(on/{tf}))':d=1:s=1920x1080:fps={fps}"
        elif pattern == 3:
            # Cinematic Zoom-Out revealing scope
            zp_filter = f"zoompan=z='max(1.30-0.24*(on/{tf}),1.05)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*0.45':d=1:s=1920x1080:fps={fps}"
        elif pattern == 4:
            # Pan Right-to-Left with slight upward drift
            zp_filter = f"zoompan=z=1.22:x='(iw-iw/zoom)*(1-on/{tf})':y='(ih-ih/zoom)*(0.7-0.4*(on/{tf}))':d=1:s=1920x1080:fps={fps}"
        else:
            # Diagonal push-in
            zp_filter = f"zoompan=z='min(1.06+0.22*(on/{tf}),1.30)':x='(iw-iw/zoom)*(0.2+0.6*(on/{tf}))':y='(ih-ih/zoom)*(0.3+0.4*(on/{tf}))':d=1:s=1920x1080:fps={fps}"


    filter_complex = (
        f"[0:v]scale=2560:1440,{zp_filter}[bg]; "
        f"[bg][1:v]overlay=0:0[v]; "
        f"[2:a]adelay=400|400,apad=whole_dur={clip_dur}[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(fps), "-t", str(clip_dur), "-i", str(image_path),
        "-i", str(overlay_png),
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-t", str(clip_dur),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_clip_path)
    ]

    print(f"[*] Rendering Panel {idx} clip ({clip_dur}s)...")
    subprocess.run(cmd, check=True)
    return output_clip_path


def get_available_bgm():
    """
    Returns a list of all mp3 files available in /home/jack/Desktop/mp3/
    """
    if not BGM_DIR.exists():
        return []
    return sorted([f.name for f in BGM_DIR.glob("*.mp3")])


def get_available_resources():
    """
    Returns metadata for all image files available in /home/jack/Desktop/scifi-writer_1/resources/
    """
    if not RESOURCES_DIR.exists():
        return []
    files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        for f in RESOURCES_DIR.glob(ext):
            files.append({
                "filename": f.name,
                "url": f"/resources/{f.name}",
                "size_kb": round(f.stat().st_size / 1024, 1)
            })
    return sorted(files, key=lambda x: x["filename"])


def find_matching_bgm(bgm_hint: str) -> str:
    """
    Finds the best matching background music file in /home/jack/Desktop/mp3/
    """
    if not BGM_DIR.exists():
        return None

    mp3_files = list(BGM_DIR.glob("*.mp3"))
    if not mp3_files:
        return None

    hint_lower = (bgm_hint or "").lower()
    if "mystery" in hint_lower or "tension" in hint_lower:
        preferred = ["Shadows-Anno_Domini_Beats.mp3", "Sinister-Anno_Domini_Beats.mp3", "Deified-The_Grey_Room_Density_and_Time.mp3"]
    elif "drama" in hint_lower or "suspense" in hint_lower:
        preferred = ["GodFury-AnnoDominiBeats.mp3", "Freefall-Anno_Domini_Beats.mp3", "Sagas-The_Grey_Room_Density_and_Time.mp3"]
    elif "reflection" in hint_lower or "calm" in hint_lower:
        preferred = ["Remember-Anno_Domini_Beats.mp3", "Sailing-Anno_Domini_Beats.mp3", "The_Off-White_Lotus-Ezra_Lipp.mp3"]
    else:
        preferred = ["Future-Anno_Domini_Beats.mp3", "Invincible-Anno_Domini_Beats.mp3"]

    for name in preferred:
        candidate = BGM_DIR / name
        if candidate.exists():
            return str(candidate)

    return str(mp3_files[0])


def get_unique_video_path(desired_name) -> Path:
    """
    STRICT ZERO-OVERWRITE GUARANTEE:
    Ensures newly rendered videos NEVER overwrite previous videos.
    If the target file already exists, assigns a unique section in the filename
    using a timestamp suffix (_YYYYMMDD_HHMMSS) or auto-incrementing counter.
    """
    target = Path(desired_name)
    if not target.is_absolute():
        target = WORKSPACE_DIR / target

    if not target.exists():
        return target

    base_stem = target.stem
    suffix = target.suffix or ".mp4"

    # Strip existing timestamp or counter pattern to avoid compounding suffixes
    clean_stem = re.sub(r'_\d{8}_\d{6}(?:_\d+)?$', '', base_stem)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = target.parent / f"{clean_stem}_{timestamp}{suffix}"

    counter = 1
    while candidate.exists():
        candidate = target.parent / f"{clean_stem}_{timestamp}_{counter:02d}{suffix}"
        counter += 1

    return candidate


def compile_full_video(storyboard: dict, output_mp4: str = "science_1.mp4", bgm_path: str = None, bgm_volume: float = 0.22, progress_cb=None):
    """
    Compiles all panel clips into the final polished science_1.mp4 with background music.
    Guarantees that previous videos are never overwritten by assigning a unique section.
    """
    panels = storyboard.get("panels", [])
    if not panels:
        raise ValueError("Storyboard contains no panels to render.")

    story_title = storyboard.get("title", "Aurora Rising")
    clip_paths = []

    if progress_cb:
        progress_cb(10, "Rendering individual panel clips...")

    # 1. Render all panel clips
    for idx, panel in enumerate(panels):
        clip_path = str(TEMP_DIR / f"clip_panel_{panel.get('index')}.mp4")
        if progress_cb:
            pct = 15 + int((idx / len(panels)) * 50)
            progress_cb(pct, f"Rendering Panel {panel.get('index')} ({panel.get('header')})...")
        render_panel_clip(panel, story_title, clip_path)
        clip_paths.append(clip_path)

    # 2. Write concat list
    concat_txt = TEMP_DIR / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    merged_raw = TEMP_DIR / "merged_raw.mp4"
    if progress_cb:
        progress_cb(70, "Concatenating panel clips...")

    print("[*] Concatenating panel clips...")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(merged_raw)
    ]
    subprocess.run(cmd_concat, check=True)

    total_dur = get_audio_duration(str(merged_raw))
    print(f"[*] Merged storyboard duration: {total_dur:.2f}s")

    # 3. Background Music (BGM)
    if not bgm_path or not os.path.exists(bgm_path):
        bgm_path = find_matching_bgm(storyboard.get("bgm", ""))

    final_out = Path(output_mp4)
    if not final_out.is_absolute():
        final_out = WORKSPACE_DIR / output_mp4
    # Enforce strict zero-overwrite guarantee
    final_out = get_unique_video_path(final_out)
    print(f"[*] Target unique output path: {final_out.name}")

    if progress_cb:
        progress_cb(85, "Mixing cinematic soundtrack and mastering audio...")

    if bgm_path and os.path.exists(bgm_path):
        print(f"[*] Mixing BGM track: {os.path.basename(bgm_path)} (vol={bgm_volume})...")
        fade_out_start = max(0.0, total_dur - 3.5)
        filter_audio = (
            f"[1:a]aloop=loop=-1:size=2e+09,volume={bgm_volume},"
            f"afade=t=in:ss=0:d=1.5,afade=t=out:st={fade_out_start:.2f}:d=3.5[bgm]; "
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd_final = [
            "ffmpeg", "-y",
            "-i", str(merged_raw),
            "-i", str(bgm_path),
            "-filter_complex", filter_audio,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "256k",
            str(final_out)
        ]
        subprocess.run(cmd_final, check=True)
    else:
        print("[!] No BGM specified. Outputting video with speech narration only.")
        shutil.copy(str(merged_raw), str(final_out))

    if progress_cb:
        progress_cb(96, "Generating video snapshots...")

    try:
        project_slug = storyboard.get("project_slug") or get_story_slug(storyboard.get("title", ""))
        extract_video_snapshots(str(final_out), project_slug, len(panels))
    except Exception as e:
        print(f"[!] Warning: Failed to extract snapshots: {e}")

    if progress_cb:
        progress_cb(100, "Rendering complete!")

    print(f"[+] Final Video Successfully Created: {final_out}")
    print(f"[+] File Size: {final_out.stat().st_size / (1024*1024):.2f} MB")
    return str(final_out)


def extract_video_snapshots(video_path: str, project_slug: str, num_panels: int = 5):
    """
    Extracts high quality frame snapshots from the rendered video for gallery preview.
    """
    snap_dir = ASSETS_DIR / f"{project_slug}_snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    dur = get_audio_duration(video_path)
    if dur <= 0:
        dur = 30.0
    interval = dur / (num_panels + 1)
    snapshots = []
    for i in range(1, num_panels + 1):
        timestamp = max(0.5, interval * i)
        snap_file = snap_dir / f"snap_panel_{i}.jpg"
        cmd = [
            "ffmpeg", "-y", "-ss", f"{timestamp:.2f}",
            "-i", str(video_path),
            "-vframes", "1", "-q:v", "2",
            str(snap_file)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            snapshots.append({
                "index": i,
                "url": f"/assets/{snap_dir.name}/snap_panel_{i}.jpg",
                "caption": f"PANEL {i} ({timestamp:.1f}s)"
            })
        except Exception as e:
            print(f"[!] Snapshot {i} extraction error: {e}")
    return snapshots


if __name__ == "__main__":
    md_file = WORKSPACE_DIR / "template.md"
    if len(sys.argv) > 1:
        md_file = Path(sys.argv[1])

    print(f"[*] Reading storyboard markdown: {md_file}...")
    content = md_file.read_text(encoding="utf-8")
    parsed = parse_storyboard_markdown(content)
    print(f"[*] Parsed title: {parsed['title']} | Panels: {len(parsed['panels'])}")

    out_file = "science_1.mp4"
    if len(sys.argv) > 2:
        out_file = sys.argv[2]

    compile_full_video(parsed, out_file)
