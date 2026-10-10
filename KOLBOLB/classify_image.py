#!/usr/bin/env python3
"""
Image Classifier & Describer Client for KoboldCpp Multimodal Vision
Usage:
    python3 classify_image.py /path/to/image.png
    python3 classify_image.py /path/to/image.jpg --prompt "What objects are on the table?"
"""
import os
import sys
import base64
import json
import argparse
import urllib.request
import urllib.error

def get_default_api_url():
    for port in [5002, 5001]:
        try:
            with urllib.request.urlopen(f"http://localhost:{port}/api/v1/model", timeout=0.5) as r:
                if r.status == 200:
                    return f"http://localhost:{port}/v1/chat/completions"
        except Exception:
            pass
    return "http://localhost:5002/v1/chat/completions"

DEFAULT_PROMPT = (
    "Analyze and classify this image in detail.\n"
    "1. Overview: Provide a rich, accurate description of the scene, atmosphere, and action.\n"
    "2. Objects & Elements: List all key objects, tools, creatures, or characters detected.\n"
    "3. Text & Readouts: Transcribe any visible words, signs, numbers, or labels (if any).\n"
    "4. Lighting & Colors: Describe the visual style, palette, and lighting conditions."
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    parser = argparse.ArgumentParser(description="Classify and describe images with local AI vision.")
    parser.add_argument("image", help="Path to the image file (png, jpg, webp)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Custom prompt or question about the image")
    parser.add_argument("--url", default=None, help="KoboldCpp API URL (auto-detects port 5002 or 5001)")
    args = parser.parse_args()

    api_url = args.url if args.url else get_default_api_url()

    if not os.path.isfile(args.image):
        print(f"[✗] Error: File '{args.image}' not found.")
        sys.exit(1)

    print(f"==================================================================")
    print(f" Analyzing Image: {os.path.basename(args.image)}")
    print(f" Connecting to:   {api_url}")
    print(f"==================================================================")

    # Detect mime type
    ext = os.path.splitext(args.image)[1].lower()
    mime = "image/png"
    if ext in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"

    base64_data = encode_image(args.image)
    data_url = f"data:{mime};base64,{base64_data}"

    payload = {
        "model": "qwen2-vl",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": args.prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ],
        "max_tokens": 800,
        "temperature": 0.2
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            res = json.loads(response.read().decode('utf-8'))
            reply = res["choices"][0]["message"]["content"]
            print("\n[AI Vision Analysis]:\n")
            print(reply)
            print("\n==================================================================")
    except urllib.error.URLError as e:
        print(f"\n[✗] Connection Error: {e}")
        print("    Ensure KoboldCpp is running with Vision enabled (e.g. ./start_vision_studio.sh)")
    except Exception as e:
        print(f"\n[✗] Error: {e}")

if __name__ == "__main__":
    main()
