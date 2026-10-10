#!/usr/bin/env python3
import numpy as np
from moviepy.editor import ImageSequenceClip, ImageClip, ColorClip, CompositeVideoClip, AudioFileClip, VideoFileClip
from PIL import Image, ImageDraw
import os
import glob
import random
import shutil
import uuid

def create_square_mask(size, side_length):
    """
    Creates a square mask of the given side length.
    The mask is a white square (revealing) on a black background (hiding).
    """
    img = Image.new("L", size, 0)  # Black background
    draw = ImageDraw.Draw(img)
    center = (size[0] // 2, size[1] // 2)  # Center of the image

    # Coordinates for the square
    left = center[0] - side_length // 2
    top = center[1] - side_length // 2
    right = center[0] + side_length // 2
    bottom = center[1] + side_length // 2

    draw.rectangle([left, top, right, bottom], fill=255)  # White square
    return np.array(img)

def apply_mask(top_img, bottom_img, mask):
    """
    Combines the top and bottom images using the mask.
    The mask should be a 2D array where 255 reveals the bottom image and 0 keeps the top image.
    """
    return np.where(mask[:, :, None] == 255, bottom_img, top_img)

def create_transition(duration=2, fps=24):
    """
    Creates a transition video where the top image gradually reveals the next image in the list
    using an expanding square mask.
    Saves the resulting video as 'square_mask_transition.mp4'.
    
    :param duration: Duration of each transition.
    :param fps: Frames per second.
    """
    frames = []
    num_frames = duration * fps  # Total number of frames
    image_list = glob.glob('static/novel_images/*.jpg') + glob.glob('static/novel_images/*.png')  # Get all jpg and png files
    image_list.sort(key=os.path.getmtime, reverse=False)  # Sort by modification time, oldest first

    if len(image_list) < 2:
        print("Not enough images in the directory to create a transition.")
        return

    # Loop through all pairs of images in the directory
    for i in range(len(image_list) - 1):
        top_img_path = image_list[i]
        bottom_img_path = image_list[i + 1]

        try:
            # Load images
            top_img = np.array(Image.open(top_img_path))
            bottom_img = np.array(Image.open(bottom_img_path))
        except Exception as e:
            print(f"Error loading images: {top_img_path}, {bottom_img_path}. Exception: {e}")
            continue

        print(f"Transitioning from {top_img_path} to {bottom_img_path}")
        print(f"Top image shape: {top_img.shape}, Bottom image shape: {bottom_img.shape}")

        # Use the largest dimension (width or height) to ensure the square grows fully
        max_side_length = max(top_img.shape[0], top_img.shape[1])

        # Create frames for the transition from top_img to bottom_img
        for j in range(num_frames):
            side_length = int((j / num_frames) * max_side_length)  # Increase square size over time
            mask = create_square_mask((top_img.shape[1], top_img.shape[0]), side_length)
            frame = apply_mask(top_img, bottom_img, mask)
            frames.append(ImageClip(frame, duration=1/fps))

            if j == num_frames // 2:  # Print debug info mid-transition
                print(f"Mid-transition at frame {j}, side_length: {side_length}")

    if not frames:
        print("No frames were generated!")
        return

    print(f"Total frames generated: {len(frames)}")

    # Create and save the video
    video_clip = ImageSequenceClip([np.array(f.img) for f in frames], fps=fps)
    video_clip.write_videofile('static/temp_exp/square_mask_transition.mp4', codec='libx264')

def add_title(video_path, hex_color="#A52A2A"):
    hex_color = random.choice(["#A52A2A", "#ad1f1f", "#16765c", "#7a4111", "#9b1050", "#8e215d", "#2656ca"])

    # Load the video file
    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    video_duration = video_clip.duration

    # Set the desired size of the padded video (extra padding for title)
    padded_size = (width + 50, height + 50)
    title_image_path = "static/assets/square_512x768.png"
    
    # Calculate the position for centering the video within the larger frame
    x_position = (padded_size[0] - width) / 2
    y_position = (padded_size[1] - height) / 2

    # Convert hex color to RGB
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    rgb_tuple = (r, g, b)

    # Create a background color clip
    background_clip = ColorClip(padded_size, color=rgb_tuple)

    # Add the video clip on top of the background
    padded_video_clip = CompositeVideoClip([background_clip, video_clip.set_position((x_position, y_position))])
    padded_video_clip = padded_video_clip.set_duration(video_duration)

    # Load the title image and set its duration to match the video
    title_image = ImageClip(title_image_path).set_duration(video_duration)

    # Resize the title image to cover the entire video frame
    title_image = title_image.resize(padded_video_clip.size)

    # Position the title image over the entire frame (centered by default)
    title_image = title_image.set_position(("center", "center"))

    # Combine the padded video and the title image
    composite_clip = CompositeVideoClip([padded_video_clip, title_image])
    composite_clip = composite_clip.set_duration(video_duration)

    # Load a random background music
    mp3_files = glob.glob("static/music/*.mp3")
    random.shuffle(mp3_files)
    mp_music = random.choice(mp3_files)
    music_clip = AudioFileClip(mp_music).set_duration(video_duration)

    # Set the audio of the composite clip to the background music
    composite_clip = composite_clip.set_audio(music_clip)

    # Save the final video
    uid = uuid.uuid4().hex
    os.makedirs('static/temp_exp', exist_ok=True)
    os.makedirs('static/output_videos', exist_ok=True)
    output_path = 'static/temp_exp/square_transitionX.mp4'
    composite_clip.write_videofile(output_path)
    shutil.copyfile(output_path, f'static/output_videos/square_mask_transitionX_{uid}.mp4')

    return output_path

# Example usage
create_transition(duration=2, fps=24)
video_path = 'static/temp_exp/square_mask_transition.mp4'
add_title(video_path)
