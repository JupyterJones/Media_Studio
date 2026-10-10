#!/usr/bin/env python3
"""
Build V3 Local: 100% Local Pipeline using local Stable Diffusion LCM
Non-destructive: Writes to assets/panels_v3, assets/audio_v3, and science_v3.mp4.
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
import torch
from diffusers import StableDiffusionPipeline, LCMScheduler

import scifi_engine

WORKSPACE_DIR = Path(__file__).resolve().parent
PANELS_V3_DIR = WORKSPACE_DIR / "assets" / "panels_v3"
AUDIO_V3_DIR = WORKSPACE_DIR / "assets" / "audio_v3"
SNAPSHOTS_V3_DIR = WORKSPACE_DIR / "assets" / "snapshots_v3"
TEMP_V3_DIR = WORKSPACE_DIR / "temp_v3"
OUTPUT_V3_MP4 = WORKSPACE_DIR / "science_v3.mp4"

CHECKPOINT_PATH = Path("/home/jack/Desktop/Comfy-UI/models/checkpoints/dreamshaper_8LCM.safetensors")

for d in [PANELS_V3_DIR, AUDIO_V3_DIR, SNAPSHOTS_V3_DIR, TEMP_V3_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Maximize multi-threaded CPU performance
torch.set_num_threads(8)


def load_local_sd_pipeline():
    print(f"[*] [LOCAL SD] Loading checkpoint: {CHECKPOINT_PATH.name}...")
    start_t = time.time()
    pipe = StableDiffusionPipeline.from_single_file(
        str(CHECKPOINT_PATH),
        torch_dtype=torch.float32,
        safety_checker=None
    )
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.to("cpu")
    pipe.enable_attention_slicing()
    print(f"[+] [LOCAL SD] Model loaded in {time.time() - start_t:.1f}s")
    return pipe


def generate_local_panels(storyboard, pipe, steps=4):
    print(f"\n[*] [LOCAL SD] Generating {len(storyboard['panels'])} panels with local Stable Diffusion...")
    for p in storyboard["panels"]:
        idx = p["index"]
        out_img = PANELS_V3_DIR / f"panel_{idx}.jpg"
        p["image_path"] = str(out_img)

        # Check if already generated
        if out_img.exists() and out_img.stat().st_size > 10000:
            print(f"[*] Panel {idx} already exists at {out_img.name}, skipping.")
            continue

        prompt = p["image_prompt"]
        print(f"\n--- [PANEL {idx}/5 LOCAL SD GENERATION] ---")
        print(f"Prompt: {prompt}")
        print(f"Steps: {steps} | CFG: 1.5 | Model: {CHECKPOINT_PATH.name}")

        t0 = time.time()
        generator = torch.Generator("cpu").manual_seed(42 + idx * 100)
        image = pipe(
            prompt=prompt,
            negative_prompt="blurry, low quality, artifacts, watermark, deformed, noisy",
            num_inference_steps=steps,
            guidance_scale=1.5,
            width=512,
            height=512,
            generator=generator
        ).images[0]

        image.save(str(out_img), quality=95)
        print(f"[+] Panel {idx} generated & saved in {time.time() - t0:.1f}s -> {out_img.name}")


def generate_v3_audio(storyboard):
    print("\n[*] [KOKORO TTS] Preparing V3 audio clips...")
    for p in storyboard["panels"]:
        idx = p["index"]
        p["audio_path"] = str(AUDIO_V3_DIR / f"panel_{idx}.wav")
        # Reuse if exists in audio_v3 or synthesize
        if not os.path.exists(p["audio_path"]):
            existing = WORKSPACE_DIR / "assets" / "audio" / f"panel_{idx}.wav"
            if existing.exists():
                shutil.copy(str(existing), p["audio_path"])
                print(f"[+] Synced audio for Panel {idx}")
            else:
                scifi_engine.synthesize_panel_audio(p)


def render_v3_video(storyboard):
    print(f"\n[*] [COMPOSITOR] Compiling science_v3.mp4 with 100% local assets...")
    
    clip_paths = []
    for p in storyboard["panels"]:
        clip_path = str(TEMP_V3_DIR / f"clip_panel_{p['index']}.mp4")
        # Override overlay path to temp_v3
        scifi_engine.TEMP_DIR = TEMP_V3_DIR
        scifi_engine.render_panel_clip(p, storyboard.get("title", "Aurora Rising V3"), clip_path)
        clip_paths.append(clip_path)

    concat_txt = TEMP_V3_DIR / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{os.path.abspath(cp)}'\n")

    merged_raw = TEMP_V3_DIR / "merged_raw.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt), "-c", "copy", str(merged_raw)
    ], check=True)

    total_dur = scifi_engine.get_audio_duration(str(merged_raw))
    bgm_path = scifi_engine.find_matching_bgm(storyboard.get("bgm", "Shadows"))
    
    print(f"[*] Mixing soundtrack: {os.path.basename(bgm_path)}...")
    fade_out_start = max(0.0, total_dur - 3.5)
    filter_audio = (
        f"[1:a]aloop=loop=-1:size=2e+09,volume=0.22,"
        f"afade=t=in:ss=0:d=1.5,afade=t=out:st={fade_out_start:.2f}:d=3.5[bgm]; "
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(merged_raw),
        "-i", str(bgm_path),
        "-filter_complex", filter_audio,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
        str(OUTPUT_V3_MP4)
    ]
    subprocess.run(cmd, check=True)
    print(f"\n🎉 [SUCCESS] 100% Local Stable Diffusion Video Created: {OUTPUT_V3_MP4}")
    print(f"Size: {OUTPUT_V3_MP4.stat().st_size / (1024*1024):.2f} MB | Duration: {total_dur:.1f}s")


def extract_v3_snapshots():
    for i, t in enumerate(["00:00:04", "00:00:18", "00:00:28", "00:00:40", "00:00:50"], 1):
        out_snap = SNAPSHOTS_V3_DIR / f"snap_panel{i}_v3.jpg"
        subprocess.run([
            "ffmpeg", "-y", "-ss", t, "-i", str(OUTPUT_V3_MP4),
            "-frames:v", "1", str(out_snap)
        ], capture_output=True)


if __name__ == "__main__":
    md_path = WORKSPACE_DIR / "TEMPLATEv3.md"
    content = md_path.read_text(encoding="utf-8")
    storyboard = scifi_engine.parse_storyboard_markdown(content)
    
    pipe = load_local_sd_pipeline()
    generate_local_panels(storyboard, pipe, steps=4)
    del pipe
    
    generate_v3_audio(storyboard)
    render_v3_video(storyboard)
    extract_v3_snapshots()
    print("\n✅ All V3 local tasks complete!")
