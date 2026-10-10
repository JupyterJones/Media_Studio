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

NON_BASE_MODEL_KEYWORDS = ["motion", "pose", "controlnet", "depth", "canny", "adapter", "ip-adapter", "t2i"]
PREFERRED_MODELS = [
    "comiccraftLCM_beta4.safetensors",
    "coldfleshRealisticLCM_v10.safetensors",
    "dreamshaper_8LCM.safetensors",
    "madnessLCMV1_v10.safetensors",
    "realisticLCMBYStable_v10.safetensors"
]

def get_available_models():
    models = set()
    for d in CHECKPOINTS_DIRS:
        if os.path.exists(d):
            try:
                for f in os.listdir(d):
                    full_path = os.path.join(d, f)
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

def get_default_model(models):
    for p in PREFERRED_MODELS:
        if p in models:
            return p
    return models[0] if models else "comiccraftLCM_beta4.safetensors"

DEFAULT_MODEL = get_default_model(MODELS)

DEFAULT_PROMPT = (
    "A highly detailed  full body image of a Beautiful Female alien cyborg art and illustration by theo el, in the style of balanced symmetry, light orange and cyan, detailed facial features, manticore, organic forms, muted tones, meticulous portraiture, complex patterns --ar 1:2 --stylize 750 --v 6"
)

def resolve_model(m):
    """Resolve a model name, path, stem, or index to an exact absolute file path."""
    if not m:
        return None
    m_clean = m.strip()

    # 1. Direct file path check
    if os.path.isfile(m_clean):
        return os.path.abspath(m_clean)

    # 2. Integer index into MODELS list
    if m_clean.isdigit():
        idx = int(m_clean)
        if 0 <= idx < len(MODELS):
            m_clean = MODELS[idx]

    # 3. Direct exact match or .safetensors in any checkpoint directory
    for d in CHECKPOINTS_DIRS:
        if not os.path.exists(d):
            continue
        cand = os.path.join(d, m_clean)
        if os.path.isfile(cand):
            return os.path.abspath(cand)
        cand_st = os.path.join(d, f"{m_clean}.safetensors")
        if os.path.isfile(cand_st):
            return os.path.abspath(cand_st)

    # 4. Case-insensitive stem match across all discovered models
    m_lower = m_clean.lower()
    for cand in MODELS:
        cand_stem = cand.replace(".safetensors", "")
        if m_lower in (cand.lower(), cand_stem.lower()):
            for d in CHECKPOINTS_DIRS:
                full = os.path.join(d, cand)
                if os.path.isfile(full):
                    return os.path.abspath(full)

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

def compile_video_from_frames(image_paths, output_mp4_path, fps=10):
    """
    Stitches an ordered sequence of images into a browser-ready MP4 (H.264, YUV420p) via FFmpeg.
    """
    if not image_paths:
        print("[!] No images provided for video compilation.")
        return False

    temp_dir = tempfile.mkdtemp(prefix="cfg_video_")
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

def run_cfg_sweep(
    model_filename,
    prompt,
    seed=123456,
    num_images=50,
    cfg_start=1.0,
    cfg_step=0.04,
    num_steps=4,
    lora_path=DEFAULT_LORA,
    lora_scale=0.25,
    vae_path=None,
    output_base_dir=BASE_DIR,
    fps=10,
    make_video=True,
    run_join_all=False
):
    if os.path.isfile(model_filename):
        model_path = os.path.abspath(model_filename)
        model_filename = os.path.basename(model_path)
    else:
        resolved = resolve_model(model_filename)
        if not resolved or not os.path.exists(resolved):
            print(f"[!] Error: Model file not found: {model_filename}")
            return
        model_path = resolved
        model_filename = os.path.basename(model_path)

    output_dir = os.path.join(output_base_dir, "static", "novel_images")
    temp_exp_dir = os.path.join(output_base_dir, "static", "temp_exp")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_exp_dir, exist_ok=True)
    cfg_json_path = os.path.join(output_dir, "cfg.json")

    print("\n" + "=" * 65)
    print(f"[*] Target Model: {model_filename}")
    print(f"[*] Destination directory: {output_dir}")
    print(f"[*] Tracking Database: {cfg_json_path}")
    print(f"[*] Fixed Seed: {seed}")
    print(f"[*] CFG Sweep: {num_images} images from {cfg_start:.3f} (step +{cfg_step:.3f})")
    print("=" * 65)

    # 1. Load or initialize cfg.json
    db = {}
    if os.path.exists(cfg_json_path):
        try:
            with open(cfg_json_path, "r") as f:
                db = json.load(f)
            print(f"[*] Loaded existing database from {cfg_json_path} ({len(db.get('runs', []))} past records)")
        except Exception as e:
            print(f"[!] Warning: Failed to read {cfg_json_path}: {e}. Starting fresh.")
            db = {}

    if not isinstance(db, dict) or "runs" not in db:
        db = {
            "seed": seed,
            "prompt": prompt,
            "model": model_filename,
            "next_image_id": 1,
            "runs": []
        }

    # 2. Check which steps are already generated vs which need generation
    tasks_to_generate = []
    skipped_count = 0
    for i in range(num_images):
        current_cfg = round(cfg_start + (i * cfg_step), 4)
        cfg_str = f"{current_cfg:.3f}".replace(".", "-")
        filename = f"{seed}_{cfg_str}.png"
        output_path = os.path.join(output_dir, filename)

        # Check for 3-decimal file or legacy 2-decimal file
        legacy_fn = f"{seed}_{current_cfg:.2f}".replace(".", "-") + ".png"
        legacy_path = os.path.join(output_dir, legacy_fn)
        if not (os.path.exists(output_path) and os.path.getsize(output_path) > 0) and (os.path.exists(legacy_path) and os.path.getsize(legacy_path) > 0):
            filename = legacy_fn
            output_path = legacy_path

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            skipped_count += 1
            # Ensure it is recorded in db['runs']
            if not any(r.get("file") == filename for r in db["runs"]):
                mtime = os.path.getmtime(output_path)
                img_id = db.get("next_image_id", len(db["runs"]) + 1)
                db["runs"].append({
                    "image_id": img_id,
                    "file": filename,
                    "timestamp": datetime.fromtimestamp(mtime).isoformat(),
                    "mode": "cfg_sweep",
                    "prompt": prompt,
                    "steps": num_steps,
                    "guidance_scale": current_cfg,
                    "seed": seed,
                    "width": 512,
                    "height": 768,
                    "model": model_filename
                })
                db["next_image_id"] = img_id + 1
            print(f"[*] [{i + 1}/{num_images}] Resuming: {filename} (CFG {current_cfg:.3f}) already exists. Skipping.")
        else:
            tasks_to_generate.append((i, current_cfg, filename, output_path))

    # Save any backfilled records to cfg.json
    try:
        with open(cfg_json_path, "w") as f:
            json.dump(db, f, indent=4)
    except Exception as e:
        print(f"[!] Warning: Could not save {cfg_json_path}: {e}")

    # 3. If there are tasks left to generate, load model and run inference
    if tasks_to_generate:
        start_idx, first_cfg, first_fn, _ = tasks_to_generate[0]
        print(f"\n[*] Resuming generation at step {start_idx + 1}/{num_images} (CFG {first_cfg:.3f}, {len(tasks_to_generate)} remaining)...")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        pipe_kwargs = {
            "torch_dtype": torch_dtype,
            "use_safetensors": True,
            "extract_ema": True,
        }

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
            print(f"\n[!] Failed to load model '{model_filename}': {e}")
            print("[!] This checkpoint could not be loaded as a standard Stable Diffusion 1.5 pipeline.")
            print(f"[!] Tip: Try running with a verified LCM checkpoint, e.g.:")
            print(f"    python3 ONE_model_cfg.py -m comiccraftLCM_beta4.safetensors")
            return []
        pipe.to(device)
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)

        if device == "cpu":
            pipe.enable_attention_slicing(1)
            is_taesd = vae_path and "taesd" in vae_path.lower()
            if not is_taesd and hasattr(pipe, "vae") and pipe.vae is not None:
                if hasattr(pipe.vae, "enable_slicing"):
                    pipe.vae.enable_slicing()

        if lora_path and os.path.exists(lora_path) and lora_scale > 0:
            print(f"[*] Applying LoRA {os.path.basename(lora_path)} with scale {lora_scale}...")
            pipe.load_lora_weights(lora_path)
            pipe.fuse_lora(lora_scale=lora_scale)

        tokenizer = pipe.tokenizer
        text_encoder = pipe.text_encoder

        emb = encode_chunked(tokenizer, text_encoder, prompt)
        num_chunks = emb.shape[1] // 77
        neg_emb = encode_matching_negative(tokenizer, text_encoder, "blurry, low quality, deformed, nudity, large exaggerated breasts, nipples, nsfw, NSFW", num_chunks)

        try:
            for (i, current_cfg, filename, output_path) in tasks_to_generate:
                print(f"[*] [{i + 1}/{num_images}] Generating image: {filename} | CFG: {current_cfg:.3f} | Seed: {seed}", flush=True)
                try:
                    generator = torch.Generator(device=device).manual_seed(seed)
                    image = pipe(
                        prompt_embeds=emb,
                        negative_prompt_embeds=neg_emb,
                        generator=generator,
                        width=512,
                        height=768,
                        num_inference_steps=num_steps,
                        guidance_scale=current_cfg,
                    ).images[0]

                    image.save(output_path)
                    print(f"[+] [{i + 1}/{num_images}] Saved: {output_path}")

                    # Update cfg.json incrementally
                    img_id = db.get("next_image_id", len(db["runs"]) + 1)
                    db["runs"].append({
                        "image_id": img_id,
                        "file": filename,
                        "timestamp": datetime.now().isoformat(),
                        "mode": "cfg_sweep",
                        "prompt": prompt,
                        "steps": num_steps,
                        "guidance_scale": current_cfg,
                        "seed": seed,
                        "width": 512,
                        "height": 768,
                        "model": model_filename
                    })
                    db["next_image_id"] = img_id + 1
                    db["last_completed_cfg"] = current_cfg
                    db["last_completed_file"] = filename
                    with open(cfg_json_path, "w") as f:
                        json.dump(db, f, indent=4)

                except Exception as e:
                    print(f"[!] Error generating CFG {current_cfg:.3f}: {e}")

        finally:
            del pipe
            del tokenizer
            del text_encoder
            del emb
            del neg_emb
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    else:
        print(f"\n[*] All {num_images} images for seed {seed} already exist! No new images needed.")

    print(f"\n[✓] Completed all generations for CFG sweep. Image directory: {output_dir}")

    # 4. Compile frames into cgfX.mp4 / cfgX.mp4 and copy to static/temp_exp/
    if make_video:
        print("\n" + "=" * 65)
        print("[*] Sorting CFG frames sequentially to compile video...")
        print("=" * 65)

        # Collect candidate frames for this seed and CFG sweep
        frame_dict = {}  # {float_cfg: file_path}

        # First check sweep range frames
        for i in range(num_images):
            c_cfg = round(cfg_start + (i * cfg_step), 4)
            c_str = f"{c_cfg:.3f}".replace(".", "-")
            c_path = os.path.join(output_dir, f"{seed}_{c_str}.png")
            if os.path.exists(c_path) and os.path.getsize(c_path) > 0:
                frame_dict[c_cfg] = c_path
            else:
                c_str_legacy = f"{c_cfg:.2f}".replace(".", "-")
                c_path_legacy = os.path.join(output_dir, f"{seed}_{c_str_legacy}.png")
                if os.path.exists(c_path_legacy) and os.path.getsize(c_path_legacy) > 0:
                    frame_dict[c_cfg] = c_path_legacy

        # Also search output_dir for any other frames generated with this seed
        for fname in os.listdir(output_dir):
            if fname.startswith(f"{seed}_") and fname.endswith(".png"):
                fpath = os.path.join(output_dir, fname)
                try:
                    cfg_num_str = fname.replace(f"{seed}_", "").replace(".png", "").replace("-", ".")
                    c_val = float(cfg_num_str)
                    if c_val not in frame_dict and os.path.getsize(fpath) > 0:
                        frame_dict[c_val] = fpath
                except Exception:
                    pass

        sorted_cfgs = sorted(frame_dict.keys())
        sorted_frame_paths = [frame_dict[k] for k in sorted_cfgs]

        if sorted_frame_paths:
            print(f"[*] Found {len(sorted_frame_paths)} sorted frames for seed {seed} (CFG {sorted_cfgs[0]:.3f} -> {sorted_cfgs[-1]:.3f})")
            local_cgf = os.path.join(output_dir, "cgfX.mp4")
            local_cfg = os.path.join(output_dir, "cfgX.mp4")
            dest_cgf = os.path.join(temp_exp_dir, "cgfX.mp4")
            dest_cfg = os.path.join(temp_exp_dir, "cfgX.mp4")

            success = compile_video_from_frames(sorted_frame_paths, local_cgf, fps=fps)
            if success:
                # Copy/alias to cfgX.mp4 in novel_images
                shutil.copyfile(local_cgf, local_cfg)
                # Copy to static/temp_exp/
                shutil.copyfile(local_cgf, dest_cgf)
                shutil.copyfile(local_cgf, dest_cfg)
                print(f"[✓] Created local videos: {local_cgf} and {local_cfg}")
                print(f"[✓] Copied to temp_exp: {dest_cgf} and {dest_cfg}")

                db["video"] = "cgfX.mp4"
                db["video_frames"] = len(sorted_frame_paths)
                db["video_fps"] = fps
                with open(cfg_json_path, "w") as f:
                    json.dump(db, f, indent=4)
        else:
            print(f"[!] No existing frames found for seed {seed} to compile video.")

    # 5. Optionally invoke join_all_videos if requested
    if run_join_all:
        join_script = os.path.join(BASE_DIR, "join_all_videos")
        if os.path.exists(join_script):
            print("\n[*] Invoking join_all_videos to concatenate temp_exp clips...")
            try:
                subprocess.run([sys.executable, join_script], check=True)
                print("[✓] join_all_videos completed successfully.")
            except Exception as e:
                print(f"[!] join_all_videos failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run SD1.5 LCM inference sweeping CFG with fixed seed.")
    parser.add_argument("-p", "--prompt", default=DEFAULT_PROMPT, help="Prompt text")
    parser.add_argument("-s", "--seed", type=int, default=123456, help="Fixed random seed (default: 123456)")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Model name or index (default: xenogasmLCMEditionSFWNSFW_lcmV5.safetensors)")
    parser.add_argument("-n", "--num-images", type=int, default=50, help="Number of CFG stepped images (default: 50)")
    parser.add_argument("--cfg-start", type=float, default=1.0, help="Starting CFG scale (default: 1.0)")
    parser.add_argument("--cfg-step", type=float, default=0.04, help="CFG step increment (default: 0.04)")
    parser.add_argument("--steps", type=int, default=4, help="Inference steps (default: 4)")
    parser.add_argument("--lora", default=DEFAULT_LORA, help="Path to LoRA file (default: more_details.safetensors)")
    parser.add_argument("--lora-scale", type=float, default=0.25, help="LoRA scale weight (default: 0.25)")
    parser.add_argument("--vae", default=None, help="Optional custom VAE path")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second for generated video (default: 10)")
    parser.add_argument("--no-video", action="store_true", help="Skip video compilation")
    parser.add_argument("--join-all", action="store_true", help="Automatically run join_all_videos after copying to static/temp_exp/")
    args = parser.parse_args()

    resolved_model = resolve_model(args.model)
    if not resolved_model:
        print(f"[!] No valid model found matching: {args.model}")
        return

    run_cfg_sweep(
        model_filename=resolved_model,
        prompt=args.prompt,
        seed=args.seed,
        num_images=args.num_images,
        cfg_start=args.cfg_start,
        cfg_step=args.cfg_step,
        num_steps=args.steps,
        lora_path=resolve_lora(args.lora),
        lora_scale=args.lora_scale,
        vae_path=resolve_vae(args.vae),
        output_base_dir=BASE_DIR,
        fps=args.fps,
        make_video=not args.no_video,
        run_join_all=args.join_all
    )

if __name__ == '__main__':
    main()
