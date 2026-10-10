#!/usr/bin/env bash
# ==========================================================
# Media Studio Unified Server - Stop Script
# Gracefully terminates the server running on port 5200.
# ==========================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDS=$(lsof -ti :5200 2>/dev/null)
if [ -z "$PIDS" ]; then
    PIDS=$(pgrep -f "$DIR/run_studio.py")
fi

if [ -z "$PIDS" ]; then
    echo "[!] Media Studio is not currently running."
    exit 0
fi

PID_LIST=$(echo $PIDS | tr '\n' ' ')
echo "[*] Stopping Media Studio server (PID: $PID_LIST)..."
for pid in $PIDS; do
    kill "$pid" 2>/dev/null
done

# Wait up to 30 seconds for graceful shutdown
for i in {1..60}; do
    ANY_ALIVE=0
    for pid in $PIDS; do
        if kill -0 "$pid" 2>/dev/null; then
            ANY_ALIVE=1
            break
        fi
    done
    if [ "$ANY_ALIVE" -eq 0 ]; then
        break
    fi
    sleep 0.5
done

for pid in $PIDS; do
    if kill -0 "$pid" 2>/dev/null; then
        echo "[*] Force terminating PID $pid..."
        kill -9 "$pid" 2>/dev/null
    fi
done

# Clean up any remaining processes bound to port 5200
STILL_RUNNING=$(lsof -ti :5200 2>/dev/null)
if [ -n "$STILL_RUNNING" ]; then
    for pid in $STILL_RUNNING; do
        kill -9 "$pid" 2>/dev/null
    done
fi

echo "[✓] Media Studio stopped successfully."
