#!/usr/bin/env python3
"""
Apply Effects: Post-Processing Video FX Engine
Provides standalone, zero-dependency visual effects post-processing for any Sci-Fi video.
Works directly on MP4 files using FFmpeg filtergraphs.

Usage:
  python3 apply_effects.py --input staacor_news.mp4 --preset cyberpunk
  python3 apply_effects.py --input science_1.mp4 --preset vhs
  python3 apply_effects.py --input science_v2.mp4 --effects scanlines,vignette
  python3 apply_effects.py --list
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent
EXPORTS_DIR = WORKSPACE_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Preset Filter Definitions (FFmpeg filter_complex chains)
EFFECT_PRESETS = {
    "cyberpunk": {
        "description": "High-contrast neon glow, boosted cyan & magenta color balance, and subtle edge vignette.",
        "filters": [
            "eq=contrast=1.22:saturation=1.35:brightness=-0.02",
            "colorbalance=rs=0.12:gs=-0.05:bs=0.22:rm=0.08:gm=-0.04:bm=0.18",
            "vignette=PI/5"
        ]
    },
    "scanlines": {
        "description": "Retro CRT television scanline grid with subtle phosphor glow.",
        "filters": [
            "drawgrid=width=1920:height=4:thickness=1:color=black@0.32",
            "eq=contrast=1.08:saturation=1.12"
        ]
    },
    "vhs": {
        "description": "1990s retro magnetic tape noise, color drift, softened contrast, and corner vignette.",
        "filters": [
            "curves=vintage",
            "noise=alls=14:allf=t+u",
            "vignette=PI/4",
            "eq=contrast=1.05:saturation=1.15"
        ]
    },
    "vignette": {
        "description": "Cinematic dark corner vignette focusing attention on center action.",
        "filters": [
            "vignette=PI/4"
        ]
    },
    "dust": {
        "description": "Atmospheric floating particles and cosmic dust grain.",
        "filters": [
            "noise=alls=22:allf=t+u"
        ]
    },
    "thermal": {
        "description": "Predator-style thermal / false-color heat reconnaissance mode.",
        "filters": [
            "lutrgb=r='val*1.4':g='255-val':b='val*0.35'",
            "eq=contrast=1.45:brightness=-0.05"
        ]
    },
    "holonet": {
        "description": "Staacor News planetary broadcast feed: scanlines + cyan tint + telemetry glow.",
        "filters": [
            "colorbalance=rs=-0.1:gs=0.1:bs=0.25",
            "drawgrid=width=1920:height=6:thickness=1:color=cyan@0.20",
            "eq=contrast=1.15:saturation=1.2"
        ]
    },
    "noir": {
        "description": "High contrast black and white cinematic noir with film grain.",
        "filters": [
            "hue=s=0",
            "eq=contrast=1.35:brightness=-0.03",
            "noise=alls=15:allf=t+u",
            "vignette=PI/4"
        ]
    }
}


def list_presets():
    print("=" * 65)
    print("🎬 AVAILABLE SCI-FI VIDEO FX PRESETS (100% LOCAL & STANDALONE)")
    print("=" * 65)
    for name, info in EFFECT_PRESETS.items():
        print(f"  • {name:<12} : {info['description']}")
    print("\nIndividual effects: scanlines, vignette, vhs, cyberpunk, dust, thermal, holonet, noir")
    print("=" * 65)


def apply_video_effects(input_path: str, output_path: str = None, preset: str = None, custom_effects: list = None):
    """
    Applies visual effects filters to an input video file.
    """
    inp = Path(input_path)
    if not inp.is_absolute():
        inp = WORKSPACE_DIR / inp

    if not inp.exists():
        raise FileNotFoundError(f"Input video not found: {inp}")

    if not output_path:
        base_stem = inp.stem
        tag = preset or "fx"
        out = WORKSPACE_DIR / f"{base_stem}_{tag}.mp4"
    else:
        out = Path(output_path)
        if not out.is_absolute():
            out = WORKSPACE_DIR / out

    filter_list = []

    if preset and preset.lower() in EFFECT_PRESETS:
        filter_list.extend(EFFECT_PRESETS[preset.lower()]["filters"])
    elif custom_effects:
        for fx in custom_effects:
            fx_clean = fx.strip().lower()
            if fx_clean in EFFECT_PRESETS:
                filter_list.extend(EFFECT_PRESETS[fx_clean]["filters"])
            elif fx_clean == "vignette":
                filter_list.append("vignette=PI/4")
            elif fx_clean == "scanlines":
                filter_list.append("drawgrid=width=1920:height=4:thickness=1:color=black@0.32")
            elif fx_clean == "dust":
                filter_list.append("noise=alls=20:allf=t+u")

    if not filter_list:
        filter_list.append("vignette=PI/5")

    vf_chain = ",".join(filter_list)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(inp),
        "-vf", vf_chain,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out)
    ]

    print(f"[*] Applying FX [{preset or ','.join(custom_effects or ['default'])}]...")
    print(f"    Source : {inp.name} ({inp.stat().st_size / (1024*1024):.2f} MB)")
    print(f"    Filter : {vf_chain}")
    print(f"    Target : {out.name}")

    subprocess.run(cmd, check=True)

    print(f"[+] FX Process Complete: {out.name}")
    print(f"[+] Output Size: {out.stat().st_size / (1024*1024):.2f} MB")
    return str(out)


def main():
    parser = argparse.ArgumentParser(description="Sci-Fi Video Post-Processing FX Engine")
    parser.add_argument("--input", "-i", type=str, help="Input MP4 video file")
    parser.add_argument("--output", "-o", type=str, help="Output MP4 video file")
    parser.add_argument("--preset", "-p", type=str, help="Preset name (cyberpunk, vhs, scanlines, vignette, dust, thermal, holonet, noir)")
    parser.add_argument("--effects", "-e", type=str, help="Comma-separated effects (e.g. scanlines,vignette)")
    parser.add_argument("--list", "-l", action="store_true", help="List all available presets and descriptions")

    args = parser.parse_args()

    if args.list:
        list_presets()
        return

    if not args.input:
        parser.print_help()
        print("\nTip: Run with --list to see all available presets.")
        sys.exit(1)

    custom_list = [e.strip() for e in args.effects.split(",")] if args.effects else None
    apply_video_effects(
        input_path=args.input,
        output_path=args.output,
        preset=args.preset or ("cyberpunk" if not custom_list else None),
        custom_effects=custom_list
    )


if __name__ == "__main__":
    main()
