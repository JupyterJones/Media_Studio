import os
import gc
import sys
import json
import signal
import shutil
import tempfile
import argparse
import subprocess
from random import randint
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

    temp_dir = tempfile.mkdtemp(prefix="seed_video_")
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

def generate_seeds_for_model(
    model_filename,
    prompt,
    base_seed=123456,
    num_seeds=30,
    num_steps=4,
    guidance_scale=1.5,
    lora_path=None,
    lora_scale=0.25,
    vae_path=None,
    output_base_dir=BASE_DIR,
    fps=10,
    make_video=True
):
    if os.path.isfile(model_filename):
        model_path = os.path.abspath(model_filename)
        model_filename = os.path.basename(model_path)
    else:
        resolved = resolve_model(model_filename)
        if not resolved or not os.path.exists(resolved):
            print(f"[!] Warning: Model file not found: {model_filename}, skipping.")
            return
        model_path = resolved
        model_filename = os.path.basename(model_path)

    output_dir = os.path.join(output_base_dir, "static", "novel_images")
    temp_exp_dir = os.path.join(output_base_dir, "static", "temp_exp")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_exp_dir, exist_ok=True)
    seed_json_path = os.path.join(output_dir, "seed.json")

    print(f"\n" + "=" * 65)
    print(f"[*] Target Model: {model_filename}")
    print(f"[*] Destination Directory: {output_dir}")
    print(f"[*] Tracking Database: {seed_json_path}")
    print(f"[*] Seeds: {num_seeds} (base: {base_seed}, steps: {num_steps}, cfg: {guidance_scale})")
    print(f"=" * 65)

    # 1. Load or initialize seed.json
    db = {}
    if os.path.exists(seed_json_path):
        try:
            with open(seed_json_path, "r") as f:
                db = json.load(f)
            print(f"[*] Loaded existing database from {seed_json_path} ({len(db.get('runs', []))} past records)")
        except Exception as e:
            print(f"[!] Warning: Failed to read {seed_json_path}: {e}. Starting fresh.")
            db = {}

    if not isinstance(db, dict) or "runs" not in db:
        db = {
            "base_seed": base_seed,
            "num_seeds": num_seeds,
            "prompt": prompt,
            "model": model_filename,
            "next_image_id": 1,
            "runs": []
        }

    # 2. Check which seed images already exist on disk
    tasks_to_generate = []
    for inc in range(num_seeds):
        current_seed = base_seed + inc
        filename = f"{current_seed}_{model_filename}_output.png"
        output_path = os.path.join(output_dir, filename)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            if not any(r.get("file") == filename for r in db["runs"]):
                mtime = os.path.getmtime(output_path)
                img_id = db.get("next_image_id", len(db["runs"]) + 1)
                db["runs"].append({
                    "image_id": img_id,
                    "file": filename,
                    "timestamp": datetime.fromtimestamp(mtime).isoformat(),
                    "mode": "seed_explorer",
                    "prompt": prompt,
                    "steps": num_steps,
                    "guidance_scale": guidance_scale,
                    "seed": current_seed,
                    "width": 512,
                    "height": 768,
                    "model": model_filename
                })
                db["next_image_id"] = img_id + 1
            print(f"[*] [{inc + 1}/{num_seeds}] Resuming: {filename} (seed {current_seed}) already exists. Skipping.")
        else:
            tasks_to_generate.append((inc, current_seed, filename, output_path))

    with open(seed_json_path, "w") as f:
        json.dump(db, f, indent=4)

    # 3. Generate missing seed images if any
    if tasks_to_generate:
        start_inc, first_seed, _, _ = tasks_to_generate[0]
        print(f"\n[*] Resuming generation at seed {first_seed} (step {start_inc + 1}/{num_seeds}, {len(tasks_to_generate)} remaining)...")

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
            print(f"    python3 ONE_model_seeds.py -m comiccraftLCM_beta4.safetensors")
            return []
        pipe.to(device)
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)

        if device == "cpu":
            pipe.enable_attention_slicing(1)
            is_taesd = vae_path and "taesd" in vae_path.lower()
            if not is_taesd and hasattr(pipe, "vae") and pipe.vae is not None:
                if hasattr(pipe.vae, "enable_slicing"):
                    pipe.vae.enable_slicing()
                if hasattr(pipe.vae, "enable_tiling"):
                    pipe.vae.enable_tiling()

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
            for (inc, current_seed, filename, output_path) in tasks_to_generate:
                print(f"[*] [{inc + 1}/{num_seeds}] Generating model: {model_filename} | Seed: {current_seed}", flush=True)
                try:
                    generator = torch.Generator(device=device).manual_seed(current_seed)
                    image = pipe(
                        prompt_embeds=emb,
                        negative_prompt_embeds=neg_emb,
                        generator=generator,
                        width=512,
                        height=768,
                        num_inference_steps=num_steps,
                        guidance_scale=guidance_scale,
                    ).images[0]

                    image.save(output_path)
                    print(f"[+] [{inc + 1}/{num_seeds}] Saved: {output_path}")

                    # Incremental update to seed.json
                    img_id = db.get("next_image_id", len(db["runs"]) + 1)
                    db["runs"].append({
                        "image_id": img_id,
                        "file": filename,
                        "timestamp": datetime.now().isoformat(),
                        "mode": "seed_explorer",
                        "prompt": prompt,
                        "steps": num_steps,
                        "guidance_scale": guidance_scale,
                        "seed": current_seed,
                        "width": 512,
                        "height": 768,
                        "model": model_filename
                    })
                    db["next_image_id"] = img_id + 1
                    db["last_completed_seed"] = current_seed
                    db["last_completed_file"] = filename
                    with open(seed_json_path, "w") as f:
                        json.dump(db, f, indent=4)

                except Exception as e:
                    print(f"[!] Error generating seed {current_seed} for {model_filename}: {e}")
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
        print(f"\n[*] All {num_seeds} seeds for model {model_filename} already exist! No new images needed.")

    print(f"\n[✓] Completed all generations for seed exploration. Directory: {output_dir}")

    # 4. Compile sequential video (seedX.mp4 / seedsX.mp4)
    if make_video:
        print("\n" + "=" * 65)
        print("[*] Sorting seed frames sequentially to compile video...")
        print("=" * 65)

        sorted_frame_paths = []
        for inc in range(num_seeds):
            c_seed = base_seed + inc
            c_fn = f"{c_seed}_{model_filename}_output.png"
            c_fp = os.path.join(output_dir, c_fn)
            if os.path.exists(c_fp) and os.path.getsize(c_fp) > 0:
                sorted_frame_paths.append(c_fp)

        if sorted_frame_paths:
            print(f"[*] Found {len(sorted_frame_paths)} sorted frames for seed range {base_seed} -> {base_seed + len(sorted_frame_paths) - 1}")
            local_seed_mp4 = os.path.join(output_dir, "seedX.mp4")
            local_seeds_mp4 = os.path.join(output_dir, "seedsX.mp4")
            dest_seed_mp4 = os.path.join(temp_exp_dir, "seedX.mp4")
            dest_seeds_mp4 = os.path.join(temp_exp_dir, "seedsX.mp4")

            success = compile_video_from_frames(sorted_frame_paths, local_seed_mp4, fps=fps)
            if success:
                shutil.copyfile(local_seed_mp4, local_seeds_mp4)
                shutil.copyfile(local_seed_mp4, dest_seed_mp4)
                shutil.copyfile(local_seed_mp4, dest_seeds_mp4)
                print(f"[✓] Created local videos: {local_seed_mp4} and {local_seeds_mp4}")
                print(f"[✓] Copied to temp_exp: {dest_seed_mp4} and {dest_seeds_mp4}")

                db["video"] = "seedX.mp4"
                db["video_frames"] = len(sorted_frame_paths)
                db["video_fps"] = fps
                with open(seed_json_path, "w") as f:
                    json.dump(db, f, indent=4)
        else:
            print(f"[!] No existing frames found for model {model_filename} to compile video.")

def generate_with_model(
    prompt,
    seed,
    model_filename,
    output_dir=None,
    num_steps=4,
    guidance_scale=1.5,
    lora_path=None,
    lora_scale=0.25,
    vae_path=None
):
    if output_dir is None:
        model_dir_name = model_filename.replace(".safetensors", "")
        output_dir = os.path.join(BASE_DIR, model_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    if os.path.isfile(model_filename):
        model_path = os.path.abspath(model_filename)
        model_filename = os.path.basename(model_path)
    else:
        resolved = resolve_model(model_filename)
        if not resolved or not os.path.exists(resolved):
            print(f"[!] Warning: Model file not found: {model_filename}, skipping.")
            return
        model_path = resolved
        model_filename = os.path.basename(model_path)

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
        print(f"    python3 ONE_model_seeds.py -m comiccraftLCM_beta4.safetensors")
        return []
    pipe.to(device)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)

    # CPU / Memory Optimization
    if device == "cpu":
        pipe.enable_attention_slicing(1)
        is_taesd = vae_path and "taesd" in vae_path.lower()
        if not is_taesd and hasattr(pipe, "vae") and pipe.vae is not None:
            if hasattr(pipe.vae, "enable_slicing"):
                pipe.vae.enable_slicing()
            if hasattr(pipe.vae, "enable_tiling"):
                pipe.vae.enable_tiling()

    if lora_path and os.path.exists(lora_path) and lora_scale > 0:
        pipe.load_lora_weights(lora_path)
        pipe.fuse_lora(lora_scale=lora_scale)

    tokenizer = pipe.tokenizer
    text_encoder = pipe.text_encoder

    emb = encode_chunked(tokenizer, text_encoder, prompt)
    num_chunks = emb.shape[1] // 77
    neg_emb = encode_matching_negative(tokenizer, text_encoder, "blurry, low quality, deformed", num_chunks)

    generator = torch.Generator(device=device).manual_seed(seed)
    image = pipe(
        prompt_embeds=emb,
        negative_prompt_embeds=neg_emb,
        generator=generator,
        width=512,
        height=768,
        num_inference_steps=num_steps,
        guidance_scale=guidance_scale,
    ).images[0]

    output_path = os.path.join(output_dir, f"{seed}_{model_filename}_output.png")
    image.save(output_path)
    print(f"[+] Successfully saved output: {output_path}")

    del pipe
    del tokenizer
    del text_encoder
    del emb
    del neg_emb
    del image
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def main():
    parser = argparse.ArgumentParser(description="Run SD1.5 LCM inference across seeds for model(s).")
    parser.add_argument("-p", "--prompt", default=(
        "Extremely old colossal carved stone statues, the size of giant trees"
        "depicting farm animals such as ducks, roosters, chickens, and horses."
        "Their surfaces are cracked and weathered, with peeling dark green and burnt orange paint"
        "The stone statues of animals resemble an ancient dystopian zoo overgrown with weeds and dead vines"
    ), help="Prompt text")
    parser.add_argument("-s", "--seed", type=int, default=123456, help="Random starting seed (default: 123456)")
    parser.add_argument("-n", "--num-seeds", type=int, default=30, help="Number of seeds to generate (default: 30)")
    parser.add_argument("--steps", type=int, default=4, help="Inference steps (default: 4)")
    parser.add_argument("--guidance", type=float, default=1.5, help="Guidance scale (default: 1.5)")
    parser.add_argument("-m", "--model", default="delusionsLCM_v20", help="Specific model name, index, or comma-separated list (default: delusionsLCM_v20)")
    parser.add_argument("--lora", default=DEFAULT_LORA, help="Path to LoRA file (default: more_details.safetensors)")
    parser.add_argument("--lora-scale", type=float, default=0.25, help="LoRA scale weight (0 to disable, default: 0.25)")
    parser.add_argument("--vae", default=None, help="Optional path to custom VAE (default: uses model's built-in VAE)")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second for generated video (default: 10)")
    parser.add_argument("--no-video", action="store_true", help="Skip video compilation")
    args = parser.parse_args()

    target_models = []
    if args.model:
        if args.model.strip().lower() == "all":
            target_models = list(MODELS)
        else:
            for item in args.model.split(","):
                resolved = resolve_model(item)
                if resolved and resolved not in target_models:
                    target_models.append(resolved)
                elif not resolved:
                    print(f"[!] Warning: No model matched '{item.strip()}'")
    else:
        target_models = [DEFAULT_MODEL]

    if not target_models:
        print(f"[!] No valid models matched selection: {args.model}")
        return

    total = len(target_models)
    print(f"[*] Starting seed batch generation for {total} model(s)...")

    for idx, model_filename in enumerate(target_models, 1):
        print(f"\n[*] [{idx}/{total}] Processing model: {model_filename}")
        try:
            generate_seeds_for_model(
                model_filename=model_filename,
                prompt=args.prompt,
                base_seed=args.seed,
                num_seeds=args.num_seeds,
                num_steps=args.steps,
                guidance_scale=args.guidance,
                lora_path=resolve_lora(args.lora),
                lora_scale=args.lora_scale,
                vae_path=resolve_vae(args.vae),
                output_base_dir=BASE_DIR,
                fps=args.fps,
                make_video=not args.no_video
            )
        except Exception as e:
            print(f"[!] Error processing model {model_filename}: {e}")

    print("\n[✓] All requested models and seeds processed successfully!")

if __name__ == '__main__':
    main()