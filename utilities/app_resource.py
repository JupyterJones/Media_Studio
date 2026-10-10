#!/home/jack/virtualenv_name/bin/python
import os
import random
import glob
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, flash, jsonify, make_response, abort
# Image Processing Libraries
from PIL import (
    Image, ImageOps, ImageDraw, ImageFont, ImageFilter, ImageEnhance, 
    ImageSequence, ImageChops, ImageStat, ImageColor, ImagePalette
)
from moviepy.editor import (
    ImageClip, VideoClip, clips_array, concatenate_videoclips, CompositeVideoClip, 
    ColorClip, VideoFileClip, AudioFileClip, concatenate_audioclips, TextClip, 
    ImageSequenceClip
)
from datetime import datetime
import inspect
import subprocess
import shutil
from werkzeug.utils import secure_filename
import numpy as np
import cv2
from PIL import Image
import glob
import subprocess
import string
import uuid
import base64
import io
import json
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ImageDraw, ImageFont
from functools import wraps
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

app.config['UPLOAD_FOLDER'] = 'static/archived-images'
app.config['MASK_FOLDER'] = 'static/masks'
app.config['STORE_FOLDER'] = 'static/archived-store'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB
# Directory to save downloaded videos and extracted images
DOWNLOAD_FOLDER = 'static/downloads'
ARCHIVED_IMAGES_FOLDER = 'static/archived-images'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['ARCHIVED_IMAGES_FOLDER'] = ARCHIVED_IMAGES_FOLDER

# Ensure the directories exist
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(ARCHIVED_IMAGES_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['MASK_FOLDER']):
    os.makedirs(app.config['MASK_FOLDER'])

if not os.path.exists(app.config['STORE_FOLDER']):
    os.makedirs(app.config['STORE_FOLDER'])
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

# Decorator to protect routes
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            flash("You must be logged in to perform this action.", "danger")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper
MP3_DIR='static/music/'
# Helper function to list all MP3s in the directory
def get_an_mp3():
    #mp3_list = [f for f in os.listdir(MP3_DIR) if f.endswith('.mp3')]
    mp3_ = random.choice(glob.glob(MP3_DIR+'*.mp3'))
    #mp3_list = sorted(mp3_list, key=os.path.getmtime, reverse=True)
    return mp3_

def rename_jpeg_to_jpg(directory):
    """
    Rename all .jpeg files in the specified directory to .jpg.
    :param directory: Path to the directory containing files to rename
    """
    if not os.path.exists(directory):
        print(f"The directory '{directory}' does not exist.")
        return
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(".jpeg"):
            old_path = os.path.join(directory, filename)
            new_filename = f"{os.path.splitext(filename)[0]}.jpg"
            new_path = os.path.join(directory, new_filename)
            os.rename(old_path, new_path)
            #print(f"Renamed: '{filename}' -> '{new_filename}'")


# Logging function
def logit(message):
    try:
        # Get the current timestamp
        timestr = datetime.now().strftime('%A_%b-%d-%Y_%H-%M-%S')
        #print(f"timestr: {timestr}")

        # Get the caller's frame information
        caller_frame = inspect.stack()[1]
        filename = caller_frame.filename
        lineno = caller_frame.lineno

        # Convert message to string if it's a list
        if isinstance(message, list):
            message_str = ' '.join(map(str, message))
        else:
            message_str = str(message)

        # Construct the log message with filename and line number
        log_message = f"{timestr} - File: {filename}, Line: {lineno}: {message_str}\n"

        # Open the log file in append mode
        with open("exp_log.txt", "a") as file:
            # Write the log message to the file
            file.write(log_message)

            # Print the log message to the console
            print(log_message)

    except Exception as e:
        # If an exception occurs during logging, print an error message
        print(f"Error occurred while logging: {e}")

logit("App started")

def get_image_paths():
    image_paths = []
    for ext in ['png', 'jpg', 'jpeg']:
        image_paths.extend(glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], f'*.{ext}')))
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    logit(f"Image paths: {image_paths}")
    return image_paths

def stored_image_paths():
    image_paths = []
    for ext in ['png', 'jpg', 'jpeg']:
        image_paths.extend(glob.glob(os.path.join(app.config['STORE_FOLDER'], f'*.{ext}')))
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    logit(f"Image paths: {image_paths}")
    return image_paths

@app.route('/')
def index():
    image_paths = stored_image_paths()
    return render_template('index_exp.html', image_paths=image_paths)

def load_images(image_directory):
    image_paths = []
    for ext in ['png', 'jpg', 'jpeg']:
        image_paths.extend(glob.glob(os.path.join(image_directory, f'*.{ext}')))
    random.shuffle(image_paths)
    return image_paths[:3]

def convert_to_grayscale(image_path):
    image = Image.open(image_path).convert('L')
    mask_path = os.path.join(app.config['MASK_FOLDER'], 'greyscale_mask.png')
    image.save(mask_path)
    #copy to upload folder
    unique_mask = f"static/archived-store/mask{uuid.uuid4()}.png"
    shutil.copy(mask_path, unique_mask)
    #return mask_path
    return redirect(url_for('index'))    

def convert_to_binary(image_path):
    # Convert image to grayscale
    image = Image.open(image_path).convert('L')
    
    # Calculate the mean pixel value to use as the threshold
    np_image = np.array(image)
    threshold = np.mean(np_image)
    
    # Convert image to binary based on the mean threshold
    binary_image = image.point(lambda p: 255 if p > threshold else 0)
    
    # Save the binary mask
    mask_path = os.path.join(app.config['MASK_FOLDER'], 'binary_mask.png')
    binary_image.save(mask_path)
    
    # Invert the binary mask
    inverted_image = binary_image.point(lambda p: 255 - p)
    
    # Save the inverted binary mask
    inverted_mask_path = os.path.join(app.config['MASK_FOLDER'], 'inverted_binary_mask.png')
    inverted_image.save(inverted_mask_path)
    unique_mask1 = f"static/archived-images/mask1{uuid.uuid4()}.png"
    unique_mask2 = f"static/archived-images/mask2{uuid.uuid4()}.png"
    # Copy both images to the upload folder
    shutil.copy(mask_path, unique_mask1)
    shutil.copy(inverted_mask_path, unique_mask2)
    return redirect(url_for('index'))
    #return mask_path, inverted_mask_path


def resize_images_to_base(base_image, images):
    base_size = base_image.size
    logit(f"Base size: {base_size}")
    resized_images = [base_image]
    for img in images[1:]:
        resized_images.append(img.resize(base_size, resample=Image.Resampling.LANCZOS))
    return resized_images

@app.route('/get_images', methods=['POST','GET'])
def get_images():
    image_directory = app.config['UPLOAD_FOLDER']
    logit(f"Image directory: {image_directory}")
    image_paths = load_images(image_directory)
    logit(f"Loaded images: {image_paths}")
    return render_template('display_images_exp.html', image_paths=image_paths, mask_path=None, opacity=0.5)

@app.route('/play_mp3', methods=['GET', 'POST'])
def play_mp3():
    music = 'static/audio/narration.mp3'
    return render_template('play_mp3.html', music=music)

@app.route('/edit_mask', methods=['POST'])
def edit_mask():
    image_paths = request.form.getlist('image_paths')
    mask_path = request.form.get('mask_path')
    opacity = float(request.form.get('opacity', 0.5))
    return render_template('display_images_exp.html', image_paths=image_paths, mask_path=mask_path, opacity=opacity)

@app.route('/store_result', methods=['POST'])
def store_result():
    result_image_path = request.form.get('result_image')
    unique_id = datetime.now().strftime('%Y%m%d%H%M%S')
    store_path = os.path.join(app.config['STORE_FOLDER'], f'result_{unique_id}.png')
    
    # Correct the path for the result image
    result_image_path = result_image_path.replace('/static/', 'static/')
    
    # Save the result image to the store folder
    image = Image.open(result_image_path)
    image.save(store_path)
    return redirect(url_for('index'))

@app.route('/refresh-images')
def refresh_images():
    try:
        # Run the script using subprocess
        subprocess.run(['/var/www/flaskarchitect/virtualenv_name/bin/python', 'refresh_images.py'], check=True)
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        return f"An error occurred: {e}"

@app.route('/refresh-video')
def refresh_video():
    try:
        # Run the script using subprocess
        subprocess.run(['python', 'refresh_video.py'], check=True)
        subprocess.run(['python', 'Best_FlipBook'], check=True)
        subprocess.run(['python', 'diagonal_transition'], check=True)        
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        return f"An error occurred: {e}"

@app.route('/display_resources', methods=['POST','GET'])
def display_resources():
    directory = 'static/archived-images'
    rename_jpeg_to_jpg(directory)
    images = glob.glob('static/archived-images/*.jpg')
    image_directory = app.config['UPLOAD_FOLDER']
    logit(f"Image directory: {image_directory}")
    image_paths = glob.glob('static/archived-images/*.jpg')
    #list by date last image first
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    return render_template('display_resources_exp.html', image_paths=image_paths)

@app.route('/select_images', methods=['GET', 'POST'])
def select_images():
    if request.method == 'POST':
        top_image = request.form.get('top_image')
        mask_image = request.form.get('mask_image')
        bottom_image = request.form.get('bottom_image')

        if not top_image or not mask_image or not bottom_image:
            return "Please select one top image, one mask image, and one bottom image."

        # Redirect to the blend_images route with the selected images
        return redirect(url_for('blend_images', top=top_image, mask=mask_image, bottom=bottom_image))

    image_paths = get_image_paths()
    return render_template('select_images.html', image_paths=image_paths)

@app.route('/blend_images', methods=['POST', 'GET'])
def blend_images():
    # Retrieve selected images from the form
    top_image = request.form.get('top_image')
    mask_image = request.form.get('mask_image')
    bottom_image = request.form.get('bottom_image')
    opacity = float(request.form.get('opacity', 0.5))

    # Check if all required images are provided
    if not all([top_image, mask_image, bottom_image]):
        return "Please select one top image, one mask image, and one bottom image."

    # Process images
    image_paths = [top_image, mask_image, bottom_image]
    result_path = blend_images_with_grayscale_mask(image_paths, mask_image, opacity)
    mask_image ="static/masks/mask.png"
    return redirect(url_for('index'))#, image_paths=image_paths, mask_path=mask_image, opacity=opacity))
    #render_template('blend_result_exp.html', result_image=result_path, image_paths=image_paths, mask_image=mask_image, opacity=opacity)

def blend_images_with_grayscale_mask(image_paths, mask_path, opacity):
    if len(image_paths) != 3:
        logit(f"Error: Expected exactly 3 image paths, got {len(image_paths)}")
        return None

    base_image_path, mask_image_path, top_image_path = image_paths
    logit(f"Base image path: {base_image_path}")
    logit(f"Mask image path: {mask_image_path}")
    logit(f"Top image path: {top_image_path}")

    base_image = Image.open(base_image_path)
    mask_image = Image.open(mask_path).convert('L')
    top_image = Image.open(top_image_path)
    base_image = base_image.resize((512,768), Image.LANCZOS)
    top_image = top_image.resize((512,768), Image.LANCZOS)
    mask_image = mask_image.resize((512,768), Image.LANCZOS)
    #base_image, top_image = resize_images_to_base(base_image, [base_image, top_image])[0], resize_images_to_base(base_image, [base_image, top_image])[1]
    blended_image = Image.composite(top_image, base_image, mask_image)

    unique_id = datetime.now().strftime('%Y%m%d%H%M%S')
    result_path = os.path.join(app.config['STORE_FOLDER'], f'result_{unique_id}.png')
    blended_image.save(result_path)
    logit(f"Blended image saved at: {result_path}")
    return redirect(url_for('index'))
    #return result_path

@app.route('/select_mask_image', methods=['POST', 'GET'])
def select_mask_image():
    if request.method == 'POST':
        selected_image = request.form.get('selected_image')
        if not selected_image:
            return "Please select an image for masking."
        return render_template('choose_mask.html', selected_image=selected_image)
    
    #get_image_paths = lambda: [os.path.join(app.config['MASK_FOLDER'], f) for f in os.listdir(app.config['MASK_FOLDER'])]
    image_paths = get_image_paths()
    return render_template('select_mask_image.html', image_paths=image_paths)

#get_image_paths = lambda: [os.path.join(app.config['MASK_FOLDER'], f) for f in os.listdir(app.config['MASK_FOLDER'])]

@app.route('/choose_mask', methods=['POST'])
def choose_mask():
    selected_image = request.form.get('selected_image')
    mask_type = request.form.get('mask_type')

    if not selected_image:
        return "Please select an image for masking."
    
    if mask_type == 'grayscale':
        mask_path = convert_to_grayscale(selected_image)
    elif mask_type == 'binary':
        mask_path = convert_to_binary(selected_image)
    else:
        return "Invalid mask type selected."
    #redirect to select
    return redirect(url_for('select_images'))
#render_template('select_images.html', image_paths=[selected_image], mask_path=mask_path, opacity=0.5)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/index_upload')
@login_required
def index_upload():
    logit("Rendering upload form.")
    return render_template('upload.html')

@app.route('/upload', methods=['POST', 'GET'])

def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        logit("No file part in request.")
        return redirect(request.url)

    file = request.files['file']

    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        flash('No selected file')
        logit("No file selected.")
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        logit(f"File saved to {save_path}.")
        return redirect(url_for('uploaded_file', filename=filename))
    else:
        flash('File type not allowed')
        logit("File type not allowed.")
        return redirect(request.url)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # You can create a route to handle what happens after a file is uploaded successfully
    logit(f"File uploaded: {filename}.")
    return redirect(url_for('index'))

def extract_random_frames(video_path, num_frames=25):
    try:
        video = VideoFileClip(video_path)
        duration = video.duration
        timestamps = sorted([random.uniform(0, duration) for _ in range(num_frames)])
        saved_images = []
        
        for i, timestamp in enumerate(timestamps):
            frame = video.get_frame(timestamp)
            img = Image.fromarray(frame)
            image_filename = f"frame_{i+1}.jpg"
            image_path = os.path.join(app.config['ARCHIVED_IMAGES_FOLDER'], image_filename)
            img.save(image_path)
            saved_images.append(image_filename)
        
        return saved_images
    except Exception as e:
        logit(f"Error extracting frames: {e}")
        raise

@app.route('/get_video_images', methods=['GET', 'POST'])
def get_video_images():
    if request.method == 'POST':
        url = request.form['url']
        if url:
            try:
                # Download the YouTube video
                video_path = download_youtube_video(url)
                
                # Extract 25 random frames
                images = extract_random_frames(video_path)
                
                # Redirect to display the images
                return redirect(url_for('display_images'))
            except Exception as e:
                logit(f"Error in /get_images: {e}")
                return str(e)
    
    return render_template('get_images.html')

@app.route('/images')
def display_images():
    try:
        images = os.listdir(app.config['ARCHIVED_IMAGES_FOLDER'])
        images = [os.path.join(app.config['ARCHIVED_IMAGES_FOLDER'], img) for img in images]
        return render_template('YouTube_gallery.html', images=images)
    except Exception as e:
        logit(f"Error in /images: {e}")
        return str(e)

def download_youtube_video(url):
    try:
        # Set the download options
        ydl_opts = {
            'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], '%(title)s.%(ext)s'),
            'format': 'mp4',  # Best format available
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video information and download the video
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title')
            
            # Sanitize and format the filename to remove spaces and special characters
            sanitized_title = secure_filename(video_title)
            sanitized_title = sanitized_title.replace(" ", "_")
            download_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f"{sanitized_title}.mp4")
            static_video_path = os.path.join('static', 'temp.mp4')

            # Find the downloaded file
            for root, dirs, files in os.walk(app.config['DOWNLOAD_FOLDER']):
                for file in files:
                    if file.endswith('.mp4'):
                        actual_downloaded_file = os.path.join(root, file)
                        break
                else:
                    continue
                break

            # Check if the video was downloaded correctly
            if os.path.exists(actual_downloaded_file):
                # Move the downloaded video to the static/temp.mp4 path
                shutil.move(actual_downloaded_file, static_video_path)
                logit(f"Video downloaded and moved to: {static_video_path}")
            else:
                logit(f"Downloaded file does not exist: {actual_downloaded_file}")
                raise FileNotFoundError(f"File not found: {actual_downloaded_file}")

            return static_video_path

    except Exception as e:
        logit(f"Error downloading video: {e}")
        raise
def create_feathered_image(foreground_path, output_path):
    # Load the foreground image
    foreground = cv2.imread(foreground_path)
    height, width = foreground.shape[:2]

    # Initialize dlib's face detector
    detector = dlib.get_frontal_face_detector()
    gray_foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY)
    faces = detector(gray_foreground)

    # Create an alpha channel and a binary mask
    alpha_channel = np.zeros((height, width), dtype=np.uint8)

    if len(faces) == 0:
        print("No face detected in the image. Using the entire image with no feathering.")
        # Use the entire image with a full alpha channel
        alpha_channel = np.full((height, width), 255, dtype=np.uint8)
    else:
        for face in faces:
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            center = (x + w // 2, y + h // 2)
            radius = max(w, h) // 2
            cv2.circle(alpha_channel, center, radius, 255, -1)

        # Feather the edges of the mask
        alpha_channel = cv2.GaussianBlur(alpha_channel, (101, 101), 0)

    # Add the alpha channel to the foreground image
    foreground_rgba = np.dstack((foreground, alpha_channel))

    # Save the result as a PNG file with transparency
    cv2.imwrite(output_path, foreground_rgba)

    print(f"Feathered image saved to: {output_path}")

    return output_path

def overlay_feathered_on_background(foreground_path, background_path, output_path):
    # Load the feathered image and background image
    foreground = cv2.imread(foreground_path, cv2.IMREAD_UNCHANGED)  # Load with alpha channel
    background = cv2.imread(background_path)

    # Resize and crop both images to 512x768
    foreground = resize_and_crop(foreground)
    background = resize_and_crop(background)

    # Extract the alpha channel from the foreground image
    alpha_channel = foreground[:, :, 3] / 255.0
    foreground_rgb = foreground[:, :, :3]

    # Ensure background has 4 channels
    background_rgba = cv2.cvtColor(background, cv2.COLOR_BGR2BGRA)
    background_alpha = background_rgba[:, :, 3] / 255.0

    # Validate dimensions
    if foreground_rgb.shape[:2] != background_rgba.shape[:2]:
        raise ValueError(f"Foreground and background dimensions do not match: {foreground_rgb.shape[:2]} vs {background_rgba.shape[:2]}")

    # Blend the images
    for i in range(3):  # For each color channel
        background_rgba[:, :, i] = (foreground_rgb[:, :, i] * alpha_channel + background_rgba[:, :, i] * (1 - alpha_channel)).astype(np.uint8)

    # Save the result
    cv2.imwrite(output_path, background_rgba)

    print(f"Composite image saved to: {output_path}")

    im = Image.open(output_path).convert('RGB')
    im.save(output_path[:-3] + 'jpg', quality=95)
    return output_path


def resize_and_crop(image, target_width=512, target_height=768):
    # Resize the image to fit the target dimensions while maintaining the aspect ratio
    height, width = image.shape[:2]
    aspect_ratio = width / height
    target_aspect_ratio = target_width / target_height

    if aspect_ratio > target_aspect_ratio:
        new_width = target_width
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = target_height
        new_width = int(new_height * aspect_ratio)

    resized_image = cv2.resize(image, (new_width, new_height))

    # Ensure the resized image is at least the target dimensions
    if resized_image.shape[0] < target_height or resized_image.shape[1] < target_width:
        resized_image = cv2.resize(image, (target_width, target_height))

    # Crop the resized image to the target dimensions
    crop_x = (resized_image.shape[1] - target_width) // 2
    crop_y = (resized_image.shape[0] - target_height) // 2
    cropped_image = resized_image[crop_y:crop_y + target_height, crop_x:crop_x + target_width]

    return cropped_image


@app.route('/face_detect', methods=['POST', 'GET'])
def face_detect():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            logit("No file part in request.")
            return redirect(request.url)

        file = request.files['file']

        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            logit("No file selected.")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            logit(f"File saved to {save_path}.")

            # Create a feathered PNG image from the detected face
            feathered_image_path = create_feathered_image(save_path, 'static/archived-images/feathered_face.png')

            # Overlay the feathered image on the background
            background_image_path = random.choice(glob.glob("static/archived-images/*.jpg"))
            output_composite_path = overlay_feathered_on_background(feathered_image_path, background_image_path, 'static/archived-images/composite_image.png')

            return render_template('face_detect.html', feathered_image=feathered_image_path, composite_image=output_composite_path)

    return render_template('face_detect.html')



@app.route('/about')#, methods=['POST', 'GET'])
def about():
    return render_template('application_overview.html')
def resize_image(image_path):
    # Open the image
    image = Image.open(image_path)
    
    # Resize the image
    resized_image = image.resize((512, 768), Image.LANCZOS)
    
    # Save the resized image
    resized_image.save(image_path)
    
    print(f"Resized image saved at: {image_path}")
    
@app.route('/resize_all')#, methods=['POST', 'GET'])
def resize_all():
    # Resize all images in the upload folder
    image_paths = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*.jpg'))
    logit(f"Image paths: {image_paths}")
    for image_path in image_paths:
        logit(f"Resizing image: {image_path}")
        resize_image(image_path)
    return redirect(url_for('index'))

@app.route('/mk_mask')
def mk_mask():
    masks=glob.glob('static/archived-images/mask*.jpg')
    # list by date, last image first
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)
    return render_template('mk_mask.html',mask_data=mask_data)


@app.route('/create_circle_mask', methods=['POST'])
def create_circle_mask():
    # Get input values from the form
    x = int(request.form.get('x', 0))
    y = int(request.form.get('y', 0))
    size = int(request.form.get('size', 50)) + 20
    feather = int(request.form.get('feather', 20))
    aspect = int(request.form.get('aspect', 0))
    
    # Calculate width and height based on aspect
    if aspect > 0:
        width = size + aspect  # Make width larger for wide aspect
        height = size
    elif aspect < 0:
        width = size
        height = size + abs(aspect)  # Make height larger for tall aspect
    else:
        width, height = size, size  # Default to square aspect ratio

    # Create a black background image (size 512x768)
    background = Image.new('RGBA', (512, 768), (0, 0, 0, 255))
    
    # Create a white ellipse (or circle if width == height)
    ellipse = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ellipse)
    draw.ellipse((0, 0, width, height), fill=(255, 255, 255, 255))

    # Apply feathering (blur the edges)
    ellipse = ellipse.filter(ImageFilter.GaussianBlur(feather))

    # Calculate position to paste the ellipse (centered by default)
    paste_position = (256 + x - width // 2, 384 + y - height // 2)
    background.paste(ellipse, paste_position, ellipse)
    background = background.convert('RGB')
    
    # Optionally blur the whole background
    background = background.filter(ImageFilter.GaussianBlur(30))
    
    # Save the result in static/archived-images
    mask_path = f'static/archived-images/mask_{x}_{y}_{size}_{feather}_{aspect}.jpg'
    background.save(mask_path)
    # save a copy of the mask to static/masks with same name as the mask_path not mask png
    shutil.copy(mask_path, 'static/masks/' + os.path.basename(mask_path))
     
    # List and sort masks by date (latest first)
    masks = glob.glob('static/archived-images/mask*.jpg')
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)

    return render_template('mk_mask.html', mask_path=mask_path, mask_data=mask_data)

@app.route('/create_rectangle_mask', methods=['POST'])
def create_rectangle_mask():
    # Get input values from the form
    x = int(request.form.get('x', 0))
    y = int(request.form.get('y', 0))
    size = int(request.form.get('size', 50)) + 20
    feather = int(request.form.get('feather', 20))
    aspect = int(request.form.get('aspect', 0))

    # Calculate width and height based on aspect
    if aspect > 0:
        width = size + aspect  # Make width larger for wide aspect
        height = size
    elif aspect < 0:
        width = size
        height = size + abs(aspect)  # Make height larger for tall aspect
    else:
        width, height = size, size  # Default to square aspect ratio

    # Create a new background image with a transparent background (RGBA)
    background = Image.new('RGBA', (512, 768), (0, 0, 0, 255))

    # Create a rectangle image with a transparent background (RGBA)
    rectangle_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))

    # Create an ImageDraw object to draw on the rectangle image
    draw = ImageDraw.Draw(rectangle_image)

    # Draw a solid white rectangle (change color as needed)
    draw.rectangle([0, 0, width, height], fill=(255, 255, 255, 255))

    # Apply feathering (blur the edges of the rectangle)
    rectangle_image = rectangle_image.filter(ImageFilter.GaussianBlur(feather))

    # Calculate the position to paste the rectangle (centered by default)
    paste_position = (256 + x - width // 2, 384 + y - height // 2)

    # Paste the rectangle onto the background with alpha blending
    background.paste(rectangle_image, paste_position, rectangle_image)

    # Optionally blur the whole background if needed
    background = background.filter(ImageFilter.GaussianBlur(30))

    # Convert the image to RGB mode
    background = background.convert('RGB')

    # Save the result in static/archived-images
    mask_path = f'static/archived-images/mask_{x}_{y}_{size}_{feather}_{aspect}.jpg'
    background.save(mask_path)

    # Save a copy of the mask to static/masks with the same name
    shutil.copy(mask_path, 'static/masks/' + os.path.basename(mask_path))

    # List and sort masks by date (latest first)
    masks = glob.glob('static/archived-images/mask*.jpg')
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)

    return render_template('mk_mask.html', mask_path=mask_path, mask_data=mask_data)

@app.route('/select_text')
def select_text():
    # Get list of txt files from static/TEXT directory
    txt_files = []
    txt_path = os.path.join('static', 'TEXT')
    
    # Create directory if it doesn't exist
    if not os.path.exists(txt_path):
        os.makedirs(txt_path)
        
    # Get all .txt files
    for file in os.listdir(txt_path):
        # Check if file is a .txt or .html file
        if file.endswith('.txt') or file.endswith('.html'):
            txt_files.append(file)
    logit(txt_files)        
    return render_template('select_text.html', txt_files=txt_files)

@app.route('/read_text/<filename>')
def read_text(filename):
    try:
        file_path = os.path.join('static', 'TEXT', filename)
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('read_text.html', content=content, filename=filename)
    except:
        return "Error reading file"

# ----------- 
@app.route('/delete_app_images', methods=['GET', 'POST'])
@login_required
def delete_app_images():
    image_dirs = {
        'archived-store': 'static/archived-store',
        'temp_images': 'static/temp_images',
        'masks': 'static/masks',
        'archived-masks': 'static/archived-masks',
        'archived-images': 'static/archived-images',
        'vid_resources': 'static/vid_resources'
    }
    
    selected_dir = None
    images = []
    
    if request.method == 'POST':
        if 'directory' in request.form:
            selected_dir = request.form['directory']
            # Get images from selected directory
            if selected_dir in image_dirs:
                path = image_dirs[selected_dir]
                images = [f for f in os.listdir(path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        
        if 'delete_images' in request.form:
            selected_dir = request.form['current_dir']
            images_to_delete = request.form.getlist('selected_images')
            for image in images_to_delete:
                try:
                    os.remove(os.path.join(image_dirs[selected_dir], image))
                except OSError as e:
                    print(f"Error deleting {image}: {e}")
            
            # Refresh image list after deletion
            if selected_dir in image_dirs:
                path = image_dirs[selected_dir]
                images = [f for f in os.listdir(path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    
    return render_template('delete_app_images.html', 
                         image_dirs=image_dirs, 
                         selected_dir=selected_dir, 
                         images=images)
DEFAULT_FONT_PATH = "static/fonts/DejaVuSans-Bold.ttf"
FONT_SIZE = 24
PADDING = 10
NOVEL_DIRECTORY = 'static/archived-store'

@app.route('/add_novel_caption')
@login_required
def add_novel_caption():
    logged_in_user = session.get('user')
    
    # Get the list of images in the NOVEL_DIRECTORY
    images = [img for img in os.listdir(NOVEL_DIRECTORY) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # Generate the default path for captioned image
    dest = os.path.join(NOVEL_DIRECTORY, 'captioned.jpg')
    return render_template('add_novel_caption.html', images=images, captioned_image=dest)

@app.route('/add_caption', methods=['POST'])
def add_caption():
    # Get form data
    selected_image = request.form.get('selected_image')
    caption_text = request.form.get('caption', '')
    offset = int(request.form.get('offset', 35))
    alpha = int(request.form.get('alpha', 155))
    
    if not selected_image:
        flash("No image selected.", "danger")
        return redirect(url_for('add_novel_caption'))
    
    # Sanitize caption text for filenames
    safe_caption_text = re.sub(r'[^a-zA-Z0-9_-]', '', caption_text.replace(' ', '_'))
    
    # Generate paths
    image_path = os.path.join(NOVEL_DIRECTORY, selected_image)
    output_path = os.path.join(NOVEL_DIRECTORY, 'captioned.jpg')
    
    try:
        # Open and process the image
        image = Image.open(image_path).convert("RGBA")
        
        # Create overlay for caption
        text_image = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_image)
        font = ImageFont.truetype(DEFAULT_FONT_PATH, FONT_SIZE)
        
        # Split caption into lines
        lines = caption_text.splitlines()
        max_text_width = max(draw.textlength(line, font=font) for line in lines)
        line_height = FONT_SIZE + PADDING // 2
        total_text_height = line_height * len(lines)
        
        # Calculate caption box dimensions
        background_width = max_text_width + 2 * PADDING
        background_height = total_text_height + 2 * PADDING
        background_x = (image.width - background_width) // 2
        background_y = image.height - background_height - offset
        
        # Draw background rectangle
        draw.rectangle(
            [background_x, background_y, background_x + background_width, background_y + background_height],
            fill=(255, 255, 255, alpha)
        )
        
        # Draw text lines
        y_offset = background_y + PADDING
        for line in lines:
            text_width = draw.textlength(line, font=font)
            text_x = background_x + (background_width - text_width) // 2
            draw.text((text_x, y_offset), line, font=font, fill=(0, 0, 0, 255))
            y_offset += line_height
        
        # Merge overlay with image and save
        combined_image = Image.alpha_composite(image, text_image)
        combined_image.convert("RGB").save(output_path, "JPEG")
        
        # Save captioned image with unique filenames
        unique_filename = os.path.join(NOVEL_DIRECTORY, f"{uuid.uuid4()}.jpg")
        shutil.copy(output_path, unique_filename)
        cpto = os.path.join('static/vid_resources', f'{uuid.uuid4()}.jpg')
        # Copy the file
        shutil.copy(output_path, cpto)

    except Exception as e:
        flash(f"Error processing image: {e}", "danger")
        return redirect(url_for('add_novel_caption'))
    
    # Refresh the image list and return the updated template
    images = [img for img in os.listdir(NOVEL_DIRECTORY) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return render_template('add_novel_caption.html', image_path=output_path, images=images, captioned_image=output_path)

# Database setup
def init_db():
    try:
        with sqlite3.connect("static/users.db") as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
        print("Database initialized.")
    except sqlite3.Error as e:
        print(f"Database initialization failed: {e}")

# Insert a test user
def create_test_user():
    try:
        with sqlite3.connect("static/users.db") as conn:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (
                "admin_login", 
                generate_password_hash("admin_login_password123", method='pbkdf2:sha256', salt_length=8)
            ))
            print("Test user created.")
    except sqlite3.IntegrityError:
        print("Test user already exists.")

# Login route
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        with sqlite3.connect("static/users.db") as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user and check_password_hash(user[2], password):
                session['user'] = username
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials.", "danger")
    return render_template("login.html")

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    text = "Welcome to the Dashboard, {}!".format(session['user'])
    return render_template('dashboard.html', text=text)
    #return f"Welcome to the Dashboard, {session['user']}!"

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))
#---------- video routes  
# Create frames and keepers directories if they don't exist
if not os.path.exists('static/frames'):
    os.mkdir('static/frames')
if not os.path.exists('static/keepers_resourses'):
    os.mkdir('static/keepers_resourses')

# Function to extract frames from MP4 using OpenCV
def extract_frames(video_path, output_folder):
    cap = cv2.VideoCapture(video_path)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(os.path.join(output_folder, f'frame_{count}.jpg'), frame)
        count += 1
    cap.release()  

def limit_backups(source_dir='static/archived_images',max_files = 45):
    backup_dir = 'static/backups_resources'
    
    
    # Ensure backup directory exists
    os.makedirs(backup_dir, exist_ok=True)
    
    # Get all files in the source directory, sorted by modification time (oldest first)
    files = sorted(
        [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))],
        key=lambda f: os.path.getmtime(os.path.join(source_dir, f))
    )
    
    # If there are more than the max allowed, move the oldest files to the backup directory
    if len(files) > max_files:
        files_to_backup = files[:-max_files]  # Select all but the last 15 files
        
        for file in files_to_backup:
            file_path = os.path.join(source_dir, file)
            # Create a unique backup filename with a timestamp, preserving the extension
            file_extension = os.path.splitext(file)[1]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{os.path.splitext(file)[0]}_{timestamp}{file_extension}"
            backup_file_path = os.path.join(backup_dir, backup_filename)
            
            # Move the file to the backup directory
            shutil.move(file_path, backup_file_path)
            print(f"Moved {file} to {backup_file_path}")

#delete images in 'static/keepers_resourses/
def keepers_resourses():
    for file in os.listdir('static/keepers_resourses'):
        file_path = os.path.join('static/keepers_resourses', file)
        if os.path.isfile(file_path):
            os.remove(file_path)

# Function to delete all files in 'static/frames/'
def delete_frames():
    frames_dir = 'static/frames'
    for file in os.listdir(frames_dir):
        file_path = os.path.join(frames_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
           
# Route to display video selection and form submission
@app.route('/get_frames', methods=['GET', 'POST'])
@login_required
def get_frames():
    delete_frames()
    video_dir = 'static/video_resources'
    keepers_resourses()
    # Use glob to find all .mp4 files in the directory
    video_files = glob.glob(os.path.join(video_dir, '*.mp4'))
    # sort the files by modification time
    video_files = sorted(video_files, key=os.path.getmtime, reverse=True)    
    # Get only the filenames (basename)
    video_files = [os.path.basename(video) for video in video_files]  
    video_images= glob.glob('static/keepers_resourses/*.jpg')  
    video_images = sorted(video_images, key=os.path.getmtime, reverse=True)                                                          # post the images in reverse order      
    return render_template('copy_frames.html', video_files=video_files, video_images=video_images)

# Route to handle form submission and extract frames from the selected video
@app.route('/process_frames', methods=['POST'])
def process_video():
    # Get selected video from form in copy_frames.html
    video_filename = request.form.get('video')
    # This is the location of the archive videos 
    video_dir = 'static/video_resources'
    video_path = os.path.join(video_dir, video_filename)
    output_folder = 'static/frames'

    # Clear frames folder before extracting new frames
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Extract frames from the selected video
    extract_frames(video_path, output_folder)

    # List all frames in the frames directory
    frames = os.listdir(output_folder)
    return render_template('copy_frames.html', frames=frames)

# Route to handle form submission for image deletion
@app.route('/add_frames', methods=['POST', 'GET'])
def add_frames_route():
    selected_images = request.form.getlist('image')
    for image in selected_images:
        id_ = str(uuid.uuid4())
        source = os.path.join('static/frames', image)
        destination1 = os.path.join('static/keepers_resourses', id_ + image)
        shutil.copy(source, destination1)
        destination2 = os.path.join('static/archived-images', id_ + image)
        shutil.copy(source, destination2)
        destination3 = os.path.join('static/archived-images', id_ + image)
        shutil.copy(source, destination3)
        destination4 = os.path.join('static/archived-images', id_ + image)
        shutil.copy(source, destination4)
    limit_backups(source_dir='static/archived-images',max_files=60)
    limit_backups(source_dir = 'static/archived-images')            
    return redirect(url_for('get_frames'))

#---------- video routes

@app.route('/video_menu')
def video_menu():
    #image_paths = stored_image_paths()
    return render_template('video_menu.html')

@app.route('/stepopen_doors', methods=['GET', 'POST'])
def stepopen_doors_route():
    subprocess.run(['python', 'stepopen_door_directory.py'], check=True)
    return redirect(url_for('video_menu'))

@app.route('/square_transition', methods=['GET', 'POST'])
def square_transition_route():
    subprocess.run(['python', 'square_transition'], check=True)
    return redirect(url_for('video_menu'))
@app.route('/circular_transition', methods=['GET', 'POST'])
def circular_transition_route():
    subprocess.run(['python', 'stepcircular_transition.py'], check=True)
    return redirect(url_for('video_menu'))    
@app.route('/zoom_each', methods=['GET', 'POST'])
def zoom_each_route():
    subprocess.run(['python', 'stepzoomeach.py'], check=True)
    return redirect(url_for('video_menu'))    

# Define paths
ARCHIVED_STORE_DIR = "static/archived-store"
ARCHIVED_IMAGES_DIR = "static/archived-images"
VIDEO_RESOURCES_DIR = "static/vid_resources"

# Ensure the video resources directory exists
os.makedirs(VIDEO_RESOURCES_DIR, exist_ok=True)

@app.route("/step1", methods=["GET", "POST"])
def step1():
    # Ensure the archived store directory exists and empty it for new images
    #os.makedirs(VIDEO_RESOURCES_DIR, exist_ok=True)
    #shutil.rmtree(VIDEO_RESOURCES_DIR, ignore_errors=True)
    #os.makedirs(VIDEO_RESOURCES_DIR, exist_ok=True)
    # Get all images from the archived-store directory
    images = [f for f in os.listdir(ARCHIVED_STORE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if request.method == "POST":
        # Get selected image filenames from the form
        selected_images = request.form.getlist("selected_images")

        if not selected_images:
            flash("No images were selected. Please choose at least one.")
            return redirect(url_for("step1"))

        # Copy selected images to video_resources directory
        for image in selected_images:
            src_path = os.path.join(ARCHIVED_STORE_DIR, image)
            dest_path = os.path.join(VIDEO_RESOURCES_DIR, image)
            shutil.copy(src_path, dest_path)

        flash(f"Successfully copied {len(selected_images)} images to {VIDEO_RESOURCES_DIR}")
        return redirect(url_for("step2"))

    return render_template("transfer.html", step="Step 1: Select Images from Archived Store", images=images, source_folder="archived-store")


@app.route("/step2", methods=["GET", "POST"])
def step2():
    # Get all images from the archived-images directory
    images = [f for f in os.listdir(ARCHIVED_IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if request.method == "POST":
        # Get selected image filenames from the form
        selected_images = request.form.getlist("selected_images")

        if not selected_images:
            flash("No images were selected. Please choose at least one.")
            return redirect(url_for("step2"))

        # Copy selected images to video_resources directory
        for image in selected_images:
            src_path = os.path.join(ARCHIVED_IMAGES_DIR, image)
            dest_path = os.path.join(VIDEO_RESOURCES_DIR, image)
            shutil.copy(src_path, dest_path)

        flash(f"Successfully copied {len(selected_images)} images to {VIDEO_RESOURCES_DIR}")
        return redirect(url_for("step1"))

    return render_template("transfer2.html", step="Step 2: Select Images from Archived Images", images=images, source_folder="archived-images")

# Route to display terms and conditions
@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

def get_stored_videos():
    videos = []
    for filename in os.listdir('static/bash_vids'):
        #sort by latest date modified
        #filename = sorted(glob.glob(filename), key=os.path.getmtime, reverse=True)
        if filename.lower().endswith('finalx.mp4'):
            videos.append(filename)
    return videos
@app.route('/slow_and_reverse')
def slow_and_reverse():
    #video_filename = request.form.get('video')
    #subprocess.run(['bash', 'static/bash_vids/slow_rev.sh'], check=True)
    videos = get_stored_videos()
    return render_template('slow_and_reverse.html', videos=videos)
def process_and_size_images(source_dir):
    # Step 1: Ensure the originals directory exists
    originals_dir = os.path.join(source_dir, 'originals')
    os.makedirs(originals_dir, exist_ok=True)

    # Step 2: Iterate over images in the source directory
    for filename in os.listdir(source_dir):
        filepath = os.path.join(source_dir, filename)
        if not os.path.isfile(filepath) or not filename.lower().endswith(('png', 'jpg', 'jpeg')):
            continue  # Skip non-image files and files in subdirectories
        
        # Step 3: Move the original to the originals directory (if not already there)
        original_path = os.path.join(originals_dir, filename)
        if not os.path.exists(original_path):
            os.rename(filepath, original_path)
        
        # Step 4: Open the image
        with Image.open(original_path) as img:
            original_width, original_height = img.size

            # Check if the image is already 512x768
            if original_width == 512 and original_height == 768:
                # Save it back as a JPG if necessary
                new_filename = os.path.splitext(filename)[0] + ".jpg"
                new_filepath = os.path.join(source_dir, new_filename)
                img.convert("RGB").save(new_filepath, format='JPEG', quality=95)
                continue

            # Step 5: Create a blurred background
            blurred = img.resize((512, 768)).filter(ImageFilter.GaussianBlur(15))

            # Step 6: Resize the original image while maintaining aspect ratio
            aspect_ratio = original_width / original_height
            if aspect_ratio > (512 / 768):  # Wider than the target aspect
                new_width = 512
                new_height = int(512 / aspect_ratio)
            else:  # Taller than the target aspect
                new_height = 768
                new_width = int(768 * aspect_ratio)
            
            resized_original = img.resize((new_width, new_height), Image.LANCZOS)

            # Step 7: Overlay the resized original onto the blurred background
            offset_x = (512 - new_width) // 2
            offset_y = (768 - new_height) // 2
            blurred.paste(resized_original, (offset_x, offset_y))

            # Step 8: Save the resulting image as a JPG
            new_filename = os.path.splitext(filename)[0] + ".jpg"  # Change extension to .jpg
            new_filepath = os.path.join(source_dir, new_filename)
            blurred.convert("RGB").save(new_filepath, format='JPEG', quality=95)

# Directory to process
source_directory = 'static/vid_resources'
process_and_size_images(source_directory)

# Directory to process
source_directory = 'static/vid_resources'
process_and_size_images(source_directory)
source_directory = 'static/novel_images'
process_and_size_images(source_directory)

@app.route('/stepsquare_transition', methods=['GET', 'POST'])
def stepsquare_transition_route():
    subprocess.run(['python', 'stepsquare_transition'], check=True)
    return redirect(url_for('video_menu'))

@app.route('/stepfadem', methods=['GET', 'POST'])
def stepsfadem_route():
    subprocess.run(['python', 'stepfadem'], check=True)
    return redirect(url_for('video_menu'))


@app.route('/stepblendem')
def stepblendem_route():
    # Define the size for resizing images
    SIZE = (512, 768)
    # Get a list of image files
    DIR = "static/vid_resources/"
    image_files = sorted(glob.glob(DIR + "*.jpg")) + sorted(glob.glob(DIR + "*.png"))
    random.shuffle(image_files)
    #print(f"Number of images: {len(image_files)}")

    # Create a temporary directory to store the resized images
    temp_dir = 'btemp/'
    os.makedirs(temp_dir, exist_ok=True)

    # Load and resize the images
    resized_images = []
    for image_file in image_files:
        img = cv2.imread(image_file)
        img = cv2.resize(img, SIZE)
        resized_images.append(img)

    # Create a video writer
    out_path = 'xxxxoutput.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, 30, SIZE)

    # Keep track of video duration
    video_duration = 0

    # Create the video with fading transitions
    for i in range(len(resized_images)):
        if video_duration >= 58:  # Limit video to 58 seconds
            break

        img1 = resized_images[i]
        img2 = resized_images[(i + 1) % len(resized_images)]  # Wrap around to the first image
        step_size = 5
        for alpha in range(0, 150):  # Gradually change alpha from 0 to 100 for fade effect
            alpha /= 150.0
            blended = cv2.addWeighted(img1, 1 - alpha, img2, alpha, 0)
            out.write(blended)
            video_duration += 1 / 30  # Assuming 30 FPS

    out.release()

    # Prepare an audio clip of the same duration (58 seconds)
    audio_clip = AudioFileClip(get_an_mp3()).subclip(0, 58)

    # Load the video clip
    video_clip = VideoFileClip(out_path)

    # Set the audio of the video clip
    video_clip = video_clip.set_audio(audio_clip)

    # Load the static frame to overlay
    frame_clip = ImageClip("static/assets/blendem_frame.png", duration=video_clip.duration).set_position("center")

    # Composite the frame with the video
    final_clip = CompositeVideoClip([video_clip, frame_clip])

    # Save the final video with the overlay and music
    final_output_path = 'static/temp_exp/blendem_final_outputX.mp4'
    uid = str(uuid.uuid4())
    des = DIR.replace("/", "_")
    mp4_file = f"static/videos/{des}{uid}.mp4"

    final_clip.write_videofile(final_output_path, codec='libx264')
    shutil.copyfile(final_output_path, mp4_file)
    return redirect(url_for('index'))
@app.route('/stepBest_flipbook')
def stepBest_flipbook_route():
    try:
        subprocess.run(['python', 'stepBest_FlipBook'], check=True)
        return redirect(url_for('video_menu'))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500

@app.route('/step_video1')
def step_video1_route():
    try:
        subprocess.run(['python', 'step_video1.py'], check=True)
        return redirect(url_for('video_menu'))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route('/stepSLIDEin')#stepSLIDEin_route
def stepSLIDEin_route():
    try:
        subprocess.run(['/bin/bash', 'stepSLIDEin'], check=True)
        return redirect(url_for('video_menu'))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500

@app.route('/joinallvid')#stepSLIDEin_route
def joinallvid_route():
    try:
        subprocess.run(['python', 'joinallvid'], check=True)
        return redirect(url_for('video_menu'))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500

# App entry point
if __name__ == "__main__":
    init_db()
    create_test_user()
    app.run(debug=True, host="0.0.0.0", port=5700)
