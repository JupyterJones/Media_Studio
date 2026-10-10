#!/usr/bin/env python3
import os
import gc
import signal
import argparse
from random import randint
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
    "wide establishing shot with 24mm ultra-wide lens, capturing the vast car lot, "
    "the protagonist walks onto the car lot, looking around in awe, overcast grey sky with "
    "dappled shade from trees, natural colors, realistic textures, shallow depth of field, "
    "static camera, cinematic photography 8k, sharp focus, extra detail, beautiful composition"
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

def generate_long_prompt(
    prompt=DEFAULT_PROMPT,
    negative_prompt="blurry, low quality, deformed, artifacts, ugly, nudity, large exaggerated breasts, nipples, nsfw, NSFW",
    model_filename=DEFAULT_MODEL,
    seed=123456,
    num_steps=6,
    guidance_scale=1.5,
    lora_path=None,
    lora_scale=0.25,
    vae_path=None,
    output_dir="static/novel_images"
):
    os.makedirs(output_dir, exist_ok=True)
    if os.path.isfile(model_filename):
        model_path = os.path.abspath(model_filename)
        model_filename = os.path.basename(model_path)
    else:
        resolved = resolve_model(model_filename)
        if not resolved or not os.path.exists(resolved):
            print(f"[!] Model file not found: {model_filename}")
            return None
        model_path = resolved
        model_filename = os.path.basename(model_path)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    print(f"[*] Loading model: {model_filename} on {device}")
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
        print(f"    python3 ONEv2.py -m comiccraftLCM_beta4.safetensors")
        return None
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
        print(f"[*] Applying LoRA {os.path.basename(lora_path)} (scale: {lora_scale})")
        pipe.load_lora_weights(lora_path)
        pipe.fuse_lora(lora_scale=lora_scale)

    tokenizer = pipe.tokenizer
    text_encoder = pipe.text_encoder

    emb = encode_chunked(tokenizer, text_encoder, prompt)
    num_chunks = emb.shape[1] // 77
    neg_emb = encode_matching_negative(tokenizer, text_encoder, negative_prompt, num_chunks)

    print(f"[*] Prompt chunks: {num_chunks} | Generating 512x768 image with seed={seed}...")
    generator = torch.Generator(device=device).manual_seed(seed)

    try:
        gc.collect()
        image = pipe(
            prompt_embeds=emb,
            negative_prompt_embeds=neg_emb,
            generator=generator,
            width=512,
            height=768,
            num_inference_steps=num_steps,
            guidance_scale=guidance_scale,
        ).images[0]

        model_stem = model_filename.replace(".safetensors", "")
        out_filename = f"{seed}_{model_stem}_longprompt.png"
        out_path = os.path.join(output_dir, out_filename)
        image.save(out_path)
        print(f"[+] Saved: {out_path}")
        return out_path
    finally:
        del pipe
        del tokenizer
        del text_encoder
        del emb
        del neg_emb
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

def main():
    parser = argparse.ArgumentParser(description="Long-prompt chunked embedding SD 1.5 LCM generator (512x768)")
    parser.add_argument("-p", "--prompt", default=DEFAULT_PROMPT, help="Positive long prompt")
    parser.add_argument("--negative-prompt", default="blurry, low quality, deformed", help="Negative prompt")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Model name or index")
    parser.add_argument("-s", "--seed", type=int, default=123456, help="Seed")
    parser.add_argument("--steps", type=int, default=6, help="Inference steps (default: 6)")
    parser.add_argument("--guidance", type=float, default=1.5, help="Guidance scale (default: 1.5)")
    parser.add_argument("--lora", default=None, help="Path to LoRA")
    parser.add_argument("--lora-scale", type=float, default=0.25, help="LoRA scale")
    parser.add_argument("--vae", default=None, help="Path to custom VAE")
    parser.add_argument("-o", "--output-dir", default="static/novel_images", help="Output directory")
    args = parser.parse_args()

    resolved = resolve_model(args.model)
    if not resolved:
        print(f"[!] Unknown model: {args.model}")
        return

    generate_long_prompt(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        model_filename=resolved,
        seed=args.seed,
        num_steps=args.steps,
        guidance_scale=args.guidance,
        lora_path=resolve_lora(args.lora),
        lora_scale=args.lora_scale,
        vae_path=resolve_vae(args.vae),
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()