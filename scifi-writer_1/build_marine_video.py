#!/usr/bin/env python3
"""
Build Marine Video: Dedicated Pipeline for Cybernetic Marine Storyboard
Outputs:
  - Assets: assets/marine_panels/, assets/marine_audio/, assets/marine_snapshots/
  - Master Video: cybernetic_marine.mp4 (1080p, H.264, AAC)
Non-destructive: Zero overwrite of existing panel or video releases.
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import scifi_engine

WORKSPACE_DIR = Path(__file__).resolve().parent
PANELS_DIR = WORKSPACE_DIR / "assets" / "marine_panels"
AUDIO_DIR = WORKSPACE_DIR / "assets" / "marine_audio"
SNAPSHOTS_DIR = WORKSPACE_DIR / "assets" / "marine_snapshots"
TEMP_DIR = WORKSPACE_DIR / "temp_marine"
OUTPUT_MP4 = WORKSPACE_DIR / "cybernetic_marine.mp4"
STORYBOARD_MD = WORKSPACE_DIR / "cybernetic_marine.md"
BGM_PATH = Path("/home/jack/Desktop/mp3/Shadows-Anno_Domini_Beats.mp3")

KOKORO_BIN = Path("/home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/kokoro-tts")
KOKORO_MODEL = Path("/home/jack/Desktop/Kokoro-TTS-Pause/kokoro-v1.0.onnx")
KOKORO_VOICES = Path("/home/jack/Desktop/Kokoro-TTS-Pause/voices-v1.0.bin")

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

for d in [PANELS_DIR, AUDIO_DIR, SNAPSHOTS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def generate_marine_audio(panels):
    print("\n[*] [KOKORO TTS] Synthesizing Cybernetic Marine audio...")
    for p in panels:
        idx = p["index"]
        wav_out = AUDIO_DIR / f"panel_{idx}.wav"
        p["audio_path"] = str(wav_out)

        if wav_out.exists() and wav_out.stat().st_size > 1000:
            dur = scifi_engine.get_audio_duration(str(wav_out))
            print(f"[+] Audio for Panel {idx} already exists ({dur:.2f}s), using existing.")
            continue

        spoken_text = p.get("spoken_text") or scifi_engine.clean_for_speech(p.get("raw_text", ""))
        voice = p.get("voice", "af_nova")
        speed = p.get("speed", 0.95)

        temp_txt = TEMP_DIR / f"tts_{idx}.txt"
        temp_txt.write_text(spoken_text, encoding="utf-8")

        print(f"[*] Panel {idx} Voice: {voice} | Speed: {speed}")
        print(f"    Dialogue: \"{spoken_text[:75]}...\"")

        cmd = [
            str(KOKORO_BIN),
            str(temp_txt),
            str(wav_out),
            "--voice", voice,
            "--model", str(KOKORO_MODEL),
            "--voices", str(KOKORO_VOICES),
            "--speed", str(speed)
        ]
        t0 = time.time()
        subprocess.run(cmd, check=True)
        dur = scifi_engine.get_audio_duration(str(wav_out))
        print(f"[+] Synthesized {wav_out.name} ({dur:.2f}s) in {time.time() - t0:.2f}s")


def generate_marine_overlay(width: int, height: int, story_title: str, panel: dict, output_png: str):
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_top = ImageFont.truetype(FONT_BOLD, 22)
    font_badge = ImageFont.truetype(FONT_BOLD, 18)
    font_body = ImageFont.truetype(FONT_BOLD, 26)
    font_meta = ImageFont.truetype(FONT_BOLD, 15)

    clean_title = scifi_engine.sanitize_text_for_display(story_title)
    clean_header = scifi_engine.sanitize_text_for_display(panel.get("header", ""))

    # 1. Top HUD Bar (Teal / Oceanic Cyberpunk)
    draw.rectangle([(0, 0), (width, 56)], fill=(6, 18, 26, 225))
    draw.line([(0, 56), (width, 56)], fill=(0, 240, 210, 230), width=2)
    top_title = f">> {clean_title.upper()} // {clean_header.upper()}"
    draw.text((40, 16), top_title, fill=(0, 240, 210), font=font_top)
    draw.text((width - 400, 18), "NEURAL SYNC: 98.6% // SECTOR PACIFICA", fill=(140, 215, 210), font=font_meta)

    # 2. Bottom Dialogue Box
    box_x1 = 110
    box_y1 = height - 215
    box_x2 = width - 110
    box_y2 = height - 50

    draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], fill=(4, 14, 22, 230))
    draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], outline=(0, 210, 200, 180), width=2)

    # Neon amber/cyan corner brackets
    corner = 24
    for cx, cy, dx, dy in [
        (box_x1, box_y1, 1, 1),
        (box_x2, box_y1, -1, 1),
        (box_x1, box_y2, 1, -1),
        (box_x2, box_y2, -1, -1)
    ]:
        draw.line([(cx, cy), (cx + dx * corner, cy)], fill=(0, 255, 200, 255), width=4)
        draw.line([(cx, cy), (cx, cy + dy * corner)], fill=(0, 255, 200, 255), width=4)

    # 3. Speaker Badge
    voice = panel.get("voice", "af_nova")
    role = panel.get("voice_role", "RESEARCH SCIENTIST")
    badge_text = f":: LOG COMMS // {voice.upper()} [{role.upper()}]"
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0] + 36
    bh = 32
    bx = box_x1 + 32
    by = box_y1 - 16
    draw.rectangle([(bx, by), (bx + bw, by + bh)], fill=(0, 210, 180, 245))
    draw.text((bx + 18, by + 6), badge_text, fill=(2, 12, 16), font=font_badge)

    # 4. Dialogue Text
    raw_content = panel.get("spoken_text", panel.get("raw_text", ""))
    clean_content = scifi_engine.sanitize_text_for_display(raw_content)
    max_w = (box_x2 - box_x1) - 64
    lines = scifi_engine.wrap_text(clean_content, font_body, max_w, draw)
    text_y = box_y1 + 34
    for line in lines[:3]:
        draw.text((box_x1 + 32, text_y + 2), line, fill=(0, 0, 0, 240), font=font_body)
        draw.text((box_x1 + 30, text_y), line, fill=(240, 255, 250), font=font_body)
        text_y += 38

    overlay.save(output_png)
    return output_png


def render_clips(panels, story_title):
    print("\n[*] [COMPOSITOR] Rendering individual panel clips (1080p 30fps)...")
    clip_paths = []

    for p in panels:
        idx = p["index"]
        image_path = PANELS_DIR / f"panel_{idx}.jpg"
        audio_path = Path(p["audio_path"])
        clip_out = TEMP_DIR / f"clip_panel_{idx}.mp4"

        if not image_path.exists():
            raise FileNotFoundError(f"Missing panel image: {image_path}")

        audio_dur = scifi_engine.get_audio_duration(str(audio_path))
        clip_dur = round(audio_dur + 1.2, 2)

        overlay_png = str(TEMP_DIR / f"overlay_{idx}.png")
        generate_marine_overlay(1920, 1080, story_title, p, overlay_png)

        # Dynamic Camera Choreography
        if idx == 1:
            # High-speed swim: Fast lateral pan left to right
            zp_filter = "zoompan=z=1.12:x='min(it*18,iw-iw/zoom)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
        elif idx == 2:
            # Neural circuitry close-up: Slow micro push-in zoom
            zp_filter = "zoompan=z='min(zoom+0.0004,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
        else:
            # Panoramic shoreline & aurora: Slow sweeping zoom out
            zp_filter = "zoompan=z='max(1.15-0.0004*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"

        filter_complex = (
            f"[0:v]scale=2560:1440,{zp_filter}[bg]; "
            f"[bg][1:v]overlay=0:0[v]; "
            f"[2:a]adelay=400|400,apad=whole_dur={clip_dur}[a]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "30", "-t", str(clip_dur), "-i", str(image_path),
            "-i", str(overlay_png),
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]",
            "-t", str(clip_dur),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            str(clip_out)
        ]

        print(f"[*] Rendering Panel {idx} clip ({clip_dur}s)...")
        t0 = time.time()
        subprocess.run(cmd, check=True)
        print(f"[+] Rendered Panel {idx} in {time.time() - t0:.1f}s -> {clip_out.name}")
        clip_paths.append(clip_out)

    return clip_paths


def build_final_master(clip_paths, story_title):
    print("\n[*] [COMPOSITOR] Concatenating clips and mixing soundtrack...")
    concat_txt = TEMP_DIR / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    merged_raw = TEMP_DIR / "merged_raw.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(merged_raw)
    ]
    subprocess.run(cmd_concat, check=True)

    total_dur = scifi_engine.get_audio_duration(str(merged_raw))
    print(f"[+] Merged story duration: {total_dur:.2f}s")

    bgm_volume = 0.22
    fade_out_start = max(0.0, total_dur - 3.5)
    filter_audio = (
        f"[1:a]aloop=loop=-1:size=2e+09,volume={bgm_volume},"
        f"afade=t=in:ss=0:d=1.5,afade=t=out:st={fade_out_start:.2f}:d=3.5[bgm]; "
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd_master = [
        "ffmpeg", "-y",
        "-i", str(merged_raw),
        "-i", str(BGM_PATH),
        "-filter_complex", filter_audio,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "256k",
        str(OUTPUT_MP4)
    ]
    print(f"[*] Mixing BGM track: {BGM_PATH.name} (vol={bgm_volume})...")
    subprocess.run(cmd_master, check=True)

    print(f"\n[+] Master Video Successfully Built: {OUTPUT_MP4}")
    print(f"[+] File Size: {OUTPUT_MP4.stat().st_size / (1024*1024):.2f} MB")
    print(f"[+] Total Duration: {total_dur:.2f} seconds")


def extract_snapshots(clip_paths):
    print("\n[*] [SNAPSHOTS] Extracting 1080p preview snapshots...")
    for idx, cp in enumerate(clip_paths, 1):
        snap_path = SNAPSHOTS_DIR / f"snapshot_panel_{idx}.jpg"
        cmd = [
            "ffmpeg", "-y",
            "-ss", "2.0",
            "-i", str(cp),
            "-frames:v", "1",
            "-q:v", "2",
            str(snap_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[+] Snapshot Panel {idx}: {snap_path.name} ({snap_path.stat().st_size // 1024} KB)")


def main():
    print("=" * 65)
    print("🎬 CYBERNETIC MARINE - FULL VIDEO PIPELINE")
    print("=" * 65)

    if not STORYBOARD_MD.exists():
        raise FileNotFoundError(f"Missing storyboard: {STORYBOARD_MD}")

    content = STORYBOARD_MD.read_text(encoding="utf-8")
    parsed = scifi_engine.parse_storyboard_markdown(content)
    print(f"[*] Storyboard Title: {parsed['title']}")
    print(f"[*] Total Panels: {len(parsed['panels'])}")

    generate_marine_audio(parsed["panels"])
    clip_paths = render_clips(parsed["panels"], parsed["title"])
    build_final_master(clip_paths, parsed["title"])
    extract_snapshots(clip_paths)

    print("\n" + "=" * 65)
    print("🎉 CYBERNETIC MARINE VIDEO & ASSETS READY!")
    print("=" * 65)


if __name__ == "__main__":
    main()
