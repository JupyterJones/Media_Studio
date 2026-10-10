#!/usr/bin/env python3
"""
ONE_slerp.py - Long Prompt Spherical Linear Interpolation (SLERP) Studio
Smoothly morphs between two arbitrarily long text prompts using SLERP in embedding space,
generates sequential frames with fixed seed consistency, and compiles the result into
browser-ready MP4 videos (static/temp_exp/slerpX.mp4 and static/novel_images/slerpX.mp4).
"""

import os
import gc
import json
import signal
import shutil
import tempfile
import argparse
import subprocess
from datetime import datetime
import torch
from icecream import ic
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler, LCMScheduler

# --------------------------------------------------
# Signal Handling for Clean Exit
# --------------------------------------------------
def exit_gracefully(signum, frame):
    print("\n[*] Termination signal received. Cleaning up and exiting cleanly...")
    os._exit(0)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

# --------------------------------------------------
# Directories & Model Defaults
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_CHECKPOINTS = os.path.join(BASE_DIR, "models", "checkpoints")
LOCAL_LORAS = os.path.join(BASE_DIR, "models", "loras")
LOCAL_VAES = os.path.join(BASE_DIR, "models", "vae")

COMFY_DIR = "/home/jack/Desktop/Comfy-UI/models"
COMFY_CHECKPOINTS = os.path.join(COMFY_DIR, "checkpoints")
COMFY_LORAS = os.path.join(COMFY_DIR, "loras")
COMFY_VAES = os.path.join(COMFY_DIR, "vae")

USB_MODELS_DIR = "/media/jack/USB_USBSSD/models"

CHECKPOINT_DIRS = [
    LOCAL_CHECKPOINTS,
    COMFY_CHECKPOINTS,
    os.path.join(USB_MODELS_DIR, "checkpoints"),
    os.path.join(BASE_DIR, "models"),
]
LORA_DIRS = [
    LOCAL_LORAS,
    COMFY_LORAS,
    os.path.join(USB_MODELS_DIR, "loras"),
]
VAE_DIRS = [
    LOCAL_VAES,
    COMFY_VAES,
    os.path.join(USB_MODELS_DIR, "vae"),
]

CHECKPOINT_DIR = LOCAL_CHECKPOINTS if os.path.exists(LOCAL_CHECKPOINTS) else COMFY_CHECKPOINTS

def find_first_existing(dirs, filename):
    for d in dirs:
        if os.path.exists(d):
            cand = os.path.join(d, filename)
            if os.path.exists(cand):
                return cand
    return None

DEFAULT_LORA = find_first_existing(LORA_DIRS, "more_details.safetensors") or os.path.join(LOCAL_LORAS, "more_details.safetensors")
DEFAULT_VAE = find_first_existing(VAE_DIRS, "vae-ft-mse-840000-ema-pruned.safetensors") or find_first_existing(VAE_DIRS, "ClearVAE.safetensors")

OUTPUT_DIR = os.path.join(BASE_DIR, "static", "novel_images")
TEMP_EXP_DIR = os.path.join(BASE_DIR, "static", "temp_exp")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_EXP_DIR, exist_ok=True)

DEFAULT_MODEL = "comiccraftLCM_beta4.safetensors"

DEFAULT_PROMPT1 = (
    "A close up of a beautiful alien cyborg, steampunk robotic body, wearing battle armor,"
    "wires connecting head to torso, standing on a cliff overlooking a dystopian city, "
    "staring directly into camera, highly detailed, photorealistic 8k"
)

DEFAULT_PROMPT2 = (
    "An ancient Roman city, natural realist lighting, mountains in backgrounds"
    "towering statues, ornate courtyard sunny day blue sky fluffy clouds, "
    "cinematic lighting, ultra detailed 8k architectural concept art"
)

# --------------------------------------------------
# Model & Asset Path Resolution
# --------------------------------------------------
def resolve_checkpoint(model_name):
    if not model_name:
        model_name = DEFAULT_MODEL
    if os.path.isabs(model_name) and os.path.exists(model_name):
        return model_name
    for d in CHECKPOINT_DIRS:
        if not os.path.exists(d):
            continue
        cand = os.path.join(d, model_name)
        if os.path.exists(cand):
            return cand
        cand_ext = os.path.join(d, f"{model_name}.safetensors")
        if os.path.exists(cand_ext):
            return cand_ext
    return os.path.join(CHECKPOINT_DIR, model_name)

def resolve_lora(lora_name):
    if not lora_name:
        return None
    if os.path.isabs(lora_name) and os.path.exists(lora_name):
        return lora_name
    for d in LORA_DIRS:
        if not os.path.exists(d):
            continue
        cand = os.path.join(d, lora_name)
        if os.path.exists(cand):
            return cand
        cand_ext = os.path.join(d, f"{lora_name}.safetensors")
        if os.path.exists(cand_ext):
            return cand_ext
    return lora_name

def resolve_vae(vae_name):
    if not vae_name:
        return None
    if os.path.isabs(vae_name) and os.path.exists(vae_name):
        return vae_name
    for d in VAE_DIRS:
        if not os.path.exists(d):
            continue
        cand = os.path.join(d, vae_name)
        if os.path.exists(cand):
            return cand
        cand_ext = os.path.join(d, f"{vae_name}.safetensors")
        if os.path.exists(cand_ext):
            return cand_ext
    return vae_name

# --------------------------------------------------
# Chunked Long-Prompt Encoding
# --------------------------------------------------
def encode_chunked(tokenizer, text_encoder, prompt):
    """
    Encodes arbitrary-length prompt into chunked text embeddings.
    Returns (embedding_tensor, num_chunks).
    """
    raw_tokens = tokenizer(prompt, padding=False, truncation=False, return_tensors="pt").input_ids[0]
    bos = raw_tokens[0:1]
    eos = raw_tokens[-1:]
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
    """Encodes a single unconditional/empty 77-token chunk."""
    inputs = tokenizer("", padding="max_length", max_length=77, truncation=True, return_tensors="pt")
    with torch.no_grad():
        return text_encoder(inputs.input_ids.to(text_encoder.device))[0]

def encode_matching_negative(tokenizer, text_encoder, negative_prompt, target_chunks):
    """Encodes negative prompt repeated across target_chunks to match positive embedding shape."""
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

# --------------------------------------------------
# Spherical Linear Interpolation (SLERP)
# --------------------------------------------------
def slerp(v0, v1, t, eps=1e-7):
    """
    Spherical Linear Interpolation (SLERP) between tensors v0 and v1 at parameter t in [0.0, 1.0].
    Preserves vector norms and geometry along the hypersphere arc.
    """
    t_val = float(t)
    if t_val <= 0.0:
        return v0
    if t_val >= 1.0:
        return v1

    # Normalize along embedding dimension
    v0_norm = v0 / (torch.norm(v0, dim=-1, keepdim=True) + eps)
    v1_norm = v1 / (torch.norm(v1, dim=-1, keepdim=True) + eps)

    # Dot product clamped to [-1.0, 1.0]
    dot = (v0_norm * v1_norm).sum(dim=-1, keepdim=True)
    dot = torch.clamp(dot, -1.0, 1.0)

    # Angle between vectors
    theta_0 = torch.acos(dot)
    sin_theta_0 = torch.sin(theta_0)

    # Check for near-collinear vectors
    is_collinear = sin_theta_0.abs() < 1e-5

    theta_t = theta_0 * t_val
    sin_theta_t = torch.sin(theta_t)
    sin_theta_0_minus_t = torch.sin(theta_0 - theta_t)

    s0 = sin_theta_0_minus_t / (sin_theta_0 + eps)
    s1 = sin_theta_t / (sin_theta_0 + eps)

    res_slerp = s0 * v0 + s1 * v1
    res_lerp = (1.0 - t_val) * v0 + t_val * v1

    return torch.where(is_collinear, res_lerp, res_slerp)

# --------------------------------------------------
# Video Compilation via FFmpeg
# --------------------------------------------------
def compile_video(image_paths, output_paths, fps=10):
    if not image_paths:
        print("[!] No frames provided for video compilation.")
        return False

    temp_dir = tempfile.mkdtemp(prefix="slerp_vid_")
    try:
        for idx, img_path in enumerate(image_paths):
            symlink_path = os.path.join(temp_dir, f"frame_{idx:05d}.png")
            try:
                os.symlink(os.path.abspath(img_path), symlink_path)
            except Exception:
                shutil.copyfile(img_path, symlink_path)

        for out_path in output_paths:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
                "-framerate", str(fps),
                "-i", os.path.join(temp_dir, "frame_%05d.png"),
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast",
                "-crf", "18",
                out_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[✓] Successfully compiled video: {out_path} ({len(image_paths)} frames at {fps} fps)")
            else:
                print(f"[!] FFmpeg error compiling {out_path}: {res.stderr.strip()}")
        return True
    except Exception as e:
        print(f"[!] Exception during video compilation: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# --------------------------------------------------
# Main SLERP Pipeline Execution
# --------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Long Prompt Spherical Linear Interpolation (SLERP) Video Generator")
    parser.add_argument("-p1", "--prompt1", type=str, default=DEFAULT_PROMPT1, help="Starting prompt (Prompt A)")
    parser.add_argument("-p2", "--prompt2", type=str, default=DEFAULT_PROMPT2, help="Destination prompt (Prompt B)")
    parser.add_argument("-np", "--negative-prompt", type=str, default="blurry, low quality, deformed, artifacts, watermark", help="Negative prompt")
    parser.add_argument("-s", "--seed", type=int, default=424242, help="Fixed random seed for latent consistency")
    parser.add_argument("-n", "--num-frames", type=int, default=30, help="Number of interpolated frames to generate")
    parser.add_argument("--steps", type=int, default=5, help="Inference steps per frame (LCM: 4-8, Standard: 20-30)")
    parser.add_argument("--guidance", type=float, default=1.5, help="CFG guidance scale")
    parser.add_argument("-m", "--model", type=str, default=DEFAULT_MODEL, help="Model checkpoint filename or path")
    parser.add_argument("--lora", type=str, default=DEFAULT_LORA, help="Optional LoRA path")
    parser.add_argument("--lora-scale", type=float, default=0.25, help="LoRA scale weight")
    parser.add_argument("--vae", type=str, default=DEFAULT_VAE, help="Optional custom VAE path")
    parser.add_argument("--width", type=int, default=512, help="Frame width (default: 512)")
    parser.add_argument("--height", type=int, default=768, help="Frame height (default: 768)")
    parser.add_argument("--fps", type=int, default=10, help="Output video framerate")
    parser.add_argument("--no-video", action="store_true", help="Skip video compilation")
    parser.add_argument("--force-new", action="store_true", help="Force starting a new run instead of resuming from slerp.json")
    args = parser.parse_args()

    # --------------------------------------------------
    # Check for Existing SLERP Tracking Database to Resume
    # --------------------------------------------------
    slerp_json_path = os.path.join(OUTPUT_DIR, "slerp.json")
    temp_slerp_json_path = os.path.join(TEMP_EXP_DIR, "slerp.json")

    existing_db = None
    candidate_json_paths = [slerp_json_path, temp_slerp_json_path]

    for p in candidate_json_paths:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    cand_data = json.load(f)
                if isinstance(cand_data, dict) and cand_data.get("frames"):
                    if cand_data.get("seed") == args.seed:
                        existing_db = cand_data
                        print(f"[*] Found existing SLERP run in {p} for seed {args.seed} ({len(cand_data.get('frames', []))} frames)")
                        break
                    elif not existing_db and (args.seed == 0 or args.seed == 424242 or args.seed == 3360):
                        existing_db = cand_data
            except Exception:
                pass

    # Only consider resuming if the seed matches AND the prompts match the existing run
    prompts_match = existing_db and (args.prompt1 == existing_db.get("prompt1") and args.prompt2 == existing_db.get("prompt2"))

    if existing_db and prompts_match and not args.force_new:
        if existing_db.get("seed") == args.seed or args.seed in (0, 424242):
            args.seed = existing_db.get("seed", args.seed)
            if existing_db.get("model"):
                args.model = existing_db["model"]
            if existing_db.get("total_frames"):
                args.num_frames = int(existing_db["total_frames"])
            if existing_db.get("negative_prompt") is not None:
                args.negative_prompt = existing_db["negative_prompt"]
            if existing_db.get("steps"):
                args.steps = int(existing_db["steps"])
            if existing_db.get("guidance"):
                args.guidance = float(existing_db["guidance"])
            if existing_db.get("width"):
                args.width = int(existing_db["width"])
            if existing_db.get("height"):
                args.height = int(existing_db["height"])
            if existing_db.get("fps"):
                args.fps = int(existing_db["fps"])
            if existing_db.get("vae"):
                args.vae = existing_db["vae"]
            if existing_db.get("lora"):
                args.lora = existing_db["lora"]
            if existing_db.get("lora_scale") is not None:
                args.lora_scale = float(existing_db["lora_scale"])

            print("\n" + "=" * 65)
            print("  🔒 RESTORED & LOCKED PARAMETERS FROM slerp.json")
            print("=" * 65)
            print(f"[*] Seed:         {args.seed}")
            print(f"[*] Model:        {args.model}")
            print(f"[*] Total Frames: {args.num_frames}")
            print(f"[*] Steps:        {args.steps} | Guidance: {args.guidance}")
            print(f"[*] VAE:          {args.vae or 'Default'}")
            print(f"[*] LoRA:         {args.lora or 'None'} (Scale: {args.lora_scale})")
            print("=" * 65 + "\n")

    print("\n" + "=" * 65)
    print("      🔀 LONG PROMPT SPHERICAL LINEAR INTERPOLATION (SLERP)")
    print("=" * 65)
    print(f"[*] Prompt 1: {args.prompt1[:90]}...")
    print(f"[*] Prompt 2: {args.prompt2[:90]}...")
    print(f"[*] Model:    {args.model}")
    print(f"[*] Seed:     {args.seed} (Fixed for smooth morphing)")
    print(f"[*] Frames:   {args.num_frames} interpolation steps")
    print(f"[*] Steps:    {args.steps} | Guidance: {args.guidance} | Size: {args.width}x{args.height}")
    print("=" * 65)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_path = resolve_checkpoint(args.model)
    if not os.path.exists(model_path):
        print(f"[!] Error: Checkpoint not found at {model_path}")
        return

    pipe_kwargs = {
        "torch_dtype": torch_dtype,
        "use_safetensors": True,
        "extract_ema": True,
        "safety_checker": None,
        "requires_safety_checker": False
    }

    vae_path = resolve_vae(args.vae)
    if vae_path and os.path.exists(vae_path):
        if "taesd" in vae_path.lower():
            from diffusers import AutoencoderTiny
            print(f"[*] Loading ultra-fast TAESD VAE from: {os.path.basename(vae_path)}")
            if os.path.isdir(vae_path) and os.path.exists(os.path.join(vae_path, "config.json")):
                pipe_kwargs["vae"] = AutoencoderTiny.from_pretrained(vae_path, torch_dtype=torch_dtype)
            else:
                parent_dir = os.path.dirname(vae_path)
                sibling_taesd = os.path.join(parent_dir, "taesd")
                if os.path.isdir(sibling_taesd) and os.path.exists(os.path.join(sibling_taesd, "config.json")):
                    pipe_kwargs["vae"] = AutoencoderTiny.from_pretrained(sibling_taesd, torch_dtype=torch_dtype)
                elif os.path.isdir("/media/jack/USB_USBSSD/models/vae/taesd"):
                    pipe_kwargs["vae"] = AutoencoderTiny.from_pretrained("/media/jack/USB_USBSSD/models/vae/taesd", torch_dtype=torch_dtype)
                else:
                    pipe_kwargs["vae"] = AutoencoderTiny.from_pretrained("madebyollin/taesd", torch_dtype=torch_dtype)
        else:
            from diffusers import AutoencoderKL
            print(f"[*] Loading custom VAE from: {os.path.basename(vae_path)}")
            pipe_kwargs["vae"] = AutoencoderKL.from_single_file(vae_path, torch_dtype=torch_dtype)

    print(f"[*] Loading Stable Diffusion pipeline from {os.path.basename(model_path)}...")
    pipe = StableDiffusionPipeline.from_single_file(model_path, **pipe_kwargs)
    pipe.to(device)

    # Scheduler selection
    is_lcm = "lcm" in os.path.basename(model_path).lower() or args.steps <= 12
    if is_lcm:
        print("[*] Configuring LCMScheduler for fast latent consistency morphing")
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    else:
        print("[*] Configuring DPMSolverMultistepScheduler with Karras sigmas")
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)

    if device == "cpu":
        pipe.enable_attention_slicing(1)
        if hasattr(pipe, "vae") and pipe.vae is not None:
            if hasattr(pipe.vae, "enable_slicing"):
                pipe.vae.enable_slicing()
            if hasattr(pipe.vae, "enable_tiling"):
                pipe.vae.enable_tiling()

    # LoRA Loading
    lora_path = resolve_lora(args.lora)
    if lora_path and os.path.exists(lora_path) and args.lora_scale > 0:
        print(f"[*] Applying LoRA {os.path.basename(lora_path)} with scale {args.lora_scale}...")
        pipe.load_lora_weights(lora_path)
        pipe.fuse_lora(lora_scale=args.lora_scale)

    tokenizer = pipe.tokenizer
    text_encoder = pipe.text_encoder

    # 1. Encode both prompts
    print("[*] Encoding Prompt 1 into chunked text embeddings...")
    emb1, chunks1 = encode_chunked(tokenizer, text_encoder, args.prompt1)
    print(f"    - Prompt 1 chunks: {chunks1} (Tokens: {emb1.shape[1]})")

    print("[*] Encoding Prompt 2 into chunked text embeddings...")
    emb2, chunks2 = encode_chunked(tokenizer, text_encoder, args.prompt2)
    print(f"    - Prompt 2 chunks: {chunks2} (Tokens: {emb2.shape[1]})")

    # Match chunk counts by padding the shorter embedding with empty chunks
    max_chunks = max(chunks1, chunks2)
    empty_chunk = encode_empty_chunk(tokenizer, text_encoder)

    while chunks1 < max_chunks:
        emb1 = torch.cat([emb1, empty_chunk], dim=1)
        chunks1 += 1

    while chunks2 < max_chunks:
        emb2 = torch.cat([emb2, empty_chunk], dim=1)
        chunks2 += 1

    print(f"[*] Unified embedding length: {max_chunks} chunks ({emb1.shape[1]} tokens)")

    # 2. Encode matching negative prompt
    neg_emb = encode_matching_negative(tokenizer, text_encoder, args.negative_prompt, max_chunks)

    # 3. Load or Initialize slerp.json Tracking Database
    slerp_json_path = os.path.join(OUTPUT_DIR, "slerp.json")
    temp_slerp_json_path = os.path.join(TEMP_EXP_DIR, "slerp.json")

    db = {}
    for p in [slerp_json_path, temp_slerp_json_path]:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    db = json.load(f)
                if isinstance(db, dict) and "frames" in db:
                    print(f"[*] Loaded existing SLERP database from {p}")
                    break
            except Exception as e:
                print(f"[!] Warning reading {p}: {e}")
                db = {}

    active_db = existing_db if (existing_db and existing_db.get("seed") == args.seed and prompts_match and not args.force_new) else None

    if not active_db and (not isinstance(db, dict) or "frames" not in db or db.get("seed") != args.seed or not prompts_match):
        db = {
            "mode": "slerp",
            "seed": args.seed,
            "prompt1": args.prompt1,
            "prompt2": args.prompt2,
            "negative_prompt": args.negative_prompt,
            "model": os.path.basename(model_path),
            "vae": os.path.basename(vae_path) if vae_path else None,
            "lora": os.path.basename(lora_path) if lora_path else None,
            "lora_scale": args.lora_scale if (lora_path and args.lora_scale > 0) else 0.0,
            "total_frames": args.num_frames,
            "fps": args.fps,
            "steps": args.steps,
            "guidance": args.guidance,
            "width": args.width,
            "height": args.height,
            "timestamp": datetime.now().isoformat(),
            "last_completed_frame": None,
            "last_completed_index": -1,
            "last_completed_t": 0.0,
            "completed_count": 0,
            "frames": []
        }
    else:
        # Resuming existing run
        src = active_db if active_db else db
        db = {
            "mode": "slerp",
            "seed": args.seed,
            "prompt1": args.prompt1,
            "prompt2": args.prompt2,
            "negative_prompt": args.negative_prompt,
            "model": src.get("model", os.path.basename(model_path)),
            "vae": src.get("vae") or (os.path.basename(vae_path) if vae_path else None),
            "lora": src.get("lora") or (os.path.basename(lora_path) if lora_path else None),
            "lora_scale": src.get("lora_scale", args.lora_scale if (lora_path and args.lora_scale > 0) else 0.0),
            "total_frames": src.get("total_frames", args.num_frames),
            "fps": src.get("fps", args.fps),
            "steps": src.get("steps", args.steps),
            "guidance": src.get("guidance", args.guidance),
            "width": src.get("width", args.width),
            "height": src.get("height", args.height),
            "timestamp": src.get("timestamp", datetime.now().isoformat()),
            "last_completed_frame": src.get("last_completed_frame"),
            "last_completed_index": src.get("last_completed_index", -1),
            "last_completed_t": src.get("last_completed_t", 0.0),
            "completed_count": src.get("completed_count", 0),
            "frames": src.get("frames", [])
        }
        args.num_frames = db["total_frames"]

    # Helper to save database to both directories
    def save_slerp_json():
        try:
            with open(slerp_json_path, "w") as f:
                json.dump(db, f, indent=4)
            shutil.copyfile(slerp_json_path, temp_slerp_json_path)
        except Exception as e:
            print(f"[!] Warning: Failed saving slerp.json: {e}")

    # Backfill from disk for existing frames matching slerp_{seed}_* in OUTPUT_DIR only
    existing_disk = {}
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.startswith(f"slerp_{args.seed}_") and (f.endswith(".png") or f.endswith(".jpg")):
                try:
                    base = f.rsplit(".", 1)[0]
                    idx_str = base.split("_")[-1]
                    existing_disk[int(idx_str)] = f
                except Exception:
                    pass

    tracked_indices = {fr.get("index") for fr in db.get("frames", []) if isinstance(fr, dict)}
    for idx_val in sorted(existing_disk.keys()):
        if idx_val not in tracked_indices:
            t_val = round(idx_val / max(1, (args.num_frames - 1)), 4)
            db["frames"].append({
                "index": idx_val,
                "t": t_val,
                "file": existing_disk[idx_val]
            })

    db["frames"] = sorted(db.get("frames", []), key=lambda x: x.get("index", 0))
    if db["frames"]:
        last_item = db["frames"][-1]
        db["last_completed_frame"] = last_item.get("file")
        db["last_completed_index"] = last_item.get("index")
        db["last_completed_t"] = last_item.get("t")
    db["completed_count"] = len(db["frames"])

    # Immediately save initial database
    save_slerp_json()

    # 4. Determine tasks to generate vs existing frames to skip
    frame_paths = []
    tasks_to_generate = []
    for idx in range(args.num_frames):
        t = round(idx / max(1, (args.num_frames - 1)), 4)
        frame_filename = f"slerp_{args.seed}_{idx:04d}.png"
        frame_path = os.path.join(OUTPUT_DIR, frame_filename)
        cand_jpg = os.path.join(OUTPUT_DIR, f"slerp_{args.seed}_{idx:04d}.jpg")

        actual_path = None
        if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
            actual_path = frame_path
        elif os.path.exists(cand_jpg) and os.path.getsize(cand_jpg) > 0:
            actual_path = cand_jpg

        if actual_path:
            frame_paths.append(actual_path)
            print(f"[*] [{idx + 1}/{args.num_frames}] Resuming: {os.path.basename(actual_path)} (t={t:.3f}) already exists. Skipping.")
        else:
            tasks_to_generate.append((idx, t, frame_filename, frame_path))

    print(f"[*] SLERP Plan: {len(frame_paths)} existing frame(s) loaded, {len(tasks_to_generate)} to synthesize.")

    # 5. Generate remaining frames
    for idx, t, frame_filename, frame_path in tasks_to_generate:
        print(f"[{idx + 1}/{args.num_frames}] SLERP Morph (t={t:.3f}) -> {frame_filename}")
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
                guidance_scale=args.guidance,
            ).images[0]

        image.save(frame_path)
        frame_paths.append(frame_path)

        # Update database incrementally
        frame_entry = {
            "index": idx,
            "t": round(t, 4),
            "file": frame_filename
        }
        db["frames"] = [fr for fr in db["frames"] if fr.get("index") != idx]
        db["frames"].append(frame_entry)
        db["frames"] = sorted(db["frames"], key=lambda x: x.get("index", 0))
        db["last_completed_frame"] = frame_filename
        db["last_completed_index"] = idx
        db["last_completed_t"] = round(t, 4)
        db["completed_count"] = len(db["frames"])
        save_slerp_json()

    # 6. Sort all frame paths and compile video
    def get_frame_index(p):
        try:
            return int(os.path.splitext(os.path.basename(p))[0].split("_")[-1])
        except Exception:
            return 0

    frame_paths = sorted(frame_paths, key=get_frame_index)

    if not args.no_video and frame_paths:
        print("\n" + "=" * 65)
        print("[*] Compiling SLERP video...")
        print("=" * 65)
        target_videos = [
            os.path.join(TEMP_EXP_DIR, "slerpX.mp4"),
            os.path.join(OUTPUT_DIR, "slerpX.mp4")
        ]
        compile_video(frame_paths, target_videos, fps=args.fps)
        db["video_url"] = "/static/temp_exp/slerpX.mp4"
        save_slerp_json()

    print("\n[✓] SLERP Generation Completed Successfully!")
    print(f"    - Frames directory: {OUTPUT_DIR}")
    print(f"    - Master video:     {os.path.join(TEMP_EXP_DIR, 'slerpX.mp4')}")
    print(f"    - Tracking file:    {slerp_json_path}")

if __name__ == "__main__":
    main()
