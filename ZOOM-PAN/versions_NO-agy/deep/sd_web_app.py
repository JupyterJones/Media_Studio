import os
import json
import argparse
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler, LCMScheduler

app = Flask(__name__)

# Global pipeline (loaded once at startup)
pipe = None
current_device = None
current_model_path = None


def get_device(preference="auto"):
    if preference == "auto":
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    return preference


def load_pipeline(model_path, device_pref="auto"):
    global pipe, current_device, current_model_path

    device = get_device(device_pref)
    current_device = device

    print(f"[*] Target generation device: {device.upper()}")
    if device == "cpu":
        print("[!] WARNING: Running on CPU will be extremely slow.")

    is_lcm = "lcm" in model_path.lower()
    print(f"[*] Detected model type: {'LCM' if is_lcm else 'Standard SD 1.5'}")

    torch_dtype = torch.float16 if device == "cuda" else torch.float32

    print(f"[*] Loading model from: {model_path}")
    pipeline = StableDiffusionPipeline.from_single_file(
        model_path,
        torch_dtype=torch_dtype,
        use_safetensors=True,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipeline = pipeline.to(device)

    if device == "cpu":
        pipeline.enable_attention_slicing()
    elif device == "cuda":
        if hasattr(pipeline, "enable_xformers_memory_efficient_attention"):
            pipeline.enable_xformers_memory_efficient_attention()
        else:
            pipeline.enable_attention_slicing()

    if is_lcm:
        pipeline.scheduler = LCMScheduler.from_config(pipeline.scheduler.config)
    else:
        pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
            pipeline.scheduler.config,
            use_karras_sigmas=True
        )

    pipe = pipeline
    current_model_path = model_path
    print("[+] Pipeline ready.")


def apply_lora(lora_path, lora_scale=0.15):
    if lora_path and os.path.exists(lora_path):
        print(f"[*] Loading LoRA: {lora_path} (scale={lora_scale})")
        pipe.load_lora_weights(lora_path, adapter_name="custom_lora")
        pipe.fuse_lora(lora_scale=lora_scale)
    elif lora_path:
        print(f"[!] LoRA not found: {lora_path}")


def get_generation_history(output_dir="static/uploads/"):
    db_path = os.path.join(output_dir, "generations.json")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"next_image_id": 1, "runs": []}


@app.route('/')
def index():
    history = get_generation_history()
    # Reverse so newest first
    runs = list(reversed(history.get("runs", [])))
    return render_template('index2.html', history=runs, model_path=current_model_path, device=current_device)


@app.route('/api/generate_image', methods=['POST'])
def generate_image():
    if pipe is None:
        return jsonify({"error": "Model not loaded. Check server startup logs."}), 500

    data = request.get_json() or {}

    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({"error": "Missing required field: prompt"}), 400

    negative_prompt = data.get('negative_prompt', "blurry, out of focus, text, captions, low quality, pixelated, worst quality")
    steps = int(data.get('steps', 5))
    guidance = float(data.get('guidance', 1.5))
    width = int(data.get('width', 512))
    height = int(data.get('height', 768))
    seed = int(data.get('seed', -1))
    if seed < 0:
        seed = int(datetime.now().timestamp()) % 1000000
    num_images = min(max(int(data.get('num_images', 1)), 1), 8)
    output_dir = data.get('output_dir', 'static/uploads/')

    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(output_dir, "generations.json")

    db = get_generation_history(output_dir)

    results = []
    current_seed = seed
    model_name = os.path.basename(current_model_path).replace(".", "_")

    for i in range(num_images):
        print(f"[*] Run {i+1}/{num_images}: seed={current_seed}, steps={steps}, CFG={guidance}")
        generator = torch.Generator(device=current_device).manual_seed(current_seed)

        try:
            with torch.inference_mode():
                output = pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    width=width,
                    height=height,
                    generator=generator
                )
                image = output.images[0]
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return jsonify({"error": str(e), "partial_results": results}), 500

        img_id = db.get("next_image_id", 1)
        filename = f"{model_name}_img_{img_id:06d}.png"
        save_path = os.path.join(output_dir, filename)
        image.save(save_path)
        print(f"[+] Saved: {save_path}")

        entry = {
            "image_id": img_id,
            "file": filename,
            "url": f"/static/uploads/{filename}",
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "guidance_scale": guidance,
            "seed": current_seed,
            "width": width,
            "height": height,
            "model": current_model_path
        }
        db["runs"].append(entry)
        db["next_image_id"] = img_id + 1
        results.append(entry)

        with open(db_path, "w") as f:
            json.dump(db, f, indent=4)

        current_seed += 1

    return jsonify({
        "success": True,
        "images": results,
        "output_dir": os.path.abspath(output_dir)
    })


@app.route('/static/uploads/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/uploads', filename)


@app.route('/api/history', methods=['GET'])
def api_history():
    history = get_generation_history()
    return jsonify(history)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "device": current_device,
        "model_loaded": pipe is not None,
        "model_path": current_model_path
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Stable Diffusion Web GUI")
    parser.add_argument("--model", default="/home/jack/Desktop/Comfy-UI/models/checkpoints/comiccraftLCM_beta4.safetensors", help="Path to .safetensors model")
    parser.add_argument("--lora", type=str, default=None, help="Path to LoRA file")
    parser.add_argument("--lora_scale", type=float, default=0.15, help="LoRA scale")
    parser.add_argument("--device", type=str, default="auto", help="Device: auto, cuda, mps, cpu")
    parser.add_argument("--port", type=int, default=5040, help="Flask port")
    args = parser.parse_args()

    load_pipeline(args.model, args.device)
    if args.lora:
        apply_lora(args.lora, args.lora_scale)

    app.run(host='0.0.0.0', port=args.port, debug=False)
