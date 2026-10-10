#!/usr/bin/env python3
import os
import gc
import argparse
import json
from datetime import datetime
import torch
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, DPMSolverMultistepScheduler, LCMScheduler, EulerDiscreteScheduler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMFY_MODELS_DIR = "/home/jack/Desktop/Comfy-UI/models/checkpoints"
USB_MODELS_DIR = "/media/jack/USB_USBSSD/models"
CHECKPOINT_DIRS = [
    COMFY_MODELS_DIR,
    os.path.join(USB_MODELS_DIR, "checkpoints"),
    os.path.join(BASE_DIR, "models", "checkpoints")
]

def find_available_models():
    found = []
    seen = set()
    for d in CHECKPOINT_DIRS:
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith((".safetensors", ".ckpt")) and f not in seen:
                    seen.add(f)
                    full_p = os.path.join(d, f)
                    is_lcm = "lcm" in f.lower()
                    clean_name = f.replace(".safetensors", "").replace(".ckpt", "").replace("_", " ")
                    found.append({
                        "filename": f,
                        "name": clean_name,
                        "path": full_p,
                        "is_lcm": is_lcm,
                        "size_gb": round(os.path.getsize(full_p) / (1024 ** 3), 2)
                    })
    return found

def resolve_model_path(model_arg):
    if not model_arg:
        model_arg = "rmbtestLCM_rmbtest4V10.safetensors"

    if os.path.isfile(model_arg):
        return os.path.abspath(model_arg)

    # Check directories
    for d in CHECKPOINT_DIRS:
        if os.path.isdir(d):
            cand = os.path.join(d, model_arg)
            if os.path.isfile(cand):
                return cand
            if not cand.endswith(".safetensors") and os.path.isfile(cand + ".safetensors"):
                return cand + ".safetensors"
            for f in os.listdir(d):
                if f.endswith((".safetensors", ".ckpt")) and model_arg.lower() in f.lower():
                    return os.path.join(d, f)

    default_p = os.path.join(COMFY_MODELS_DIR, "rmbtestLCM_rmbtest4V10.safetensors")
    if os.path.isfile(default_p):
        return default_p
    return model_arg

DEFAULT_CHECKPOINT = resolve_model_path("rmbtestLCM_rmbtest4V10.safetensors")

def encode_chunked_prompt(tokenizer, text_encoder, prompt, device, max_chunks=None):
    raw_tokens = tokenizer(prompt, padding=False, truncation=False, return_tensors="pt").input_ids[0]
    bos = raw_tokens[0:1]
    eos = raw_tokens[-1:]
    content = raw_tokens[1:-1]
    
    if len(raw_tokens) <= 77 and (max_chunks is None or max_chunks == 1):
        inputs = tokenizer(prompt, padding="max_length", max_length=77, truncation=True, return_tensors="pt")
        with torch.no_grad():
            return text_encoder(inputs.input_ids.to(device))[0]
            
    chunks = [content[i:i+75] for i in range(0, max(1, len(content)), 75)]
    embs = []
    for c in chunks:
        t = torch.cat([bos, c, eos])
        pad_len = 77 - len(t)
        if pad_len > 0:
            t = torch.nn.functional.pad(t, (0, pad_len), value=tokenizer.pad_token_id)
        with torch.no_grad():
            embs.append(text_encoder(t.unsqueeze(0).to(device))[0])
            
    return torch.cat(embs, dim=1)

def encode_matching_negative(tokenizer, text_encoder, negative_prompt, target_chunks, device):
    if not negative_prompt:
        negative_prompt = ""
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
            embs.append(text_encoder(t.unsqueeze(0).to(device))[0])
    return torch.cat(embs, dim=1)

def main():
    parser = argparse.ArgumentParser(description="Offline Stable Diffusion CLI Generator (Corrected & Optimized)")
    parser.add_argument("--prompt", type=str, default="", help="Positive prompt for generation")
    parser.add_argument("--negative_prompt", type=str, default=None, help="Negative prompt for generation")
    parser.add_argument("--character", type=str, default=None, help="Character name for tagging and organization")
    parser.add_argument("--mode", type=str, default="txt2img", choices=["txt2img", "img2img"], help="Pipeline mode: txt2img or img2img")
    parser.add_argument("--init_image", type=str, default=None, help="Path to initial image for img2img mode")
    parser.add_argument("--strength", type=float, default=0.65, help="Transformation strength for img2img (0.05 to 1.0)")
    parser.add_argument("--model", type=str, default="rmbtestLCM_rmbtest4V10.safetensors", help="Path or name of local .safetensors model file")
    parser.add_argument("--list_models", action="store_true", help="Print available models JSON and exit")
    parser.add_argument("--vae", type=str, default=None, help="Path to local VAE safetensors/ckpt file (optional)")
    parser.add_argument("--lora", type=str, default=None, help="Path to primary local LoRA safetensors file (optional)")
    parser.add_argument("--lora_scale", type=float, default=0.75, help="Scale/strength of primary LoRA")
    parser.add_argument("--lora2", type=str, default=None, help="Path to secondary local LoRA safetensors file (optional)")
    parser.add_argument("--lora2_scale", type=float, default=0.75, help="Scale/strength of secondary LoRA")
    parser.add_argument("--steps", type=int, default=5, help="Number of inference steps (Standard: 25-45, LCM: 4-8)")
    parser.add_argument("--guidance", type=float, default=1.2, help="CFG guidance scale (Standard: 7.0-9.0, LCM: 1.0-2.0)")
    parser.add_argument("--width", type=int, default=512, help="Image width (e.g., 512, 768, 1024)")
    parser.add_argument("--height", type=int, default=768, help="Image height (e.g., 512, 768, 1024)")
    parser.add_argument("--seed", type=int, default=12345, help="Random seed for deterministic generation")
    parser.add_argument("--output_dir", type=str, default="./static/novel_images", help="Directory to save generated images")
    parser.add_argument("--device", type=str, default="auto", help="Execution device: auto, cuda, mps, or cpu")
    parser.add_argument("--num_images", type=int, default=1, help="Number of images to generate (default: 1)")
    parser.add_argument("--threads", type=int, default=4, help="Limit CPU execution threads (default: 4)")
    args = parser.parse_args()

    if args.list_models:
        models = find_available_models()
        print(json.dumps(models, indent=2))
        return

    if not args.prompt:
        parser.error("--prompt is required for generation")

    # Configure CPU thread limits
    if args.threads > 0:
        torch.set_num_threads(args.threads)
        try:
            torch.set_num_interop_threads(args.threads)
        except Exception:
            pass
        os.environ["OMP_NUM_THREADS"] = str(args.threads)
        os.environ["MKL_NUM_THREADS"] = str(args.threads)
        os.environ["OPENBLAS_NUM_THREADS"] = str(args.threads)
        os.environ["NUMEXPR_NUM_THREADS"] = str(args.threads)
        print(f"[*] CPU thread limit set to: {args.threads}")

    # 1. Device selection
    if args.device == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    else:
        device = args.device
    
    print(f"[*] Target generation device: {device.upper()}")
    if device == "cpu":
        print("[!] WARNING: Running on CPU")

    # 2. Determine if LCM or Standard model based on name/steps
    model_path = resolve_model_path(args.model)
    if os.path.isdir(model_path):
        print(f"[*] Detected that --model is a directory: {model_path}")
        checkpoints = []
        for root, dirs, files in os.walk(model_path):
            for file in files:
                if file.endswith((".safetensors", ".ckpt")):
                    checkpoints.append(os.path.join(root, file))
        
        if not checkpoints:
            print(f"\n[CRITICAL ERROR] The directory '{model_path}' contains no '.safetensors' or '.ckpt' model files!")
            print("[*] Please download a Stable Diffusion checkpoint (e.g. v1-5-pruned-emaonly.safetensors) and place it there, or point to a specific file path.")
            return
        elif len(checkpoints) == 1:
            selected_model = checkpoints[0]
            print(f"[+] Found exactly one model in the directory: {os.path.basename(selected_model)}")
            print(f"[*] Automatically loading: {selected_model}")
            model_path = selected_model
        else:
            print(f"\n[CRITICAL ERROR] The path provided is a directory containing MULTIPLE checkpoints:")
            for cp in checkpoints:
                print(f"   - {cp}")
            print("\n[*] Please specify the exact file path to the model you want to run. For example:")
            print(f"    python generate.py --prompt \"{args.prompt}\" --model \"{checkpoints[0]}\"")
            return

    file_size_gb = os.path.getsize(model_path) / (1024 ** 3) if os.path.isfile(model_path) else 2.0
    is_xl = "xl" in os.path.basename(model_path).lower() or file_size_gb > 5.0
    is_large_model = file_size_gb > 3.0 or is_xl
    is_lcm_model = "lcm" in model_path.lower() or args.steps <= 12

    arch_name = "SDXL" if is_xl else ("LCM Model" if is_lcm_model else "Standard SD 1.5")
    print(f"[*] Detected model architecture: {arch_name} ({file_size_gb:.2f} GB)")

    # 3. Load single file pipeline (from_single_file)
    print(f"[*] Loading model checkpoint from: {model_path}")
    try:
        if device == "cuda":
            torch_dtype = torch.float16
        elif is_large_model:
            # On CPU, large models (>3GB / SDXL) use bfloat16 to cut RAM in half and prevent OOM
            torch_dtype = torch.bfloat16
            print(f"[*] Large model detected ({file_size_gb:.2f} GB) -> enabled torch.bfloat16 for 50% CPU RAM savings")
        else:
            # Standard SD 1.5 models use float32 on CPU for normal execution
            torch_dtype = torch.float32

        PipelineClass = StableDiffusionXLPipeline if is_xl else StableDiffusionPipeline
        
        pipe = PipelineClass.from_single_file(
            model_path,
            torch_dtype=torch_dtype,
            use_safetensors=True,
            extract_ema=True,
            safety_checker=None,
            requires_safety_checker=False
        )
    except Exception as e:
        print(f"[ERROR] Failed to load model from path. Ensure the file exists and is valid. Details: {e}")
        return

    pipe = pipe.to(device)

    # 4. CPU / Memory Optimization
    if device == "cpu":
        pipe.enable_attention_slicing(1)
        if hasattr(pipe, "vae") and pipe.vae is not None:
            if hasattr(pipe.vae, "enable_slicing"):
                pipe.vae.enable_slicing()
            if hasattr(pipe.vae, "enable_tiling"):
                pipe.vae.enable_tiling()
    elif device == "cuda":
        # Memory optimization for GPUs
        pipe.enable_xformers_memory_efficient_attention() if hasattr(pipe, "enable_xformers_memory_efficient_attention") else pipe.enable_attention_slicing()

    # 5. Fix Scheduler / Sampler configuration
    is_lightning = "lightning" in (args.lora or "").lower() or "lightning" in (args.lora2 or "").lower() or "lightning" in model_path.lower()
    if is_lightning:
        print("[*] Setting scheduler to EulerDiscreteScheduler (trailing spacing required for Lightning)")
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
    elif is_lcm_model:
        print("[*] Setting scheduler to LCMScheduler (required for Latent Consistency)")
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    else:
        print("[*] Setting scheduler to DPMSolverMultistepScheduler (DPM++ 2M Karras equivalent for standard models)")
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config,
            use_karras_sigmas=True
        )

    # 5.5. Load custom VAE if provided
    if args.vae and os.path.exists(args.vae):
        print(f"[*] Loading custom VAE from: {args.vae}")
        try:
            if "taesd" in args.vae.lower():
                from diffusers import AutoencoderTiny
                taesd_repo = "madebyollin/taesdxl" if is_xl else "madebyollin/taesd"
                if os.path.isdir(args.vae) and os.path.exists(os.path.join(args.vae, "config.json")):
                    custom_vae = AutoencoderTiny.from_pretrained(args.vae, torch_dtype=torch_dtype)
                else:
                    parent_dir = os.path.dirname(args.vae)
                    sibling_taesd = os.path.join(parent_dir, "taesdxl" if is_xl else "taesd")
                    if os.path.isdir(sibling_taesd) and os.path.exists(os.path.join(sibling_taesd, "config.json")):
                        custom_vae = AutoencoderTiny.from_pretrained(sibling_taesd, torch_dtype=torch_dtype)
                    elif os.path.isdir("/media/jack/USB_USBSSD/models/vae/taesd") and not is_xl:
                        custom_vae = AutoencoderTiny.from_pretrained("/media/jack/USB_USBSSD/models/vae/taesd", torch_dtype=torch_dtype)
                    else:
                        custom_vae = AutoencoderTiny.from_pretrained(taesd_repo, torch_dtype=torch_dtype)
            else:
                from diffusers import AutoencoderKL
                custom_vae = AutoencoderKL.from_single_file(args.vae, torch_dtype=torch_dtype)

            pipe.vae = custom_vae.to(device)
            if hasattr(pipe.vae, "enable_slicing"):
                pipe.vae.enable_slicing()
            if hasattr(pipe.vae, "enable_tiling"):
                pipe.vae.enable_tiling()
            print(f"[+] Attached custom VAE: {os.path.basename(args.vae)}")
        except Exception as e:
            print(f"[!] Warning: Failed to load custom VAE ({e}). Continuing with model VAE.")

    # 6. Load and fuse LoRA weights if provided
    if args.lora and os.path.exists(args.lora):
        print(f"[*] Loading primary LoRA from: {args.lora} with scale {args.lora_scale}")
        try:
            pipe.load_lora_weights(args.lora)
            pipe.fuse_lora(lora_scale=args.lora_scale)
            print(f"[+] Attached and fused primary LoRA: {os.path.basename(args.lora)}")
        except Exception as e:
            try:
                pipe.load_lora_weights(args.lora, adapter_name="custom_lora1")
                pipe.fuse_lora(lora_scale=args.lora_scale)
                print(f"[+] Attached and fused primary LoRA (with adapter): {os.path.basename(args.lora)}")
            except Exception as e2:
                print(f"[!] Warning: Failed to load LoRA 1 ({e2})")
    elif args.lora:
        print(f"[!] Warning: Primary LoRA path '{args.lora}' not found. Skipping.")

    if args.lora2 and os.path.exists(args.lora2):
        print(f"[*] Loading secondary LoRA from: {args.lora2} with scale {args.lora2_scale}")
        try:
            pipe.load_lora_weights(args.lora2)
            pipe.fuse_lora(lora_scale=args.lora2_scale)
            print(f"[+] Attached and fused secondary LoRA: {os.path.basename(args.lora2)}")
        except Exception as e:
            try:
                pipe.load_lora_weights(args.lora2, adapter_name="custom_lora2")
                pipe.fuse_lora(lora_scale=args.lora2_scale)
                print(f"[+] Attached and fused secondary LoRA (with adapter): {os.path.basename(args.lora2)}")
            except Exception as e2:
                print(f"[!] Warning: Failed to load LoRA 2 ({e2})")
    elif args.lora2:
        print(f"[!] Warning: Secondary LoRA path '{args.lora2}' not found. Skipping.")

    # 7. Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    db_path = os.path.join(args.output_dir, "generations.json")

    # 8. Load generations history database
    db = {"next_image_id": 1, "runs": []}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r") as f:
                db = json.load(f)
        except Exception:
            pass

    # 8.5 Setup Img2Img if requested
    init_image = None
    if args.mode == "img2img":
        if not args.init_image or not os.path.exists(args.init_image):
            print(f"[CRITICAL ERROR] Initial image '{args.init_image}' not found for img2img mode!")
            return
        try:
            from PIL import Image
            from diffusers import StableDiffusionImg2ImgPipeline
            init_image = Image.open(args.init_image).convert("RGB")
            init_image = init_image.resize((args.width, args.height), Image.Resampling.LANCZOS)
            pipe = StableDiffusionImg2ImgPipeline(**pipe.components)
            print(f"[*] Initialized Img2Img pipeline with source: {args.init_image} (strength: {args.strength})")
        except Exception as e:
            print(f"[ERROR] Failed to initialize img2img pipeline: {e}")
            return

    # 8.8 Chunked Prompt Embedding Encoding (Supports unlimited prompt tokens with zero truncation)
    prompt_embeds = None
    negative_prompt_embeds = None
    if hasattr(pipe, "tokenizer") and hasattr(pipe, "text_encoder") and pipe.tokenizer is not None and pipe.text_encoder is not None:
        try:
            prompt_embeds = encode_chunked_prompt(pipe.tokenizer, pipe.text_encoder, args.prompt, device)
            num_chunks = prompt_embeds.shape[1] // 77
            negative_prompt_embeds = encode_matching_negative(pipe.tokenizer, pipe.text_encoder, args.negative_prompt or "", num_chunks, device)
            print(f"[*] Encoded prompt into {num_chunks} chunk(s) ({num_chunks * 77} max tokens) - no truncation!")
        except Exception as e:
            print(f"[!] Warning: Chunked prompt encoding failed ({e}), falling back to direct prompt strings.")
            prompt_embeds = None
            negative_prompt_embeds = None

    # 9. Perform Generation Loop
    current_seed = args.seed
    model_name = os.path.basename(model_path).replace(".", "_")

    for i in range(args.num_images):
        print(f"[*] Run {i+1}/{args.num_images} [{args.mode}]: Generating with seed={current_seed}, steps={args.steps}, CFG={args.guidance}")
        generator = torch.Generator(device=device).manual_seed(current_seed)
        
        gc.collect()
        with torch.inference_mode():
            try:
                gen_kwargs = {
                    "num_inference_steps": args.steps,
                    "guidance_scale": args.guidance,
                    "generator": generator
                }
                if prompt_embeds is not None and negative_prompt_embeds is not None:
                    gen_kwargs["prompt_embeds"] = prompt_embeds
                    gen_kwargs["negative_prompt_embeds"] = negative_prompt_embeds
                else:
                    gen_kwargs["prompt"] = args.prompt
                    gen_kwargs["negative_prompt"] = args.negative_prompt

                if args.mode == "img2img":
                    gen_kwargs["image"] = init_image
                    gen_kwargs["strength"] = args.strength
                    output = pipe(**gen_kwargs)
                else:
                    gen_kwargs["width"] = args.width
                    gen_kwargs["height"] = args.height
                    output = pipe(**gen_kwargs)
                image = output.images[0]
            except Exception as e:
                print(f"[ERROR] Generation failed: {e}")
                break

        # Save image
        img_id = db.get("next_image_id", 1)
        char_prefix = f"{args.character}_" if args.character else ""
        filename = f"{char_prefix}{model_name}_{args.mode}_img_{img_id:06d}.png"
        save_path = os.path.join(args.output_dir, filename)
        image.save(save_path)
        print(f"[+] Saved image to: {save_path}")

        # Record generation log
        db["runs"].append({
            "image_id": img_id,
            "character": args.character,
            "file": filename,
            "timestamp": datetime.now().isoformat(),
            "mode": args.mode,
            "prompt": args.prompt,
            "negative_prompt": args.negative_prompt,
            "steps": args.steps,
            "guidance_scale": args.guidance,
            "seed": current_seed,
            "width": args.width,
            "height": args.height,
            "model": model_path,
            "strength": args.strength if args.mode == "img2img" else None,
            "init_image": args.init_image if args.mode == "img2img" else None
        })
        db["next_image_id"] = img_id + 1
        
        # Save updated database
        with open(db_path, "w") as f:
            json.dump(db, f, indent=4)

        current_seed += 1

    print(f"[*] DONE. All {args.num_images} image(s) processed and logged.")

if __name__ == "__main__":
    main()
