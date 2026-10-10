#!/usr/bin/env python3

import sys
import subprocess
import os
from uuid import uuid4
from icecream import ic

def get_duration(input_file):
    """
    Returns the duration of a media file in seconds using ffprobe.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration = float(result.stdout.strip())
    return duration

def run_cmd(cmd):
    """
    Run subprocess command and show it using ic.
    """
    ic(" ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) != 3:
        print("Usage: python join_av.py input.mp3 input.mp4")
        sys.exit(1)

    mp3_file = sys.argv[1]
    mp4_file = sys.argv[2]

    if not os.path.exists(mp3_file):
        print(f"Audio file not found: {mp3_file}")
        sys.exit(1)

    if not os.path.exists(mp4_file):
        print(f"Video file not found: {mp4_file}")
        sys.exit(1)

    ic(f"Input audio: {mp3_file}")
    ic(f"Input video: {mp4_file}")

    audio_duration = get_duration(mp3_file)
    video_duration = get_duration(mp4_file)

    ic(f"Original audio duration: {audio_duration}")
    ic(f"Original video duration: {video_duration}")

    # Add 0.5 seconds of silence at beginning and end
    padded_audio = "audio_padded.mp3"
    pad_cmd = [
        "ffmpeg",
        "-y",
        "-i", mp3_file,
        "-af", "apad=pad_dur=0.5,adelay=500|500",
        padded_audio
    ]
    run_cmd(pad_cmd)

    # Updated duration after padding
    new_audio_duration = get_duration(padded_audio)
    ic(f"Padded audio duration: {new_audio_duration}")

    # Calculate playback speed change
    if video_duration == 0:
        print("Video duration is zero, cannot continue.")
        sys.exit(1)

    speed_factor = video_duration / new_audio_duration
    ic(f"Speed factor (video stretched x {speed_factor})")

    adjusted_video = "video_adjusted.mp4"
    speed_cmd = [
        "ffmpeg",
        "-y",
        "-i", mp4_file,
        "-filter:v", f"setpts={speed_factor}*PTS",
        "-an",
        adjusted_video
    ]
    run_cmd(speed_cmd)

    # Generate unique filename with UUID
    unique_id = str(uuid4())
    final_output = f"final_joined_{unique_id}.mp4"

    merge_cmd = [
        "ffmpeg",
        "-y",
        "-i", adjusted_video,
        "-i", padded_audio,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        final_output
    ]
    run_cmd(merge_cmd)

    ic(f"Created final video: {final_output}")

if __name__ == "__main__":
    main()
