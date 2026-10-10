#!/usr/bin/env python3
"""
CLI Video Generator for Sci-Fi Vision Storyboards
Usage:
    python3 build_video.py [--markdown template.md] [--output science_1.mp4] [--bgm track.mp3] [--volume 0.22]
"""

import sys
import argparse
from pathlib import Path
import scifi_engine

def main():
    parser = argparse.ArgumentParser(description="Render cinematic Sci-Fi MP4 from a Markdown Storyboard")
    parser.add_argument("--markdown", "-m", default="template.md", help="Path to markdown storyboard file")
    parser.add_argument("--output", "-o", default="science_1.mp4", help="Output MP4 filename or path")
    parser.add_argument("--bgm", "-b", default="", help="Specific BGM file path or filename in ~/Desktop/mp3/")
    parser.add_argument("--volume", "-v", type=float, default=0.22, help="BGM volume level (0.0 to 1.0)")
    parser.add_argument("--speed", "-s", type=float, default=0.95, help="TTS speech speed")

    args = parser.parse_args()

    md_path = Path(args.markdown)
    if not md_path.is_absolute():
        md_path = scifi_engine.WORKSPACE_DIR / md_path

    if not md_path.exists():
        print(f"[-] Error: Markdown file not found: {md_path}")
        sys.exit(1)

    print(f"🎬 [Sci-Fi Studio] Reading storyboard: {md_path.name}...")
    content = md_path.read_text(encoding="utf-8")
    parsed = scifi_engine.parse_storyboard_markdown(content)
    print(f"🎬 Title: {parsed['title']}")
    print(f"🎬 Recommended BGM: {parsed['bgm']}")
    print(f"🎬 Total Panels: {len(parsed['panels'])}")

    for p in parsed['panels']:
        print(f"   - Panel {p['index']}: [{p['header']}] | Voice: {p['voice']}")

    # Render video
    bgm_file = args.bgm
    if bgm_file and not Path(bgm_file).is_absolute():
        cand = scifi_engine.BGM_DIR / bgm_file
        if cand.exists():
            bgm_file = str(cand)

    out = scifi_engine.compile_full_video(
        storyboard=parsed,
        output_mp4=args.output,
        bgm_path=bgm_file,
        bgm_volume=args.volume
    )

    print(f"\n🚀 [SUCCESS] Video generated: {out}")

if __name__ == "__main__":
    main()
