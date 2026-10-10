#!/usr/bin/env python3
import numpy as np
from moviepy.editor import ImageSequenceClip, ImageClip
from PIL import Image, ImageDraw
import os
import glob
import random
import shutil
import uuid
from moviepy.editor import *
def create_circular_mask(size, radius):
    """
    Creates a circular mask of the given radius.
    The mask is a white circle (revealing) on a black background (hiding).
    """
    img = Image.new("L", size, 0)  # Black background
    draw = ImageDraw.Draw(img)
    center = (size[0] // 2, size[1] // 2)  # Center of the image
    draw.ellipse((center[0] - radius, center[1] - radius, 
                  center[0] + radius, center[1] + radius), fill=255)  # White circle
    return np.array(img)

def apply_mask(top_img, bottom_img, mask):
    """
    Combines the top and bottom images using the mask.
    The mask should be a 2D array where 255 reveals the bottom image and 0 keeps the top image.
    """
    return np.where(mask[:, :, None] == 255, bottom_img, top_img)

def create_transition(duration=2, fps=24):
    """
    Creates a transition video where the top image gradually reveals the next image in the list.
    Saves the resulting video as 'circular_mask_transition.mp4'.
    
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

        # Load images
        top_img = np.array(Image.open(top_img_path))
        bottom_img = np.array(Image.open(bottom_img_path))

        # Use height for the maximum radius to continue the transition until the entire image is covered
        max_radius = top_img.shape[0] // 2  # Based on image height, to cover the entire height

        # Create frames for the transition from top_img to bottom_img
        for j in range(num_frames):
            radius = int((j / num_frames) * max_radius)
            mask = create_circular_mask((top_img.shape[1], top_img.shape[0]), radius)
            frame = apply_mask(top_img, bottom_img, mask)
            frames.append(ImageClip(frame, duration=1/fps))
        
    # Create and save the video
    video_clip = ImageSequenceClip([np.array(f.img) for f in frames], fps=fps)
    video_clip.write_videofile('static/temp_exp/circular_mask_transition.mp4', codec='libx264')
def add_title(video_path, hex_color = "#A52A2A"):
    hex_color=random.choice(["#A52A2A","#ad1f1f","#16765c","#7a4111","#9b1050","#8e215d","#2656ca"])
    # Define the directory path
    directory_path = "tempp"
    # Check if the directory exists
    if not os.path.exists(directory_path):
        # If not, create it
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.") 
    # Load the video file and title image
    video_clip = VideoFileClip(video_path)
    print(video_clip.size)
    # how do i get the width and height of the video
    width, height = video_clip.size
    get_duration = video_clip.duration
    print(get_duration, width, height)
    title_image_path = "static/assets/circular_512x768.png"
    # Set the desired size of the padded video (e.g., video width + padding, video height + padding)
    padded_size = (width + 50, height + 50)

    # Calculate the position for centering the video within the larger frame
    x_position = (padded_size[0] - video_clip.size[0]) / 2
    y_position = (padded_size[1] - video_clip.size[1]) / 2
    #hex_color = "#09723c"
    # Remove the '#' and split the hex code into R, G, and B components
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Create an RGB tuple
    rgb_tuple = (r, g, b)

    # Create a blue ColorClip as the background
    blue_background = ColorClip(padded_size, color=rgb_tuple)

    # Add the video clip on top of the red background
    padded_video_clip = CompositeVideoClip([blue_background, video_clip.set_position((x_position, y_position))])
    padded_video_clip = padded_video_clip.set_duration(video_clip.duration)
    #title_image_path = "/home/jack/Desktop/EXPER/static/assets/Title_Image02.png"
    # Load the title image
    title_image = ImageClip(title_image_path)

    # Set the duration of the title image
    title_duration = video_clip.duration
    title_image = title_image.set_duration(title_duration)

    print(video_clip.size)
    # Position the title image at the center and resize it to fit the video dimensions
    #title_image = title_image.set_position(("left", "top"))
    title_image = title_image.set_position((0, -5))
    #video_clip.size = (620,620)
    title_image = title_image.resize(padded_video_clip.size)

    # Position the title image at the center and resize it to fit the video dimensions
    #title_image = title_image.set_position(("center", "center")).resize(video_clip.size)

    # Create a composite video clip with the title image overlay
    composite_clip = CompositeVideoClip([padded_video_clip, title_image])
    # Limit the length to video duration
    composite_clip = composite_clip.set_duration(video_clip.duration)
    # Load a random background music
    mp3_files = glob.glob("static/music/*.mp3")
    random.shuffle(mp3_files)

    # Now choose a random MP3 file from the shuffled list
    mp_music = random.choice(mp3_files)
    get_duration = AudioFileClip(mp_music).duration
    # Load the background music without setting duration
    music_clip = AudioFileClip(mp_music)
    # Fade in and out the background music
    #music duration is same as video
    music_clip = music_clip.set_duration(video_clip.duration)
    # Fade in and out the background music
    fade_duration = 1.0
    music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(fade_duration)
    # Set the audio of the composite clip to the background music
    composite_clip = composite_clip.set_audio(music_clip)
    uid = uuid.uuid4().hex
    os.makedirs('static/temp_exp', exist_ok=True)
    os.makedirs('static/output_videos', exist_ok=True)
    output_path = 'static/temp_exp/circular_mask_transitionX.mp4'
    # Export the final video with the background music
    composite_clip.write_videofile(output_path)
    mp4_file = os.path.join("static", "output_videos", f"Ready_Post_{uid}.mp4")
    shutil.copyfile(output_path, mp4_file)     
    print(mp4_file)
    VIDEO = output_path
    return VIDEO

# Example usage
create_transition(duration=2, fps=24)
video_path= 'static/temp_exp/circular_mask_transition.mp4'
add_title(video_path, hex_color = "#A52A2A")
