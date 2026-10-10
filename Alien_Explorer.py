#!/usr/bin/env python3
"""
Alien_Explorer.py - Dual-Axis SLERP + CFG Fusion Studio
Demonstrates the combined power of:
  1. SLERP: Smooth spherical interpolation from Desert Sand Dunes -> Tropical Jungle Temple
  2. Dynamic CFG "Dream Dip": Dips into the 0.001 psychedelic dream space at the midpoint
     before re-crystallizing into the dense jungle temple.

Compatible with the universal Flipbook player (live_slerp.html).
Leaves all existing codebase files completely untouched.
"""

import os
import sys
import json
import shutil
import signal
import tempfile
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import torch
from diffusers import StableDiffusionPipeline, LCMScheduler, AutoencoderTiny

# ---------------------------------------------------------------------
# Signal Handling & Hardware Setup
# ---------------------------------------------------------------------
def exit_gracefully(signum, frame):
    print("\n[*] Clean exit requested. Exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
torch.set_num_threads(4)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "static" / "novel_images"
TEMP_EXP_DIR = BASE_DIR / "static" / "temp_exp"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_EXP_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Default Prompts & Settings
# ---------------------------------------------------------------------
DEFAULT_PROMPT_A = (
    "Masterpiece, abstract line art illustration, an alien traveler wandering vast rolling desert sand dunes, "
    "strange twin suns in the sky, style Dr. Seuss and Robert Crumb, weird hallucinations, primary colors, "
    "splatter paint, spiraled twisted dunes, (Detailed:1.45),(Detailed background:1.4)"
)

DEFAULT_PROMPT_B = (
    "Masterpiece, abstract line art illustration, an alien explorer discovering an ancient stone temple in a dense "
    "tropical jungle, massive glowing ruins overgrown with spiraled twisted vines, style Dr. Seuss and Robert Crumb, "
    "weird creatures in trees, primary colors, splatter paint, (Detailed:1.45),(Detailed background:1.4)"
)

DEFAULT_NEGATIVE = "blurry, ugly, oversaturated, deformed, watermark, low quality"
DEFAULT_MODEL = "rmbtestLCM_rmbtest4V10.safetensors"
DEFAULT_SEED = 647328

# ---------------------------------------------------------------------
# Path Resolvers
# ---------------------------------------------------------------------
def resolve_model_path(model_name: str) -> str:
    cand_dirs = [
        Path("/media/jack/USB_USBSSD/models/checkpoints"),
        BASE_DIR / "models" / "checkpoints",
        BASE_DIR / "models"
    ]
    for d in cand_dirs:
        p = d / model_name
        if p.exists():
            return str(p)
        p_ext = d / f"{model_name}.safetensors"
        if p_ext.exists():
            return str(p_ext)
    return model_name

def resolve_taesd_vae() -> str:
    cand_dirs = [
        BASE_DIR / "models" / "vae" / "taesd",
        BASE_DIR / "models" / "vae" / "taesd.safetensors",
        BASE_DIR / "models" / "vae",
    ]
    for p in cand_dirs:
        if p.exists():
            return str(p)
    return None

def resolve_lora_path() -> str:
    cand = BASE_DIR / "models" / "loras" / "more_details.safetensors"
    return str(cand) if cand.exists() else None

# ---------------------------------------------------------------------
# Chunked Long-Prompt Encoding
# ---------------------------------------------------------------------
def encode_chunked(tokenizer, text_encoder, prompt):
    raw_tokens = tokenizer(prompt, padding=False, truncation=False, return_tensors="pt").input_ids[0]
    bos, eos = raw_tokens[0:1], raw_tokens[-1:]
    content = raw_tokens[1:-1]

    if len(raw_tokens) <= 77:
        inputs = tokenizer(prompt, padding="max_length", max_length=77, truncation=True, return_tensors="pt")
        with torch.no_grad():
            emb = text_encoder(inputs.input_ids.to(text_encoder.device))[0]
        return emb, 1

    chunks = [content[i:i+75] for i in range(0, max(1, len(content)), 75)]
    embs = []
    for c in chunks:
        t = torch.cat([bos, c, eos])
        pad_len = 77 - len(t)
        if pad_len > 0:
            t = torch.nn.functional.pad(t, (0, pad_len), value=tokenizer.pad_token_id)
        with torch.no_grad():
            embs.append(text_encoder(t.unsqueeze(0).to(text_encoder.device))[0])

    return torch.cat(embs, dim=1), len(chunks)

def encode_empty_chunk(tokenizer, text_encoder):
    inputs = tokenizer("", padding="max_length", max_length=77, truncation=True, return_tensors="pt")
    with torch.no_grad():
        return text_encoder(inputs.input_ids.to(text_encoder.device))[0]

def encode_matching_negative(tokenizer, text_encoder, negative_prompt, target_chunks):
    neg_tokens = tokenizer(negative_prompt, padding=False, truncation=False, return_tensors="pt").input_ids[0]
    bos, eos = neg_tokens[0:1], neg_tokens[-1:]
    content = neg_tokens[1:-1]

    embs = []
    for _ in range(target_chunks):
        c = content[:75] if len(content) else content
        t = torch.cat([bos, c, eos])
        pad_len = 77 - len(t)
        if pad_len > 0:
            t = torch.nn.functional.pad(t, (0, pad_len), value=tokenizer.pad_token_id)
        with torch.no_grad():
            embs.append(text_encoder(t.unsqueeze(0).to(text_encoder.device))[0])
    return torch.cat(embs, dim=1)

# ---------------------------------------------------------------------
# Spherical Linear Interpolation (SLERP)
# ---------------------------------------------------------------------
def slerp(v0: torch.Tensor, v1: torch.Tensor, t: float, eps: float = 1e-7) -> torch.Tensor:
    t_val = float(t)
    if t_val <= 0.0:
        return v0
    if t_val >= 1.0:
        return v1

    v0_norm = v0 / (torch.norm(v0, dim=-1, keepdim=True) + eps)
    v1_norm = v1 / (torch.norm(v1, dim=-1, keepdim=True) + eps)

    dot = torch.clamp((v0_norm * v1_norm).sum(dim=-1, keepdim=True), -1.0, 1.0)
    theta_0 = torch.acos(dot)
    sin_theta_0 = torch.sin(theta_0)

    is_collinear = sin_theta_0.abs() < 1e-5
    theta_t = theta_0 * t_val
    sin_theta_t = torch.sin(theta_t)
    sin_theta_0_minus_t = torch.sin(theta_0 - theta_t)

    s0 = sin_theta_0_minus_t / (sin_theta_0 + eps)
    s1 = sin_theta_t / (sin_theta_0 + eps)

    res_slerp = s0 * v0 + s1 * v1
    res_lerp = (1.0 - t_val) * v0 + t_val * v1
    return torch.where(is_collinear, res_lerp, res_slerp)

# ---------------------------------------------------------------------
# Dynamic CFG Curve Calculator
# ---------------------------------------------------------------------
def calculate_cfg(t: float, mode: str, cfg_min: float, cfg_max: float) -> float:
    """
    Calculates CFG value at time t [0.0, 1.0]:
    - 'dip': The Dream Dip! Starts at cfg_max, dives down to cfg_min at t=0.5, returns to cfg_max.
    - 'sweep': Linear sweep from cfg_min to cfg_max.
    - 'fixed': Fixed at cfg_min across all frames.
    """
    if mode == "dip":
        # Parabolic dip: 4 * (t - 0.5)^2 is 1.0 at t=0, 0.0 at t=0.5, and 1.0 at t=1
        factor = 4.0 * ((t - 0.5) ** 2)
        return round(cfg_min + (cfg_max - cfg_min) * factor, 4)
    elif mode == "sweep":
        return round(cfg_min + (cfg_max - cfg_min) * t, 4)
    else: # fixed
        return cfg_min

# ---------------------------------------------------------------------
# Video Compiler (FFmpeg)
# ---------------------------------------------------------------------
def compile_video(image_paths: list[str], output_path: str, fps: int = 8) -> bool:
    if not image_paths:
        return False
    temp_dir = tempfile.mkdtemp(prefix="alien_slerp_")
    try:
        for idx, img in enumerate(image_paths):
            sym = os.path.join(temp_dir, f"frame_{idx:05d}.png")
            try:
                os.symlink(os.path.abspath(img), sym)
            except Exception:
                shutil.copyfile(img, sym)

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-framerate", str(fps),
            "-i", os.path.join(temp_dir, "frame_%05d.png"),
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", "-crf", "18",
            output_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ---------------------------------------------------------------------
# Main Execution Loop
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Alien Explorer: SLERP + CFG Dynamic Dream Engine")
    parser.add_argument("-a", "--prompt-a", default=DEFAULT_PROMPT_A, help="Prompt A (Desert Dunes)")
    parser.add_argument("-b", "--prompt-b", default=DEFAULT_PROMPT_B, help="Prompt B (Jungle Temple)")
    parser.add_argument("-s", "--seed", type=int, default=DEFAULT_SEED, help="Fixed random seed (default: 647328)")
    parser.add_argument("-n", "--num-frames", type=int, default=240, help="Number of interpolated frames (default: 24)")
    parser.add_argument("--cfg-min", type=float, default=0.001, help="Minimum CFG at dream midpoint (default: 0.001)")
    parser.add_argument("--cfg-max", type=float, default=0.8, help="Maximum CFG at start/end endpoints (default: 0.8)")
    parser.add_argument("--cfg-mode", choices=["dip", "sweep", "fixed"], default="dip", help="CFG trajectory: dip, sweep, or fixed")
    parser.add_argument("--steps", type=int, default=4, help="LCM inference steps (default: 4)")
    parser.add_argument("--fps", type=int, default=3, help="Video framerate (default: 8)")
    parser.add_argument("--width", type=int, default=512, help="Frame width (default: 512)")
    parser.add_argument("--height", type=int, default=768, help="Frame height (default: 768)")
    args = parser.parse_args()

    print("=" * 70)
    print("🛸 ALIEN EXPLORER: SLERP + CFG DUAL-AXIS FUSION")
    print("=" * 70)
    print(f"[*] Scene A: Alien wandering desert sand dunes")
    print(f"[*] Scene B: Alien exploring jungle temple ruins")
    print(f"[*] Seed: {args.seed} | Frames: {args.num_frames} | LCM Steps: {args.steps}")
    print(f"[*] CFG Mode: '{args.cfg_mode}' ({args.cfg_max} -> {args.cfg_min} -> {args.cfg_max})")

    # 1. Resolve Model, VAE & LoRA
    model_path = resolve_model_path(DEFAULT_MODEL)
    print(f"[*] Loading model: {Path(model_path).name}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    pipe_kwargs = {
        "torch_dtype": torch_dtype,
        "use_safetensors": True,
        "extract_ema": True,
    }

    # Ultra-fast TAESD VAE
    vae_path = resolve_taesd_vae()
    if vae_path:
        print(f"[*] ⚡ Loading ultra-fast TAESD VAE from {vae_path} (4.9s decode)")
        try:
            if os.path.isdir(vae_path):
                pipe_kwargs["vae"] = AutoencoderTiny.from_pretrained(vae_path, torch_dtype=torch_dtype)
            else:
                pipe_kwargs["vae"] = AutoencoderTiny.from_single_file(vae_path, torch_dtype=torch_dtype)
        except Exception as e:
            print(f"[!] Note: Fallback loading TAESD: {e}")

    pipe = StableDiffusionPipeline.from_single_file(model_path, **pipe_kwargs)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.to(device)

    # Apply LoRA if present
    lora_file = resolve_lora_path()
    if lora_file:
        print(f"[*] Applying LoRA: {Path(lora_file).name} (scale: 0.25)")
        pipe.load_lora_weights(lora_file)
        pipe.fuse_lora(lora_scale=0.25)

    # 2. Encode Prompts & Unified Embeddings
    print("[*] Encoding Prompt A & Prompt B embeddings...")
    tokenizer = pipe.tokenizer
    text_encoder = pipe.text_encoder

    emb1, chunks1 = encode_chunked(tokenizer, text_encoder, args.prompt_a)
    emb2, chunks2 = encode_chunked(tokenizer, text_encoder, args.prompt_b)

    max_chunks = max(chunks1, chunks2)
    empty_chunk = encode_empty_chunk(tokenizer, text_encoder)
    while chunks1 < max_chunks:
        emb1 = torch.cat([emb1, empty_chunk], dim=1)
        chunks1 += 1
    while chunks2 < max_chunks:
        emb2 = torch.cat([emb2, empty_chunk], dim=1)
        chunks2 += 1

    neg_emb = encode_matching_negative(tokenizer, text_encoder, DEFAULT_NEGATIVE, max_chunks)

    # 3. Generate Frames
    frame_paths = []
    print("\n" + "-" * 70)
    print("🎬 RENDERING SLERP + CFG DUAL-AXIS FRAMES")
    print("-" * 70)

    for idx in range(args.num_frames):
        t = round(idx / max(1, args.num_frames - 1), 4)
        current_cfg = calculate_cfg(t, args.cfg_mode, args.cfg_min, args.cfg_max)
        
        frame_filename = f"alien_explorer_{args.seed}_{idx:04d}.png"
        frame_path = OUTPUT_DIR / frame_filename

        # Status note
        state = "🏜️ Desert Dunes" if t < 0.3 else ("🌀 Dream Dip (0.001 Hallucination)" if t < 0.7 else "🌴 Jungle Temple")
        print(f"[{idx + 1:02d}/{args.num_frames}] t={t:.3f} | SLERP: {int(t*100):3d}% | CFG: {current_cfg:.3f} | {state}")

        # Spherical interpolation of prompt embeddings
        emb_t = slerp(emb1, emb2, t)
        generator = torch.Generator(device=device).manual_seed(args.seed)

        with torch.inference_mode():
            image = pipe(
                prompt_embeds=emb_t,
                negative_prompt_embeds=neg_emb,
                generator=generator,
                width=args.width,
                height=args.height,
                num_inference_steps=args.steps,
                guidance_scale=current_cfg,
            ).images[0]

        image.save(str(frame_path))
        frame_paths.append(str(frame_path))

    # 4. Compile into Browser-Ready Videos
    print("\n" + "=" * 70)
    print("[*] Compiling frames into HD MP4 videos...")
    out_video_local = OUTPUT_DIR / "Alien_Explorer2.mp4"
    out_video_temp = TEMP_EXP_DIR / "Alien_Explorer2.mp4"

    ok = compile_video(frame_paths, str(out_video_local), fps=args.fps)
    if ok:
        shutil.copyfile(str(out_video_local), str(out_video_temp))
        print(f"[✓] Created video: {out_video_local}")
        print(f"[✓] Copied to:    {out_video_temp}")

    # 5. Write to slerp.json so it plays in live_slerp.html / flipbook
    slerp_db = {
        "mode": "slerp_cfg_fusion",
        "title": "Alien Explorer: Desert Dunes to Jungle Temple",
        "seed": args.seed,
        "total_frames": args.num_frames,
        "fps": args.fps,
        "cfg_mode": args.cfg_mode,
        "cfg_min": args.cfg_min,
        "cfg_max": args.cfg_max,
        "video": "Alien_Explorer.mp4",
        "frames": [
            {"index": i, "t": round(i / max(1, args.num_frames - 1), 4), "file": Path(p).name}
            for i, p in enumerate(frame_paths)
        ]
    }
    with open(OUTPUT_DIR / "slerp2.json", "w") as f:
        json.dump(slerp_db, f, indent=4)
    with open(TEMP_EXP_DIR / "slerp2.json", "w") as f:
        json.dump(slerp_db, f, indent=4)

    print("\n" + "=" * 70)
    print("✨ ALIEN EXPLORER MISSION COMPLETE!")
    print("=" * 70)
    print(f"🎬 Video File: {out_video_temp}")
    print(f"🕹️ Flipbook: Open your browser to http://localhost:5200/flipbook or static/live_slerp.html")
    print("=" * 70)

if __name__ == "__main__":
    main()
