#!/usr/bin/env python3
"""
roi_seamless_clone_landing_blackbg.py

This script detects a plane on a black background as the ROI and animates it flying
across a destination image along a curved "landing" path using OpenCV's seamlessClone.

How it works:
1. Load source (plane on black) and destination images in BGR.
2. Automatically detect the plane ROI using a simple black threshold.
3. Crop and optionally resize the plane to fit the destination.
4. Generate a smooth curved landing path (left-top → bottom-right).
5. Apply seamlessClone along the path and write frames to MP4.
"""

import cv2
import numpy as np
from icecream import ic

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
FPS = 30
DURATION_SECONDS = 15
OUTPUT_MP4 = "plane_landing_blackbg.mp4"
BLEND_MODE = cv2.NORMAL_CLONE
MAX_SCALE = 0.9  # Max size relative to destination

# --------------------------------------------------
# LOAD IMAGES
# --------------------------------------------------
def load_bgr(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    return img

source_bgr = load_bgr("source1.png")  # plane on pure black
dest_bgr   = load_bgr("destination2.png")

# --------------------------------------------------
# DETECT ROI ON BLACK BACKGROUND
# --------------------------------------------------
# Convert to grayscale
gray = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2GRAY)

# Threshold: non-black pixels = plane
_, mask_bin = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

# Find contours
contours, _ = cv2.findContours(mask_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if not contours:
    raise ValueError("No ROI detected.")

# Largest contour = plane
largest_contour = max(contours, key=cv2.contourArea)

# Create precise mask
mask_roi = np.zeros_like(mask_bin)
cv2.drawContours(mask_roi, [largest_contour], -1, 255, thickness=cv2.FILLED)

# Bounding box
ys, xs = np.where(mask_roi > 0)
y1, y2 = ys.min(), ys.max()
x1, x2 = xs.min(), xs.max()
ic("ROI bounds", x1, y1, x2, y2)

# Crop source and mask
source_crop = source_bgr[y1:y2+1, x1:x2+1]
mask_crop   = mask_roi[y1:y2+1, x1:x2+1]
src_h, src_w = source_crop.shape[:2]
dst_h, dst_w = dest_bgr.shape[:2]

# --------------------------------------------------
# RESIZE IF TOO BIG
# --------------------------------------------------
scale = min(dst_w * MAX_SCALE / src_w, dst_h * MAX_SCALE / src_h, 1.0)
if scale < 1.0:
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    source_crop = cv2.resize(source_crop, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    mask_crop   = cv2.resize(mask_crop, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
    src_h, src_w = source_crop.shape[:2]
    ic(f"Resized object: {src_w}x{src_h}")

# --------------------------------------------------
# CENTER RANGE
# --------------------------------------------------
half_w, half_h = src_w // 2, src_h // 2
min_x, max_x = half_w, dst_w - half_w
min_y, max_y = half_h, dst_h - half_h
if min_x >= max_x or min_y >= max_y:
    raise ValueError("Plane too large for destination.")

# --------------------------------------------------
# VIDEO WRITER
# --------------------------------------------------
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
video = cv2.VideoWriter(OUTPUT_MP4, fourcc, FPS, (dst_w, dst_h))

# --------------------------------------------------
# CURVED LANDING PATH
# --------------------------------------------------
frame_count = FPS * DURATION_SECONDS
t = np.linspace(0, 1, frame_count)
xs = min_x + t * (max_x - min_x)
ys = min_y + (t**1.5) * (max_y - min_y)  # smooth descent

# --------------------------------------------------
# ANIMATION LOOP
# --------------------------------------------------
for i, (x, y) in enumerate(zip(xs, ys)):
    center = (int(x), int(y))
    ic(i, center)

    try:
        frame = cv2.seamlessClone(
            source_crop,
            dest_bgr,
            mask_crop,
            center,
            BLEND_MODE
        )
    except cv2.error as e:
        ic("seamlessClone failed, using fallback", e)
        frame = dest_bgr.copy()

    video.write(frame)

video.release()
ic("MP4 saved:", OUTPUT_MP4)
