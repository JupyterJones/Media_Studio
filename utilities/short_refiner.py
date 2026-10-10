#!/usr/bin/env python3
"""
Refine rough ideas into high-quality T2I prompts
Automatically appends to JSON and plain text collections
Starts and stops Ollama Docker container automatically
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from icecream import ic
import subprocess

# -----------------------------
# CONFIG
# -----------------------------

#MODEL = "codellama:13b"
MODEL = "llama3.2:3b"
ENDPOINT = "http://localhost:11434/api/generate"
TIMEOUT = 900

JSON_COLLECTION = "t2i_prompts.json"
TXT_COLLECTION = "t2i_prompts.txt"
DEFAULT_VARIATIONS = 3

OLLAMA_CONTAINER = "ollama-cpu"
OLLAMA_STARTUP_DELAY = 5  # seconds

# -----------------------------
# LOGGING
# -----------------------------

def logit(*args):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = " ".join(str(a) for a in args)
    print(f"{ts} | {msg}")

# -----------------------------
# DOCKER CONTROL
# -----------------------------

def start_ollama_container():
    logit(f"Starting Docker container: {OLLAMA_CONTAINER}")
    ic("docker start", OLLAMA_CONTAINER)

    subprocess.run(
        ["docker", "start", OLLAMA_CONTAINER],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )

    logit("Waiting for Ollama to initialize...")
    time.sleep(OLLAMA_STARTUP_DELAY)

def stop_ollama_container():
    logit(f"Stopping Docker container: {OLLAMA_CONTAINER}")
    ic("docker stop", OLLAMA_CONTAINER)

    subprocess.run(
        ["docker", "stop", OLLAMA_CONTAINER],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )

# -----------------------------
# UTILITIES
# -----------------------------

def call_ollama(prompt: str) -> str:
    ic("PROMPT →", prompt)

    r = requests.post(
        ENDPOINT,
        json={
            "model": MODEL,
            "prompt": prompt,
            "max_tokens": 2000,            
            "stream": False
        },
        timeout=TIMEOUT
    )

    r.raise_for_status()
    result = r.json().get("response", "").lstrip("\ufeff\n ")
    ic("RESPONSE ←", result)
    return result

def atomic_write_json(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

# -----------------------------
# PROMPT REFINEMENT
# -----------------------------

def refine_prompt(rough_idea: str, variations: int = DEFAULT_VARIATIONS) -> dict:
    """
    Refines a rough idea into multiple T2I prompts.
    Returns a dict of variations.
    """
    outputs = {}

    for i in range(1, variations + 1):
        prompt = f"""
You are a professional text-to-image prompt engineer.
Take the following rough idea and turn it into a vivid, highly-detailed,
imaginative text-to-image prompt suitable for AI image generation.

Rough idea: "{rough_idea}"

Requirements:
- Include style, mood, lighting, camera angles if relevant
- Keep it concise but evocative
- Avoid vague words
- Output in a single unspaced paragraph
- Be verbose
- No explanations, only the prompt
"""

        refined = call_ollama(prompt).strip()
        outputs[f"{rough_idea}_variation_{i}"] = refined

    return outputs

# -----------------------------
# COLLECTION APPENDING
# -----------------------------

def append_to_collections(refined_prompts: dict):
    try:
        with open(JSON_COLLECTION, "r", encoding="utf-8") as f:
            collection = json.load(f)
    except FileNotFoundError:
        collection = {}

    collection.update(refined_prompts)
    atomic_write_json(JSON_COLLECTION, collection)
    logit(f"Appended {len(refined_prompts)} prompts to {JSON_COLLECTION}")

    with open(TXT_COLLECTION, "a", encoding="utf-8") as f:
        for prompt in refined_prompts.values():
            f.write(prompt + "\n")

    logit(f"Appended {len(refined_prompts)} prompts to {TXT_COLLECTION}")

# -----------------------------
# ENTRY POINT
# -----------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: t2i_prompt_refiner.py <rough idea> [num_variations]")
        sys.exit(1)

    rough_idea = sys.argv[1]
    variations = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_VARIATIONS

    start_ollama_container()

    try:
        logit("Refining prompt for idea:", rough_idea)
        refined_prompts = refine_prompt(rough_idea, variations)
        append_to_collections(refined_prompts)

        logit("Refined prompts:")
        for prompt in refined_prompts.values():
            logit(prompt)

    finally:
        stop_ollama_container()
        logit("Done.")

if __name__ == "__main__":
    main()
