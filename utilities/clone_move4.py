#!/usr/bin/env python3
"""
seamless_clone_movie5.py

This script creates a left-to-right moving seamless clone animation of a source object
over a destination image using OpenCV's seamlessClone function. The resulting video
is saved as an MP4 file.

How it works:
1. Load the source, destination, and mask images in BGR format.
2. Convert the mask to binary to isolate the object.
3. Crop the source and mask to the bounding box of the object.
4. Resize the object if it is too large relative to the destination.
5. Define a valid movement range for the object on the destination image.
6. Create a video writer for the output MP4.
7. Generate a motion path from left to right across the screen.
8. Loop through each frame, applying seamless cloning at the current position.
9. Write each frame to the MP4 and finalize the video.

Configuration:
- FPS: Frames per second of the output video.
- DURATION_SECONDS: Length of the animation in seconds.
- OUTPUT_MP4: Output file path.
- BLEND_MODE: OpenCV cloning mode (NORMAL_CLONE, MIXED_CLONE, MONOCHROME_TRANSFER).
- MAX_SCALE: Maximum scale of the object relative to the destination size.
"""

import cv2
import numpy as np
from icecream import ic

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
FPS = 30
DURATION_SECONDS = 15
OUTPUT_MP4 = "seamless_clone_movie5.mp4"
BLEND_MODE = cv2.NORMAL_CLONE  # NORMAL_CLONE, MIXED_CLONE, MONOCHROME_TRANSFER
MAX_SCALE = 0.9  # Max object size relative to destination

# --------------------------------------------------
# LOAD IMAGES (in BGR format)
# --------------------------------------------------
def load_bgr(path):
    """
    Loads an image from disk in BGR format.

    Args:
        path (str): Path to the image.

    Returns:
        np.ndarray: BGR image array.

    Raises:
        FileNotFoundError: If the file does not exist or cannot be read.
    """
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    return img

# Load source object, destination background, and object mask
source_bgr = load_bgr("source.png")
dest_bgr   = load_bgr("destination2.png")
mask_bgr   = load_bgr("mask2.png")

# --------------------------------------------------
# PREPARE MASK
# --------------------------------------------------
# Convert mask to grayscale and then binary (0 or 255)
mask_gray = cv2.cvtColor(mask_bgr, cv2.COLOR_BGR2GRAY)
mask_bin = (mask_gray > 128).astype(np.uint8) * 255

# Validate mask has content
if np.count_nonzero(mask_bin) == 0:
    raise ValueError("Mask is empty")

# --------------------------------------------------
# CROP SOURCE AND MASK TO MASK BOUNDS
# --------------------------------------------------
ys, xs = np.where(mask_bin > 0)      # Find non-zero pixels
y1, y2 = ys.min(), ys.max()
x1, x2 = xs.min(), xs.max()

ic("Mask bounds", x1, y1, x2, y2)

# Crop source and mask to bounding box
source_crop = source_bgr[y1:y2+1, x1:x2+1]
mask_crop   = mask_bin[y1:y2+1, x1:x2+1]

# Get dimensions
src_h, src_w = source_crop.shape[:2]
dst_h, dst_w = dest_bgr.shape[:2]

# --------------------------------------------------
# RESIZE IF OBJECT IS TOO BIG
# --------------------------------------------------
# Scale object proportionally to fit destination
scale_w = dst_w * MAX_SCALE / src_w
scale_h = dst_h * MAX_SCALE / src_h
scale = min(scale_w, scale_h, 1.0)  # Do not upscale

# Apply scaling if needed
if scale < 1.0:
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    source_crop = cv2.resize(source_crop, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    mask_crop   = cv2.resize(mask_crop, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
    src_h, src_w = source_crop.shape[:2]
    ic(f"Resized object to fit: {src_w}x{src_h}")

# --------------------------------------------------
# VALID CENTER RANGE FOR OBJECT PLACEMENT
# --------------------------------------------------
half_w = src_w // 2
half_h = src_h // 2

min_x = half_w
max_x = dst_w - half_w
min_y = half_h
max_y = dst_h - half_h

if min_x >= max_x or min_y >= max_y:
    raise ValueError("Source object is too large even after resizing")

# --------------------------------------------------
# VIDEO WRITER INITIALIZATION
# --------------------------------------------------
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
video = cv2.VideoWriter(OUTPUT_MP4, fourcc, FPS, (dst_w, dst_h))

# --------------------------------------------------
# MOTION PATH: LEFT → RIGHT
# --------------------------------------------------
frame_count = FPS * DURATION_SECONDS
xs = np.linspace(min_x, max_x, frame_count)  # Linear horizontal movement
ys = np.full(frame_count, (min_y + max_y) // 2)  # Fixed vertical position

# --------------------------------------------------
# ANIMATION LOOP
# --------------------------------------------------
for i, (x, y) in enumerate(zip(xs, ys)):
    center = (int(x), int(y))
    ic(i, center)

    # Apply seamless clone
    try:
        frame = cv2.seamlessClone(
            source_crop,
            dest_bgr,
            mask_crop,
            center,
            BLEND_MODE
        )
    except cv2.error as e:
        # Fallback if cloning fails
        ic("seamlessClone failed, using fallback", e)
        frame = dest_bgr.copy()

    # Write frame to video
    video.write(frame)

# Finalize video file
video.release()
ic("MP4 saved:", OUTPUT_MP4)
