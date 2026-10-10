#!/usr/bin/env python3
"""
update_models_video.py
Compiles model benchmark frames into modelsX.mp4 and modelX.mp4 at strictly 2 fps (2 per second),
ensuring viewers have a chance to appreciate each model's distinct artistic style.
Keeps running in the background until the active all_models process finishes.
"""

import os
import time
import shutil
import tempfile
import subprocess
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "novel_images")
TEMP_EXP_DIR = os.path.join(BASE_DIR, "static", "temp_exp")

MODELS = [
    "comiccraftLCM_beta4.safetensors",
    "dreamshaper_8LCM.safetensors",
    "possibleLoveliesLCM_v10.safetensors",
    "cyberphotonlcm_v10.safetensors",
    "semirealxLCM_v10.safetensors",
    "coldfleshRealisticLCM_v10.safetensors",
    "silversRealmixLCM_v10.safetensors",
    "geekyghostLCM_v10.safetensors",
    "xenobabesLCMEdition_v10.safetensors",
    "wonderDreamLCM_v10Crystal.safetensors",
    "twinkleRealSemiReal_v11.safetensors",
    "xenoxtcLCMEditionArtToon_v10.safetensors",
    "truevisionLCM77_v10.safetensors",
    "delusionsLCM_v20.safetensors",
    "frtMixmodelLCM_realisticV10.safetensors",
    "epicphotogasmLCM_ultimatefidelity.safetensors",
    "realmodelbase02LCM_v10.safetensors",
    "cyberrealisticLCM_cyberrealistic42.safetensors",
    "realisticLCMBYStable_v10.safetensors",
    "xenogasmLCMEditionSFWNSFW_lcmV5.safetensors",
    "photonLCM_v10.safetensors",
    "linierflowLCM_v10.safetensors",
    "madnessLCMV1_v10.safetensors",
    "kitschInSyncAndABagOfChips_v2.safetensors",
    "xxmix9realistic_v40+LCM_LoRA_Weights_SD15.fp16.safetensors",
    "rmbtestLCM_rmbtest4V10.safetensors",
    "dreamcrafterLCM_v10.safetensors"
]

def compile_at_2fps(seed=3407):
    # Collect all existing frames for the target seed in canonical model order
    frame_paths = []
    for model_name in MODELS:
        fp = os.path.join(OUTPUT_DIR, f"{seed}_{model_name}_output.png")
        if os.path.exists(fp) and os.path.getsize(fp) > 0:
            frame_paths.append(fp)

    if not frame_paths:
        # Fallback: check any seed's model output
        all_model_pngs = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*_*LCM*_output.png")))
        if all_model_pngs:
            frame_paths = all_model_pngs

    if not frame_paths:
        print("[!] No model output frames found yet.")
        return False

    temp_dir = tempfile.mkdtemp(prefix="models_2fps_")
    try:
        for idx, img_path in enumerate(frame_paths):
            symlink_path = os.path.join(temp_dir, f"frame_{idx:05d}.png")
            try:
                os.symlink(os.path.abspath(img_path), symlink_path)
            except Exception:
                shutil.copyfile(img_path, symlink_path)

        out_tmp = os.path.join(temp_dir, "modelsX_2fps.mp4")
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-framerate", "2",
            "-i", os.path.join(temp_dir, "frame_%05d.png"),
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "18",
            out_tmp
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(out_tmp) and os.path.getsize(out_tmp) > 0:
            destinations = [
                os.path.join(OUTPUT_DIR, "modelsX.mp4"),
                os.path.join(OUTPUT_DIR, "modelX.mp4"),
                os.path.join(TEMP_EXP_DIR, "modelsX.mp4"),
                os.path.join(TEMP_EXP_DIR, "modelX.mp4")
            ]
            for dst in destinations:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(out_tmp, dst)
            print(f"[✓] Successfully compiled {len(frame_paths)} frames at 2 fps (2 per second) -> modelsX.mp4 & modelX.mp4")
            return True
        else:
            print(f"[!] FFmpeg error: {res.stderr.strip()}")
            return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def is_allmodels_running():
    try:
        res = subprocess.run(["pgrep", "-f", "ONE_allmodels.py"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def main():
    # 1. Compile immediately with current frames
    print("[*] Performing initial compile at 2 fps...")
    compile_at_2fps()

    # 2. Watch loop to update as new models finish
    last_frame_count = len([f for f in os.listdir(OUTPUT_DIR) if f.startswith("3407_") and f.endswith("_output.png")])
    idle_count = 0
    while True:
        time.sleep(15)
        current_frames = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("3407_") and f.endswith("_output.png")]
        if len(current_frames) > last_frame_count:
            print(f"[*] New model frame detected ({len(current_frames)} frames). Re-compiling at 2 fps...")
            compile_at_2fps()
            last_frame_count = len(current_frames)
            idle_count = 0

        if not is_allmodels_running():
            idle_count += 1
            if idle_count >= 4 or len(current_frames) >= len(MODELS):
                break
        else:
            idle_count = 0

    # 3. Final compile after process exits to guarantee 2 fps
    print("[*] ONE_allmodels.py completed. Performing final compile at 2 fps...")
    time.sleep(3)
    compile_at_2fps()
    print("[✓] modelsX.mp4 / modelX.mp4 watcher finished.")

if __name__ == "__main__":
    main()
