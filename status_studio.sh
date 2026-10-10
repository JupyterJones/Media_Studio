#!/usr/bin/env bash
# ==========================================================
# Media Studio Unified Server - Status Script
# Checks port 5200 and prints live response status.
# ==========================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID=$(lsof -ti :5200 2>/dev/null)
PROC_PID=$(pgrep -f "$DIR/run_studio.py" | head -n 1)

if [ -n "$PID" ]; then
    echo "[✓] Media Studio is RUNNING on port 5200 (PID: $PID)"
    echo "    Response: $(curl -sI -m 30 http://127.0.0.1:5200/ | head -n 1)"
    echo "    App URLs:"
    echo "      • Media Studio:        http://localhost:5200/"
    echo "      • ZoomPan & Comics:    http://localhost:5200/zoompan/"
    echo "      • Effects Studio:      http://localhost:5200/effects/"
    echo "      • Remember DB:         http://localhost:5200/remember/"
    echo "      • SciFi Vision Studio: http://localhost:5200/scifi/"
    echo "      • AI Q&A & LoRA:       http://localhost:5200/chat/"
    if lsof -ti :5001 >/dev/null 2>&1; then
        echo "      • Kobold AI Studio:    http://localhost:5001/ [ACTIVE] (Shortcut: http://localhost:5200/kobold)"
    else
        echo "      • Kobold AI Studio:    http://localhost:5001/ [IDLE] (Run: cd KOLBOLB && ./startup.sh)"
    fi
elif [ -n "$PROC_PID" ]; then
    echo "[⏳] Media Studio is STARTING UP (PID: $PROC_PID)..."
    echo "    Loading modules (takes 1-3 minutes on older hardware)."
    echo "    View live progress: tail -f $DIR/studio.log"
else
    echo "[X] Media Studio is STOPPED."
    echo "    Run ./start_studio.sh to start it."
fi
