#!/usr/bin/env bash
# Start SciFi Vision Studio Web Application
# Fully portable across Linux drives and directories
cd "$(dirname "$0")"

# Detect Python virtual environment dynamically
if [ -f "$HOME/Desktop/Kokoro-TTS-Pause/venv/bin/python3" ]; then
    PYTHON="$HOME/Desktop/Kokoro-TTS-Pause/venv/bin/python3"
elif [ -f "/home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/python3" ]; then
    PYTHON="/home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/python3"
elif [ -f "./venv/bin/python3" ]; then
    PYTHON="./venv/bin/python3"
else
    PYTHON="$(command -v python3)"
fi

PORT=5055

echo "================================================="
echo "   🚀 LAUNCHING SCIFI VISION STUDIO (PORT ${PORT})  "
echo "   📁 Location: $(pwd)"
echo "   🐍 Python:   ${PYTHON}"
echo "================================================="

# Check if Ollama is running
if pgrep -x "ollama" > /dev/null; then
    echo "✓ Ollama server active"
else
    echo "[!] Notice: Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 2
fi

# Run the studio app
exec $PYTHON app.py
