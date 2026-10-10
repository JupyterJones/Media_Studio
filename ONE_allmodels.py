import os
import gc
import sys
import json
import signal
import shutil
import tempfile
import argparse
import subprocess
from datetime import datetime
import torch
from icecream import ic
from diffusers import StableDiffusionPipeline, LCMScheduler

def exit_gracefully(signum, frame):
    print("\n[*] Ctrl+C / termination signal received. Exiting cleanly...")
    os._exit(0)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
torch.set_num_threads(4)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_ROOTS = [
    "/media/jack/USB_USBSSD/models",
    os.path.join(BASE_DIR, "models"),
    os.path.join(os.path.expanduser("~"), "Desktop", "Comfy-UI", "models"),
]
CHECKPOINTS_DIRS = [os.path.join(r, "checkpoints") for r in MODELS_ROOTS]
LORAS_DIRS = [os.path.join(r, "loras") for r in MODELS_ROOTS]
VAE_DIRS = [os.path.join(r, "vae") for r in MODELS_ROOTS]
CHECKPOINT_DIR = next((d for d in CHECKPOINTS_DIRS if os.path.exists(d)), os.path.join(BASE_DIR, "models", "checkpoints"))

def get_default_lora():
    for d in LORAS_DIRS:
        cand = os.path.join(d, "more_details.safetensors")
        if os.path.exists(cand):
            return cand
    return os.path.join(LOCAL_MODELS_DIR, "loras", "more_details.safetensors")

DEFAULT_LORA = get_default_lora()
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "novel_images")
TEMP_EXP_DIR = os.path.join(BASE_DIR, "static", "temp_exp")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_EXP_DIR, exist_ok=True)

def resolve_model_path(model_filename):
    if not model_filename:
        return None
    if os.path.isfile(model_filename):
        return os.path.abspath(model_filename)
    for c_dir in CHECKPOINTS_DIRS:
        if not os.path.exists(c_dir):
            continue
        cand = os.path.join(c_dir, model_filename)
        if os.path.isfile(cand):
            return os.path.abspath(cand)
        cand_st = os.path.join(c_dir, f"{model_filename}.safetensors")
        if os.path.isfile(cand_st):
            return os.path.abspath(cand_st)
    return None

def resolve_lora(l):
    if not l:
        return None
    l_clean = l.strip()
    if os.path.exists(l_clean):
        return os.path.abspath(l_clean)
    for d in LORAS_DIRS:
        if not os.path.exists(d):
            continue
        cand = os.path.join(d, l_clean)
        if os.path.exists(cand):
            return os.path.abspath(cand)
        cand_st = os.path.join(d, f"{l_clean}.safetensors")
        if os.path.exists(cand_st):
            return os.path.abspath(cand_st)
    return l_clean

def resolve_vae(v):
    if not v:
        return None
    v_clean = v.strip()
    if os.path.exists(v_clean):
        return os.path.abspath(v_clean)
    for d in VAE_DIRS:
        if not os.path.exists(d):
            continue
        cand = os.path.join(d, v_clean)
        if os.path.exists(cand):
            return os.path.abspath(cand)
        cand_st = os.path.join(d, f"{v_clean}.safetensors")
        if os.path.exists(cand_st):
            return os.path.abspath(cand_st)
    return v_clean

NON_BASE_MODEL_KEYWORDS = ["motion", "pose", "controlnet", "depth", "canny", "adapter", "ip-adapter", "t2i"]

def get_available_models():
    """Dynamically scan all checkpoint directories across USB and local storage."""
    models = set()
    for c_dir in CHECKPOINTS_DIRS:
        if os.path.exists(c_dir):
            try:
                for f in sorted(os.listdir(c_dir)):
                    full_path = os.path.join(c_dir, f)
                    if os.path.isdir(full_path) or f.startswith('.'):
                        continue
                    if f.endswith(('.safetensors', '.ckpt', '.pt', '.bin')):
                        fl = f.lower()
                        if any(kw in fl for kw in NON_BASE_MODEL_KEYWORDS):
                            continue
                        models.add(f)
            except Exception:
                pass
    return sorted(list(models))

MODELS = get_available_models()

def encode_chunked(tokenizer, text_encoder, prompt, max_chunks=None):
    raw_tokens = tokenizer(prompt, padding=False, truncation=False, return_tensors="pt").input_ids[0]
    bos = raw_tokens[0:1]
    eos = raw_tokens[-1:]
    content = raw_tokens[1:-1]
    
    if len(raw_tokens) <= 77 and (max_chunks is None or max_chunks == 1):
        inputs = tokenizer(prompt, padding="max_length", max_length=77, truncation=True, return_tensors="pt")
        with torch.no_grad():
            return text_encoder(inputs.input_ids.to(text_encoder.device))[0]
            
    chunks = [content[i:i+75] for i in range(0, max(1, len(content)), 75)]
    embs = []
    for c in chunks:
        t = torch.cat([bos, c, eos])
        pad_len = 77 - len(t)
        if pad_len > 0:
            t = torch.nn.functional.pad(t, (0, pad_len), value=tokenizer.pad_token_id)
        with torch.no_grad():
            embs.append(text_encoder(t.unsqueeze(0).to(text_encoder.device))[0])
            
    return torch.cat(embs, dim=1)

def encode_matching_negative(tokenizer, text_encoder, negative_prompt, target_chunks):
    neg_tokens = tokenizer(negative_prompt, padding=False, truncation=False, return_tensors="pt").input_ids[0]
    bos, eos = neg_tokens[0:1], neg_tokens[-1:]
    content = neg_tokens[1:-1]

    embs = []
    for i in range(target_chunks):
        c = content[:75] if len(content) else content
        t = torch.cat([bos, c, eos])
        pad_len = 77 - len(t)
        if pad_len > 0:
            t = torch.nn.functional.pad(t, (0, pad_len), value=tokenizer.pad_token_id)
        with torch.no_grad():
            embs.append(text_encoder(t.unsqueeze(0).to(text_encoder.device))[0])
    return torch.cat(embs, dim=1)

def compile_video_from_frames(image_paths, output_mp4_path, fps=2):
    """
    Stitches an ordered sequence of images into a browser-ready MP4 (H.264, YUV420p) via FFmpeg.
    Default: 2 fps (2 frames per second) to give viewers time to appreciate each model style.
    """
    if not image_paths:
        print("[!] No images provided for video compilation.")
        return False

    temp_dir = tempfile.mkdtemp(prefix="models_video_")
    try:
        for idx, img_path in enumerate(image_paths):
            symlink_path = os.path.join(temp_dir, f"frame_{idx:05d}.png")
            try:
                os.symlink(os.path.abspath(img_path), symlink_path)
            except Exception:
                shutil.copyfile(img_path, symlink_path)

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-framerate", str(fps),
            "-i", os.path.join(temp_dir, "frame_%05d.png"),
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "18",
            output_mp4_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[!] FFmpeg error during video compilation: {res.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"[!] Exception during video compilation: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def generate_with_model(
    prompt,
    seed,
    model_filename,
    num_steps=None,
    guidance_scale=None,
    lora_path=None,
    lora_scale=0.3,
    vae_path=None
):
    model_path = resolve_model_path(model_filename)
    if not model_path or not os.path.exists(model_path):
        print(f"[!] Warning: Model file not found: {model_filename}, skipping.")
        return None, None, None

    is_lcm = "lcm" in model_filename.lower()

    # Smart auto-tuning: LCM models get 5 steps & 1.5 CFG; Non-LCM models get 18 steps & 6.5 CFG
    if is_lcm:
        effective_steps = num_steps if (num_steps is not None and num_steps <= 12) else 5
        effective_guidance = guidance_scale if (guidance_scale is not None and guidance_scale <= 3.0) else 1.5
    else:
        effective_steps = num_steps if (num_steps is not None and num_steps > 12) else 18
        effective_guidance = guidance_scale if (guidance_scale is not None and guidance_scale > 3.0) else 6.5

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_type_str = "LCM Model (LCMScheduler)" if is_lcm else "Standard SD 1.5 (DPMSolverMultistepScheduler)"
    print(f"\n" + "=" * 60)
    print(f"[*] Loading model: {model_filename} on {device} ({torch_dtype})")
    print(f"[*] Architecture:  {model_type_str}")
    print(f"[*] Auto-Tuned:    Steps={effective_steps} | CFG={effective_guidance}")
    print(f"=" * 60)

    pipe_kwargs = {
        "torch_dtype": torch_dtype,
        "use_safetensors": True,
        "extract_ema": True,
    }

    # Optional custom VAE
    if vae_path and os.path.exists(vae_path):
        if "taesd" in vae_path.lower():
            from diffusers import AutoencoderTiny
            print(f"[*] Loading ultra-fast TAESD VAE from {vae_path}...")
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
            print(f"[*] Loading custom VAE from {vae_path}...")
            pipe_kwargs["vae"] = AutoencoderKL.from_single_file(vae_path, torch_dtype=torch_dtype)

    try:
        pipe = StableDiffusionPipeline.from_single_file(model_path, **pipe_kwargs)
    except Exception as e:
        print(f"\n[!] Skipping incompatible model '{model_filename}': {e}")
        return None
    pipe.to(device)

    # Dynamic scheduler selection based on model architecture
    if is_lcm:
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    else:
        from diffusers import DPMSolverMultistepScheduler
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)

    # CPU / Memory Optimization
    if device == "cpu":
        pipe.enable_attention_slicing(1)
        is_taesd = vae_path and "taesd" in vae_path.lower()
        if not is_taesd and hasattr(pipe, "vae") and pipe.vae is not None:
            if hasattr(pipe.vae, "enable_slicing"):
                pipe.vae.enable_slicing()
            if hasattr(pipe.vae, "enable_tiling"):
                pipe.vae.enable_tiling()

    # Optional LoRA (e.g. more_details.safetensors)
    if lora_path and os.path.exists(lora_path) and lora_scale > 0:
        print(f"[*] Applying LoRA {os.path.basename(lora_path)} with scale {lora_scale}...")
        pipe.load_lora_weights(lora_path)
        pipe.fuse_lora(lora_scale=lora_scale)

    tokenizer = pipe.tokenizer
    text_encoder = pipe.text_encoder

    emb = encode_chunked(tokenizer, text_encoder, prompt)
    num_chunks = emb.shape[1] // 77
    neg_emb = encode_matching_negative(tokenizer, text_encoder, "blurry, low quality, deformed, nudity, large exaggerated breasts, nipples, nsfw, NSFW", num_chunks)

    generator = torch.Generator(device=device).manual_seed(seed)

    print(f"[*] Generating image with seed {seed}, steps {effective_steps}, cfg {effective_guidance}...")
    image = pipe(
        prompt_embeds=emb,
        negative_prompt_embeds=neg_emb,
        generator=generator,
        width=512,
        height=768,
        num_inference_steps=effective_steps,
        guidance_scale=effective_guidance,
    ).images[0]

    output_path = os.path.join(OUTPUT_DIR, f"{seed}_{model_filename}_output.png")
    image.save(output_path)
    print(f"[+] Successfully saved output: {output_path}")

    # Explicit memory cleanup between models
    del pipe
    del tokenizer
    del text_encoder
    del emb
    del neg_emb
    del image
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return output_path, effective_steps, effective_guidance

def main():
    parser = argparse.ArgumentParser(description="Run SD1.5 LCM inference across models with memory cleanup.")
    parser.add_argument("-p", "--prompt", default=(
    "Dense Bosch-style surreal nightmare painting, horror vacui composition"
    "hundreds of intertwined grotesque creatures, skulls, tentacles, hybrid monsters"
    "medieval minstrel with lute, fish with human faces, crowned beast, candlelight chiaroscuro"
    "muted earth tones, aged oil painting texture, Northern Renaissance dark fantasy"
    "highly detailed, chaotic symbolic tableau"), help="Prompt text")
    parser.add_argument("-s", "--seed", type=int, default=234567, help="Random seed")
    parser.add_argument("--steps", type=int, default=4, help="Inference steps (default: 4)")
    parser.add_argument("--guidance", type=float, default=1.5, help="Guidance scale (default: 1.5)")
    parser.add_argument("-m", "--model", default=None, help="Specific model name, index, or comma-separated list (default: all)")
    parser.add_argument("--lora", default=DEFAULT_LORA, help="Path to LoRA file (default: more_details.safetensors)")
    parser.add_argument("--lora-scale", type=float, default=0.25, help="LoRA scale weight (0 to disable, default: 0.25)")
    parser.add_argument("--vae", default=None, help="Optional path to custom VAE (default: uses model's built-in VAE)")
    parser.add_argument("--fps", type=float, default=2, help="Frames per second for generated video (default: 2, 2 per second)")
    parser.add_argument("--no-video", action="store_true", help="Skip video compilation")
    args = parser.parse_args()

    target_models = MODELS
    if args.model:
        if args.model.isdigit():
            idx = int(args.model)
            if 0 <= idx < len(MODELS):
                target_models = [MODELS[idx]]
        else:
            selected = [m.strip() for m in args.model.split(",")]
            target_models = [m for m in selected if m in MODELS]
        
        if not target_models:
            print(f"[!] No valid models matched selection: {args.model}")
            return

    total = len(target_models)
    models_json_path = os.path.join(OUTPUT_DIR, "models.json")

    print("\n" + "=" * 65)
    print(f"[*] All Models Batch Generator ({total} models)")
    print(f"[*] Destination Directory: {OUTPUT_DIR}")
    print(f"[*] Tracking Database: {models_json_path}")
    print(f"[*] Seed: {args.seed} | Steps: {args.steps} | Guidance: {args.guidance}")
    print("=" * 65)

    # 1. Load or initialize models.json
    db = {}
    if os.path.exists(models_json_path):
        try:
            with open(models_json_path, "r") as f:
                db = json.load(f)
            print(f"[*] Loaded existing database from {models_json_path} ({len(db.get('runs', []))} past records)")
        except Exception as e:
            print(f"[!] Warning: Failed to read {models_json_path}: {e}. Starting fresh.")
            db = {}

    if not isinstance(db, dict) or "runs" not in db:
        db = {
            "seed": args.seed,
            "prompt": args.prompt,
            "next_image_id": 1,
            "runs": []
        }
    else:
        # Preserve and adopt seed and prompt from models.json if resuming
        existing_seed = db.get("seed")
        existing_runs = db.get("runs", [])
        # If user didn't specify a custom seed (default 424242 or 0) or if models.json has active progress:
        if existing_seed and (args.seed == 424242 or args.seed == 0 or args.seed == existing_seed or len(existing_runs) < len(target_models)):
            print(f"[*] Resuming from existing models.json: Seed {existing_seed} ({len(existing_runs)}/{len(target_models)} models already in database).")
            args.seed = existing_seed
            if (not args.prompt or args.prompt == "A close up of a alien cyborg, steampunk warrior, robotic body and cyborg face, wearing battle armor, staring directly into camera, highly detailed, photorealistic 8k") and db.get("prompt"):
                args.prompt = db["prompt"]

    # 2. Check which models are already generated on disk
    models_to_generate = []
    completed_model_names = {r.get("model") for r in db.get("runs", []) if r.get("model")}
    completed_files = {r.get("file") for r in db.get("runs", []) if r.get("file")}

    for idx, model_name in enumerate(target_models, 1):
        filename = f"{args.seed}_{model_name}_output.png"
        output_path = os.path.join(OUTPUT_DIR, filename)

        # 1) Verified in models.json and file exists on disk
        if (model_name in completed_model_names or filename in completed_files) and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"[*] [{idx}/{total}] Resuming: {filename} ({model_name}) verified in models.json. Skipping.")
            continue

        # 2) File exists on disk but was missing in models.json - record it now
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            mtime = os.path.getmtime(output_path)
            img_id = db.get("next_image_id", len(db["runs"]) + 1)
            db["runs"].append({
                "image_id": img_id,
                "file": filename,
                "timestamp": datetime.fromtimestamp(mtime).isoformat(),
                "mode": "all_models",
                "prompt": args.prompt,
                "steps": args.steps,
                "guidance_scale": args.guidance,
                "seed": args.seed,
                "width": 512,
                "height": 768,
                "model": model_name
            })
            db["next_image_id"] = img_id + 1
            print(f"[*] [{idx}/{total}] Resuming: {filename} ({model_name}) found on disk. Recorded to models.json and skipping.")
        else:
            models_to_generate.append((idx, model_name, filename, output_path))

    with open(models_json_path, "w") as f:
        json.dump(db, f, indent=4)

    # 3. Generate missing models if any
    if models_to_generate:
        start_idx, first_m, _, _ = models_to_generate[0]
        print(f"\n[*] Resuming generation at model '{first_m}' (step {start_idx}/{total}, {len(models_to_generate)} remaining)...")

        for (idx, model_name, filename, output_path) in models_to_generate:
            print(f"[*] [{idx}/{total}] Processing model: {model_name}", flush=True)
            try:
                out, actual_steps, actual_guidance = generate_with_model(
                    prompt=args.prompt,
                    seed=args.seed,
                    model_filename=model_name,
                    num_steps=args.steps,
                    guidance_scale=args.guidance,
                    lora_path=resolve_lora(args.lora),
                    lora_scale=args.lora_scale,
                    vae_path=resolve_vae(args.vae)
                )
                if out and os.path.exists(out):
                    img_id = db.get("next_image_id", len(db["runs"]) + 1)
                    db["runs"].append({
                        "image_id": img_id,
                        "file": filename,
                        "timestamp": datetime.now().isoformat(),
                        "mode": "all_models",
                        "prompt": args.prompt,
                        "steps": actual_steps,
                        "guidance_scale": actual_guidance,
                        "seed": args.seed,
                        "width": 512,
                        "height": 768,
                        "model": model_name
                    })
                    db["next_image_id"] = img_id + 1
                    db["last_completed_model"] = model_name
                    db["last_completed_file"] = filename
                    with open(models_json_path, "w") as f:
                        json.dump(db, f, indent=4)
            except Exception as e:
                print(f"[!] Error processing {model_name}: {e}")
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
    else:
        print(f"\n[*] All {total} requested models already exist for seed {args.seed}! No new images needed.")

    print("\n[✓] All requested models processed successfully!")

    # 4. Compile sequential video (modelsX.mp4 / modelX.mp4)
    if not args.no_video:
        print("\n" + "=" * 65)
        print("[*] Sorting model frames sequentially to compile video...")
        print("=" * 65)

        sorted_frame_paths = []
        for model_name in target_models:
            fn = f"{args.seed}_{model_name}_output.png"
            fp = os.path.join(OUTPUT_DIR, fn)
            if os.path.exists(fp) and os.path.getsize(fp) > 0:
                sorted_frame_paths.append(fp)

        if sorted_frame_paths:
            print(f"[*] Found {len(sorted_frame_paths)} sorted model frames (Seed {args.seed})")
            local_models = os.path.join(OUTPUT_DIR, "modelsX.mp4")
            local_model = os.path.join(OUTPUT_DIR, "modelX.mp4")
            dest_models = os.path.join(TEMP_EXP_DIR, "modelsX.mp4")
            dest_model = os.path.join(TEMP_EXP_DIR, "modelX.mp4")

            success = compile_video_from_frames(sorted_frame_paths, local_models, fps=args.fps)
            if success:
                shutil.copyfile(local_models, local_model)
                shutil.copyfile(local_models, dest_models)
                shutil.copyfile(local_models, dest_model)
                print(f"[✓] Created local videos: {local_models} and {local_model}")
                print(f"[✓] Copied to temp_exp: {dest_models} and {dest_model}")

                db["video"] = "modelsX.mp4"
                db["video_frames"] = len(sorted_frame_paths)
                db["video_fps"] = args.fps
                with open(models_json_path, "w") as f:
                    json.dump(db, f, indent=4)
        else:
            print(f"[!] No existing frames found to compile models video.")

if __name__ == '__main__':
    main()