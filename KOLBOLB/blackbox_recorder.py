#!/usr/bin/env python3
"""
Black Box Mission Recorder & Cross-Browser JSON Persistence Server
Listens on http://127.0.0.1:5005
Maintains mission_history.json on disk for 100% cross-browser persistence.
Archives images and voice audio, serves them via HTTP, and compiles mp4 video via ffmpeg.
"""

import os
import sys
import json
import base64
import subprocess
import shutil
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 5005
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORD_DIR = os.path.join(BASE_DIR, "mission_record")
HISTORY_FILE = os.path.join(RECORD_DIR, "mission_history.json")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "Orpheus_Mission_Log.mp4")

os.makedirs(RECORD_DIR, exist_ok=True)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(hist):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2)

class BlackBoxHandler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if self.path == "/status":
            files = os.listdir(RECORD_DIR)
            images = [f for f in files if f.endswith(".png")]
            audios = [f for f in files if f.endswith(".wav")]
            data = {
                "status": "online",
                "recorded_scenes": len(images),
                "recorded_audio": len(audios),
                "record_dir": RECORD_DIR,
                "history_file": HISTORY_FILE,
                "history_turns": len(load_history()),
                "video_exists": os.path.exists(OUTPUT_VIDEO)
            }
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        elif self.path == "/history":
            hist = load_history()
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"history": hist}).encode("utf-8"))
            return

        elif self.path == "/use_status":
            use_mp4 = os.path.join(BASE_DIR, "use.mp4")            
            use_jpg = os.path.join(BASE_DIR, "use.jpg")
            use_mp3 = os.path.join(BASE_DIR, "use.mp3")
            use_wav = os.path.join(BASE_DIR, "use.wav")
            result_mp4 = os.path.join(BASE_DIR, "result.mp4")
            cyber_vid = os.path.join(BASE_DIR, "cyber_rock_lipsync_10s.mp4")

            data = {
                "use_mp4": {
                    "exists": os.path.exists(use_mp4),
                    "size": os.path.getsize(use_mp4) if os.path.exists(use_mp4) else 0,
                    "mtime": int(os.path.getmtime(use_mp4)) if os.path.exists(use_mp4) else 0,
                    "url": f"http://127.0.0.1:{PORT}/use.mp4"
                },            
                "use_jpg": {
                    "exists": os.path.exists(use_jpg),
                    "size": os.path.getsize(use_jpg) if os.path.exists(use_jpg) else 0,
                    "mtime": int(os.path.getmtime(use_jpg)) if os.path.exists(use_jpg) else 0,
                    "url": f"http://127.0.0.1:{PORT}/use.jpg"
                },
                "use_mp3": {
                    "exists": os.path.exists(use_mp3),
                    "size": os.path.getsize(use_mp3) if os.path.exists(use_mp3) else 0,
                    "mtime": int(os.path.getmtime(use_mp3)) if os.path.exists(use_mp3) else 0,
                    "url": f"http://127.0.0.1:{PORT}/use.mp3"
                },
                "use_wav": {
                    "exists": os.path.exists(use_wav),
                    "size": os.path.getsize(use_wav) if os.path.exists(use_wav) else 0,
                    "mtime": int(os.path.getmtime(use_wav)) if os.path.exists(use_wav) else 0,
                    "url": f"http://127.0.0.1:{PORT}/use.wav"
                },
                "result_mp4": {
                    "exists": os.path.exists(result_mp4),
                    "size": os.path.getsize(result_mp4) if os.path.exists(result_mp4) else 0,
                    "mtime": int(os.path.getmtime(result_mp4)) if os.path.exists(result_mp4) else 0,
                    "url": f"http://127.0.0.1:{PORT}/result.mp4"
                },
                "cyber_10s_mp4": {
                    "exists": os.path.exists(cyber_vid),
                    "size": os.path.getsize(cyber_vid) if os.path.exists(cyber_vid) else 0,
                    "url": f"http://127.0.0.1:{PORT}/cyber_rock_lipsync_10s.mp4"
                }
            }
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # Serve media and static files directly (cross-browser safe with full CORS)
        clean_path = self.path.split("?")[0].lstrip("/")
        if clean_path.startswith("media/"):
            clean_path = clean_path[6:]
        
        # Check in RECORD_DIR, then BASE_DIR
        fpath = os.path.join(RECORD_DIR, clean_path)
        if not (os.path.exists(fpath) and os.path.isfile(fpath)):
            fpath = os.path.join(BASE_DIR, clean_path)

        if os.path.exists(fpath) and os.path.isfile(fpath):
            self.send_response(200)
            self._set_cors()
            ext = os.path.splitext(fpath)[1].lower()
            mime_map = {
                ".html": "text/html; charset=utf-8",
                ".js": "application/javascript",
                ".css": "text/css",
                ".json": "application/json",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".wav": "audio/wav",
                ".mp3": "audio/mpeg",
                ".mp4": "video/mp4"
            }
            self.send_header("Content-Type", mime_map.get(ext, "application/octet-stream"))
            self.send_header("Content-Length", str(os.path.getsize(fpath)))
            self.end_headers()
            if self.command != "HEAD":
                with open(fpath, "rb") as f:
                    self.wfile.write(f.read())
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        
        try:
            payload = json.loads(body) if body else {}
        except Exception as e:
            payload = {}

        if self.path == "/save_turn":
            # Save a complete game turn into mission_history.json on disk
            hist = load_history()
            turn_index = payload.get("turn_index", len(hist) + 1)
            scene_id = f"scene_{turn_index:03d}"

            # Save media files if present
            image_url = ""
            audio_url = ""

            img_b64 = payload.get("image_b64")
            if img_b64:
                if "base64," in img_b64:
                    img_b64 = img_b64.split("base64,")[1]
                img_path = os.path.join(RECORD_DIR, f"{scene_id}.png")
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                image_url = f"http://127.0.0.1:{PORT}/media/{scene_id}.png"

            audio_b64 = payload.get("audio_b64")
            if audio_b64:
                if "base64," in audio_b64:
                    audio_b64 = audio_b64.split("base64,")[1]
                audio_path = os.path.join(RECORD_DIR, f"{scene_id}.wav")
                with open(audio_path, "wb") as f:
                    f.write(base64.b64decode(audio_b64))
                audio_url = f"http://127.0.0.1:{PORT}/media/{scene_id}.wav"

            turn_data = {
                "turn_index": turn_index,
                "scene_id": scene_id,
                "command": payload.get("command", ""),
                "story_text": payload.get("story_text", ""),
                "choices": payload.get("choices", []),
                "carried_item": payload.get("carried_item", None),
                "image_url": image_url,
                "audio_url": audio_url,
                "timestamp": payload.get("timestamp", 0)
            }

            # Update existing turn or append
            replaced = False
            for i, t in enumerate(hist):
                if t.get("turn_index") == turn_index:
                    # preserve existing image or audio if not provided in update
                    if not image_url and t.get("image_url"):
                        turn_data["image_url"] = t.get("image_url")
                    if not audio_url and t.get("audio_url"):
                        turn_data["audio_url"] = t.get("audio_url")
                    hist[i] = turn_data
                    replaced = True
                    break

            if not replaced:
                hist.append(turn_data)

            save_history(hist)

            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "saved",
                "scene_id": scene_id,
                "turn_index": turn_index,
                "total_turns": len(hist),
                "turn_data": turn_data
            }).encode("utf-8"))
            print(f"[BLACKBOX] Saved Turn #{turn_index} ({scene_id}) to mission_history.json")
            return

        elif self.path == "/save_scene":
            # Direct media save
            files = sorted(os.listdir(RECORD_DIR))
            scene_id = payload.get("scene_id")
            if not scene_id:
                highest = 0
                for f in files:
                    if f.startswith("scene_") and ("." in f):
                        try:
                            num = int(f.split("_")[1].split(".")[0])
                            if num > highest:
                                highest = num
                        except: pass
                highest += 1
                scene_id = f"scene_{highest:03d}"

            img_b64 = payload.get("image_b64")
            if img_b64:
                if "base64," in img_b64:
                    img_b64 = img_b64.split("base64,")[1]
                with open(os.path.join(RECORD_DIR, f"{scene_id}.png"), "wb") as f:
                    f.write(base64.b64decode(img_b64))

            audio_b64 = payload.get("audio_b64")
            if audio_b64:
                if "base64," in audio_b64:
                    audio_b64 = audio_b64.split("base64,")[1]
                with open(os.path.join(RECORD_DIR, f"{scene_id}.wav"), "wb") as f:
                    f.write(base64.b64decode(audio_b64))

            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "saved", "scene_id": scene_id}).encode("utf-8"))
            return

        elif self.path == "/rewind":
            # Rewind mission_history.json to target_turn_index
            target = payload.get("target_turn_index", 1)
            hist = load_history()
            hist = [t for t in hist if t.get("turn_index") <= target]
            save_history(hist)

            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "rewound",
                "remaining_turns": len(hist),
                "current_turn": hist[-1] if hist else None
            }).encode("utf-8"))
            print(f"[BLACKBOX] Rewound mission_history.json to Turn #{target}")
            return

        elif self.path == "/reset_mission":
            save_history([])
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "reset"}).encode("utf-8"))
            print("[BLACKBOX] Reset mission_history.json to empty")
            return

        elif self.path == "/render_video":
            res = self.compile_video()
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        elif self.path == "/set_use_file":
            file_type = payload.get("type", "image")
            b64_data = payload.get("data")
            preset_name = payload.get("preset")
            now = time.time()
            
            if file_type == "image":
                target = os.path.join(BASE_DIR, "use.jpg")
                if b64_data:
                    if "base64," in b64_data:
                        b64_data = b64_data.split("base64,")[1]
                    with open(target, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                elif preset_name:
                    src = os.path.join(BASE_DIR, os.path.basename(preset_name))
                    if os.path.exists(src):
                        shutil.copyfile(src, target)
                if os.path.exists(target):
                    os.utime(target, (now, now))
                resp = {"status": "ok", "file": "use.jpg", "path": target, "mtime": int(now)}
                print(f"[BLACKBOX] Updated use.jpg from {'preset ' + preset_name if preset_name else 'upload'}")
            else:
                filename = payload.get("filename", "use.mp3")
                ext = os.path.splitext(filename)[1].lower()
                if ext not in [".mp3", ".wav", ".mp4", ".m4a", ".ogg", ".flac"]:
                    ext = ".mp3"
                target = os.path.join(BASE_DIR, f"use{ext}")
                if b64_data:
                    if "base64," in b64_data:
                        b64_data = b64_data.split("base64,")[1]
                    with open(target, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                elif preset_name:
                    src = os.path.join(BASE_DIR, os.path.basename(preset_name))
                    if os.path.exists(src):
                        shutil.copyfile(src, target)
                if os.path.exists(target):
                    os.utime(target, (now, now))
                resp = {"status": "ok", "file": f"use{ext}", "path": target, "mtime": int(now)}
                print(f"[BLACKBOX] Updated {os.path.basename(target)} from {'preset ' + preset_name if preset_name else 'upload'}")
                
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        elif self.path == "/render_wav2lip":
            seconds = payload.get("seconds", None)
            target_out = os.path.join(BASE_DIR, "result.mp4")
            face_path = os.path.join(BASE_DIR, "use.jpg")
            
            # Select most recently modified audio/source file (supports mp3, wav, mp4, m4a)
            candidates = [
                os.path.join(BASE_DIR, f) for f in ["use.mp3", "use.wav", "use.mp4", "use.m4a", "use.ogg", "use.flac"]
                if os.path.exists(os.path.join(BASE_DIR, f))
            ]
            if candidates:
                candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                audio_path = candidates[0]
            else:
                audio_path = os.path.join(BASE_DIR, "Generated_Track_driving_cyberpunk_rock_energe_7623.wav")

            if not os.path.exists(face_path):
                face_path = os.path.join(BASE_DIR, "avatar_cyber_singer.jpg")

            print(f"[BLACKBOX] Launching Wav2Lip neural render:")
            print(f"  Face:    {face_path}")
            print(f"  Audio:   {audio_path}")
            print(f"  Seconds: {seconds if seconds else 'Full track'}")

            cmd = [
                sys.executable,
                os.path.join(BASE_DIR, "generate_neural_video.py"),
                "--face", face_path,
                "--audio", audio_path,
                "--outfile", target_out
            ]
            if seconds and float(seconds) > 0:
                cmd.extend(["--seconds", str(seconds)])
                
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
                mtime = int(os.path.getmtime(target_out)) if os.path.exists(target_out) else int(time.time())
                resp = {
                    "status": "success",
                    "video_url": f"http://127.0.0.1:{PORT}/result.mp4?t={mtime}",
                    "face": face_path,
                    "audio": audio_path
                }
                print(f"[BLACKBOX] Wav2Lip render finished successfully -> {target_out}")
            except subprocess.CalledProcessError as err:
                print(f"[BLACKBOX] Wav2Lip render error:\n{err.stderr}")
                resp = {
                    "status": "error",
                    "message": err.stderr or str(err)
                }

            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def compile_video(self):
        """Finds all scene pairs and renders a cinematic mp4 video using ffmpeg."""
        files = sorted(os.listdir(RECORD_DIR))
        scenes = sorted(list(set([f.split(".")[0] for f in files if f.startswith("scene_")])))

        if not scenes:
            return {"status": "error", "message": "No recorded scenes found in mission_record."}

        temp_clips = []
        concat_list_file = os.path.join(RECORD_DIR, "concat_list.txt")
        fallback_img = os.path.join(BASE_DIR, "orpheus_background.png")

        try:
            for s in scenes:
                img = os.path.join(RECORD_DIR, f"{s}.png")
                audio = os.path.join(RECORD_DIR, f"{s}.wav")
                clip = os.path.join(RECORD_DIR, f"clip_{s}.mp4")

                if not os.path.exists(img):
                    img = fallback_img

                if not os.path.exists(audio):
                    continue

                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-i", img,
                    "-i", audio,
                    "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,zoompan=z='min(zoom+0.0015,1.15)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720",
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-c:a", "aac", "-b:a", "192k",
                    "-pix_fmt", "yuv420p",
                    "-shortest",
                    clip
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                temp_clips.append(clip)

            if not temp_clips:
                return {"status": "error", "message": "No audio clips available to sync with scenes."}

            with open(concat_list_file, "w") as f:
                for c in temp_clips:
                    f.write(f"file '{c}'\n")

            cmd_concat = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_list_file,
                "-c", "copy",
                OUTPUT_VIDEO
            ]
            subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            for c in temp_clips:
                try: os.remove(c)
                except: pass
            try: os.remove(concat_list_file)
            except: pass

            return {
                "status": "success",
                "video_path": OUTPUT_VIDEO,
                "scenes_compiled": len(temp_clips),
                "message": f"Successfully compiled {len(temp_clips)} scenes into {OUTPUT_VIDEO}!"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

def run_server():
    server = HTTPServer(("127.0.0.1", PORT), BlackBoxHandler)
    print(f"==========================================================")
    print(f"  Orpheus Black Box Recorder active on http://127.0.0.1:{PORT}")
    print(f"  Disk JSON Database: {HISTORY_FILE}")
    print(f"  Target Video:       {OUTPUT_VIDEO}")
    print(f"==========================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Black Box Recorder.")
        server.server_close()

if __name__ == "__main__":
    run_server()
