#!/usr/bin/env python3

import os
import sys
import random
import asyncio
import argparse
from pathlib import Path
import shutil
import requests
import httpx
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, ColorClip, VideoFileClip
)
from moviepy.video.fx.all import fadein, fadeout
from icecream import ic
import uuid
# --- CONFIGURATION ---
# API Endpoints
PHI_URL = "http://localhost:11434/api/generate"
TTS_API_URL = "http://localhost:8880/v1/audio/speech"
TTS_VOICE = "bf_emma" # Or any other voice you prefer

# File & Directory Settings
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}
OUTPUT_DIR = Path("./static/projects/")
OUTPUT_VIDEO_FILENAME = "static/projects/story_video1a.mp4"
OUTPUT_AUDIO_FILENAME = "static/projects/story_audio1a.mp3"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --- MODEL INITIALIZATION ---
blip_processor = None
blip_model = None

def init_models():
    """Load the heavy AI models into memory."""
    global blip_processor, blip_model
    if blip_model is None:
        ic("Loading BLIP model for image captioning...")
        blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        ic("✅ BLIP model loaded.")

# --- CORE FUNCTIONS ---

def select_random_images(directory: Path, num_images: int = 10) -> list[Path]:
    """Scans a directory and selects a random number of images."""
    ic(f"Scanning {directory} for images...")
    image_files = [p for p in directory.glob("*") if p.suffix.lower() in IMAGE_EXTENSIONS]

    if not image_files:
        print(f"❌ Error: No images found in directory: {directory}")
        sys.exit(1)

    if len(image_files) < num_images:
        ic(f"⚠️ Warning: Found only {len(image_files)} images. Using all of them.")
        return image_files

    selected = random.sample(image_files, num_images)
    ic(f"Selected {len(selected)} random images.")
    return selected

def generate_captions(image_paths: list[Path]) -> list[str]:
    """Generates a raw caption for each image using the BLIP model."""
    captions = []
    for i, image_path in enumerate(image_paths):
        ic(f"Generating caption for image {i+1}/{len(image_paths)}: {image_path.name}")
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = blip_processor(image, return_tensors="pt")
            out = blip_model.generate(**inputs)
            caption = blip_processor.decode(out[0], skip_special_tokens=True)
            ic(f"  > Raw Caption: '{caption}'")
            captions.append(caption)
        except Exception as e:
            ic(f"❌ Failed to process image {image_path.name}: {e}")
            captions.append(f"An image of an unknown entity.") # Fallback caption
    return captions

def generate_story(captions: list[str]) -> str:
    """Uses raw captions to generate a cohesive story with Phi."""
    ic("Crafting a story with Phi model...")
    scenes = "\n".join([f"- Scene {i+1}: {caption}" for i, caption in enumerate(captions)])
    prompt = (
        f"You are a master sci-fi storyteller. Weave a single, short, coherent narrative in the style of Edgar Allen Poe, that connects the following scenes. "
        f"Make the story poetic, mysterious, and immersive. Do not list the scenes; write a flowing story, in the style of Edgar Allen Poe.\n\n"
        f"Scenes:\n{scenes}\n\nStory:"
    )

    payload = {
        "model": "phi:latest",
        "prompt": prompt,
        "stream": False,
        "temperature": 0.75,
    }

    try:
        response = requests.post(PHI_URL, json=payload, timeout=500)
        response.raise_for_status()
        story = response.json().get("response", "").strip()
        ic("✅ Story generated successfully.")
        ic(f"  > Story Snippet: '{story[:150]}...'")
        return story
    except Exception as e:
        ic(f"❌ Failed to generate story with Phi: {e}")
        return "In the silence of the void, memories flicker and fade. A story lost to time."

async def synthesize_audio(story: str, output_path: Path) -> Path:
    """Converts the story text to an MP3 audio file using a TTS API."""
    ic("Synthesizing audio from story text...")
    payload = {
        "model": "kokoro",
        "voice": TTS_VOICE,
        "input": story,
        "response_format": "mp3"
    }

    try:
        async with httpx.AsyncClient(timeout=400.0) as client:
            response = await client.post(TTS_API_URL, json=payload)
            response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        ic(f"✅ Audio saved to {output_path}")
        return output_path
    except Exception as e:
        ic(f"❌ Failed to synthesize audio: {e}")
        sys.exit(1)

def create_video(image_paths: list[Path], audio_path: Path, output_path: Path):
    """Creates a video from images and an audio file with transitions."""
    ic("Assembling the final video...")
    try:
        audio_clip = AudioFileClip(str(audio_path))
        audio_duration = audio_clip.duration
        num_images = len(image_paths)
        
        # We'll use portrait 720p as a standard size
        screen_size = (512, 768)
        
        # Duration for each clip to be on screen, accounting for transitions
        transition_duration = 1.5 # seconds for fade
        
        # Calculate how long each image is fully visible
        # Total duration = (visible_duration * num_images) + (transition_duration * (num_images - 1))
        # This is complex. Let's simplify: each clip "slot" has a fixed time.
        slot_duration = audio_duration / num_images
        
        ic(f"  > Audio duration: {audio_duration:.2f}s")
        ic(f"  > Time slot per image: {slot_duration:.2f}s")

        video_clips = []
        current_time = 0
        
        for i, image_path in enumerate(image_paths):
            # Create a clip that is long enough for its slot plus the transition
            clip_duration = slot_duration + transition_duration
            
            clip = (ImageClip(str(image_path))
                    .set_duration(clip_duration)
                    .resize(height=screen_size[1]) # Resize to fit height
                    .set_position(('center', 'center')))
            
            # Apply fade in and fade out
            # The fadeout of one clip overlaps with the fadein of the next
            clip = clip.fx(fadein, transition_duration).fx(fadeout, transition_duration)
            
            # Set the start time. Subsequent clips start earlier to overlap the fades.
            clip = clip.set_start(current_time)
            
            video_clips.append(clip)
            
            current_time += slot_duration

        # Create a black background for the entire duration
        background = ColorClip(size=screen_size, color=(0, 0, 0), duration=audio_duration)
        
        # Composite all clips onto the background
        final_video = CompositeVideoClip([background] + video_clips)
        final_video = final_video.set_audio(audio_clip)

        ic(f"Writing video file to {output_path}...")
        final_video.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            fps=24,
            temp_audiofile='temp-audio.m4a', 
            remove_temp=True
        )
        ic(f"✅ Video creation complete!")

    except Exception as e:
        ic(f"❌ Failed to create video: {e}")
        sys.exit(1)

# --- ADD TITLE --------

def add_title_image(video_path, hex_color="#A52A2A"):
    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    padded_size = (width + 60, height + 70)
    x_offset = (padded_size[0] - width) // 2
    y_offset = (padded_size[1] - height) // 2
    r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
    bg = ColorClip(padded_size, color=(r, g, b)).set_duration(video_clip.duration)
    padded = CompositeVideoClip([bg, video_clip.set_position((x_offset, y_offset))])
    title_path = "static/assets/talks.png"
    title = ImageClip(title_path).resize(padded.size).set_duration(video_clip.duration)
    final = CompositeVideoClip([padded, title])
    uid = str(uuid.uuid4())
    output_path = f"static/projects/{uid}_final.mp4"
    final.write_videofile(output_path, fps=24)
    shutil.copy(output_path, f"/home/jack/Desktop/DOCKER/static/projects/Ready_Post_{uid}.mp4")
    return output_path


# --- MAIN EXECUTION ---

async def main():
    parser = argparse.ArgumentParser(
        description="Create a narrated sci-fi video story from a directory of images.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "image_directory",
        type=Path,
        help="The directory containing the images to use for the story."
    )
    args = parser.parse_args()

    image_dir = args.image_directory
    if not image_dir.is_dir():
        print(f"❌ Error: Directory not found at '{image_dir}'")
        sys.exit(1)

    # 1. Initialize AI Models
    init_models()

    # 2. Select Images
    selected_images = select_random_images(image_dir, num_images=8)

    # 3. Generate Captions
    raw_captions = generate_captions(selected_images)

    # 4. Generate Story
    story = generate_story(raw_captions)
    if not story:
        print("❌ Aborting due to failure in story generation.")
        sys.exit(1)
    
    # 5. Synthesize Audio
    audio_file_path = OUTPUT_DIR / OUTPUT_AUDIO_FILENAME
    await synthesize_audio(story, audio_file_path)

    # 6. Create Video
    video_file_path = OUTPUT_DIR / OUTPUT_VIDEO_FILENAME
    create_video(selected_images, audio_file_path, video_file_path)
    video_path = (f"{video_file_path.resolve()}")
    add_title_image(video_path, hex_color="#A52A2A")
    print("\n🎉 --- Story Generation Complete --- 🎉")
    print(f"Final video saved to: {video_file_path.resolve()}")

if __name__ == "__main__":
    asyncio.run(main())