import os
import sys
import time
from huggingface_hub import hf_hub_download

MODELS = [
    {
        "repo": "bartowski/Llama-3.2-1B-Instruct-GGUF",
        "file": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "desc": "Llama 3.2 1B (Fast / Lightweight ~800MB)"
    },
    {
        "repo": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "desc": "Llama 3.2 3B (Smart / Balanced ~2.0GB)"
    },
    {
        "repo": "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "file": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "desc": "Qwen 2.5 7B (Deep Reasoning ~4.7GB)"
    },
]

TARGET_DIR = "/home/jack/Desktop/Media_Studio/KOLBOLB"

def main():
    for item in MODELS:
        dest_file = os.path.join(TARGET_DIR, item["file"])
        if os.path.exists(dest_file) and os.path.getsize(dest_file) > 100 * 1024 * 1024:
            print(f"[ALREADY EXISTS] {item['file']}")
            continue
        print(f"\n==========================================")
        print(f"Downloading {item['desc']}...")
        print(f"==========================================")
        t0 = time.time()
        try:
            hf_hub_download(
                repo_id=item["repo"],
                filename=item["file"],
                local_dir=TARGET_DIR,
                local_dir_use_symlinks=False
            )
            print(f"Finished {item['file']} in {time.time() - t0:.1f}s")
        except Exception as e:
            print(f"Error downloading {item['file']}: {e}")

if __name__ == "__main__":
    main()
