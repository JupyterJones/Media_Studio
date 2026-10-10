#!/usr/bin/env python3
import os

content = """[Unit]
Description=Ollama Service
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=10
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_MODELS=/home/jack/.ollama"
"""

target_path = "/etc/systemd/system/ollama.service.d/override.conf"

try:
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w") as f:
        f.write(content)
    print("[+] Successfully wrote clean override.conf!")
except Exception as e:
    print(f"[!] Error: {e}")
