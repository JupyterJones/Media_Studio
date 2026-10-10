#!/usr/bin/env bash
# ==============================================================================
# High-Speed Direct CDN Downloader for AceStep Music Models
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${DIR}/music_models"
mkdir -p "$TARGET_DIR"

declare -A MODELS
MODELS["ace-vae-BF16.gguf"]="https://huggingface.co/koboldcpp/music/resolve/main/ace-vae-BF16.gguf"
MODELS["acestep-5Hz-lm-1.7B-Q8_0.gguf"]="https://huggingface.co/koboldcpp/music/resolve/main/acestep-5Hz-lm-1.7B-Q8_0.gguf"
MODELS["acestep-v15-sftturbo50-Q8_0.gguf"]="https://huggingface.co/koboldcpp/music/resolve/main/acestep-v15-sftturbo50-Q8_0.gguf"

for FILE in "${!MODELS[@]}"; do
    URL="${MODELS[$FILE]}"
    DEST="${TARGET_DIR}/${FILE}"
    echo "=================================================================="
    echo " Downloading: ${FILE}..."
    echo "=================================================================="
    curl -L -C - --fail --retry 5 --retry-delay 3 -o "$DEST" "$URL"
    echo " [✓] Completed ${FILE}"
done

echo "=================================================================="
echo " All Music Models Ready in music_models/"
echo "=================================================================="
