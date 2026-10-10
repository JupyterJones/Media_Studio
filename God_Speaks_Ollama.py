#!/usr/bin/env python3
"""
God_Speaks_Ollama.py - AI Creative Director Agent for Media Studio powered by Ollama.
Orchestrates image generation, voice synthesis, motion zoom, and video assembly 100% locally.
Replaces Gemini with local Ollama models (default: llama3.2:3b).
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
import ollama

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------
# 1. TOOL DEFINITIONS (Subprocess execution of Media Studio components)
# ---------------------------------------------------------------------

def generate_scene_image(prompt: str, seed: int = 647328, cfg: float = 0.001) -> str:
    """
    Generates a scene illustration using your proven LCM model (rmbtestLCM_rmbtest4V10.safetensors).
    Returns the file path of the generated PNG.
    """
    output_dir = BASE_DIR / "static" / "novel_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🎨 [AGENT TOOL] Generating image: '{prompt[:60]}...'")
    print(f"   Model: madnessLCMV1_v10 | Seed: {seed} | CFG: {cfg:.3f}")

    cmd = [
        sys.executable, str(BASE_DIR / "ONE_model_cfg.py"),
        "--prompt", prompt,
        "--model", "madnessLCMV1_v10.safetensors",
        "--seed", str(seed),
        "--cfg-start", str(cfg),
        "--num-images", "1",
        "--no-video"
    ]
    subprocess.run(cmd, cwd=str(BASE_DIR), check=True)
    
    cfg_str = f"{cfg:.3f}".replace(".", "-")
    img_path = output_dir / f"{seed}_{cfg_str}.png"
    if not img_path.exists():
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


def assemble_final_video(video_clip: str, audio_path: str, output_filename: str = "God_Speaks_Ollama_Final.mp4") -> str:
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
# 2. OLLAMA AGENT ORCHESTRATOR
# ---------------------------------------------------------------------

def run_director(model_name: str = "llama3.2:3b", user_prompt: str = None):
    if not user_prompt:
        user_prompt = (
            "Create a Dr Seuss style cartoon video of Eve and a large snake in the garden of Eden, the snake climbs a tree and holds an apple. A voice 'God' says 'Listen you two, that is not a good idea.'"
        )

    print("=" * 65)
    print(f"🎬 AI STUDIO DIRECTOR (OLLAMA): {model_name.upper()}")
    print("=" * 65)
    print(f"User Request: {user_prompt}\n")

    system_instruction = (
        "You are the AI Creative Director Agent for Media Studio.\n"
        "Analyze the user's creative request and return a comprehensive production plan in JSON format.\n"
        "The JSON MUST have exactly these keys:\n"
        "  - \"image_prompt\": A detailed Stable Diffusion / LCM visual prompt describing the scene, style (e.g. Dr Seuss, Robert Crumb cartoon), characters, colors, and atmosphere.\n"
        "  - \"dialogue\": The exact spoken line for God or narrator to speak in the voiceover.\n"
        "  - \"voice\": The Kokoro voice name (e.g., \"am_adam\").\n"
        "  - \"seed\": Fixed seed number (e.g., 647328).\n"
        "  - \"cfg\": CFG scale float value (e.g., 0.001).\n"
        "  - \"duration\": Length of the motion clip in seconds (e.g., 5).\n"
        "  - \"output_filename\": The final MP4 filename (e.g., \"God_Speaks_Ollama_Garden_of_Eden2.mp4\").\n"
        "Output ONLY valid JSON."
    )

    print(f"🧠 [DIRECTOR] Consulting Ollama ({model_name}) for production plan...")
    
    try:
        res = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            format="json"
        )
        content = res["message"]["content"]
        plan = json.loads(content)
    except Exception as e:
        print(f"[!] Ollama JSON plan error: {e}. Falling back to default production parameters.")
        plan = {
            "image_prompt": "Whimsical cartoon of Eve in the garden of Eden, snake in a curly tree holding an apple, Dr Seuss style, colorful, expressive line art",
            "dialogue": "Listen you two, that is not a good idea.",
            "voice": "am_adam",
            "seed": 647328,
            "cfg": 0.001,
            "duration": 5,
            "output_filename": "God_Speaks_Ollama_Garden_of_Eden2.mp4"
        }

    # Normalize dialogue
    dialogue = plan.get("dialogue", "Listen you two, that is not a good idea.")
    if isinstance(dialogue, list):
        dialogue = " ".join(dialogue)

    image_prompt = plan.get("image_prompt", user_prompt)
    voice = plan.get("voice", "am_adam")
    seed = int(plan.get("seed", 647328))
    cfg = float(plan.get("cfg", 0.001))
    duration = int(plan.get("duration", 5))
    output_filename = plan.get("output_filename", "God_Speaks_Ollama_Garden_of_Eden2.mp4")

    print("\n📋 [DIRECTOR'S PRODUCTION PLAN]")
    print(f"   • Visual Prompt:   {image_prompt}")
    print(f"   • Dialogue:        \"{dialogue}\"")
    print(f"   • Voice:           {voice}")
    print(f"   • Seed / CFG:      {seed} / {cfg}")
    print(f"   • Duration:        {duration}s")
    print(f"   • Target File:     {output_filename}")
    print("-" * 65)

    # 1. Image Generation
    img_path = generate_scene_image(prompt=image_prompt, seed=seed, cfg=cfg)

    # 2. Voiceover Synthesis
    audio_path = generate_voiceover(text=dialogue, voice=voice)

    # 3. Motion Clip
    clip_path = create_motion_clip(image_path=img_path, duration=duration)

    # 4. Final Movie Assembly
    final_video = assemble_final_video(video_clip=clip_path, audio_path=audio_path, output_filename=output_filename)

    print("\n" + "=" * 65)
    print("✨ OLLAMA DIRECTOR FINISHED:")
    print("=" * 65)
    print(f"🎉 Production Complete! Your movie is ready:")
    print(f"📹 {final_video}\n")
    return final_video


def main():
    parser = argparse.ArgumentParser(description="AI Studio Director powered by local Ollama models.")
    parser.add_argument("--model", type=str, default="llama3.2:3b", help="Ollama model to use (default: llama3.2:3b)")
    parser.add_argument("--prompt", type=str, default=None, help="Custom creative request prompt")
    args = parser.parse_args()

    run_director(model_name=args.model, user_prompt=args.prompt)


if __name__ == "__main__":
    main()
