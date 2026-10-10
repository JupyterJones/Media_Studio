#!/usr/bin/env python3
"""
KOLBOLB Neural Video Lip-Sync Generator (Wav2Lip)
Usage:
  python3 generate_neural_video.py [face_image] [audio_file] [output_video] [duration_seconds]
Defaults:
  face:   /home/jack/Desktop/KOLBOLB/avatar_cyber_singer.jpg
  audio:  /home/jack/Desktop/KOLBOLB/Generated_Track_driving_cyberpunk_rock_energe_7623.wav
  output: /home/jack/Desktop/KOLBOLB/cyber_rock_lipsync.mp4
"""

import sys
import os
import shutil
import subprocess
import argparse
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAV2LIP_DIR = os.path.join(BASE_DIR, "wav2lip")
PYTHON_BIN = os.path.join(WAV2LIP_DIR, "venv_wav2lip", "bin", "python")
CHECKPOINT = os.path.join(WAV2LIP_DIR, "checkpoints", "wav2lip.pth")
DEFAULT_FACE = os.path.join(BASE_DIR, "avatar_cyber_singer.jpg")
DEFAULT_AUDIO = os.path.join(BASE_DIR, "Generated_Track_driving_cyberpunk_rock_energe_7623.wav")
DEFAULT_OUT = os.path.join(BASE_DIR, "cyber_rock_lipsync.mp4")

def extract_driving_vocals(input_audio, output_vocal_wav, verbose=True):
    """
    Extracts isolated vocals from a mixed song to drive Wav2Lip lip movements:
    1. DSP Center-channel extraction + vocal formant bandpass (200Hz - 3500Hz)
       + dynamic noise gate to cut bass, drum sizzle, and wide stereo instruments.
    2. Voice Activity Detection (VAD) via Whisper to detect exact singing timestamps
       and smoothly silence instrumental solos, drum breaks, and outros.
    """
    temp_dsp = os.path.join(BASE_DIR, "temp_dsp_filter.wav")
    try:
        # 1. FFmpeg vocal bandpass & center channel extraction
        cmd_dsp = [
            "ffmpeg", "-y", "-i", input_audio,
            "-af", "stereotools=mlev=1.4:slev=0.08,highpass=f=200,lowpass=f=3500,agate=threshold=0.015:ratio=4:range=0.02:attack=10:release=120",
            "-vn", "-ar", "16000", "-ac", "1",
            temp_dsp
        ]
        subprocess.run(cmd_dsp, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        import scipy.io.wavfile as wavfile
        sr, data = wavfile.read(temp_dsp)
        data = data.astype(np.float32) / 32768.0
        duration = len(data) / sr

        # 2. Whisper Singing / Speech Activity Detection
        try:
            import whisper
            if verbose:
                print("  [AI] Detecting singing segments with Whisper VAD...")
            model = whisper.load_model("tiny")
            res = model.transcribe(input_audio)
            segments = [s for s in res.get("segments", []) if s.get("text", "").strip()]

            if segments:
                mask = np.zeros(len(data), dtype=np.float32)
                fade_len = int(0.12 * sr)  # 120ms smooth crossfade

                for seg in segments:
                    s_idx = max(0, int((seg['start'] - 0.2) * sr))
                    e_idx = min(len(data), int((seg['end'] + 0.3) * sr))
                    mask[s_idx:e_idx] = 1.0

                if fade_len > 0:
                    kernel = np.ones(fade_len) / fade_len
                    mask = np.convolve(mask, kernel, mode="same")
                    mask = np.clip(mask, 0.0, 1.0)

                data = data * mask
                if verbose:
                    print(f"  [✓] Voice Activity Mask applied: {len(segments)} vocal phrases detected.")
                    print("      Instrumental solos & drum breaks silenced for lip-sync.")
            else:
                if verbose:
                    print("  [*] No discrete lyrics detected; using DSP formant bandpass.")
        except Exception as err:
            if verbose:
                print(f"  [!] Whisper VAD skipped ({err}); proceeding with DSP filter.")

        # Normalize vocal energy for clear mouth enunciation
        peak = np.max(np.abs(data))
        if peak > 0.01:
            data = (data / peak) * 0.95

        wavfile.write(output_vocal_wav, sr, (data * 32767.0).astype(np.int16))
        return True
    finally:
        if os.path.exists(temp_dsp):
            try: os.remove(temp_dsp)
            except: pass

def main():
    parser = argparse.ArgumentParser(description="Generate photorealistic lip-synced video using Wav2Lip")
    parser.add_argument("--face", default=DEFAULT_FACE, help="Path to face image or video")
    parser.add_argument("--audio", default=DEFAULT_AUDIO, help="Path to audio WAV/MP3")
    parser.add_argument("--outfile", default=DEFAULT_OUT, help="Path to output MP4 video")
    parser.add_argument("--seconds", type=float, default=None, help="Optional duration in seconds (clips audio for faster render)")
    parser.add_argument("--pads", nargs=4, type=int, default=[0, 10, 0, 0], help="Mouth padding [top, bottom, left, right]")
    parser.add_argument("--no-vocal-isolation", dest="vocal_isolation", action="store_false", default=True,
                        help="Disable vocal/music isolation (lips will react to raw audio including music)")
    args = parser.parse_args()

    face_path = os.path.abspath(args.face)
    audio_path = os.path.abspath(args.audio)
    out_path = os.path.abspath(args.outfile)

    if not os.path.exists(face_path):
        print(f"[!] Error: Face file not found: {face_path}")
        sys.exit(1)
    if not os.path.exists(audio_path):
        print(f"[!] Error: Audio file not found: {audio_path}")
        sys.exit(1)

    audio_to_use = audio_path
    temp_clipped = None
    temp_driving = None

    if args.seconds:
        temp_clipped = os.path.join(BASE_DIR, "temp_clipped_audio.wav")
        print(f"[*] Trimming soundtrack to first {args.seconds}s for fast generation...")
        cmd_trim = [
            "ffmpeg", "-y", "-i", args.audio,
            "-t", str(args.seconds),
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100",
            temp_clipped
        ]
        subprocess.run(cmd_trim, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio_to_use = temp_clipped

    if args.vocal_isolation:
        temp_driving = os.path.join(BASE_DIR, "temp_driving_vocals.wav")
        print("[*] Isolating voice from background music for clean lip-sync...")
        extract_driving_vocals(audio_to_use, temp_driving, verbose=True)

    print("==================================================================")
    print("  KOLBOLB Neural Lip-Sync Video Studio (Wav2Lip) ")
    print("==================================================================")
    print(f"  Face:           {args.face}")
    print(f"  Soundtrack:     {audio_to_use} (Full-fidelity music mix)")
    print(f"  Lip Driving:    {temp_driving if temp_driving else audio_to_use}")
    print(f"  Vocal Isolated: {'YES (Lips will NOT sing instruments)' if args.vocal_isolation else 'NO'}")
    print(f"  Output:         {args.outfile}")
    print(f"  Pads:           {args.pads}")
    print("------------------------------------------------------------------")
    print("  Generating video frames... (running on AMD Ryzen CPU)")

    cmd = [
        PYTHON_BIN,
        "inference.py",
        "--checkpoint_path", CHECKPOINT,
        "--face", face_path,
        "--audio", audio_to_use,
        "--outfile", out_path,
        "--pads", str(args.pads[0]), str(args.pads[1]), str(args.pads[2]), str(args.pads[3])
    ]
    if temp_driving and os.path.exists(temp_driving):
        cmd.extend(["--driving_audio", temp_driving])

    try:
        subprocess.run(cmd, cwd=WAV2LIP_DIR, check=True)
        print("------------------------------------------------------------------")
        print(f" [✓] SUCCESS! Neural Video generated at: {args.outfile}")
        print("==================================================================")
    finally:
        if temp_clipped and os.path.exists(temp_clipped):
            try: os.remove(temp_clipped)
            except: pass
        if temp_driving and os.path.exists(temp_driving):
            try: os.remove(temp_driving)
            except: pass

if __name__ == "__main__":
    main()
