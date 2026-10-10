#!/usr/bin/env python3
"""
God_Speaks.py - AI Creative Director Agent for Media Studio.
Orchestrates image generation, voice synthesis, motion zoom, and video assembly.
Leaves all existing codebase files completely untouched.
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------
# 0. API KEY RESOLUTION (Supports "KEY" alias & GOOGLE_API_KEY)
# ---------------------------------------------------------------------
def resolve_api_key() -> str:
    leaked_prefix = "AIzaSyB8h"
    for candidate in [
        os.environ.get("GEMINI_API_KEY"),
        os.environ.get("GOOGLE_API_KEY"),
    ]:
        if candidate and not candidate.startswith(leaked_prefix):
            return candidate

    # Fallback: check ~/.bashrc
    bashrc_path = Path.home() / ".bashrc"
    if bashrc_path.exists():
        for m in re.finditer(r'export (?:GEMINI|GOOGLE)_API_KEY=["\'](.*?)["\']', bashrc_path.read_text()):
            if not m.group(1).startswith(leaked_prefix):
                return m.group(1)

    print("[!] ERROR: No valid API key found. Please run 'KEY' in your terminal or set GOOGLE_API_KEY.")
    sys.exit(1)

API_KEY = resolve_api_key()
client = genai.Client(api_key=API_KEY)

# ---------------------------------------------------------------------
# 1. TOOL DEFINITIONS (Calling your existing tools via subprocess)
# ---------------------------------------------------------------------

def generate_scene_image(prompt: str, seed: int = 647328, cfg: float = 0.001) -> str:
    """
    Generates a scene illustration using your proven LCM model (rmbtestLCM_rmbtest4V10.safetensors).
    Returns the file path of the generated PNG.
    """
    output_dir = BASE_DIR / "static" / "novel_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🎨 [AGENT TOOL] Generating image: '{prompt[:60]}...'")
    print(f"   Model: rmbtestLCM | Seed: {seed} | CFG: {cfg:.3f}")

    # Call your ONE_model_cfg.py script in single-image mode
    cmd = [
        sys.executable, str(BASE_DIR / "ONE_model_cfg.py"),
        "--prompt", prompt,
        "--model", "rmbtestLCM_rmbtest4V10.safetensors",
        "--seed", str(seed),
        "--cfg-start", str(cfg),
        "--num-images", "1",
        "--no-video"
    ]
    subprocess.run(cmd, cwd=str(BASE_DIR), check=True)
    
    # Locate generated image
    cfg_str = f"{cfg:.3f}".replace(".", "-")
    img_path = output_dir / f"{seed}_{cfg_str}.png"
    if not img_path.exists():
        # Fallback to 2-decimal legacy formatting if needed
        cfg_str_legacy = f"{cfg:.2f}".replace(".", "-")
        img_path = output_dir / f"{seed}_{cfg_str_legacy}.png"

    print(f"   ✓ Image ready: {img_path}")
    return str(img_path)


def generate_voiceover(text: str, voice: str = "am_adam") -> str:
    """
    Generates spoken audio for God or narration using Kokoro TTS.
    Returns the file path of the generated WAV audio.
    """
    output_dir = BASE_DIR / "static" / "output_videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / "god_voice.wav"
    text_path = output_dir / "god_voice.txt"
    text_path.write_text(text, encoding="utf-8")

    print(f"\n🎙️ [AGENT TOOL] Generating voiceover: \"{text}\" (Voice: {voice})")

    # Call Kokoro TTS
    cmd = [
        "kokoro-tts",
        str(text_path),
        str(audio_path),
        "--voice", voice,
        "--speed", "0.9",
        "--lang", "en-us"
    ]
    try:
        subprocess.run(cmd, cwd=str(BASE_DIR), check=True)
        # Apply a subtle deep reverb/echo with FFmpeg for God's voice
        deep_audio_path = output_dir / "god_voice_echo.wav"
        ffmpeg_reverb = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(audio_path),
            "-af", "aecho=0.8:0.88:60:0.4,bass=g=4",
            str(deep_audio_path)
        ]
        subprocess.run(ffmpeg_reverb, check=True)
        audio_path = deep_audio_path
    except Exception as e:
        print(f"   [!] Kokoro CLI note: {e}")

    print(f"   ✓ Voiceover ready: {audio_path}")
    return str(audio_path)


def create_motion_clip(image_path: str, duration: int = 5) -> str:
    """
    Converts a still image into an HD motion video clip (slow zoom/pan) using FFmpeg.
    Returns the file path of the MP4 clip.
    """
    out_clip = image_path.replace(".png", "_motion.mp4")
    print(f"\n🎬 [AGENT TOOL] Creating motion zoom clip from {image_path} ({duration}s)")

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-loop", "1", "-i", image_path,
        "-vf", "scale=8000:-1,zoompan=z='min(zoom+0.0008,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=512x768",
        "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_clip
    ]
    subprocess.run(cmd, cwd=str(BASE_DIR), check=True)
    print(f"   ✓ Motion clip ready: {out_clip}")
    return out_clip


def assemble_final_video(video_clip: str, audio_path: str, output_filename: str = "God_Speaks_Final.mp4") -> str:
    """
    Merges the motion video clip with the voiceover audio into a finished MP4 movie.
    Returns the final MP4 path.
    """
    output_dir = BASE_DIR / "static" / "output_videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / output_filename

    print(f"\n📦 [AGENT TOOL] Assembling final video into {final_path}...")

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-i", video_clip,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(final_path)
    ]
    subprocess.run(cmd, cwd=str(BASE_DIR), check=True)
    print(f"   ✓ Final movie complete: {final_path}")
    return str(final_path)


TOOL_MAP = {
    "generate_scene_image": generate_scene_image,
    "generate_voiceover": generate_voiceover,
    "create_motion_clip": create_motion_clip,
    "assemble_final_video": assemble_final_video,
}

# ---------------------------------------------------------------------
# 2. AGENT ORCHESTRATION LOOP
# ---------------------------------------------------------------------
def run_director():
    prompt = (
        "Create a Dr Seuss style cartoon video of Eve in the garden of Eden, "
        "the snake climbs a tree and holds an apple. "
        "A voice 'God' says 'Listen you two, that is not a good idea.'"
    )

    print("=" * 65)
    print("🎬 AI STUDIO DIRECTOR: GOD SPEAKS")
    print("=" * 65)
    print(f"User Request: {prompt}\n")

    system_instruction = """
    You are the Director Agent for Media Studio.
    You create animations by directing available tools:
    1. Call generate_scene_image with a detailed Dr Seuss / Robert Crumb prompt (seed 647328, cfg 0.001).
    2. Call generate_voiceover with God's dialogue ('Listen you two, that is not a good idea.').
    3. Call create_motion_clip on the generated image.
    4. Call assemble_final_video to combine the motion clip and voiceover.
    5. Present the final summary to the user when finished.
    """

    chat = client.chats.create(
        model="gemini-3.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[generate_scene_image, generate_voiceover, create_motion_clip, assemble_final_video],
            temperature=0.4,
        )
    )

    response = chat.send_message(prompt)

    # Tool calling loop
    while response.function_calls:
        for call in response.function_calls:
            func_name = call.name
            func_args = call.args
            
            tool_func = TOOL_MAP[func_name]
            result = tool_func(**func_args)

            response = chat.send_message(
                types.Part.from_function_response(
                    name=func_name,
                    response={"result": result}
                )
            )

    print("\n" + "=" * 65)
    print("✨ DIRECTOR FINISHED:")
    print("=" * 65)
    print(response.text)


if __name__ == "__main__":
    run_director()
