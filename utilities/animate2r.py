#!/usr/bin/env python3
import os
import subprocess
from PIL import Image
from icecream import ic

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------

BACKGROUND_IMAGE = "static/projects/animate/scene.jpg"
ROBOT_IMAGE = "static/projects/animate/robot2r.png"
FRAME_DIR = "frames_robot_anim"
OUTPUT_VIDEO = "static/projects/robot_move2.mp4"

TOTAL_STEPS = 200
MOVE_X = -2
MOVE_Y = 1
FPS = 30  # playback speed

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

def main():
    ic("Starting robot animation render...")

    # Ensure frame directory exists
    if not os.path.exists(FRAME_DIR):
        os.makedirs(FRAME_DIR)

    # Load images
    ic("Loading images")
    scene = Image.open(BACKGROUND_IMAGE).convert("RGBA")
    robot = Image.open(ROBOT_IMAGE).convert("RGBA")

    width, height = scene.size
    ic(width, height)

    # Start position (top-left corner of the robot)
    x = 0
    y = 0

    frame_count = 0

    # Render frames
    for step in range(TOTAL_STEPS):
        ic(f"Creating frame {step}")

        frame = scene.copy()
        frame.alpha_composite(robot, (x, y))

        frame_path = os.path.join(FRAME_DIR, f"frame_{step:04d}.png")
        frame.save(frame_path)

        # Move robot
        x += MOVE_X
        y += MOVE_Y

        # Boundaries check (so robot doesn't wander off)
        if x > width:
            x = width
        if y > height:
            y = height

        frame_count += 1

    ic(f"Total frames created: {frame_count}")

    # -------------------------------------------------------
    # Build MP4 using ffmpeg
    # -------------------------------------------------------

    ic("Building MP4 using ffmpeg")

    ffmpeg_cmd = (
        f"ffmpeg -y -framerate {FPS} -i {FRAME_DIR}/frame_%04d.png "
        f"-c:v libx264 -pix_fmt yuv420p {OUTPUT_VIDEO}"
    )

    ic(ffmpeg_cmd)
    subprocess.run(ffmpeg_cmd, shell=True)

    ic(f"Finished! Video saved to: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()
