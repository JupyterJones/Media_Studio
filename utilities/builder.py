#!/usr/bin/env python3
"""
Arcanian Timeline Story Engine (CPU-Friendly)
---------------------------------------------

Pipeline:
1. Load images from folder
2. Generate captions using LLaVa via Ollama CLI (safe)
3. Proofread captions with LLaMA3.2
4. Generate full story with Qwen3:8B
5. Generate placeholder embeddings (for nomic-embed-text)
6. Save JSON timeline report

Models required locally:
- LLaVa:latest          (image captioning)
- Qwen3:8B              (story generation)
- LLaMA3.2:3B           (proofreading)
- nomic-embed-text:latest (embeddings, placeholder)
"""

import os
import json
import subprocess
from icecream import ic

# ---------------- CONFIG ----------------
IMAGE_FOLDER = "/home/jack/Desktop/DOCKER/static/images/imagine/"
OUTPUT_JSON = "arcanian_timeline.json"

# Models
IMAGE_MODEL = "LLaVa:latest"
STORY_MODEL = "Qwen3:8B"
PROOF_MODEL = "LLaMA3.2:3B"
EMBED_MODEL = "nomic-embed-text:latest"

# ---------------- HELPER FUNCTIONS ----------------
def generate_text(prompt, model, max_tokens=256):
    """
    Generate text from a prompt using Ollama API.
    """
    import requests
    OLLAMA_API_URL = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens
    }
    try:
        resp = requests.post(OLLAMA_API_URL, json=payload)
        if resp.status_code != 200:
            ic("Error calling model", resp.text)
            return ""
        text = ""
        for line in resp.text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text += obj.get("completion", "")
            except json.JSONDecodeError:
                continue
        return text.strip()
    except Exception as e:
        ic("Exception in generate_text:", e)
        return ""

def generate_image_caption(image_path):
    """
    Generate a caption for an image using LLaVa via Ollama CLI.
    Avoids HTTP API filename/JSON errors.
    """
    ic("Captioning image via CLI", image_path)
    try:
        result = subprocess.run(
            ["ollama", "generate", IMAGE_MODEL, "--image", image_path, "--prompt", "Describe this image in detail."],
            capture_output=True, text=True, check=True
        )
        caption = result.stdout.strip()
        ic("Caption generated:", caption)
        return caption
    except subprocess.CalledProcessError as e:
        ic("CLI caption error:", e.stderr)
        return ""

def proofread_text(text):
    """
    Proofread text using LLaMA3.2 (grammar/style improvements).
    """
    ic("Proofreading text")
    prompt = f"Correct grammar and improve readability of this text:\n{text}"
    corrected = generate_text(prompt, PROOF_MODEL, max_tokens=256)
    ic("Proofread result:", corrected)
    return corrected

def embed_text(text):
    """
    Placeholder embedding generator (nomic-embed-text cannot generate via API).
    """
    ic("Embedding text (placeholder)")
    embedding = [0.0] * 768
    return embedding

# ---------------- MAIN PIPELINE ----------------
def main():
    timeline = []

    # 1. Sort images
    image_files = sorted(
        [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    )

    # 2. Process each image
    for img_file in image_files:
        img_path = os.path.join(IMAGE_FOLDER, img_file)
        caption = generate_image_caption(img_path)
        if not caption:
            ic("Warning: empty caption for", img_file)

        # Proofread caption
        caption = proofread_text(caption)

        # Generate embedding (placeholder)
        embedding = embed_text(caption)

        timeline.append({
            "image": img_file,
            "caption": caption,
            "embedding": embedding
        })

    # 3. Generate full story from captions
    ic("Generating full story from captions")
    story_prompt = "Write a 10-part Arcanian timeline story from these image captions:\n"
    story_prompt += "\n".join([item["caption"] for item in timeline])
    story = generate_text(story_prompt, STORY_MODEL, max_tokens=1024)

    # Proofread story
    story = proofread_text(story)

    # 4. Save JSON report
    report = {
        "images": timeline,
        "story": story
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(report, f, indent=2)

    ic("Pipeline complete. Timeline saved to", OUTPUT_JSON)

if __name__ == "__main__":
    main()
