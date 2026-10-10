#!/usr/bin/env bash
# ==============================================================================
# KoboldCpp Master Startup Script - Created by Esperanza for Jack
# ==============================================================================
# Launches the full suite:
#   1. Text Generation: Llama 3.2 1B Instruct (CPU AVX2 optimized)
#   2. Image Generation: LCM Stable Diffusion + TAESD fast VAE
#   3. Voice Narration: Kokoro TTS (C++ embedded)
#   4. Server-Side Persistence: Local JSON database (Cross-browser sync)
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
PORT=5001
THREADS=4                     # Optimized for AMD Ryzen 5 3400G physical cores
CONTEXT_SIZE=4096

TEXT_MODEL="${DIR}/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
TTS_MODEL="${DIR}/Kokoro_no_espeak_Q8.gguf"
STORAGE_FILE="${DIR}/kobold_storage.json"
# Ensure storage file exists
if [ ! -f "$STORAGE_FILE" ]; then
    echo "{}" > "$STORAGE_FILE"
fi
# Check USB image_models 
SD_MODEL="/media/jack/USB_USBSSD/models/checkpoints/dreamshaper_8LCM.safetensors"
SD_VAE="/media/jack/USB_USBSSD/models/vae/taesd.safetensors"


echo "=================================================================="
echo " Starting KoboldCpp Creative Studio (Esperanza's All-In-One Setup) "
echo "=================================================================="
echo " Processor:  AMD Ryzen 5 3400G (${THREADS} Threads)"
echo " Web UI:     http://localhost:${PORT}"
echo " Storage:    ${STORAGE_FILE} (Cross-browser synced)"
echo " SD_MODEL:   ${SD_MODEL}"
echo " SD_VAE:   ${SD_VAE}"
echo "------------------------------------------------------------------"

# Build command arguments
CMD_ARGS=(
    "--model" "$TEXT_MODEL"
    "--threads" "$THREADS"
    "--contextsize" "$CONTEXT_SIZE"
    "--port" "$PORT"
    "--savedatafile" "$STORAGE_FILE"
    "--skiplauncher"
)

# Attach Kokoro TTS if present
if [ -f "$TTS_MODEL" ]; then
    echo " [✓] Voice: Kokoro TTS model detected."
    CMD_ARGS+=("--ttsmodel" "$TTS_MODEL")
else
    echo " [!] Voice: Kokoro model not found at ${TTS_MODEL}, starting without TTS."
fi

# Attach Stable Diffusion if external drive models are mounted
if [ -f "$SD_MODEL" ]; then
    echo " [✓] Image: LCM SD model detected."
    CMD_ARGS+=("--sdmodel" "$SD_MODEL" "--sdthreads" "$THREADS")
    
    if [ -f "$SD_VAE" ]; then
        echo " [✓] Image: TAESD VAE detected."
        CMD_ARGS+=("--sdvae" "$SD_VAE")
    fi
else
    echo " [!] Image: SD Model not found at ${SD_MODEL}."
    echo "     (Make sure your external drive is mounted if you want image gen)."
fi

# Attach AceStep Music Studio if models are present
MUSIC_DIR="${DIR}/music_models"
MUSIC_EMBED="${MUSIC_DIR}/Ace-Qwen3-Embedding-0.6B-Q8_0.gguf"
MUSIC_VAE="${MUSIC_DIR}/ace-vae-BF16.gguf"
MUSIC_LLM="${MUSIC_DIR}/acestep-5Hz-lm-1.7B-Q8_0.gguf"
MUSIC_DIFF="${MUSIC_DIR}/acestep-v15-sftturbo50-Q8_0.gguf"

if [ -f "$MUSIC_EMBED" ] && [ -f "$MUSIC_VAE" ] && [ -f "$MUSIC_LLM" ] && [ -f "$MUSIC_DIFF" ]; then
    echo " [✓] Music: AceStep 1.5 models detected (MusicUI active at /musicui)."
    CMD_ARGS+=(
        "--musicembeddings" "$MUSIC_EMBED"
        "--musicvae" "$MUSIC_VAE"
        "--musicllm" "$MUSIC_LLM"
        "--musicdiffusion" "$MUSIC_DIFF"
        "--musiclowvram"
    )
fi

# Launch Black Box Recorder service in background if not already running
if [ -f "${DIR}/blackbox_recorder.py" ]; then
    if ! ss -tuln 2>/dev/null | grep -q ":5005 "; then
        python3 "${DIR}/blackbox_recorder.py" &
        RECORDER_PID=$!
        trap 'kill $RECORDER_PID 2>/dev/null || true' EXIT
        echo " [✓] Black Box Mission Recorder launched on port 5005."
    else
        echo " [✓] Black Box Mission Recorder already active on port 5005."
    fi
fi

echo "------------------------------------------------------------------"
echo " Launching server... Press Ctrl+C to stop."
echo "=================================================================="

exec ./koboldcpp "${CMD_ARGS[@]}"
