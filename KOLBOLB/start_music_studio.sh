#!/usr/bin/env bash
# ==============================================================================
# KoboldCpp Music Studio Startup Script - Created by Esperanza for Jack
# ==============================================================================
# Launches KoboldCpp configured for local AI Music Generation (AceStep 1.5):
#   - Text Planner: Llama 3.2 1B Instruct (Lyricist & Song Architect)
#   - Music Embeddings: Ace-Qwen3 0.6B Q8_0
#   - Music Language Model: AceStep 1.7B Q8_0
#   - Music Diffusion: AceStep v1.5 SFT-Turbo Q8_0
#   - Audio VAE: Ace VAE BF16 (44.1kHz Stereo output)
#   - Low VRAM/RAM Mode: Unloads diffusion weights when idle to save RAM
#   - Web UI: http://localhost:5001/musicui
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PORT="${1:-5001}"
THREADS=4
CONTEXT_SIZE=4096
TEXT_MODEL="${DIR}/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
MUSIC_DIR="${DIR}/music_models"

MUSIC_EMBED="${MUSIC_DIR}/Ace-Qwen3-Embedding-0.6B-Q8_0.gguf"
MUSIC_VAE="${MUSIC_DIR}/ace-vae-BF16.gguf"
MUSIC_LLM="${MUSIC_DIR}/acestep-5Hz-lm-1.7B-Q8_0.gguf"
MUSIC_DIFF="${MUSIC_DIR}/acestep-v15-sftturbo50-Q8_0.gguf"

echo "=================================================================="
echo " Starting KoboldCpp Music Studio (AceStep 1.5)                    "
echo "=================================================================="
echo " Processor:  AMD Ryzen 5 3400G (${THREADS} CPU Threads)"
echo " Music UI:   http://localhost:${PORT}/musicui"
echo "------------------------------------------------------------------"

# Verify models
MISSING=0
for f in "$TEXT_MODEL" "$MUSIC_EMBED" "$MUSIC_VAE" "$MUSIC_LLM" "$MUSIC_DIFF"; do
    if [ ! -f "$f" ]; then
        echo " [✗] Missing model: $f"
        MISSING=1
    fi
done

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "Run 'python3 download_music_models.py' first to download the required models."
    exit 1
fi

echo " [✓] Lyricist & Planner: Llama 3.2 1B"
echo " [✓] Music Embeddings:   Ace-Qwen3 0.6B (Q8_0)"
echo " [✓] Audio VAE:          Ace VAE (BF16)"
echo " [✓] Music LM:           AceStep 1.7B (Q8_0)"
echo " [✓] Music Diffusion:    AceStep v1.5 Turbo (Q8_0)"
echo " [✓] Memory Management:  --musiclowvram enabled"
echo "------------------------------------------------------------------"
echo " Launching server... Open http://localhost:${PORT}/musicui"
echo "=================================================================="

exec ./koboldcpp \
    --model "$TEXT_MODEL" \
    --threads "$THREADS" \
    --contextsize "$CONTEXT_SIZE" \
    --port "$PORT" \
    --skiplauncher \
    --musicembeddings "$MUSIC_EMBED" \
    --musicvae "$MUSIC_VAE" \
    --musicllm "$MUSIC_LLM" \
    --musicdiffusion "$MUSIC_DIFF" \
    --musiclowvram
