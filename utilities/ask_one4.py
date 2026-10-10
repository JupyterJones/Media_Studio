#!/home/jack/miniconda3/envs/PY39/bin/python

import requests
import json
import sys
import time
import os
import re
from datetime import datetime
from icecream import ic

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
REQUEST_TIMEOUT = 1200

#DEFAULT_MODEL = "codellama:latest"
DEFAULT_MODEL = "mistral:7b"
#DEFAULT_MODEL = "llama3.2:3b" #very good
#DEFAULT_MODEL = "phi3:latest" # good -


TTS_API_URL = "http://localhost:8880/v1/audio/speech"
OUTPUT_DIR = "/home/jack/Desktop/HDD500/DOCKER"
VOICES = [
    'bf_alice', 'bf_emma', 'bf_lily', 'bf_v0emma', 'bf_v0isabella',
    'af_alloy', 'af_aoede', 'af_bella', 'af_heart', 'af_jadzia',
    'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river',
    'af_sarah', 'af_sky', 'af_v0', 'af_v0bella', 'af_v0irulan',
    'af_v0nicole', 'af_v0sarah', 'af_v0sky', 'am_adam', 'am_echo',
    'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx',
    'am_puck', 'am_santa', 'am_v0adam', 'am_v0gurney', 'am_v0michael',
    'bm_daniel', 'bm_fable'
]
#ASSISTANT_VOICE = VOICES[23] # good am_adam
#ASSISTANT_VOICE = VOICES[24] # okay am_echo
#ASSISTANT_VOICE = VOICES[25] # am_eric okay bit fast
ASSISTANT_VOICE = VOICES[27]
ic(f"ASSISTANT_VOICE: {ASSISTANT_VOICE}")
HEADERS = {"Content-Type": "application/json"}

ic(f"Using TTS voice: {ASSISTANT_VOICE}")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    ic(f"Created output directory: {OUTPUT_DIR}")

# -------------------------------------------------
# CLEAN TEXT FOR TTS (REMOVE PARENTHESIS CONTENT)
# -------------------------------------------------
def clean_text_for_tts(text):
    ic("Cleaning AI text for TTS...")
    # Remove all text within parentheses, including the parentheses
    cleaned = re.sub(r'\([^)]*\)', '', text)
    # Also remove other problematic characters
    cleaned = re.sub(r'[\"\*\_\[\]\{\}\<\>\']', '', cleaned)
    # Collapse multiple spaces to single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# -------------------------------------------------
# SAFE TIMESTAMP FILENAME
def timestamp_filename(ext="txt"):
    return datetime.now().strftime("%Y%m%d_%H%M%S") + f".{ext}"

# -------------------------------------------------
def query_streaming(model_name, prompt, max_tokens=4096, temperature=0.85, top_p=0.95):
    """
    Streaming query to Ollama model in salty old sailor style.
    Ensures:
      - No parentheses (), brackets [], curly braces {}
      - Stage-direction words removed
      - Proper spacing between chunks
      - TTS-ready output
    """

    # Token-efficient, TTS-ready structured prompt
    structured_prompt = (
        f"Write a long, first-person story in the style of a salty old story teller. "
        f"Use rough bar slang, curses, pauses, grog talk, and chaotic memories. "
        f"Do NOT include anything in parentheses (), brackets [], curly braces {{}}. "
        f"Do NOT include stage directions like 'hiccup', 'slurs', 'staggers', 'stammers', 'grumbles', or 'mutters'. "
        f"Keep it very verbose, chaotic, and suitable for TTS conversion. "
        f"Write naturally, as if the story teller is speaking aloud in a tavern, telling a story about:\n{prompt}"
    )

    ic(f"Sending to model: {model_name}")
    ic(f"structured_prompt length (chars): {len(structured_prompt)}")

    estimated_prompt_tokens = len(structured_prompt) // 4
    num_predict = max_tokens - estimated_prompt_tokens
    ic(f"estimated_prompt_tokens: {estimated_prompt_tokens}")
    ic(f"num_predict set to: {num_predict}")

    payload = {
        "model": model_name,
        "prompt": structured_prompt,
        "stream": True,
        "num_predict": num_predict,
        "temperature": temperature,
        "top_p": top_p
    }

    # Stage-direction words to remove
    stage_words = ['hiccup', 'slurs', 'staggers', 'stammers', 'grumbles', 'mutters']
    stage_pattern = r'\b(?:' + '|'.join(stage_words) + r')\b'

    def clean_text(text):
        """Remove bracketed content, stage words, and collapse spaces"""
        # Remove (), [], {}
        text = re.sub(r'\([^()]*\)', ' ', text)
        text = re.sub(r'\[[^\[\]]*\]', ' ', text)
        text = re.sub(r'\{[^\{\}]*\}', ' ', text)
        # Remove stage-direction words
        text = re.sub(stage_pattern, '', text, flags=re.IGNORECASE)
        # Collapse multiple spaces
        text = re.sub(r'\s{2,}', ' ', text)
        return text

    try:
        with requests.post(
            OLLAMA_GENERATE_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            stream=True
        ) as response:

            response.raise_for_status()
            ic(f"HTTP status: {response.status_code}")

            full_text = ""
            start = time.time()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    part = data.get("response", "")
                    part = clean_text(part)

                    # Append without adding extra spaces
                    full_text += part
                    print(part, end="", flush=True)

                    if data.get("done", False):
                        break

                except json.JSONDecodeError:
                    cleaned = clean_text(line)
                    full_text += cleaned
                    print(cleaned, end="", flush=True)

            elapsed = time.time() - start
            ic(f"Model completed in {elapsed:.2f} seconds\n")
            print("\n")  # final newline
            return full_text

    except Exception as e:
        ic(f"Error contacting model {model_name}: {e}")
        return f"ERROR: {e}"

# TTS GENERATION
# -------------------------------------------------
def generate_tts(text):
    filename = timestamp_filename("mp3")
    output_path = os.path.join(OUTPUT_DIR, filename)

    payload = {
        "input": text,
        "voice": ASSISTANT_VOICE
    }

    try:
        ic(f"TTS sending first 40 chars:\n{text[:40]}...")
        response = requests.post(
            TTS_API_URL,
            json=payload,
            headers=HEADERS,
            timeout=680
        )

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            ic(f"TTS saved: {output_path}")
            return output_path
        else:
            ic(f"TTS ERROR {response.status_code}: {response.text}")
            return None

    except Exception as e:
        ic(f"TTS failure: {e}")
        return None

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    ic("Starting single-model AI + TTS pipeline...")

    if len(sys.argv) >= 3:
        model_name = sys.argv[1]
        prompt = " ".join(sys.argv[2:]).strip()
    elif len(sys.argv) == 2:
        model_name = DEFAULT_MODEL
        prompt = sys.argv[1].strip()
    else:
        print("Usage: python ask_one2.py <model_name(optional)> <prompt>")
        sys.exit(1)

    ic(f"Model selected: {model_name}")
    ic(f"Prompt length: {len(prompt)} characters")

    # Run model
    raw_response = query_streaming(model_name, prompt)

    # Clean for TTS
    cleaned_text = clean_text_for_tts(raw_response)

    # Save text file
    text_filename = timestamp_filename("txt")
    text_path = os.path.join(OUTPUT_DIR, text_filename)
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    ic(f"Text saved to: {text_path}")

    # Convert to MP3
    ic("Sending cleaned text to TTS generator...")
    mp3_path = generate_tts(cleaned_text)

    print("\n=============================================")
    print(f"Text saved: {text_path}")
    if mp3_path:
        print(f"MP3 generated: {mp3_path}")
    else:
        print("❌ TTS FAILED")
    print("=============================================\n")
