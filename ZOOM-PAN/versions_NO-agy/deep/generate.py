#!/usr/bin/env python3
import os
import argparse
import json
from datetime import datetime
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler, LCMScheduler

def main():
    parser = argparse.ArgumentParser(description="Offline Stable Diffusion CLI Generator (Corrected & Optimized)")
    parser.add_argument("--prompt", type=str, required=True, help="Positive prompt for generation")
    parser.add_argument("--negative_prompt", type=str, default="blurry, out of focus, text, captions, low quality, pixelated, worst quality", help="Negative prompt")
    parser.add_argument("--model", default="/home/jack/Desktop/Comfy-UI/models/checkpoints/comiccraftLCM_beta4.safetensors")
    #type=str, required=True, help="Path to your local .safetensors model file")
    parser.add_argument("--lora", type=str, default=None, help="Path to local LoRA safetensors file (optional)")
    parser.add_argument("--lora_scale", type=float, default=0.15, help="Scale/strength of the loaded LoRA")
    parser.add_argument("--steps", type=int, default=5, help="Number of inference steps (Standard: 25-45, LCM: 4-8)")
    parser.add_argument("--guidance", type=float, default=1.5, help="CFG guidance scale (Standard: 7.0-9.0, LCM: 1.0-2.0)")
    parser.add_argument("--width", type=int, default=512, help="Image width (e.g., 512, 768, 1024)")
    parser.add_argument("--height", type=int, default=768, help="Image height (e.g., 512, 768, 1024)")
    parser.add_argument("--seed", type=int, default=12345, help="Random seed for deterministic generation")
    parser.add_argument("--output_dir", type=str, default="static/uploads/", help="Directory to save generated images")
    parser.add_argument("--device", type=str, default="auto", help="Execution device: auto, cuda, mps, or cpu")
    args = parser.parse_args()

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
        print("[!] WARNING: Running on CPU will be extremely slow. Enable CUDA/GPU if possible.")

    # 2. Determine if LCM or Standard model based on name/steps
    is_lcm_model = "lcm" in args.model.lower() or args.steps <= 12
    print(f"[*] Detected model type: {'Latent Consistency Model (LCM)' if is_lcm_model else 'Standard SD 1.5'}")

    # 3. Load single file pipeline (from_single_file)
    print(f"[*] Loading model checkpoint from: {args.model}")
    try:
        # Load pipeline in fp16 if running on CUDA for 2x speedup and 50% memory savings
        torch_dtype = torch.float16 if device == "cuda" else torch.float32
        
        pipe = StableDiffusionPipeline.from_single_file(
            args.model,
            torch_dtype=torch_dtype,
            use_safetensors=True,
            safety_checker=None,
            requires_safety_checker=False
        )
    except Exception as e:
        print(f"[ERROR] Failed to load model from path. Ensure the file exists and is valid. Details: {e}")
        return

    pipe = pipe.to(device)

    # 4. CPU / Memory Optimization
    if device == "cpu":
        pipe.enable_attention_slicing()
    elif device == "cuda":
        # Memory optimization for GPUs
        pipe.enable_xformers_memory_efficient_attention() if hasattr(pipe, "enable_xformers_memory_efficient_attention") else pipe.enable_attention_slicing()

    # 5. Fix Scheduler / Sampler configuration
    # Crucial step: Standard models and LCM models require fundamentally different schedulers!
    if is_lcm_model:
        print("[*] Setting scheduler to LCMScheduler (required for Latent Consistency)")
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    else:
        print("[*] Setting scheduler to DPMSolverMultistepScheduler (DPM++ 2M Karras equivalent for standard models)")
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config,
            use_karras_sigmas=True
        )

    # 6. Load and fuse LoRA weights if provided
    if args.lora and os.path.exists(args.lora):
        print(f"[*] Loading LoRA weight from: {args.lora} with scale {args.lora_scale}")
        pipe.load_lora_weights(args.lora, adapter_name="custom_lora")
        pipe.fuse_lora(lora_scale=args.lora_scale)
    elif args.lora:
        print(f"[!] Warning: LoRA path '{args.lora}' was specified but file was not found. Skipping LoRA.")

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

    # 9. Perform Generation Loop (Generates 4 images starting from seed, matching original script)
    current_seed = args.seed
    model_name = os.path.basename(args.model).replace(".", "_")

    for i in range(4):
        print(f"[*] Run {i+1}/4: Generating with seed={current_seed}, steps={args.steps}, CFG={args.guidance}")
        generator = torch.Generator(device=device).manual_seed(current_seed)
        
        # Note: We do NOT pass "denoise" argument to text-to-image pipeline as it is unsupported and will cause a TypeError.
        # "denoise" is only supported in img2img (StableDiffusionImg2ImgPipeline).
        with torch.inference_mode():
            try:
                output = pipe(
                    prompt=args.prompt,
                    negative_prompt=args.negative_prompt,
                    num_inference_steps=args.steps,
                    guidance_scale=args.guidance,
                    width=args.width,
                    height=args.height,
                    generator=generator
                )
                image = output.images[0]
            except Exception as e:
                print(f"[ERROR] Generation failed: {e}")
                break

        # Save image
        img_id = db.get("next_image_id", 1)
        filename = f"{model_name}_img_{img_id:06d}.png"
        save_path = os.path.join(args.output_dir, filename)
        image.save(save_path)
        print(f"[+] Saved image to: {save_path}")

        # Record generation log
        db["runs"].append({
            "image_id": img_id,
            "file": filename,
            "timestamp": datetime.now().isoformat(),
            "prompt": args.prompt,
            "negative_prompt": args.negative_prompt,
            "steps": args.steps,
            "guidance_scale": args.guidance,
            "seed": current_seed,
            "width": args.width,
            "height": args.height,
            "model": args.model
        })
        db["next_image_id"] = img_id + 1
        
        # Save updated database
        with open(db_path, "w") as f:
            json.dump(db, f, indent=4)

        current_seed += 1

    print("[*] DONE. All 4 images processed and logged.")

if __name__ == "__main__":
    main()
