import os
import random
import subprocess
import cv2
import dlib
import numpy as np
from skimage.transform import PiecewiseAffineTransform, warp

# Configuration
INPUT_VIDEO = "avatar.mp4"
TEMP_VIDEO = "temp_blink_video.mp4"
OUTPUT_VIDEO = "output.mp4"
MODEL_PATH = "/home/jack/Desktop/Media_Studio/BLINK/shape_predictor_68_face_landmarks.dat"

# Initialize Face Detector & Landmark Predictor
print("Loading face detector and landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

# Open source video
cap = cv2.VideoCapture(INPUT_VIDEO)
if not cap.isOpened():
    raise FileNotFoundError(f"Could not open input video: {INPUT_VIDEO}")

fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"Video Info: {width}x{height} @ {fps:.1f} FPS, {total_frames} frames ({total_frames / fps:.1f}s)")

# Setup VideoWriter
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(TEMP_VIDEO, fourcc, fps, (width, height))

def warp_blink(img, landmarks, alpha, w, h):
    """Warps upper eyelids down toward lower eyelids based on alpha (0=open, 1=closed)."""
    src = landmarks.copy()
    dst = landmarks.copy()
    
    # Eyelid landmark indices (dlib 68-point model)
    # Left eye: 37, 38 (top) -> 41, 40 (bottom)
    # Right eye: 43, 44 (top) -> 47, 46 (bottom)
    top_eye = [37, 38, 43, 44]
    bot_eye = [41, 40, 47, 46]

    for t, b in zip(top_eye, bot_eye):
        dst[t] = src[t] + alpha * 0.92 * (src[b] - src[t])

    # Anchor image boundaries to keep background, hair, and neck completely still
    corners = np.array([
        [0, 0],
        [w - 1, 0],
        [0, h - 1],
        [w - 1, h - 1]
    ])

    src_full = np.vstack([src, corners])
    dst_full = np.vstack([dst, corners])

    try:
        tform = PiecewiseAffineTransform.from_estimate(dst_full, src_full)
    except AttributeError:
        tform = PiecewiseAffineTransform()
        tform.estimate(dst_full, src_full)

    warped = (warp(img, tform, output_shape=(h, w)) * 255).astype(np.uint8)
    return warped

# Generate natural blink schedule
# Smooth eyelid transition: open -> closing -> closed -> opening -> open
blink_curve = [0.25, 0.60, 0.95, 1.0, 0.70, 0.35]
blink_frames = {}

current_frame = int(fps * 2.0)  # Start first blink after 2 seconds
random.seed(42)  # For reproducible natural timing

while current_frame < total_frames - len(blink_curve):
    for offset, alpha in enumerate(blink_curve):
        blink_frames[current_frame + offset] = alpha

    # 15% probability of a natural double-blink
    if random.random() < 0.15:
        current_frame += len(blink_curve) + random.randint(4, 8)
        for offset, alpha in enumerate(blink_curve):
            if current_frame + offset < total_frames:
                blink_frames[current_frame + offset] = alpha

    # Next blink scheduled every 3.0 to 5.5 seconds
    current_frame += int(fps * random.uniform(3.0, 5.5))

total_blinks = len(blink_frames) // len(blink_curve)
print(f"Scheduled {total_blinks} blinks across the video.")

# Process video frames
frame_idx = 0
last_landmarks = None

print("Processing video...")
while True:
    ret, frame = cap.read()
    if not ret:
        break

    if frame_idx in blink_frames:
        alpha = blink_frames[frame_idx]
        
        # Detect face & landmarks for the blinking frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 0)
        if len(faces) > 0:
            shape = predictor(gray, faces[0])
            last_landmarks = np.array([[p.x, p.y] for p in shape.parts()])

        if last_landmarks is not None:
            frame = warp_blink(frame, last_landmarks, alpha, width, height)

    out.write(frame)
    frame_idx += 1

    if frame_idx % 250 == 0 or frame_idx == total_frames:
        percent = (frame_idx / total_frames) * 100
        print(f"Progress: {frame_idx}/{total_frames} frames ({percent:.1f}%)")

cap.release()
out.release()
cv2.destroyAllWindows()

# Check for audio in the source video and mux it into the output
print("Checking for audio stream in source video...")
probe_cmd = [
    "ffprobe", "-v", "error", "-select_streams", "a:0",
    "-show_entries", "stream=codec_type", "-of", "default=noprint_wrappers=1", INPUT_VIDEO
]

has_audio = False
try:
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    if "codec_type=audio" in res.stdout:
        has_audio = True
except Exception:
    pass

if has_audio:
    print("Muxing original audio and encoding final MP4...")
    mux_cmd = [
        "ffmpeg", "-y", "-i", TEMP_VIDEO, "-i", INPUT_VIDEO,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-map", "0:v:0", "-map", "1:a:0?",
        "-shortest",
        OUTPUT_VIDEO
    ]
    subprocess.run(mux_cmd, check=True)
    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)
else:
    print("Encoding final MP4...")
    encode_cmd = [
        "ffmpeg", "-y", "-i", TEMP_VIDEO,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        OUTPUT_VIDEO
    ]
    subprocess.run(encode_cmd, check=True)
    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)

print(f"\nDone! Successfully generated: {OUTPUT_VIDEO}")