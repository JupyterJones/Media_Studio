#!/usr/bin/env bash
# ==========================================================
# Media Studio Unified Server - Background Launcher
# Runs on Port 5200 with nohup so you can close your terminal
# and browser freely without interrupting the server.
# ==========================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$DIR/studio.log"

# Check if port 5200 is already in use and responding
EXISTING_PID=$(lsof -ti :5200 2>/dev/null)
if [ -n "$EXISTING_PID" ]; then
    echo "[✓] Media Studio is ALREADY RUNNING on port 5200 (PID: $EXISTING_PID)."
    echo "    App URLs:"
    echo "      • Media Studio:        http://localhost:5200/"
    echo "      • ZoomPan & Comics:    http://localhost:5200/zoompan/"
    echo "      • Effects Studio:      http://localhost:5200/effects/"
    echo "      • Remember DB:         http://localhost:5200/remember/"
    echo "      • SciFi Vision Studio: http://localhost:5200/scifi/"
    echo "      • AI Q&A & LoRA:       http://localhost:5200/chat/"
    echo "      • Kobold AI Studio:    http://localhost:5001/ (Shortcut: http://localhost:5200/kobold)"
    echo ""
    echo "    To restart it, run ./stop_studio.sh first."
    exit 0
fi

# Check if Ollama is running (needed for SciFi Studio AI & God Speaks)
if pgrep -x "ollama" > /dev/null; then
    echo "[✓] Ollama server active"
else
    echo "[!] Notice: Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 2
fi

# Check if process is already starting up
PROC_PID=$(pgrep -f "$DIR/run_studio.py" | head -n 1)
if [ -n "$PROC_PID" ]; then
    echo "[*] Media Studio process is already starting up (PID: $PROC_PID)."
    echo "[*] Streaming startup output and looping until complete..."
    SERVER_PID=$PROC_PID
else
    PYTHON_EXEC="$DIR/venv/bin/python"
    if [ ! -f "$PYTHON_EXEC" ]; then
        echo "[X] Error: Local venv python not found at $PYTHON_EXEC"
        exit 1
    fi

    echo "[*] Launching Media Studio Unified Server in the background..."
    > "$LOG_FILE"
    nohup setsid "$PYTHON_EXEC" -u "$DIR/run_studio.py" </dev/null >> "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    disown "$SERVER_PID" 2>/dev/null

    echo "[*] Server process started (PID: $SERVER_PID). Streaming startup output:"
fi

echo "-----------------------------------------------------------------"

# Stream the log live to terminal as the server loads
tail -n 20 -f "$LOG_FILE" &
TAIL_PID=$!

# Clean up background tail if interrupted (server continues in background)
trap 'kill "$TAIL_PID" 2>/dev/null; echo ""; echo "-----------------------------------------------------------------"; echo "[*] Detached from startup log. Server process is still running in background (PID: $SERVER_PID)."; echo "    Check current status with: ./status_studio.sh"; exit 0' INT TERM

# Loop until server is fully loaded and responding on port 5200 (wait up to 3 minutes / 180 seconds)
MAX_WAIT_SECONDS=180
READY=0

for ((i=1; i<=MAX_WAIT_SECONDS; i++)); do
    # Check if process died during initialization
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        sleep 0.5
        kill "$TAIL_PID" 2>/dev/null
        wait "$TAIL_PID" 2>/dev/null
        echo "-----------------------------------------------------------------"
        echo "[X] Error: Server process (PID: $SERVER_PID) terminated unexpectedly!"
        echo "    Check log output: cat $LOG_FILE"
        exit 1
    fi

    # Check if port 5200 is bound and responding to HTTP
    if lsof -ti :5200 >/dev/null 2>&1 && curl -s -m 30 http://127.0.0.1:5200/ >/dev/null 2>&1; then
        READY=1
        break
    fi

    sleep 1
done

# Allow a moment for any remaining startup banner text to flush to stdout
sleep 1
kill "$TAIL_PID" 2>/dev/null
wait "$TAIL_PID" 2>/dev/null
trap - INT TERM

echo "-----------------------------------------------------------------"
if [ "$READY" -eq 1 ]; then
    echo "[✓] Media Studio is FULLY LOADED and ready! (PID: $SERVER_PID)"
    echo "    Log output: $LOG_FILE"
    echo ""
    echo "    App URLs:"
    echo "      • Media Studio:        http://localhost:5200/"
    echo "      • ZoomPan & Comics:    http://localhost:5200/zoompan/"
    echo "      • Effects Studio:      http://localhost:5200/effects/"
    echo "      • Remember DB:         http://localhost:5200/remember/"
    echo "      • SciFi Vision Studio: http://localhost:5200/scifi/"
    echo "      • AI Q&A & LoRA:       http://localhost:5200/chat/"
    echo "      • Kobold AI Studio:    http://localhost:5001/ (Shortcut: http://localhost:5200/kobold)"
    echo ""
    echo "    Server is running in the background."
    echo "    You can now safely open the URLs or close this terminal."
else
    echo "[!] Server process is still running (PID: $SERVER_PID), but port 5200 did not respond within 3 minutes."
    echo "    The server may still be initializing slow modules. Check current status with: ./status_studio.sh"
    echo "    Log output: $LOG_FILE"
fi
