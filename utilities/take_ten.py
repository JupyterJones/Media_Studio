#!/usr/bin/env python3
import os
import json
import subprocess
import requests
from random import sample, choice
from icecream import ic
import re
import uuid
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, ImageClip, AudioFileClip
import glob
import random
import shutil

# ---------------- CONFIG ----------------

IMAGE_DIR = "static/projects"
OUTPUT_DIR = "/home/jack/Desktop/HDD500/DOCKER/static/projects"
NUM_IMAGES = 10
TRANSITION_DURATION = 3.5  # seconds
VOICES = [
    'bf_alice', 'bf_emma', 'bf_lily', 'bf_v0emma', 'bf_v0isabella',
    'af_alloy', 'af_aoede', 'af_bella', 'af_heart', 'af_jadzia',
    'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river',
    'af_sarah', 'af_sky', 'af_v0', 'af_v0bella', 'af_v0irulan',
    'af_v0nicole', 'af_v0sarah', 'af_v0sky', 'am_adam', 'am_echo',
    'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx',
    'am_puck', 'am_santa', 'am_v0adam', 'am_v0gurney', 'am_v0michael',
    'bm_daniel', 'bm_fable'
]
ASSISTANT_VOICE = VOICES[1]
TTS_API_URL = "http://localhost:8880/v1/audio/speech"
HEADERS = {"Content-Type": "application/json"}
STORY_FILE = "/home/jack/Desktop/DOCKER/static/projects/text_1764305709.txt"

# ---------------- UTILITIES ----------------

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        ic(f"Created directory: {path}")

def clean_text_for_tts(text):
    ic("Cleaning AI text for TTS...")
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'["*_\[\]{}<>]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def sanitize_filename(text, max_length=20):
    base = text.strip()[:max_length]
    base = re.sub(r'\W+', '_', base)
    return base or "output"

def get_audio_duration(audio_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        duration = float(result.stdout.strip())
        ic(f"Duration of {audio_path}: {duration} seconds")
        return duration
    except Exception as e:
        ic(f"Failed to get audio duration: {e}")
        return 0

def generate_tts(text):
    filename = sanitize_filename(text) + f"_{ASSISTANT_VOICE}.mp3"
    ic(filename)
    mp3_path = os.path.join(OUTPUT_DIR, filename)
    payload = {"input": text, "voice": ASSISTANT_VOICE}

    try:
        ic(f"Sending TTS request for first 40 chars:\n{text[:40]}...")
        response = requests.post(TTS_API_URL, json=payload, headers=HEADERS, timeout=380)

        if response.status_code == 200:
            with open(mp3_path, 'wb') as f:
                f.write(response.content)
            ic(f"TTS MP3 saved: {mp3_path}")

            # Convert to M4A
            m4a_path = mp3_path.replace(".mp3", ".m4a")
            subprocess.run([
                "ffmpeg", "-y", "-i", mp3_path, "-c:a", "aac", "-b:a", "192k", "-strict", "-2", m4a_path
            ], check=True)
            ic(f"Converted to M4A: {m4a_path}")

            # Append 1 second silence to prevent stutter at end
            silence_path = os.path.join(OUTPUT_DIR, "silence.m4a")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-t", "1", "-i", "aevalsrc=0",
                "-c:a", "aac", "-b:a", "192k", silence_path
            ], check=True)

            padded_audio_path = os.path.join(OUTPUT_DIR, filename.replace(".mp3", "_padded.m4a"))
            subprocess.run([
                "ffmpeg", "-y", "-i", f"concat:{m4a_path}|{silence_path}",
                "-c", "copy", padded_audio_path
            ], check=True)
            ic(f"Padded audio with 1s silence: {padded_audio_path}")

            return padded_audio_path
        else:
            ic(f"TTS error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        ic(f"TTS request failed: {e}")
        return None

def add_title_image(video_path, hex_color="#A52A2A"):
    directory_path = "temp"
    ensure_dir(directory_path)

    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    title_image_path = "/home/jack/Desktop/HDD500/DOCKER/static/assets/512x768_Title_Image02.png"
    padded_size = (width + 40, height + 40)
    x_position = (padded_size[0] - video_clip.size[0]) / 2
    y_position = (padded_size[1] - video_clip.size[1]) / 2

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    rgb_tuple = (r, g, b)

    background = ColorClip(padded_size, color=rgb_tuple)
    padded_video_clip = CompositeVideoClip([background, video_clip.set_position((x_position, y_position))])
    padded_video_clip = padded_video_clip.set_duration(video_clip.duration)

    title_image = ImageClip(title_image_path).set_duration(video_clip.duration).resize(padded_video_clip.size).set_position((0, -5))
    composite_clip = CompositeVideoClip([padded_video_clip, title_image])

    if not composite_clip.audio:
        mp3_files = glob.glob("/mnt/HDD500/collections/Music/*.mp3")
        random.shuffle(mp3_files)
        mp_music = random.choice(mp3_files)
        music_clip = AudioFileClip(mp_music).subclip(0, 40)
        fade_duration = 1.0
        music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(fade_duration)
        composite_clip = composite_clip.set_audio(music_clip)
    uid = str(uuid.uuid4())
    output_path = f"static/projects/{uid}final_output3.mp4"
    composite_clip.write_videofile(output_path)
    mp4_file = f"/mnt/HDD500/collections/vids/Ready_Post_{uid}.mp4"
    ic(mp4_file)
    shutil.copyfile(output_path, mp4_file)
    return output_path

# ---------------- MAIN ----------------

ensure_dir(OUTPUT_DIR)
if not os.path.exists(STORY_FILE):
    raise FileNotFoundError(f"{STORY_FILE} not found.")

with open(STORY_FILE, "r", encoding="utf-8") as f:
    text = f.read()

cleaned_text = clean_text_for_tts(text)
AUDIO_OUTPUT = generate_tts(cleaned_text)
if not AUDIO_OUTPUT:
    raise RuntimeError("TTS generation failed.")

all_images = glob.glob(os.path.join(IMAGE_DIR, "*.jpg")) + glob.glob(os.path.join(IMAGE_DIR, "*.png"))
if len(all_images) < NUM_IMAGES:
    raise ValueError(f"Not enough images in {IMAGE_DIR}. Found {len(all_images)}, need {NUM_IMAGES}")

selected_images = sample(all_images, NUM_IMAGES)
ic(f"Selected images: {selected_images}")

audio_duration = get_audio_duration(AUDIO_OUTPUT)
duration_per_image = (audio_duration + (NUM_IMAGES - 1) * TRANSITION_DURATION) / NUM_IMAGES
ic(f"Audio duration: {audio_duration}s, per image duration: {duration_per_image}s")

inputs = []
for img in selected_images:
    inputs += ["-loop", "1", "-t", f"{duration_per_image}", "-i", os.path.abspath(img)]

filters = []
for i in range(NUM_IMAGES):
    filters.append(f"[{i}:v]scale=-2:768,pad=512:768:(512-iw)/2:(768-ih)/2[v{i}]")

in_stream = "[v0]"
for i in range(NUM_IMAGES - 1):
    out_stream = f"[out{i}]"
    transition = choice([
        "fade", "wipeleft", "wiperight", "wipeup", "wipedown",
        "slideleft", "slideright", "slideup", "slidedown", "dissolve", "pixelize"
    ])
    offset = (duration_per_image * (i + 1)) - TRANSITION_DURATION
    filters.append(f"{in_stream}[v{i+1}]xfade=transition={transition}:duration={TRANSITION_DURATION}:offset={offset}{out_stream}")
    in_stream = out_stream

filter_complex = ";".join(filters)
final_label = in_stream

VIDEO_OUTPUT = os.path.join(OUTPUT_DIR, f"mushrooms_slideshow_{uuid.uuid4().hex[:6]}.mp4")
ffmpeg_cmd = ["ffmpeg", "-y"] + inputs + ["-i", AUDIO_OUTPUT,
    "-filter_complex", filter_complex,
    "-map", final_label,
    "-map", f"{len(selected_images)}:a",
    "-pix_fmt", "yuv420p",
    "-shortest",
    "-c:a", "aac",
    VIDEO_OUTPUT
]

ic(f"Running FFmpeg command...")
subprocess.run(ffmpeg_cmd, check=True)
video_path = VIDEO_OUTPUT
NEW_VID = add_title_image(video_path, hex_color="#A52A2A")
ic(f"Video created successfully at: {NEW_VID}")
