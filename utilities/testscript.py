#!/usr/bin/env python3

import os
import json
from icecream import ic
from datetime import datetime
import requests
import glob
import subprocess

# =========================
# CONFIG
# =========================
STATE_DIR = "world_state"
IMAGE_DIR = os.path.join(STATE_DIR, "images")
TTS_DIR = os.path.join(STATE_DIR, "tts")
MP4_DIR = os.path.join(STATE_DIR, "mp4")
INTERACTIONS_FILE = os.path.join(STATE_DIR, "interaction_history.json")

KOKORO_TTS_URL = "http://localhost:8880/v1/audio/speech"

MALE_VOICE = "am_adam"
FEMALE_VOICE = "af_heart"
NARRATOR_VOICE = "af_sky"

# =========================
# UTILS
# =========================
def ensure_dirs():
    for d in [STATE_DIR, IMAGE_DIR, TTS_DIR, MP4_DIR]:
        os.makedirs(d, exist_ok=True)

def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default if default is not None else {}

def clean_text(text: str) -> str:
    return text.replace("*", "").replace("\n", " ").replace("\r", "").strip()

def get_audio_duration(path):
    try:
        result = subprocess.run(
            ["ffprobe", "-i", path, "-show_entries", "format=duration",
             "-v", "quiet", "-of", "csv=p=0"],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except:
        return 0

# =========================
# TTS GENERATION
# =========================
def generate_tts(text: str, filename_base: str, voice: str):
    text = clean_text(text)
    if not text: return None
    
    mp3_path = os.path.join(TTS_DIR, f"{filename_base}_{voice}.mp3")
    try:
        resp = requests.post(KOKORO_TTS_URL, json={"input": text, "voice": voice}, timeout=300)
        resp.raise_for_status()
        with open(mp3_path, "wb") as f:
            f.write(resp.content)
        return mp3_path
    except Exception as e:
        ic("TTS generation failed:", e)
        return None

def concat_mp3s(mp3_list, output_path):
    list_file = os.path.join(TTS_DIR, "mp3_list.txt")
    with open(list_file, "w") as f:
        for mp3 in mp3_list:
            if mp3: f.write(f"file '{os.path.abspath(mp3)}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path], check=True, capture_output=True)
    return output_path

# =========================
# VIDEO PROCESSING
# =========================
def create_video_segment(image_path, audio_path, output_path):
    """Creates a single MP4 segment from one image and one audio file."""
    duration = get_audio_duration(audio_path)
    if duration <= 0: duration = 1.0 # Fallback
    
    ic(f"Creating segment: {image_path} for {duration}s")
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(duration),
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=512:768", # Ensure uniform size for concat
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def concat_videos(video_list, final_output):
    """Joins the video segments into one final file."""
    list_file = os.path.join(MP4_DIR, "video_list.txt")
    with open(list_file, "w") as f:
        for v in video_list:
            f.write(f"file '{os.path.abspath(v)}'\n")
    
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", final_output
    ], check=True, capture_output=True)

# =========================
# MAIN
# =========================
def main():
    ensure_dirs()

    history = load_json(INTERACTIONS_FILE, [])
    if not history:
        ic("No interactions found.")
        return

    # 1. Get the last 3 entries
    last_entries = history[-3:]
    
    # 2. Get the last 3 images (sorted by creation time/name)
    all_images = sorted(glob.glob(os.path.join(IMAGE_DIR, "*_512x768.jpg")))
    last_images = all_images[-len(last_entries):]

    if not last_images:
        ic("No images found.")
        return

    video_segments = []

    # 3. Process each entry as a separate segment
    for i, (entry, img_path) in enumerate(zip(last_entries, last_images)):
        ic(f"Processing Segment {i+1}")
        
        safe_name = f"segment_{i}_{datetime.now().strftime('%H%M%S')}"
        
        # Generate TTS for parts
        a_mp3 = generate_tts(entry.get("action", ""), f"{safe_name}_a", MALE_VOICE)
        r_mp3 = generate_tts(entry.get("reflection", ""), f"{safe_name}_r", FEMALE_VOICE)
        p_mp3 = generate_tts(entry.get("image_prompt", ""), f"{safe_name}_p", NARRATOR_VOICE)
        
        # Combine TTS for this specific entry
        segment_audio = os.path.join(TTS_DIR, f"{safe_name}_combined.mp3")
        concat_mp3s([a_mp3, r_mp3, p_mp3], segment_audio)
        
        # Create mini-video for this entry
        segment_video = os.path.join(MP4_DIR, f"{safe_name}.mp4")
        create_video_segment(img_path, segment_audio, segment_video)
        
        video_segments.append(segment_video)

    # 4. Final Concatenation
    if video_segments:
        final_video_name = os.path.join(MP4_DIR, f"final_narration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        concat_videos(video_segments, final_video_name)
        ic("FINAL VIDEO CREATED:", final_video_name)

if __name__ == "__main__":
    main()
'''

### Key Improvements Made:
1.  **Segmented Creation:** Instead of trying to build one giant command, it builds a small `.mp4` for each history entry. This ensures that **Image 1** stays on screen exactly as long as the **Entry 1 audio** takes to play.
2.  **Uniform Scaling:** Added `-vf "scale=512:768"` inside the video creation. FFmpeg often fails to concatenate videos if they are even 1 pixel different in size; this forces them to match.
3.  **Zip Mapping:** Used `zip(last_entries, last_images)` to ensure the $N^{th}$ image always matches the $N^{th}$ text entry.
4.  **FFmpeg Robustness:** Added `-tune stillimage` and `-pix_fmt yuv420p` to ensure the resulting MP4 is compatible with standard video players (like QuickTime or Windows Media Player).
5.  **Clean Duration Handling:** It calculates the audio length for every segment individually using `ffprobe`.
'''