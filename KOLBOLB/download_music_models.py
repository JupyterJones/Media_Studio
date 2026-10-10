#!/usr/bin/env python3
"""
AceStep Music Models Downloader for KoboldCpp
Configured for CPU-friendly Quantized Models (Total: ~5.38 GB)
"""
import os
import sys
import time
from huggingface_hub import hf_hub_download

REPO_ID = "koboldcpp/music"
TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_models")

MODELS = [
    {
        "file": "Ace-Qwen3-Embedding-0.6B-Q8_0.gguf",
        "expected_mb": 748,
        "desc": "Ace-Qwen3 Text Embeddings (Q8_0)"
    },
    {
        "file": "ace-vae-BF16.gguf",
        "expected_mb": 322,
        "desc": "Ace-Step Audio VAE (BF16)"
    },
    {
        "file": "acestep-5Hz-lm-1.7B-Q8_0.gguf",
        "expected_mb": 1884,
        "desc": "Ace-Step Music Language Model (1.7B Q8_0)"
    },
    {
        "file": "acestep-v15-sftturbo50-Q8_0.gguf",
        "expected_mb": 2431,
        "desc": "Ace-Step Diffusion Transformer (Turbo Q8_0)"
    }
]

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print("==================================================================")
    print(" AceStep 1.5 Music Models Downloader")
    print(" Destination: " + TARGET_DIR)
    print(" Total size: ~5.38 GB across 4 models")
    print("==================================================================")

    for i, item in enumerate(MODELS, 1):
        filename = item["file"]
        dest = os.path.join(TARGET_DIR, filename)
        min_size = (item["expected_mb"] - 10) * 1024 * 1024
        
        if os.path.exists(dest) and os.path.getsize(dest) > min_size:
            actual_mb = os.path.getsize(dest) / (1024 * 1024)
            print(f"[{i}/{len(MODELS)}] [✓ ALREADY EXISTS] {filename} ({actual_mb:.1f} MB)")
            continue

        print(f"\n[{i}/{len(MODELS)}] Downloading {item['desc']} (~{item['expected_mb']} MB)...")
        t0 = time.time()
        try:
            hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                local_dir=TARGET_DIR,
                local_dir_use_symlinks=False
            )
            elapsed = time.time() - t0
            actual_mb = os.path.getsize(dest) / (1024 * 1024)
            print(f"[✓ COMPLETE] {filename} ({actual_mb:.1f} MB in {elapsed:.1f}s)")
        except Exception as e:
            print(f"[✗ ERROR] Failed to download {filename}: {e}")
            sys.exit(1)

    print("\n==================================================================")
    print(" All AceStep music models are ready in music_models/")
    print("==================================================================")

if __name__ == "__main__":
    main()
