#!/usr/bin/env bash
# ==============================================================================
# KoboldCpp Vision Studio Startup Script - Created by Esperanza for Jack
# ==============================================================================
# Launches KoboldCpp configured for Multimodal Vision & Image Classification:
#   - Model: Qwen2-VL 2B Instruct (Fast, high-accuracy vision-language model)
#   - Projector: Qwen2-VL 2B mmproj Q5_1 (Vision encoder)
#   - CPU: 4 Threads (AMD Ryzen 5 3400G)
#   - Web UI: http://localhost:5001 (Includes Drag & Drop Image Upload)
#   - REST API: /v1/chat/completions & /api/v1/generate (Base64 image input)
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PORT="${1:-5001}"
THREADS=4
CONTEXT_SIZE=4096
VISION_DIR="${DIR}/vision_models"

TEXT_MODEL="${VISION_DIR}/Qwen2-VL-2B-Instruct-Q4_K_M.gguf"
MMPROJ_MODEL="${VISION_DIR}/Qwen2-VL-2B-mmproj-q5_1.gguf"

echo "=================================================================="
echo " Starting KoboldCpp Vision Studio (Qwen2-VL Multimodal)           "
echo "=================================================================="
echo " Processor:  AMD Ryzen 5 3400G (${THREADS} CPU Threads)"
echo " Web UI:     http://localhost:${PORT} (Drag & drop images to test)"
echo "------------------------------------------------------------------"

if [ ! -f "$TEXT_MODEL" ] || [ ! -f "$MMPROJ_MODEL" ]; then
    echo " [✗] Vision models not found in ${VISION_DIR}."
    echo "     Please ensure both Qwen2-VL-2B-Instruct and mmproj are downloaded."
    exit 1
fi

echo " [✓] Vision Language Model: Qwen2-VL-2B-Instruct (Q4_K_M)"
echo " [✓] Multimodal Projector:  Qwen2-VL-2B-mmproj (Q5_1)"
echo "------------------------------------------------------------------"
echo " Launching server... Open http://localhost:${PORT}"
echo "=================================================================="

exec ./koboldcpp \
    --model "$TEXT_MODEL" \
    --mmproj "$MMPROJ_MODEL" \
    --threads "$THREADS" \
    --contextsize "$CONTEXT_SIZE" \
    --port "$PORT" \
    --skiplauncher
