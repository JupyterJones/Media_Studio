#!/usr/bin/env python3
"""
Add silence between audio segments
Usage: python3 add_silence_between.py input1.wav input2.wav output.wav --pause 2.0
"""

import sys
import os
import numpy as np
import soundfile as sf

def add_silence(audio_files, output_file, pause_seconds=2.0):
    """Merge audio files with silence between them"""
    segments = []
    sample_rate = 24000
    
    valid_files = [f for f in audio_files if os.path.exists(f) and os.path.getsize(f) > 0]
    if not valid_files:
        print("[!] No valid non-empty audio files to merge!")
        return

    for idx, audio_file in enumerate(valid_files):
        try:
            data, sr = sf.read(audio_file)
            if sample_rate is None:
                sample_rate = sr
            segments.append(data)
            
            # Add silence (except after last file)
            if idx < len(valid_files) - 1:
                silence_samples = int(pause_seconds * sr)
                if data.ndim > 1:
                    silence = np.zeros((silence_samples, data.shape[1]))
                else:
                    silence = np.zeros(silence_samples)
                segments.append(silence)
        except Exception as e:
            print(f"[!] Error reading {audio_file}: {e}")
    
    if segments:
        final_audio = np.concatenate(segments)
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        sf.write(output_file, final_audio, sample_rate)
        print(f"✅ Created {output_file} with {pause_seconds}s pauses")
        print(f"   Total duration: {len(final_audio)/sample_rate:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 add_silence_between.py input1.wav input2.wav output.wav --pause 2.0")
        sys.exit(1)
    
    pause = 2.0
    if "--pause" in sys.argv:
        pause_idx = sys.argv.index("--pause")
        pause = float(sys.argv[pause_idx + 1])
        input_files = sys.argv[1:pause_idx]
        output_file = input_files.pop()
    else:
        input_files = sys.argv[1:-1]
        output_file = sys.argv[-1]
    
    add_silence(input_files, output_file, pause)
