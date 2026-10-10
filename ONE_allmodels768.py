import os
import gc
import signal
import argparse
import torch
from icecream import ic
from diffusers import StableDiffusionPipeline, LCMScheduler

def exit_gracefully(signum, frame):
    print("\n[*] Ctrl+C / termination signal received. Exiting cleanly...")
    os._exit(0)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USB_MODELS_DIR = "/media/jack/USB_USBSSD/models" if os.path.exists("/media/jack/USB_USBSSD/models") else os.path.join(BASE_DIR, "models")
CHECKPOINT_DIR = os.path.join(USB_MODELS_DIR, "checkpoints") if os.path.exists(os.path.join(USB_MODELS_DIR, "checkpoints")) else os.path.join(BASE_DIR, "models", "checkpoints")
LOCAL_LORA = os.path.join(BASE_DIR, "models", "loras", "more_details.safetensors")

NON_BASE_MODEL_KEYWORDS = ["motion", "pose", "controlnet", "depth", "canny", "adapter", "ip-adapter", "t2i"]

def get_available_models():
    if not os.path.exists(CHECKPOINT_DIR):
        return []
    res = []
    for f in sorted(os.listdir(CHECKPOINT_DIR)):
        full = os.path.join(CHECKPOINT_DIR, f)
        if os.path.isdir(full) or f.startswith('.'):
            continue
        if f.endswith(('.safetensors', '.ckpt', '.pt', '.bin')):
            fl = f.lower()
            if any(kw in fl for kw in NON_BASE_MODEL_KEYWORDS):
                continue
            res.append(f)
    return res

MODELS = get_available_models()
DEFAULT_LORA = os.path.join(USB_MODELS_DIR, "loras", "more_details.safetensors") if os.path.exists(os.path.join(USB_MODELS_DIR, "loras", "more_details.safetensors")) else os.path.join(BASE_DIR, "models", "loras", "more_details.safetensors")
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "novel_images")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 768
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

def generate_with_model(
    prompt,
    seed,
    model_filename,
    num_steps=4,
    guidance_scale=1.5,
    lora_path=None,
    lora_scale=0.3,
    vae_path=None,
    width=DEFAULT_WIDTH,
    height=DEFAULT_HEIGHT
):
    model_path = os.path.join(CHECKPOINT_DIR, model_filename)
    if not os.path.exists(model_path):
        print(f"[!] Warning: Model file not found: {model_path}, skipping.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    print(f"\n" + "=" * 60)
    print(f"[*] Loading model: {model_filename} on {device} ({torch_dtype})")
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

    # Swap in LCM scheduler
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)

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

    print(f"[*] Generating image with seed {seed}, steps {num_steps}, cfg {guidance_scale}...")
    image = pipe(
        prompt_embeds=emb,
        negative_prompt_embeds=neg_emb,
        generator=generator,
        num_inference_steps=num_steps,
        guidance_scale=guidance_scale,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT
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
    print(f"[*] Starting batch generation for {total} model(s)...")

    for idx, model_name in enumerate(target_models, 1):
        print(f"[*] [{idx}/{total}] Processing model: {model_name}", flush=True)
        try:
            generate_with_model(
                prompt=args.prompt,
                seed=args.seed,
                model_filename=model_name,
                num_steps=args.steps,
                guidance_scale=args.guidance,
                lora_path=args.lora,
                lora_scale=args.lora_scale,
                vae_path=args.vae,
                width=DEFAULT_WIDTH,
                height=DEFAULT_HEIGHT
            )
        except Exception as e:
            print(f"[!] Error processing {model_name}: {e}")
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    print("\n[✓] All requested models processed successfully!")

if __name__ == '__main__':
    main()