#!/usr/bin/env python3

from PIL import Image, ImageFilter
from icecream import ic
from moviepy.editor import (
    ImageClip,
    VideoClip,
    VideoFileClip,
    CompositeVideoClip,
    ColorClip,
    AudioFileClip
)
import glob
import random
import os
import uuid
import shutil

# ==========================================================
# IMAGE FEATHERING
# ==========================================================

def feather_image(image, radius=50):
    """
    Applies a feathered transparency effect to the top and bottom edges of an image.
    """
    ic("Feathering image", image.size, "radius", radius)

    img = image.copy()

    mask = Image.new("L", img.size, 0)
    mask.paste(255, (0, radius, img.width, img.height - radius))
    mask = mask.filter(ImageFilter.GaussianBlur(radius))

    img.putalpha(mask)
    return img


# ==========================================================
# VERTICAL SEAMLESS IMAGE
# ==========================================================

def create_vertical_seamless_image(images, feather_radius=10, overlap=100):
    """
    Creates a seamless vertical image by stacking images with overlap and feathering.
    """
    total_height = sum(img.height for img in images) - overlap * (len(images) - 1)
    max_width = max(img.width for img in images)

    ic("Combined image size", max_width, total_height)

    combined = Image.new("RGBA", (max_width, total_height))

    y_offset = 0
    for idx, img in enumerate(images):
        feathered = feather_image(img, feather_radius)
        combined.paste(feathered, (0, y_offset), feathered)
        ic(f"Pasted image {idx+1}", "y_offset", y_offset)
        y_offset += img.height - overlap

    return combined


# ==========================================================
# SCROLLING VIDEO CREATION
# ==========================================================

def make_scrolling_video(image_path, output_video_path, video_duration=58, video_size=(512, 768)):
    """
    Creates a vertical scrolling video from bottom to top.
    """
    ic("Loading image for scrolling", image_path)

    image_clip = ImageClip(image_path)

    def scroll_frame(get_frame, t):
        y = int((image_clip.size[1] - video_size[1]) * (1 - t / video_duration))
        frame = get_frame(t)
        return frame[y:y + video_size[1], 0:video_size[0]]

    video = VideoClip(
        lambda t: scroll_frame(image_clip.get_frame, t),
        duration=video_duration
    ).set_fps(24)

    ic("Writing scrolling video", output_video_path)
    video.write_videofile(output_video_path, codec="libx264", audio=False)

    video.close()
    image_clip.close()

    return output_video_path


# ==========================================================
# TITLE FRAME + MUSIC OVERLAY
# ==========================================================

def add_title_image(video_path, hex_color="#A52A2A"):
    """
    Adds padded frame, title overlay image, and background music.
    """
    hex_color = random.choice([
        "#A52A2A", "#ad1f1f", "#16765c",
        "#7a4111", "#9b1050", "#8e215d", "#2656ca"
    ])

    ic("Using frame color", hex_color)

    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    video = VideoFileClip(video_path)
    width, height = video.size
    duration = video.duration

    ic("Video size", width, height, "Duration", duration)

    padded_size = (width + 50, height + 50)
    x_pos = (padded_size[0] - width) / 2
    y_pos = (padded_size[1] - height) / 2

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    background = ColorClip(padded_size, color=(r, g, b)).set_duration(duration)

    padded_video = CompositeVideoClip([
        background,
        video.set_position((x_pos, y_pos))
    ]).set_duration(duration)

    title_image_path = "static/assets/vertical_scroll.png"
    title = ImageClip(title_image_path)\
        .set_duration(duration)\
        .resize(padded_video.size)\
        .set_position((0, -5))

    composite = CompositeVideoClip([padded_video, title]).set_duration(duration)

    mp3_files = glob.glob("static/music/*.mp3")
    random.shuffle(mp3_files)
    music_path = random.choice(mp3_files)

    ic("Selected music", music_path)

    music = AudioFileClip(music_path)\
        .set_duration(duration)\
        .audio_fadein(1.0)\
        .audio_fadeout(1.0)

    composite = composite.set_audio(music)

    uid = uuid.uuid4().hex
    output_path = "static/temp_exp/verticalX.mp4"
    os.makedirs("static/temp_exp", exist_ok=True)
    os.makedirs("static/output_videos", exist_ok=True)
    final_copy = os.path.join("static", "output_videos", f"Ready_Post_{uid}.mp4")

    ic("Rendering final video", output_path)
    composite.write_videofile(output_path)

    shutil.copyfile(output_path, final_copy)
    ic("Copied to archive", final_copy)

    # Cleanup
    video.close()
    music.close()
    composite.close()
    padded_video.close()
    background.close()
    title.close()

    return output_path


# ==========================================================
# MAIN PIPELINE
# ==========================================================

image_files = (
    glob.glob("static/novel_images/*.png") +
    glob.glob("static/novel_images/*.jpg")
)

image_files.sort(key=os.path.getmtime, reverse=True)
ic("Images found", len(image_files))

images = [
    Image.open(img).convert("RGBA").resize((512, 768), Image.LANCZOS)
    for img in image_files
]

vertical_image = create_vertical_seamless_image(
    images,
    feather_radius=10,
    overlap=100
)

vertical_image_path = "static/vertical_seamless_image.png"
vertical_image.save(vertical_image_path)
ic("Saved vertical image", vertical_image_path)

scroll_video_path = make_scrolling_video(
    vertical_image_path,
    "static/vertical_seamless_video.mp4",
    video_duration=58,
    video_size=(512, 768)
)

add_title_image(scroll_video_path)
