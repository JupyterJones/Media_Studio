#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import base64

# import datetime
import gc
import glob
import inspect
import json
import os
import random
import re

# from uuid import uuid4 # uuid is already imported, uuid4 can be accessed via uuid.uuid4()
import shutil
import signal
import sqlite3
import subprocess
import threading

# from pytrends.request import TrendReq
import time
import traceback
import uuid
import wave

# Custom Logging
import datetime
import io
from io import BytesIO
from random import randint
from uuid import uuid4

# Machine Learning Libraries
# import tensorflow as tf
import numpy as np
import psutil
import requests
from icecream import ic

# Image Processing Libraries
from PIL import (
    Image,
    ImageColor,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageOps,
)

import cv2
import dlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import moviepy.editor as mp
import nltk
import pygame
import spacy

# External Libraries
import yt_dlp

# --------------- stitch ---------------------------
# Flask Imports
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from flask_caching import Cache
from flask_cors import CORS
from gtts import gTTS
from moviepy.editor import *  # Consider importing specific classes/functions

# from moviepy.video.fx import all # This is not used, but kept it as you said no changes
# from skimage.future import graph
# Video and Audio Processing (MoviePy, ffmpeg, gTTS, Pygame)
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    ImageSequenceClip,
    TextClip,
    VideoClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)

# -----------------------------
from moviepy.video.fx import all
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from nltk.corpus import stopwords
from pydantic import BaseModel
from pydub import AudioSegment

# gc.set_debug(gc.DEBUG_LEAK)
from pytrends.request import TrendReq
from skimage import color, future, io, segmentation
from skimage.io import imread, imsave
from werkzeug.utils import secure_filename  # For handling uploaded filenames safely

# import tensorflow_hub as hub
# from tensorflow.python.ops.numpy_ops import np_config
# np_config.enable_numpy_behavior()


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
CORS(app)
# Download NLTK data (run these once if not already done)
# nltk.download("punkt")
# nltk.download("stopwords")

# Load Spacy model
nlp = spacy.load("en_core_web_sm")


# Define the model class using Pydantic BaseModel
class PromptModel(BaseModel):
    text: str
    min_words: int = 40
    max_words: int = 60

    def preprocess_text(self):
        """Tokenizes and filters the text, removing stopwords."""
        stop_words = set(stopwords.words("english"))
        tokens = nltk.word_tokenize(self.text)
        filtered_tokens = [
            word for word in tokens if word.isalnum() and word.lower() not in stop_words
        ]
        return filtered_tokens

    def extract_key_phrases(self):
        """Extracts key phrases using Spacy."""
        doc = nlp(self.text)
        key_phrases = set(chunk.text for chunk in doc.noun_chunks)
        return list(key_phrases)

    def generate_prompt(self):
        """Generates a prompt with a word count between min_words and max_words."""
        phrases = self.extract_key_phrases()
        selected_phrases = random.sample(phrases, min(len(phrases), 5))
        prompt = " ".join(selected_phrases)

        # Ensure prompt has at least min_words
        if len(prompt.split()) < self.min_words:
            additional_phrases = random.sample(phrases, 2)
            prompt += " " + " ".join(additional_phrases)

        # Limit prompt to max_words
        return " ".join(prompt.split()[: self.max_words])


# --------------------


"""
Optional Flask performance profiling (development only).

When enabled, wraps the Flask WSGI app with Werkzeug's ProfilerMiddleware,
using Python's cProfile to measure request execution time, function call
counts, and performance bottlenecks. Profiling output is printed to the
console after each request and restricted to the top slowest calls.

Disabled by default because profiling significantly slows execution and
should never be used in production.
"""
# app.config['PROFILE'] = True
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

# -------------------------------
# CONFIGURATION
# -------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
COMPUTER_IMAGE_DIRECTORY = os.path.join(STATIC_DIR, "computer_images")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
OVERLAY_DIR = os.path.join(STATIC_DIR, "overlays")
RESULT_DIR = os.path.join(STATIC_DIR, "results")
DATA_FILE = os.path.join(BASE_DIR, "overlays.json")
ARCHIVED_MASKS=os.path.join(STATIC_DIR, "archived-masks")
for d in [COMPUTER_IMAGE_DIRECTORY, STATIC_DIR, UPLOAD_DIR, OVERLAY_DIR, RESULT_DIR, ARCHIVED_MASKS]:
    os.makedirs(d, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)
app.config["COMPUTER_IMAGE_DIRECTORY"] = COMPUTER_IMAGE_DIRECTORY
UPLOAD_FOLDER = "static/novel_images"
app.config["UPLOAD_FOLDER"] = "static/novel_images"
MASK_FOLDER = "static/masks"
app.config["MASK_FOLDER"] = "static/archived-masks"
NOVEL_IMAGES = "static/novel_images"
app.config["NOVEL_IMAGES"] = "static/novel_images"
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # Limit upload size to 16MB
ARCHIVED_IMAGES_FOLDER = "static/archived-images"
app.config["ARCHIVED_IMAGES_FOLDER"] = "static/archived-images"
DOWNLOAD_FOLDER = "static/downloads"
app.config["DOWNLOAD_FOLDER"] = "static/downloads"
UPLOADFOLDER = "static/novel_images"
app.config["UPLOADFOLDER"] = "static/novel_images"
ARCHIVED_RESOURCES = "static/archived_resources"
app.config["ARCHIVED_RESOURCES"] = "static/archived_resources"
RESOURCE_IMAGES = "static/resource_images"
app.config["RESOURCE_IMAGES"] = "static/resource_images"
# Ensure the directories exist
app.config["NOVEL_IMAGES"] = "static/novel_images"
text_directory = "static/TEXT"
os.makedirs(text_directory, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(ARCHIVED_IMAGES_FOLDER, exist_ok=True)
os.makedirs(ARCHIVED_RESOURCES, exist_ok=True)
os.makedirs(RESOURCE_IMAGES, exist_ok=True)
os.makedirs(UPLOADFOLDER, exist_ok=True)
os.makedirs(MASK_FOLDER, exist_ok=True)
os.makedirs(NOVEL_IMAGES, exist_ok=True)

def move_novel_image_to_resource_images(image_path):
    """
    Safely moves an image file (e.g. from static/novel_images) to static/resource_images.
    If a collision occurs, appends a timestamp to preserve data without overwriting.
    Returns the destination filepath or None.
    """
    if not image_path or not os.path.exists(image_path):
        return None
    dest_dir = "static/resource_images"
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(image_path)
    dest_path = os.path.join(dest_dir, filename)
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(filename)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
        dest_path = os.path.join(dest_dir, f"{name}_{timestamp}{ext}")
    shutil.move(image_path, dest_path)
    print(f"Moved novel image to static/resource_images: {image_path} -> {dest_path}")
    return dest_path


ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "mp4",
    "mkv",
    "avi",
}
# --------------------
# Flask configuration for file uploads
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_AUDIO"] = {"mp3"}
app.config["ALLOWED_AUDIO_EXTENSIONS"] = {"mp3", "jpg", "jpeg", "png"}
app.config["ALLOWED_IMAGE"] = {"jpg", "jpeg", "png", "mp3"}
mp3_dir = "static/mp3"

def allowed_file(filename, ALLOWED_EXTENSIONS):
    """Check if the uploaded file is allowed."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_AUDIO_EXTENSIONS"]
    )


# Configurations
app.config["TEMP_FOLDER"] = "static/temp/"
app.config["FONT_FOLDER"] = "static/fonts/"
app.config["NOVEL_IMAGES"] = "static/novel_images/"
TEMPLATE_DIR = "templates"
app.config["TEMPLATE_DIR"] = "templates"
os.makedirs(app.config["TEMP_FOLDER"], exist_ok=True)
currentDir = os.getcwd()

"""
# Configuring SimpleCache with a limit on cache size

This module configures caching and request size limits for the Flask application.
The caching system is designed to improve performance by temporarily storing
the results of expensive computations in memory, reducing redundant processing
and external API calls.

The application uses Flask-Caching with the SimpleCache backend, which stores
cached data directly in the Python process memory. This approach provides very
fast access to cached values but is limited to a single process. Cached data is
not shared across multiple workers and is cleared when the application restarts.
As a result, this cache backend is best suited for development environments or
single-process deployments where persistence and inter-process synchronization
are not required.

A default cache timeout of five minutes is applied to all cached entries unless
explicitly overridden. After this timeout expires, cached values are automatically
invalidated and removed, ensuring that stale data is not served indefinitely and
that memory usage remains controlled. When a cached value expires, it is recomputed
on the next request and stored again for subsequent use.

To prevent unbounded memory growth, the cache is limited to a maximum of one hundred
entries. When this threshold is reached, older cached items are evicted to make room
for newer ones. This eviction policy protects the application from excessive RAM
consumption, particularly in scenarios where cache keys are generated dynamically
or depend on user-specific parameters.

In addition to caching, the module enforces a maximum request body size of twenty
megabytes. Any incoming request that exceeds this limit is automatically rejected
by Flask before reaching application logic, returning a 413 Request Entity Too
Large response. This safeguard helps protect the application from accidental large
uploads, malformed requests, and memory exhaustion attacks.

The Cache object is initialized with the Flask application instance, which activates
caching using the configured settings. Once initialized, the cache can be used
throughout the application to cache route responses, function results, and other
temporary data needed during request processing.
"""
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # 5 minutes cache timeout
app.config["CACHE_THRESHOLD"] = 100  # Max 100 items in cache
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB limit

cache = Cache(app)

# Define the log file path
LOG_FILE_PATH = "static/app_log.txt"

# Ensure the log file exists or create it
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, "w"):
        pass  # Create an empty log file if it doesn't exist


def logit(*args):
    """
    Lightweight file-based logging utility for debugging and runtime diagnostics.
    Accepts ANY number of positional arguments and safely joins them into a
    single log message.

    Examples:
        logit("Hello world")
        logit("x:", x, "y:", y)
        logit("Paths:", image_paths)
        logit(["list", "of", "values"])
    """

    try:
        # --- timestamp ---
        timestr = datetime.datetime.now().strftime("%A_%b-%d-%Y_%H-%M-%S")

        # --- caller info ---
        frame = inspect.stack()[1]
        filename = frame.filename
        lineno = frame.lineno

        # --- normalize all inputs ---
        parts = []
        for arg in args:
            if isinstance(arg, (list, tuple, set)):
                parts.append(" ".join(map(str, arg)))
            else:
                parts.append(str(arg))

        message_str = " ".join(parts)

        # --- final log line ---
        log_message = f"{timestr} - File: {filename}, Line: {lineno}: {message_str}\n"

        # --- write log ---
        with open(LOG_FILE_PATH, "a") as f:
            f.write(log_message)

        # Optional console echo (leave commented if you want quiet logs)
        # print(log_message, end="")

    except Exception as e:
        print(f"[LOGIT ERROR] {e}")


@app.route("/readlog")
def readlog():
    """
    This route declaration is used to open the logfile LOG_FILE_PATH = 'static/app_log.txt'
    created by logit function
    """
    logdatas = open(LOG_FILE_PATH, "r").read().split("\n")
    logit(logdatas)
    return render_template("read_log.html", log_content=logdatas)


def readlog():
    """
    This function is used to open the logfile LOG_FILE_PATH = 'static/app_log.txt'
    created by logit function and return the data.
    """
    log_file_path = "static/app_log.txt"
    with open(log_file_path, "r") as Input:
        logdata = Input.read()
    # print last entry
    logdata = logdata.split("\n")
    return logdata


@app.route("/delete_log")
def delete_log():
    """
    This route declaration is used to delete the logfile LOG_FILE_PATH = 'static/app_log.txt'
    created by logit function
    """
    open(LOG_FILE_PATH, "w").close()
    logit("Log file deleted successfully")
    return redirect("/view_log")


# Logging function
@app.route("/view_log", methods=["GET", "POST"])
def view_log():
    """
    This route declaration is used to view the logfile LOG_FILE_PATH = 'static/app_log.txt'
    created by logit function
    """
    data = readlog()
    return render_template("view_log.html", data=data)


@app.route("/")
# @cache.cached(timeout=60)
def index():
    session["visited_index"] = True
    image_paths = stored_image_paths()
    post = get_intro(limit=1)
    decoded_post = []
    for row in post:
        # Replace newlines in the content (third field) with <br>
        id, title, content, image, video_filename = row
        if content:
            content = content.replace("\r\n", "<br>").replace(
                "\n", "<br>"
            )  # handle both \r\n and \n
            decoded_post.append((id, title, content, image, video_filename))
    return render_template("index.html", post=decoded_post)


@app.before_request
def ensure_index_page():
    # Check if the session is new (i.e., user hasn't visited the index page)
    if "visited_index" not in session:
        # If the requested URL is not the index or static files, redirect to the index page
        if (
            request.endpoint != "index"
            and not request.path.startswith("/static")
            and not request.path.startswith("/api")
            and not request.path.startswith("/batch_status")
            and not request.path.startswith("/effects")
            and not request.path.startswith("/remember")
            and not request.path.startswith("/zoompan")
            and not request.path.startswith("/zoom_pan")
        ):
            return redirect(url_for("index"))


@app.route("/effects_studio")
@app.route("/effects_studio/")
def effects_studio_route():
    return redirect("/effects")


"""
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/favicon.ico")
def favicon():
    # Set the size of the favicon
    size = (16, 16)

    # Create a new image with a transparent background
    favicon = Image.new("RGBA", size, (0, 0, 0, 0))

    # Create a drawing object
    draw = ImageDraw.Draw(favicon)

    # Draw a yellow square
    square_color = (255, 0, 255)
    draw.rectangle([(0, 0), size], fill=square_color)
    circle_color = (255, 0, 0)
    # Draw a red circle
    circle_center = (size[0] // 2, size[1] // 2)
    circle_radius = size[0] // 3
    draw.ellipse(
        [
            (circle_center[0] - circle_radius, circle_center[1] - circle_radius),
            (circle_center[0] + circle_radius, circle_center[1] + circle_radius),
        ],
        fill=circle_color,
    )

    # Save the image to a memory buffer
    image_buffer = BytesIO()
    favicon.save(image_buffer, format="ICO")
    image_buffer.seek(0)

    return Response(image_buffer.getvalue(), content_type="image/x-icon")
"""


@app.route("/favicon.ico")
def favicon():
    size = (32, 32)
    favicon_img = Image.new("RGBA", size, (0, 0, 0, 0))  # transparent background
    draw = ImageDraw.Draw(favicon_img)

    # Draw yellow circle
    draw.ellipse([(0, 0), size], fill=(255, 255, 0))

    # Load a TTF font
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    font_size = 24
    font = ImageFont.truetype(font_path, font_size)

    # Draw red 'F' in center using textbbox
    text = "F"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_pos = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(text_pos, text, font=font, fill=(255, 0, 0))

    # Save to BytesIO as ICO
    buf = BytesIO()
    favicon_img.save(buf, format="ICO")
    buf.seek(0)

    return Response(buf.getvalue(), content_type="image/x-icon")


# @app.route('/convert', methods=['POST'])
def convert_images():
    # Directory containing the JPG images
    # Check if directory exists
    if not os.path.isdir(app.config["NOVEL_IMAGES"]):
        return redirect(url_for("index"))

    # Loop through all files in the directory
    image_directory = app.config["NOVEL_IMAGES"]
    for filename in os.listdir(image_directory):
        if filename.lower().endswith(".jpg"):
            # Construct full file paths
            jpg_path = os.path.join(image_directory, filename)
            png_filename = os.path.splitext(filename)[0] + ".png"
            png_path = os.path.join(image_directory, png_filename)

            try:
                # Open the JPG image and convert it to PNG
                with Image.open(jpg_path) as img:
                    img = img.convert(
                        "RGBA"
                    )  # Ensure image has alpha channel if needed
                    img.save(png_path, format="PNG")

                # Remove the original JPG file
                os.remove(jpg_path)

            except Exception as e:
                print(f"Failed to convert {jpg_path}. Error: {e}")
    return redirect(url_for("index"))


@app.route("/mk_mask")
def mk_mask():
    masks = glob.glob("static/archived-images/mask*.jpg")
    # list by date, last image first
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)
    return render_template("mk_mask.html", mask_data=mask_data)


@app.route("/create_circle_mask", methods=["POST"])
def create_circle_mask():
    # Get input values from the form
    x = int(request.form.get("x", 0))
    y = int(request.form.get("y", 0))
    size = int(request.form.get("size", 50)) + 20
    feather = int(request.form.get("feather", 20))
    aspect = int(request.form.get("aspect", 0))

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
    background = Image.new("RGBA", (512, 768), (0, 0, 0, 255))

    # Create a white ellipse (or circle if width == height)
    ellipse = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ellipse)
    draw.ellipse((0, 0, width, height), fill=(255, 255, 255, 255))

    # Apply feathering (blur the edges)
    ellipse = ellipse.filter(ImageFilter.GaussianBlur(feather))

    # Calculate position to paste the ellipse (centered by default)
    paste_position = (256 + x - width // 2, 384 + y - height // 2)
    background.paste(ellipse, paste_position, ellipse)
    background = background.convert("RGB")

    # Optionally blur the whole background
    background = background.filter(ImageFilter.GaussianBlur(30))

    # Save the result in static/archived-images
    mask_path = f"static/archived-images/mask_{x}_{y}_{size}_{feather}_{aspect}.jpg"
    background.save(mask_path)
    # save copies to static/masks, static/archived-masks, and static/novel_images
    shutil.copy(mask_path, "static/masks/" + os.path.basename(mask_path))
    shutil.copy(mask_path, "static/archived-masks/" + os.path.basename(mask_path))
    shutil.copy(mask_path, "static/novel_images/" + os.path.basename(mask_path))

    # List and sort masks by date (latest first)
    masks = glob.glob("static/archived-images/mask*.jpg")
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)

    return render_template("mk_mask.html", mask_path=mask_path, mask_data=mask_data)


@app.route("/create_rectangle_mask", methods=["POST"])
def create_rectangle_mask():
    # Get input values from the form
    x = int(request.form.get("x", 0))
    y = int(request.form.get("y", 0))
    size = int(request.form.get("size", 50)) + 20
    feather = int(request.form.get("feather", 20))
    aspect = int(request.form.get("aspect", 0))

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
    background = Image.new("RGBA", (512, 768), (0, 0, 0, 255))

    # Create a rectangle image with a transparent background (RGBA)
    rectangle_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

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
    background = background.convert("RGB")

    # Save the result in static/archived-images
    mask_path = f"static/archived-images/mask_{x}_{y}_{size}_{feather}_{aspect}.jpg"
    background.save(mask_path)

    # Save copies of the mask to static/masks, static/archived-masks, and static/novel_images
    shutil.copy(mask_path, "static/masks/" + os.path.basename(mask_path))
    shutil.copy(mask_path, "static/archived-masks/" + os.path.basename(mask_path))
    shutil.copy(mask_path, "static/novel_images/" + os.path.basename(mask_path))

    # List and sort masks by date (latest first)
    masks = glob.glob("static/archived-images/mask*.jpg")
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)

    return render_template("mk_mask.html", mask_path=mask_path, mask_data=mask_data)

    # return send_file(mask_path, as_attachment=True)


def save_text_to_file(filename, text):
    try:
        with open(os.path.join(TEXT_FILES_DIR, filename), "w") as file:
            file.write(text)
    except Exception as e:
        print(f"An error occurred while saving file '{filename}': {e}")


# Route for the form
@app.route("/add_text", methods=["GET", "POST"])
def add_text():
    # Get the list of images in the NOVEL_IMAGES
    images = os.listdir(app.config["NOVEL_IMAGES"])
    images = [img for img in images if img.lower().endswith((".png", ".jpg", ".jpeg"))]

    if request.method == "POST":
        image_file = request.form["image_file"]
        text = request.form["text"]
        position = (int(request.form["x_position"]), int(request.form["y_position"]))
        font_size = int(request.form["font_size"])
        color = request.form["color"]
        font_path = os.path.join(app.config["FONT_FOLDER"], "xkcd-script.ttf")
        font = ImageFont.truetype(font_path, font_size)

        # Open the image
        image_path = os.path.join(app.config["NOVEL_IMAGES"], image_file)
        image = Image.open(image_path)

        # Draw the text on the image
        draw = ImageDraw.Draw(image)
        draw.text(position, text, font=font, fill=color)

        # Save the temporary image for preview
        temp_image_path = os.path.join(app.config["NOVEL_IMAGES"], "temp-image.png")
        image.save(temp_image_path)

        return render_template(
            "add_text.html",
            images=images,
            selected_image=image_file,
            temp_image="temp-image.png",
            text=text,
            position=position,
            font_size=font_size,
            color=color,
        )

    return render_template("add_text.html", images=images)


# Route to save the final image
@app.route("/save_image", methods=["POST"])
def save_image():
    image_file = request.form["image_file"]
    final_text = request.form["final_text"]
    position = eval(request.form["final_position"])  # Convert string back to tuple
    font_size = int(request.form["final_font_size"])
    color = request.form["final_color"]
    font_path = os.path.join(app.config["FONT_FOLDER"], "xkcd-script.ttf")
    font = ImageFont.truetype(font_path, font_size)

    # Open the image again
    image_path = os.path.join(app.config["NOVEL_IMAGES"], image_file)
    image = Image.open(image_path)

    # Draw the final text on the image
    draw = ImageDraw.Draw(image)
    draw.text(position, final_text, font=font, fill=color)

    # Save the image with a unique UUID
    unique_filename = f"{uuid.uuid4()}.png"
    final_image_path = os.path.join(app.config["NOVEL_IMAGES"], unique_filename)
    image.save(final_image_path)
    # logit(f"line481 final_image_path: {final_image_path}")

    return redirect(url_for("add_text"))


def stored_image_paths():
    image_paths = []
    for ext in ["png", "jpg", "jpeg"]:
        image_paths.extend(
            glob.glob(os.path.join(app.config["NOVEL_IMAGES"], f"*.{ext}"))
        )
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    return image_paths


@app.route("/mk_videos")
def mk_videos():
    image_paths = stored_image_paths()
    return render_template("mk_videos.html", image_paths=image_paths)


@app.route("/img_processing")
def img_processing_route():
    image_paths = stored_image_paths()
    # sorted by date, last image first
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    return render_template("img_processing.html", image_paths=image_paths)


def load_images(image_directory):
    image_paths = []
    for ext in ["png", "jpg", "jpeg"]:
        image_paths.extend(glob.glob(os.path.join(image_directory, f"*.{ext}")))
    random.shuffle(image_paths)
    # image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    return image_paths[:3]


def load_image(image_directory):
    image_paths_ = []
    for ext in ["png", "jpg", "jpeg"]:
        image_paths_.extend(glob.glob(os.path.join(image_directory, f"*.{ext}")))
    # random.shuffle(image_paths)
    image_paths_ = sorted(image_paths_, key=os.path.getmtime, reverse=True)
    return image_paths_[:3]


def convert_to_grayscale(image_path):
    os.makedirs(app.config["MASK_FOLDER"], exist_ok=True)
    os.makedirs(app.config["NOVEL_IMAGES"], exist_ok=True)
    os.makedirs("static/archived-images", exist_ok=True)

    image = Image.open(image_path).convert("L")
    mask_path = os.path.join(app.config["MASK_FOLDER"], "greyscale_mask.png")
    image.save(mask_path)

    # Timestamped archive copy in static/archived-masks/
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ts_mask_path = os.path.join(app.config["MASK_FOLDER"], f"greyscale_mask_{timestamp}.png")
    image.save(ts_mask_path)

    # Copy to novel_images (both fixed name and timestamped)
    shutil.copy(mask_path, os.path.join(app.config["NOVEL_IMAGES"], "greyscale_mask.png"))
    shutil.copy(ts_mask_path, os.path.join(app.config["NOVEL_IMAGES"], f"greyscale_mask_{timestamp}.png"))
    shutil.copy(mask_path, "static/archived-images")

    return mask_path


def convert_to_binary(image_path):
    os.makedirs(app.config["MASK_FOLDER"], exist_ok=True)
    os.makedirs(app.config["NOVEL_IMAGES"], exist_ok=True)
    os.makedirs("static/archived-images", exist_ok=True)

    # Convert image to grayscale
    image = Image.open(image_path).convert("L")

    # Calculate the mean pixel value to use as the threshold
    np_image = np.array(image)
    threshold = float(np.mean(np_image))

    # Convert image to binary based on the mean threshold
    binary_image = image.point(lambda p: 255 if p > threshold else 0)

    # Save the binary mask to static/archived-masks/
    mask_path = os.path.join(app.config["MASK_FOLDER"], "binary_mask.png")
    binary_image.save(mask_path)

    # Invert the binary mask
    inverted_image = binary_image.point(lambda p: 255 - p)

    # Save the inverted binary mask to static/archived-masks/
    inverted_mask_path = os.path.join(
        app.config["MASK_FOLDER"], "inverted_binary_mask.png"
    )
    inverted_image.save(inverted_mask_path)

    # Timestamped archive copies in static/archived-masks/
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ts_mask_path = os.path.join(app.config["MASK_FOLDER"], f"binary_mask_{timestamp}.png")
    ts_inv_path = os.path.join(app.config["MASK_FOLDER"], f"inverted_binary_mask_{timestamp}.png")
    binary_image.save(ts_mask_path)
    inverted_image.save(ts_inv_path)

    # Copy binary mask AND inverted binary mask to static/novel_images/
    shutil.copy(mask_path, os.path.join(app.config["NOVEL_IMAGES"], "binary_mask.png"))
    shutil.copy(inverted_mask_path, os.path.join(app.config["NOVEL_IMAGES"], "inverted_binary_mask.png"))
    shutil.copy(ts_mask_path, os.path.join(app.config["NOVEL_IMAGES"], f"binary_mask_{timestamp}.png"))
    shutil.copy(ts_inv_path, os.path.join(app.config["NOVEL_IMAGES"], f"inverted_binary_mask_{timestamp}.png"))

    # Also copy to static/archived-images
    shutil.copy(mask_path, "static/archived-images")
    shutil.copy(inverted_mask_path, "static/archived-images")

    return mask_path


def resize_images_to_base(base_image, images):
    base_size = base_image.size
    resized_images = [base_image]
    for img in images[1:]:
        resized_images.append(img.resize(base_size, resample=Image.Resampling.LANCZOS))
    return resized_images


@app.route("/get_images", methods=["POST", "GET"])
def get_images():
    image_directory = app.config["UPLOAD_FOLDER"]
    image_paths = load_images(image_directory)
    # shuffle the images
    random.shuffle(image_paths)
    image_paths_ = load_image(image_directory)
    random.shuffle(image_paths_)
    return render_template(
        "display_images_exp.html",
        image_paths=image_paths,
        mask_path=None,
        opacity=0.5,
        image_paths_=image_paths_,
    )


@app.route("/play_narration", methods=["GET", "POST"])
def play_narration():
    music = "static/audio/narration.mp3"
    return render_template("play_mp3.html", music=music)


@app.route("/edit_mask", methods=["POST"])
def edit_mask():
    image_paths = request.form.getlist("image_paths")
    mask_path = request.form.get("mask_path")
    opacity = float(request.form.get("opacity", 0.5))
    return render_template(
        "display_images_exp.html",
        image_paths=image_paths,
        mask_path=mask_path,
        opacity=opacity,
    )


@app.route("/store_result", methods=["POST"])
def store_result():
    result_image_path = request.form.get("result_image")
    unique_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    store_path = os.path.join(app.config["NOVEL_IMAGES"], f"result_{unique_id}.png")

    # Correct the path for the result image
    result_image_path = result_image_path.replace("/static/", "static/")

    # Save the result image to the store folder
    image = Image.open(result_image_path)
    image.save(store_path)
    return redirect(url_for("index"))


@app.route("/refresh-images")
def refresh_images():
    try:
        if os.path.exists("refresh_images.py"):
            subprocess.run([sys.executable, "refresh_images.py"], check=True)
        return redirect(url_for("index"))
    except subprocess.CalledProcessError as e:
        return f"An error occurred: {e}"


@app.route("/refresh-video")
def refresh_video():
    try:
        convert_images_route()
        createvideo()
        subprocess.run([sys.executable, "refresh_video.py"], check=True)
        subprocess.run([sys.executable, "Best_FlipBook"], check=True)
        subprocess.run([sys.executable, "diagonal_transition"], check=True)
        subprocess.run([sys.executable, "blendem"], check=True)
        subprocess.run(["/bin/bash", "slide"], check=True)
        subprocess.run(["/bin/bash", "zoomX4"], check=True)
        subprocess.run([sys.executable, "fadem"], check=True)
        subprocess.run(["/bin/bash", "zoomY4"], check=True)
        subprocess.run([sys.executable, "vertical_scroll"], check=True)
        video_path = "static/temp_exp/diagonal1.mp4"
        add_title(video_path, hex_color="#A52A2A")

        join_script = "join_all_videos" if os.path.exists("join_all_videos") else "joinvid"
        subprocess.run([sys.executable, join_script], check=True)

        return redirect(url_for("create_video"))

    except subprocess.CalledProcessError as e:
        return f"An error occurred: {e}"


@app.route("/display_resources", methods=["POST", "GET"])
def display_resources():
    # Logging function for debugging
    logit("display_resources function called")

    # Glob pattern to get image paths in static/archived_resource directory
    image_paths = (
        glob.glob("static/archived_resources/*.jpg")
        + glob.glob("static/archived_resource/*.png")
        + glob.glob("static/archived_resources/*.jpeg")
    )
    logit(f"Image paths found: {image_paths}")

    # Sort images by modification date, newest first
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    logit(f"Sorted image paths: {image_paths}")

    # Render template and pass image paths
    return render_template("display_resources_exp.html", image_paths=image_paths)


@app.route("/copy_images", methods=["GET", "POST"])
def copy_images():
    size_and_format_images_route()
    if request.method == "POST":
        selected_images = request.form.getlist("selected_images")

        # Copy the selected images to the store folder
        for image_path in selected_images:
            logit(f"___Copying image: {image_path}")
            shutil.copy(image_path, "static/novel_resources")
            shutil.copy(image_path, "static/novel_images")

        # Redirect to a page where you can view the stored images
        return redirect(url_for("img_processing_route"))


@app.route("/select_mask_image", methods=["POST", "GET"])
def select_mask_image():
    if request.method == "POST":
        selected_image = request.form.get("selected_image")
        if not selected_image:
            return "Please select an image for masking."
        return render_template("choose_mask.html", selected_image=selected_image)
    image_paths = get_image_paths()
    return render_template("select_mask_image.html", image_paths=image_paths)


@app.route("/choose_mask", methods=["POST"])
def choose_mask():
    selected_image = request.form.get("selected_image")
    mask_type = request.form.get("mask_type")

    if not selected_image:
        return "Please select an image for masking."

    if mask_type == "grayscale":
        mask_path = convert_to_grayscale(selected_image)
    elif mask_type == "binary":
        mask_path = convert_to_binary(selected_image)
    else:
        return "Invalid mask type selected."
    # redirect to select
    return redirect(url_for("select_images"))


# render_template('select_images.html', image_paths=[selected_image], mask_path=mask_path, opacity=0.5)


def extract_random_frames(video_path, num_frames=25):
    try:
        video = VideoFileClip(video_path)
        duration = video.duration
        timestamps = sorted([random.uniform(0, duration) for _ in range(num_frames)])
        saved_images = []

        for i, timestamp in enumerate(timestamps):
            frame = video.get_frame(timestamp)
            img = Image.fromarray(frame)
            image_filename = f"frame_{i + 1}.jpg"
            image_path = os.path.join(
                app.config["ARCHIVED_IMAGES_FOLDER"], image_filename
            )
            img.save(image_path)
            saved_images.append(image_filename)

        return saved_images
    except Exception as e:
        print(f"Error extracting frames: {e}")
        raise


@app.route("/get_video_images", methods=["GET", "POST"])
def get_video_images():
    if request.method == "POST":
        url = request.form["url"]
        if url:
            try:
                # Download the YouTube video
                video_path = download_youtube_video(url)

                # Extract 25 random frames
                images = extract_random_frames(video_path)

                # Redirect to display the images
                return redirect(url_for("display_images"))
            except Exception as e:
                print(f"Error in /get_images: {e}")
                return str(e)

    return render_template("get_images.html")


@app.route("/images")
def display_images():
    try:
        images = os.listdir(app.config["ARCHIVED_IMAGES_FOLDER"])
        images = [
            os.path.join(app.config["ARCHIVED_IMAGES_FOLDER"], img) for img in images
        ]
        return render_template("YouTube_gallery.html", images=images)
    except Exception as e:
        print(f"Error in /images: {e}")
        return str(e)


def download_youtube_video(url):
    try:
        # Set the download options
        ydl_opts = {
            "outtmpl": os.path.join(app.config["DOWNLOAD_FOLDER"], "%(title)s.%(ext)s"),
            "format": "mp4",  # Best format available
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video information and download the video
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get("title")

            # Sanitize and format the filename to remove spaces and special characters
            sanitized_title = secure_filename(video_title)
            sanitized_title = sanitized_title.replace(" ", "_")
            download_path = os.path.join(
                app.config["DOWNLOAD_FOLDER"], f"{sanitized_title}.mp4"
            )
            static_video_path = os.path.join("static", "temp.mp4")

            # Find the downloaded file
            for root, dirs, files in os.walk(app.config["DOWNLOAD_FOLDER"]):
                for file in files:
                    if file.endswith(".mp4"):
                        actual_downloaded_file = os.path.join(root, file)
                        break
                else:
                    continue
                break

            # Check if the video was downloaded correctly
            if os.path.exists(actual_downloaded_file):
                # Move the downloaded video to the static/temp.mp4 path
                shutil.move(actual_downloaded_file, static_video_path)
            else:
                raise FileNotFoundError(f"File not found: {actual_downloaded_file}")

            return static_video_path

    except Exception as e:
        print(f"Error downloading video: {e}")
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
        print(
            "No face detected in the image. Using the entire image with no feathering."
        )
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
    foreground = cv2.imread(
        foreground_path, cv2.IMREAD_UNCHANGED
    )  # Load with alpha channel
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
        raise ValueError(
            f"Foreground and background dimensions do not match: {foreground_rgb.shape[:2]} vs {background_rgba.shape[:2]}"
        )

    # Blend the images
    for i in range(3):  # For each color channel
        background_rgba[:, :, i] = (
            foreground_rgb[:, :, i] * alpha_channel
            + background_rgba[:, :, i] * (1 - alpha_channel)
        ).astype(np.uint8)

    # Save the result
    cv2.imwrite(output_path, background_rgba)

    print(f"Composite image saved to: {output_path}")

    im = Image.open(output_path).convert("RGB")
    im.save(output_path[:-3] + "jpg", quality=95)
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
    cropped_image = resized_image[
        crop_y : crop_y + target_height, crop_x : crop_x + target_width
    ]

    return cropped_image

ALLOWEDEXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
}
def allowedfile(filename):
    ic(f"{filename} : {ALLOWEDEXTENSIONS}")
    logit(f"{filename} : {ALLOWEDEXTENSIONS}")
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWEDEXTENSIONS

@app.route("/face_detect", methods=["POST", "GET"])
def face_detect():
    if request.method == "POST":
        # Check if the file part is in the request
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]

        # Handle case where no file is selected
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        # Validate file and save if allowed
        if file and allowedfile(file.filename):
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            # Create a feathered PNG image from the detected face
            feathered_image_path = create_feathered_image(
                save_path, "static/archived-images/feathered_face.png"
            )
            # Randomly select a background image from the static/archived-images/ folder
            background_image_path = random.choice(glob.glob("static/archived-images/*.jpg"))

            # Overlay the feathered image on the background and generate the composite image
            output_composite_path = overlay_feathered_on_background(
                feathered_image_path,
                background_image_path,
                "static/archived-images/composite_image.png",
            )

            # Generate unique filenames using UUID for feathered and composite images
            feathered_image_uuid = str(uuid.uuid4()) + ".png"
            composite_image_uuid = str(uuid.uuid4()) + ".png"

            # Copy the feathered and composite images to the archived_resources directory
            feathered_image_archive_path = os.path.join(
                "static/archived_resources", feathered_image_uuid
            )
            composite_image_archive_path = os.path.join(
                "static/archived_resources", composite_image_uuid
            )

            shutil.copy(feathered_image_path, feathered_image_archive_path)
            shutil.copy(output_composite_path, composite_image_archive_path)

            # Return the template with paths to the generated images
            return render_template(
                "face_detect.html",
                feathered_image=feathered_image_archive_path,
                composite_image=composite_image_archive_path,
            )

    # Render the face_detect template on GET request or error cases
    return render_template("face_detect.html")


@app.route("/about")  # , methods=['POST', 'GET'])
def about():
    if os.path.exists(os.path.join(app.template_folder, "about.html")):
        return render_template("about.html")
    return render_template("application_overview.html")


def resize_image(image_path):
    # Open the image
    image = Image.open(image_path)
    # Resize the image
    resized_image = image.resize((512, 768), Image.LANCZOS)
    # Save the resized image
    resized_image.save(image_path)
    print(f"Resized image saved at: {image_path}")


@app.route("/resize_all")  # , methods=['POST', 'GET'])
def resize_all():
    # Resize all images in the upload folder
    image_paths = glob.glob(os.path.join(app.config["UPLOAD_FOLDER"], "*.jpg"))
    for image_path in image_paths:
        resize_image(image_path)
    return redirect(url_for("index"))


@app.route("/upload_image", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        image_file = request.files["image"]
        image_file = convert_webp_to_jpg(image_file)
        if image_file:
            filename = image_file.filename
            image_path = os.path.join(
                "static", filename
            )  # Ensure only one 'static/' prefix
            image_file.save(image_path)
            return render_template(
                "confirm_image.html", image_path=filename
            )  # Pass only the filename
    return render_template("upload_image.html")


@app.route("/torn_edge", methods=["POST"])
def create_torn_edge_effect():
    filename = request.form.get("image_path")
    image_path = os.path.join("static", filename)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_filename = f"result_{timestamp}.png"
    output_path = os.path.join("static", "NOVEL_IMAGES", output_filename)
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size

    # Create a mask with the same size as the image
    mask = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(mask)

    # Create a random torn edge effect for all edges
    np.random.seed(0)
    torn_edge_top = np.random.normal(0, 60, width)
    torn_edge_bottom = np.random.normal(0, 60, width)
    torn_edge_left = np.random.normal(0, 60, height)
    torn_edge_right = np.random.normal(0, 60, height)

    torn_edge_top = np.clip(torn_edge_top, -100, 100)
    torn_edge_bottom = np.clip(torn_edge_bottom, -100, 100)
    torn_edge_left = np.clip(torn_edge_left, -100, 100)
    torn_edge_right = np.clip(torn_edge_right, -100, 100)

    # Apply torn edges to the top and bottom
    for x in range(width):
        draw.line((x, 0, x, int(torn_edge_top[x])), fill=0)
        draw.line((x, height, x, height - int(torn_edge_bottom[x])), fill=0)

    # Apply torn edges to the left and right
    for y in range(height):
        draw.line((0, y, int(torn_edge_left[y]), y), fill=0)
        draw.line((width, y, width - int(torn_edge_right[y]), y), fill=0)

    # Apply Gaussian blur to smooth the edges
    mask = mask.filter(ImageFilter.GaussianBlur(2))

    result = Image.composite(
        image, Image.new("RGBA", image.size, (255, 255, 255, 0)), mask
    )
    result.save(output_path, "PNG")
    # copy to upload folder
    shutil.copy(output_path, app.config["UPLOAD_FOLDER"])
    return render_template(
        "torn_edge.html",
        original_image=filename,
        torn_image=os.path.join("NOVEL_IMAGES", output_filename),
    )


SCAN_DATA_FILE = "local_scan_data.json"
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", "webp"]
STATIC_IMAGE_DIR = "static/local_images"
JUNK_IMAGE_DIR = "static/junk_resources"
if not os.path.exists(JUNK_IMAGE_DIR):
    os.makedirs(JUNK_IMAGE_DIR)
STATIC_IMAGE_DIR = "static/local_images"
if not os.path.exists(STATIC_IMAGE_DIR):
    os.makedirs(STATIC_IMAGE_DIR)
STATIC_GALLERY_DATA_FILE = "local_static_gallery_data.json"

app.static_folder = "static"  # Set the static folder to 'static'
app.config["SECRET_KEY"] = "your_secret_key"
app.config["VUPLOAD_FOLDER"] = "static/videos"
app.config["ALLOWED_EXTENSIONS"] = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "mp4",
    "mkv",
    "avi",
}

# app.config['ALLOWED_EXTENSIONS'] = {'mp4'}
# app.config['DATABASE'] = 'static/blog3.db'
app.config["DATABASE"] = "static/blog4.db"
DATABASE = app.config["DATABASE"]
app.config["DATABASEF"] = "static/functions.db"
DATABASEF = app.config["DATABASEF"]

'''
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )
'''

@app.route("/upload_video/<int:post_id>", methods=["POST"])
def upload_video(post_id):
    if "videoFile" not in request.files:
        print("No file part")
        flash("No file part")
        return redirect(request.url)

    file = request.files["videoFile"]
    if file.filename == "":
        flash("No selected file")
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["VUPLOAD_FOLDER"], filename))
        print(f"Filename: {filename}")
        # Update the database with the filename
        update_video_filename(post_id, filename)
        flash("Video uploaded successfully")
        return redirect(url_for("post", post_id=post_id))
    else:
        flash("Allowed file types are .mp4")
        return redirect(request.url)


def update_video_filename(post_id, filename):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE post SET video_filename = ? WHERE id = ?", (filename, post_id)
        )
        conn.commit()


"""
# Initialize SQLite database if not exists
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(''
            CREATE TABLE IF NOT EXISTS post (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                content TEXT NOT NULL,
                video_filename TEXT NULL,
                image BLOB
            )
        '')
        conn.commit()
"""


# Function to fetch a single post by ID
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def post(post_id):
    if request.method == "POST":
        return upload_video(post_id)

    post = get_post(post_id)
    if not post:
        flash("Post not found")
        return redirect(url_for("home"))

    image_data = get_image_data(post_id)
    video_filename = (
        post[4] if post[4] else None
    )  # Adjust index based on your database schema

    return render_template(
        "post.html", post=post, image_data=image_data, video_filename=video_filename
    )


def get_post(post_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, content, image, video_filename FROM post WHERE id = ? ORDER BY id DESC",
            (post_id,),
        )
        post = cursor.fetchone()
    return post


# Function to fetch all posts
def get_posts(limit=None):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        if limit:
            cursor.execute(
                "SELECT id, title, content, image, video_filename FROM post ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        else:
            cursor.execute(
                "SELECT id, title, content, image, video_filename FROM post ORDER BY id DESC"
            )
        posts = cursor.fetchall()
    return posts


def get_intro(limit=1):
    print(f"Fetching post with limit={limit}")
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            if limit:
                print("Fetching post with id = 864")
                cursor.execute(
                    "SELECT id, title, content, image, video_filename FROM post WHERE id = ?",
                    (864,),
                )
            else:
                print("Fetching all posts ordered by id DESC")
                cursor.execute(
                    "SELECT id, title, content, image, video_filename FROM post ORDER BY id DESC"
                )

            posts = cursor.fetchall()

            return posts
        except sqlite3.OperationalError as e:
            print(f"SQLite error occurred: {e}")
            raise


# Function to fetch image data
def get_image(post_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM post WHERE id = ?", (post_id,))
        post = cursor.fetchone()
        if post and post[0]:
            return post[0]  # Return base64 encoded image data
        return None


@app.route("/home2")
def home2():
    posts = get_posts(limit=6)
    for post in posts:
        print(post[3])  # Limit to last 6 posts
    return render_template("home.html", posts=posts)


@app.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        image = (
            request.files["image"].read()
            if "image" in request.files and request.files["image"].filename != ""
            else None
        )
        if image:
            image = base64.b64encode(image).decode("utf-8")
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO post (title, content, image) VALUES (?, ?, ?)",
                (title, content, image),
            )
            conn.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for("home2"))
    return render_template("new_post.html")


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = get_post(post_id)
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        image_data = get_image(post_id)  # Get the current image data
        if "image" in request.files and request.files["image"].filename != "":
            image = request.files["image"].read()
            image_data = base64.b64encode(image).decode(
                "utf-8"
            )  # Update with new image data
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE post SET title = ?, content = ?, image = ? WHERE id = ?",
                (title, content, image_data, post_id),
            )
            conn.commit()
        flash("Post updated successfully!", "success")
        return redirect(url_for("post", post_id=post_id))
    return render_template("edit_post.html", post=post)


@app.route("/contents")
def contents():
    posts = get_posts()
    contents_data = []
    for post in posts:
        excerpt = (
            post[2][:300] + "..." if len(post[2]) > 300 else post[2]
        )  # Assuming content is in the third column (index 2)
        contents_data.append({"id": post[0], "title": post[1], "excerpt": excerpt})
    return render_template("contents.html", contents_data=contents_data)


@app.route("/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM post WHERE id = ?", (post_id,))
        conn.commit()
    flash("Post deleted successfully!", "success")
    return redirect(url_for("home"))


"""
def load_txt_files(directory):
    init_db()  # Initialize the SQLite database if not already created
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                filepath = os.path.join(directory, filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    title = os.path.splitext(filename)[0]
                    content = file.read()
                    cursor.execute('SELECT id FROM post WHERE title = ? ORDER BY id DESC', (title,))
                    existing_post = cursor.fetchone()
                    if not existing_post:
                        cursor.execute('INSERT INTO post (title, content) VALUES (?, ?)', (title, content))
                        conn.commit()
                        logit(f'Added post: {title}')
                    else:
                        logit(f'Skipped existing post: {title}')
    except sqlite3.Error as e:
        print(f'SQLite error: {e}')
    finally:
        conn.close()
"""


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_terms = request.form["search_terms"]
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Define the search terms
        search_terms = search_terms.split(
            ","
        )  # Split by comma to get individual search terms
        results = []

        # Construct the WHERE clause for the SQL query to filter rows based on all search terms
        where_conditions = []
        for term in search_terms:
            where_conditions.append("content LIKE ?")

        where_clause = " AND ".join(where_conditions)

        # Create a tuple of search terms with wildcard characters for the SQL query
        search_terms_tuple = tuple(f"%{term.strip()}%" for term in search_terms)

        # Execute the SELECT query with the constructed WHERE clause
        query = f"SELECT ROWID, title, content, image, video_filename FROM post WHERE {where_clause} ORDER BY ROWID DESC"
        rows = cursor.execute(query, search_terms_tuple)

        for row in rows:
            results.append((row[0], row[1], row[2], row[3], row[4]))

        conn.close()
        return render_template("search.html", results=results)

    return render_template("search.html", results=[])


def get_image_data(post_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM post WHERE id = ?", (post_id,))
        post = cursor.fetchone()
        if post and post[0]:
            return base64.b64decode(post[0])  # Decode base64 to binary
        else:
            return None


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    if request.method == "POST":
        if "videoFile" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["videoFile"]

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["VUPLOAD_FOLDER"], filename))

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE post SET video_filename = ? WHERE id = ?",
                    (filename, post_id),
                )
                conn.commit()
                flash("Video uploaded successfully")

            return redirect(url_for("show_post", post_id=post_id))

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, content, image, video_filename FROM post WHERE id = ? ORDER BY id DESC",
            (post_id,),
        )
        post = cursor.fetchone()
        if not post:
            flash("Post not found")
            return redirect(url_for("home"))

        image_data = base64.b64decode(post[3]) if post[3] else None
        video_filename = post[4] if post[4] else None
    print(f"video_filename: {video_filename}")
    return render_template(
        "post.html", post=post, image_data=image_data, video_filename=video_filename
    )


@app.route("/image/<int:post_id>")
def view_image(post_id):
    image_data = get_image_data(post_id)
    if image_data:
        return send_file(io.BytesIO(image_data), mimetype="image/jpeg")
    else:
        return "No image found", 404


TEXT_FILES_DIR = "static/TEXT"


# Index route to display existing text files and create new ones
@app.route("/edit_text", methods=["GET", "POST"])
def edit_text():
    text_directory = "static/TEXT"

    if request.method == "POST":
        filename = request.form["filename"]
        text = request.form["text"]
        save_text_to_file(filename, text)
        return redirect(url_for("edit_text"))
    else:
        # Path to the file containing list of file paths
        text_files = os.listdir(TEXT_FILES_DIR)
        text_directory = "static/TEXT"
        files = sorted(
            text_files,
            key=lambda x: os.path.getmtime(os.path.join(text_directory, x)),
            reverse=True,
        )
        # files=glob.glob('static/TEXT/*.txt')
        print(f"files 1: {files}")
        # Call the function to list files by creation time
        # files = list_files_by_creation_time(files)
        print(f"files 2: {files}")
        return render_template("edit_text.html", files=files)


# Route to edit a text file
@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    if request.method == "POST":
        text = request.form["text"]
        save_text_to_file(filename, text)
        return redirect(url_for("index"))
    else:
        text = read_text_from_file(filename)
        return render_template("edit.html", filename=filename, text=text)


# Route to delete a text file
@app.route("/delete/<filename>")
def delete(filename):
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"File deleted: {filename}")
    return redirect(url_for("index"))


def list_files_by_creation_time(file_paths):
    """
    List files by their creation time, oldest first.

    Args:
    file_paths (list): List of file paths.

    Returns:
    list: List of file paths sorted by creation time.
    """
    # Log the start of the function
    print("Listing files by creation time...")

    # Create a dictionary to store file paths and their creation times
    file_creation_times = {}

    # Iterate through each file path
    for file_path in file_paths:
        # Get the creation time of the file
        try:
            creation_time = os.path.getctime(file_path)
            # Store the file path and its creation time in the dictionary
            file_creation_times[file_path] = creation_time
        except FileNotFoundError:
            # Log a warning if the file is not found
            print(f"File not found: {file_path}")

    # Sort the dictionary by creation time
    sorted_files = sorted(file_creation_times.items(), key=lambda x: x[1], reverse=True)

    # Extract the file paths from the sorted list
    sorted_file_paths = [file_path for file_path, _ in sorted_files]

    # Log the end of the function
    print("File listing complete.")

    # Return the sorted file paths
    return sorted_file_paths


def read_text_from_file(filename):
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    with open(filepath, "r") as file:
        text = file.read()
        print(f"Text read from file: {filename}")
        return text


@app.route("/generate", methods=["POST"])
def generate_text():
    input_text = request.form["input_text"]
    generated_text = generate_text_with_model(input_text)
    print(f"Generated text: {generated_text}")
    return jsonify({"generated_text": generated_text})


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


def generate_text_with_model(input_text):
    """
    Generate text using a locally running Ollama model (phi:latest).
    """
    ic("Connecting to Ollama...")
    ic(OLLAMA_URL)
    ic(MODEL_NAME)

    payload = {
        "model": MODEL_NAME,
        "prompt": input_text,
        "options": {"temperature": 0.8, "top_p": 0.9, "num_predict": 500},
        "stream": False,
    }

    try:
        ic("Sending request to Ollama...")
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()

        data = response.json()
        ic("Response received")

        # Ollama returns a JSON object; the text is in the 'response' key
        generated_text = data.get("response", "").strip()
        ic(generated_text[:200])  # Show first 200 chars for debugging

        return generated_text

    except requests.exceptions.RequestException as e:
        ic(f"Error communicating with Ollama: {e}")
        return "Error: Unable to connect to Ollama model."
    except json.JSONDecodeError:
        ic("Error decoding JSON response.")
        return "Error: Invalid JSON response from Ollama."


@app.route("/ask", methods=["GET", "POST"])
def ask():
    return html_content


html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ollama phi:latest Text Generation</title>
    <link rel="stylesheet" href="static/dark.css">
    <style>
        textarea {
            width: 100% !important;
            height: 60px !important;
            margin: 10px 0;
            padding: 10px;
            font-size: 16px;
        }
        input[type="submit"] {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #007bff;
            color: white;
            border: none;
            cursor: pointer;
        }
        pre {
            background-color: darkgray;
            padding: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 22px;
        }
        #text {
            background-color: black;
            margin-top: 20px;
            font-size: 24px;
        }
    
        </style>
</head>
<body>
    <h1>GPT-2 Text Generation</h1>
    <!-- Add link home -->
    <a href="/">Home</a>
    <form id="inputForm">
        <label for="input_text">Enter Input Text:</label><br>
        <textarea class="small" id="input_text" name="input_text"></textarea><br>
        <input type="submit" value="Generate Text">
    </form>
    <pre style="color:black;" id="generated_text"></pre>
    <script>
        document.getElementById('inputForm').addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            document.getElementById('generated_text').innerHTML = '<h2>Generated Text:</h2>' + data.generated_text;
        });
    </script>
</body>
</html>
"""


@app.route("/ask_gemini")
def ask_gemini():
    """Heavy-duty cloud AI assistant powered by Google Gemini."""
    return render_template("ask_gemini.html")


@app.route("/api/ask_gemini", methods=["POST"])
def api_ask_gemini():
    """API endpoint for Gemini heavy-duty code, file, and narrative analysis."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "GOOGLE_API_KEY environment variable is not set.",
                }
            ),
            500,
        )

    try:
        from google import genai
        from PIL import Image

        client = genai.Client(api_key=api_key)

        json_data = request.get_json(silent=True) or {}
        payload = (request.form.get("payload") or json_data.get("payload") or "").strip()
        instruction = (request.form.get("instruction") or json_data.get("instruction") or "").strip()
        model_name = (request.form.get("model") or json_data.get("model") or "gemini-2.5-flash").strip()

        contents = []

        # Check for optional image file attachment
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename != "":
                img = Image.open(file.stream)
                contents.append(img)

        # Assemble text parts
        prompt_parts = []
        if instruction:
            prompt_parts.append(f"INSTRUCTIONS / TASK:\n{instruction}\n")
        if payload:
            prompt_parts.append(f"CONTENT / CODE / PAYLOAD:\n{payload}\n")

        if not prompt_parts and not contents:
            return jsonify({"status": "error", "message": "No content provided."}), 400

        contents.append("\n".join(prompt_parts))

        # Call Gemini API
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
        )

        reply_text = (
            response.text if response and response.text else "No response text generated."
        )

        return jsonify({
            "status": "success",
            "response": reply_text,
            "model": model_name,
        })

    except Exception as e:
        logit(f"[GEMINI ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def save_static_gallery_data(data):
    with open(STATIC_GALLERY_DATA_FILE, "w") as f:
        json.dump(data, f)
    print(f"Static gallery data saved to {STATIC_GALLERY_DATA_FILE}")


def load_static_gallery_data():
    # Scan directories if static gallery data file is missing or empty
    if not os.path.exists(STATIC_GALLERY_DATA_FILE):
        print(f"{STATIC_GALLERY_DATA_FILE} not found. Scanning directories.")
        scan_directories()
    else:
        with open(STATIC_GALLERY_DATA_FILE, "r") as f:
            data = json.load(f)
            print(f"Static gallery data loaded from {STATIC_GALLERY_DATA_FILE}")
            return data
    return None


# Define supported image extensions
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", "webp"]


def scan_directories():
    image_dirs = []
    # Define the base directory to search in (static/*resources)
    base_dir = "static"

    # Walk through directories starting from 'static'
    for root, dirs, files in os.walk(base_dir):
        # Check if the directory contains the word 'resources'
        # if 'resources' in root:
        logit(f"Scanning directory: {root}")
        # Filter the files by image extensions
        image_files = [
            f for f in files if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
        ]

        # If the directory contains 20 or more images, add it to the results
        if len(image_files) >= 20:
            image_dirs.append({"path": root, "images": image_files})
            print(f"Found {len(image_files)} images in directory: {root}")

    return image_dirs


def save_scan_data(data):
    with open(SCAN_DATA_FILE, "w") as f:
        json.dump(data, f)
    print(f"Scan data saved to {SCAN_DATA_FILE}")


def load_scan_data():
    if os.path.exists(SCAN_DATA_FILE):
        with open(SCAN_DATA_FILE, "r") as f:
            data = json.load(f)
            print(f"Scan data loaded from {SCAN_DATA_FILE}")
            return data
    print(f"{SCAN_DATA_FILE} not found.")
    return None


def select_random_images(image_dirs):
    gallery_data = []
    for dir_data in image_dirs:
        images = dir_data["images"]
        if len(images) >= 5:
            sample_images = random.sample(images, 3)
            gallery_data.append(
                {
                    "directory": dir_data["path"],
                    "images": [
                        os.path.join(dir_data["path"], img) for img in sample_images
                    ],
                }
            )
            print(f"Selected images from directory: {dir_data['path']}")
    return gallery_data


# get a list of images in STATIC_IMAGE_DIR
def resource_images():
    images = glob.glob(os.path.join(STATIC_IMAGE_DIR, "*.jpg"))
    images += glob.glob(os.path.join(STATIC_IMAGE_DIR, "*.png"))
    return images


def copy_images_to_static(gallery_data):
    if not os.path.exists(STATIC_IMAGE_DIR):
        os.makedirs(STATIC_IMAGE_DIR)
        print(f"Created directory: {STATIC_IMAGE_DIR}")
    static_image_paths = []
    for item in gallery_data:
        static_images = []
        for img_path in item["images"]:
            img_name = os.path.basename(img_path)
            dest_path = os.path.join(STATIC_IMAGE_DIR, img_name)
            shutil.copy(img_path, dest_path)
            static_images.append(dest_path)
            print(f"Copied image {img_name} to {STATIC_IMAGE_DIR}")
        static_image_paths.append(
            {"directory": item["directory"], "images": static_images}
        )
    return static_image_paths


def remove_gallery_images():
    gallery_folder = "static/local_images/"
    # if not os.path.exists(junk_folder):
    if not os.path.exists(gallery_folder):
        os.makedirs(gallery)
    folder = "static/local_images/"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            # back up images 'static/junk' with a unique uuid before removing
            shutil.copy(
                file_path, "static/junk_resources/" + str(uuid.uuid4()) + filename
            )
            os.remove(file_path)
            try:
                os.remove("local_scan_data.json")
                print(f"Removed file: {file_path}")
            except:
                print(f"Removed file: {file_path}")
    return print(f"Removed file: {file_path}")


@app.route("/gallery")
def gallery():
    remove_gallery_images()
    scan_data = load_scan_data()
    if not scan_data:
        print("No scan data found. Scanning directories.")
        scan_data = scan_directories()
        save_scan_data(scan_data)
        gallery_data = select_random_images(scan_data)
        static_gallery_data = copy_images_to_static(gallery_data)
    else:
        static_gallery_data = load_static_gallery_data()
        if not static_gallery_data:
            print("No static gallery data found. Creating new static gallery data.")
            gallery_data = select_random_images(scan_data)
            static_gallery_data = copy_images_to_static(gallery_data)
            save_static_gallery_data(static_gallery_data)
    return render_template("gallery.html", gallery_data=static_gallery_data)


@app.route("/remove_images", methods=["GET", "POST"])
def remove_images():
    folder = "static/novel_images/"
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                move_novel_image_to_resource_images(file_path)
    return redirect(url_for("mk_videos"))




# Directory containing the images
archived_images_dir = "static/novel_images"
# archived_images_dir = 'static/archived-images/'  # Update this path as needed


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------------
@app.route("/remove_image", methods=["GET", "POST"])
def remove_image():
    folder = "static/archived_resources/"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Removed file: {file_path}")
    return redirect(url_for("index"))


# Directory containing the images
archived_images = "static/archived_resources"


@app.route("/clean_archives", methods=["GET", "POST"])
def clean_archives():
    if request.method == "POST":
        # Get selected images
        selected_images = request.form.getlist("selected_images")
        # list of images sorted by creation time

        # Remove selected images
        for image in selected_images:
            image_path = os.path.join(archived_images, image)
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"Removed image: {image_path}")

        return redirect(url_for("clean_archives"))

    # Get list of images in the directory (png and jpg)
    images = [
        os.path.basename(img)
        for img in glob.glob(os.path.join(archived_images, "*.png"))
    ]
    images += [
        os.path.basename(img)
        for img in glob.glob(os.path.join(archived_images, "*.jpg"))
    ]
    images = sorted(
        images,
        key=lambda x: os.path.getmtime(os.path.join(archived_images, x)),
        reverse=True,
    )
    print(f"clean_archives_Images: {images}")
    return render_template("clean_archives.html", images=images)


def create_backup_folder():
    backup_folder = os.path.join(os.getcwd(), "static", "Backups")
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
        print(f"Backup folder created at: {backup_folder}")


@app.route("/edit_files", methods=["GET", "POST"])
def edit_files():
    filename = request.args.get("filename", "")
    directory_path = "."
    PATH = os.getcwd()
    print(f"Current Directory:, {PATH}")
    full_path = os.path.join(PATH, directory_path, filename)

    if not os.path.exists(filename):
        return "File not found", 404

    if request.method == "POST":
        content = request.form.get("content")

        if content is not None:
            date_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{os.path.splitext(filename)[0]}_{date_str}.txt"
            print(f"File edited and saved as: {new_filename}")

            with open(os.path.join(directory_path, new_filename), "w") as new_file:
                new_file.write(content)

            print(f"File edited and saved as: {new_filename}")

            return send_file(
                os.path.join(directory_path, new_filename), as_attachment=True
            )

    with open(full_path, "r") as file:
        content = file.read()

    return render_template("edit_files.html", filename=filename, content=content)


@app.route("/edit_html", methods=["POST", "GET"])
def edit_html():
    path = TEMPLATE_DIR

    if request.method == "POST":
        if "load_file" in request.form:
            selected_file = request.form["selected_file"]
            file_path = os.path.join(path, selected_file)

            # Load the HTML content from the file
            html_content = load_html_file(file_path)

            # Return JSON for AJAX to update the textarea
            return jsonify({"html_content": html_content})

        elif "edited_content" in request.form:
            edited_content = request.form["edited_content"]
            file_path = os.path.join(path, request.form["selected_file"])

            # Save the edited HTML content
            with open(file_path, "w") as file:
                file.write(edited_content)
                flash("File updated successfully!", "success")

    return render_template("choose_file.html", files=choose_html())


def load_html_file(file_path):
    """Load the content of the selected HTML file."""
    with open(file_path, "r") as file:
        html_content = file.read()
    return html_content


def choose_html():
    """List all HTML files in the templates directory."""
    path = TEMPLATE_DIR
    files = glob.glob(path + "/*.html")
    # show changes first
    files = sorted(files, key=os.path.getmtime, reverse=True)
    return [os.path.basename(file) for file in files]


@app.route("/html_index")
def html_index():
    template_files = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".html")]
    return render_template("html_index.html", template_files=template_files)


def feather_image(image, radius=50):
    """Applies a feathered transparency effect to the left and right edges of an image."""
    print(f"Applying feather effect with radius {radius} to image of size {image.size}")

    mask = Image.new("L", image.size, 0)
    mask.paste(255, (radius, 0, image.width - radius, image.height))
    mask = mask.filter(ImageFilter.GaussianBlur(radius))

    image.putalpha(mask)
    return image


def create_seamless_image(images, feather_radius=5, overlap=100):
    """Creates a seamless image by blending the provided images with feathered edges and overlap."""
    total_width = sum(img.width for img in images) - overlap * (len(images) - 1)
    max_height = max(img.height for img in images)

    print(f"Creating combined image of size {total_width}x{max_height}")

    combined_image = Image.new("RGBA", (total_width, max_height))

    x_offset = 0
    for i, img in enumerate(images):
        feathered_img = feather_image(img, feather_radius)
        combined_image.paste(feathered_img, (x_offset, 0), feathered_img)
        x_offset += img.width - overlap
        print(f"Image {i + 1} pasted at position {x_offset}")

    return combined_image


def make_scrolling_video(
    image_path, output_video_path, video_duration=10, video_size=(512, 768)
):
    """Creates a video by scrolling across the image from left to right."""

    print(f"Loading image from {image_path}")

    image = ImageClip(image_path)

    def scroll_func(get_frame, t):
        x = int((image.size[0] - video_size[0]) * t / video_duration)
        return get_frame(t)[0 : video_size[1], x : x + video_size[0]]

    video = VideoClip(
        lambda t: scroll_func(image.get_frame, t), duration=video_duration
    )
    video = video.set_fps(24)

    print(f"Saving video to {output_video_path}")
    video.write_videofile(output_video_path, codec="libx264", audio=False)


@app.route("/create_video", methods=["POST", "GET"])
def create_video_route():
    """Endpoint to create a scrolling video from a set of images."""
    # copy static/temp_exp/TEMP2.mp4 static/temp_exp/diagonal1.mp4
    # shutil.copy("static/temp_exp/TEMP2.mp4", "static/temp_exp/diagonal1.mp4")
    try:
        vid_directory = "static/novel_images"

        # Get all image files in the directory
        # image_files = glob.glob(os.path.join(vid_directory, '*.png'))
        image_files = glob.glob(os.path.join(vid_directory, "*.png")) + glob.glob(
            os.path.join(vid_directory, "*.jpg")
        )

        if not image_files:
            print("No image files found.")
            return jsonify({"error": "No image files found."}), 404

        # Sort files by modification time
        image_files = sorted(image_files, key=os.path.getmtime, reverse=True)

        if len(image_files) < 6:
            print("Less than 6 images found. Adjusting the number of selected images.")

        images = [
            Image.open(img).convert("RGBA").resize((512, 768), resample=Image.LANCZOS)
            for img in image_files
        ]

        # Create the seamless image
        seamless_image_path = "static/seamless_image.png"
        seamless_image = create_seamless_image(images, feather_radius=10, overlap=100)
        seamless_image.save(seamless_image_path)
        print(f"Seamless image saved as {seamless_image_path}")

        # Create the scrolling video
        video_path = "static/seamless_video.mp4"
        video_duration = 45
        video_size = (512, 768)
        make_scrolling_video(
            seamless_image_path, video_path, video_duration, video_size
        )

        # Optionally run external process if needed
        add_title_image(video_path, hex_color="#A52A2A")
        return redirect(url_for("index"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def createvideo():
    try:
        vid_directory = "static/novel_images"
        # Get all image files in the directory
        # image_files = glob.glob(os.path.join(vid_directory, '*.png'))
        image_files = glob.glob(os.path.join(vid_directory, "*.png")) + glob.glob(
            os.path.join(vid_directory, "*.jpg")
        )

        if not image_files:
            print("No image files found.")
            return jsonify({"error": "No image files found."}), 404

        # Sort files by modification time
        image_files = sorted(image_files, key=os.path.getmtime, reverse=True)

        if len(image_files) < 6:
            print("Less than 6 images found. Adjusting the number of selected images.")

        images = [
            Image.open(img).convert("RGBA").resize((512, 768), resample=Image.LANCZOS)
            for img in image_files[:10]
        ]

        # Create the seamless image
        seamless_image_path = "static/seamless_image.png"
        seamless_image = create_seamless_image(images, feather_radius=5, overlap=50)
        seamless_image.save(seamless_image_path)
        print(f"Seamless image saved as {seamless_image_path}")

        # Create the scrolling video
        video_path = "static/seamless_videoX.mp4"
        video_duration = 56
        video_size = (512, 768)
        make_scrolling_video(
            seamless_image_path, video_path, video_duration, video_size
        )

        # Optionally run external process if needed
        add_title_image(video_path, hex_color="#A52A2A")
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Error creating video 1938: {e}")
        return jsonify({"error": str(e)}), 500


def add_title_image(video_path, hex_color="#A52A2A"):
    hex_color = random.choice(
        ["#A52A2A", "#ad1f1f", "#16765c", "#7a4111", "#9b1050", "#8e215d", "#2656ca"]
    )
    # Define the directory path
    directory_path = "temp"
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
    title_image_path = "static/assets/512x568_border.png"
    # Set the desired size of the padded video (e.g., video width + padding, video height + padding)
    padded_size = (width + 50, height + 50)

    # Calculate the position for centering the video within the larger frame
    x_position = (padded_size[0] - video_clip.size[0]) / 2
    y_position = (padded_size[1] - video_clip.size[1]) / 2
    # hex_color = "#09723c"
    # Remove the '#' and split the hex code into R, G, and B components
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Create an RGB tuple
    rgb_tuple = (r, g, b)

    # Create a blue ColorClip as the background
    blue_background = ColorClip(padded_size, color=rgb_tuple)

    # Add the video clip on top of the red background
    padded_video_clip = CompositeVideoClip(
        [blue_background, video_clip.set_position((x_position, y_position))]
    )
    padded_video_clip = padded_video_clip.set_duration(video_clip.duration)
    # title_image_path = "/home/jack/Desktop/EXPER/static/assets/Title_Image02.png"
    # Load the title image
    title_image = ImageClip(title_image_path)

    # Set the duration of the title image
    title_duration = video_clip.duration
    title_image = title_image.set_duration(title_duration)

    print(video_clip.size)
    # Position the title image at the center and resize it to fit the video dimensions
    # title_image = title_image.set_position(("left", "top"))
    title_image = title_image.set_position((0, -5))
    # video_clip.size = (620,620)
    title_image = title_image.resize(padded_video_clip.size)

    # Position the title image at the center and resize it to fit the video dimensions
    # title_image = title_image.set_position(("center", "center")).resize(video_clip.size)

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
    # music duration is same as video
    music_clip = music_clip.set_duration(video_clip.duration)
    # Fade in and out the background music
    fade_duration = 1.0
    music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(fade_duration)
    # Set the audio of the composite clip to the background music
    composite_clip = composite_clip.set_audio(music_clip)
    uid = uuid.uuid4().hex
    output_path = "static/temp_exp/TEMP2X.mp4"
    # Export the final video with the background music
    composite_clip.write_videofile(output_path)
    mp4_file = f"static/output_videos/Ready_Post_{uid}.mp4"
    shutil.copyfile(output_path, mp4_file)
    print(mp4_file)
    VIDEO = output_path
    return VIDEO


def add_title(video_path, hex_color="#A52A2A"):
    hex_color = random.choice(
        ["#A52A2A", "#ad1f1f", "#16765c", "#7a4111", "#9b1050", "#8e215d", "#2656ca"]
    )
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
    title_image_path = "static/assets/512x568_border.png"
    # Set the desired size of the padded video (e.g., video width + padding, video height + padding)
    padded_size = (width + 50, height + 50)

    # Calculate the position for centering the video within the larger frame
    x_position = (padded_size[0] - video_clip.size[0]) / 2
    y_position = (padded_size[1] - video_clip.size[1]) / 2
    # hex_color = "#09723c"
    # Remove the '#' and split the hex code into R, G, and B components
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Create an RGB tuple
    rgb_tuple = (r, g, b)

    # Create a blue ColorClip as the background
    blue_background = ColorClip(padded_size, color=rgb_tuple)

    # Add the video clip on top of the red background
    padded_video_clip = CompositeVideoClip(
        [blue_background, video_clip.set_position((x_position, y_position))]
    )
    padded_video_clip = padded_video_clip.set_duration(video_clip.duration)
    # title_image_path = "/home/jack/Desktop/EXPER/static/assets/Title_Image02.png"
    # Load the title image
    title_image = ImageClip(title_image_path)

    # Set the duration of the title image
    title_duration = video_clip.duration
    title_image = title_image.set_duration(title_duration)

    print(video_clip.size)
    # Position the title image at the center and resize it to fit the video dimensions
    # title_image = title_image.set_position(("left", "top"))
    title_image = title_image.set_position((0, -5))
    # video_clip.size = (620,620)
    title_image = title_image.resize(padded_video_clip.size)

    # Position the title image at the center and resize it to fit the video dimensions
    # title_image = title_image.set_position(("center", "center")).resize(video_clip.size)

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
    # music duration is same as video
    music_clip = music_clip.set_duration(video_clip.duration)
    # Fade in and out the background music
    fade_duration = 1.0
    music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(fade_duration)
    # Set the audio of the composite clip to the background music
    composite_clip = composite_clip.set_audio(music_clip)
    uid = uuid.uuid4().hex
    output_path = "static/temp_exp/TEMP1X.mp4"
    # Export the final video with the background music
    composite_clip.write_videofile(output_path)
    mp4_file = f"static/output_videos/Ready_Post_{uid}.mp4"
    shutil.copyfile(output_path, mp4_file)
    print(mp4_file)
    VIDEO = output_path
    return VIDEO


def ensure_dir_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def next_points(point, imgsize, avoid_points=[], shuffle=True):
    point_list = [
        p
        for p in [
            (point[0], point[1] + 1),
            (point[0], point[1] - 1),
            (point[0] + 1, point[1]),
            (point[0] - 1, point[1]),
        ]
        if 0 < p[0] < imgsize[0] // 2
        and 0 < p[1] < imgsize[1]
        and p not in avoid_points
    ]

    if shuffle:
        random.shuffle(point_list)

    return point_list


def degrade_color(color, degradation=10):
    return tuple(min(c + degradation, 255) for c in color)


def spread(img, point, color, max_white=100, degradation=10):
    if color[0] <= max_white and img.getpixel(point)[0] > color[0]:
        img.putpixel(point, color)
        points = next_points(point, img.size, shuffle=False)
        color = degrade_color(color, degradation)
        for point in points:
            spread(img, point, color)


def binarize_array(numpy_array, threshold=200):
    return np.where(numpy_array > threshold, 255, 0)


def processr_image(seed_count, seed_max_size, imgsize=(510, 766), count=0):
    margin_h, margin_v = 60, 60
    color = (0, 0, 0)
    img = Image.new("RGB", imgsize, "white")
    old_points = []
    posible_root_points = []

    for seed in range(seed_count):
        point = None
        while not point or point in old_points:
            point = (
                random.randrange(0 + margin_h, imgsize[0] // 2),
                random.randrange(0 + margin_v, imgsize[1] - margin_v),
            )
        old_points.append(point)
        posible_root_points.append(point)
        img.putpixel(point, color)

        seedsize = random.randrange(0, seed_max_size)
        flow = 0
        for progress in range(seedsize):
            flow += 1
            points = next_points(point, imgsize, old_points)
            try:
                point = points.pop()
            except IndexError:
                posible_root_points.remove(point)
                for idx in reversed(range(len(posible_root_points))):
                    points = next_points(posible_root_points[idx], imgsize, old_points)
                    try:
                        point = points.pop()
                        flow = 0
                        break
                    except IndexError:
                        posible_root_points.pop()
                if not point:
                    break

            old_points.append(point)
            posible_root_points.append(point)
            img.putpixel(point, color)

            for surr_point in points:
                spread(img, surr_point, degrade_color(color))

    cropped = img.crop((0, 0, imgsize[0] // 2, imgsize[1]))
    img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(cropped, (0, 0, imgsize[0] // 2, imgsize[1]))
    img = img.filter(ImageFilter.GaussianBlur(radius=10))

    filename0 = "static/images/blot.png"
    img.save(filename0)

    im_grey = img.convert("LA")
    mean = np.mean(np.array(im_grey)[:, :, 0])

    image_file = Image.open(filename0)
    imagex = image_file.convert("L")
    imagey = np.array(imagex)
    imagez = binarize_array(imagey, mean)

    temp_filename = "static/images/tmmmp.png"
    cv2.imwrite(temp_filename, imagez)

    final_filename = time.strftime("static/archived-images/GOODblots%Y%m%d%H%M%S.png")
    ImageOps.expand(
        Image.open(temp_filename).convert("L"), border=1, fill="white"
    ).save(final_filename)

    print("GoodBlot: ", count)
    return final_filename

    def weight_boundary(graph, src, dst, n):
        default = {"weight": 0.0, "count": 0}
        count_src = graph[src].get(n, default)["count"]
        count_dst = graph[dst].get(n, default)["count"]
        weight_src = graph[src].get(n, default)["weight"]
        weight_dst = graph[dst].get(n, default)["weight"]
        count = count_src + count_dst
        return {
            "count": count,
            "weight": (count_src * weight_src + count_dst * weight_dst) / count,
        }

    def merge_boundary(graph, src, dst):
        pass

    labels2 = future.graph.merge_hierarchical(
        labels,
        g,
        thresh=0.08,
        rag_copy=False,
        in_place_merge=True,
        merge_func=merge_boundary,
        weight_func=weight_boundary,
    )

    out = color.label2rgb(labels2, img, kind="avg")

    # Save the processed image
    output_filename = os.path.join(
        app.config["UPLOAD_FOLDER"], f"processed_{time.time()}.png"
    )
    imsave(output_filename, out)
    return output_filename


# Route for the main page
@app.route("/uploadfile", methods=["GET", "POST"])
def uploadfile():
    if request.method == "POST":
        # Check if the post request has the file part
        if "file" not in request.files:
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Process the image and get the output path
            processed_image_path = process_image(filepath)

            return redirect(
                url_for(
                    "uploaded_file", filename=os.path.basename(processed_image_path)
                )
            )
    return """
    <!doctype html>
    <title>Upload an image</title>
    <h1>Upload an image for segmentation processing</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """


try:
    os.makedirs("static/outlines")
except FileExistsError:
    # directory already exists
    pass


def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)
    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)
    # return the edged image
    return edged


# image = cv2.imread('mahotastest/orig-color.png')
def change_extension(orig_file, new_extension):
    p = change_ext(orig_file)
    new_name = p.rename(p.with_suffix(new_extension))
    return new_name


def FilenameByTime(directory):
    timestamp = str(time.time()).replace(".", "")
    filename = f"{directory}/{timestamp}.png"
    return filename


def auto_canny(image, sigma=0.33):
    v = np.median(image)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)
    return edged


def outlineJ(filename, sigma=0.33):
    # Load the image and apply Canny edge detection
    image = cv2.imread(filename)
    edged = auto_canny(image, sigma=sigma)

    # Invert the colors for black-and-white outlines
    inverted = cv2.bitwise_not(edged)

    # Paths to save the images
    temp_path = "static/outlines/temp2.png"
    outline_path = "static/outlines/outlined.png"
    transparent_path = "static/outlines/transparent_outline.png"

    # Save the inverted black-and-white image
    cv2.imwrite(temp_path, inverted)

    # Open the black-and-white outline image
    frontimage = Image.open(temp_path).convert("RGBA")  # Load as RGBA for transparency

    # Process to create the black outline with transparent background
    datas = frontimage.getdata()

    newData = []
    for item in datas:
        # If the pixel is white, make it transparent
        if item[0] > 200 and item[1] > 200 and item[2] > 200:  # Adjust as necessary
            newData.append((255, 255, 255, 0))
        else:
            newData.append((0, 0, 0, 255))  # Keep black as is

    frontimage.putdata(newData)
    frontimage.save(transparent_path)  # Save the transparent outline

    # Open the original image to apply the outline
    background = Image.open(filename).convert("RGBA")
    background.paste(frontimage, (3, 3), frontimage)  # Paste with transparency

    # Save the outlined image
    background.save(outline_path)

    # Save the outline on a white background
    outline_on_white = Image.new("RGBA", background.size, "WHITE")
    outline_on_white.paste(frontimage, (0, 0), frontimage)
    outline_on_white.save(temp_path)

    # Save the images with timestamps
    unique_id = uuid.uuid4().hex
    # savefile = f"static/outlines/{unique_id}.png"

    savefile = FilenameByTime("static/outlines")
    shutil.copyfile(
        transparent_path, f"static/archived-images/{unique_id}outlines_transparent.png"
    )
    shutil.copyfile(outline_path, f"static/archived-images/{unique_id}_outlined.png")
    shutil.copyfile(temp_path, f"static/archived-images/{unique_id}_bw.png")

    return outline_path, transparent_path, temp_path


@app.route("/outlinefile", methods=["GET", "POST"])
def outlinefile():
    if request.method == "POST":
        # Check if the post request has the file part
        if "file" not in request.files:
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Process the image and get the output path
            savefile, display_filename, temp_filename = outlineJ(filepath, sigma=0.33)
            return render_template(
                "outlines.html", filename=display_filename, temp_filename=temp_filename
            )
    return """
    <!doctype html>
    <title>Upload an image</title>
    <h1>Upload an image for outline processing</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """


# def allowed_file(filename):
#    return '.' in filename and filename.rsplit('.', 1)[1].lower() in{'png', 'jpg', 'jpeg', 'gif'}

# SQLite database setup functions
'''
def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    """
    try:
        conn = sqlite3.connect(DATABASEF)
        conn.row_factory = sqlite3.Row
        print("Database connection established.")
        return conn
    except sqlite3.Error as e:
        print(f"Error establishing database connection: {e}")
        traceback.print_exc()
        return None

def create_db():
    """
    Initializes the database by creating necessary tables if they don't exist.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS functions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_text TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print(f"Database {DATABASEF} initialized.")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        traceback.print_exc()

def read_functions():
    """
    Reads all function texts from the database.
    """
    print("Reading functions from database...")
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return []
        cursor = conn.cursor()
        cursor.execute('SELECT function_text FROM functions')
        functions = [row[0] for row in cursor.fetchall()]
        conn.close()
        print("Functions retrieved from database.")
        return functions
    except sqlite3.Error as e:
        print(f"Error reading functions: {e}")
        traceback.print_exc()
        return []

def insert_function(function_text):
    """
    Inserts a new function text into the database.
    """
    try:
        print("Inserting function into database...")
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return
        cursor = conn.cursor()
        cursor.execute('INSERT INTO functions (function_text) VALUES (?)', (function_text,))
        conn.commit()
        conn.close()
        print("Function inserted into database.")
    except sqlite3.Error as e:
        print(f"Error inserting function: {e}")
        traceback.print_exc()

def insert_functions():
    """
    Inserts functions from 'con_html.txt' into the database if not already initialized.
    """
    print("Checking if functions need to be inserted into the database...")
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key='initialized'")
        result = cursor.fetchone()
        if result is None:
            print("Initializing and inserting functions from 'con_html.txt'...")
            with open('all_html.txt', 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            # Assuming functions are separated by '\n.\n'
            segments = content.strip().split('@app')
            for segment in segments:
                cleaned_segment = segment.strip()
                if cleaned_segment:
                    cursor.execute('INSERT INTO functions (function_text) VALUES (?)', (cleaned_segment,))
            cursor.execute("INSERT INTO metadata (key, value) VALUES ('initialized', 'true')")
            conn.commit()
            print("Functions inserted into database.")
        else:
            print("Functions already inserted into database.")
        conn.close()
    except sqlite3.Error as e:
        print(f"Error inserting functions into database: {e}")
        traceback.print_exc()

def get_last_function():
    """
    Retrieves the most recently inserted function from the database.
    """
    print("Retrieving the last function from the database...")
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return None
        cursor = conn.cursor()
        cursor.execute('SELECT function_text FROM functions ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        if result:
            print("Last function retrieved successfully.")
            return result[0]
        else:
            print("No functions found in the database.")
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving last function: {e}")
        traceback.print_exc()
        return None
'''


@app.route("/index_code")
def index_code():
    """
    Renders the main index page with the latest function.
    """
    functions = get_last_function()
    return render_template("index_code.html", functions=functions)


@app.route("/save", methods=["POST"])
def save():
    """
    Saves the provided code and generates suggestions.
    """
    code = request.form["code"]
    suggestions = generate_suggestions(code)
    return {"suggestions": suggestions}


def generate_suggestions(code):
    """
    Generates suggestions based on the last two words of the provided code.
    Each suggestion is approximately 400 characters long.
    """
    print("Generating suggestions...")
    functions = read_functions()

    if not functions:
        print("No functions available to generate suggestions.")
        return []

    # Retrieve the last line from the code
    lines = code.strip().split("\n")
    last_line = lines[-1] if lines else ""
    print(f"Last line of code: '{last_line}'")

    # Split the last line into words and get the last two words
    words = last_line.split()
    last_two_words = " ".join(words[-2:]) if len(words) >= 2 else last_line
    print(f"Last two words: '{last_two_words}'")

    # Function to split snippet based on last_two_words and return completion
    def split_snippet(snippet, last_two_words):
        index = snippet.rfind(last_two_words)
        if index != -1:
            completion = snippet[index + len(last_two_words) :].strip()
            return completion
        return snippet.strip()

    # Search for matching snippets based on the last two words
    matching_snippets = []
    found_indices = set()  # To store indices of found snippets to avoid duplicates

    for i, snippet in enumerate(functions, start=1):
        if last_two_words in snippet:
            if i not in found_indices:
                found_indices.add(i)
                completion = split_snippet(snippet, last_two_words)
                formatted_snippet = f"<pre>{i}: {completion}</pre>"
                # Adjust the snippet length to approximately 400 characters
                if len(formatted_snippet) > 400:
                    formatted_snippet = formatted_snippet[:397] + "..."
                matching_snippets.append(formatted_snippet)
                print(f"Added snippet {i}: {formatted_snippet}")

    # Return up to 20 suggestions, limited to 5 for demonstration purposes
    suggestions = matching_snippets[:5]
    print(f"Generated {len(suggestions)} suggestions.")
    return suggestions


@app.route("/save_code", methods=["POST"])
def save_code():
    """
    Saves the provided code to the database.
    """
    code = request.data.decode("utf-8")
    print(
        f"Received code to save: {code[:50]}..."
    )  # Log first 50 characters for brevity
    if code:
        insert_function(code)
        return "Code saved successfully", 200
    else:
        print("No code provided in the request.")
        return "No code provided in the request", 400


@app.route("/functions", methods=["GET", "POST"])
def get_functions():
    """
    Retrieves all functions from the database and returns them as JSON.
    """
    print("Fetching all functions from the database.")
    conn = get_db_connection()
    if conn is None:
        print("Failed to establish database connection.")
        return jsonify([]), 500
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functions")
    functions = cursor.fetchall()
    conn.close()
    print(f"Retrieved {len(functions)} functions from the database.")
    return jsonify([dict(ix) for ix in functions])


@app.route("/functions/<int:id>", methods=["PUT", "GET"])
def update_response(id):
    """
    Updates the function text for a given function ID.
    """
    new_response = request.json.get("function_text")
    print(f"Updating function ID {id} with new text.")
    if not new_response:
        print("No new function text provided.")
        return (
            jsonify({"status": "failure", "message": "No function text provided"}),
            400,
        )
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return (
                jsonify({"status": "failure", "message": "Database connection failed"}),
                500,
            )
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE functions SET function_text = ? WHERE id = ?", (new_response, id)
        )
        conn.commit()
        conn.close()
        print(f"Function ID {id} updated successfully.")
        return jsonify(
            {"status": "success", "message": "Function updated successfully"}
        )
    except sqlite3.Error as e:
        print(f"Error updating function ID {id}: {e}")
        traceback.print_exc()
        return jsonify({"status": "failure", "message": "Error updating function"}), 500


@app.route("/view_functions", methods=["GET", "POST"])
def view_functions():
    """
    Renders a page to view all functions.
    """
    print("Rendering view_functions page.")
    conn = get_db_connection()
    if conn is None:
        print("Failed to establish database connection.")
        return render_template("view_functions.html", data=[])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functions")
    data = cursor.fetchall()
    conn.close()
    print(f"Retrieved {len(data)} functions for viewing.")
    return render_template("view_functions.html", data=data)


@app.route("/update_function", methods=["POST", "GET"])
def update_function():
    """
    Updates a specific function based on form data and redirects to the view page.
    """
    id = request.form.get("id")
    new_function_text = request.form.get("function_text")
    print(f"Received update for function ID {id}.")
    if not id or not new_function_text:
        print("Missing function ID or new function text in the request.")
        return redirect(url_for("view_functions"))
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return redirect(url_for("view_functions"))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE functions SET function_text = ? WHERE id = ?",
            (new_function_text, id),
        )
        conn.commit()
        conn.close()
        print(f"Function ID {id} updated successfully via form.")
        return redirect(url_for("view_functions"))
    except sqlite3.Error as e:
        print(f"Error updating function ID {id}: {e}")
        traceback.print_exc()
        return redirect(url_for("view_functions"))


def get_suggestions(search_term):
    try:
        # Create a database connection
        conn = sqlite3.connect(":memory:")
        c = conn.cursor()

        # Create table
        c.execute(
            """CREATE TABLE IF NOT EXISTS dialogue
                     (id INTEGER PRIMARY KEY,
                      search_term TEXT,
                      ChatGPT_PAIR TEXT,
                      ChatGPT_PAIRb BLOB
                      )"""
        )
        conn.commit()

        # Perform operations
        cnt = 0
        DATA = set()
        INDEX = "----SplitHere------"
        with open("app.py", "r") as data:
            Lines = data.read()
            lines = Lines.replace(search_term, INDEX + search_term)
            lines = lines.split(INDEX)
            for line in lines:
                if search_term in line:
                    cnt += 1
                    DATA.add(f"{line[:1200]}")
                    # Insert dialogue pair into the table
                    c.execute(
                        "INSERT INTO dialogue (search_term, ChatGPT_PAIR, ChatGPT_PAIRb) VALUES (?, ?, ?)",
                        (search_term, line, line.encode("utf-8")),
                    )
                    conn.commit()

        # Close the database connection
        conn.close()
        return DATA
    except Exception as e:
        print(f"An error occurred: {e}")
        return set()


@app.route("/search_file", methods=["GET", "POST"])
def search_file():
    search_term = (
        request.args.get("q", "")
        if request.method == "GET"
        else request.form.get("q", "")
    )
    if search_term:
        data = get_suggestions(search_term)
        return render_template_string(
            """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Search Results</title>
            <link rel="stylesheet" href="{{ url_for('static', filename='css/themed.css') }}">
        </head>
        <body>
        <div class="container">
            <a class="btn btn-secondary" href="/search_file">🔍 Search Again</a> &nbsp;
            <a class="btn btn-secondary" href="/">🏠 Home</a>
            <br><br>
            <h1>Search Results for "{{ search_term }}"</h1>
            {% for item in data %}
                <div style="border-bottom: 1px solid var(--border-color); padding: 12px 0;">
                    <pre>{{ item }}</pre>
                </div>
            {% endfor %}
        </div>
        </body>
        </html>
        """,
            search_term=search_term,
            data=data,
        )
    else:
        return render_template_string(
            """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Enter Search Term</title>
            <link rel="stylesheet" href="{{ url_for('static', filename='css/themed.css') }}">
        </head>
        <body>
        <div class="container" style="max-width: 600px; margin: 40px auto;">
            <h1>Enter a Search Term</h1>
            <form action="/search_file" method="post">
                <input type="text" name="q" placeholder="Enter search term...">
                <button type="submit" class="btn">Search</button>
            </form>
        </div>
        </body>
        </html>
        """
        )


@app.route("/convert-images")
def convert_images_route():
    try:
        convert_images()
        return redirect(url_for("mk_videos"))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/create-video")
def create_video():
    try:
        createvideo()
        return redirect(url_for("mk_videos"))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/refresh-video-process")
def refresh_video_route():
    try:
        subprocess.run([sys.executable, "refresh_video.py"], check=True)
        return redirect(url_for("mk_videos"))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route("/best-flipbook")
def best_flipbook_route():
    try:
        subprocess.run([sys.executable, "Best_FlipBook"], check=True)
        return redirect(url_for("mk_videos"))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route("/diagonal-transition")
def diagonal_transition_route():
    try:
        subprocess.run([sys.executable, "diagonal_transition"], check=True)
        video_path = "static/temp_exp/diagonal1.mp4"
        add_title(video_path, hex_color="#A52A2A")
        return redirect(url_for("mk_videos"))

    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route("/slide")
def slide_route():
    try:
        subprocess.run(["/bin/bash", "slide"], check=True)
        return redirect(url_for("mk_videos"))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route("/zoomx4")
def zoomx4_route():
    try:
        subprocess.run(["/bin/bash", "zoomX4"], check=True)
        return redirect(url_for("mk_videos"))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route("/zoomy4")
def zoomy4_route():
    try:
        subprocess.run(["/bin/bash", "zoomY4"], check=True)
        return redirect(url_for("mk_videos"))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route("/vertical-scroll")
def vertical_scroll_route():
    try:
        subprocess.run([sys.executable, "vertical_scroll.py"], check=True)
        return redirect(url_for("mk_videos"))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route("/add-title")
def add_title_route():
    try:
        video_path = "static/temp_exp/diagonal1.mp4"
        add_title(video_path, hex_color="#A52A2A")
        return redirect(url_for("mk_videos"))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/join-video")
def join_video_route():
    try:
        subprocess.run([sys.executable, "join_all_videos"], check=True)
        return redirect(url_for("mk_videos"))
    except subprocess.CalledProcessError as e:
        return jsonify(error=str(e)), 500


@app.route("/refresh-all")
def refresh_all_route():
    try:
        # Call each route sequentially
        convert_and_resize_images_route()
        create_video_route()
        refresh_video_route()
        best_flipbook_route()
        diagonal_transition_route()
        # blendem_route()
        slide_route()
        zoomx4_route()
        vertical_scroll_route()
        add_title_route()
        join_video_route()
        resize_mp4_route

        return redirect(url_for("create_video"))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/convert_and_resize_images")
def convert_and_resize_images_route():
    img_dir = "static/novel_images"

    # Ensure the directory exists
    if not os.path.exists(img_dir):
        return "Directory not found", 404

    # Get all files in the directory and sort by creation time
    image_files = [
        f for f in os.listdir(img_dir) if f.lower().endswith((".png", ".jpg"))
    ]
    image_files = sorted(
        image_files,
        key=lambda x: os.path.getctime(os.path.join(img_dir, x)),
        reverse=True,
    )

    # Iterate over sorted images
    for file in image_files:
        img_file_path = os.path.join(img_dir, file)

        # Convert to JPG if PNG and set the new path
        if file.lower().endswith(".png"):
            new_file_path = os.path.splitext(img_file_path)[0] + ".jpg"
        else:
            new_file_path = img_file_path

        try:
            # Open the image
            with Image.open(img_file_path) as img:
                # Resize image to height of 768 while maintaining aspect ratio
                width, height = img.size
                new_height = 768
                new_width = int((new_height / height) * width)
                resized_img = img.resize((new_width, new_height))

                # Center crop to 512x768
                left = (new_width - 512) / 2
                top = 0
                right = (new_width + 512) / 2
                bottom = 768
                cropped_img = resized_img.crop((left, top, right, bottom))

                # Convert to RGB (only for PNGs)
                if file.lower().endswith(".png"):
                    cropped_img = cropped_img.convert("RGB")

                # Save the resulting image as JPG
                cropped_img.save(new_file_path, "JPEG")

        except Exception:
            continue

    return redirect(url_for("conversion_complete"))


@app.route("/conversion_complete")
def conversion_complete():
    return "All PNG and JPG files have been converted, resized to 512x768, and saved."


@app.route("/base")
def base():
    return render_template("base_1.html")


# Step 1: Resize videos and save as basename_512x768.mp4
def resize_videos(directory, target_size=(512, 768)):
    for filename in os.listdir(directory):
        if filename.endswith("X.mp4") and not filename.endswith("_512x768.mp4"):
            filepath = os.path.join(directory, filename)

            # Load the video file
            video_clip = VideoFileClip(filepath)

            # Resize the video to the target size (512x768)
            resized_clip = video_clip.resize(newsize=target_size)

            # Save the resized video with the new name basename_512x768.mp4
            new_filename = os.path.splitext(filename)[0] + "_512x768.mp4"
            resized_filepath = os.path.join(directory, new_filename)

            # Write the resized video to a file
            resized_clip.write_videofile(resized_filepath)

            # Close the clip to release resources
            video_clip.close()


# Step 2: Concatenate all the resized videos
def concatenate_resized_videos(directory, output_file):
    video_clips = []

    # Look for all files that match *_512x768.mp4
    for filename in os.listdir(directory):
        if filename.endswith("_512x768.mp4"):
            filepath = os.path.join(directory, filename)

            # Load the resized video file
            video_clip = VideoFileClip(filepath)

            # Add to the list of clips to concatenate
            video_clips.append(video_clip)

    # Concatenate all resized video clips
    if video_clips:
        final_clip = concatenate_videoclips(video_clips, method="compose")

        # Write the final concatenated clip to the output file
        final_clip.write_videofile(output_file)

        # Close the clips to release resources
        for clip in video_clips:
            clip.close()


@app.route("/resize_mp4")
def resize_mp4_route():
    # Directory containing the original *.mp4 files
    input_directory = "static/temp_exp"

    # Output file name for the concatenated video
    output_file = (
        "static/temp_exp/all_asset_videos.mp4"
    )

    # Step 1: Resize and save videos
    resize_videos(input_directory)

    # Step 2: Concatenate resized videos
    concatenate_resized_videos(input_directory, output_file)
    return redirect(url_for("display_resources"))


archived_images_dir = "static/novel_images"


def resize_and_crop_image(image_path):
    """Resize image to height 768 keeping aspect ratio, then center-crop to 512x768."""
    try:
        print(f"Processing image: {image_path}")
        with Image.open(image_path) as img:
            # Resize image to height 768 while maintaining the aspect ratio
            width, height = img.size
            aspect_ratio = width / height
            new_height = 768
            new_width = 512  # int(aspect_ratio * new_height)

            print(
                f"Original size: {width}x{height}, Resizing to: {new_width}x{new_height}"
            )

            img = img.resize((new_width, new_height), Image.LANCZOS)

            # Calculate cropping box to center-crop the image to 512x768
            # left = (new_width - 512) / 2
            # top = 0  # Since height is already 768, no need to crop vertically
            # right = (new_width + 512) / 2
            # bottom = 768

            # print(f"Cropping coordinates: left={left}, top={top}, right={right}, bottom={bottom}")

            # img = img.crop((left, top, right, bottom))

            # Save the cropped image as JPG
            new_image_path = os.path.splitext(image_path)[0] + ".jpg"
            img.convert("RGB").save(new_image_path, "JPEG")

            print(f"Saved resized and cropped image: {new_image_path}")

            # Optionally, remove the original PNG file if it exists
            if image_path.lower().endswith(".png"):
                os.remove(image_path)
                print(f"Removed original PNG file: {image_path}")

    except Exception as e:
        print(f"Error processing {image_path}: {e}")


@app.route("/size_and_format_images")
def size_and_format_images_route():
    """Resize and format PNG/JPG images in the specified directory."""
    print("Starting image resizing and formatting...")
    for image_path in glob.glob(os.path.join(archived_images_dir, "*")):
        if image_path.lower().endswith((".png", ".jpg")):
            print(f"Resizing image: {image_path}")
            resize_and_crop_image(image_path)
    print("Image resizing completed.")
    return redirect(url_for("img_processing_route"))


@app.route("/clean_storage", methods=["GET", "POST"])
def clean_storage_route():
    directory_path = "static/temp_exp"
    delete_non_X_mp4_files(directory_path)
    # Resize and format images before processing
    size_and_format_images_route()

    if request.method == "POST":
        # Get selected images from form
        selected_images = request.form.getlist("selected_images")

        if selected_images:
            valid_images = []
            for img in selected_images:
                p = os.path.join(archived_images_dir, img)
                if os.path.exists(p):
                    valid_images.append(img)
                else:
                    base = os.path.splitext(img)[0]
                    for ext in [".jpg", ".png", ".jpeg"]:
                        cand = base + ext
                        if os.path.exists(os.path.join(archived_images_dir, cand)):
                            valid_images.append(cand)
                            break
            if valid_images:
                # Generate a unique video file name
                unique_id = str(uuid.uuid4())
                archive_dir = "static/image-archives"
                os.makedirs(archive_dir, exist_ok=True)
                video_filename = os.path.join(archive_dir, f"{unique_id}.mp4")
                temp_raw_filename = os.path.join(archive_dir, f"temp_{unique_id}.mp4")

                # Get dimensions from the first image to set video size
                first_image_path = os.path.join(archived_images_dir, valid_images[0])
                first_image = cv2.imread(first_image_path)
                if first_image is not None:
                    height, width = first_image.shape[:2]
                else:
                    width, height = 512, 768

                # Ensure even dimensions (required for H.264 / yuv420p)
                width = width if width % 2 == 0 else width + 1
                height = height if height % 2 == 0 else height + 1

                # Define temporary raw video writer (1 frame per second)
                video = cv2.VideoWriter(
                    temp_raw_filename, cv2.VideoWriter_fourcc(*"mp4v"), 1, (width, height)
                )

                # Write each selected image to the video (resizing to match if needed)
                written_count = 0
                for image in valid_images:
                    image_path = os.path.join(archived_images_dir, image)
                    img = cv2.imread(image_path)
                    if img is not None:
                        if img.shape[1] != width or img.shape[0] != height:
                            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
                        video.write(img)
                        written_count += 1

                # Release the VideoWriter object after writing the video
                video.release()

                # Re-encode to clean, browser-compatible H.264 using FFmpeg
                if written_count > 0 and os.path.exists(temp_raw_filename):
                    try:
                        ffmpeg_cmd = [
                            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
                            "-i", temp_raw_filename,
                            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                            "-c:v", "libx264",
                            "-pix_fmt", "yuv420p",
                            "-preset", "fast",
                            "-crf", "18",
                            "-movflags", "+faststart",
                            video_filename
                        ]
                        subprocess.run(ffmpeg_cmd, check=True)
                        if os.path.exists(temp_raw_filename):
                            os.remove(temp_raw_filename)
                        print(f"[✓] Archived {written_count} images into H.264 video: {video_filename}")
                    except Exception as e:
                        print(f"[!] FFmpeg error during archive: {e}. Falling back to raw file.")
                        if os.path.exists(temp_raw_filename):
                            shutil.move(temp_raw_filename, video_filename)

                # Remove selected images from storage only after video is safely created
                for image in valid_images:
                    image_path = os.path.join(archived_images_dir, image)
                    if os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            print(f"[!] Could not remove {image_path}: {e}")

        return redirect(url_for("clean_storage_route"))

    # Fetch all images (JPG and PNG) in the archived directory
    images = [
        os.path.basename(img)
        for img in glob.glob(os.path.join(archived_images_dir, "*.jpg"))
    ]
    images.extend(
        [
            os.path.basename(img)
            for img in glob.glob(os.path.join(archived_images_dir, "*.png"))
        ]
    )

    # Sort images by creation time
    images = sorted(
        images,
        key=lambda x: os.path.getctime(os.path.join(archived_images_dir, x)),
        reverse=True,
    )

    return render_template("img_processing.html", images=images)


@app.route("/get_videos", methods=["GET", "POST"])
def get_videos():
    video_files = glob.glob("static/video_history/*.mp4")
    return render_template("get_videos.html", video_files=video_files)


@app.route("/upload_form")
def upload_form():
    image_directory = "static/novel_images/"  # Directory containing the images
    images_list = []

    # Retrieve all image files from the directory
    image_files = [
        f
        for f in os.listdir(image_directory)
        if f.endswith(".jpg") or f.endswith(".png")
    ]
    # List by date of creation reverse
    image_files = sorted(
        image_files,
        key=lambda x: os.path.getctime(os.path.join(image_directory, x)),
        reverse=True,
    )
    return render_template(
        "upload_form.html", video_url=None, video_type=None, image_files=image_files
    )


@app.route("/process_selected_images", methods=["POST"])
def process_selected_images():
    # Check if any images were uploaded
    bg_image_uploaded = request.files.get("bg_image")
    fg_image_uploaded = request.files.get("fg_image")

    # Check if any existing images were selected
    bg_image_selected = request.form.get("bg_image_selected")
    fg_image_selected = request.form.get("fg_image_selected")

    if bg_image_uploaded and bg_image_uploaded.filename != "":
        bg_filename = "background.png"
        bg_image_uploaded.save(os.path.join("static", bg_filename))
        bg_file_path = os.path.abspath(os.path.join("static", bg_filename))
    elif bg_image_selected:
        bg_file_path = os.path.abspath(
            os.path.join("static/novel_images", bg_image_selected)
        )
    else:
        return redirect(url_for("upload_form"))

    if fg_image_uploaded and fg_image_uploaded.filename != "":
        fg_filename = "foreground.png"
        fg_image_uploaded.save(os.path.join("static", fg_filename))
        fg_file_path = os.path.abspath(os.path.join("static", fg_filename))
    elif fg_image_selected:
        fg_file_path = os.path.abspath(
            os.path.join("static/novel_images", fg_image_selected)
        )
    else:
        return redirect(url_for("upload_form"))

    # Apply zoom effect and get the processed image list
    images_list = zoom_effect(bg_file_path, fg_file_path)

    if not os.path.exists("static/overlay_zooms/title"):
        os.makedirs("static/overlay_zooms/title")

    output_mp4_file = "static/overlay_zooms/title/title_video.mp4"
    frames_per_second = 30
    create_mp4_from_images(images_list, output_mp4_file, frames_per_second)
    shutil.copy(output_mp4_file, "static/temp_exp/title_video.mp4")
    # Create a timestamped copy of the output MP4
    file_bytime = time.strftime("%Y%m%d-%H%M%S") + ".mp4"
    shutil.copy(output_mp4_file, "static/overlay_zooms/title/" + file_bytime)
    video_url = url_for("static", filename="overlay_zooms/title/" + file_bytime)

    return render_template("upload.html", video_url=video_url, video_type="title")


# Route to process all images in a directory (main video)@app.route('/zoom_all')
@app.route("/zoom_all")
def process_directory():
    image_directory = "static/novel_images/"  # Directory containing the images
    images_list = []

    # Retrieve all image files from the directory
    image_files = [
        f
        for f in os.listdir(image_directory)
        if f.endswith(".jpg") or f.endswith(".png")
    ]
    # list by date of creation reverse
    image_files = sorted(
        image_files,
        key=lambda x: os.path.getctime(os.path.join(image_directory, x)),
        reverse=True,
    )

    # Ensure there are at least two images to work with
    if len(image_files) < 2:
        print(f"Not enough images in {image_directory} to process.")
        return render_template(
            "upload.html", error="Not enough images to apply zoom effect."
        )

    # Iterate over image pairs
    for i in range(0, len(image_files) - 1, 2):
        # Define image paths for the current pair
        image_path1 = os.path.join(image_directory, image_files[i])
        image_path2 = os.path.join(image_directory, image_files[i + 1])

        # Apply zoom effect with two different images
        images = zoom_effect(image_path1, image_path2)
        images_list.extend(images)

        # Logging the processed images
        print(f"Processed images: {image_files[i]} and {image_files[i + 1]}")

    # Ensure the output directory exists
    if not os.path.exists("static/overlay_zooms/main"):
        os.makedirs("static/overlay_zooms/main")

    # Generate MP4 file from processed images
    output_mp4_file = "static/overlay_zooms/main/main_video.mp4"
    frames_per_second = 30
    create_mp4_from_images(images_list, output_mp4_file, frames_per_second)

    # Save the output with a timestamp
    file_bytime = time.strftime("%Y%m%d-%H%M%S") + ".mp4"
    shutil.copy(output_mp4_file, "static/overlay_zooms/main/" + file_bytime)
    video_url = url_for("static", filename="overlay_zooms/main/" + file_bytime)

    # Copy the video to a temporary directory
    dst = "static/temp_exp/vopt.mp4"
    src = output_mp4_file
    shutil.copy(src, dst)

    return render_template("upload.html", video_url=video_url, video_type="main")


# Route to concatenate title and main videos
@app.route("/concatenate_videos")
def concatenate_videos_route():
    # Paths to the title and main videos
    title_video = "static/overlay_zooms/title/title_video.mp4"
    main_video = "static/overlay_zooms/main/main_video.mp4"

    # Check if both videos exist
    if not os.path.exists(title_video) or not os.path.exists(main_video):
        return "Both title and main videos must exist to concatenate."

    # Load video clips
    title_clip = VideoFileClip(title_video)
    main_clip = VideoFileClip(main_video)

    # Ensure both videos are resized to 512x768
    desired_resolution = (512, 768)
    title_clip = title_clip.resize(desired_resolution)
    main_clip = main_clip.resize(desired_resolution)

    # Concatenate the clips
    final_clip = concatenate_videoclips([title_clip, main_clip])

    # Prepare the output directory and file path
    output_dir = "static/overlay_zooms/final"
    output_file = os.path.join(output_dir, "final_video.mp4")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write the final video to a file
    final_clip.write_videofile(output_file, codec="libx264", fps=30)

    # Save a timestamped copy of the final video
    file_bytime = time.strftime("%Y%m%d-%H%M%S") + ".mp4"
    shutil.copy(output_file, os.path.join(output_dir, file_bytime))

    # Generate URL for the video
    video_url = url_for("static", filename=f"overlay_zooms/final/{file_bytime}")

    # Copy the final video to the temp_exp directory
    shutil.copy(output_file, "static/temp_exp/finalX.mp4")

    # Redirect to another route after completion
    return redirect(url_for("mk_videos"))


def zoom_effect(bg_file, fg_file):
    # Open background and foreground images, convert them to RGBA for transparency
    bg = Image.open(bg_file).convert("RGBA")
    fg = Image.open(fg_file).convert("RGBA")

    # Get size of the background image
    SIZE = bg.size

    # Resize background and foreground images to the same size for consistency
    bg = bg.resize(SIZE, resample=Image.Resampling.LANCZOS)
    fg = fg.resize(SIZE, resample=Image.Resampling.LANCZOS)

    result_images = []

    # Generate zoom effect by resizing the foreground progressively
    for i in range(200):
        # Calculate progressive size scaling for foreground
        size = (int(fg.width * (i + 1) / 200), int(fg.height * (i + 1) / 200))

        # Resize foreground with progressive zoom
        fg_resized = fg.resize(size, resample=Image.Resampling.LANCZOS)

        # Apply gradual transparency (alpha) to foreground
        fg_resized.putalpha(int((i + 1) * 255 / 200))

        # Create a copy of the background image to composite the foreground onto
        result = bg.copy()

        # Calculate position to center the resized foreground
        x = int((bg.width - fg_resized.width) / 2)
        y = int((bg.height - fg_resized.height) / 2)

        # Alpha composite the resized foreground onto the background
        result.alpha_composite(fg_resized, (x, y))

        # Add the result to the list of images
        result_images.append(result)

    return result_images


# Function to create MP4 from images (unchanged)
def create_mp4_from_images(images_list, output_file, fps):
    # latest change
    # images_list = sorted(images_list, key=lambda x: os.path.getctime(os.path.join('static/novel_images', x)), reverse=True)
    image_arrays = [np.array(image) for image in images_list]
    clip = ImageSequenceClip(image_arrays, fps=fps)
    clip.write_videofile(output_file, codec="libx264", fps=fps)
    shutil.copy(output_file, "static/temp_exp/resized_titleX.mp4")


@app.route("/archive_images")
def archive_images_route():
    source_dir = os.path.join("static", "masks")
    dest_dir = os.path.join("static", "archived-images/")

    # Ensure the destination directory exists
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Copy each image from source to destination
    for filename in os.listdir(source_dir):
        if filename.endswith(".jpg") or filename.endswith(
            ".png"
        ):  # Adjust extensions as needed
            src_file = os.path.join(source_dir, filename)
            dest_file = os.path.join(dest_dir, filename)
            shutil.copy(src_file, dest_file)

    return redirect(url_for("select_images"))  # Redirect to an appropriate page


@app.route("/view_masks")
def view_masks():
    masks = glob.glob("static/masks/*.jpg")
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)
    return render_template("view_masks.html", mask_data=mask_data)


@app.route("/delete_mask", methods=["POST", "GET"])
def delete_mask():
    mask_path = request.form.get("mask_path")
    if mask_path:
        try:
            os.remove(mask_path)
            print(f"Deleted mask: {mask_path}")
        except Exception as e:
            print(f"Error deleting mask: {e}")
    return redirect(url_for("view_masks"))


# Paths


@app.route("/concat_videos")
def concat_videos():
    # Define the file paths
    output_file = "static/temp_exp/OUTPUT_PATHX.mp4"
    title_path = "static/temp_exp/resized_title.mp4"
    main_path = "static/temp_exp/resized_main.mp4"
    #recent change jan7
    mp3_directory = "static/mp3"
    mp3_dir = "static/mp3"    

    # Check if input files exist
    if not os.path.exists(title_path):
        print(f"Error: Title video '{title_path}' not found.")
        return "Title video not found", 400
    if not os.path.exists(main_path):
        print(f"Error: Main video '{main_path}' not found.")
        return "Main video not found", 400

    # Pick a random MP3 file from static/mp3s directory
    try:
        mp3_files = [f for f in os.listdir(mp3_directory) if f.endswith(".mp3")]
        if not mp3_files:
            print("No MP3 files found in 'static/mp3s'.")
            return "No MP3 files available", 400
        random_mp3 = os.path.join(mp3_directory, random.choice(mp3_files))
        print(f"Selected random MP3: {random_mp3}")
    except Exception as e:
        print(f"Error selecting random MP3: {e}")
        return f"Error selecting MP3: {e}", 500

    # Construct the ffmpeg command with audio
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "info",  # Enable FFmpeg print for debugging
        "-i",
        title_path,
        "-i",
        main_path,
        "-i",
        random_mp3,  # Add the randomly selected MP3
        "-filter_complex",
        "[0:v][1:v]concat=n=2:v=1:a=0[outv]",
        "-map",
        "[outv]",  # Video output stream
        "-map",
        "2:a",  # Map the audio from the random MP3
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-shortest",  # Use shortest flag to end when either video or audio finishes
        "-y",
        output_file,  # Output file
    ]

    # Execute the command
    try:
        subprocess.run(command, check=True)
        print("Video concatenation and audio addition successful!")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during concatenation: {e}")
        return f"Error during concatenation: {e}", 500

    return redirect(url_for("mk_videos"))


def bak(filename):
    try:
        # Get the current date and time
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        # make static/backup/ if not exists
        if not os.path.exists("static/backup"):
            os.makedirs("static/backup")
        backup = glob.glob("static/backup/backup*.py")
        # if len backup > 8   delete the oldest
        if len(backup) > 8:
            backup.sort()
            os.remove(backup[0])
        # Generate a backup filename with the timestamp
        backup_filename = f"static/backup/backup_{timestamp}.py"

        # Copy the file to the new backup filename
        shutil.copy(filename, backup_filename)

        print(f"File '{filename}' successfully backed up as '{backup_filename}'.")
    except Exception as e:
        print(f"An error occurred while backing up the file: {e}")


@app.route("/moviepy")
def moviepy_route():
    return render_template("moviepy_info.html")


@app.route("/flask_info")
def flask_info_route():
    return render_template("flask_info.html")


@app.route("/moviepy_fx_info")
def moviepy_fx_route():
    return render_template("moviepy_fx.html")


@app.route("/PIL_info")
def PIL_info_route():
    return render_template("PIL_info.html")


@app.route("/crop_image")
def select_image():
    images = os.listdir(app.config["UPLOADFOLDER"])
    return render_template("viewing_page.html", images=images)


# Route for processing the image (crop, resize, sharpen)
@app.route("/processimage", methods=["POST"])
def processimage():
    try:
        image_file = request.form["image_file"]
        x1 = int(request.form["x1"])
        y1 = int(request.form["y1"])
        x2 = int(request.form["x2"])
        y2 = int(request.form["y2"])

        img_path = os.path.join(app.config["UPLOADFOLDER"], image_file)
        img = cv2.imread(img_path)

        print(f"Image {image_file} loaded successfully")

        # Crop the image
        cropped_img = img[y1:y2, x1:x2]
        print(f"Image cropped: Upper-Left ({x1}, {y1}), Lower-Right ({x2}, {y2})")

        # Resize to 512x768
        resized_img = cv2.resize(cropped_img, (512, 768))
        print("Image resized to 512x768")

        # Sharpen the image using a kernel
        sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened_img = cv2.filter2D(resized_img, -1, sharpen_kernel)
        print("Image sharpened")

        # Save the processed image temporarily for viewing
        processed_image_name = f"processed_{image_file}"
        processed_img_path = os.path.join(
            app.config["ARCHIVED_RESOURCES"], processed_image_name
        )
        cv2.imwrite(processed_img_path, sharpened_img)

        print(f"Processed image saved temporarily as {processed_image_name}")

        return render_template(
            "viewing_page.html",
            processed_image=processed_image_name,
            images=os.listdir(app.config["UPLOADFOLDER"]),
        )

    except Exception as e:
        print(f"Error processing image: {e}")
        return redirect(url_for("select_image"))


# Route for saving the processed image permanently
@app.route("/saveimage", methods=["POST"])
def saveimage():
    try:
        processed_image = request.form["image_file"]
        processed_img_path = os.path.join(
            app.config["ARCHIVED_RESOURCES"], processed_image
        )

        # Move the processed image to final storage if necessary
        # For now, it's already in the `archived_resources` folder

        print(f"Image {processed_image} saved successfully")

        return redirect(url_for("select_image"))

    except Exception as e:
        print(f"Error saving image: {e}")
        return redirect(url_for("select_image"))


@app.route("/fadem")
def fadem():
    subprocess.run([sys.executable, "fadem"], check=True)
    return redirect(url_for("mk_videos"))


# Helper functions
def ensure_dir_exists(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        print(f"Directory created: {dir_name}")
    else:
        print(f"Directory already exists: {dir_name}")


@app.route("/all_code")
def all_code():
    return render_template("all_code.html")


@app.route("/all_html")
def all_html():
    return render_template("all_html.html")


VIDEO_DIR = "static/temp_exp"


@app.route("/view_videos")
def view_videos():
    # List all videos from the temp-exp folder
    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]
    # videos = sorted(videos, key=os.path.getmtime, reverse=True)
    return render_template("view_video.html", videos=videos)


@app.route("/concatenate_novel", methods=["POST"])
def concatenate_novel():
    try:
        # Get the selected videos from the form
        video1_filename = request.form.get("video1")
        video2_filename = request.form.get("video2")

        if not video1_filename or not video2_filename:
            return "Please select two videos", 400

        # Full paths for the selected videos
        # video1_path = os.path.join(VIDEO_DIR, video1_filename)
        # video2_path = os.path.join(VIDEO_DIR, video2_filename)

        video1_path = video1_filename
        video2_path = video2_filename
        resize_video(video1_path, "static/temp_exp/resized_video1.mp4")
        resize_video(video2_path, "static/temp_exp/resized_video2.mp4")
        concatenate_videos(
            "static/temp_exp/resized_video1.mp4",
            "static/temp_exp/resized_video2.mp4",
            "static/temp_exp/novel_concatenationX.mp4",
        )
        # Redirect back to view_video.html with the result
        shutil.copy(
            "static/temp_exp/novel_concatenationX.mp4",
            "static/novel_images/novel_concatenation.mp4",
        )
        return redirect(url_for("view_videos"))

    except Exception as e:
        return f"Error: {str(e)}", 500


def resize_video(input_file, output_file, width=512, height=768):
    """
    Resizes and pads a video to the target resolution (512x768) while maintaining aspect ratio.
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                input_file,
                "-vf",
                f"scale={width}:-1,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-c:a",
                "copy",
                "-y",
                output_file,
            ],
            check=True,
        )
        print(f"Resized and padded {input_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error resizing video {input_file}: {e}")


def concatenate_videos(video1, video2, output_file):
    """
    Concatenates two videos sequentially with audio using ffmpeg.
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                video1,
                "-i",
                video2,
                "-filter_complex",
                "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1",
                "-y",
                output_file,
            ],
            check=True,
        )
        print(f"Concatenated videos saved as {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error concatenating videos: {e}")


@app.route("/concatenatem", methods=["POST"])
def concatenatem():
    try:
        # Get the selected videos from the form
        video1_filename = request.form.get("video1")
        video2_filename = request.form.get("video2")

        if not video1_filename or not video2_filename:
            return "Please select two videos", 400

        # Full paths for the selected videos
        video1_path = os.path.join(VIDEO_DIR, video1_filename)
        video2_path = os.path.join(VIDEO_DIR, video2_filename)

        # Load the video files using MoviePy
        video1 = VideoFileClip(video1_path)
        video2 = VideoFileClip(video2_path)

        # Concatenate the video clips
        final_clip = concatenate_videoclips([video1, video2], method="compose")

        # Save the concatenated video back to the temp-exp directory
        output_filename = "concatenated_video.mp4"
        output_path = os.path.join(VIDEO_DIR, output_filename)
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        # run ffmpeg command to fix video
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                output_path,
                "-c:a",
                "copy",
                "-y",
                "static/temp_exp/concatenated_videoX.mp4",
            ],
            check=True,
        )
        # Close video files to free resources
        video1.close()
        video2.close()

        # Redirect back to view_video.html with the result
        return redirect(url_for("view_videos"))

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/add_border")
def add_border():
    images = [
        f
        for f in os.listdir("static/archived_resources/")
        if os.path.isfile(os.path.join("static/archived_resources/", f))
    ]
    thumbnails = []
    for image in images:
        with Image.open("static/archived_resources/" + image) as img:
            img.thumbnail((200, 200))
            thumbnail_name = "thumbnail_" + image
            img.save("static/thumbnails/" + thumbnail_name)
            thumbnails.append(thumbnail_name)
    return render_template("add_border.html", images=images, thumbnails=thumbnails)


@app.route("/select_border")
def select_border():
    borders = os.listdir("static/transparent_borders/")
    return render_template("select_border.html", borders=borders)


@app.route("/apply_border", methods=["POST", "GET"])
def apply_border():
    if not os.path.exists("archived_resources"):
        os.makedirs("archived_resources")
    selected_image = request.form["image"]
    selected_border = request.form["border"]
    try:
        with Image.open("static/archived_resources/" + selected_image) as img:
            with Image.open("static/transparent_borders/" + selected_border) as border:
                img = img.resize(border.size)
                img.paste(border, (0, 0), border)
                final_image_name = "final_" + selected_image
                img.save("static/final_images/" + final_image_name)
        return render_template(
            "final_image.html",
            final_image=final_image_name,
            message="Border applied successfully.",
        )
    except Exception as e:
        error_message = f"An error occurred: {str(e)}. Please try again."
        return render_template(
            "apply_border.html",
            image=selected_image,
            border=selected_border,
            error_message=error_message,
        )


@app.route("/select_border_image", methods=["GET"])
def select_border_image():
    try:
        image = request.args.get("image")
        if not image:
            raise ValueError("No image selected.")
        return render_template(
            "select_border.html",
            image=image,
            borders=os.listdir("static/transparent_borders/"),
        )
    except Exception as e:
        error_message = f"An error occurred: {str(e)}. Please try again."
        return render_template("add_border.html", error_message=error_message)


# Route for creating a text file and converting it to MP3


@app.route("/create_text_file", methods=["GET", "POST"])
def create_text_file():
    if request.method == "POST":
        print("Received request to create a text file.")
        # Get the text content from the textarea
        text_content = request.form.get("textarea_content")
        print(f"Text content for file: {text_content}")

        # Create the file path
        text_file_path = os.path.join("static/new_video", "text_file.txt")

        # Write the text content to the file
        with open(text_file_path, "w") as file:
            file.write(text_content)
        print(f"Text file created at {text_file_path}")

        return render_template("text_file_created.html", text_file_path=text_file_path)

    return render_template("create_text_file.html")


# Path to store MP3 files
MP3_DIR = "static/mp3s/"


@app.route("/text_mp3", methods=["GET", "POST"])
def text_mp3():
    if request.method == "POST":
        print("Received POST request.")

        # Get the text from the form
        text = request.form["text"]
        print(f"Text received: {text}")

        # Preserve original text and clean it up for filenames
        text0 = text
        text_clean = text.replace(" ", "")
        print(f"Cleaned text (no spaces): {text_clean}")

        # Create filenames for the MP3 and text files
        filename = MP3_DIR + text_clean[:25] + ".mp3"
        textname = "static/text/" + text_clean[:25] + ".txt"
        print(f"Generated MP3 filename: {filename}")
        print(f"Generated text file name: {textname}")

        # Save the text to a file
        with open(textname, "w") as f:
            f.write(text0)
        print(f"Text saved to {textname}")

        # Convert text to MP3 using gTTS
        tts = gTTS(text=text0)
        tts.save(filename)
        print(f"MP3 file saved as {filename}")

        # Copy the MP3 file to a temporary location
        shutil.copy(filename, "static/TEMP.mp3")
        print("MP3 file copied to static/TEMP.mp3")

        # Play the MP3 using pygame (optional, comment out if not needed)
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        print("Playing MP3 audio...")

        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
        print("Finished playing MP3, pygame exited.")

        # Return the text and list of MP3s to the template
        return render_template(
            "text_mp3.html", text=text0, filename=filename, mp3_list=get_mp3_list()
        )

    # GET request: Render form with the list of existing MP3 files
    print("Rendering form with list of existing MP3 files.")
    return render_template("text_mp3.html", mp3_list=get_mp3_list())


# Route to play an MP3 selected by the user
@app.route("/play_mp3/<filename>")
def play_mp3(filename):
    # Render the template to play the selected MP3
    return render_template("play_mp3.html", filename=filename)


# Helper function to list all MP3s in the directory
def get_mp3_list():
    mp3_list = [f for f in os.listdir(MP3_DIR) if f.endswith(".mp3")]
    # mp3_list = glob.glob(MP3_DIR+'*.mp3')
    mp3_list = sorted(mp3_list, key=os.path.getmtime, reverse=True)
    return mp3_list


@app.route("/add_audio", methods=["POST"])
def add_audio():
    # Get the video and audio file paths from the form
    video = request.form["video"]
    audio = request.form["audio"]

    # Define the full paths to the video and audio files
    video_path = os.path.join("static/temp_exp", video)
    audio_path = os.path.join("static/mp3", audio)

    # Call function to add the audio to the video
    output_path = add_sound_to_video(video_path, audio_path)

    # Redirect to the play_video route to show the combined video
    return redirect(url_for("play_video", filename=os.path.basename(output_path)))


def add_sound_to_video(video_path, audio_path):
    # Load the video clip
    video_clip = VideoFileClip(video_path)

    # Load the audio clip
    audio_clip = AudioFileClip(audio_path)

    # Set the audio for the video
    video_with_audio = video_clip.set_audio(audio_clip)

    # Define the output path for the new video
    output_path = video_path.replace(".mp4", "_audio.mp4")

    # Write the video with audio to a new file
    video_with_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_path


# redundent
@app.route("/combinez", methods=["POST"])
def combinez_video_audio():
    image_file = request.form.get("image_path")
    audio_file = request.form.get("audio_path")
    logit("line 3821")
    if not image_file or not audio_file:
        logit("No image or audio file selected")
        return jsonify({"error": "No image or audio selected"}), 400

    logit(f"Selected image: {image_file}")
    logit(f"Selected audio: {audio_file}")

    # Construct full paths for the image and audio
    image_path = os.path.join("static/archived_resources", image_file)
    audio_path = os.path.join("static/mp3s", audio_file)

    # Generate output filename
    output_filename = (
        f"output_{image_file.rsplit('.', 1)[0]}_{audio_file.rsplit('.', 1)[0]}.mp4"
    )
    output_path = os.path.join("static/temp_exp", output_filename)

    try:
        logit(f"Processing image: {image_path} and audio: {audio_path}")

        # Create video from image and audio
        output_path = add_sound_to_image(image_path, audio_path)
        if output_path:
            return jsonify({"success": True, "output_video": output_path})
        else:
            return jsonify({"error": " 3961"}), 500

    except Exception as e:
        logit(f"Error processing video and audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/add_sound_image", methods=["GET"])
def render_add_sound_form():
    # Get list of audio and image files
    audio_files = [f for f in os.listdir("static/mp3s") if f.endswith(".mp3")]
    image_files = [
        f
        for f in os.listdir("static/archived_resources")
        if f.endswith((".png", ".jpg"))
    ]
    random.shuffle(image_files)
    image_files = image_files[:50]  # Limit to 50 images
    return render_template(
        "sound_to_image.html", audio_files=audio_files, image_files=image_files
    )


@app.route("/add_sound_square", methods=["GET"])
def render_add_sound_square_form():
    # Get list of audio and image files
    audio_files = [f for f in os.listdir("static/output") if f.endswith(".mp3")]
    # sort audio by date reversed
    audio_files.sort(
        key=lambda x: os.path.getmtime(os.path.join("static/output", x)), reverse=True
    )
    image_files = [
        f for f in os.listdir("static/square") if f.endswith((".png", ".jpg"))
    ]
    random.shuffle(image_files)
    image_files = image_files[:50]  # Limit to 50 images
    return render_template(
        "sound_to_square.html", audio_files=audio_files, image_files=image_files
    )


@app.route("/play_video/<filename>")
def play_video(filename):
    # This route will display the newly generated video
    return render_template("play_video.html", video_file=filename)


# Global variable to store the process ID of the running FFmpeg process
ffmpeg_pid = None

# Define the path for your video output directory
video_output_dir = "static/videos/"


@app.route("/start_ffmpeg", methods=["POST", "GET"])
def start_ffmpeg():
    global ffmpeg_pid
    try:
        # Define the FFmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-hide_banner",
            "-f",
            "pulse",
            "-i",
            "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor",
            "-f",
            "x11grab",
            "-framerate",
            "30",
            "-video_size",
            "1366x760",
            "-i",
            ":0.0",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-strict",
            "-2",
            "-g",
            "120",
            "-f",
            "flv",
            "-y",
            f"{video_output_dir}$(date +'%Y-%m-%d_%H-%M-%S')_video3.flv",
        ]

        # Start the FFmpeg process
        process = subprocess.Popen(ffmpeg_cmd)
        ffmpeg_pid = process.pid

        # print.debug(f"Started FFmpeg process with PID: {ffmpeg_pid}")
        return jsonify({"message": "FFmpeg started", "pid": ffmpeg_pid}), 200
    except Exception as e:
        # print.error(f"Error starting FFmpeg: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/stop_ffmpeg", methods=["POST", "GET"])
def stop_ffmpeg():
    global ffmpeg_pid
    if ffmpeg_pid:
        try:
            # Stop the FFmpeg process using the stored PID
            os.kill(ffmpeg_pid, signal.SIGTERM)
            # print.info(f"Stopped FFmpeg process with PID: {ffmpeg_pid}")
            ffmpeg_pid = None  # Reset PID
            return jsonify({"message": "FFmpeg stopped"}), 200
        except Exception as e:
            # print.error(f"Error stopping FFmpeg: {str(e)}")
            return jsonify({"error": str(e)}), 500
    else:
        # print.warning("No FFmpeg process is running")
        return jsonify({"message": "No FFmpeg process to stop"}), 400


# Directories
CONTENT_DIR = "static/archived_resources"
STYLE_DIR = "static/style_resources"
RESULT_DIR = "static/novel_resources"

if not os.path.exists(CONTENT_DIR):
    os.makedirs(CONTENT_DIR)
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
if not os.path.exists(STYLE_DIR):
    os.makedirs(STYLE_DIR)

# hub_model = hub.load("http://0.0.0.0:8000/magenta_arbitrary-image-stylization-v1-256_2.tar.gz")


# Helper functions
def tensor_to_image(tensor):
    tensor = tensor * 255
    tensor = np.array(tensor, dtype=np.uint8)
    if np.ndim(tensor) > 3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return Image.fromarray(tensor)


def load_img(path_to_img):
    max_dim = 512
    img = tf.io.read_file(path_to_img)
    img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)

    shape = tf.cast(tf.shape(img)[:-1], tf.float32)
    long_dim = max(shape)
    scale = max_dim / long_dim

    new_shape = tf.cast(shape * scale, tf.int32)
    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]
    return img


@app.route("/styling", methods=["GET", "POST"])
def styling():
    if request.method == "POST":
        content_image_name = request.form["content_image"]
        style_image_name = request.form["style_image"]

        # Prepare paths
        content_path = os.path.join(CONTENT_DIR, content_image_name)
        style_path = os.path.join(STYLE_DIR, style_image_name)

        # Load content and style images
        content_image = load_img(content_path)
        style_image = load_img(style_path)

        # Stylize the image
        stylized_image = hub_model(
            tf.constant(content_image), tf.constant(style_image)
        )[0]
        result_image = tensor_to_image(stylized_image)

        # Save the result image
        timestr = time.strftime("%Y%m%d-%H%M%S")
        result_filename = f"Result_{timestr}.jpg"
        result_path = os.path.join(RESULT_DIR, result_filename)
        tempfile = "static/archived_resources/tmp_result.jpg"
        result_image.save(tempfile)
        convert_to_mellow_colors(tempfile)
        shutil.copy(tempfile, result_path)
        # copy to a uuid file in static/novel_resources
        uid = str(uuid.uuid4())
        shutil.copy(tempfile, f"static/novel_resources/{uid}.jpg")
        return render_template(
            "styling.html",
            content_images=os.listdir(CONTENT_DIR)[0:20],
            style_images=os.listdir(STYLE_DIR)[0:20],
            result_image=tempfile,
        )

    # List content and style images
    content_images = os.listdir(CONTENT_DIR)
    style_images = os.listdir(STYLE_DIR)
    # shuffle the images
    random.shuffle(content_images)
    random.shuffle(style_images)
    # display only 20 images
    content_images = content_images[:20]
    style_images = style_images[:20]
    return render_template(
        "styling.html", content_images=content_images, style_images=style_images
    )


# Define the 9 colors
palette = {
    "red": [255, 0, 0],
    "green": [0, 255, 0],
    "blue": [0, 0, 255],
    "cyan": [0, 255, 255],
    "magenta": [255, 0, 255],
    "yellow": [255, 255, 0],
    "black": [0, 0, 0],
    "white": [255, 255, 255],
    "gray": [128, 128, 128],
}


# Convert a pixel to the closest color in the palette
def closest_color(pixel):
    distances = {}
    for color_name, color_value in palette.items():
        distance = np.linalg.norm(np.array(pixel) - np.array(color_value))
        distances[color_name] = distance
    closest = min(distances, key=distances.get)
    return palette[closest]


def convert_to_mellow_colors(image_path):
    # Open the image
    image = Image.open(image_path)

    # Step 1: Enhance the saturation moderately (factor 1.5)
    enhancer = ImageEnhance.Color(image)
    enhanced_image = enhancer.enhance(1.5)

    # Step 2: Convert to RGB if not already
    enhanced_image = enhanced_image.convert("RGB")

    # Step 3: Convert to numpy array for manipulation
    img_array = np.array(enhanced_image)

    # Step 4: Apply color mapping (map each pixel to the closest color in our 9-color palette)
    mellow_image = np.apply_along_axis(closest_color, 2, img_array)

    # Step 5: Convert back to an image
    result_image = Image.fromarray(np.uint8(mellow_image))

    # Step 6: Save the result image with uuid
    uid = str(uuid.uuid4())
    output_uid = f"static/archived_resources/{uid}_output_primary_colors.jpg"
    outputuid = f"static/novel_images/{uid}_output_primary_colors.jpg"
    output_path = "static/archived_resources/enhanced.jpg"
    result_image.save(output_path)
    shutil.copy(output_path, output_uid)
    shutil.copy(output_path, outputuid)
    print(f"Saved output to: {output_path}")
    return output_uid


# Define the static directories
STATIC_FOLDER = "static"
ARCHIVE_FOLDER = os.path.join(STATIC_FOLDER, "archived_resources")

# Ensure the archive folder exists
if not os.path.exists(ARCHIVE_FOLDER):
    os.makedirs(ARCHIVE_FOLDER)


@app.route("/copy")
def copy():
    # List directories under static folder (except archived_resources)
    directories = [
        d
        for d in os.listdir(STATIC_FOLDER)
        if os.path.isdir(os.path.join(STATIC_FOLDER, d))
        and d != "archived_resources"
        and d.strip().endswith("resources")  # Ensure trailing spaces are removed
    ]
    # sort the directories
    print(f"Directories: {directories}")
    # sorted by creation reversed order
    directories.sort(
        key=lambda x: os.path.getctime(os.path.join(STATIC_FOLDER, x)), reverse=True
    )
    static_gallery_data = load_static_gallery_data()
    if not static_gallery_data:
        print("No static gallery data found. Creating new static gallery data.")
        scan_data = load_scan_data()
        gallery_data = select_random_images(scan_data)
        static_gallery_data = copy_images_to_static(gallery_data)
        save_static_gallery_data(static_gallery_data)
        videos_data, corrupt_videos = scan_videos()
    return render_template(
        "copy.html",
        directories=directories,
        resources=resource_images(),
        data=static_gallery_data,
    )
    # return render_template('copy.html', directories=directories, resources=resource_images(),data=static_gallery_data,videos=videos_data, corrupt_videos=corrupt_videos)


@app.route("/view_images", methods=["POST"])
def view_images():
    # Get selected directory from the form
    selected_dir = request.form.get("directory")
    directory_path = os.path.join(STATIC_FOLDER, selected_dir)

    # List image files in the selected directory (only common image formats)
    images = [
        f
        for f in os.listdir(directory_path)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
    ]
    # shuffle and display only 20 images
    random.shuffle(images)
    images = images[:20]
    return render_template(
        "display_directories.html", images=images, selected_dir=selected_dir
    )


@app.route("/copy_image", methods=["POST"])
def copy_image():
    # Get selected images and directory from the form
    selected_images = request.form.getlist("selected_images")
    selected_dir = request.form.get("selected_dir")

    source_dir = os.path.join(STATIC_FOLDER, selected_dir)

    # Copy each selected image to the archive folder
    for image in selected_images:
        source_path = os.path.join(source_dir, image)
        destination_path = "static/archived_resources/" + image
        print(f"Copying {image} to {destination_path}")
        shutil.copy2(source_path, destination_path)

    return redirect(url_for("copy"))


def is_server_running(port):
    """Check if there is a process listening on the specified port."""
    for proc in psutil.process_iter(["pid", "name", "connections"]):
        try:
            # Check if 'connections' is available
            if proc.info["connections"] is not None:
                for conn in proc.info["connections"]:
                    if conn.laddr.port == port:
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Handle cases where the process has terminated or access is denied
            continue
    return False


def start_tensorflow_server():
    # TensorFlow exterior model server disabled for clean standalone deployment
    pass


# Paths to video and audio directories
VIDEO_DIR = "static/temp_exp"
AUDIO_DIR = "static/audio_mp3"
OUTPUT_DIR = "static/output_videos"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)  # Create the output directory if it doesn't exist


@app.route("/sound_2_video")
def sound_2_video():
    print("Serving main page with video and audio files")

    # Get video and audio file lists
    video_files = os.listdir(VIDEO_DIR)
    audio_files = os.listdir(AUDIO_DIR)

    # Filter only supported video/audio files (e.g., .mp4 and .mp3)
    video_files = [f for f in video_files if f.endswith(".mp4")]
    audio_files = [f for f in audio_files if f.endswith(".mp3")]

    print(f"Found video files: {video_files}")
    print(f"Found audio files: {audio_files}")

    return render_template(
        "sound_to_video.html", video_files=video_files, audio_files=audio_files
    )


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)


# Path to the uploads and output folders
# UPLOAD_FOLDER = 'static/uploads/'
# OUTPUT_FOLDER = 'static/uploads/'
logit("line 4224 recentchange: Path to the uploads and output folders")


@app.route("/video_edit")
def video_edit():
    return render_template("video_edit.html")


@app.route("/trim-video", methods=["POST"])
def trim_video():
    start_time = float(request.form["startTime"])
    end_time = float(request.form["endTime"])
    input_video = "static/video_resources/use.mp4"
    output_video = os.path.join(OUTPUT_FOLDER, "trimmed_video.mp4")

    try:
        # Log the trimming process
        print(f"Trimming video from {start_time} to {end_time}")

        # Use MoviePy to trim the video
        ffmpeg_extract_subclip(
            input_video, start_time, end_time, targetname=output_video
        )
        return redirect(url_for("video_edit"))

    except Exception as e:
        print(f"Error trimming video: {str(e)}")
        return f"Error: {str(e)}", 500


@app.route("/reverse_video", methods=["POST", "GET"])
def reverse_video():
    inc = str(random.randint(0, 99))
    input_video = "static/video_resources/forward.mp4"
    video_output_dir = "static/temp_exp"
    # Define the FFmpeg command
    _cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        f"{input_video}",
        "-vf",
        "reverse",
        "-af",
        "areverse",
        "-y",
        "static/temp_exp/reverse.mp4",
    ]

    # Start the FFmpeg process
    subprocess.run(_cmd, check=True)
    return redirect(url_for("video_edit"))


# Define path for videos and temp export
VIDEO_DIR = os.path.join("static", "temp_exp")
TEMP_EXP_DIR = os.path.join("static", "videos")


# Function to list all video files in a directory recursively
def list_videos_recursive(directory):
    video_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(("X.mp4", "X.avi", "X.mkv")):  # Add more formats if needed
                video_files.append(os.path.join(root, file))
    return video_files


@app.route("/ffmpeg")
def ffmpeg():
    # List all videos from the static/videos/ directory
    videos = list_videos_recursive(VIDEO_DIR)
    processed_videos = os.listdir(TEMP_EXP_DIR)  # List processed videos
    return render_template(
        "ffmpeg.html", videos=videos, processed_videos=processed_videos
    )


@app.route("/process_ffmpeg", methods=["POST"])
def process_ffmpeg():
    if request.method == "POST":
        video_path = request.form["video_path"]
        start_time = request.form["start_time"]
        duration = request.form["duration"]
        output_filename = request.form["output_filename"]

        # Make sure the output filename ends with .mp4
        if not output_filename.endswith(".mp4"):
            output_filename += ".mp4"

        # Set the full path for the output file
        output_path = os.path.join(TEMP_EXP_DIR, output_filename)

        # Build the ffmpeg command
        command = [
            "ffmpeg",
            "-i",
            video_path,  # input video path
            "-ss",
            start_time,  # start time
            "-t",
            duration,  # duration
            "-c:a",
            "copy",
            "-y",  # copy codec to avoid re-encoding
            output_path,  # output video path
        ]

        # Run the ffmpeg command
        try:
            print(f"Running command: {' '.join(command)}")
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during processing: {e}")
            return f"Error during processing: {e}"

        # Redirect to the ffmpeg page to refresh the processed videos
        return redirect(url_for("ffmpeg"))


@app.route("/temp_exp/<filename>")
def send_processed_video(filename):
    return send_from_directory(TEMP_EXP_DIR, filename)


@app.route("/edit_description", methods=["GET", "POST"])
def edit_description():
    target = "templates/about.html" if os.path.exists("templates/about.html") else "templates/application_overview.html"
    with open(target, "r") as file:
        description = file.read()

    return render_template("edit_about.html", description=description)


@app.route("/save_description", methods=["POST"])
def save_description():
    # Retrieve the updated description from the form submission
    updated_description = request.form["description"]

    # Save to both about.html and application_overview.html for consistency
    for target in ["templates/about.html", "templates/application_overview.html"]:
        try:
            with open(target, "w") as file:
                file.write(updated_description)
        except Exception:
            pass
    return redirect(url_for("edit_description"))


def degrade_color(color):
    """Decreases color intensity to simulate ink fade."""
    return tuple(max(0, c - 30) for c in color)


def draw_blob(img, center, size, color):
    """Draws a blob (circle) at the specified point."""
    for _ in range(size):
        # Random offset within a small range to create irregularity
        offset_x = random.randint(-size // 2, size // 2)
        offset_y = random.randint(-size // 2, size // 2)
        blob_point = (center[0] + offset_x, center[1] + offset_y)
        if 0 <= blob_point[0] < img.size[0] and 0 <= blob_point[1] < img.size[1]:
            img.putpixel(blob_point, color)


def processr_image(seed_count, seed_max_size, imgsize=(510, 766), count=0):
    """Generates a Rorschach-style inkblot."""
    margin_h, margin_v = 60, 60
    color = (0, 0, 0)
    img = Image.new("RGB", imgsize, "white")

    for seed in range(seed_count):
        point = (
            random.randrange(0 + margin_h, imgsize[0] // 2),
            random.randrange(0 + margin_v, imgsize[1] - margin_v),
        )

        # Random blob size
        blob_size = random.randint(10, seed_max_size)
        draw_blob(img, point, blob_size, color)

    # Symmetry: Flip left half onto right half
    cropped = img.crop((0, 0, imgsize[0] // 2, imgsize[1]))
    flipped = cropped.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(flipped, (imgsize[0] // 2, 0))

    # Apply a blur to smooth the inkblot edges
    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=15))

    # Convert to grayscale and find the mean for thresholding
    im_grey = blurred_img.convert("L")
    mean = np.mean(np.array(im_grey))

    # Binarize the blurred image based on the mean threshold
    image_array = np.array(im_grey)
    binary_image = np.where(image_array > mean, 255, 0).astype(np.uint8)

    # Save the binary image
    temp_filename = "static/images/tmmmp.png"
    cv2.imwrite(temp_filename, binary_image)

    # Expand the border and save the final image
    final_filename = time.strftime("static/archived-images/GOODblots%Y%m%d%H%M%S.png")
    ImageOps.expand(Image.fromarray(binary_image), border=1, fill="white").save(
        final_filename
    )

    # Create and save the inverted image (black and white swapped)
    inverted_image = np.where(binary_image == 255, 0, 255).astype(np.uint8)
    inverted_filename = time.strftime(
        "static/archived-images/INVERTEDblots%Y%m%d%H%M%S.png"
    )
    ImageOps.expand(Image.fromarray(inverted_image), border=1, fill="black").save(
        inverted_filename
    )
    # copy blots to static/blot_resources/
    shutil.copy(final_filename, "static/blot_resources/")
    shutil.copy(inverted_filename, "static/blot_resources/")
    return final_filename, inverted_filename


@app.route("/inkblot")
def rorschach():
    ensure_dir_exists("static/images")
    ensure_dir_exists("static/blot_resources")

    # Generate the inkblots
    inkblot_images = []
    for count in range(2):  # Generate 2 inkblots as an example
        seed_count = random.randint(6, 10)
        seed_max_size = random.randint(100, 400)  # Smaller sizes to generate blobs
        final_image, inverted_image = processr_image(
            seed_count, seed_max_size, count=count
        )
        inkblot_images.append({"normal": final_image, "inverted": inverted_image})

    # Pass the image paths to the template
    return render_template("Rorschach.html", inkblot_images=inkblot_images)


def process_image(image_path):
    img = imread(image_path)
    labels = segmentation.slic(img, compactness=30, n_segments=400)
    g = future.graph.rag_mean_color(img, labels)

    def weight_boundary(graph, src, dst, n):
        default = {"weight": 0.0, "count": 0}
        count_src = graph[src].get(n, default)["count"]
        count_dst = graph[dst].get(n, default)["count"]
        weight_src = graph[src].get(n, default)["weight"]
        weight_dst = graph[dst].get(n, default)["weight"]
        count = count_src + count_dst
        return {
            "count": count,
            "weight": (count_src * weight_src + count_dst * weight_dst) / count,
        }

    def merge_boundary(graph, src, dst):
        pass

    labels2 = future.graph.merge_hierarchical(
        labels,
        g,
        thresh=0.08,
        rag_copy=False,
        in_place_merge=True,
        merge_func=merge_boundary,
        weight_func=weight_boundary,
    )

    out = color.label2rgb(labels2, img, kind="avg")

    # Save the processed image
    output_filename = os.path.join(
        app.config["UPLOAD_FOLDER"], f"processed_{time.time()}.png"
    )
    imsave(output_filename, out)
    return output_filename


@app.route("/upload_mp4_video")
def upload_mp4_video():
    return render_template("upload_mp4.html")


@app.route("/upload_mp4_f", methods=["POST"])
def upload_mp4_f():
    uploaded_file = request.files["videoFile"]
    if uploaded_file.filename != "":
        # Save the uploaded file to a directory or process it as needed
        # For example, you can save it to a specific directory:
        uploaded_file.save("static/video_resources/forward.mp4")
        #                   /' + uploaded_file.filename)
        VIDEO = "static/video_resources/forward.mp4"
        return render_template("upload_mp4.html", VIDEO=VIDEO)
    else:
        VIDEO = "static/video_resources/forward.mp4"
        return render_template("upload_mp4.html", VIDEO=VIDEO)


@app.route("/view_files")
def view_files():
    masks = glob.glob("static/temp_exp/*.mp4")
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)
    return render_template("view_files.html", videos=masks)


print("TEST LOG")


@app.route("/delete_file", methods=["POST", "GET"])
def delete_file():
    mask_path = request.form.get("mask_path")
    print(f"XXXXXXXX {mask_path}")
    if mask_path:
        try:
            os.remove(mask_path)
            print(f"Deleted mask: {mask_path}")
        except Exception as e:
            print(f"Error deleting mask: {e}")
    return redirect(url_for("view_files"))


@app.route("/notes")
def notes():
    with open("static_new/text/notes_app.txt") as f:
        text = f.read()
        # paragraph = text.split('----------')
        # search the paragraph for "uploads"

    return render_template("note_app_note.html", text=text)


# split at the line "----------" and return the second part


@app.route("/notes_index", methods=["POST", "GET"])
def notes_index():
    if request.method == "POST":
        search_term = request.form.get("search", "").strip()
        if search_term:
            with open("static_new/text/notes_app.txt", "r") as f:
                text = f.read()
                paragraphs = text.split("----------")

                # Filter paragraphs that contain the search term
                matching_paragraphs = [p for p in paragraphs if search_term in p]

            if matching_paragraphs:
                print(f"Matching Paragraphs:  {matching_paragraphs}")
                return render_template("notes_app.html", text=matching_paragraphs)
            else:
                return render_template("notes_app.html", text=["No matching results."])
        else:
            return render_template("notes_app.html", text=["Enter a search term."])

    return render_template("notes_app.html", text=[])


@app.route("/search_notes", methods=["POST", "GET"])
def search_notes():
    if request.method == "POST":
        search_term = request.form.get("search", "").strip()
        if search_term:
            with open("static_new/text/notes_app.txt", "r") as f:
                text = f.read()
                paragraphs = text.split("----------")

                # Filter paragraphs that contain the search term
                matching_paragraphs = [p for p in paragraphs if search_term in p]

            if matching_paragraphs:
                print(f"Matching Paragraphs: , {matching_paragraphs}")
                return render_template("notes_app.html", text=matching_paragraphs)
            else:
                return render_template("notes_app.html", text=["No matching results."])
        else:
            return render_template("notes_app.html", text=["Enter a search term."])

    return render_template("notes_app.html", text=[])


# Function to add ten dashes before and after the content
def format_content(content):
    separator = "----------\n"  # Define the separator
    formatted_content = (
        f"{separator}{content.strip()}"  # Add separator before the content
    )
    return formatted_content


@app.route("/append_notes", methods=["POST", "GET"])
def append_notes():
    if request.method == "POST":
        new_content = request.form.get("new_content", "").strip()
        if new_content:
            formatted_content = format_content(new_content)  # Format the content
            with open("static_new/text/notes_app.txt", "a") as f:
                f.write(formatted_content)
            render_template("notes_app.html")
        else:
            return "No content to append"

    return render_template("append_notes_app.html")


@app.route("/edit_notes", methods=["GET", "POST"])
def edit_notes():
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        write_notes(content)
        return redirect(url_for("notes"))
    else:
        text = read_notes()
        return render_template("edit_notes.html", text=text)


@app.route("/note_index", methods=["POST", "GET"])
def note_index():
    if request.method == "POST":
        search_term = request.form.get("search", "").strip()
        if search_term:
            text = read_notes()
            paragraphs = text.split("----------")

            # Filter paragraphs that contain the search term
            matching_paragraphs = [p for p in paragraphs if search_term in p]

            if matching_paragraphs:
                print(f"Matching Paragraphs: , {matching_paragraphs}")
                return render_template("notes_app.html", text=matching_paragraphs)
            else:
                return render_template("notes_app.html", text=["No matching results."])
        else:
            return render_template("notes_app.html", text=["Enter a search term."])

    return render_template("notes_app.html", text=[])


# Function to read the contents of the notes file
def read_notes():
    with open("static_new/text/notes_app.txt", "r") as f:
        return f.read()


# Image processing function


@app.route("/open_doors", methods=["GET", "POST"])
def open_doors_route():
    subprocess.run(
        [sys.executable, "open_door_directory.py"],
        check=True,
    )
    return redirect(url_for("mk_videos"))


@app.route("/three_doors", methods=["GET", "POST"])
def three_doors():
    if request.method == "POST":
        # Retrieve selected images from the form
        top_path = request.form.get("top_image")
        foreground_path = request.form.get("center_image")
        background_path = request.form.get("bottom_image")

        if not top_path or not foreground_path or not background_path:
            return (
                "Please select one top image, one center image, and one bottom image."
            )

        # Redirect to the 'slide_apart_animation' route with selected images
        return redirect(
            url_for(
                "slide_apart_animation",
                top_path=top_path,
                foreground_path=foreground_path,
                background_path=background_path,
            )
        )
    image_paths = get_image_paths()
    return render_template("three_doors.html", image_paths=image_paths)


def resize_if_needed(clip, target_size=(512, 768)):
    """Resizes the clip if it is not already the target size."""
    if clip.size != target_size:
        print(f"Image size {clip.size} is not {target_size}, resizing...")
        return clip.resize(target_size)
    print(f"Image is already the correct size: {clip.size}")
    return clip


@app.route("/slide_apart_animation", methods=["GET"])
def slide_apart_animation():
    # Retrieve the image paths passed as arguments in the URL
    top_path = request.args.get("top_path")
    foreground_path = request.args.get("foreground_path")
    background_path = request.args.get("background_path")

    # Check if the paths were passed correctly
    if not top_path or not foreground_path or not background_path:
        return "Top, foreground, and background images are required."

    print("Loading images...")

    # Load images using moviepy
    top_image = mp.ImageClip(top_path).set_duration(
        1
    )  # Show the top image for 1 second
    foreground = mp.ImageClip(foreground_path)
    background = mp.ImageClip(background_path)

    # Resize foreground and background if needed
    print("Verifying and resizing images if necessary...")
    foreground = resize_if_needed(foreground)
    background = resize_if_needed(background)

    # Split the foreground into two halves
    print("Splitting the foreground image into two halves.")
    left_half = foreground.crop(x1=0, y1=0, x2=256, y2=768)
    right_half = foreground.crop(x1=256, y1=0, x2=512, y2=768)

    # Define the sliding effect
    def make_frame(t):
        slide_distance = min(
            256, int(256 * t / 3)
        )  # Adjust slide distance according to time

        # Create a blank frame (RGB format)
        frame = np.zeros((768, 512, 3), dtype=np.uint8)

        # Add background image to the frame
        frame[:, :, :] = background.get_frame(t)

        # Add the left sliding half
        if slide_distance < 256:
            left_part_width = 256 - slide_distance
            frame[:, :left_part_width] = left_half.get_frame(t)[:, slide_distance:256]

        # Add the right sliding half
        if slide_distance < 256:
            right_part_width = 256 + slide_distance
            frame[:, right_part_width:] = right_half.get_frame(t)[
                :, : 256 - slide_distance
            ]

        return frame

    # Create a video clip from the frames generated by make_frame
    print("Creating the animation...")
    animation = mp.VideoClip(make_frame, duration=3)

    # Now concatenate the title image and the sliding animation
    print("Concatenating the title image and the animation...")

    # Concatenate the top image and the sliding animation
    final_clip = mp.concatenate_videoclips([top_image, animation])

    # Optionally write the output video file
    final_clip.write_videofile("static/temp_exp/slide_apart_with_titleX.mp4", fps=24)

    return redirect(url_for("mk_videos"))


@app.route("/square_transition", methods=["GET", "POST"])
def square_transition_route():
    subprocess.run(
        [sys.executable, "square_transition.py"],
        check=True,
    )
    return redirect(url_for("mk_videos"))


@app.route("/circular_transition", methods=["GET", "POST"])
def circular_transition_route():
    subprocess.run(
        [sys.executable, "circular_transition.py"],
        check=True,
    )
    return redirect(url_for("mk_videos"))


# Create frames and keepers directories if they don't exist
if not os.path.exists("static/frames"):
    os.mkdir("static/frames")
if not os.path.exists("static/keepers_resourses"):
    os.mkdir("static/keepers_resourses")
if not os.path.exists("static/music"):
    os.mkdir("static/music")

# Function to extract frames from MP4 using OpenCV
def extract_frames(video_path, output_folder):
    cap = cv2.VideoCapture(video_path)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        ic(count)
        cv2.imwrite(os.path.join(output_folder, f"frame_{count}.jpg"), frame)
        count += 1
    cap.release()


# ----------------------- VIDEO ROUTES -----------------------
def limit_backups(source_dir="static/novel_images", max_files=15):
    backup_dir = "static/backups_resources"

    # Ensure backup directory exists
    os.makedirs(backup_dir, exist_ok=True)

    # Get all files in the source directory, sorted by modification time (oldest first)
    files = sorted(
        [
            f
            for f in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, f))
        ],
        key=lambda f: os.path.getmtime(os.path.join(source_dir, f)),
    )

    # If there are more than the max allowed, move the oldest files to the backup directory
    if len(files) > max_files:
        files_to_backup = files[:-max_files]  # Select all but the last 15 files

        for file in files_to_backup:
            file_path = os.path.join(source_dir, file)
            # Create a unique backup filename with a timestamp, preserving the extension
            file_extension = os.path.splitext(file)[1]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.splitext(file)[0]}_{timestamp}{file_extension}"
            backup_file_path = os.path.join(backup_dir, backup_filename)

            # Move the file to the backup directory
            shutil.move(file_path, backup_file_path)
            print(f"Moved {file} to {backup_file_path}")


# delete images in 'static/keepers_resourses/
def keepers_resourses():
    for file in os.listdir("static/keepers_resourses"):
        file_path = os.path.join("static/keepers_resourses", file)
        if os.path.isfile(file_path):
            os.remove(file_path)


COPY_FRAMES = """<!DOCTYPE html>
<html>
<head>
    <title>Image Review and Keep</title>
    <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
        <h1>Select a Video to Process</h1>
        <a href="/">HOME</a>&nbsp;&nbsp; | &nbsp;&nbsp;
        <a href="get_frames">Choose Another Video</a>
    <form action="/process_frames" method="post">
        <label for="video">Choose a video:</label>
        <select name="video" id="video">
            {% for video in video_files %}
                <option value="{{ video }}">{{ video }}</option>
            {% endfor %}
        </select>
        <br><br>
        <input type="submit" value="Process Video">
    </form>
    <h1>Review and Keep Images</h1>
    <form action="/add_frames" method="post">
        {% for frame in frames %}
            <div style="display: inline-block; text-align: center; margin: 10px;">
                <img src="{{ url_for('static', filename='frames/' + frame) }}" width="200">
                <br>
                <input type="checkbox" name="image" value="{{ frame }}"> Keep
            </div>
        {% endfor %}
        <br><br>
        <input type="submit" value="Keep Selected Images">
    </form>
</body>
</html>
"""


# Function to extract frames from MP4 using OpenCV
def extract_frames(video_path, output_folder):
    cap = cv2.VideoCapture(video_path)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(os.path.join(output_folder, f"frame_{count}.jpg"), frame)
        count += 1
    cap.release()


# Route to display video selection and form submission
@app.route("/get_frames", methods=["GET", "POST"])
def get_frames():
    delete_frames()
    video_dir = "/media/jack/9930-14E11/ProductionWareHouse/DOCKER/static/videos"
    keepers_resourses()
    # Use glob to find all .mp4 files in the directory
    video_files = glob.glob(os.path.join(video_dir, "*.mp4"))
    # sort the files by modification time
    video_files = sorted(video_files, key=os.path.getmtime, reverse=True)
    # Get only the filenames (basename)
    video_files = [os.path.basename(video) for video in video_files]
    video_images = glob.glob("static/results/*.jpg")
    video_images = sorted(
        video_images, key=os.path.getmtime, reverse=True
    )  # post the images in reverse order
    return render_template_string(
        COPY_FRAMES, video_files=video_files, video_images=video_images
    )


# Route to handle form submission and extract frames from the selected video
@app.route("/process_frames", methods=["POST"])
def process_frames():
    # Get selected video from form in COPY_FRAMES
    video_filename = request.form.get("video")
    # This is the location of the archive videos
    video_dir = "/media/jack/9930-14E11/ProductionWareHouse/DOCKER/static/videos"
    video_path = os.path.join(video_dir, video_filename)
    output_folder = "static/frames"

    # Clear frames folder before extracting new frames
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Extract frames from the selected video
    extract_frames(video_path, output_folder)

    # List all frames in the frames directory
    frames = os.listdir(output_folder)
    return render_template_string(COPY_FRAMES, frames=frames)


def limit_backups(source_dir="static/archived_images", max_files=45):
    backup_dir = "static/backups_resources"

    # Ensure backup directory exists
    os.makedirs(backup_dir, exist_ok=True)

    # Get all files in the source directory, sorted by modification time (oldest first)
    files = sorted(
        [
            f
            for f in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, f))
        ],
        key=lambda f: os.path.getmtime(os.path.join(source_dir, f)),
    )

    # If there are more than the max allowed, move the oldest files to the backup directory
    if len(files) > max_files:
        files_to_backup = files[:-max_files]  # Select all but the last 15 files

        for file in files_to_backup:
            file_path = os.path.join(source_dir, file)
            # Create a unique backup filename with a timestamp, preserving the extension
            file_extension = os.path.splitext(file)[1]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.splitext(file)[0]}_{timestamp}{file_extension}"
            backup_file_path = os.path.join(backup_dir, backup_filename)

            # Move the file to the backup directory
            shutil.move(file_path, backup_file_path)
            print(f"Moved {file} to {backup_file_path}")


"""
# Route to handle form submission for image deletion
@app.route('/add_frames', methods=['POST', 'GET'])
def add_frames_route():
    selected_images = request.form.getlist('image')
    for image in selected_images:
        id_ = str(uuid.uuid4())
        source = os.path.join('static/frames', image)
        destination1 = os.path.join('static/results', id_ + image)
        shutil.copy(source, destination1)
        destination2 = os.path.join('static/projects', id_ + image)
        shutil.copy(source, destination2)
        #destination3 = os.path.join('static/archived-images', id_ + image)
        #shutil.copy(source, destination3)
        #destination4 = os.path.join('static/archived-images', id_ + image)
        #shutil.copy(source, destination4)
    limit_backups(source_dir='static/archived-images',max_files=60)
    limit_backups(source_dir = 'static/archived-images')            
    return redirect(url_for('get_frames'))
"""


# Function to delete all files in 'static/frames/'
def delete_frames():
    frames_dir = "static/frames"
    for file in os.listdir(frames_dir):
        file_path = os.path.join(frames_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


# Route to handle form submission for image deletion
@app.route("/add_frames", methods=["POST", "GET"])
def add_frames():
    selected_images = request.form.getlist("image")
    for image in selected_images:
        id_ = str(uuid.uuid4())
        source = os.path.join("static/frames", image)
        destination1 = os.path.join("static/keepers_resourses", id_ + image)
        shutil.copy(source, destination1)
        destination2 = os.path.join("static/archived-images", id_ + image)
        shutil.copy(source, destination2)
        destination3 = os.path.join("static/novel_images", id_ + image)
        shutil.copy(source, destination3)
        destination4 = os.path.join("static/novel_images", id_ + image)
        shutil.copy(source, destination4)
    limit_backups(source_dir="static/novel_images", max_files=40)
    limit_backups(source_dir="static/novel_images")
    return redirect(url_for("get_frames"))


# ----------------------- END VIDEO ROUTES -----------------------
# ----------------------- SEARCH ROUTES -----------------------
# Define the directory where your templates are stored
TEMPLATE_FOLDER = "templates"


@app.route("/search_templates", methods=["GET", "POST"])
def search_templates_route():
    results = []
    search_term = ""

    if request.method == "POST":
        search_term = request.form.get("search_term", "").strip().lower()
        if search_term:
            # Search through all the HTML files in the template folder
            for root, dirs, files in os.walk(TEMPLATE_FOLDER):
                for file in files:
                    if file.endswith(".html"):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r") as f:
                            content = (
                                f.read().lower()
                            )  # Convert content to lowercase to ignore case
                            if search_term in content:
                                # Find lines that contain the search term
                                matching_lines = [
                                    line
                                    for line in content.splitlines()
                                    if search_term in line
                                ]
                                results.append(
                                    {"file": file, "matches": matching_lines}
                                )

    return render_template(
        "search_templates.html", search_term=search_term, results=results
    )


AUDIO_DIR_A = "static/mp3s"
IMAGE_DIR_A = "static/archived_resources"
OUTPUT_DIR_A = "static/temp_exp"


@app.route("/render_avatar_sound", methods=["GET"])
def render_avatar_sound_form():
    return redirect(url_for("upload_media"))


@app.route("/mk_avatar", methods=["POST"])
def mk_avatar_route():
    # Get the image and audio file paths from the form data
    image_file = request.form.get("image_path")  # Name of the select field in the form
    audio_file = request.form.get("audio")  # Name of the select field in the form

    if image_file and audio_file:
        # Construct full paths
        image_path = os.path.join(IMAGE_DIR_A, image_file)
        if os.path.exists(os.path.join("static/voice", audio_file)):
            audio_path = os.path.join("static/voice", audio_file)
        else:
            audio_path = os.path.join(AUDIO_DIR_A, audio_file)

        # Ensure static/projects is populated for makeavatar
        os.makedirs("static/projects", exist_ok=True)
        try:
            from PIL import Image
            im = Image.open(image_path).convert("RGB")
            im = im.resize((512, 768), resample=Image.LANCZOS)
            im.save("static/projects/use.jpg", "JPEG", quality=95)
        except Exception:
            shutil.copy(image_path, "static/projects/use.jpg")
        shutil.copy(audio_path, "static/projects/use.mp3")

        # Also copy to legacy sample_data dir
        dest_dir = os.path.join("static", "Wav2Lip-master", "sample_data")
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy(image_path, os.path.join(dest_dir, "use.jpg"))
        shutil.copy(audio_path, os.path.join(dest_dir, "use.mp3"))

        # Process the image and audio to create a video
        output_path = add_sound_to_avatar(image_path, audio_path)

        if output_path:
            # Generate a unique ID for the output file
            uid = str(uuid.uuid4())
            final_output_path = f"{OUTPUT_DIR_A}/{uid}_avatar.mp4"

            shutil.copy(output_path, final_output_path)
            # cp otput to the static folder static/temp_exp/temp_avatar.mp4
            shutil.copy(output_path, "static/temp_exp/temp_avatar.mp4")
            return redirect(url_for("render_avatar_sound_form"))
            # return render_template('sound_to_avatar.html', video=final_output_path)
            # return render_template('mk_avatar.html', video=final_output_path)
        else:
            return "Error creating video 4958", 500
    else:
        return "Missing image or audio path", 400


def add_sound_to_avatar(image_path, audio_path):
    try:
        # Load the image and create an ImageClip
        image_clip = ImageClip(image_path)

        # Load the audio clip
        audio_clip = AudioFileClip(audio_path)

        # Get the duration of the audio clip
        audio_duration = audio_clip.duration

        # Set the duration for the image clip (max duration 45 seconds)
        final_duration = min(audio_duration, 45)
        image_clip = image_clip.set_duration(final_duration)

        # Set the frames per second (fps) for the image clip
        image_clip.fps = 24

        # Set the audio to the image clip
        video_clip = image_clip.set_audio(audio_clip)

        # Define output path for the video
        output_path = image_path.replace(".jpg", "_avatar.mp4").replace(
            ".png", "_avatar.mp4"
        )

        # Write the video with audio to a new file
        video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        return output_path
    except Exception as e:
        print(f"Error creating video 4991: {e}")
        return None


# run Wav2Lip avatar generation
@app.route("/makeit")
def makeit():
    subprocess.run(
        [sys.executable, "static/Wav2Lip-master/makeavatar"],
        check=True,
    )
    return redirect(url_for("render_avatar_sound_form"))


@app.route("/create_avatar", methods=["GET", "POST"])
def create_avatar():
    return redirect(url_for("upload_media"))


# Paths
square_folder = "static/square"
temp_folder = "static/temp_512x512"
video_folder = "static/videos"
audio_file = "static/voice/ALL_VOICE.mp3"
video_output = os.path.join(video_folder, "515x768.mp4")

# Ensure necessary directories exist
os.makedirs(temp_folder, exist_ok=True)
os.makedirs(video_folder, exist_ok=True)
os.makedirs(square_folder, exist_ok=True)
os.makedirs(square_folder, exist_ok=True)
audiofiles = "static/voice"
os.makedirs(audiofiles, exist_ok=True)


# Step 1: Resize images to 512x512
def resize_square_images():
    # for filename in os.listdir(square_folder):
    for filename in os.listdir("static/square"):
        if filename.endswith((".jpg", ".png")):
            img_path = os.path.join("static/square", filename)
            img = Image.open(img_path).convert("RGB")
            img = img.resize((512, 512), resample=Image.Resampling.LANCZOS)
            output_path = os.path.join(
                "static/temp_512x512", os.path.splitext(filename)[0] + ".jpg"
            )
            img.save(output_path, "JPEG")


# Step 2: Create a long image from selected images
def create_long_image(selected_images):
    logit("Creating long image from selected images...")
    long_image_height = 0
    images = []
    # sort images alphabetically reversed
    selected_images = sorted(selected_images, reverse=True)
    # Load images and calculate total height
    for image in selected_images:
        img_path = os.path.join(temp_folder, image)
        img = Image.open(img_path)
        images.append(img)
        long_image_height += img.height

    # Create a new long image
    long_image = Image.new("RGB", (512, long_image_height))

    # Paste each image into the long image
    current_height = 0
    for img in images:
        long_image.paste(img, (0, current_height))
        current_height += img.height

    long_image_path = os.path.join(temp_folder, "long_image.jpg")
    long_image.save(long_image_path)
    logit(f"Long image created: {long_image_path}")
    return long_image_path


# Step 3: Create scrolling video from the long image
# def create_video(long_image_path, duration=45.0):
def make_scrolling_videos(
    image_path, output_video_path, video_duration=45, video_size=(512, 768)
):
    """Creates a video by scrolling across the image vertically."""

    print(f"Loading image from {image_path}")

    image = ImageClip(image_path)

    # Check if the image dimensions are valid
    if image.size[0] != video_size[0]:
        print("Error: Image width must be equal to the video width.")
        return

    # Function to create a scrolling effect vertically
    def scroll_func(get_frame, t):
        # Calculate the y position for scrolling
        y = int((image.size[1] - video_size[1]) * t / video_duration)
        return get_frame(t)[y : y + video_size[1], 0 : video_size[0]]

    # Create the video clip with the scrolling effect
    video = VideoClip(
        lambda t: scroll_func(image.get_frame, t), duration=video_duration
    )
    video = video.set_fps(24)

    print(f"Saving video to {output_video_path}")
    video.write_videofile(output_video_path, codec="libx264", audio=False)
    # copy the video to the static static/temp_exp/515x768X.mp4
    shutil.copy(output_video_path, "static/temp_exp/512x768X.mp4")
    # copy with unique uuid to static/Videos
    uid = str(uuid.uuid4())
    final_output_path = f"{video_folder}/{uid}_512x768X.mp4"
    shutil.copy(output_video_path, final_output_path)
    video_path = "static/temp_exp/512x768X.mp4"
    Video = add_halloween_title_image(video_path, hex_color="#A52A2A")
    return Video


@app.route("/square_images")
def square_images():
    resize_square_images()
    images = os.listdir("static/temp_512x512")
    # list by date reverse
    images = sorted(images, reverse=True)
    return render_template("512x512.html", images=images)


@app.route("/create_square_video", methods=["POST"])
def create_square_video():
    selected_images = request.form.getlist("images")
    duration = request.form.get("speed", 45.0)  # Default duration is 20 seconds
    logit(f"Selected images: {selected_images}")
    logit(f"Video duration set to: {duration} seconds")

    if selected_images:
        # Create a long vertical image and then a video from it
        long_image_path = create_long_image(selected_images)
        output_video_path = os.path.join(video_folder, "515x768.mp4")
        duration = float(duration)
        image_path = long_image_path
        make_scrolling_videos(
            image_path, output_video_path, video_duration=duration
        )  # Corrected line

    return render_template(
        "512x512.html", images=os.listdir(temp_folder), video_filename="515x768.mp4"
    )


@app.route("/vertical_square")
def vertical_square():
    return render_template("512x512.html")


@app.route("/static/temp_512x512/<filename>")
def serve_image(filename):
    return send_from_directory(temp_folder, filename)


# square_zoomy_route subprocess bash square_zoomy4
@app.route("/square_zoomy", methods=["GET", "POST"])
def square_zoomy_route():
    subprocess.run(["/bin/bash", "square_zoomY4"], check=True)
    return redirect(url_for("mk_videos"))


# Function to generate random artist prompt selections
def generate_random_prompt():
    """Generates a random artist, media, topic, style, and media prompt."""
    Views = [
        "Birds Eye View",
        "High Angle shot",
        "Eye Level shot",
        "Low Angle shot",
        "First-Person View",
        "Over-the-Shoulder Shot",
        "Overhead shot",
        "Third-Person View",
        "Top Down View",
        "Cinematic shot",
        "Aerial View",
        "Gopro view",
        "Tracking shot",
        "crane shot",
        "fish eye view",
        "panorama 360 view",
        "Drone shot",
    ]
    Artist = [
        "Leonardo Da Vinci",
        "Rembrandt",
        "Vincent Van Gogh",
        "Claude Monet",
        "Gustav Klimt",
        "Paul Cezanne",
        "Bill Sienkiewicz",
        "Jean Giraud Moebius",
        "Caravaggio",
        "Francisco De Goya",
        "Juli Bell",
        "Boris Vallejo",
        "Frida Kahlo",
        "Salvador Dali",
        "Norman Rockwell",
        "James Abbott McNeill",
        "Bill Sienkiewicz",
        "Jean Giraud Moebius",
    ]
    Topic = [
        "Abstracted",
        "Animals",
        "Architecture",
        "Astronomy",
        "Ocean",
        "Mountains",
        "Death",
        "Buildings",
        "Forest",
        "Seashore",
        "Flowers",
        "desert",
        "beach",
        "river",
        "lake",
        "forest",
        "sea",
        "aliens",
        "wolves",
        "sunset",
        "sky",
        "waves",
        "apocalyptic textures",
        "apocalyptic",
        "dystopian",
        "jungle",
        "insects",
        "space",
    ]
    Style = [
        "Abstract Art",
        "Steampunk",
        "Grunge",
        "Art Deco",
        "Art Nouveau",
        "Baroque",
        "Cubism",
        "Expressionism",
        "Futurism",
        "Impressionism",
        "Minimalism",
        "Nordic",
        "Pop Art",
        "Post-Impressionism",
        "Realism",
        "Renaissance",
        "Surrealism",
        "Symbolism",
        "Ukiyo-e",
        "Ukiyo-e",
        "Vaporwave",
    ]
    Media = [
        "Acrylic On Canvas",
        "Charcoal",
        "Collage",
        "Crayon",
        "Emulsion",
        "Enamel",
        "Drypoint",
        "Ceramic",
        "sketch",
        "chalk",
        "watercolor",
        "pastel",
        "acrylic",
        "oil",
        "watercolor",
        "ink",
        "pastel",
        "watercolor",
        "acrylic",
        "oil",
        "alcohol ink art",
    ]

    selection = (
        random.choice(Views),
        random.choice(Artist),
        random.choice(Media),
        random.choice(Topic),
        random.choice(Style),
        random.choice(Media),
    )

    return selection


# Function to read text from a file
def load_text_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


# Function to save text to a file
def save_text_to_file(text, filename):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(text + ".\n")


# Function to save the generated prompt to a file
def save_prompt(text):
    with open("prompts1.txt", "a", encoding="utf-8") as file:
        file.write(text + ".\n")


# Route to home page for prompt generation
@app.route("/mk_prompt", methods=["GET", "POST"])
def mk_prompt_route():
    if request.method == "POST":
        # Save the user-submitted prompt to prompts.txt
        prompt_text = request.form["prompt_text"]
        save_text_to_file(prompt_text, "prompts.txt")
        return redirect(url_for("mk_prompt_route"))

    # Load text from prompts.txt
    TEXT = load_text_from_file("prompts.txt")
    prompt_model = PromptModel(text=TEXT)

    # Generate random artist prompts using your generator function
    generated_prompts = []
    for _ in range(3):
        prompt_generated = prompt_model.generate_prompt()
        generated_prompts.append(prompt_generated)

    # Define random top and bottom texts
    TOP = (
        "Graphic novel cover page top text in fancy gold 3D letters: "
        + random.choice(
            [
                '"AI Generated"',
                '"Python Prompts"',
                '"Generated Prompt"',
                '"Flask Prompts"',
                '"Machine Learning Prompts"',
            ]
        )
    )
    BOTTOM = random.choice(
        [
            '"Prompts by Python"',
            '"Prompts by AI"',
            '"Prompts by Machine Learning"',
            '"Prompts by FlaskArchitect"',
            '"Prompts by Flask"',
        ]
    )

    # Combine generated prompts into one text
    combined_text = TOP + " ".join(generated_prompts) + BOTTOM
    save_prompt(combined_text + ".\n\n")

    # Generate random prompt selection for display
    random_prompt_selection = generate_random_prompt()

    # Render the template with all data
    return render_template(
        "index_prompt_tones.html",
        top_text=TOP,
        generated_prompts=generated_prompts,
        bottom_text=BOTTOM,
        text=TEXT,
        random_prompt_selection=random_prompt_selection,
    )


# -----------------------------------------
VIDEOS_PATH = "static/output_videos"
ARCHIVES_PATH = "static/archives_results"
JSON_FILE = "videos.json"


def extract_random_frame(video_path, output_folder, num_frames=3):
    clip = VideoFileClip(video_path)
    duration = clip.duration
    frames = []

    for i in range(num_frames):
        random_time = random.uniform(0, duration)
        frame_path = os.path.join(output_folder, f"frame_{i}.jpg")
        clip.save_frame(frame_path, t=random_time)
        frames.append(frame_path)

    return frames


def scan_videos():
    corrupt_videos = []

    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f), corrupt_videos

    videos_data = {}
    video_files = glob.glob(os.path.join(VIDEOS_PATH, "*.mp4"))

    for video in video_files:
        video_name = os.path.basename(video)
        video_folder = os.path.join(ARCHIVES_PATH, video_name)
        os.makedirs(video_folder, exist_ok=True)

        try:
            # Extract 3 random frames
            frames = extract_random_frame(video, video_folder)
            videos_data[video_name] = frames
        except Exception as e:
            print(f"Error processing video {video_name}: {e}")
            corrupt_videos.append(video_name)

    # Save results in videos.json
    with open(JSON_FILE, "w") as f:
        json.dump(videos_data, f)

    return videos_data, corrupt_videos


@app.route("/review_videos")
def review_videos():
    videos_data, corrupt_videos = scan_videos()
    return render_template(
        "review_videos.html", videos=videos_data, corrupt_videos=corrupt_videos
    )


@app.route("/delete_json", methods=["POST"])
def delete_json():
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)
    return redirect(url_for("index"))


def mk_temp(data):  # Create a temporary file
    with open("tempfile.txt", "a") as inputs:
        inputs.write(data + "\n")  # Ensure each entry is on a new line


# Create the bash database and table if they don't exist
import os
import sqlite3
from icecream import ic

# --------------------------------------
# Define the directory to manage files in
ALLOWED_DIRECTORIES = {
    "static": os.path.join(BASE_DIR, "static") if "BASE_DIR" in locals() else "static",
    "templates": os.path.join(BASE_DIR, "templates") if "BASE_DIR" in locals() else "templates",
}


# Helper function to check allowed extensions
def allowed_file(filename):
    return os.path.splitext(filename)[1] in ALLOWED_EXTENSIONS


# Helper function to ensure valid directory access
def safe_join(base, *paths):
    target_path = os.path.join(base, *paths)
    abs_base = os.path.abspath(base)
    abs_target = os.path.abspath(target_path)

    # Ensure the target path is within the base directory
    if not abs_target.startswith(abs_base):
        raise ValueError(f"Access to {abs_target} is not allowed")

    return abs_target


@app.route("/file_home")
def file_home():
    """Landing page to choose directory to manage."""
    return render_template(
        "choose_directory.html", directories=ALLOWED_DIRECTORIES.keys()
    )


@app.route("/file_manager/<directory>")
def file_manager(directory):
    """List all files and directories within the chosen base directory."""
    if directory not in ALLOWED_DIRECTORIES:
        flash(f"Invalid directory: {directory}", "error")
        return redirect(url_for("file_home"))

    base_dir = ALLOWED_DIRECTORIES[directory]
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        for filename in filenames:
            if allowed_file(filename):
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, base_dir)
                files.append(relative_path)
    files.sort()
    return render_template(
        "file_manager.html", files=files, current_directory=directory
    )


@app.route("/move", methods=["POST"])
def move_file():
    """Move a file to a new location."""
    directory = request.form["directory"]
    base_dir = ALLOWED_DIRECTORIES[directory]

    src = safe_join(base_dir, request.form["src"])
    dest = safe_join(base_dir, request.form["dest"])

    try:
        if not os.path.isdir(os.path.dirname(dest)):
            flash("Destination directory does not exist.", "error")
            return redirect(url_for("file_manager", directory=directory))

        shutil.move(src, dest)
        logit(f"Moved file: {src} to {dest}")
        flash(f"Moved {os.path.basename(src)} to {dest}", "success")
    except Exception as e:
        logit(f"Failed to move file: {src} to {dest}. Error: {e}")
        flash(f"Error moving file: {e}", "error")

    return redirect(url_for("file_manager", directory=directory))


@app.route("/rename", methods=["POST"])
def rename_file():
    """Rename a file."""
    directory = request.form["directory"]
    base_dir = ALLOWED_DIRECTORIES[directory]

    src = safe_join(base_dir, request.form["src"])
    new_name = request.form["new_name"]
    dest = safe_join(base_dir, os.path.dirname(src), new_name)

    try:
        os.rename(src, dest)
        logit(f"Renamed file: {src} to {dest}")
        flash(f"Renamed {os.path.basename(src)} to {new_name}", "success")
    except Exception as e:
        logit(f"Failed to rename file: {src} to {new_name}. Error: {e}")
        flash(f"Error renaming file: {e}", "error")

    return redirect(url_for("file_manager", directory=directory))


# changed /delete to /deletem
# changed delete_file to /delete_filez
@app.route("/deletem", methods=["POST"])
def delete_filez():
    """Delete a file."""
    directory = request.form["directory"]
    base_dir = ALLOWED_DIRECTORIES[directory]

    file_to_delete = safe_join(base_dir, request.form["file"])

    try:
        if os.path.exists(file_to_delete):
            if "novel_images" in file_to_delete:
                dest = move_novel_image_to_resource_images(file_to_delete)
                logit(f"Moved novel image to resource_images: {file_to_delete} -> {dest}")
                flash(f"Moved {os.path.basename(file_to_delete)} to static/resource_images", "success")
            else:
                os.remove(file_to_delete)
                logit(f"Deleted file: {file_to_delete}")
                flash(f"Deleted {os.path.basename(file_to_delete)}", "success")
        else:
            flash(f"File {os.path.basename(file_to_delete)} not found", "error")
    except Exception as e:
        logit(f"Failed to delete/move file: {file_to_delete}. Error: {e}")
        flash(f"Error deleting/moving file: {e}", "error")

    return redirect(url_for("file_manager", directory=directory))


@app.route("/edit/<directory>/<path:filename>")
def edit_file(directory, filename):
    """Load file content for editing."""
    if directory not in ALLOWED_DIRECTORIES:
        flash(f"Invalid directory: {directory}", "error")
        return redirect(url_for("file_home"))

    base_dir = ALLOWED_DIRECTORIES[directory]
    file_path = safe_join(base_dir, filename)

    try:
        with open(file_path, "r") as file:
            content = file.read()
        return render_template(
            "filemanager_edit_file.html",
            file_content=content,
            filename=filename,
            directory=directory,
        )
    except Exception as e:
        logit(f"Failed to load file: {file_path}. Error: {e}")
        flash(f"Error loading file: {e}", "error")
        return redirect(url_for("file_manager", directory=directory))


@app.route("/save", methods=["POST"])
def save_file():
    """Save edited file content."""
    directory = request.form["directory"]
    base_dir = ALLOWED_DIRECTORIES[directory]
    filename = request.form["filename"]
    file_path = safe_join(base_dir, filename)
    new_content = request.form["file_content"]

    try:
        with open(file_path, "w") as file:
            file.write(new_content)
        logit(f"File saved: {file_path}")
        flash(f"Saved changes to {filename}", "success")
    except Exception as e:
        logit(f"Failed to save file: {file_path}. Error: {e}")
        flash(f"Error saving file: {e}", "error")

    return redirect(url_for("file_manager", directory=directory))


@app.route("/copy", methods=["POST"])
def copy_file():
    """Copy a file to a new location."""
    directory = request.form["directory"]
    base_dir = ALLOWED_DIRECTORIES[directory]

    src = safe_join(base_dir, request.form["src"])
    dest = safe_join(base_dir, request.form["dest"])

    try:
        if not os.path.isdir(os.path.dirname(dest)):
            flash("Destination directory does not exist.", "error")
            return redirect(url_for("file_manager", directory=directory))

        shutil.copy2(src, dest)  # shutil.copy2 to preserve metadata
        logit(f"Copied file: {src} to {dest}")
        flash(f"Copied {os.path.basename(src)} to {dest}", "success")
    except Exception as e:
        logit(f"Failed to copy file: {src} to {dest}. Error: {e}")
        flash(f"Error copying file: {e}", "error")

    return redirect(url_for("file_manager", directory=directory))


@app.route("/create_directory", methods=["POST"])
def create_directory():
    """Create a new directory."""
    directory = request.form["directory"]
    base_dir = ALLOWED_DIRECTORIES[directory]
    new_directory = safe_join(base_dir, request.form["new_directory"])

    try:
        os.makedirs(new_directory, exist_ok=True)
        logit(f"Created directory: {new_directory}")
        flash(f"Created new directory: {new_directory}", "success")
    except Exception as e:
        logit(f"Failed to create directory: {new_directory}. Error: {e}")
        flash(f"Error creating directory: {e}", "error")

    return redirect(url_for("file_manager", directory=directory))


@app.route("/create_file/<directory>", methods=["GET", "POST"])
def create_file(directory):
    # Logic to create a file in the specified directory
    # You might return a form in GET and handle the file creation in POST
    return f"Create file in {directory}"


# --------------------------------------


# Define paths for video and audio directories
VIDEO_DIR = "static/temp_exp"
AUDIO_DIR = "static/mp3s" if os.path.exists("static/mp3s") else "static/mp3"
OUTPUT_DIR = "static/temp_exp"

# Ensure directories exist
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Route to render the form (sound_to_video.html)
@app.route("/sound_to_video")
def sound_to_video():
    # Fetch available videos and audios from their respective directories
    os.makedirs(VIDEO_DIR, exist_ok=True)
    videos = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")])

    audio_dir = AUDIO_DIR
    if not os.path.exists(audio_dir) or not os.listdir(audio_dir):
        for candidate in ["static/mp3s", "static/mp3", "static/audio"]:
            if os.path.exists(candidate) and any(f.endswith(".mp3") for f in os.listdir(candidate)):
                audio_dir = candidate
                break
    os.makedirs(audio_dir, exist_ok=True)
    audios = sorted([f for f in os.listdir(audio_dir) if f.endswith(".mp3")])
    ic(f"videos count: {len(videos)}, audios count: {len(audios)}")
    # Render the HTML form and pass the list of videos and audios
    return render_template("soundtovideo.html", videos=videos, audios=audios)


# Route to handle combining video and audio
@app.route("/combine", methods=["POST"])
def combine_video_audio():
    # Get the video and audio file names from the form
    video = request.form.get("video")
    audio = request.form.get("audio")

    # Check if both video and audio are provided
    if not video or not audio:
        return jsonify({"error": "No video or audio selected"}), 400

    # Define full paths to the video and audio files
    video_path = os.path.join(VIDEO_DIR, video)
    audio_path = os.path.join(AUDIO_DIR, audio)
    if not os.path.exists(audio_path):
        for candidate in ["static/mp3", "static/mp3s", "static/audio"]:
            cand_path = os.path.join(candidate, audio)
            if os.path.exists(cand_path):
                audio_path = cand_path
                break

    # Ensure the video and audio files exist
    if not os.path.exists(video_path) or not os.path.exists(audio_path):
        return jsonify({"error": "Video or audio file not found"}), 404

    # Generate output filename
    output_filename = (
        f"output_{video.replace('.mp4', '')}_{audio.replace('.mp3', '')}_combined.mp4"
    )
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    output_path = os.path.join(OUTPUT_DIR, "videoX.mp4")
    shutil.copy(video_path, output_path)

    try:
        # Load the video and audio clips
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # Determine the shorter duration between video and audio, then add 1 second
        min_duration = min(video_clip.duration, audio_clip.duration) + 1

        # Ensure the new duration doesn't exceed either media's total length
        min_duration = min(min_duration, video_clip.duration, audio_clip.duration)

        # Trim the video and audio to the new duration
        video_clip = video_clip.subclip(0, min_duration)
        audio_clip = audio_clip.subclip(0, min_duration)

        # Combine the trimmed video with the trimmed audio
        video_with_audio = video_clip.set_audio(audio_clip)

        # Write the final video to the output path
        video_with_audio.write_videofile(
            output_path, codec="libx264", audio_codec="aac"
        )

        # Optionally copy to a temporary location for immediate access (if needed)
        temp_vid = os.path.join(VIDEO_DIR, "text2videoX.mp4")
        shutil.copy(output_path, temp_vid)
        VIDEODIR = "static/temp_exp"
        temp_vid = os.path.join(VIDEODIR, "text2videoX.mp4")        
        shutil.copy(output_path, temp_vid)
        # Respond with success and the temporary video path
        return jsonify({"success": True, "output_video": temp_vid})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Release resources after processing
        video_clip.close()
        audio_clip.close()


def add_sound_to_image(image_path, audio_path):
    try:
        # Log the paths for debugging
        print(f"Image Path: {image_path}")
        print(f"Audio Path: {audio_path}")

        # Create an ImageClip from the image
        image_clip = ImageClip(image_path)

        # Load the audio file
        audio_clip = AudioFileClip(audio_path)

        # Log the duration of the audio for debugging
        print(f"Audio Duration: {audio_clip.duration} seconds")

        # Set the duration of the image clip to match the audio clip duration
        image_clip = image_clip.set_duration(audio_clip.duration)

        # Set the audio to the image clip
        video_clip = image_clip.set_audio(audio_clip)

        # Define the output path for the video
        output_path = image_path.replace(".jpg", "_audio.mp4").replace(
            ".png", "_audio.mp4"
        )

        # Log the output path for debugging
        print(f"Output Video Path: {output_path}")

        # Write the final video file with an FPS (frames per second) of 24
        video_clip.write_videofile(
            output_path, codec="libx264", audio_codec="aac", fps=24
        )
        # copy to static/temp_exp/STILLX.mp4
        shutil.copy(output_path, "static/temp_exp/STILLX.mp4")

        im = Image.open(image_path).convert("RGB")
        w, h = im.size
        if w > 833:
            im = im.resize((512, 512), resample=Image.LANCZOS)
        if w == 832:
            im = im.resize((512, 768), resample=Image.LANCZOS)
        im.save("static/projects/use.jpg")
        # copy to static/projects/use.mp3
        shutil.copy(audio_path, "static/projects/use.mp3")
        subprocess.run(
            [
                sys.executable,
                "static/Wav2Lip-master/makeavatar",
            ],
            check=True,
        )

        return output_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def add_sound_to_square(image_path, audio_path):
    try:
        # Log the paths for debugging
        print(f"Image Path: {image_path}")
        print(f"Audio Path: {audio_path}")

        # Create an ImageClip from the image
        image_clip = ImageClip(image_path)

        # Load the audio file
        audio_clip = AudioFileClip(audio_path)

        # Log the duration of the audio for debugging
        print(f"Audio Duration: {audio_clip.duration} seconds")

        # Set the duration of the image clip to match the audio clip duration
        image_clip = image_clip.set_duration(audio_clip.duration)

        # Set the audio to the image clip
        video_clip = image_clip.set_audio(audio_clip)

        # Define the output path for the video
        output_path = image_path.replace(".jpg", "_audio.mp4").replace(
            ".png", "_audio.mp4"
        )

        # Log the output path for debugging
        print(f"Output Video Path: {output_path}")

        # Write the final video file with an FPS (frames per second) of 24
        video_clip.write_videofile(
            output_path, codec="libx264", audio_codec="aac", fps=24
        )
        # copy to static/temp_exp/STILLX.mp4
        shutil.copy(output_path, "static/temp_exp/halloweenX.mp4")
        vide_path = "static/temp_exp/halloweenX.mp4"
        VIDEO = add_halloween_frame(video_path, hex_color="#A52A2A")
        print(f"VIDEO_XXXXXXXX: {VIDEO}")
        im = Image.open(image_path).convert("RGB")
        im.save("static/projects/use.jpg")
        # copy to static/projects/use.mp3
        shutil.copy(audio_path, "static/projects/use.mp3")
        subprocess.run(
            [
                sys.executable,
                "static/Wav2Lip-master/makeavatar",
            ],
            check=True,
        )

        return output_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def log_memory_usage(interval=60, output_file="static/Memory_usage.info"):
    """
    Logs memory usage to a specified file at regular intervals.
    """
    while True:
        # Get current memory usage
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.used / (1024 * 1024)  # Convert to MB
        available_memory = memory_info.available / (1024 * 1024)  # Convert to MB

        log_data = (
            f"Timestamp: {datetime.datetime.now()} - "
            f"Flask App Memory Usage: {memory_usage:.2f} MB - "
            f"Available Memory: {available_memory:.2f} MB - "
            f"Total System Memory: {memory_info.total / (1024 * 1024):.2f} MB - "
            f"Percentage: {memory_info.percent}%\n"
        )

        # Log the memory usage to the file
        with open(output_file, "a") as f:
            f.write(log_data)

        print(log_data)  # Optional for console output
        time.sleep(interval)


# Define the start_memory_logger function
def start_memory_logger(interval=60, output_file="static/Memory_usage.info"):
    """
    Starts the memory logger in a separate thread to avoid blocking the main Flask thread.

    Args:
    - interval (int): Time in seconds between logging memory usage.
    - output_file (str): The file to log memory usage information.
    """
    memory_thread = threading.Thread(
        target=log_memory_usage, args=(interval, output_file)
    )
    memory_thread.daemon = (
        True  # Daemonize the thread so it stops with the main process
    )
    memory_thread.start()


# Start the memory logger when your Flask app starts
# start_memory_logger(interval=60)


# Function to plot memory usage and save with a unique filename
def plot_memory_usage(log_file="static/Memory_usage.info"):
    timestamps = []
    memory_usages = []
    available_memories = []
    total_memories = []

    # Read memory usage log
    with open(log_file, "r") as f:
        for line in f:
            if "Flask App Memory Usage" in line:
                # Example log line format:
                # "Timestamp: 2024-10-17 11:18:16.490485 - Flask App Memory Usage: 5184.33 MB - Available Memory: 6223.44 MB - Total System Memory: 11904.64 MB - Percentage: 47.7%"
                parts = line.split(" - ")
                timestamp_str = parts[0].replace("Timestamp: ", "")
                memory_usage_str = (
                    parts[1].replace("Flask App Memory Usage: ", "").replace(" MB", "")
                )
                available_memory_str = (
                    parts[2].replace("Available Memory: ", "").replace(" MB", "")
                )
                total_memory_str = (
                    parts[3].replace("Total System Memory: ", "").replace(" MB", "")
                )

                # Parse timestamp and memory usage using existing datetime import
                timestamps.append(
                    datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                )
                memory_usages.append(float(memory_usage_str))
                available_memories.append(float(available_memory_str))
                total_memories.append(float(total_memory_str))

    # Plot the data
    plt.figure(figsize=(5.12, 7.68))  # 512x768 size in inches (adjust dpi later)

    plt.plot(
        timestamps,
        memory_usages,
        marker="o",
        linestyle="-",
        color="b",
        label="Flask App Memory Usage (MB)",
    )
    plt.plot(
        timestamps,
        available_memories,
        marker="o",
        linestyle="-",
        color="g",
        label="Available Memory (MB)",
    )
    plt.plot(
        timestamps,
        total_memories,
        marker="o",
        linestyle="-",
        color="r",
        label="Total System Memory (MB)",
    )

    plt.xlabel("Timestamp")
    plt.ylabel("Memory Usage (MB)")
    plt.title("Flask App Memory Usage Over Time")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()

    # Ensure the graph directory exists
    if not os.path.exists("static/graph"):
        os.makedirs("static/graph")

    # Generate a unique filename using current timestamp
    output_image = (
        f"static/graph/graph_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )

    # Save the plot as a PNG image
    os.makedirs(
        os.path.dirname(output_image), exist_ok=True
    )  # Create directory if it doesn't exist
    plt.savefig(output_image, dpi=100)  # 512x768 at 100 DPI
    plt.close()


# Call the function to generate and save a graph with a unique name
# Function to get the most recent file from the static/graph directory
def get_latest_graph():
    graph_dir = "static/graph"
    files = [
        os.path.join(graph_dir, f) for f in os.listdir(graph_dir) if f.endswith(".png")
    ]
    if not files:
        return None  # If no files exist, return None
    latest_file = max(
        files, key=os.path.getctime
    )  # Get the file with the latest creation time
    return os.path.basename(latest_file)  # Return only the filename


# Flask route to generate the graph and display it
@app.route("/memory-graph")
def memory_graph():
    # Generate a new graph before displaying
    plot_memory_usage()

    # Find the latest graph image file
    latest_graph_image = get_latest_graph()

    # If no graph is found, handle it gracefully
    if not latest_graph_image:
        return "No graph available. Please try again after memory logging."

    # Render the template with the latest graph image
    return render_template("memory_graph.html", graph_image=latest_graph_image)


# Legacy Balacoon Route Redirects -> Kokoro TTS
@app.route("/balacoon", methods=["GET", "POST"])
def balacoon():
    flash("Voice synthesis has been upgraded to Kokoro TTS.")
    return redirect(url_for("text_to_mp3"))


@app.route("/balacoon_download/<filename>")
def balacoon_download_file(filename):
    search_dirs = [VOICE_FOLDER, "static/output", "static/text2audio5"]
    for sdir in search_dirs:
        target = os.path.join(sdir, filename)
        if os.path.exists(target):
            return send_file(target, as_attachment=True)
    return "File not found", 404


@app.route("/combine_b", methods=["POST"])
def combine_b_video_audio():
    image_file = request.form.get("image_path")
    audio_file = request.form.get("audio_path")
    print(f"Received request to combine image: {image_file} and audio: {audio_file}")

    if not image_file or not audio_file:
        print("No image or audio file selected")
        return jsonify({"error": "No image or audio selected"}), 400

    print(f"Selected image: {image_file}")
    print(f"Selected audio: {audio_file}")

    # Construct full paths for the image and audio
    # image_path = os.path.join('static/novel_images', image_file)
    # audio_path = os.path.join('static/output', audio_file)
    image_path = image_file
    audio_path = audio_file

    print(f"Image path: {image_path}")
    print(f"Audio path: {audio_path}")
    # Generate output filename
    output_filename = (
        f"output_{image_file.rsplit('.', 1)[0]}_{audio_file.rsplit('.', 1)[0]}.mp4"
    )
    output_path = os.path.join("static/output", output_filename)

    try:
        print(f"Processing image: {image_path} and audio: {audio_path}")

        # Create video from image and audio
        output_path = add_sound_to_image(image_path, audio_path)
        if output_path:
            return jsonify({"success": True, "output_video": output_path})
        else:
            return jsonify({"error": "Error creating video 5934"}), 500

    except Exception as e:
        print(f"Error processing video and audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/combine_h", methods=["POST"])
def combine_h_video_audio():
    if not os.path.exists("static/temp_image"):
        os.makedirs("static/temp_image")

    image_file = request.form.get("image_path")
    audio_file = request.form.get("audio_path")
    print(f"Received request to combine image: {image_file} and audio: {audio_file}")
    print(f"XXXXXXXXXXXX: {image_file} and audio: {audio_file}")
    if not image_file or not audio_file:
        print("No image or audio file selected")
        return jsonify({"error": "No image or audio selected"}), 400

    print(f"Selected SQUARE image: {image_file}")
    print(f"Selected SQUARE audio: {audio_file}")

    # Construct full paths for the image and audio
    image_path = os.path.join("static/square", image_file)
    audio_path = os.path.join("static/output", audio_file)

    print(f"Image square path: {image_path}")
    print(f"Audio square path: {audio_path}")
    # Generate output filename
    output_filename = (
        f"output_{image_file.rsplit('.', 1)[0]}_{audio_file.rsplit('.', 1)[0]}.mp4"
    )
    output_path = os.path.join("static/output", output_filename)

    try:
        print(f"Processing image: {image_path} and audio: {audio_path}")

        # Create video from image and audio
        output_path = add_sound_to_square(image_path, audio_path)
        if output_path:
            return jsonify({"success": True, "output_video": output_path})
        else:
            return jsonify({"error": "Error creating video 6010"}), 500

    except Exception as e:
        print(f"Error processing video and audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


def size_blur_image(image_path):
    # Open the original image
    original_image = Image.open(image_path).convert("RGB")

    # Check if the image is square
    width, height = original_image.size
    if width != height:
        print(f"Skipping {image_path}: not a square image.")
        return  # Skip non-square images

    # Create a 512x768 blurred background
    blurred_background = original_image.resize((512, 768)).filter(
        ImageFilter.GaussianBlur(radius=15)
    )

    # Create a 512x512 copy of the original image
    centered_image = original_image.resize((512, 512))

    # Paste the 512x512 centered image onto the blurred background
    x_offset = (512 - 512) // 2  # Horizontal centering
    y_offset = (768 - 512) // 2  # Vertical centering
    blurred_background.paste(centered_image, (x_offset, y_offset))
    image_save = "static/square_resources/" + os.path.basename(image_path)
    # Save the final image, overwriting the original image
    if not os.path.exists("static/square_resources"):
        os.makedirs("static/square_resources")
    blurred_background.save(image_save)
    print(f"Processed and named: {image_path}")
    return image_path


@app.route("/size_blur", methods=["POST", "GET"])
def size_blur():
    # delete 'static/square_resources/*.jpg'
    if os.path.exists("static/square_resources"):
        shutil.rmtree("static/square_resources")
    blurred = []
    image_files = glob.glob("static/square/*.jpg") + glob.glob("static/square/*.png")
    for image_path in image_files:
        image_file = size_blur_image(image_path)
        blurred.append(image_file)
    print(blurred)
    print(image_files)
    print(f"Blurred: {blurred}")
    print(f"Image files: {image_files}")
    if not len(blurred):
        return render_template("size_blurr.html", image_files=image_files)
    # return render_template('size_blurr.html', image_files=blurred)
    blurred_list = glob.glob("static/square_resources/*.jpg")
    return render_template("size_blurr.html", image_files=blurred_list)


def restore_to_square(image_path):
    # Open the original image
    original_image = Image.open(image_path).convert("RGB")

    # Check if the image is square
    width, height = original_image.size
    if width == height:
        print(f"Skipping {image_path}: square image.")
        return  # Skip square images

    # Create a 512x768 blurred background
    blurred_background = original_image.resize((512, 768)).filter(
        ImageFilter.GaussianBlur(radius=15)
    )

    # Create a 512x512 copy of the original image
    centered_image = original_image.resize((512, 512))

    # Paste the 512x512 centered image onto the blurred background
    x_offset = (512 - 512) // 2  # Horizontal centering
    y_offset = (768 - 512) // 2  # Vertical centering
    blurred_background.paste(centered_image, (x_offset, y_offset))
    image_path = image_path.replace(".jpg", "_restored.jpg")
    # Save the final image, overwriting the original image
    blurred_background.save(image_path)
    if not os.path.exists("static/restored_resources"):
        os.makedirs("static/restored_resources")
    shutil.copy(image_path, "static/restored_resources")
    print(f"Processed and named: {image_path}")
    return image_path


@app.route("/restore", methods=["POST", "GET"])
def restore():
    # remove the current images in "static/restored_resources/
    for f in os.listdir("static/frames"):
        os.remove(os.path.join("static/frames", f))
    blurred = []
    image_files = glob.glob("static/frames/*.jpg")
    for image_path in image_files:
        image_file = restore_to_square(image_path)
        blurred.append(image_file)
    print(blurred)
    print(image_files)
    print(f"Blurred: {blurred}")
    print(f"Image files: {image_files}")
    if not len(blurred):
        return render_template("size_blurr.html", image_files=image_files)
    # return render_template('size_blurr.html', image_files=blurred)
    blurred_list = glob.glob("static/restored_resources/*_restored.jpg")
    return render_template("size_blurr.html", image_files=blurred_list)


# def convert a webp to jpg
def convert_webp_to_jpg(image_path):
    # Open the original image
    original_image = Image.open(image_path).convert("RGB")

    # Check if the image is square
    width, height = original_image.size
    if width != height:
        print(f"Skipping {image_path}: not a square image.")
        return  # Skip non-square images

    # Convert the image to JPEG format
    converted_image = original_image.convert("RGB")


def add_halloween_frame(video_path, hex_color="#A52A2A"):
    hex_color = random.choice(
        ["#A52A2A", "#ad1f1f", "#16765c", "#7a4111", "#9b1050", "#8e215d", "#2656ca"]
    )
    # Define the directory path
    directory_path = "temp"
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
    title_image_path = "static/assets/halloween.png"
    # Set the desired size of the padded video (e.g., video width + padding, video height + padding)
    padded_size = (width + 50, height + 50)

    # Calculate the position for centering the video within the larger frame
    x_position = (padded_size[0] - video_clip.size[0]) / 2
    y_position = (padded_size[1] - video_clip.size[1]) / 2
    # hex_color = "#09723c"
    # Remove the '#' and split the hex code into R, G, and B components
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Create an RGB tuple
    rgb_tuple = (r, g, b)

    # Create a blue ColorClip as the background
    blue_background = ColorClip(padded_size, color=rgb_tuple)

    # Add the video clip on top of the red background
    padded_video_clip = CompositeVideoClip(
        [blue_background, video_clip.set_position((x_position, y_position))]
    )
    padded_video_clip = padded_video_clip.set_duration(video_clip.duration)
    # title_image_path = "/home/jack/Desktop/EXPER/static/assets/Title_Image02.png"
    # Load the title image
    title_image = ImageClip(title_image_path)

    # Set the duration of the title image
    title_duration = video_clip.duration
    title_image = title_image.set_duration(title_duration)

    print(video_clip.size)
    # Position the title image at the center and resize it to fit the video dimensions
    # title_image = title_image.set_position(("left", "top"))
    title_image = title_image.set_position((0, -5))
    # video_clip.size = (620,620)
    title_image = title_image.resize(padded_video_clip.size)

    # Position the title image at the center and resize it to fit the video dimensions
    # title_image = title_image.set_position(("center", "center")).resize(video_clip.size)

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
    # music duration is same as video
    music_clip = music_clip.set_duration(video_clip.duration)
    # Fade in and out the background music
    fade_duration = 1.0
    music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(fade_duration)
    # Set the audio of the composite clip to the background music
    composite_clip = composite_clip.set_audio(music_clip)
    uid = uuid.uuid4().hex
    output_path = "static/temp_exp/halloweenX.mp4"
    video_path = "static/temp_exp/halloweenX.mp4"

    # Export the final video with the background music
    composite_clip.write_videofile(video_path)
    mp4_file = f"static/output_videos/Ready_Post_{uid}.mp4"
    shutil.copyfile(output_path, mp4_file)
    Video = overlay_text(video_path)
    logit(Video)
    print(mp4_file)

    VIDEO = output_path
    return VIDEO


def add_halloween_title_image(video_path, hex_color="#A52A2A"):
    # Randomly select a color from a list of Halloween-themed colors
    hex_color = random.choice(
        ["#A52A2A", "#ad1f1f", "#16765c", "#7a4111", "#9b1050", "#8e215d", "#2656ca"]
    )
    logit(f"Selected hex color: {hex_color}")

    # Define the directory path
    directory_path = "temp"

    # Check if the directory exists, if not create it
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logit(f"Directory '{directory_path}' created.")
    else:
        logit(f"Directory '{directory_path}' already exists.")

    # Load the video file
    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    duration = video_clip.duration
    logit(f"Video size: {width}x{height}, Duration: {duration}s")

    # Check if the video has audio
    has_audio = video_clip.audio is not None
    if has_audio:
        logit("Video has existing audio. No external audio will be added.")
    else:
        logit("No audio detected in the video. Adding background music.")

    # Choose a random Halloween title image
    title_image_path = random.choice(glob.glob("static/assets/*halloween.png"))
    logit(f"Selected title image: {title_image_path}")

    # Define the padded size for the video with a 50px border
    padded_size = (width + 50, height + 50)

    # Calculate position to center the video within the padded area
    x_position = (padded_size[0] - width) / 2
    y_position = (padded_size[1] - height) / 2

    # Convert hex color to RGB
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    rgb_tuple = (r, g, b)

    # Create a background color clip (as a frame) with the padded size
    background_clip = ColorClip(padded_size, color=rgb_tuple)
    logit(f"Created background clip with RGB: {rgb_tuple}")

    # Overlay the video onto the background
    padded_video_clip = CompositeVideoClip(
        [background_clip, video_clip.set_position((x_position, y_position))]
    )
    padded_video_clip = padded_video_clip.set_duration(duration)

    # Load the title image and resize it to match the padded video size
    title_image = ImageClip(title_image_path).set_duration(duration).resize(padded_size)
    title_image = title_image.set_position((0, -5))

    # Composite the title image over the padded video
    composite_clip = CompositeVideoClip([padded_video_clip, title_image]).set_duration(
        duration
    )

    # If the video has no audio, add background music
    if not has_audio:
        # Load a random background music track
        mp3_files = glob.glob("static/music/*.mp3")
        if mp3_files:
            random.shuffle(mp3_files)
            mp_music = random.choice(mp3_files)
            music_clip = AudioFileClip(mp_music).set_duration(duration)

            # Add fade in and fade out to the music
            fade_duration = 1.0
            music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(
                fade_duration
            )

            # Set the composite clip's audio to the music
            composite_clip = composite_clip.set_audio(music_clip)
            logit(f"Background music added: {mp_music}")
        else:
            logit("No music files found. Skipping background audio.")

    # Generate a unique ID for the output file
    uid = uuid.uuid4().hex
    output_path = "static/temp_exp/halloweenX.mp4"
    logit(f"Output video path: {output_path}")

    # Export the final video
    composite_clip.write_videofile(output_path, codec="libx264", audio=not has_audio)

    # Copy the output file to the final destination
    mp4_file = f"static/output_videos/Ready_Post_{uid}.mp4"
    shutil.copyfile(output_path, mp4_file)
    logit(f"Final video saved to: {mp4_file}")

    return mp4_file


def delete_non_X_mp4_files(directory_path):
    # Get all the .mp4 files in the directory
    mp4_files = (
        glob.glob(os.path.join(directory_path, "*.mp4"))
        + glob.glob(os.path.join(directory_path, "*.wav"))
        + glob.glob(os.path.join(directory_path, "*.mp3"))
    )

    for file_path in mp4_files:
        # Get the filename from the file path
        filename = os.path.basename(file_path)

        # Check if the filename ends with 'X.mp4'
        if not filename.lower().endswith("x.mp4"):
            try:
                # Delete the file if it doesn't end with 'X.mp4'
                os.remove(file_path)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
        else:
            print(f"Kept: {filename}")


# Configuration for font folder
app.config["FONT_FOLDER"] = "static/fonts/"


@app.route("/merge_video_background", methods=["GET", "POST"])
def merge_video_background():
    if request.method == "POST":
        # Get the selected video and image file paths from the form
        video_filename = request.form.get("video_file")
        image_filename = request.form.get("image_file")

        if not video_filename or not image_filename:
            return "Please select both a video and an image file.", 400

        video_path = os.path.join("static/temp_exp", video_filename)
        image_path = os.path.join("static/novel_images", image_filename)

        # Check if the selected video and image files exist
        if not os.path.exists(video_path) or not os.path.exists(image_path):
            return "Video or Image file not found!", 404

        video_clip = None
        background_image = None
        composite_clip = None
        try:
            # Load the video and image using MoviePy
            video_clip = VideoFileClip(video_path).resize((512, 512))
            background_image = (
                ImageClip(image_path).set_duration(video_clip.duration).resize((512, 768))
            )

            # Position the video in the center of the background image
            x_position = (background_image.size[0] - video_clip.size[0]) / 2  # Center horizontally
            y_position = (background_image.size[1] - video_clip.size[1]) / 2  # Center vertically

            # Create a composite video with the video on top of the image background
            composite_clip = CompositeVideoClip(
                [background_image, video_clip.set_position((x_position, y_position))]
            )

            # Set the output path for the intermediate video
            intermediate_output_path = "static/temp_exp/temp_merged_videoX.mp4"
            composite_clip.write_videofile(intermediate_output_path, codec="libx264")
            logit(f"Merged video saved to: {intermediate_output_path}")

            # Call overlay_text to add random Halloween-themed text to the final video
            final_video_path = overlay_text(intermediate_output_path)

            # Serve the video file as the response
            return send_file(final_video_path, as_attachment=True)
        finally:
            if video_clip:
                video_clip.close()
            if background_image:
                background_image.close()
            if composite_clip:
                composite_clip.close()

    # On GET request, display the HTML form
    os.makedirs("static/novel_images", exist_ok=True)
    os.makedirs("static/temp_exp", exist_ok=True)
    image_files = sorted([f for f in os.listdir("static/novel_images") if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    video_files = sorted([f for f in os.listdir("static/temp_exp") if f.lower().endswith((".mp4", ".mov", ".webm"))])

    return render_template(
        "im_on_mp4.html", image_files=image_files, video_files=video_files
    )


# Function to overlay random Halloween-themed text on the video
def overlay_text(video_path):
    VIDEO = video_path
    text = random.choice(
        [
            "Spooky season vibes!",
            "Fright night fun!",
            "Witch, please!",
            "Trick or treat yourself!",
            "Boo-tifully spooky!",
            "Ghosts, ghouls, and good times!",
            "Witch way to the candy?",
            "Fangs for the memories!",
            "Eat, drink, and be scary!",
            "Creepin' it real!",
            "Bone-chilling fun!",
            "Too cute to spook!",
            "Ghouls just wanna have fun!",
            "This is where the magic happens!",
            "Spooky treats for spooky people!",
            "Resting witch face.",
            "Feeling fa-boo-lous!",
            "It's all just a bunch of hocus pocus.",
            "Boo crew on the loose!",
            "Something wicked this way comes.",
            "Monsters, witches, and bats, oh my!",
        ]
    )

    video_clip = None
    final_clip = None
    try:
        # Load the video clip
        video_clip = VideoFileClip(VIDEO)
        logit(
            f"Loaded video: {VIDEO}, Duration: {video_clip.duration} seconds, Size: {video_clip.size}"
        )

        # Set the path for the font
        font_folder = app.config.get("FONT_FOLDER", "static/fonts/")
        font_path = os.path.join(font_folder, "xkcd-script.ttf")
        if not os.path.exists(font_path):
            font_path = "DejaVu-Sans"

        # Create the text clip to overlay with custom position (20px from left, 50px down from top)
        try:
            text_clip = (
                TextClip(
                    text,
                    font=font_path,
                    fontsize=40,
                    color="yellow",
                    stroke_color="black",
                    stroke_width=2,
                )
                .set_position((20, 50))
                .set_duration(video_clip.duration)
            )
            print(f"Selected random text: '{text}'")
            final_clip = CompositeVideoClip([video_clip, text_clip])
        except Exception as e_text:
            print(f"TextClip warning: {e_text}. Falling back to video without text overlay.")
            final_clip = video_clip

        # Generate unique filename for output
        uid = uuid.uuid4().hex
        output_path = "static/temp_exp/halloween_textX.mp4"
        final_clip.write_videofile(output_path, codec="libx264")
        logit(f"Video with overlay saved to: {output_path}")

        # Define final destination for the MP4 file
        os.makedirs("static/output_videos", exist_ok=True)
        mp4_file = f"static/output_videos/Ready_Post_{uid}.mp4"
        shutil.copyfile(output_path, mp4_file)
        logit(f"Copied final video to: {mp4_file}")

        return mp4_file
    finally:
        if video_clip:
            video_clip.close()
        if final_clip and final_clip != video_clip:
            final_clip.close()


@app.route("/utilities", methods=["GET", "POST"])
def utilities():
    return render_template("utilities.html")


# Define paths for uploads
UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/png_overlay")
def png_overlay():
    # Serve the html form to select files and set the overlay options
    return render_template("png_overlay.html")


@app.route("/png_on_mp4", methods=["POST", "GET"])
def png_on_mp4():
    # Get the uploaded files and overlay parameters
    video_file = request.files["mp4"]
    png_file = request.files["png"]
    start_time = float(request.form["start_time"])
    stop_time = float(request.form["stop_time"])
    x_pos = int(request.form["x_pos"])  # Get x position from form
    y_pos = int(request.form["y_pos"])  # Get y position from form

    # Save the uploaded files to the upload folder
    video_path = os.path.join("static/uploads", video_file.filename)
    png_path = os.path.join("static/uploads", png_file.filename)
    video_file.save(video_path)
    png_file.save(png_path)

    # Load the video
    video_clip = VideoFileClip(video_path)

    # Load the PNG image and set start time and duration based on start/stop times
    png_clip = (
        ImageClip(png_path, transparent=True)
        .set_start(start_time)
        .set_duration(stop_time - start_time)
    )

    # Resize the PNG if necessary (adjust as needed)
    # png_clip = png_clip.resize(height=100)

    # Set the position of the PNG overlay using the custom x and y positions
    png_clip = png_clip.set_position((x_pos, y_pos))

    # Create a composite video with the overlay
    final_clip = CompositeVideoClip([video_clip, png_clip])

    # Output video file
    output_path = os.path.join("static", f"outputp_{video_file.filename}")
    final_clip.write_videofile(
        "static/temp_exp/png_overlayXa.mp4", codec="libx264", fps=24, audio=True
    )
    # run ffmpeg on generated file to verify
    subprocess.run(
        [
            "ffmpeg",
            "-i",
            "static/temp_exp/png_overlayXa.mp4",
            "-y",
            "static/temp_exp/png_overlayX.mp4",
        ]
    )
    # Return the output video file to the user
    video = "static/temp_exp/png_overlayX.mp4"
    return redirect(url_for("index"))  # , video=video))


@app.route("/outputp/<filename>")
def serve_output_filep(filename):
    return send_from_directory("static/outputp_", filename)


@app.route("/face_copy", methods=["GET", "POST"])
def face_copy():
    video_dir = "static/temp_exp"
    video_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]

    return render_template("face_copy.html", video_files=video_files)


@app.route("/process_face_copy", methods=["POST"])
def process_face_copy():
    source_video = request.form["source_video"]
    destination_video = request.form["destination_video"]

    source_path = os.path.join("static/videos", source_video)
    destination_path = os.path.join("static/videos", destination_video)

    logit(f"Processing face copy: {source_video} to {destination_video}")

    # Call the face detection, lipsync, and overlay functions here

    # Save the final result
    result_path = os.path.join(
        "static/projects", f"face_swap_{source_video}_to_{destination_video}.mp4"
    )

    # Assuming you have the result saved
    logit(f"Result saved at: {result_path}")

    return f"Face copied from {source_video} to {destination_video}. <br> Saved at {result_path}"


UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ------------------------------
@app.route("/green_screen_overlay", methods=["GET", "POST"])
def green_screen_overlay():
    if request.method == "POST":
        if "background" not in request.files or "greenscreen" not in request.files:
            return "Missing background or greenscreen video", 400

        background_file = request.files["background"]
        greenscreen_file = request.files["greenscreen"]

        # Save uploaded files
        background_path = os.path.join(
            app.config["UPLOAD_FOLDER"], background_file.filename
        )
        greenscreen_path = os.path.join(
            app.config["UPLOAD_FOLDER"], greenscreen_file.filename
        )
        background_file.save(background_path)
        greenscreen_file.save(greenscreen_path)

        # Load videos
        background_clip = VideoFileClip(background_path)
        greenscreen_clip = VideoFileClip(greenscreen_path)

        # Log durations
        app.logger.info(f"Background clip duration: {background_clip.duration} seconds")
        app.logger.info(
            f"Greenscreen clip duration: {greenscreen_clip.duration} seconds"
        )

        # Check if greenscreen clip exceeds background duration
        if greenscreen_clip.duration > background_clip.duration:
            app.logger.warning(
                "Trimming greenscreen clip to match background duration."
            )
            greenscreen_clip = greenscreen_clip.subclip(0, background_clip.duration)

        # Check audio availability
        if background_clip.audio is not None:
            audio_duration = background_clip.audio.duration
            app.logger.info(f"Audio clip duration: {audio_duration} seconds")

            # Ensure audio duration matches video duration
            if audio_duration > background_clip.duration:
                app.logger.warning("Trimming audio clip to match background duration.")
                background_clip.audio = background_clip.audio.subclip(
                    0, background_clip.duration
                )

        # Resize and position the greenscreen
        resize_width = int(request.form.get("resize_width", 500))
        resize_height = int(request.form.get("resize_height", 500))
        x_offset = int(request.form.get("x_offset", 0))
        y_offset = int(request.form.get("y_offset", 0))

        greenscreen_clip = greenscreen_clip.resize(
            width=resize_width, height=resize_height
        )
        greenscreen_clip = greenscreen_clip.set_position((x_offset, y_offset))

        # Apply the chroma key effect to make green transparent
        greenscreen_clip = make_transparent_greenscreen(greenscreen_clip)

        # Set the duration of the greenscreen clip to match the background clip
        greenscreen_clip = greenscreen_clip.set_duration(background_clip.duration)

        # Overlay greenscreen on background and set audio
        final_clip = CompositeVideoClip([background_clip, greenscreen_clip])

        # If the background has audio, set it to the final clip
        if background_clip.audio is not None:
            final_clip = final_clip.set_audio(background_clip.audio)

        # Save the output video
        output_path = os.path.join(app.config["UPLOAD_FOLDER"], "output.mp4")
        try:
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        except OSError as e:
            app.logger.error(f"Error during video processing: {e}")
            return str(e), 500

        # Send the output video back to the client
        return send_from_directory(
            app.config["UPLOAD_FOLDER"], "output.mp4", as_attachment=True
        )

    return render_template("green_screen.html")


def make_transparent_greenscreen(clip):
    """Apply a chroma key effect to make green pixels transparent."""

    def remove_green(get_frame, t):
        frame = get_frame(t)

        # Create a mask based on green color
        mask = (frame[:, :, 0] < 100) & (frame[:, :, 1] > 150) & (frame[:, :, 2] < 100)

        # Set green pixels to transparent (RGBA format)
        frame = np.dstack(
            (frame, np.ones((frame.shape[0], frame.shape[1]), dtype=frame.dtype) * 255)
        )  # Add alpha channel
        frame[mask] = [0, 0, 0, 0]  # Set the green pixels to transparent

        return frame

    return clip.fl(remove_green)


UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/green_screen", methods=["GET", "POST"])
def greenscreen():
    if request.method == "POST":
        greenscreen_file = request.files.get("greenscreen")
        background_file = request.files.get("background")

        # Get resize and offset parameters
        resize_width = int(request.form.get("resize_width", 300))
        resize_height = int(request.form.get("resize_height", 300))
        x_offset = int(request.form.get("x_offset", 0))
        y_offset = int(request.form.get("y_offset", 0))

        if greenscreen_file and background_file:
            greenscreen_path = os.path.join(
                app.config["UPLOAD_FOLDER"], greenscreen_file.filename
            )
            background_path = os.path.join(
                app.config["UPLOAD_FOLDER"], background_file.filename
            )

            # Save uploaded files
            greenscreen_file.save(greenscreen_path)
            background_file.save(background_path)

            output_video_path = os.path.join(UPLOAD_FOLDER, "output_video.mp4")
            process_g_video(
                greenscreen_path,
                background_path,
                output_video_path,
                resize_width,
                resize_height,
                x_offset,
                y_offset,
            )

            return render_template("green_screen2.html", output_video=output_video_path)

    return render_template("green_screen2.html")


def process_g_video(
    greenscreen_path,
    background_path,
    output_path,
    resize_width,
    resize_height,
    x_offset,
    y_offset,
):
    try:
        # Load the greenscreen video
        greenscreen_clip = VideoFileClip(greenscreen_path)
        audio_clip = greenscreen_clip.audio  # Extract audio from greenscreen video

        # Load the background video
        background_clip = VideoFileClip(background_path)

        # Resize the greenscreen video
        greenscreen_clip = greenscreen_clip.resize(
            newsize=(resize_width, resize_height)
        )

        # Create a mask for the greenscreen
        greenscreen_mask = create_green_mask(greenscreen_clip)

        # Apply the mask to the greenscreen clip
        greenscreen_clip = greenscreen_clip.set_mask(greenscreen_mask)

        # Composite the videos
        final_clip = CompositeVideoClip(
            [background_clip, greenscreen_clip.set_position((x_offset, y_offset))]
        )

        # Combine audio
        combined_audio = create_combined_audio(audio_clip, background_clip.audio)
        final_clip = final_clip.set_audio(combined_audio)

        # Write the output video
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        logit("Video processing complete, saved to: {}".format(output_path))

    except Exception as e:
        error_message = (
            f"Error processing video: {str(e)}\nTraceback: {traceback.format_exc()}"
        )
        logit(error_message)  # Log the full error with traceback


def create_combined_audio(greenscreen_audio, background_audio):
    if background_audio is not None:
        # Start background audio after greenscreen audio
        background_audio = background_audio.set_start(greenscreen_audio.duration)
        return concatenate_audioclips([greenscreen_audio, background_audio])
    return greenscreen_audio


def create_green_mask(clip):
    """
    Create a mask for the greenscreen video by isolating green colors.
    This returns a valid MoviePy mask.
    """

    def make_mask(get_frame, t):
        frame = get_frame(t)
        # Convert the frame to HSV color space
        hsv_frame = cv2.cvtColor(frame[..., :3], cv2.COLOR_RGB2HSV)

        # Define the range for the green color in HSV
        lower_green = np.array([40, 100, 100])  # Lower bound for green
        upper_green = np.array([80, 255, 255])  # Upper bound for green

        # Create a mask where green is present
        mask = cv2.inRange(hsv_frame, lower_green, upper_green)

        # Log the sum of mask pixels to check the number of detected greens
        logit(f"Mask sum at time {t}: {np.sum(mask)}")  # Log sum of mask pixels

        # Normalize to 0-1 range and ensure it's a float32 mask
        mask = mask.astype(np.float32) / 255.0

        # Invert mask: green becomes transparent, non-green becomes visible
        mask = 1 - mask

        # Return a valid MoviePy mask by wrapping the numpy array in a VideoClip
        return mask[..., np.newaxis]  # Add a channel dimension

    # Create a VideoClip for the mask
    mask_clip = clip.fl(make_mask)

    # Set the duration of the mask clip to match the original clip
    mask_clip = mask_clip.set_duration(clip.duration)

    # Mark this clip as a mask
    mask_clip.ismask = True  # Explicitly indicate that this clip is a mask

    return mask_clip


VIDEO_DIR = "static/temp_exp"
IMAGE_DIR = "static/novel_images"

# Default JSON data for animation if none is provided
default_animation_data = [
    {"zoom": 1.0, "pan": [0, 0]},
    {"zoom": 1.0, "pan": [0, 0]},
    {"zoom": 1.2, "pan": [0.1, 0.1]},
    {"zoom": 1.5, "pan": [0.2, 0.2]},
    {"zoom": 2.0, "pan": [0.4, 0.4]},
    {"zoom": 2.0, "pan": [0.4, 0.4]},
    {"zoom": 2.0, "pan": [0.4, 0.4]},
    {"zoom": 1.2, "pan": [0.1, 0.8]},
    {"zoom": 1.2, "pan": [0.1, 0.8]},
    {"zoom": 3.2, "pan": [0.1, 0.8]},
    {"zoom": 3.2, "pan": [0.1, 0.8]},
    {"zoom": 1.2, "pan": [0.1, 0.8]},
    {"zoom": 1.2, "pan": [0.1, 0.8]},
    {"zoom": 2.5, "pan": [0.6, 0.6]},
    {"zoom": 3.0, "pan": [0.8, 0.8]},
    {"zoom": 2.5, "pan": [0.6, 0.6]},
    {"zoom": 1.5, "pan": [0.2, 0.2]},
    {"zoom": 1.0, "pan": [0, 0]},
]


@app.route("/jsonzoom")
@app.route("/json_zoom")
def jsonzoom():
    # Retrieve image filenames from static/novel_images
    image_folder = "static/novel_images"
    os.makedirs(image_folder, exist_ok=True)
    images = sorted([
        file
        for file in os.listdir(image_folder)
        if file.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    # Pass default animation data as formatted JSON
    return render_template(
        "json_zoom.html",
        images=images,
        default_animation_data=json.dumps(default_animation_data, indent=2),
        video_file="static/temp_exp/final_zoomyyX.mp4",
    )


@app.route("/create_animation", methods=["POST"])
def create_animation():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload provided."}), 400
        image_name = data.get("image")
        animation_data = data.get("animation_data", [])

        if not isinstance(animation_data, list) or len(animation_data) < 2:
            return jsonify({"error": "Invalid animation data. At least 2 keyframes are required."}), 400

        # User configurable smoothness & motion parameters (default: 120 steps for half-speed slow & smooth motion)
        try:
            interpolation_steps = int(data.get("interpolation_steps", 120))
            interpolation_steps = max(15, min(interpolation_steps, 300))
        except (ValueError, TypeError):
            interpolation_steps = 120

        try:
            frame_rate = float(data.get("frame_rate", 25.0))
            frame_rate = max(10.0, min(frame_rate, 60.0))
        except (ValueError, TypeError):
            frame_rate = 25.0

        easing = str(data.get("easing", "cosine")).lower()
        if easing not in ["cosine", "smoothstep", "cubic", "linear"]:
            easing = "cosine"

        apply_border = bool(data.get("apply_border", True))

        # Paths
        os.makedirs("static/novel_images", exist_ok=True)
        os.makedirs("static/temp_exp", exist_ok=True)
        image_path = os.path.join("static", "novel_images", image_name)
        if not os.path.exists(image_path):
            return jsonify({"error": f"Image file not found: {image_name}"}), 404

        output_video_path = os.path.join("static/temp_exp", "output.mp4")

        # Create the smooth zoom and pan animation
        final_video_path = create_zoom_pan_animation(
            image_path=image_path,
            animation_data=animation_data,
            output_video_path=output_video_path,
            interpolation_steps=interpolation_steps,
            frame_rate=frame_rate,
            easing=easing,
            apply_border=apply_border,
        )

        if not final_video_path or not os.path.exists(final_video_path):
            return jsonify({"error": "Failed to generate animation video."}), 500

        web_video_path = f"/{final_video_path}" if not final_video_path.startswith("/") else final_video_path
        return jsonify(
            {
                "success": True,
                "message": f"Smooth video created ({interpolation_steps} steps/kf, {easing} easing at {int(frame_rate)} FPS)",
                "video_path": web_video_path,
            }
        )

    except Exception as e:
        print(f"Error in create_animation: {str(e)}")
        return (
            jsonify({"error": f"An error occurred while creating the animation: {str(e)}"}),
            500,
        )


def create_zoom_pan_animation(
    image_path,
    animation_data,
    output_video_path,
    interpolation_steps=120,
    frame_rate=25.0,
    easing="cosine",
    apply_border=True,
):
    import math

    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        return None

    # Get image dimensions
    original_height, original_width = image.shape[:2]

    # Set the output frame dimensions
    output_width, output_height = 512, 768

    # Video writer for mp4 format
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(
        output_video_path, fourcc, frame_rate, (output_width, output_height)
    )

    dst_pts = np.float32([
        [0, 0],
        [output_width, 0],
        [0, output_height]
    ])

    # Loop through keyframes and interpolate between them with sub-pixel precision
    for i in range(len(animation_data) - 1):
        start_frame = animation_data[i]
        end_frame = animation_data[i + 1]

        start_zoom = float(start_frame.get("zoom", 1.0))
        end_zoom = float(end_frame.get("zoom", 1.0))
        start_pan = start_frame.get("pan", [0.5, 0.5])
        end_pan = end_frame.get("pan", [0.5, 0.5])

        for step in range(interpolation_steps):
            t = step / float(interpolation_steps)

            # Apply easing curve to remove sharp corners & mechanical jerk
            if easing == "cosine":
                ease_t = (1.0 - math.cos(t * math.pi)) / 2.0
            elif easing == "smoothstep":
                ease_t = t * t * (3.0 - 2.0 * t)
            elif easing == "cubic":
                ease_t = 4.0 * t * t * t if t < 0.5 else 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0
            else:
                ease_t = t  # linear

            zoom = start_zoom + (end_zoom - start_zoom) * ease_t
            pan_x = start_pan[0] + (end_pan[0] - start_pan[0]) * ease_t
            pan_y = start_pan[1] + (end_pan[1] - start_pan[1]) * ease_t

            # Sub-pixel floating-point viewport computation (avoids integer pixel stair-stepping)
            crop_width = original_width / max(zoom, 0.001)
            crop_height = original_height / max(zoom, 0.001)

            max_x = max(0.0, original_width - crop_width)
            max_y = max(0.0, original_height - crop_height)

            x_offset = max(0.0, min(float(pan_x) * max_x, max_x))
            y_offset = max(0.0, min(float(pan_y) * max_y, max_y))

            src_pts = np.float32([
                [x_offset, y_offset],
                [x_offset + crop_width, y_offset],
                [x_offset, y_offset + crop_height]
            ])
            M = cv2.getAffineTransform(src_pts, dst_pts)
            frame = cv2.warpAffine(
                image, M, (output_width, output_height),
                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
            video_writer.write(frame)

    video_writer.release()
    print(f"Video saved successfully at {output_video_path}")

    # Sharpen frames while preserving smooth framerate and all frames (no decimation)
    sharpened_output = "static/temp_exp/sharpened_output.mp4"
    subprocess.call(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            output_video_path,
            "-vf",
            "unsharp=5:5:0.8:5:5:0.0",
            "-r",
            str(frame_rate),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-y",
            sharpened_output,
        ]
    )

    border_asset = "static/assets/zoom_pan_json_border_l.png"
    if not os.path.exists(border_asset):
        for candidate in ["static/assets/Zoom_Images.png", "static/assets/512x768_overlay.png"]:
            if os.path.exists(candidate):
                border_asset = candidate
                break

    final_video_path = os.path.join("static/temp_exp", "final_zoomyyX.mp4")
    if apply_border and os.path.exists(border_asset):
        subprocess.call(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                sharpened_output,
                "-i",
                border_asset,
                "-filter_complex",
                "[0:v]scale=w=512:h=748:force_original_aspect_ratio=decrease,pad=512:768:(512-iw)/2:(778-ih)/2[v0];"
                "[1:v][v0]overlay=15:36",
                "-r",
                str(frame_rate),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-y",
                final_video_path,
            ]
        )
    else:
        subprocess.call(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                sharpened_output,
                "-r",
                str(frame_rate),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-y",
                final_video_path,
            ]
        )

    logit(f"Final video created at: {final_video_path}")
    return final_video_path

    logit(f"Final video created at: {final_video_path}")
    return final_video_path


def stabilize_video(input_video, output_video):
    logit(f"Stabilizing video: {input_video}")
    trf_file = "transforms.trf"
    try:
        subprocess.call(
            [
                "ffmpeg",
                "-i",
                input_video,
                "-vf",
                "vidstabdetect=shakiness=5:accuracy=10",
                "-f",
                "null",
                "-",
            ]
        )
        if os.path.exists(trf_file):
            subprocess.call(
                [
                    "ffmpeg",
                    "-i",
                    input_video,
                    "-vf",
                    f"vidstabtransform=smoothing=5:input={trf_file}",
                    "-y",
                    output_video,
                ]
            )
        else:
            shutil.copyfile(input_video, output_video)
    except Exception as e:
        print(f"Warning in stabilize_video: {e}")
        shutil.copyfile(input_video, output_video)
    logit(f"Stabilized video saved at: {output_video}")


@app.route("/tinymce", methods=["GET", "POST"])
def tinymce():
    return render_template("tinymce.html")


def novel_image_paths():
    image_paths = glob.glob(
        os.path.join(app.config["NOVEL_IMAGES"], "*.png")
    ) + glob.glob(os.path.join(app.config["NOVEL_IMAGES"], "*.jpg"))
    return image_paths


@app.route("/mk_novel", methods=["GET", "POST"])
# @cache.cached(timeout=60)
def mk_novel():
    session["visited_index"] = True
    image_paths = novel_image_paths()
    return render_template("mk_novel.html", image_paths=image_paths)


# Directory containing the images
images_dir = "static/novel_images/"
output_video = "static/temp_exp/novel_video.mp4"

# Frame size and timing parameters
frame_width, frame_height = 720, 1424
static_duration = 7
slide_duration = 0.5


def create_image_frame(image1, image2):
    """Stack two images vertically to create a 1024x2048 frame."""
    clip1 = ImageClip(image1).resize((frame_width, frame_width))
    clip2 = ImageClip(image2).resize((frame_width, frame_width))
    stacked_frame = CompositeVideoClip(
        [
            clip1.set_position(("center", "top")),
            clip2.set_position(("center", "bottom")),
        ],
        size=(frame_width, frame_height),
    )
    return stacked_frame.set_duration(static_duration)


def create_sliding_transition(frames):
    """Create a sliding transition effect with delay for each frame pair."""
    video_clips = []
    for i in range(len(frames) - 1):
        # Current static frame
        current_frame = frames[i]

        # Next frame with slide-in effect
        next_frame = (
            frames[i + 1].set_start(static_duration).set_duration(slide_duration)
        )

        # Composite to show slide-up effect
        transition_clip = CompositeVideoClip(
            [
                current_frame.set_position(("center", "center")).set_duration(
                    static_duration + slide_duration
                ),
                next_frame.set_position(
                    lambda t: (
                        "center",
                        frame_height * (1 - t / slide_duration) - frame_height,
                    )
                ),  # slide in
            ],
            size=(frame_width, frame_height),
        ).set_duration(static_duration + slide_duration)

        # Add transition clip to the video sequence
        video_clips.append(transition_clip)

    # Add the last frame without transition
    video_clips.append(frames[-1].set_duration(static_duration))

    return concatenate_videoclips(video_clips, method="compose")


@app.route("/create_novel_video", methods=["POST", "GET"])
def create_novel_video():
    images = load_novel_images(images_dir)

    # Ensure an even number of images for pairing
    if len(images) % 2 != 0:
        images = images[:-1]

    # Group images into pairs and create 2-image frames
    frames = []
    for i in range(0, len(images), 2):
        frame = create_image_frame(images[i], images[i + 1])
        frames.append(frame)

    # Apply sliding transition between each frame pair
    final_video = create_sliding_transition(frames)

    # Export the final video
    final_video.write_videofile(output_video, fps=24)
    video_path = output_video
    add_title(video_path, hex_color="#A52A2A")
    return render_template(
        "mk_novel_2.html", image_paths=novel_image_paths(), video_path=video_path
    )


@app.route("/preview_novel_video", methods=["POST", "GET"])
def preview_novel_video():
    images = load_novel_images(images_dir)

    video_path = output_video

    return render_template(
        "mk_novel_2.html", images=novel_image_paths(), video_path=video_path
    )


def add_title(video_path, hex_color="#A52A2A"):
    hex_color = random.choice(
        ["#A52A2A", "#ad1f1f", "#16765c", "#7a4111", "#9b1050", "#8e215d", "#2656ca"]
    )

    # Load the video file
    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    video_duration = video_clip.duration

    # Set the desired size of the padded video (extra padding for title)
    padded_size = (width + 50, height + 50)
    title_image_path = "static/assets/720x1424.png"

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
    padded_video_clip = CompositeVideoClip(
        [background_clip, video_clip.set_position((x_position, y_position))]
    )
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
    output_path = "static/temp_exp/novel_creationX.mp4"
    composite_clip.write_videofile(output_path)
    shutil.copyfile(
        output_path, f"static/output_videos/square_mask_transitionX_{uid}.mp4"
    )
    # get basename of output_path
    bas = os.path.basename(output_path)
    video = bas
    return render_template("mk_novel_2.html", video=bas)


# ------------------------------------

app.config["DATABASE"] = "static/blog3.db"
# DATABASE = 'static/blog3.db'
app.config["DATABASE"] = "static/blog4.db"
DATABASE = "static/blog4.db"


# def allowed_file(filename):
def allowed_file(filename):
    logit(f"XXXXX__filename: {filename}")
    logit(f"filename.rsplit: {filename.rsplit('.', 1)}")
    logit(
        "'.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']"
    )
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@app.route("/upload_novel_video/<int:post_id>", methods=["POST"])
def upload_novel_video(post_id):
    if "videoFile" not in request.files:
        print("No file part")
        flash("No file part")
        return redirect(request.url)

    file = request.files["videoFile"]
    if file.filename == "":
        flash("No selected file")
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["VUPLOAD_FOLDER"], filename))
        print(f"Filename: {filename}")
        # Update the database with the filename
        update_video_filename(post_id, filename)
        flash("Video uploaded successfully")
        return redirect(url_for("post", post_id=post_id))
    else:
        flash("Allowed file types are .mp4")
        return redirect(request.url)


def list_files_by_creation_time(file_paths):
    """
    List files by their creation time, oldest first.
    Args:
    file_paths (list): List of file paths.
    Returns:
    list: List of file paths sorted by creation time.
    """
    # Log the start of the function
    print("Listing files by creation time...")
    # Create a dictionary to store file paths and their creation times
    file_creation_times = {}
    # Iterate through each file path
    for file_path in file_paths:
        # Get the creation time of the file
        try:
            creation_time = os.path.getctime(file_path)
            # Store the file path and its creation time in the dictionary
            file_creation_times[file_path] = creation_time
        except FileNotFoundError:
            # Log a warning if the file is not found
            print(f"File not found: {file_path}")
    # Sort the dictionary by creation time
    sorted_files = sorted(file_creation_times.items(), key=lambda x: x[1], reverse=True)
    # Extract the file paths from the sorted list
    sorted_file_paths = [file_path for file_path, _ in sorted_files]
    # Log the end of the function
    print("File listing complete.")
    # Return the sorted file paths
    return sorted_file_paths


def read_text_from_file(filename):
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    with open(filepath, "r") as file:
        text = file.read()
        print(f"Text read from file: {filename}")
        return text


# ----------------------------


def load_novel_images(novel_images_dir):
    """Load and sort images from the directory."""

    images = sorted(
        [
            os.path.join(images_dir, f)
            for f in os.listdir(images_dir)
            if f.endswith(".jpg")
        ]
    )

    return images


@app.route("/start_project", methods=["GET", "POST"])
def start_project():
    images = []
    novel_images_dir = glob.glob("static/novel_images/*.jpg") + glob.glob(
        "static/novel_images/*.png"
    )
    # sort the images by creation time (reversed)
    novel_images_dir = sorted(novel_images_dir, key=os.path.getctime, reverse=True)
    for image in novel_images_dir:
        images.append(os.path.basename(image))
    return render_template("start_project2.html", images=images)


# -----------------------------


def get_post(post_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, content, image, video_filename FROM post WHERE id = ? ORDER BY id DESC",
            (post_id,),
        )
        post = cursor.fetchone()
    return post


# Function to fetch all posts
def get_posts(limit=None):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        if limit:
            cursor.execute(
                "SELECT id, title, content, image, video_filename FROM post ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        else:
            cursor.execute(
                "SELECT id, title, content, image, video_filename FROM post ORDER BY id DESC"
            )
        posts = cursor.fetchall()
    return posts


def get_intro(limit=1):
    print(f"Fetching post with limit={limit}")
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            if limit:
                print("Fetching post with id = 864")
                cursor.execute(
                    "SELECT id, title, content, image, video_filename FROM post WHERE id = ?",
                    (864,),
                )
            else:
                print("Fetching all posts ordered by id DESC")
                cursor.execute(
                    "SELECT id, title, content, image, video_filename FROM post ORDER BY id DESC"
                )

            posts = cursor.fetchall()

            return posts
        except sqlite3.OperationalError as e:
            print(f"SQLite error occurred: {e}")
            raise


# Function to fetch image data
def get_image(post_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM post WHERE id = ?", (post_id,))
        post = cursor.fetchone()
        if post and post[0]:
            return post[0]  # Return base64 encoded image data
        return None


# Create the output directory if it doesn't exist
output_directory = "static/temp"
os.makedirs(output_directory, exist_ok=True)


@app.route("/mk_flipnovel", methods=["POST", "GET"])
def mk_flipnovel():
    # Set up paths
    output_directory = "static/temp"
    final_output_directory = "static/output_videos/"
    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(final_output_directory, exist_ok=True)

    # Clear temporary files
    for f in glob.glob(f"{output_directory}/*"):
        os.remove(f)

    # Load images from the directory by creation time reversed
    novel_images_dir = glob.glob("static/novel_images/*.jpg") + glob.glob(
        "static/novel_images/*.png"
    )
    image_list = sorted(novel_images_dir, key=os.path.getctime, reverse=True)
    if not image_list:
        return "Error: No images found in the input directory."

    video_paths = []

    # Generate video segments
    for i, base_image_path in enumerate(image_list[:-1]):
        try:
            base_image = Image.open(base_image_path).convert("RGBA")
            next_image_path = image_list[i + 1]
            next_image = Image.open(next_image_path).convert("RGBA")

            # Generate frames for the transition
            frames = []
            bs = (500, 766)  # Base size for resizing
            step = 10  # Step size for transition
            hold_frames = 30  # Frames to hold before transition
            delay_frames = 120  # Frames to hold after transition

            # Hold on the current image
            for _ in range(hold_frames):
                frames.append(np.array(base_image))

            # Create the flip transition
            for j in range(0, bs[0], step):
                current_frame = next_image.copy()
                resized_base_image = base_image.resize(
                    (bs[0] - j, bs[1]), Image.BICUBIC
                )
                current_frame.paste(resized_base_image, (0, 0), resized_base_image)
                frames.append(np.array(current_frame))

            # Hold on the final frame
            for _ in range(delay_frames):
                frames.append(np.array(current_frame))

            # Save the video segment
            output_video_path = os.path.join(output_directory, f"segment_{i}.mp4")
            imageio.mimsave(output_video_path, frames, fps=30)
            video_paths.append(output_video_path)
        except Exception as e:
            print(f"Error creating video for {base_image_path}: {e}")
            continue

    # Ensure at least one video segment was created
    if not video_paths:
        return "Error: No video segments were created."

    # Generate ffmpeg input list
    input_list_path = os.path.join(output_directory, "input_list.txt")
    try:
        with open(input_list_path, "w") as f:
            for video_path in video_paths:
                f.write(f"file '{os.path.abspath(video_path)}'\n")
    except Exception as e:
        return f"Error: Unable to create input list - {e}"

    # Concatenate video segments
    concatenated_video_path = os.path.join(output_directory, "final_novel_result.mp4")
    ffmpeg_command = f"ffmpeg -y -f concat -safe 0 -i {input_list_path} -c copy {concatenated_video_path}"
    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        return f"Error: ffmpeg concatenation failed - {e}"

    if not os.path.exists(concatenated_video_path):
        return "Error: Concatenation failed."

    # Move the final video
    final_output_video_path = os.path.join(
        final_output_directory, f"{uuid.uuid4()}.mp4"
    )
    shutil.copyfile(concatenated_video_path, final_output_video_path)

    # Add a title and return
    try:
        add_flip_title(final_output_video_path, hex_color="#A52A2A")
    except Exception as e:
        return f"Error adding title: {e}"

    return redirect("/start_project")


def add_flip_title(video_path, hex_color="#A52A2A"):
    directory_path = "static/temp"
    os.makedirs(directory_path, exist_ok=True)

    # Randomize background color
    hex_color = random.choice(
        ["#A52A2A", "#ad1f1f", "#16765c", "#7a4111", "#9b1050", "#8e215d", "#2656ca"]
    )
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))

    # Load the video clip
    video_clip = VideoFileClip(video_path)
    video_duration = video_clip.duration  # Use video duration to align music and video

    # Load title image
    title_image_path = "static/assets/Title_Image02.png"
    title_image = (
        ImageClip(title_image_path).resize(video_clip.size).set_duration(video_duration)
    )

    # Create a colored background
    background = ColorClip(video_clip.size, color=(r, g, b)).set_duration(
        video_duration
    )

    # Composite the video with the background and title
    composite = CompositeVideoClip(
        [
            background,
            video_clip.set_position("center"),
            title_image.set_position("center"),
        ]
    )

    # Load and set a random background music
    mp3_files = glob.glob("static/music/*.mp3")
    if not mp3_files:
        raise FileNotFoundError("No MP3 files found in the specified directory.")
    random.shuffle(mp3_files)
    mp_music = random.choice(mp3_files)
    music_clip = AudioFileClip(mp_music).subclip(
        0, min(video_duration, AudioFileClip(mp_music).duration)
    )

    # Fade in and fade out the music
    fade_duration = 1.0  # 1-second fade in/out
    music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(fade_duration)

    # Set the audio of the composite clip to the background music
    composite = composite.set_audio(music_clip)

    # Save the final video
    output_path = os.path.join("static/temp_exp", "final_flipbookX.mp4")
    composite.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_path


app.config["UPLOAD_NOVEL_IMAGES"] = "static/temp_exp"
app.config["OUTPUT_NOVEL_IMAGES"] = "static/edited_videos"
app.config["OUTPUT_NOVEL_DIR"] = "static/novel_audio_mp3"
os.makedirs(app.config["OUTPUT_NOVEL_IMAGES"], exist_ok=True)
os.makedirs(app.config["OUTPUT_NOVEL_DIR"], exist_ok=True)


@app.route("/novel_audio", methods=["POST", "GET"])
def novel_audio():
    # List available videos in the temp_exp NOVEL_IMAGES
    videos = sorted(
        [
            f
            for f in os.listdir(app.config["UPLOAD_NOVEL_IMAGES"])
            if f.endswith(".mp4")
        ],
        key=lambda x: os.path.getmtime(
            os.path.join(app.config["UPLOAD_NOVEL_IMAGES"], x)
        ),
        reverse=True,
    )
    return render_template("add_novel_audio.html", videos=videos)


@app.route("/get_video/<filename>")
def get_video(filename):
    # Serve a selected video file
    return send_from_directory(app.config["UPLOAD_NOVEL_IMAGES"], filename)


@app.route("/add_novel_audio", methods=["POST"])
def add_novel_audio():
    try:
        video_file = request.form["video_file"]
        audio_file = request.form["audio_file"]
        start_time = float(request.form["start_time"])

        video_path = os.path.join(app.config["UPLOAD_NOVEL_IMAGES"], video_file)
        audio_path = os.path.join(app.config["UPLOAD_NOVEL_IMAGES"], audio_file)

        # Create non-destructive output file path
        output_file = f"{uuid.uuid4()}_preview.mp4"
        output_path = os.path.join(app.config["OUTPUT_NOVEL_IMAGES"], output_file)

        # Load the video and audio, and set the audio timing
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path).set_start(start_time)
        video_with_audio = CompositeVideoClip([video.set_audio(audio)])

        # Write the new video with added audio to the output folder
        video_with_audio.write_videofile(
            output_path, codec="libx264", audio_codec="aac"
        )

        return jsonify({"output_url": url_for("get_video", filename=output_file)})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/novel_balacoon", methods=["GET", "POST"])
def novel_balacoon():
    flash("Novel voice synthesis has been upgraded to Kokoro TTS.")
    return redirect(url_for("text_to_mp3"))


@app.route("/combine_novel", methods=["POST"])
def combine_novel_audio():
    image_file = request.form.get("image_path")
    audio_file = request.form.get("audio_path")
    logit(f"Received request to combine image: {image_file} and audio: {audio_file}")

    if not image_file or not audio_file:
        logit("No image or audio file selected")
        return jsonify({"error": "No image or audio selected"}), 400

    logit(f"Selected image: {image_file}")
    logit(f"Selected audio: {audio_file}")

    # Construct full paths for the image and audio
    # image_path = os.path.join('static/novel_images', image_file)
    # audio_path = os.path.join('static/output', audio_file)
    image_path = image_file
    audio_path = audio_file

    logit(f"Image path: {image_path}")
    logit(f"Audio path: {audio_path}")
    # Generate output filename
    output_filename = (
        f"output_{image_file.rsplit('.', 1)[0]}_{audio_file.rsplit('.', 1)[0]}.mp4"
    )
    output_path = os.path.join("static/novel_audio_mp3", output_filename)

    try:
        logit(f"Processing image: {image_path} and audio: {audio_path}")

        # Create video from image and audio
        output_path = add_sound_to_novel_image(image_path, audio_path)
        if output_path:
            return jsonify({"success": True, "output_video": output_path})
        else:
            return jsonify({"error": "Error creating video 5934"}), 500

    except Exception as e:
        logit(f"Error processing video and audio: {str(e)}")
        return jsonify({"error": str(e)}), 700


def add_sound_to_novel_image(image_path, audio_path):
    # Define the path for the silent audio clip in MP3 format
    silence_path = "silence.mp3"

    # Check if the silent audio file exists; if not, create a 0.7-second MP3 silence
    if not os.path.exists(silence_path):
        silence = AudioSegment.silent(duration=800)  # 700 ms of silence
        silence.export(silence_path, format="mp3")

    # Load both the main audio file and the silence clip
    audio_clip = AudioFileClip(audio_path)
    silence_clip = AudioFileClip(silence_path)

    # Apply fade-out to the audio clips before concatenation using moviepy's audio_fadeout
    fade_duration = 0.6  # Fade duration in seconds
    audio_clip = afx.audio_fadeout(audio_clip, fade_duration)
    silence_clip = afx.audio_fadeout(silence_clip, fade_duration)

    # Concatenate silence before, main audio, and silence after
    combined_audio = concatenate_audioclips([silence_clip, audio_clip, silence_clip])

    # Ensure the audio duration matches the image duration exactly
    image_clip = ImageClip(image_path).set_duration(combined_audio.duration)

    # Define the output path for the combined audio in MP3 format
    combined_audio_path = audio_path.replace(".mp3", "_combined.mp3")

    # Write the combined audio to a file (ensure it's saved as MP3)
    combined_audio.write_audiofile(combined_audio_path, codec="libmp3lame")

    # Set the combined audio to the image clip
    video_clip = image_clip.set_audio(combined_audio)

    # Define the output path for the final video
    output_path = image_path.replace(".jpg", "_audio.mp4").replace(".png", "_audio.mp4")

    # Write the final video file with an FPS (frames per second) of 24
    video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

    # Copy to static/temp_exp/STILLX.mp4
    shutil.copy(output_path, "static/temp_exp/STILLX.mp4")
    im = Image.open(image_path).convert("RGB")
    w, h = im.size
    if w > 833:
        im = im.resize((512, 512), resample=Image.LANCZOS)
    if w == 832:
        im = im.resize((512, 768), resample=Image.LANCZOS)
    im.save("static/projects/use.jpg")
    # copy to static/projects/use.mp3
    shutil.copy(audio_path, "static/projects/use.mp3")
    subprocess.run(
        [
            sys.executable,
            "static/Wav2Lip-master/makeavatar",
        ],
        check=True,
    )
    return output_path


@app.route("/merge_novel_videos", methods=["GET", "POST"])
def merge_novel_videos():
    mp4_files = glob.glob("static/temp_exp/*.mp4")
    mp4_files.sort(key=os.path.getmtime, reverse=True)
    return render_template("merge_novel_videos.html", mp4_files=mp4_files)


# Directory where the videos are stored
VIDEO_DIRECTORY = "static/temp_exp"
MERGED_VIDEO_PATH = os.path.join(VIDEO_DIRECTORY, "merged_novel_videos.mp4")


@app.route("/merge_videos", methods=["POST"])
def merge_videos():
    # Retrieve selected video paths from the form
    selected_videos = request.form.getlist("selected_videos")
    # list last video by creation time
    selected_videos.sort(key=os.path.getmtime)  # , reverse=True)
    if not selected_videos:
        return redirect(url_for("merge_novel_videos"))

    try:
        # Load each selected video using moviepy
        clips = [VideoFileClip(video) for video in selected_videos]

        # Concatenate all selected videos into one
        merged_clip = concatenate_videoclips(clips, method="compose")
        merged_clip.write_videofile(MERGED_VIDEO_PATH, codec="libx264")

        # Close all video clips
        for clip in clips:
            clip.close()

    except Exception:
        return "An error occurred while merging the videos."

    # Return the merged video file as a download
    # copy to static/temp_exp/novel.mp4
    shutil.copy(MERGED_VIDEO_PATH, "static/temp_exp/novel.mp4")

    return send_file(MERGED_VIDEO_PATH, as_attachment=True)


# Route for the form
@app.route("/add_novel_text", methods=["GET", "POST"])
def add_novel_text():
    # Get the list of images in the NOVEL_IMAGES
    images = os.listdir(NOVEL_DIRECTORY)
    images = [img for img in images if img.lower().endswith((".png", ".jpg", ".jpeg"))]

    if request.method == "POST":
        image_file = request.form["image_file"]
        text = request.form["text"]
        position = (int(request.form["x_position"]), int(request.form["y_position"]))
        font_size = int(request.form["font_size"])
        color = request.form["color"]
        font_path = os.path.join(app.config["FONT_FOLDER"], "xkcd-script.ttf")
        font = ImageFont.truetype(font_path, font_size)

        # Open the image
        image_path = os.path.join("static/novel_images", image_file)
        image = Image.open(image_path)

        # Draw the text on the image
        draw = ImageDraw.Draw(image)
        draw.text(position, text, font=font, fill=color)

        # Save the temporary image for preview
        # if directory 'static/temp_image/' create
        if not os.path.exists("static/temp_image"):
            os.makedirs("static/temp_image")
        temp_image_path = os.path.join("static/temp_image", "temp-image.png")
        image = image.convert("RGB")
        image.save(temp_image_path)
        dest = os.path.join("static/novel_images", "temp-image.png")
        shutil.copy(temp_image_path, dest)
        return render_template(
            "add_novel_text.html",
            images=images,
            selected_image=image_file,
            temp_image="temp-image.png",
            text=text,
            position=position,
            font_size=font_size,
            color=color,
        )

    return render_template("add_novel_text.html", images=images)


# Route to save the final image
@app.route("/save_novel_image", methods=["POST"])
def save_novel_image():
    image_file = request.form["image_file"]
    final_text = request.form["final_text"]
    position = eval(request.form["final_position"])  # Convert string back to tuple
    font_size = int(request.form["final_font_size"])
    color = request.form["final_color"]
    font_path = os.path.join(app.config["FONT_FOLDER"], "xkcd-script.ttf")
    font = ImageFont.truetype(font_path, font_size)

    # Open the image again
    image_path = os.path.join("static/novel_images", image_file)
    image = Image.open(image_path)

    # Draw the final text on the image
    draw = ImageDraw.Draw(image)
    draw.text(position, final_text, font=font, fill=color)

    # Save the image with a unique UUID
    unique_filename = f"{uuid.uuid4()}.png"
    final_image_path = os.path.join(VIDEO_DIRECTORY, unique_filename)
    image.save(final_image_path)

    return redirect(url_for("add_text"))


# --------------------------------
# Load a default font (replace with an actual font path if available)
DEFAULT_FONT_PATH = "static/fonts/DejaVuSans-Bold.ttf"
FONT_SIZE = 24
PADDING = 10
NOVEL_DIRECTORY = "static/novel_images"


@app.route("/add_novel_caption")
def add_novel_caption():
    # Get the list of images in the NOVEL_DIRECTORY
    images = [
        img
        for img in os.listdir(NOVEL_DIRECTORY)
        if img.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    # Sort images by modification time (latest image last)
    images.sort(key=lambda img: os.path.getmtime(os.path.join(NOVEL_DIRECTORY, img)))
    dest = os.path.join("static/novel_images", "captioned.jpg")
    # `captioned_image` is now the most recently modified/added image
    return render_template(
        "add_novel_caption.html", images=images, captioned_image=dest
    )


@app.route("/add_caption", methods=["POST"])
def add_caption():
    # Get selected image and caption text
    selected_image = request.form.get("selected_image")
    caption_text = request.form["caption"]
    # Retrieve optional offset from user input; default to 20 if not provided
    offset = int(request.form.get("offset", 20))
    alpha = int(request.form.get("alpha", 155))
    if not selected_image:
        return "No image selected.", 400

    # Sanitize caption text for a valid filename
    safe_caption_text = re.sub(r"[^a-zA-Z0-9_-]", "", caption_text.replace(" ", "_"))

    # Generate new name for the captioned image (appending '_captioned' to the original name)
    base_name, ext = os.path.splitext(selected_image)
    captioned_image_name = f"{base_name}_captioned{ext}"
    output_path = os.path.join("static/novel_images", captioned_image_name)
    dest = os.path.join("static/novel_images", "captioned.jpg")

    # Open the selected image
    image_path = os.path.join(NOVEL_DIRECTORY, selected_image)
    image = Image.open(image_path).convert("RGBA")

    # Create an overlay for the caption
    text_image = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_image)
    font = ImageFont.truetype(DEFAULT_FONT_PATH, FONT_SIZE)

    # Split the caption text into lines by newline character
    lines = caption_text.splitlines()  # Split text into lines by newline

    # Calculate the width of the longest line to ensure the box is wide enough
    max_text_width = max(draw.textlength(line, font=font) for line in lines)
    line_height = FONT_SIZE + PADDING // 2  # Add space between lines
    total_text_height = line_height * len(lines)  # Total height for all lines

    # Set rectangular background width and height
    background_width = max_text_width + 2 * PADDING
    background_height = total_text_height + 2 * PADDING
    background_x = (image.width - background_width) // 2
    background_y = (
        image.height - background_height - offset
    )  # Near the bottom of the image

    # Draw white background for the caption box
    draw.rectangle(
        [
            background_x,
            background_y,
            background_x + background_width,
            background_y + background_height,
        ],
        fill=(255, 255, 255, alpha),
    )

    # Draw each line of text, ensuring that lines are centered and spaced out
    y_offset = background_y + PADDING  # Start drawing after padding
    for line in lines:
        # Get the width of the current line
        text_width = draw.textlength(line, font=font)
        text_x = background_x + (background_width - text_width) // 2  # Center each line
        draw.text((text_x, y_offset), line, font=font, fill=(0, 0, 0, 255))
        y_offset += line_height  # Move down for the next line

    # Combine captioned overlay with original image
    combined_image = Image.alpha_composite(image, text_image)

    # Save the final captioned image with a new name to avoid overwriting
    combined_image.convert("RGB").save(output_path, "JPEG")
    shutil.copy(output_path, dest)
    # create uuid for captioned image
    unique_filename = f"static/novel_images/{uuid.uuid4()}.jpg"
    shutil.copy(output_path, unique_filename)
    # Retrieve updated list of images
    images = [
        img
        for img in os.listdir(NOVEL_DIRECTORY)
        if img.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    return render_template(
        "add_novel_caption.html",
        image_path=output_path,
        images=images,
        captioned_image=dest,
    )


# --------------------------------
"""
@app.route('/view_files')
def view_files():
    masks = glob.glob('static/temp_exp/*.mp4')
    masks = sorted(masks, key=os.path.getmtime, reverse=True)
    filenames = [os.path.basename(mask) for mask in masks]
    mask_data = zip(masks, filenames)
    return render_template('view_files.html', videos=masks)
print("TEST LOG")
@app.route('/delete_file', methods=['POST', 'GET'])
def delete_file():
    mask_path = request.form.get('mask_path')
    print(f'XXXXXXXX {mask_path}')
    if mask_path:
        try:
            os.remove(mask_path)
            print(f"Deleted mask: {mask_path}")
        except Exception as e:
            print(f"Error deleting mask: {e}")
    return redirect(url_for('view_files'))

"""


# --------------------------------
@app.route("/view_novel_files")
def view_novel_files():
    # Get all image paths in sorted order (newest first)
    image_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        image_paths.extend(glob.glob(f"static/novel_images/{ext}"))
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    return render_template("view_novel_files.html", image_paths=image_paths)


@app.route("/delete_novel_file", methods=["POST"])
def delete_novel_file():
    # Retrieve all selected image paths
    selected_image_paths = request.form.getlist("image_paths[]")
    print(f"Selected images for deletion (moving to resource_images): {selected_image_paths}")

    moved_count = 0
    # Iterate and safely move each selected image to static/resource_images
    for image_path in selected_image_paths:
        try:
            if os.path.exists(image_path):
                dest = move_novel_image_to_resource_images(image_path)
                if dest:
                    moved_count += 1
        except Exception as e:
            print(f"Error moving image {image_path} to resource_images: {e}")

    flash(f"Moved {moved_count} image(s) from novel_images to static/resource_images", "success")
    # Redirect back to view the updated file list
    return redirect(url_for("view_novel_files"))


@app.route("/delete_novel_image", methods=["POST"])
def delete_novel_image():
    data = request.get_json(silent=True) or request.form
    image_name = data.get("image") or data.get("filename") or data.get("image_path")
    if not image_name:
        return jsonify({"success": False, "error": "No image specified"}), 400

    filename = os.path.basename(image_name)
    src_path = os.path.join("static", "novel_images", filename)
    if os.path.exists(src_path):
        dest_path = move_novel_image_to_resource_images(src_path)
        return jsonify({"success": True, "message": f"Moved to {dest_path}", "dest": dest_path})
    return jsonify({"success": False, "error": f"Image {filename} not found in static/novel_images"}), 404


@app.route("/view_resource_images")
def view_resource_images():
    resource_dir = "static/resource_images"
    os.makedirs(resource_dir, exist_ok=True)
    image_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        image_paths.extend(glob.glob(f"{resource_dir}/{ext}"))
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    return render_template("view_resource_images.html", image_paths=image_paths)


@app.route("/restore_resource_images", methods=["POST"])
def restore_resource_images():
    selected_image_paths = request.form.getlist("image_paths[]")
    novel_dir = "static/novel_images"
    os.makedirs(novel_dir, exist_ok=True)
    restored_count = 0
    for img_path in selected_image_paths:
        if os.path.exists(img_path):
            filename = os.path.basename(img_path)
            dest = os.path.join(novel_dir, filename)
            if os.path.exists(dest):
                name, ext = os.path.splitext(filename)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
                dest = os.path.join(novel_dir, f"{name}_{timestamp}{ext}")
            shutil.move(img_path, dest)
            restored_count += 1
    flash(f"Restored {restored_count} image(s) to static/novel_images", "success")
    return redirect(url_for("view_resource_images"))



@app.route("/cp_store")
def cp_store():
    source_dir = "static/novel_images"
    target_dir = "static/novel_images"

    try:
        # If the target directory doesn't exist, use copytree to copy all contents
        if not os.path.exists(target_dir):
            shutil.copytree(source_dir, target_dir)
        else:
            # If the directory exists, copy each file individually
            for filename in os.listdir(source_dir):
                source_file = os.path.join(source_dir, filename)
                target_file = os.path.join(target_dir, filename)

                # Copy only files, not directories within source_dir
                if os.path.isfile(source_file):
                    shutil.copy2(source_file, target_file)

        return redirect(url_for("mk_novel"))
    except Exception as e:
        # Handle any exceptions that occur and return an error message
        return f"Error copying files: {e}"


# ------------loads images from archived-images/ --------------------


@app.route("/select_images", methods=["GET", "POST"])
def select_images():
    if request.method == "POST":
        top_image = request.form.get("top_image")
        mask_image = request.form.get("mask_image")
        bottom_image = request.form.get("bottom_image")

        if not top_image or not mask_image or not bottom_image:
            return "Please select one top image, one mask image, and one bottom image."

        # Redirect to the blend_images route with the selected images
        return redirect(
            url_for("blend_images", top=top_image, mask=mask_image, bottom=bottom_image)
        )

    image_paths = get_image_paths()
    return render_template("select_images.html", image_paths=image_paths)


@app.route("/blend_images", methods=["POST", "GET"])
def blend_images():
    # Retrieve selected images from the form
    top_image = request.form.get("top_image")
    mask_image = request.form.get("mask_image")
    bottom_image = request.form.get("bottom_image")
    opacity = float(request.form.get("opacity", 0.5))

    # Check if all required images are provided
    if not top_image or not mask_image or not bottom_image:
        return "Please select one top image, one mask image, and one bottom image."

    # Process images
    image_paths = [top_image, mask_image, bottom_image]
    result_path = blend_images_with_grayscale_mask(image_paths, mask_image, opacity)
    mask_image = "static/masks/mask.png"
    return redirect(
        url_for("clean_storage_route")
    )  # , image_paths=image_paths, mask_path=mask_image, opacity=opacity))


# render_template('blend_result_exp.html', result_image=result_path, image_paths=image_paths, mask_image=mask_image, opacity=opacity)


def blend_images_with_grayscale_mask(image_paths, mask_path, opacity):
    if len(image_paths) != 3:
        return None
    base_image_path, mask_image_path, top_image_path = image_paths
    base_image = Image.open(base_image_path)
    mask_image = Image.open(mask_path).convert("L")
    top_image = Image.open(top_image_path)
    base_image = base_image.resize((512, 768), Image.LANCZOS)
    top_image = top_image.resize((512, 768), Image.LANCZOS)
    mask_image = mask_image.resize((512, 768), Image.LANCZOS)
    # base_image, top_image = resize_images_to_base(base_image, [base_image, top_image])[0], resize_images_to_base(base_image, [base_image, top_image])[1]
    blended_image = Image.composite(top_image, base_image, mask_image)

    unique_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    result_path = os.path.join(app.config["NOVEL_IMAGES"], f"result_{unique_id}.png")
    blended_image.save(result_path)

    return result_path

def get_image_paths():
    image_paths = []
    for ext in ["png", "jpg", "jpeg"]:
        # image_paths.extend(glob.glob(os.path.join('/static/archived-images/', f'*.{ext}')))
        # image paths are static/novel_images/
        image_paths = glob.glob("static/novel_images/*.jpg") + glob.glob(
            "static/novel_images/*.png"
        )
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    return image_paths
'''    
def get_image_paths():
    image_paths = []
    for ext in ["png", "jpg", "jpeg"]:
        # image_paths.extend(glob.glob(os.path.join('/static/archived-images/', f'*.{ext}')))
        # image paths are static/novel_images/
        image_paths = glob.glob("static/archived-images/*.jpg") + glob.glob(
            "static/archived-images/*.png"
        )
    image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    return image_paths
'''

@app.route("/short_out")
def short_out():
    return redirect("mk_novel")


@app.route("/move_square")
def move_square():
    # Generate a unique ID for the new resource directory
    uid = os.urandom(8).hex()
    dest = f"static/{uid}_resources"

    # Make sure the destination directory exists
    os.makedirs(dest, exist_ok=True)

    # Source directory containing files to be moved
    src = "static/square_resources"

    # Move each item within src to the new destination directory
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dest_item = os.path.join(dest, item)

        # Move file or directory
        if os.path.isfile(src_item):
            shutil.move(src_item, dest_item)
        elif os.path.isdir(src_item):
            shutil.move(src_item, os.path.join(dest, item))

    # Redirect after the move operation
    return redirect("copy")


# Define paths for image directories
ARCHIVE_PATH = "static/novel_images/"  # Corrected path
CROPPED_PATH = "static/cropped/"

# Ensure the cropped directory exists
os.makedirs(CROPPED_PATH, exist_ok=True)


# Route to display all images in the archive
@app.route("/crop_archive_image")
def crop_archive_image():
    # Fetch images from the archive directory
    new_image = request.args.get("new_image", "")
    images = glob.glob(os.path.join(ARCHIVE_PATH, "*.*"))
    return render_template("crop_archive_image.html", images=images, new_image=new_image)


# Route to handle cropping of selected image
@app.route("/crop_store_image", methods=["POST", "GET"])
def crop_store_image():
    # Get form data
    image = request.form.get("image")
    size = request.form.get("size")
    pos = request.form.get("pos")
    logit(f"Cropping_Info, image: {image}, size: {size}, pos: {pos}")
    if not image or not size or not pos:
        flash("Please provide all required fields (image, size, and position).")
        return redirect(url_for("crop_archive_image"))

    try:
        # Convert form inputs to required formats
        size = tuple(map(int, size.split(",")))
        pos = tuple(map(int, pos.split(",")))

        # Process and crop the image
        new_image_path = crop_store_image_function(image, size, pos)
        logit(f"Cropping_Info, new_image_path: {new_image_path}")
        flash("Image cropped and saved successfully!")
    except Exception as e:
        flash(f"Error cropping image: {e}")
        return redirect(url_for("crop_archive_image"))

    # Redirect back to the archive image list with the new image path
    return redirect(url_for("crop_archive_image", new_image=new_image_path))

UID = str(uuid.uuid4())
# Function to crop and save the image
def crop_store_image_function(image_path, size, pos):
    # Open the image, crop, and resize it
    im = Image.open(image_path)
    cropped_image = im.crop(pos).resize(size)


    # Define paths for saving the new cropped image
    new_image_path = os.path.join(
        CROPPED_PATH, f"cropped_{os.path.basename(image_path)}"
    )
    orig_image_path = os.path.join(
        ARCHIVE_PATH, f"cropped_{os.path.basename(image_path)}"
    )

 
    unique_image_path = os.path.join(
        CROPPED_PATH, f"cropped_{UID}_{os.path.basename(image_path)}"
    )

    # Save the cropped image
    cropped_image.save(new_image_path)
    
    # Copy and resize the saved image to archive path at 512x768
    shutil.copy(new_image_path, orig_image_path)
    shutil.copy(new_image_path, unique_image_path)
    subprocess.run(["mogrify", "-resize", "512x768!", orig_image_path])
    subprocess.run(["mogrify", "-resize", "512x768!", new_image_path])
    shutil.copy(new_image_path, unique_image_path)
    #subprocess.run(["mogrify", "-resize", "512x768!", unique_image_path])
    return new_image_path


# archived-images to novel_images
@app.route("/archive_to_novel")
def archive_to_novel():
    dest = "static/novel_images"
    # Make sure the destination directory exists
    os.makedirs(dest, exist_ok=True)

    # Source directory containing files to be moved
    # src = 'static/archived-images'
    src = "static/archived_resources"
    # Move each item within src to the new destination directory
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dest_item = os.path.join(dest, item)

        # Move file or directory
        if os.path.isfile(src_item):
            shutil.move(src_item, dest_item)
        elif os.path.isdir(src_item):
            shutil.move(src_item, os.path.join(dest, item))

    # Redirect after the move operation
    return redirect("img_processing")


# -------------------------


def get_an_mp3():
    mp3s = random.choice(glob.glob("static/music/*.mp3"))
    return mp3s


@app.route("/blendem")
def blendem_route():
    # Define the size for resizing images
    SIZE = (512, 768)
    # Get a list of image files
    DIR = "static/novel_images/"
    image_files = sorted(glob.glob(DIR + "*.jpg")) + sorted(glob.glob(DIR + "*.png"))
    random.shuffle(image_files)
    print(f"Number of images: {len(image_files)}")

    # Create a temporary directory to store the resized images
    temp_dir = "btemp/"
    os.makedirs(temp_dir, exist_ok=True)

    # Load and resize the images
    resized_images = []
    for image_file in image_files:
        img = cv2.imread(image_file)
        img = cv2.resize(img, SIZE)
        resized_images.append(img)

    # Create a video writer
    out_path = "xxxxoutput.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_path, fourcc, 30, SIZE)

    # Keep track of video duration
    video_duration = 0

    # Create the video with fading transitions
    for i in range(len(resized_images)):
        if video_duration >= 58:  # Limit video to 58 seconds
            break

        img1 = resized_images[i]
        img2 = resized_images[
            (i + 1) % len(resized_images)
        ]  # Wrap around to the first image
        step_size = 5
        for alpha in range(
            0, 150
        ):  # Gradually change alpha from 0 to 100 for fade effect
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
    frame_clip = ImageClip(
        "static/assets/blendem_frame.png", duration=video_clip.duration
    ).set_position("center")

    # Composite the frame with the video
    final_clip = CompositeVideoClip([video_clip, frame_clip])

    # Save the final video with the overlay and music
    final_output_path = "static/temp_exp/blendem_final_outputX.mp4"
    uid = str(uuid.uuid4())
    des = DIR.replace("/", "_")
    mp4_file = f"static/output_videos/{des}{uid}.mp4"

    final_clip.write_videofile(final_output_path, codec="libx264")
    shutil.copyfile(final_output_path, mp4_file)
    return redirect(url_for("index"))


# -------------------------


@app.route("/shrink_flipbook", methods=["GET"])
def shrink_flipbook_route():
    # Directory setup
    image_directory = "static/novel_images"
    output_directory = "static/temp_exp"
    final_output_directory = "static/output_videos/"
    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(final_output_directory, exist_ok=True)

    # Get sorted image list by last modified date
    image_list = sorted(
        glob.glob(os.path.join(image_directory, "*.png"))
        + glob.glob(os.path.join(image_directory, "*.jpg")),
        key=os.path.getmtime,
    )

    # List to store generated video paths
    video_paths = []

    for i in range(len(image_list) - 1):
        choice = randint(1, 4)
        try:
            base_image_path = image_list[i]
            image_to_paste_path = image_list[(i - 1) % len(image_list)]

            # Open base image
            base_image = Image.open(base_image_path).convert("RGBA")
            bs = base_image.size

            # Create frames for each step in transformation
            IMG_SRC = []
            for j in range(0, bs[0], 5):
                current_frame = base_image.copy()
                image_to_paste = Image.open(image_to_paste_path).convert("RGBA")
                image_to_paste = image_to_paste.resize(
                    (bs[0] - j, bs[1] - j), Image.BICUBIC
                )

                # Determine paste position based on choice
                x, y = (
                    (0 + j, 0 + j)
                    if choice == 1
                    else (0, 0)
                    if choice == 2
                    else (0 + j, 0)
                    if choice == 3
                    else (0, 0 + j)
                )
                paste_position = (x, y)

                # Check image fits within base image dimensions
                if (
                    image_to_paste.size[0] + paste_position[0] <= base_image.size[0]
                    and image_to_paste.size[1] + paste_position[1] <= base_image.size[1]
                ):
                    current_frame.paste(image_to_paste, paste_position, image_to_paste)
                    IMG_SRC.append(np.array(current_frame))

            # Save frames to MP4
            output_video_path = os.path.join(output_directory, f"output_video_{i}.mp4")
            imageio.mimsave(output_video_path, IMG_SRC, fps=30)
            video_paths.append(output_video_path)
        except Exception as e:
            return jsonify({"error": f"Error processing images: {e}"}), 500

    # Concatenate videos
    input_list_path = os.path.join(output_directory, "input_list.txt")
    with open(input_list_path, "w") as input_list_file:
        for video_path in video_paths:
            input_list_file.write(f"file '{os.path.abspath(video_path)}'\n")

    concatenated_video_path = os.path.join(output_directory, "final_result.mp4")
    ffmpeg_command = f"ffmpeg -y -f concat -safe 0 -i {input_list_path} -c copy {concatenated_video_path}"
    subprocess.run(ffmpeg_command, shell=True, check=True)

    # Unique filename for the final video
    final_output_video_path = os.path.join(
        final_output_directory, str(uuid.uuid4()) + ".mp4"
    )
    shutil.copyfile(concatenated_video_path, final_output_video_path)

    # Add title image and music
    add_shrink_title_image(final_output_video_path)

    return redirect(url_for("index"))


def add_shrink_title_image(video_path):
    hex_color = random.choice(
        ["#A52A2A", "#ad1f1f", "#16765c", "#7a4111", "#9b1050", "#8e215d", "#2656ca"]
    )
    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    video_duration = video_clip.duration
    title_image_path = "static/assets/flipbook_title.png"
    padded_size = (width + 50, height + 50)
    x_position = (padded_size[0] - width) / 2
    y_position = (padded_size[1] - height) / 2

    # Background color setup and composite overlay
    rgb_tuple = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    blue_background = ColorClip(padded_size, color=rgb_tuple)
    padded_video_clip = CompositeVideoClip(
        [blue_background, video_clip.set_position((x_position, y_position))]
    )
    title_image = (
        ImageClip(title_image_path)
        .set_duration(video_clip.duration)
        .set_position((0, -5))
        .resize(padded_video_clip.size)
    )
    composite_clip = CompositeVideoClip([padded_video_clip, title_image]).set_duration(
        video_clip.duration
    )

    # Add random music
    mp3_files = glob.glob("static/music/*.mp3")
    random.shuffle(mp3_files)
    music_clip = (
        AudioFileClip(random.choice(mp3_files))
        .subclip(20, 20 + video_clip.duration)
        .set_duration(video_clip.duration)
    )
    composite_clip = composite_clip.set_audio(music_clip)

    output_path = "static/temp_exp/shrink_flipbookX.mp4"
    composite_clip.write_videofile(output_path)
    unique_output_path = (
        f"static/output_videos/AI_Flipbook_{uuid.uuid4().hex}.mp4"
    )
    shutil.copyfile(output_path, unique_output_path)


# -------------------------

# Directories setup
image_directory = "static/novel_images"
output_directory = "static/temp_exp"
final_output_directory = "static/output_videos/"
os.makedirs(image_directory, exist_ok=True)
os.makedirs(output_directory, exist_ok=True)
os.makedirs(final_output_directory, exist_ok=True)


# Function to prepare the home directory
def prep_homedirectory():
    image_directory = "static/temp_images_exp"
    logit(f"Image directory: {image_directory}")

    # Create or clear the image directory
    if os.path.exists(image_directory):
        shutil.rmtree(image_directory)
        logit(f"Cleared contents of image directory: {image_directory}")
    os.makedirs(image_directory, exist_ok=True)
    logit(f"Created image directory: {image_directory}")

    # Copy all jpg and png files from source to image_directory
    for f in os.listdir("static/novel_images"):
        if f.endswith((".jpg", ".jpeg", ".png")):
            logit(f"Copying {f} to {image_directory}")
            shutil.copy(os.path.join("static", "novel_images", f), image_directory)

    # Directory containing images
    image_directory = "static/temp_images_exp"

    # Get and sort the list of image files by last modified date
    image_files = [
        os.path.join(image_directory, f)
        for f in os.listdir(image_directory)
        if f.endswith((".jpg", ".jpeg", ".png"))
    ]

    # Sort by last modified time
    image_files = sorted(image_files, key=os.path.getmtime)

    # To return only filenames without full paths, use:
    image_files = [os.path.basename(f) for f in image_files]

    return image_files


# Function to create zoom effect video
def image_dir_to_zoom():
    selected_directory = "static/temp_images_exp"
    os.makedirs(selected_directory, exist_ok=True)

    image_files = glob.glob(f"{selected_directory}/*.[jp][pn]g")
    if not image_files:
        logit("No images found in the directory.")
        return None

    output_video = "generated_video_exp.mp4"
    frame_rate = 60
    zoom_increment = 0.0005
    zoom_duration = 300
    width, height = 512, 768

    ffmpeg_cmd = (
        f"ffmpeg -hide_banner -pattern_type glob -framerate {frame_rate} "
        f"-i '{selected_directory}/*.jpg' "
        f"-vf \"scale=8000:-1,zoompan=z='min(zoom+{zoom_increment},1.5)':x='iw/2':y='ih/2-4000':d={zoom_duration}:s={width}x{height},crop={width}:{height}:0:256\" "
        f"-c:v libx264 -pix_fmt yuv420p -r {frame_rate} -s {width}x{height} -y {output_video}"
    )

    logit(f"FFmpeg command: {ffmpeg_cmd}")
    try:
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
        logit("Video generated successfully.")
    except subprocess.CalledProcessError as e:
        logit(f"FFmpeg command failed: {e}")
        return None

    video_name = str(uuid.uuid4()) + "_zoom_exp.mp4"
    if not os.path.exists("static/assets_exp"):
        os.makedirs("static/assets_exp")
    shutil.copy(output_video, os.path.join("static/assets_exp", video_name))

    output_vid = os.path.join("static/assets_exp", video_name)
    logit(f"Generated video: {output_vid}")

    video_path = output_vid

    # Speed up the video
    # output_path = 'static/temp_exp/final_output_exp.mp4'
    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-vf",
        "setpts=0.3*PTS",
        "-c:a",
        "copy",
        "-y",
        "static/temp_exp/VideoFaster_expX.mp4",
    ]
    logit(f"Running FFmpeg command to speed up video: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    video_paths = "static/temp_exp/VideoFaster_expX.mp4"
    # add_zoom_title_image(video_path, hex_color="#A52A2A")
    # logit("Video sped up successfully.")
    # output_path = 'static/temp_exp/final_output_expX.mp4'
    return video_paths


# Function to add title image and background music
def add_zoom_title_image(video_path, hex_color="#A52A2A"):
    directory_path = "static/temp_exp"
    os.makedirs(directory_path, exist_ok=True)

    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    video_duration = video_clip.duration
    padded_size = (width + 80, height + 80)
    x_position = (padded_size[0] - width) / 2
    y_position = (padded_size[1] - height) / 2

    # Convert hex to RGB and create background clip
    rgb_tuple = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    background_clip = ColorClip(padded_size, color=rgb_tuple)
    padded_video_clip = CompositeVideoClip(
        [background_clip, video_clip.set_position((x_position, y_position))]
    ).set_duration(video_clip.duration)

    # Load and resize title image
    title_image = (
        ImageClip("static/assets/Zoom_Images.png")
        .resize(padded_video_clip.size)
        .set_position((0, -5))
        .set_duration(video_clip.duration)
    )
    composite_clip = CompositeVideoClip([padded_video_clip, title_image]).set_duration(
        video_clip.duration
    )

    # Load background music
    mp3_files = glob.glob("static/music/*.mp3")
    random.shuffle(mp3_files)
    music_clip = (
        AudioFileClip(random.choice(mp3_files))
        .audio_fadein(0.5)
        .audio_fadeout(0.5)
        .set_duration(video_clip.duration)
    )
    composite_clip = composite_clip.set_audio(music_clip)

    output_path = "static/temp_exp/final_output_expX.mp4"
    composite_clip.write_videofile(output_path)

    # Save output and speed up the video
    unique_name = f"AI_Creates_Composite_{uuid.uuid4()}.mp4"
    shutil.copyfile(
        output_path, f"static/output_videos/{unique_name}"
    )

    return output_path


# Combined route to run all processes in sequence
@app.route("/zoom_each", methods=["GET"])
def zoom_each_route():
    # Step 1: Prepare home directory and get shuffled images
    images = prep_homedirectory()
    if not images:
        return jsonify(error="No images available after preparation"), 500

    # Step 2: Generate zoom effect video
    video_path = image_dir_to_zoom()
    if not video_path:
        return jsonify(error="Zoom effect video generation failed"), 500

    # Step 3: Add title image and background music to the video
    final_video_path = add_zoom_title_image(video_path)
    if not final_video_path:
        return jsonify(error="Final video generation failed"), 500

    return jsonify(
        message="All processing completed successfully",
        final_video_path=final_video_path,
    )


# ----------------------------------------


def init_db():
    """Initialize the SQLite database if it doesn't exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS post (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                content TEXT UNIQUE NOT NULL,
                video_filename TEXT NULL,
                image BLOB
            )
        """
        )
        conn.commit()


def load_txt_files(directory):
    """Load .txt files from the directory into the SQLite database."""
    init_db()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                filepath = os.path.join(directory, filename)
                with open(filepath, "r", encoding="utf-8") as file:
                    title = os.path.splitext(filename)[0]
                    new_content = file.read()

                    # Step 1: Check if post with this title already exists
                    cursor.execute("SELECT content FROM post WHERE title = ?", (title,))
                    existing_post = cursor.fetchone()

                    if existing_post:
                        existing_content = existing_post[0]

                        # Step 2: Compare contents
                        if new_content != existing_content:
                            # Content has changed; delete old entry and insert new one
                            cursor.execute("DELETE FROM post WHERE title = ?", (title,))
                            cursor.execute(
                                "INSERT INTO post (title, content) VALUES (?, ?)",
                                (title, new_content),
                            )
                            print(f"Updated content for title: {title}")
                        else:
                            print(".", end="")
                    else:
                        # No existing post with this title; insert new entry
                        cursor.execute(
                            "INSERT INTO post (title, content) VALUES (?, ?)",
                            (title, new_content),
                        )
                        print(f"Added new post: {title}")

                    conn.commit()  # Commit after each insert/update
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()


# upload an img to static/novel_images
@app.route("/upload_img", methods=["POST"])
def upload_img():
    if "file" not in request.files:
        return jsonify(error="No file found"), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify(error="No file selected"), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        return jsonify(message="File uploaded successfully"), 200

    else:
        return jsonify(error="Invalid file type"), 400


# ----------------------------------------

OUTPUT_DIR = "static/text2audio5"

# Ensure the output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Select the predetermined speaker (for simplicity, the first speaker is used here)
#PREDETERMINED_SPEAKER = tts.get_speakers()[3]


# Route to process a large text file
@app.route("/convert_large_text", methods=["POST", "GET"])
def convert_large_text():
    if request.method == "GET":
        # Render a simple form to upload the file
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Upload Text File</title>
        </head>
        <body>
            <h1>Upload Text File</h1>
            <a href="/list_audio_files">list existing files</a>
            <form action="/convert_large_text" method="post" enctype="multipart/form-data">
                <input type="file" name="text_file" accept=".txt">
                <button type="submit">Convert</button>
            </form>
        </body>
        </html>
        """
    elif request.method == "POST":
        if "text_file" not in request.files:
            return "No file part", 400

        text_file = request.files["text_file"]
        if text_file.filename == "":
            return "No selected file", 400

        # Read and process the text file
        text_content = text_file.read().decode("utf-8")
        paragraphs = text_content.split("\n\n")  # Split on double newlines

        audio_files = []
        for idx, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue  # Skip empty paragraphs

            mp3_filename = f"paragraph_{idx + 1}.mp3"
            mp3_file_path = os.path.join(OUTPUT_DIR, mp3_filename)
            generate_mp3_with_kokoro_tts(paragraph, mp3_file_path, voice=ASSISTANT_VOICE)
            audio_files.append(mp3_filename)

        return render_template("audio_files.html", audio_files=audio_files)


# Route to list available audio files
@app.route("/list_audio_files")
def list_audio_files():
    audio_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]
    audio_files.sort()
    return render_template("audio_files.html", audio_files=audio_files)


# Route to download a specific audio file
@app.route("/download_audio/<filename>")
def download_audio(filename):
    # Get list of audio and image files
    audio_files = [f for f in os.listdir("static/text2audio") if f.endswith(".mp3")]
    image_files = [
        f for f in os.listdir("static/novel_images") if f.endswith((".png", ".jpg"))
    ]
    random.shuffle(image_files)
    image_files = image_files[:50]  # Limit to 50 images
    return render_template(
        "sound_to_story.html", audio_files=audio_files, image_files=image_files
    )


@app.route("/create_story", methods=["POST"])
def create_story_audio():
    image_file = request.form.get("image_path")
    audio_file = request.form.get("audio_path")
    logit(
        f"Received request to create story image: {image_file} and audio: {audio_file}"
    )

    if not image_file or not audio_file:
        logit("No image or audio file selected")
        return jsonify({"error": "No image or audio selected"}), 400

    logit(f"Selected image: {image_file}")
    logit(f"Selected audio: {audio_file}")

    # Construct full paths for the image and audio
    image_path = os.path.join("static/novel_images", image_file)
    audio_path = os.path.join("static/text2audio", audio_file)
    # image_path = image_file
    # audio_path = audio_file

    logit(f"Image path: {image_path}")
    logit(f"Audio path: {audio_path}")
    # Generate output filename
    output_filename = (
        f"output_{image_file.rsplit('.', 1)[0]}_{audio_file.rsplit('.', 1)[0]}.mp4"
    )
    output_path = os.path.join("static/novel_audio_mp3", output_filename)

    try:
        logit(f"Processing image: {image_path} and audio: {audio_path}")

        # Create video from image and audio
        output_path = add_sound_to_novel_image(image_path, audio_path)
        if output_path:
            return jsonify({"success": True, "output_video": output_path})
        else:
            return jsonify({"error": "Error creating video 5934"}), 500

    except Exception as e:
        logit(f"Error processing video and audio: {str(e)}")
        return jsonify({"error": str(e)}), 700


def add_sound_to_story(image_path, audio_path):
    logit(f"Adding sound to story: {image_path} and {audio_path}")
    # Define the path for the silent audio clip in MP3 format
    silence_path = "silence.mp3"

    # Check if the silent audio file exists; if not, create a 0.7-second MP3 silence
    if not os.path.exists(silence_path):
        silence = AudioSegment.silent(duration=800)  # 700 ms of silence
        silence.export(silence_path, format="mp3")

    # Load both the main audio file and the silence clip
    audio_clip = AudioFileClip(audio_path)
    silence_clip = AudioFileClip(silence_path)

    # Apply fade-out to the audio clips before concatenation using moviepy's audio_fadeout
    fade_duration = 0.6  # Fade duration in seconds
    audio_clip = afx.audio_fadeout(audio_clip, fade_duration)
    silence_clip = afx.audio_fadeout(silence_clip, fade_duration)

    # Concatenate silence before, main audio, and silence after
    combined_audio = concatenate_audioclips([silence_clip, audio_clip, silence_clip])

    # Ensure the audio duration matches the image duration exactly
    image_clip = ImageClip(image_path).set_duration(combined_audio.duration)

    # Define the output path for the combined audio in MP3 format
    combined_audio_path = audio_path.replace(".mp3", "_combined.mp3")

    # Write the combined audio to a file (ensure it's saved as MP3)
    combined_audio.write_audiofile(combined_audio_path, codec="libmp3lame")

    # Set the combined audio to the image clip
    video_clip = image_clip.set_audio(combined_audio)

    # Define the output path for the final video
    output_path = image_path.replace(".jpg", "_audio.mp4").replace(".png", "_audio.mp4")

    # Write the final video file with an FPS (frames per second) of 24
    video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

    # Copy to static/temp_exp/STILLX.mp4
    shutil.copy(output_path, "static/temp_exp/STILLX.mp4")
    im = Image.open(image_path).convert("RGB")
    w, h = im.size
    if w > 833:
        im = im.resize((512, 512), resample=Image.LANCZOS)
    if w == 832:
        im = im.resize((512, 768), resample=Image.LANCZOS)
    im.save("static/projects/use.jpg")
    # copy to static/projects/use.mp3
    shutil.copy(audio_path, "static/projects/use.mp3")
    subprocess.run(
        [
            sys.executable,
            "static/Wav2Lip-master/makeavatar",
        ],
        check=True,
    )
    return output_path


@app.route("/combine_story", methods=["POST"])
def combine_story_audio():
    image_file = request.form.get("image_path")
    audio_file = request.form.get("audio_path")

    if not image_file or not audio_file:
        logit("No image or audio file selected")
        return jsonify({"error": "No image or audio selected"}), 400

    logit(f"Selected image: {image_file}")
    logit(f"Selected audio: {audio_file}")

    # Construct full paths for the image and audio
    image_path = os.path.join("static/novel_images", image_file)
    audio_path = os.path.join("static/text2audio", audio_file)

    # Generate output filename
    output_filename = (
        f"output_{image_file.rsplit('.', 1)[0]}_{audio_file.rsplit('.', 1)[0]}.mp4"
    )
    output_path = os.path.join("static/temp_exp", output_filename)

    try:
        logit(f"Processing image: {image_path} and audio: {audio_path}")

        # Create video from image and audio
        output_path = add_sound_to_story(image_path, audio_path)
        if output_path:
            return jsonify({"success": True, "output_video": output_path})
        else:
            return jsonify({"error": " 3961"}), 500

    except Exception as e:
        logit(f"Error processing video and audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mp3upload", methods=["POST", "GET"])
def mp3upload():
    print("Received MP3 upload request.")
    audio_file = None  # Default to no audio file

    if request.method == "POST":
        # Check if a file part is in the request
        if "file" not in request.files:
            print("No file part in the request.")
            return render_template(
                "player.html", error="No file uploaded", audio_file=None
            )

        file = request.files["file"]

        # Check if a file was selected
        if file.filename == "":
            print("No file selected for upload.")
            return render_template(
                "playmp3.html", error="No file selected", audio_file=None
            )

        # Save the MP3 file
        if file and file.filename.lower().endswith(".mp3"):
            audio_file = os.path.join("static", "TEMP.mp3")
            file.save(audio_file)
            print(f"MP3 file saved to {audio_file}")
            return render_template("playmp3.html", audio_file="TEMP.mp3")

        print("Invalid file type. Only MP3 files are allowed.")
        return render_template(
            "player.html",
            error="Invalid file type. Please upload an MP3 file.",
            audio_file=None,
        )

    return render_template("playmp3.html", audio_file=None)


# --------------------


def sound2image(image_path, audio_path):
    try:
        # Log the paths for debugging
        print(f"Image Path: {image_path}")
        print(f"Audio Path: {audio_path}")

        # Create an ImageClip from the image
        image_clip = ImageClip(image_path)

        # Load the audio file
        audio_clip = AudioFileClip(audio_path)

        # Log the duration of the audio for debugging
        print(f"Audio Duration: {audio_clip.duration} seconds")

        # Set the duration of the image clip to match the audio clip duration
        image_clip = image_clip.set_duration(audio_clip.duration)

        # Set the audio to the image clip
        video_clip = image_clip.set_audio(audio_clip)

        # Define the output path for the video
        output_path = image_path.replace(".jpg", "_audio.mp4").replace(
            ".png", "_audio.mp4"
        )

        # Log the output path for debugging
        print(f"Output Video Path: {output_path}")

        # Write the final video file with an FPS (frames per second) of 24
        video_clip.write_videofile(
            output_path, codec="libx264", audio_codec="aac", fps=24
        )
        # copy to static/temp_exp/STILLX.mp4
        shutil.copy(output_path, "static/temp_exp/STILLX.mp4")

        "temp_exp/sound2_imageX.mp4"

        im = Image.open(image_path).convert("RGB")
        w, h = im.size
        if w > 833:
            im = im.resize((512, 512), resample=Image.LANCZOS)
        if w == 832:
            im = im.resize((512, 768), resample=Image.LANCZOS)
        im.save("static/projects/use.jpg")
        # copy to static/projects/use.mp3
        shutil.copy(audio_path, "static/projects/use.mp3")
        subprocess.run(
            [
                sys.executable,
                "static/Wav2Lip-master/makeavatar",
            ],
            check=True,
        )

        return output_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# if 'static/story_resources' not exist
if not os.path.exists("static/story_resources"):
    os.makedirs("static/story_resources")


@app.route("/sound_2_image", methods=["POST"])
def sound_2_image():
    image_file = request.form.get("image_path")
    audio_file = request.form.get("audio_path")

    if not image_file or not audio_file:
        logit("No image or audio file selected")
        return jsonify({"error": "No image or audio selected"}), 400

    logit(f"Selected image: {image_file}")
    logit(f"Selected audio: {audio_file}")

    # Construct full paths for the image and audio
    image_path = os.path.join("static/story_resources", image_file)
    audio_path = os.path.join("static/text2audio3", audio_file)

    # Generate output filename
    output_filename = (
        f"output_{image_file.rsplit('.', 1)[0]}_{audio_file.rsplit('.', 1)[0]}.mp4"
    )
    output_path = os.path.join("static/temp_exp", output_filename)

    try:
        logit(f"Processing image: {image_path} and audio: {audio_path}")

        # Create video from image and audio
        output_path = sound2image(image_path, audio_path)
        if output_path:
            return jsonify({"success": True, "output_video": output_path})
        else:
            return jsonify({"error": " 3961"}), 500

    except Exception as e:
        logit(f"Error processing video and audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/sound2_image", methods=["GET"])
def sound2_image():
    # Get list of audio and image files
    audio_files = [f for f in os.listdir("static/text2audio3/") if f.endswith(".mp3")]
    # sort audio files
    # Sort audio files numerically based on the numbers in their filenames
    audio_files.sort(key=lambda x: int(os.path.splitext(x)[0]))
    image_files = [
        f for f in os.listdir("static/story_resources") if f.endswith((".png", ".jpg"))
    ]
    random.shuffle(image_files)
    image_files = image_files[:50]  # Limit to 50 images
    return render_template(
        "mp3_2_image.html", audio_files=audio_files, image_files=image_files
    )


"static/story_resources/*.mp4"


@app.route("/story", methods=["GET"])
def story():
    # Get list of audio and image files

    video_files = glob.glob("static/story_resources/*.mp4")
    return render_template("story.html", video_files=video_files)


# --------------------
@app.route("/get_trends", methods=["GET", "POST"])
def get_trends():
    pytrends = TrendReq()
    region = "united_states"  # Default region
    keyword = "technology"  # Default keyword
    trends = []
    suggestions = []

    if request.method == "POST":
        # Get region and keyword from the form
        region = request.form.get("region", "united_states")
        keyword = request.form.get("keyword", "technology")

        # Fetch trending searches for the selected region
        trending_searches = pytrends.trending_searches(pn=region)
        trends = trending_searches[0].tolist()

        # Fetch suggestions for the keyword
        suggestions = pytrends.suggestions(keyword=keyword)

    return render_template(
        "trends.html",
        trends=trends,
        suggestions=suggestions,
        region=region,
        keyword=keyword,
    )


"""
@app.route("/search_templates", methods=["GET"])
def search_templates():
    # cat all templates contents into static/All.html
    subprocess.run(["cat", "templates/*.html",">","static/All.html"], cwd="templates", check=True)
    # Path to the concatenated HTML file
    html_file_path = "static/All.html"

    # Read and load the HTML file as text
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
    except FileNotFoundError:
        html_content = "HTML file not found."

    # Render the template and pass the HTML content
    return render_template("All.html", html_content=html_content)
"""


@app.route("/search_all_templates", methods=["GET"])
def search_all_templates():
    # Path to the static file
    txt_file_path = "static/All.txt"

    # Get all HTML files in the templates directory
    templates_dir = "templates"
    html_files = [f for f in os.listdir(templates_dir) if f.endswith(".html")]

    try:
        # Concatenate all files into All.txt with HTML content escaped
        with open(txt_file_path, "w", encoding="utf-8") as output_file:
            for html_file in html_files:
                with open(
                    os.path.join(templates_dir, html_file), "r", encoding="utf-8"
                ) as file:
                    content = file.read()  # Read file content
                    # escaped_content = html.escape(content)  # Escape the content
                    # output_file.write(escaped_content)  # Write the escaped content to the output file
                    output_file.write(content)
                    output_file.write(
                        "\n---------------\n"
                    )  # Add a newline between files

        # Read the concatenated content from All.txt
        with open(txt_file_path, "r", encoding="utf-8") as file:
            txt_content = file.read()  # Read the escaped content

    except FileNotFoundError:
        txt_content = "Text file not found."

    # Render the template and pass the escaped content
    return render_template("template_search.html", txt_content=txt_content)


# --------------------
TITLE_DIR = "static/overlay_zooms/title/"
MAIN_DIR = "static/temp_exp/"
OUTPUT_PATH = "static/temp_exp/titledX.mp4"
RESIZED_TITLE_PATH = "static/temp_exp/resized_title.mp4"
RESIZED_MAIN_PATH = "static/temp_exp/resized_main.mp4"


@app.route("/title", methods=["GET", "POST"])
def title_route():
    if request.method == "POST":
        title_file = request.form.get("title_file")
        main_file = request.form.get("main_file")

        if title_file and main_file:
            title_path = os.path.join(TITLE_DIR, title_file)
            main_path = os.path.join(MAIN_DIR, main_file)

            # Resize videos
            resize_videos(title_path, main_path)

            # Concatenate videos
            concatenate_title_video()
            video = "static/temp_exp/titledX.mp4"
            return render_template("title.html", video=video)

    title_files = [f for f in os.listdir(TITLE_DIR) if f.endswith(".mp4")]
    main_files = [f for f in os.listdir(MAIN_DIR) if f.endswith(".mp4")]

    return render_template("title.html", title_files=title_files, main_files=main_files)


def resize_videos(title_path, main_path):
    width = 512
    height = 768

    command_title = [
        "ffmpeg",
        "-i",
        title_path,
        "-vf",
        f"scale={width}:{height}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-y",
        RESIZED_TITLE_PATH,
    ]

    command_main = [
        "ffmpeg",
        "-i",
        main_path,
        "-vf",
        f"scale={width}:{height}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-y",
        RESIZED_MAIN_PATH,
    ]

    try:
        subprocess.run(command_title, check=True)
        subprocess.run(command_main, check=True)
        print("Resizing successful!")
    except subprocess.CalledProcessError as e:
        print(f"Error during resizing: {e}")


def concatenate_title_video():
    command = [
        "ffmpeg",
        "-i",
        RESIZED_TITLE_PATH,
        "-i",
        RESIZED_MAIN_PATH,
        "-filter_complex",
        "[0:v:0][1:v:0]concat=n=2:v=1[outv]",
        "-map",
        "[outv]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-shortest",
        "-y",
        OUTPUT_PATH,
    ]

    try:
        subprocess.run(command, check=True)
        print("Concatenation successful!")
    except subprocess.CalledProcessError as e:
        print(f"Error during concatenation: {e}")


# --------------------


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/index_upload")
def index_upload():
    """Render the upload page."""
    return render_template("index_upload.html")


@app.route("/upload", methods=["POST", "GET"])
def upload_file():
    """Handle the file upload."""
    if request.method == "POST":
        # Check if the POST request has the file part
        if "file" not in request.files:
            flash("No file part")
            print("No file part in request.")
            return redirect(request.url)

        file = request.files["file"]

        # Check if a file was selected
        if file.filename == "":
            flash("No selected file")
            print("No file selected.")
            return redirect(request.url)

        # Check if the file has a valid extension
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
            filename = secure_filename(file.filename)

            # Save the file to the main upload directory
            save_path = os.path.join("static/novel_images", filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)

            # Copy the file to additional directories
            shutil.copy(save_path, "static/image-archives/")
            shutil.copy(save_path, "static/archived_resources/")
            ic(f"File saved to {save_path} and copied to archive directories.")

            return redirect(url_for("uploaded_file", filename=filename))
        else:
            flash("File type not allowed")
            print("File type not allowed.")
            return redirect(request.url)
    return render_template("index_upload.html")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Display the uploaded file."""
    file_url = url_for("static", filename=f"novel_images/{filename}")
    return f"File successfully uploaded: <a href='{file_url}'>{filename}</a>"


# --------------------
# Flask configuration for file uploads
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_AUDIO_EXTENSIONS"] = {"mp3", "jpg"}


def allowed_file(filename):
    """Check if the uploaded file is an allowed MP3 file."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_AUDIO_EXTENSIONS"]
    )


@app.route("/mp3_upload", methods=["POST", "GET"])
def mp3_upload():
    if request.method == "POST":
        # Check if the POST request has the file part
        if "file" not in request.files:
            return "No file part in the request", 400

        file = request.files["file"]

        # If no file is selected
        if file.filename == "":
            return "No file selected", 400

        # If the file is allowed
        if file and allowed_file(file.filename):
            audio_file = os.path.join(app.config["UPLOAD_FOLDER"], "TEMP.mp3")
            file.save(audio_file)
            print(f"MP3 file saved to {audio_file}")
            # Pass the saved file path to the template
            return render_template("player.html", audio_file=audio_file)
        else:
            return "Invalid file type. Only MP3 files are allowed.", 400

    # For GET requests, render the upload form
    return """
    <!doctype html>
    <title>Upload MP3</title>
    <h1>Upload MP3 File</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    """


@app.route("/static_audio/<filename>")
def serve_static_audio(filename):
    """Serve static files (like TEMP.mp3)."""
    return redirect(url_for("static", filename=filename))


# --------------------
@app.route("/image_upload", methods=["POST", "GET"])
def image_upload():
    if request.method == "POST":
        # Check if the POST request has the file part
        if "file" not in request.files:
            return "No file part in the request", 400

        file = request.files["file"]

        # If no file is selected
        if file.filename == "":
            return "No file selected", 400
        # if 'static/text2audio3' create it
        if not os.path.exists("static/text2audio3"):
            os.makedirs("static/text2audio3")
        # If the file is allowed
        if file and allowed_file(file.filename):
            image_file = os.path.join(app.config["UPLOAD_FOLDER"], "TEMP.jpg")
            file.save(image_file)
            shutil.copy(image_file, "static/story_resources/")
            print(f"MP3 file saved to {image_file}")
            # Pass the saved file path to the template
            audio_file = os.path.join(app.config["UPLOAD_FOLDER"], "TEMP.mp3")
            shutil.copy(audio_file, "static/text2audio3")
            img = image_file
            return render_template("player.html", audio_file=audio_file, img=img)
        else:
            return "Invalid file type. Only MP3 files are allowed.", 400

    # For GET requests, render the upload form
    return """
    <!doctype html>
    <title>Upload MP3</title>
    <h1>Upload MP3 File</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    """


@app.route("/combine_audio_image", methods=["POST", "GET"])
def combine_audio_image():
    if request.method == "POST":
        # Check if the POST request has both audio and image files
        if "audio" not in request.files or "image" not in request.files:
            return "Both audio and image files are required.", 400

        audio_file = request.files["audio"]
        image_file = request.files["image"]

        # Validate file selections
        if audio_file.filename == "" or image_file.filename == "":
            return "Both files must be selected.", 400

        if not allowed_file(audio_file.filename, app.config["ALLOWED_AUDIO"]):
            return "Invalid audio file. Only MP3 files are allowed.", 400

        if not allowed_file(image_file.filename, app.config["ALLOWED_IMAGE"]):
            return "Invalid image file. Only JPG, JPEG, or PNG files are allowed.", 400

        # Save files temporarily
        temp_audio = os.path.join(app.config["UPLOAD_FOLDER"], "temp_audio.mp3")
        temp_image = os.path.join(app.config["UPLOAD_FOLDER"], "temp_image.jpg")
        output_video = "static/temp_exp/temp_videoX.mp4"

        audio_file.save(temp_audio)
        image_file.save(temp_image)
        print(f"Temporary files saved: {temp_audio}, {temp_image}")

        # Combine files into a video using FFmpeg
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            temp_image,
            "-i",
            temp_audio,
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            output_video,
        ]
        try:
            subprocess.run(ffmpeg_command, check=True)
            print(f"Video created successfully at {output_video}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating video: {e}")
            return "Failed to create video.", 500

        # Send the file directly to the browser for download
        output_video = "static/temp_exp/temp_videoX.mp4"

        return render_template(
            "player.html", img=temp_image, audio_file=audio_file, video=output_video
        )
    # For GET requests, render the combine form
    return """
    <!doctype html>
    <title>Combine MP3 and JPG</title>
    <h1>Combine MP3 Audio and JPG Image into MP4</h1>
    <form method="POST" enctype="multipart/form-data">
        <label for="audio">Select MP3 file:</label><br>
        <input type="file" name="audio" id="audio"><br><br>
        <label for="image">Select JPG file:</label><br>
        <input type="file" name="image" id="image"><br><br>
        <input type="submit" value="Combine and Download">
    </form>
    """


# --------------------


# Set up logging to capture GC debug output and store it in memory
gc_data = []  # Store GC collection data for plotting


# Enable GC debugging for memory leak detection


def continuous_gc_monitor(interval=120):
    """Run garbage collection monitoring every `interval` seconds."""
    global gc_data
    while True:
        collected = gc.collect()  # Force garbage collection
        gc_data.append(collected)  # Store the collected data
        if len(gc_data) > 1000:
            gc_data = gc_data[-1000:]
        logit(f"Garbage collection run: {collected} objects collected")
        time.sleep(interval)  # Wait for the specified interval


@app.route("/gc_logs")
def show_gc_logs():
    """Display recent GC logs with dark terminal styling."""
    logs = []
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r") as f:
            for line in f:
                if "Garbage collection" in line:
                    logs.append(line.strip())
    recent_logs = logs[-60:] if logs else ["No GC logs recorded yet."]
    log_text = "\n".join(recent_logs)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Garbage Collection Logs</title>
    <link rel="stylesheet" href="/static/css/themed.css">
    <style>
        body {{
            background: #080812;
            color: #e2e8f0;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: rgba(18, 22, 38, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            padding: 24px 28px;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5);
        }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
            color: #f8fafc;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.85rem;
            background: rgba(255, 255, 255, 0.08);
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.15);
            transition: all 0.2s;
        }}
        .btn:hover {{
            background: #38bdf8;
            color: #080812;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #00f0ff, #38bdf8);
            color: #080812;
            border: none;
        }}
        .terminal-box {{
            background: #0b0f19;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 16px;
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 0.82rem;
            line-height: 1.6;
            color: #38bdf8;
            max-height: 580px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 class="title">📜 Python Garbage Collection Logs</h1>
                <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                    Showing last {len(recent_logs)} collection cycles &bull; Monitored every 120s
                </div>
            </div>
            <div style="display: flex; gap: 8px;">
                <a href="/gc_logs" class="btn">🔄 Refresh</a>
                <a href="/gc_plot" class="btn btn-primary">📈 View GC Plot</a>
                <a href="/utilities" class="btn">⚙️ Utilities Hub</a>
            </div>
        </div>
        <div class="terminal-box">{log_text}</div>
    </div>
</body>
</html>"""
    return html


@app.route("/gc_plot")
def gc_plot():
    """Generate and view a plot of GC collection over time."""
    global gc_data
    if len(gc_data) < 2:
        collected = gc.collect()
        gc_data.append(collected)
    if len(gc_data) >= 1:
        fig, ax = plt.subplots(figsize=(10, 4.8), facecolor="#0e1222")
        ax.set_facecolor("#151b33")
        ax.plot(
            gc_data,
            color="#00f0ff",
            marker="o",
            markersize=5,
            linewidth=2,
            label="Objects Collected",
        )
        ax.fill_between(range(len(gc_data)), gc_data, color="#00f0ff", alpha=0.15)
        ax.set_xlabel("Collection Cycle (every 120s)", color="#cbd5e1", fontsize=11)
        ax.set_ylabel("Objects Collected", color="#cbd5e1", fontsize=11)
        ax.set_title(
            "Python Garbage Collection Trend Over Time",
            color="#f8fafc",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )
        ax.tick_params(colors="#94a3b8")
        ax.grid(True, color="#334155", linestyle="--")
        for spine in ax.spines.values():
            spine.set_color("#475569")
        ax.legend(facecolor="#0e1222", edgecolor="#475569", labelcolor="#f8fafc")
        plt.tight_layout()

        filename = "gc_plot_latest.png"
        filepath = os.path.join("static", filename)
        fig.savefig(filepath, dpi=120)
        plt.close(fig)

        total_cycles = len(gc_data)
        last_collected = gc_data[-1] if gc_data else 0
        max_collected = max(gc_data) if gc_data else 0
        avg_collected = round(sum(gc_data) / len(gc_data), 1) if gc_data else 0
        vm = psutil.virtual_memory()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Garbage Collection Plot</title>
    <link rel="stylesheet" href="/static/css/themed.css">
    <style>
        body {{
            background: #080812;
            color: #e2e8f0;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: rgba(18, 22, 38, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            padding: 24px 28px;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5);
        }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
            color: #f8fafc;
        }}
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 12px 16px;
        }}
        .stat-label {{
            font-size: 0.78rem;
            color: #94a3b8;
            margin-bottom: 4px;
        }}
        .stat-val {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #38bdf8;
        }}
        .plot-box {{
            background: #0b0f19;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .plot-img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.85rem;
            background: rgba(255, 255, 255, 0.08);
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.15);
            transition: all 0.2s;
        }}
        .btn:hover {{
            background: #38bdf8;
            color: #080812;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #00f0ff, #38bdf8);
            color: #080812;
            border: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 class="title">📈 Python Garbage Collection Plot</h1>
                <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                    Cyclic reference detection & memory cleanup diagnostics
                </div>
            </div>
            <div style="display: flex; gap: 8px;">
                <a href="/gc_plot" class="btn btn-primary">🔄 Re-plot</a>
                <a href="/gc_logs" class="btn">📜 View GC Logs</a>
                <a href="/utilities" class="btn">⚙️ Utilities Hub</a>
            </div>
        </div>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-label">Total Cycles</div>
                <div class="stat-val">{total_cycles}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Last Cycle Collected</div>
                <div class="stat-val" style="color: #10b981;">{last_collected} obj</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Peak Cycle Collected</div>
                <div class="stat-val" style="color: #f59e0b;">{max_collected} obj</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg / Cycle</div>
                <div class="stat-val">{avg_collected} obj</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">System RAM Load</div>
                <div class="stat-val" style="color: #a855f7;">{vm.percent}%</div>
            </div>
        </div>

        <div class="plot-box">
            <img src="/static/{filename}?t={time.time()}" alt="GC Collection Plot" class="plot-img">
        </div>
    </div>
</body>
</html>"""
        return html

    return """<!DOCTYPE html><html><body style='background:#080812;color:white;font-family:sans-serif;padding:40px;text-align:center;'>
    <h2>⏳ Gathering GC Data...</h2><p style='color:#94a3b8;'>The GC monitor thread collects samples every 120s. Please wait a few moments and refresh.</p>
    <p><a href='/gc_logs' style='color:#38bdf8;'>View Raw GC Logs</a> &bull; <a href='/utilities' style='color:#38bdf8;'>Back to Utilities</a></p>
    </body></html>"""


def start_gc_monitor():
    """Start the GC monitor thread before Flask app starts serving requests."""
    thread = threading.Thread(target=continuous_gc_monitor, daemon=True)
    thread.start()
    logit("Started GC monitoring in the background.")


ACTIVE_TASKS = {}
ACTIVE_TASKS_LOCK = threading.Lock()


def register_active_task(task_id, description):
    """Register an active background job like generation or transcoding."""
    with ACTIVE_TASKS_LOCK:
        ACTIVE_TASKS[task_id] = {
            "description": description,
            "started_at": time.time(),
        }


def unregister_active_task(task_id):
    """Remove a finished background job."""
    with ACTIVE_TASKS_LOCK:
        ACTIVE_TASKS.pop(task_id, None)


register_task = register_active_task
unregister_task = unregister_active_task


@app.route("/api/system_status")
def system_status_api():
    """Real-time system resource & busy status API."""
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    cpu = psutil.cpu_percent(interval=None)

    # Detect active external media processes (FFmpeg, ImageMagick, SD Generation)
    active_procs = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            pname = proc.info.get("name", "").lower()
            cmd = " ".join(proc.info.get("cmdline") or []).lower()
            if any(k in pname for k in ["ffmpeg", "mogrify", "convert"]):
                active_procs.append(proc.info["name"])
            elif any(k in cmd for k in ["generate.py", "one_model_cfg.py", "onev2.py", "one_model_seeds.py", "one_allmodels.py"]):
                active_procs.append("SD Image Generation")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    with ACTIVE_TASKS_LOCK:
        registered = [t["description"] for t in ACTIVE_TASKS.values()]

    all_tasks = list(set(active_procs + registered))

    # Thresholds:
    # Overloaded: RAM > 90% or CPU > 92%
    # Busy: RAM > 80% or CPU > 75% or active task running
    is_overloaded = vm.percent >= 90 or cpu >= 92
    is_busy = is_overloaded or vm.percent >= 80 or cpu >= 75 or len(all_tasks) > 0

    if is_overloaded:
        state = "overloaded"
        message = "System Overloaded: High CPU / Memory Pressure"
        badge_color = "#ef4444"
    elif is_busy:
        task_str = f" ({', '.join(all_tasks)})" if all_tasks else ""
        state = "busy"
        message = f"System Busy{task_str}"
        badge_color = "#f59e0b"
    else:
        state = "ready"
        message = "System Ready"
        badge_color = "#10b981"

    return jsonify(
        {
            "status": state,
            "message": message,
            "badge_color": badge_color,
            "cpu_percent": round(cpu, 1),
            "ram_percent": round(vm.percent, 1),
            "ram_used_gb": round(vm.used / (1024**3), 2),
            "ram_total_gb": round(vm.total / (1024**3), 2),
            "swap_percent": round(swap.percent, 1),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "active_tasks": all_tasks,
            "is_busy": is_busy,
            "is_overloaded": is_overloaded,
        }
    )


@app.route("/api/free_memory", methods=["POST", "GET"])
def free_memory_api():
    """Trigger manual garbage collection and cache flushing."""
    collected = gc.collect()
    plt.close("all")
    vm = psutil.virtual_memory()
    return jsonify(
        {
            "status": "success",
            "objects_collected": collected,
            "ram_percent": round(vm.percent, 1),
            "ram_used_gb": round(vm.used / (1024**3), 2),
        }
    )


# --------------------
# Path to store generated images
IMAGE_FOLDER = os.path.join(os.getcwd(), "static", "novel_images")
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Path to store generated images
IMAGE_FOLDER = os.path.join(os.getcwd(), "static", "novel_images")
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)


@app.route("/convert_text", methods=["GET", "POST"])
def convert_text():
    if request.method == "POST":
        # Get data from the form
        text = request.form["text"]  # Multi-line text
        font = request.form["font"]
        color = request.form["color"]
        pointsize = request.form["pointsize"]
        gravity = request.form["gravity"]
        x = request.form["x"]
        y = request.form["y"]
        line_spacing = request.form["line_spacing"]
        bg_color = request.form["bg_color"]  # Get the selected background color

        # Split the text into individual lines
        text_lines = text.split("*")
        logit(f"Text lines: {text_lines}")
        # Current timestamp for file naming (using datetime)
        timestamp = datetime.datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )  # Correct timestamp generation
        output_file = f"{IMAGE_FOLDER}/text_image_{timestamp}.jpg"

        # Start with a transparent or solid background (no white background)
        base_command = [
            "convert",
            "-size",
            "512x768",  # Set image size
            "xc:" + bg_color,  # Use the background color selected by the user
            output_file,
        ]

        # Execute the base image creation (with transparent or solid color background)
        result = subprocess.run(base_command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            raise Exception(f"ImageMagick command failed: {result.stderr}")

        # Generate the image layers for each line of text (on top of the background)
        y_base = int(y)  # Starting Y position for the first line
        for line in text_lines:
            # Add text directly to the main output file
            command = [
                "convert",
                output_file,  # Use the current image as input
                "-font",
                font,
                "-gravity",
                gravity,
                "-fill",
                color,
                "-pointsize",
                pointsize,
                "-background",
                bg_color,  # Set the text background color to match the image
                "-page",
                f"+{x}+{y_base}",  # Add the text at the specified position
                f"label:{line}",
                "-composite",  # Composite (overlay) the text on the existing image
                output_file,  # Save the result back to the same file
            ]

            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                raise Exception(f"ImageMagick command failed: {result.stderr}")

            # Increment Y position for the next line
            y_base += int(pointsize) + int(line_spacing)

        # Now copy the image to a static filename so we can reference it consistently
        static_image_path = f"{IMAGE_FOLDER}/temp_image.jpg"
        shutil.copy(output_file, static_image_path)
        # Copy timestamped file to archived-images
        shutil.copy(output_file, f"static/archived-images/text_image_{timestamp}.jpg")

        # Return the generated image with a consistent filename
        return render_template("convert_text.html", image=static_image_path)

    return render_template("convert_text.html")


# --------------------
@app.route("/fish_kiss")
def fish_kiss():
    return render_template("fish_kiss.html")


@app.route("/where_is_alice")
def where_is_alice():
    return render_template("where_is_alice.html")


# fish_video_maker stop_motion images at static/stop_motion
@app.route("/fish_video_maker")
def fish_video_maker():
    return render_template("fish_video_maker.html")


@app.route("/stop_motion")
def stop_motion():
    return render_template("stop_motion.html")


# Ensure the save path exists
SAVE_PATH = os.path.join(app.root_path, "static", "capture_resources")
os.makedirs(SAVE_PATH, exist_ok=True)


@app.route("/save-capture", methods=["POST"])
def save_capture():
    try:
        # Get the image data URL from the request
        data = request.get_json()
        image_data_url = data.get("imageData")

        if not image_data_url:
            return jsonify({"error": "No image data provided"}), 400

        # Log the received data to check the image data URL
        print("Received image data:", image_data_url[:100])  # log first 100 chars

        # Remove the "data:image/png;base64," part of the URL
        image_data = image_data_url.split(",")[1]

        # Decode the base64 string to bytes
        image_bytes = base64.b64decode(image_data)

        # Create an image from the byte data
        image = Image.open(BytesIO(image_bytes))

        # Generate a unique file name
        uid = os.urandom(8).hex()
        image_path = os.path.join(SAVE_PATH, f"{uid}_captured_area.png")

        # Log the save path
        print(f"Saving image to: {image_path}")

        # Check if the directory exists
        if not os.path.exists(SAVE_PATH):
            print(f"Error: Directory does not exist: {SAVE_PATH}")
            return jsonify({"error": "Save directory does not exist"}), 500

        # Save the image
        image.save(image_path)

        shutil.copy(image_path, "static/capture_resources/temp.png")
        # Verify the image is saved by checking the file existence
        if os.path.isfile(image_path):
            print(f"Image saved successfully at: {image_path}")
        else:
            print("Error: Image not saved to the file system.")

        # Return a success response
        # subprocess mogrify -gravity center -crop 512x512+0+0 {image_path}
        subprocess.run(
            [
                "mogrify",
                "-gravity",
                "center",
                "-crop",
                "512x512+0+0",
                "static/capture_resources/temp.png",
            ]
        )
        # copy crop to uuid
        uid = os.urandom(8).hex()
        imagepath = os.path.join(SAVE_PATH, f"{uid}_captured_area.png")
        shutil.copy("static/capture_resources/temp.png", imagepath)
        return (
            jsonify({"message": "Image saved successfully!", "path": image_path}),
            200,
        )
    except Exception as e:
        # Log the error with full details
        print(f"Error saving image: {e}")
        return jsonify({"error": str(e)}), 500


# --------------------
# get static/output_videos/ and copy to static/vids
# --------------------
# Configuration
CAPDATABASE = "static/captions.db"
UPLOAD_CAPTIONS = "static/captions_resources"

if not os.path.exists(UPLOAD_CAPTIONS):
    os.makedirs(UPLOAD_CAPTIONS)


# Database creation and initialization
def create_caption_db():
    conn = sqlite3.connect(CAPDATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS captions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            width TEXT,
            height TEXT,
            text TEXT,
            background_color TEXT,
            font TEXT,
            font_size INTEGER,
            font_color TEXT
        )
    """
    )
    conn.commit()
    conn.close()


# Route to serve the form
@app.route("/mk_captions")
def mk_captions():
    return render_template("mk_captions.html")


# Save caption as an image and store in database
@app.route("/save_captions", methods=["POST"])
def save_captions():
    if request.content_type != "application/json":
        return (
            jsonify(
                {"success": False, "error": "Content-Type must be application/json"}
            ),
            415,
        )

    try:
        # Get data from the frontend (JS)
        data = request.get_json()

        # Log the data to check what we're receiving
        ic(f"Received Data: {data}")

        # Extract base64 image data
        image_data = data["imageData"].split(",")[1]  # Extract base64 image data
        image_bytes = base64.b64decode(image_data)

        # Generate a unique filename using the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(UPLOAD_CAPTIONS, f"caption_{timestamp}.png")

        # Save the image to the file system
        with open(filename, "wb") as f:
            f.write(image_bytes)
        # SAVE COPY TO "static/novel_images" ,static/archived_resources
        shutil.copy(filename, "static/novel_images")
        shutil.copy(filename, "static/archived_resources")
        shutil.copy(filename, "static/archived-images")

        # Save data to the database
        conn = sqlite3.connect(CAPDATABASE)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO captions (
                filename, width, height, text, background_color, font, font_size, font_color
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                filename,
                data["width"],  # Ensure box_size is passed in the form
                data["height"],
                data["text"],  # Ensure text is passed in the form
                data[
                    "background_color"
                ],  # Ensure background_color is passed in the form
                data["font"],  # Font choice passed in the form
                data["font_size"],  # Font size passed in the form
                data["font_color"],  # Font color passed in the form
            ),
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "filename": filename})
    except KeyError as e:
        # Handle missing fields in the form
        return (
            jsonify({"success": False, "error": f"Missing required field: {str(e)}"}),
            400,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/get_caption_data/<int:caption_id>", methods=["GET"])
def get_caption_data(caption_id):
    """Route to retrieve caption data by ID."""
    try:
        # Connect to the database
        conn = sqlite3.connect(CAPDATABASE)
        cursor = conn.cursor()

        # Query to get the caption data by ID
        cursor.execute("SELECT * FROM captions WHERE id = ?", (caption_id,))
        caption = cursor.fetchone()

        # Close the connection
        conn.close()

        if caption:
            caption_data = {
                "id": caption[0],
                "filename": caption[1],
                "box_size": caption[2],
                "text": caption[3],
                "background_color": caption[4],
                "font": caption[6],
                "font_size": caption[7],
                "font_color": caption[8],
            }
            return jsonify({"success": True, "caption": caption_data})
        else:
            return jsonify({"success": False, "error": "Caption not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/view_captions")
def view_captions():
    caption_images = glob.glob("static/captions_resources/*.png")
    return render_template("view_caption_data.html", caption_images=caption_images)


# --------------------
@app.route("/transfer_directories")
def transfer_directories():
    # List directories only in 'static' folder
    transfer_src = sorted([d for d in glob.glob("static/*") if os.path.isdir(d)])
    transfer_dst = sorted([d for d in glob.glob("static/*") if os.path.isdir(d)])

    # Count files in each directory
    src_with_file_counts = [
        (d, len([f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]))
        for d in transfer_src
    ]
    dst_with_file_counts = [
        (d, len([f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]))
        for d in transfer_dst
    ]

    # Pass data to the template
    return render_template(
        "transfer.html",
        transfer_src=src_with_file_counts,
        transfer_dst=dst_with_file_counts,
        data_src=len(transfer_src),
        data_dst=len(transfer_dst),
    )


@app.route("/transfer_src_to_dst", methods=["POST"])
def transfer_src_to_dst():
    # Get the selected source and destination
    src = request.form.get("src")
    dest = request.form.get("dest")

    if not src or not dest:
        return "Source or destination not selected!", 400

    # Ensure the source and destination directories exist
    if not os.path.isdir(src) or not os.path.isdir(dest):
        return "Invalid source or destination directory!", 400

    # Transfer all files from source to destination
    for filename in os.listdir(src):
        src_path = os.path.join(src, filename)
        dest_path = os.path.join(dest, filename)
        if os.path.isfile(src_path):
            shutil.copy(src_path, dest_path)

    return redirect(url_for("transfer_directories"))


# Route to handle the form submission
@app.route("/empty_0000_resources")
def empty_0000_resources():
    # Get the selected source and destination
    DIR = "static/0000_resources"
    for file in os.listdir(DIR):
        os.remove(os.path.join(DIR, file))
    return redirect(url_for("transfer_directories"))


# --------------------
# Route to show demos_and_narratives
@app.route("/demos_and_narratives")
def demos_and_narratives():
    return render_template("demos_and_narratives.html")


# --------------------
# JSON file to store video URLs
DATA_FILE = "youtube_videos.json"

# Ensure the JSON file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as file:
        json.dump([], file)  # Start with an empty list


def load_youtube_videos():
    """Load video URLs from the JSON file."""
    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_youtube_videos(videos):
    """Save video URLs to the JSON file."""
    with open(DATA_FILE, "w") as file:
        json.dump(videos, file, indent=4)


# --------------------
# Route to display YouTube Videos
@app.route("/youtube_videos", methods=["GET"])
def youtube_videos():
    videos = load_youtube_videos()
    return render_template("youtube_videos.html", videos=videos)


# --------------------
# Route to save a new video URL
@app.route("/add_youtube_video", methods=["POST"])
def add_youtube_video():
    data = request.get_json()
    if not data or "video_code" not in data:
        return jsonify({"error": "Invalid data"}), 400

    video_code = data["video_code"].strip()
    if not video_code:
        return jsonify({"error": "Empty video code"}), 400

    # Load existing videos and add the new one
    videos = load_youtube_videos()
    if video_code not in videos:  # Avoid duplicates
        videos.append(video_code)
        save_youtube_videos(videos)

    return jsonify({"message": "Video added successfully", "videos": videos})


# --------------------
# Route to retrieve all videos (for API usage)
@app.route("/get_youtube_videos", methods=["GET"])
def get_youtube_videos():
    videos = load_youtube_videos()
    return jsonify(videos)


# --------------------
# Route to display YouTube Videos JSON in a textarea
@app.route("/edit_youtube_videos", methods=["GET"])
def edit_youtube_videos():
    videos = load_youtube_videos()
    return render_template(
        "edit_youtubevideos.html", json_data=json.dumps(videos, indent=4)
    )


# --------------------
# Route to save edited JSON data
@app.route("/save_youtube_videos", methods=["POST"])
def save_youtube_videos_api():
    data = request.form.get("json_data")
    try:
        # Validate and parse the JSON data
        videos = json.loads(data)
        if not isinstance(videos, list):
            raise ValueError("Data must be a list.")
        save_youtube_videos(videos)
        return jsonify({"message": "Videos updated successfully!"}), 200
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400


# --------------------
@app.route("/utilitie", methods=["GET", "POST"])
def utilitie():
    if request.method == "POST":
        filename = request.form["filename"]
        filepath = "static/text_files"
        # Ensure the filepath and filename are safe and valid
        script_path = os.path.join(filepath, filename)
        if not os.path.exists(script_path):
            flash("File not found. Please check the filename and path.", "error")
            return redirect(url_for("utilities"))

        try:
            # Run the Python script or any command using subprocess
            if len(sys.argv) > 1:
                ARG = sys.argv[1]
                logit(f"Argument provided: {ARG}")
            else:
                ARG = ""
                logit("No argument provided")
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                check=True,
            )
            output = result.stdout
            logit(f"Script {script_path} executed successfully.")
        except subprocess.CalledProcessError as e:
            output = e.stderr
            logit(f"An error occurred while executing the script {script_path}: {e}")

        return render_template("utilitie.html", result=output)

    return render_template("utilitie.html")


@app.route("/bash", methods=["GET", "POST"])
def bash():
    if request.method == "POST":
        filename = request.form["filename"]
        arg = request.form["arg"]
        filepath = "static/text_files"
        # Ensure the filepath and filename are safe and valid
        script_path = os.path.join(filepath, filename)
        if not os.path.exists(script_path):
            flash("File not found. Please check the filename and path.", "error")
            return redirect(url_for("bash"))

        try:
            # Run the Python script or any command using subprocess

            cmd = ["/bin/bash", script_path, arg]
            logit(cmd)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout
            logit(f"Script {script_path} executed successfully.")
        except subprocess.CalledProcessError as e:
            output = e.stderr
            logit(f"An error occurred while executing the script {script_path}: {e}")

        return render_template("bash.html", result=output)

    return render_template("bash.html")


@app.route("/terminal_index")
def terminal_index():
    return render_template("terminal_index.html")


@app.route("/execute_command", methods=["POST"])
def execute_command():
    command = request.form.get("command")
    try:
        output = subprocess.check_output(
            command, shell=True, text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        output = e.output
    return jsonify({"output": output})


@app.route("/index_bash")
def index_bash():
    video = findvideos()
    return render_template("run_bash.html", video=video)


def findvideo_all():
    videoroot_directory = "static"
    MP4 = []
    for dirpath, dirnames, filenames in os.walk(videoroot_directory):
        for filename in filenames:
            if filename.endswith(".mp4"):  # and "Final" in filename:
                MP4.append(os.path.join(dirpath, filename))
    if MP4:
        last_video = session.get("last_video")
        new_video = random.choice([video for video in MP4 if video != last_video])
        session["last_video"] = new_video
        return new_video
    else:
        return None


@app.route("/run_bash", methods=["POST", "GET"])
def run_bash():
    bash_command = request.form.get("bash_command")

    try:
        result = subprocess.check_output(
            bash_command, shell=True, text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        result = e.output
    video = findvideos()
    return render_template("run_bash.html", result=result, video=video)


def findvideos():
    videoroot_directory = "static"
    MP4 = []
    for dirpath, dirnames, filenames in os.walk(videoroot_directory):
        for filename in filenames:
            if filename.endswith(".mp4"):  # and "Final" in filename:
                MP4.append(os.path.join(dirpath, filename))
    if MP4:
        last_video = session.get("last_video")
        new_video = random.choice([video for video in MP4 if video != last_video])
        session["last_video"] = new_video
        return new_video
    else:
        return None


@app.route("/editor", methods=["GET", "POST"])
def editor():
    """
    Flask route for '/editor'.
    Handles GET requests by listing all text files in 'TEXT_FILES_DIR' sorted based upon their last modification time. If a POST request occurs, it saves the given filename and corresponding content to file named after that with its original name appended as '.txt', if such an existing file exists; otherwise creates one new for you specified by user within form data (filename) on '/editor'.
    """
    if request.method == "POST":
        filename = request.form["filename"]
        text = request.form["text"]
        save_text_to_file(filename, text)
        return redirect(url_for("editor"))
    else:
        # files = os.listdir(TEXT_FILES_DIR)
        # files = files.sort(key=lambda x: os.path.getmtime(x))
        files = sorted(
            [
                file
                for file in os.listdir(TEXT_FILES_DIR)
                if os.path.isfile(os.path.join(TEXT_FILES_DIR, file))
            ],
            key=lambda x: os.path.getmtime(os.path.join(TEXT_FILES_DIR, x)),
            reverse=True,
        )

        logit(files)
        # files = sort_files_by_date(TEXT_FILES_DIR)
        return render_template("editor1.html", files=files)


"""
To use this application, an image must be selected. Then the text is entered into a text box. A font and a size is selected. You may then chose a font and caption background color. Click Generate Image. The text will be placed on the image as a caption. Then a speaker voice is chosen and you select create mp4. That will create the Video. 
"""
# --- App Initialization and Configuration ---
app.secret_key = "your_super_secret_key_here"
app.config["UPLOAD_FOLDER"] = "static"  # Main static folder
app.config["USER_UPLOADS_FOLDER"] = os.path.join(app.config["UPLOAD_FOLDER"], "results")
app.config["RESULTS_FOLDER"] = "static/results"
app.config["FONTS_DIR"] = "static/fonts"  # Ensure this path is correct
app.config["DEFAULT_IMAGE"] = "static/default.jpg"  # Ensure 'static/default.jpg' exists
app.config["UPLOAD_MEDIA"] = os.path.join("static", "sources")
app.config["UPLOAD_AUDIO"] = os.path.join("static", "results")
UPLOAD_AUDIO = "static/results"
PROJECT_DIR = os.path.join("static", "project_files")

# --- Define folder constants (use app.config where possible for consistency) ---
# RESULTS_FOLDER = 'static/results' # Already in app.config
# USER_UPLOADS_FOLDER = 'static/uploads' # Mismatch with app.config['USER_UPLOADS_FOLDER'] ('user_uploads') - Standardizing
IMAGE_DIRECTORY = app.config["USER_UPLOADS_FOLDER"]  # Use config for consistency
VIDEO_DIRECTORY = "static/results"  # Custom path for join_four source videos
CONVERT_UPLOAD_FOLDER = "static/convert_uploads"
CONVERT_OUTPUT_FOLDER = "static/convert_results"
COMPUTER_IMAGE_DIRECTORY = "static/computer_images"
RESULTS_FOLDER = "static/results"
# --------------------------------------------------
# DIRECTORIES
# --------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")
UPLOADS = os.path.join(STATIC, "uploads")
CLIPS = os.path.join(STATIC, "clips")
AUDIO = os.path.join(STATIC, "audio")
OUTPUT = os.path.join(STATIC, "output")
THUMBS = os.path.join(STATIC, "thumbs")
FONTS_DIR = os.path.join(STATIC, "fonts")
for p in [UPLOADS, CLIPS, AUDIO, OUTPUT, THUMBS, FONTS_DIR]:
    if not os.path.exists(p):
        os.makedirs(p)


def get_sorted_files_by_date(path, extensions=None):
    files = []
    for f in os.listdir(path):
        if not os.path.isfile(os.path.join(path, f)):
            continue
        if extensions and not f.endswith(extensions):
            continue
        full_path = os.path.join(path, f)
        mod_time = os.path.getmtime(full_path)
        files.append((f, mod_time))

    # Sort descending (newest first)
    files.sort(key=lambda x: x[1], reverse=True)

    # Return just the filenames
    return [file[0] for file in files]


# Example usage
image_exts = (".png", ".jpg", ".jpeg", ".JPG", ".JPEG", ".PNG")
audio_exts = (".mp3", ".wav", ".m4a", ".MP3", ".WAV", ".M4A")
video_exts = ".mp4"


# --- Create necessary folders ---
def create_necessary_folders():
    folders_to_create = [
        app.config["RESULTS_FOLDER"],
        app.config["USER_UPLOADS_FOLDER"],
        app.config["UPLOAD_MEDIA"],
        VIDEO_DIRECTORY,  # If it's a source, it should exist. If output, moviepy handles it. Let's ensure it.
        CONVERT_UPLOAD_FOLDER,
        CONVERT_OUTPUT_FOLDER,
        PROJECT_DIR,
    ]
    for folder in folders_to_create:
        if not os.path.exists(folder):
            os.makedirs(folder)
            ic(f"Created folder: {folder}")
        else:
            ic(f"Folder already exists: {folder}")


create_necessary_folders()

"""
@app.route('/favicon.ico')
def favicon():
    svg = '''
    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
        <circle cx="32" cy="32" r="30" fill="yellow" stroke="black" stroke-width="2"/>
        <text x="32" y="42" font-size="32" text-anchor="middle" fill="black" font-family="Arial">F</text>
    </svg>
    '''
    return Response(svg, mimetype='image/svg+xml')
"""


def safe_filename(text, max_words=6):
    words = text.split()[:max_words]
    base_name = "_".join(words)
    safe_name = re.sub(r"[^\w_.-]", "", base_name)
    return safe_name if safe_name else "captioned_media"


def get_font_files():
    if not os.path.isdir(app.config["FONTS_DIR"]):
        print(f"Warning: Font directory {app.config['FONTS_DIR']} not found.")
        return []
    try:
        fonts = [
            f for f in os.listdir(app.config["FONTS_DIR"]) if f.endswith(".ttf")
        ]  # Or other relevant extensions
        return sorted(fonts)
    except Exception as e:
        print(f"Error listing fonts: {e}")
        return []


def add_title_image(video_path, hex_color="#A52A2A"):
    directory_path = "temp"
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        ic(f"Directory '{directory_path}' created.")
    else:
        ic(f"Directory '{directory_path}' already exists.")

    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    ic(width, height)

    title_image_path = "static/assets/apps.png"
    padded_size = (width + 45, height + 45)

    x_position = (padded_size[0] - width) / 2
    y_position = (padded_size[1] - height) / 2

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    rgb_tuple = (r, g, b)
    ic(rgb_tuple)

    background_clip = ColorClip(
        padded_size, color=rgb_tuple, duration=video_clip.duration
    )

    video_on_background = video_clip.set_position((x_position, y_position))
    padded_video_clip = CompositeVideoClip(
        [background_clip, video_on_background], size=padded_size
    )

    original_img = Image.open(title_image_path)
    resized_img = original_img.resize(padded_video_clip.size, resample=Image.LANCZOS)
    resized_img_path = os.path.join("temp", f"resized_title_{uuid.uuid4().hex[:8]}.png")
    resized_img.save(resized_img_path)

    title_image = ImageClip(resized_img_path).set_duration(video_clip.duration)
    title_image = title_image.set_position((0, -5))

    composite_clip = CompositeVideoClip([padded_video_clip, title_image])

    if not composite_clip.audio:
        mp3_files = glob.glob("static/music/*.mp3")
        ic(mp3_files)
        if mp3_files:
            random.shuffle(mp3_files)
            mp_music_path = random.choice(mp3_files)
            music_clip = AudioFileClip(mp_music_path)
            music_clip = music_clip.subclip(
                0, min(music_clip.duration, video_clip.duration)
            )
            fade_duration = 1.0
            if music_clip.duration > 2 * fade_duration:
                music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(
                    fade_duration
                )
            composite_clip = composite_clip.set_audio(music_clip)
            ic(f"Audio added: {mp_music_path}")
        else:
            ic("Warning: No MP3 files found for background music.")

    output_filename = f"titled_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(app.config["RESULTS_FOLDER"], output_filename)

    ic(output_path)
    composite_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    video_clip.close()
    if "padded_video_clip" in locals():
        padded_video_clip.close()
    if "composite_clip" in locals():
        composite_clip.close()
    if "music_clip" in locals():
        music_clip.close()
    temp_exp = "static/temp_exp/TEMP2X.mp4"

    shutil.copy(output_path, temp_exp)
    return output_path


def add_titleimage(video_path, hex_color="#A52A2A"):
    directory_path = "temp"
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        ic(f"Directory '{directory_path}' created.")
    else:
        ic(f"Directory '{directory_path}' already exists.")

    video_clip = VideoFileClip(video_path)
    width, height = video_clip.size
    ic(width, height)

    title_image_path = "static/assets/sentient.png"
    padded_size = (width + 90, height + 90)

    x_position = (padded_size[0] - width) / 2
    y_position = (padded_size[1] - height) / 2

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    rgb_tuple = (r, g, b)
    ic(rgb_tuple)

    background_clip = ColorClip(
        padded_size, color=rgb_tuple, duration=video_clip.duration
    )

    video_on_background = video_clip.set_position((x_position, y_position))
    padded_video_clip = CompositeVideoClip(
        [background_clip, video_on_background], size=padded_size
    )

    original_img = Image.open(title_image_path)
    resized_img = original_img.resize(padded_video_clip.size, resample=Image.LANCZOS)
    resized_img_path = os.path.join("temp", f"resized_title_{uuid.uuid4().hex[:8]}.png")
    resized_img.save(resized_img_path)

    title_image = ImageClip(resized_img_path).set_duration(video_clip.duration)
    title_image = title_image.set_position((0, -5))

    composite_clip = CompositeVideoClip([padded_video_clip, title_image])

    if not composite_clip.audio:
        mp3_files = glob.glob("static/music/*.mp3")
        if mp3_files:
            random.shuffle(mp3_files)
            mp_music_path = random.choice(mp3_files)
            music_clip = AudioFileClip(mp_music_path)
            music_clip = music_clip.subclip(
                0, min(music_clip.duration, video_clip.duration)
            )
            fade_duration = 1.0
            if music_clip.duration > 2 * fade_duration:
                music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(
                    fade_duration
                )
            composite_clip = composite_clip.set_audio(music_clip)
            ic(f"Audio added: {mp_music_path}")
        else:
            ic("Warning: No MP3 files found for background music.")

    output_filename = f"titled_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(PROJECT_DIR, output_filename)

    ic(output_path)
    composite_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    video_clip.close()
    if "padded_video_clip" in locals():
        padded_video_clip.close()
    if "composite_clip" in locals():
        composite_clip.close()
    if "music_clip" in locals():
        music_clip.close()

    return output_path


# ==============================================================================
# ==== MODIFIED TEXT DRAWING FUNCTION AND ITS HELPERS ==========================
# ==============================================================================


def _get_text_dimensions(draw, text, font):
    """Helper to get text dimensions, supporting older and newer Pillow versions."""
    try:
        # Modern, more accurate method
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older versions
        return draw.textsize(text, font=font)


def _wrap_text_by_pixel_width(draw, text, font, max_width):
    """
    A more accurate text wrapper that breaks lines based on pixel width,
    not character count.
    """
    words = text.split()
    if not words:
        return []

    lines = []
    current_line = words[0]
    for word in words[1:]:
        # Check if adding the next word exceeds the max width
        test_line = f"{current_line} {word}"
        width, _ = _get_text_dimensions(draw, test_line, font)
        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)  # Add the last line
    return lines


def draw_text_on_image(
    image_path,
    text_to_draw,
    font_name,
    font_size,
    text_color,
    box_color,
    box_position,
    padding=10,
    output_filename="output.png",
):
    """
    Draws text inside a full-width, semi-transparent box on an image,
    with control over vertical and horizontal alignment.

    Args:
        image_path (str): Path to the input image.
        text_to_draw (str): The text content for the caption.
        font_name (str): The filename of the .ttf font file.
        font_size (int): The size of the font.
        text_color (str): Color of the text.
        box_color (str): Color of the background box.
        box_position (str): Position key, e.g., 'top_left', 'bottom_center'.
        padding (int): Padding inside the box.
        output_filename (str): The name of the output file.
    """
    try:
        if not os.path.exists(image_path):
            print(f"Error: Image file for drawing not found at {image_path}")
            return None

        img = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size

        font_path = (
            os.path.join(app.config["FONTS_DIR"], font_name) if font_name else None
        )
        if not font_path or not os.path.exists(font_path):
            print(f"Font {font_path or font_name} not found. Using a fallback font.")
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                print("Arial not found, using default PIL font.")
                font = ImageFont.load_default()
        else:
            font = ImageFont.truetype(font_path, font_size)

        text_area_max_width = img_width - (2 * padding)
        wrapped_lines = _wrap_text_by_pixel_width(
            draw, text_to_draw, font, text_area_max_width
        )

        line_heights = [
            _get_text_dimensions(draw, line, font)[1] for line in wrapped_lines
        ]
        line_spacing = int(font_size * 0.2)
        total_text_height = (
            sum(line_heights) + max(0, len(wrapped_lines) - 1) * line_spacing
        )

        box_width = img_width
        box_height = total_text_height + (2 * padding)
        box_x = 0

        # Vertical positioning for the box
        if "top" in box_position:
            box_y = 0
        elif "bottom" in box_position:
            box_y = img_height - box_height
        elif "center" in box_position:
            box_y = (img_height - box_height) // 2
        else:  # Default to bottom
            box_y = img_height - box_height

        box_y = max(0, box_y)

        if box_color != "transparent":
            try:
                box_color_rgba = ImageColor.getrgb(box_color) + (200,)
            except ValueError:
                box_color_rgba = (0, 0, 0, 200)

            draw.rectangle(
                [box_x, box_y, box_x + box_width, box_y + box_height],
                fill=box_color_rgba,
            )

        current_y = box_y + padding
        for i, line in enumerate(wrapped_lines):
            line_width, _ = _get_text_dimensions(draw, line, font)

            # Horizontal positioning for the text
            if "left" in box_position:
                text_x = padding
            elif "right" in box_position:
                text_x = img_width - line_width - padding
            else:  # Default to center
                text_x = (img_width - line_width) / 2

            try:
                text_color_rgb = ImageColor.getrgb(text_color)
            except ValueError:
                text_color_rgb = (255, 255, 255)

            draw.text((text_x, current_y), line, font=font, fill=text_color_rgb)
            current_y += line_heights[i] + line_spacing

        output_path = os.path.join(app.config["RESULTS_FOLDER"], output_filename)
        img.save(output_path)
        ic(f"output_path> {output_path}")
        im = Image.open(output_path).convert("RGB")
        new_output_path = output_path[:-3] + "jpg"
        ic(f"new_output_path> {new_output_path}")
        avt = "static/sources/use.jpg"
        im.save(new_output_path)
        shutil.copy(new_output_path, avt)

        return output_filename

    except Exception as e:
        print(f"Error in draw_text_on_image: {e}")
        traceback.print_exc()
        return None


# ==============================================================================
# ==== END OF MODIFIED SECTION ===============================================
# ==============================================================================

# ---------------
# TTS CONFIGURATION (Kokoro ONNX Native + Multi-Voice Pause Engine)
# ---------------
KOKORO_TTS_URL = "http://localhost:8880/v1/audio/speech"  # Optional Docker fallback endpoint
ASSISTANT_VOICE = "af_heart"
OUPUT_MP3_PATH = ""

KOKORO_VOICES = {
    "⭐ Top Recommended": [
        ("af_heart", "Heart (Female - Expressive, Warm)"),
        ("af_bella", "Bella (Female - Conversational, Natural)"),
        ("af_nicole", "Nicole (Female - Crisp, Friendly)"),
        ("af_sarah", "Sarah (Female - Storyteller, Engaging)"),
        ("am_adam", "Adam (Male - Deep Narrator)"),
        ("am_echo", "Echo (Male - Balanced, Clear)"),
        ("am_michael", "Michael (Male - Warm, Natural)"),
        ("am_onyx", "Onyx (Male - Rich Baritone)"),
        ("bf_emma", "Emma (British Female - BBC Style)"),
        ("bm_george", "George (British Male - Classic)"),
        ("bm_daniel", "Daniel (British Male - Articulate)"),
    ],
    "🇺🇸 American Female": [
        ("af_heart", "Heart"),
        ("af_bella", "Bella"),
        ("af_nicole", "Nicole"),
        ("af_sarah", "Sarah"),
        ("af_nova", "Nova"),
        ("af_river", "River"),
        ("af_sky", "Sky"),
        ("af_alloy", "Alloy"),
        ("af_aoede", "Aoede"),
        ("af_jessica", "Jessica"),
        ("af_kore", "Kore"),
    ],
    "🇺🇸 American Male": [
        ("am_adam", "Adam"),
        ("am_echo", "Echo"),
        ("am_eric", "Eric"),
        ("am_fenrir", "Fenrir"),
        ("am_liam", "Liam"),
        ("am_michael", "Michael"),
        ("am_onyx", "Onyx"),
        ("am_puck", "Puck"),
        ("am_santa", "Santa"),
    ],
    "🇬🇧 British Female": [
        ("bf_alice", "Alice"),
        ("bf_emma", "Emma"),
        ("bf_isabella", "Isabella"),
        ("bf_lily", "Lily"),
    ],
    "🇬🇧 British Male": [
        ("bm_daniel", "Daniel"),
        ("bm_fable", "Fable"),
        ("bm_george", "George"),
        ("bm_lewis", "Lewis"),
    ],
    "🌍 European (French, Italian, Spanish)": [
        ("ff_siwis", "Siwis (French Female)"),
        ("if_sara", "Sara (Italian Female)"),
        ("im_nicola", "Nicola (Italian Male)"),
        ("ef_dora", "Dora (Spanish Female)"),
        ("em_alex", "Alex (Spanish Male)"),
        ("em_santa", "Santa (Spanish Male)"),
    ],
    "🇧🇷 Brazilian Portuguese": [
        ("pf_dora", "Dora (Portuguese Female)"),
        ("pm_alex", "Alex (Portuguese Male)"),
        ("pm_santa", "Santa (Portuguese Male)"),
    ],
    "🌏 Asian (Japanese, Chinese, Hindi)": [
        ("jf_alpha", "Alpha (Japanese Female)"),
        ("jf_gongitsune", "Gongitsune (Japanese Female)"),
        ("jf_nezumi", "Nezumi (Japanese Female)"),
        ("jf_tebukuro", "Tebukuro (Japanese Female)"),
        ("jm_kumo", "Kumo (Japanese Male)"),
        ("zf_xiaobei", "Xiaobei (Chinese Female)"),
        ("zf_xiaoni", "Xiaoni (Chinese Female)"),
        ("zf_xiaoxiao", "Xiaoxiao (Chinese Female)"),
        ("zf_xiaoyi", "Xiaoyi (Chinese Female)"),
        ("hf_alpha", "Alpha (Hindi Female)"),
        ("hf_beta", "Beta (Hindi Female)"),
        ("hm_omega", "Omega (Hindi Male)"),
        ("hm_psi", "Psi (Hindi Male)"),
    ],
}

_KOKORO_ONNX_INSTANCE = None


def get_kokoro_onnx():
    """
    Lazy singleton loader for local Kokoro ONNX model.
    Runs on CPU with zero Docker overhead, highly optimized for Ryzen CPUs.
    """
    global _KOKORO_ONNX_INSTANCE
    if _KOKORO_ONNX_INSTANCE is not None:
        return _KOKORO_ONNX_INSTANCE

    onnx_path = os.path.join(BASE_DIR, "models", "kokoro", "kokoro-v1.0.onnx")
    voices_path = os.path.join(BASE_DIR, "models", "kokoro", "voices-v1.0.bin")

    if os.path.exists(onnx_path) and os.path.exists(voices_path):
        try:
            from kokoro_onnx import Kokoro
            ic(f"Initializing native Kokoro ONNX model: {onnx_path}")
            _KOKORO_ONNX_INSTANCE = Kokoro(onnx_path, voices_path)
            ic("Native Kokoro ONNX model loaded successfully into memory.")
            return _KOKORO_ONNX_INSTANCE
        except Exception as e:
            ic(f"Error loading native Kokoro ONNX: {e}")
            traceback.print_exc()
            return None
    else:
        ic(f"Kokoro model files not found at {onnx_path} or {voices_path}")
        return None


def get_kokoro_voice_lang(voice_name):
    """
    Map Kokoro voice ID prefix to ISO language code.
    """
    if not voice_name:
        return "en-us"
    prefix = voice_name[0].lower()
    mapping = {
        "a": "en-us",
        "b": "en-gb",
        "e": "es",
        "f": "fr-fr",
        "h": "hi",
        "i": "it",
        "j": "ja",
        "p": "pt-br",
        "z": "zh",
    }
    return mapping.get(prefix, "en-us")


def _generate_mp3_with_kokoro_api(text_to_speak, output_mp3_path, voice="af_heart", speed=1.0):
    """
    HTTP API Fallback for Kokoro TTS Docker container.
    """
    try:
        out_dir = os.path.dirname(output_mp3_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        text_clean = text_to_speak.replace("*", "").replace("…", ", ").strip()
        payload = {
            "model": "kokoro",
            "voice": voice,
            "speed": float(speed),
            "format": "mp3",
            "input": text_clean,
        }
        response = requests.post(KOKORO_TTS_URL, json=payload, timeout=600)
        if response.status_code != 200:
            return None, f"Kokoro API returned status {response.status_code}: {response.text}"
        with open(output_mp3_path, "wb") as f:
            f.write(response.content)
        return output_mp3_path, None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to Kokoro TTS server. Please ensure local ONNX model or Docker is running."
    except Exception as e:
        return None, f"Kokoro API fallback error: {e}"


def synthesize_story_with_pauses(text_to_speak, output_mp3_path, default_voice="af_heart", default_speed=1.0):
    """
    Synthesizes speech with full markup support:
      [voice=ID]   - switch speaker character (e.g. am_adam, af_sarah, bf_alice)
      [pause=X]    - insert exact X seconds of silence (e.g. [pause=2.5])
      [slow]       - speak slower (0.85x)
      [fast]       - speak faster (1.15x)
      [speed=X]    - set speaking speed (e.g. [speed=0.95])
      [loud]       - boost volume (+4dB / 1.5x)
      [soft]       - soften volume (-4dB / 0.6x)
      [whisper]    - whisper mode (0.45x volume, 0.85x speed)
      [volume=X]   - manual amplitude multiplier
    Uses native Kokoro ONNX in-memory if available, falling back to Kokoro API if needed.
    """
    kokoro = get_kokoro_onnx()
    if kokoro is not None:
        try:
            import numpy as np
            import soundfile as sf

            out_dir = os.path.dirname(output_mp3_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            # Normalize text breaks for inline tags if any
            norm_text = text_to_speak.replace("\r\n", "\n").replace("\r", "\n")
            norm_text = re.sub(r"(\[pause=[^\]]+\])\s*(\S)", r"\1\n\2", norm_text)
            norm_text = re.sub(r"(\S)\s*(\[voice=[^\]]+\])", r"\1\n\2", norm_text)

            lines = [l.strip() for l in norm_text.splitlines() if l.strip()]
            if not lines:
                return None, "Text is empty."

            sample_rate = 24000
            chunks = []
            current_voice = default_voice
            available_voices = set(kokoro.get_voices())

            for idx, line in enumerate(lines):
                # Voice tag
                vm = re.search(r"\[voice=([a-zA-Z0-9_-]+)\]", line, re.IGNORECASE)
                if vm:
                    requested_voice = vm.group(1).lower()
                    if requested_voice in available_voices:
                        current_voice = requested_voice
                    else:
                        ic(f"Voice '{requested_voice}' not in Kokoro model, keeping '{current_voice}'")

                # Speed tag
                speed = float(default_speed)
                sm = re.search(r"\[speed=([\d.]+)\]", line, re.IGNORECASE)
                if sm:
                    try:
                        speed = float(sm.group(1))
                    except ValueError:
                        speed = float(default_speed)
                elif "[slow]" in line.lower():
                    speed = max(0.5, float(default_speed) * 0.85)
                elif "[fast]" in line.lower():
                    speed = min(2.0, float(default_speed) * 1.15)

                # Volume tag
                vol_mult = 1.0
                volm = re.search(r"\[volume=([\d.]+)\]", line, re.IGNORECASE)
                if volm:
                    try:
                        vol_mult = float(volm.group(1))
                    except ValueError:
                        vol_mult = 1.0
                elif "[loud]" in line.lower():
                    vol_mult = 1.5
                elif "[soft]" in line.lower():
                    vol_mult = 0.6
                elif "[whisper]" in line.lower():
                    vol_mult = 0.45
                    speed = max(0.5, speed * 0.85)

                # Pause tag
                pause_sec = None
                pm = re.search(r"\[pause=([\d.]+)\]", line, re.IGNORECASE)
                if pm:
                    try:
                        pause_sec = float(pm.group(1))
                    except ValueError:
                        pause_sec = 0.5
                else:
                    # Natural gap between lines or small trailing padding
                    pause_sec = 0.5 if idx < len(lines) - 1 else 0.4

                # Clean text: strip all bracketed tags and unwanted symbols
                clean_line = re.sub(r"\[.*?\]", "", line).strip()
                clean_line = clean_line.replace("*", "").replace("…", ", ")

                if clean_line:
                    lang = get_kokoro_voice_lang(current_voice)
                    ic(f"Kokoro ONNX [{idx+1}/{len(lines)}]: '{clean_line[:60]}' [voice={current_voice}, speed={speed:.2f}, vol={vol_mult:.2f}]")
                    samples, sr = kokoro.create(clean_line, voice=current_voice, speed=speed, lang=lang)
                    sample_rate = sr
                    if vol_mult != 1.0:
                        samples = np.clip(samples * vol_mult, -1.0, 1.0)
                    chunks.append(samples)

                if pause_sec and pause_sec > 0:
                    silence_samples = np.zeros(int(sample_rate * pause_sec), dtype=np.float32)
                    chunks.append(silence_samples)

            if not chunks:
                return None, "No audio content generated from text."

            combined_audio = np.concatenate(chunks)

            # Write temporary WAV, convert with ffmpeg to target MP3
            temp_wav_path = output_mp3_path + f".tmp_{uuid.uuid4().hex[:6]}.wav"
            sf.write(temp_wav_path, combined_audio, sample_rate)

            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                temp_wav_path,
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "192k",
                output_mp3_path,
            ]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

            ic(f"Kokoro ONNX: MP3 created successfully at {output_mp3_path} ({len(combined_audio)/sample_rate:.2f}s)")
            return output_mp3_path, None

        except Exception as e:
            ic(f"Kokoro ONNX synthesis failed, falling back to API: {e}")
            traceback.print_exc()

    # Fallback to Kokoro HTTP API
    return _generate_mp3_with_kokoro_api(text_to_speak, output_mp3_path, voice=default_voice, speed=default_speed)


def generate_mp3_with_kokoro_tts(text_to_speak, OUPUT_MP3_PATH, voice="af_heart", speed=1.0):
    """
    Generate MP3 speech using Kokoro TTS (ONNX native or API) and save to output path.
    Supports pauses [pause=X], voice switching [voice=Y], speed [slow]/[fast], volume [loud]/[soft].
    """
    return synthesize_story_with_pauses(text_to_speak, OUPUT_MP3_PATH, default_voice=voice, default_speed=speed)


# --- Main Application Routes ---


@app.route("/index2", methods=["GET", "POST"])
def index2():
    ic("Entering index route")
    padding = 1
    error_message = None

    # Default image setup
    current_base_image_path_relative_to_static = app.config["DEFAULT_IMAGE"]
    if request.method == "POST":
        current_base_image_path_relative_to_static = request.form.get(
            "current_base_image_for_form", app.config["DEFAULT_IMAGE"]
        )

    # Handle file upload
    uploaded_file = request.files.get("image_file")
    if uploaded_file and uploaded_file.filename != "":
        filename = secure_filename(uploaded_file.filename)
        save_path = os.path.join(app.config["USER_UPLOADS_FOLDER"], filename)
        try:
            uploaded_file.save(save_path)
            current_base_image_path_relative_to_static = os.path.join(
                os.path.basename(app.config["USER_UPLOADS_FOLDER"]), filename
            )
            ic(
                f"Uploaded image is now base image: {current_base_image_path_relative_to_static}"
            )
        except Exception as e:
            ic(f"Error saving uploaded base image: {e}")
            error_message = f"Could not save uploaded image: {e}"
            current_base_image_path_relative_to_static = request.form.get(
                "current_base_image_for_form", app.config["DEFAULT_IMAGE"]
            )

    # Setup image display and data
    image_to_display_url = url_for(
        "static", filename=current_base_image_path_relative_to_static
    )
    actual_source_image_system_path = os.path.join(
        app.config["UPLOAD_FOLDER"], current_base_image_path_relative_to_static
    )

    form_data = request.form.to_dict()
    caption_text = form_data.get(
        "caption_text",
        "You are Aphrodite, a wise, graceful, and sweet AI assistant inspired by the Greek goddess of love. You have a deep understanding of programming, especially Python and AI-related tech.",
    )
    current_fonts_list = get_font_files()
    selected_font_name = form_data.get(
        "font_name", current_fonts_list[0] if current_fonts_list else ""
    )
    font_size = int(form_data.get("font_size", 24))
    text_color = form_data.get("text_color", "#FFFFFF")
    box_color = form_data.get("box_color", "#000000")
    transparent_box = form_data.get("transparent_box")
    if transparent_box == "on":
        box_color = "transparent"

    box_position_key = form_data.get("box_position", "bottom_center")

    # Available Kokoro voices (dynamically loaded from all supported categories)
    supported_kokoro_voices = list(dict.fromkeys([v_id for group in KOKORO_VOICES.values() for v_id, _ in group]))

    selected_voice = form_data.get("speaker_voice", "af_heart")
    ic(
        f"Form Data: Caption='{caption_text}', Font='{selected_font_name}', Size={font_size}"
    )
    ic(f"Selected Kokoro voice: '{selected_voice}'")

    result_image_filename = form_data.get("generated_image_filename")
    video_filename_to_display = None

    if request.method == "POST":
        action = request.form.get("action")
        ic(f"Action requested: {action}")

        # -------------------------------
        # 1️⃣ GENERATE IMAGE WITH CAPTION
        # -------------------------------
        if action == "generate_image":
            if not caption_text:
                error_message = "Caption text cannot be empty."
            elif not os.path.exists(actual_source_image_system_path):
                error_message = (
                    f"Source image not found: {actual_source_image_system_path}."
                )
            else:
                output_basename = (
                    safe_filename(caption_text) + f"_{uuid.uuid4().hex[:6]}"
                )
                output_image_filename_ext = output_basename + ".png"
                result_image_filename = draw_text_on_image(
                    actual_source_image_system_path,
                    caption_text,
                    selected_font_name,
                    font_size,
                    text_color,
                    box_color,
                    box_position_key,
                    padding=20,
                    output_filename=output_image_filename_ext,
                )
                if result_image_filename:
                    image_to_display_url = url_for(
                        "serve_result", filename=result_image_filename
                    )
                    ic(f"Image generated successfully: {result_image_filename}")
                else:
                    error_message = "Failed to generate image. Check logs."
                    result_image_filename = None

        # -------------------------------
        # 2️⃣ CREATE MP4 WITH KOKORO AUDIO
        # -------------------------------
        elif action == "create_mp4":
            caption_for_audio = request.form.get("caption_for_audio", caption_text)
            source_captioned_image_filename = request.form.get(
                "generated_image_filename"
            )

            if not source_captioned_image_filename:
                error_message = "No captioned image specified. Generate an image first."
            elif not os.path.exists(
                os.path.join(
                    app.config["RESULTS_FOLDER"], source_captioned_image_filename
                )
            ):
                error_message = (
                    f"Captioned image '{source_captioned_image_filename}' not found."
                )
            elif not caption_for_audio:
                error_message = "Caption for audio is missing."
            else:
                image_to_display_url = url_for(
                    "serve_result", filename=source_captioned_image_filename
                )
                result_image_filename = source_captioned_image_filename

                base_name_for_media = source_captioned_image_filename.rsplit(".", 1)[0]
                mp3_filename_ext = base_name_for_media + ".mp3"
                mp3_full_path = os.path.join(
                    app.config["RESULTS_FOLDER"], mp3_filename_ext
                )
                mp4_filename_ext = base_name_for_media + ".mp4"
                mp4_full_path = os.path.join(
                    app.config["RESULTS_FOLDER"], mp4_filename_ext
                )

                # Generate MP3 using Kokoro
                generated_mp3_path, mp3_gen_error = generate_mp3_with_kokoro_tts(
                    caption_for_audio, mp3_full_path, voice=selected_voice
                )

                if not generated_mp3_path:
                    error_message = f"Failed to generate MP3: {mp3_gen_error}"
                else:
                    try:
                        ffprobe_cmd = [
                            "ffprobe",
                            "-v",
                            "error",
                            "-show_entries",
                            "format=duration",
                            "-of",
                            "default=noprint_wrappers=1:nokey=1",
                            generated_mp3_path,
                        ]
                        duration_process = subprocess.run(
                            ffprobe_cmd,
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        audio_duration = float(duration_process.stdout.strip())

                        # Append 1 second silence
                        silence_appended_mp3 = mp3_full_path.replace(
                            ".mp3", "_extended.mp3"
                        )
                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-f",
                                "lavfi",
                                "-i",
                                "anullsrc=r=44100:cl=stereo",
                                "-t",
                                "1",
                                "-q:a",
                                "9",
                                "silence.mp3",
                            ],
                            check=True,
                        )
                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-i",
                                f"concat:{generated_mp3_path}|silence.mp3",
                                "-acodec",
                                "copy",
                                silence_appended_mp3,
                            ],
                            check=True,
                        )
                        os.remove("silence.mp3")
                        generated_mp3_path = silence_appended_mp3
                        ic(f"Kokoro: Appended 1s silence to {generated_mp3_path}")
                        mp3use = "static/sources/use.mp3"
                        shutil.copy(mp3_full_path, mp3use)
                        ffmpeg_mp4_cmd = [
                            "ffmpeg",
                            "-y",
                            "-loop",
                            "1",
                            "-i",
                            os.path.join(
                                app.config["RESULTS_FOLDER"],
                                source_captioned_image_filename,
                            ),
                            "-i",
                            generated_mp3_path,
                            "-c:v",
                            "libx264",
                            "-tune",
                            "stillimage",
                            "-c:a",
                            "aac",
                            "-b:a",
                            "192k",
                            "-pix_fmt",
                            "yuv420p",
                            "-shortest",
                            mp4_full_path,
                        ]
                        subprocess.run(
                            ffmpeg_mp4_cmd,
                            check=True,
                            timeout=60,
                            capture_output=True,
                            text=True,
                        )
                        video_filename_to_display = mp4_filename_ext
                        ic(f"MP4 generated successfully: {mp4_full_path}")

                    except subprocess.CalledProcessError as e:
                        error_message = (
                            f"FFmpeg/FFprobe error (MP4): {e.stderr or str(e)}"
                        )
                    except FileNotFoundError:
                        error_message = "FFmpeg/FFprobe not found."
                    except subprocess.TimeoutExpired:
                        error_message = "FFmpeg/FFprobe (MP4) timed out."
                    except Exception as e:
                        error_message = f"Error during MP4 creation: {e}"
                        traceback.print_exc()

            if error_message and video_filename_to_display:
                video_filename_to_display = None
            if source_captioned_image_filename and os.path.exists(
                os.path.join(
                    app.config["RESULTS_FOLDER"], source_captioned_image_filename
                )
            ):
                image_to_display_url = url_for(
                    "serve_result", filename=source_captioned_image_filename
                )
                result_image_filename = source_captioned_image_filename

    # -------------------------------
    # TEMPLATE RENDER
    # -------------------------------
    final_error_to_display = error_message
    current_values = {
        "caption_text": caption_text,
        "font_name": selected_font_name,
        "font_size": font_size,
        "text_color": text_color,
        "box_color": box_color,
        "transparent_box": transparent_box,
        "box_position": box_position_key,
        "speaker_voice": selected_voice,
    }

    ic(
        f"Final state for template: result_image='{result_image_filename}', video='{video_filename_to_display}', error='{final_error_to_display}'"
    )
    ic(f"Current values for form re-population: {current_values}")
    # original colors index6.html
    return render_template(
        "index6.html",
        fonts=current_fonts_list,
        all_speakers=supported_kokoro_voices,
        current_values=current_values,
        image_to_display=image_to_display_url,
        result_image_filename=result_image_filename,
        video_filename_to_display=video_filename_to_display,
        current_base_image_for_form=current_base_image_path_relative_to_static,
        error=final_error_to_display,
    )


@app.route("/results/<filename>")
def serve_result(filename):
    return send_from_directory(app.config["RESULTS_FOLDER"], filename)


@app.route("/join_four")
def join_four():
    # Ensure VIDEO_DIRECTORY exists and is readable
    if not os.path.isdir(VIDEO_DIRECTORY):
        flash(f"Video source directory not found: {VIDEO_DIRECTORY}")
        return render_template("join_four.html", video_files=[])
    # video_files = [f for f in os.listdir(VIDEO_DIRECTORY) if f.endswith('.mp4')]
    video_files = get_sorted_files_by_date(VIDEO_DIRECTORY, extensions=video_exts)
    ic(video_files)
    return render_template("join_four.html", video_files=video_files)


@app.route("/merge", methods=["POST"])
def merge():
    selected_order = {}
    for key, value in request.form.items():
        if key.startswith("order_"):
            video_filename = key.replace("order_", "")
            try:
                position = int(value)
                selected_order[position] = video_filename
            except ValueError:
                flash("Invalid position value submitted.")
                return redirect(url_for("join_four"))
    ic(selected_order)

    if not (
        4 <= len(selected_order.values()) <= 4
        and len(set(selected_order.values())) == len(selected_order.values())
        and all(1 <= pos <= len(selected_order) for pos in selected_order.keys())
    ):
        flash("Please assign a unique position (1–4) to four different videos.")
        return redirect(url_for("join_four"))

    ordered_filenames = [selected_order[i] for i in sorted(selected_order.keys())]
    ic(ordered_filenames)

    clips = []
    final_clip = None
    try:
        for name in ordered_filenames:
            video_path = os.path.join(VIDEO_DIRECTORY, name)
            ic(video_path)
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file {name} not found.")
            clips.append(VideoFileClip(video_path))

        output_filename = f"merged_{uuid.uuid4().hex[:6]}.mp4"
        merged_video_path = os.path.join(app.config["RESULTS_FOLDER"], output_filename)

        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            merged_video_path, codec="libx264", audio_codec="aac"
        )

    except Exception as e:
        flash(f"Error during merging or processing: {e}")
        ic(f"Error merging: {e}")
        traceback.print_exc()
        return redirect(url_for("join_four"))
    finally:
        for clip in clips:
            clip.close()
        if final_clip:
            final_clip.close()

    try:
        video_with_title_path = add_title_image(
            merged_video_path, hex_color="#A52A2A"
        )  # add_title_image returns path
        ic(f"Video with title: {video_with_title_path}")
        # Pass the relative path from 'static' for url_for
        final_video_relative_path = os.path.relpath(
            video_with_title_path, app.config["UPLOAD_FOLDER"]
        )
        return render_template(
            "index1.html", output_path=final_video_relative_path
        )  # Ensure index1.html can display this
    except Exception as e:
        flash(f"Error adding title image: {e}")
        ic(f"Error adding title: {e}")
        traceback.print_exc()
        # Fallback to serving the merged video without title if title addition fails
        final_video_relative_path = os.path.relpath(
            merged_video_path, app.config["UPLOAD_FOLDER"]
        )
        return render_template(
            "index1.html",
            output_path=final_video_relative_path,
            error=f"Title addition failed: {e}",
        )


@app.route("/video/<filename>")
def serve_video(
    filename,
):  # Source videos for merging (if needed to be served directly)
    return send_from_directory(VIDEO_DIRECTORY, filename)


IMAGE_DIRECTORY = "./static/sized_images"
COMPUTER_IMAGE_DIRECTORY = "./static/computer_images"


# -------------------------------------------------
# Utility: Ensure images are resized to 512x768
# -------------------------------------------------
def ensure_resized(directory):
    """
    Check and resize all images in a directory.
    A blurred background is created by resizing the original image to 512x768.
    The original image is then resized to fit a max-width of 512, maintaining aspect ratio,
    and pasted onto the blurred background.
    Images already 512x768 are skipped.
    """
    ic(f"Checking directory: {directory}")
    if not os.path.isdir(directory):
        ic(f"Directory not found: {directory}")
        return []

    resized_files = []
    for filename in os.listdir(directory):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(directory, filename)
        try:
            with Image.open(image_path) as img:
                original_width, original_height = img.size

                # Skip if already the target size
                if (original_width, original_height) == (512, 768):
                    ic(f"Image already correct size: {filename}")
                    resized_files.append(filename)
                    continue

                ic(
                    f"Processing {filename} from {original_width}x{original_height} → 512x768 composite"
                )

                # 1. Create blurred background
                img_rgb = img.convert("RGB")
                background = img_rgb.resize((512, 768), Image.LANCZOS)
                background = background.filter(ImageFilter.GaussianBlur(15))

                # 2. Resize original to fit within 512 width, maintaining aspect ratio
                aspect_ratio = original_height / original_width
                new_width = 512
                new_height = int(new_width * aspect_ratio)

                # If new height exceeds 768, resize based on height instead
                if new_height > 768:
                    new_height = 768
                    new_width = int(new_height / aspect_ratio)

                foreground = img.resize((new_width, new_height), Image.LANCZOS)

                # 3. Paste the foreground onto the background
                paste_x = (512 - new_width) // 2
                paste_y = (768 - new_height) // 2

                # Use foreground's alpha channel as mask if it exists
                if foreground.mode == "RGBA":
                    background.paste(foreground, (paste_x, paste_y), foreground)
                else:
                    background.paste(foreground, (paste_x, paste_y))

                # 4. Save the composite image
                background.save(image_path, quality=95)
                resized_files.append(filename)

        except Exception as e:
            ic(f"Error processing {filename}: {e}")
            continue
    return resized_files


# -------------------------------------------------
# resize
def fix_image_before_ffmpeg(image_path):
    """
    Ensure image is 512x768, RGB, and in .jpg format for FFmpeg safety.
    Returns the new image path.
    """
    try:
        if not os.path.isfile(image_path):
            ic(f"File not found: {image_path}")
            return None

        with Image.open(image_path) as img:
            width, height = img.size
            ic(f"Original size: {width}x{height}")

            # Force RGB (remove alpha)
            img = img.convert("RGB")

            # Resize if not already 512x768
            if (width, height) != (512, 768):
                ic(f"Resizing {os.path.basename(image_path)} → 512x768")
                img = img.resize((512, 768))

            # Change extension to .jpg
            base, _ = os.path.splitext(image_path)
            new_path = base + ".jpg"

            # Save JPG with high quality
            img.save(new_path, "JPEG", quality=95)
            ic(f"Saved new JPG for FFmpeg: {new_path}")

            return new_path

    except Exception as e:
        ic(f"Error in fix_image_before_ffmpeg: {e}")
        return None


# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.route("/computer_images", methods=["GET"])
def computer_images():
    """Show all images from the computer_images directory (resized)."""
    if not os.path.isdir(COMPUTER_IMAGE_DIRECTORY):
        flash(f"Image directory not found: {COMPUTER_IMAGE_DIRECTORY}")
        return render_template("get_images.html", image_files=[])

    image_files = ensure_resized(COMPUTER_IMAGE_DIRECTORY)
    return render_template("computer_images.html", image_files=image_files)


@app.route("/get_images2", methods=["GET"])
def get_images2():
    """Show all images from the images directory (resized)."""
    if not os.path.isdir(IMAGE_DIRECTORY):
        flash(f"Image directory not found: {IMAGE_DIRECTORY}")
        return render_template("get_images.html", image_files=[])

    image_files = ensure_resized(IMAGE_DIRECTORY)
    return render_template("get_images.html", image_files=image_files)


ALLOWED_AUDIO_EXTS = {"mp3"}
allowed_exts = {"mp3"}
ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "mp4"}


def allowed_file(filename, allowed_exts):
    ic(f"{filename} : {allowed_exts}")
    logit(f"{filename} : {allowed_exts}")
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_exts


@app.route("/upload_media", methods=["GET", "POST"])
def upload_media():
    voice_dir = "static/voice"
    music_dir = "static/mp3s"
    os.makedirs(voice_dir, exist_ok=True)
    os.makedirs(music_dir, exist_ok=True)
    os.makedirs("static/projects", exist_ok=True)

    voice_files = sorted([f for f in os.listdir(voice_dir) if f.lower().endswith((".mp3", ".wav"))])
    music_files = sorted([f for f in os.listdir(music_dir) if f.lower().endswith((".mp3", ".wav"))])
    mp3_files = voice_files + [f"music/{f}" for f in music_files]

    if request.method == "POST":
        image_file = request.files.get("image")
        uploaded_audio = request.files.get("audio_file")
        selected_audio = request.form.get("audio_filename")

        # ---------------------------
        # AUDIO HANDLING
        # ---------------------------
        audio_saved = False
        if uploaded_audio and uploaded_audio.filename != "":
            dest_mp3 = "static/projects/use.mp3"
            uploaded_audio.save(dest_mp3)
            try:
                shutil.copy(dest_mp3, os.path.join(app.config.get("UPLOAD_MEDIA", "static/sources"), "use.mp3"))
                shutil.copy(dest_mp3, "static/Wav2Lip-master/sample_data/use.mp3")
            except Exception:
                pass
            audio_saved = True
            ic(f"Saved uploaded audio directly to: {dest_mp3}")
        elif selected_audio:
            source_path = None
            if selected_audio.startswith("music/"):
                source_path = os.path.join(music_dir, selected_audio.replace("music/", ""))
            elif os.path.exists(os.path.join(voice_dir, selected_audio)):
                source_path = os.path.join(voice_dir, selected_audio)
            elif os.path.exists(os.path.join(music_dir, selected_audio)):
                source_path = os.path.join(music_dir, selected_audio)
            elif os.path.exists(os.path.join("static/results", selected_audio)):
                source_path = os.path.join("static/results", selected_audio)

            if source_path and os.path.exists(source_path):
                dest_mp3 = "static/projects/use.mp3"
                shutil.copy(source_path, dest_mp3)
                try:
                    shutil.copy(dest_mp3, os.path.join(app.config.get("UPLOAD_MEDIA", "static/sources"), "use.mp3"))
                    shutil.copy(dest_mp3, "static/Wav2Lip-master/sample_data/use.mp3")
                except Exception:
                    pass
                audio_saved = True
                ic(f"Copied selected audio {source_path} to: {dest_mp3}")

        if not audio_saved and not os.path.exists("static/projects/use.mp3"):
            flash("Please upload or select an audio/voice file for the avatar.")
            return redirect(url_for("upload_media"))

        # ---------------------------
        # IMAGE PROCESSING SECTION
        # ---------------------------
        if (
            image_file
            and image_file.filename != ""
            and allowed_file(image_file.filename, ALLOWED_IMAGE_EXTS)
        ):
            try:
                from PIL import Image

                img = Image.open(image_file.stream)
                img = img.convert("RGB")
                img = img.resize((512, 768), resample=Image.LANCZOS)

                # Guarantee even dimensions for FFmpeg
                w, h = img.size
                even_w = w if w % 2 == 0 else w + 1
                even_h = h if h % 2 == 0 else h + 1
                if (even_w, even_h) != (w, h):
                    ic(f"Adjusting to even dimensions: {w}x{h} → {even_w}x{even_h}")
                    new_img = Image.new("RGB", (even_w, even_h), (0, 0, 0))
                    new_img.paste(img, (0, 0))
                    img = new_img

                # Save directly to static/projects/use.jpg for makeavatar
                dest_project_img = "static/projects/use.jpg"
                img.save(dest_project_img, "JPEG", quality=95)
                ic(f"Saved avatar face to: {dest_project_img}")

                # Also save backups to static/sources and sample_data
                try:
                    dest_image_path = os.path.join(app.config.get("UPLOAD_MEDIA", "static/sources"), "use.jpg")
                    img.save(dest_image_path, "JPEG", quality=95)
                    img.save("static/Wav2Lip-master/sample_data/use.jpg", "JPEG", quality=95)
                except Exception:
                    pass

                flash(
                    "Media files processed and copied to static/projects! Click 'EXECUTE Make Avatar' below."
                )
            except Exception as e:
                ic(f"Error saving image: {e}")
                flash(f"Error saving image file: {e}")
                return redirect(url_for("upload_media"))
        elif not os.path.exists("static/projects/use.jpg"):
            flash("Please upload a JPG image for the avatar face.")
            return redirect(url_for("upload_media"))
        else:
            flash("Audio updated in static/projects/use.mp3! Ready to make avatar.")

        return redirect(url_for("upload_media"))

    return render_template(
        "upload_media.html",
        voice_files=voice_files,
        music_files=music_files,
        mp3_files=mp3_files
    )


@app.route("/make_avatar", methods=["GET"])
def make_avatar():
    mp4_file = "static/temp_exp/avatarX.mp4"
    try:
        script_path = "static/Wav2Lip-master/makeavatar"
        if os.path.exists(script_path):
            result = subprocess.run(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            flash("Avatar synthesized successfully with Wav2Lip!")
        else:
            flash("Error: Wav2Lip makeavatar script not found.")
    except subprocess.CalledProcessError as e:
        ic(e.stderr)
        flash(f"Wav2Lip generation error: {e.stderr or e}")

    avatar_files = []
    try:
        avatars_dir = "static/avatars"
        if os.path.exists(avatars_dir):
            avatar_files = [
                f
                for f in os.listdir(avatars_dir)
                if f.lower().endswith(".mp4") and not f.startswith(".")
            ]
            avatar_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(avatars_dir, f)),
                reverse=True,
            )
            avatar_files = avatar_files[:12]
    except Exception as ex:
        ic(f"Error listing avatars: {ex}")

    return render_template("avatar.html", mp4_file=mp4_file, avatar_files=avatar_files)


@app.route("/avatar")
def avatar():
    mp4_file = "static/temp_exp/avatarX.mp4"
    if not os.path.exists(mp4_file):
        try:
            script_path = "static/Wav2Lip-master/makeavatar"
            if os.path.exists(script_path):
                subprocess.run(
                    [sys.executable, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            ic(e.stderr)

    avatar_files = []
    try:
        avatars_dir = "static/avatars"
        if os.path.exists(avatars_dir):
            avatar_files = [
                f
                for f in os.listdir(avatars_dir)
                if f.lower().endswith(".mp4") and not f.startswith(".")
            ]
            avatar_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(avatars_dir, f)),
                reverse=True,
            )
            avatar_files = avatar_files[:12]
    except Exception as ex:
        ic(f"Error listing avatars: {ex}")

    return render_template("avatar.html", mp4_file=mp4_file, avatar_files=avatar_files)


@app.route("/convert", methods=["GET", "POST"])
def convert():
    if request.method == "POST":
        if "audio" not in request.files:
            flash("No file part")
            return redirect(request.url)
        uploaded_file = request.files["audio"]
        if uploaded_file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            input_path = os.path.join(CONVERT_UPLOAD_FOLDER, filename)
            uploaded_file.save(input_path)
            ic(f"Uploaded audio for conversion saved to: {input_path}")

            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_{uuid.uuid4().hex[:6]}.mp3"  # Unique name
            output_path = os.path.join(CONVERT_OUTPUT_FOLDER, output_filename)

            command = [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-vn",
                "-ar",
                "44100",
                "-ac",
                "2",
                "-b:a",
                "192k",
                output_path,
            ]
            ic(f"Running ffmpeg command: {' '.join(command)}")
            try:
                subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    timeout=60,
                )
                ic(f"Conversion successful: {output_path}")
                session["download_mp3_relative"] = os.path.join(
                    os.path.basename(CONVERT_OUTPUT_FOLDER), output_filename
                )
                copy_path = os.path.join("static/results", output_filename)
                ic(f"copy_path {copy_path}")
                shutil.copy(output_path, copy_path)
                return redirect(url_for("download_page"))
            except subprocess.CalledProcessError as e:
                ic("FFmpeg error output:", e.stderr.decode())
                flash(f"Conversion failed: {e.stderr.decode()}")
            except subprocess.TimeoutExpired:
                ic("FFmpeg conversion timed out.")
                flash("Conversion process timed out.")
            except FileNotFoundError:
                ic("FFmpeg not found.")
                flash(
                    "Error: FFmpeg command not found. Please ensure it's installed and in PATH."
                )
            return redirect(request.url)

    return render_template_string(
        """
    <!doctype html>
    <head>
      <title>Upload and Convert Audio</title>
      <link rel="stylesheet" href="{{ url_for('static', filename='css/themed.css') }}">
    </head>
    <body>
    <div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul class="flashes">
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <h1>🎙️ Upload Audio (AAC, M4A, WAV, MP4) to Convert to MP3</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=audio accept=".aac,.m4a,.wav,.mp4,.ogg,.flac">
      <br><br>
      <button type=submit class="btn">Upload and Convert</button>
    </form>
    </div>
    </body>
    """
    )


@app.route("/download_mp3")
def download_page():
    """
    Download MP3 Page
    Purpose:
              Displays an HTML page containing the downloaded MP3 file and buttons to download it or convert another file.
    Arguments:
              None
    Return Value:
              Rendered HTML template as a string.
    """
    file_path_in_static_relative = session.get("download_mp3_relative")
    if not file_path_in_static_relative:
        flash("No file available for download or session expired.")
        return redirect(url_for("convert"))

    full_system_path = os.path.join(
        app.config["UPLOAD_FOLDER"], file_path_in_static_relative
    )
    if not os.path.exists(full_system_path):
        flash(f"File {os.path.basename(file_path_in_static_relative)} not found.")
        return redirect(url_for("convert"))

    return render_template_string(
        f"""
    <!doctype html>
    <head>
      <title>MP3 Ready</title>
      <link rel="stylesheet" href="{{{{ url_for('static', filename='css/themed.css') }}}}">
    </head>
    <body>
    <div class="container">
      <h2>🎧 Your MP3 file is ready: {os.path.basename(file_path_in_static_relative)}</h2>
      <br>
      <audio controls>
        <source src="{{{{ url_for('static', filename='{file_path_in_static_relative}') }}}}" type="audio/mpeg">
        Your browser does not support the audio element.
      </audio>
      <br><br>
      <a class="btn" href="{{{{ url_for('static', filename='{file_path_in_static_relative}') }}}}" download>⬇️ Download MP3</a>
      &nbsp;&nbsp;
      <a class="btn btn-secondary" href="{{{{ url_for('convert') }}}}">🔁 Convert Another</a>
    </div>
    </body>
    """
    )


@app.route("/upload_image_simple", methods=["POST"])
def upload_file_simple():
    """
    Uploads an image to the user's uploads folder.

    Parameters:
        request (flask.Request): The incoming HTTP request.
    Returns:
        str or tuple: A success message if upload is successful, otherwise a tuple containing error message and HTTP status code.
    """
    if "imageFile" not in request.files:
        return "No imageFile field in request", 400
    uploaded_file = request.files["imageFile"]
    if uploaded_file.filename == "":
        return "No file selected", 400

    if uploaded_file and allowed_file(uploaded_file.filename, ALLOWED_IMAGE_EXTS):
        filename = secure_filename(uploaded_file.filename)
        os.makedirs(app.config["USER_UPLOADS_FOLDER"], exist_ok=True)
        save_path = os.path.join(app.config["USER_UPLOADS_FOLDER"], filename)
        try:
            uploaded_file.save(save_path)
            return f"File {filename} uploaded successfully to {app.config['USER_UPLOADS_FOLDER']}"
        except Exception as e:
            ic(f"Error saving simple upload: {e}")
            return f"Error saving file: {e}", 500
    else:
        return "Invalid file type", 400


# --------------------
def add_frame_overlay(image_path, frame_path):
    background = Image.open(image_path).convert("RGBA")
    overlay = Image.open(frame_path).convert("RGBA")
    overlay = overlay.resize(background.size, Image.LANCZOS)
    combined = Image.alpha_composite(background, overlay)
    return combined


# --------------------
def create_temp_images_with_frame(image_paths, frame_path):
    temp_dir = "temp_frames"
    os.makedirs(temp_dir, exist_ok=True)
    temp_files = []
    for i, img_path in enumerate(image_paths):
        combined_img = add_frame_overlay(img_path, frame_path)
        temp_path = os.path.join(temp_dir, f"temp_frame_{i}.png")
        combined_img.save(temp_path)
        temp_files.append(temp_path)
        ic(f"Created: {temp_path}")
    return temp_files, temp_dir


# --------------------
def create_video_with_audio(image_paths, audio_path, output_path, buffer_sec=1.0):
    ic("Starting video creation...")

    frame_path = "static/assets/frame.png"
    temp_images, temp_dir = [], ""
    audio, padded_audio, video, final_video = None, None, None, None
    try:
        audio = AudioFileClip(audio_path)
        original_duration = audio.duration
        ic(f"Original audio duration: {original_duration:.2f}s")

        silence = AudioClip(lambda t: [0, 0], duration=0.25, fps=audio.fps)
        padded_audio = concatenate_audioclips([silence, audio, silence])
        padded_audio_duration = padded_audio.duration
        ic(f"Padded audio duration: {padded_audio_duration:.2f}s")

        temp_images, temp_dir = create_temp_images_with_frame(image_paths, frame_path)
        num_images = len(temp_images)

        total_video_duration = padded_audio_duration + buffer_sec
        ic(f"Total video duration with buffer: {total_video_duration:.2f}s")

        image_duration = total_video_duration / num_images
        ic(f"Each image duration: {image_duration:.4f}s")

        clips = [ImageClip(img).set_duration(image_duration) for img in temp_images]

        video = concatenate_videoclips(clips, method="compose")
        ic(f"Concatenated video duration: {video.duration:.4f}s")

        final_video = video.set_audio(padded_audio).set_fps(24)
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

        ic(f"Saved final video as: {output_path}")

    finally:
        if audio:
            audio.close()
        if padded_audio:
            padded_audio.close()
        if video:
            video.close()
        if final_video:
            final_video.close()
        if temp_dir and os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
            ic(f"Deleted temp directory: {temp_dir}")


def static_dir():
    image_dir = "static/images/newai"
    if not os.path.isdir(image_dir):
        return []
    image_files = glob.glob(os.path.join(image_dir, "*.jpg"))
    return image_files


# --------------------
@app.route("/generate_video", methods=["GET", "POST"])
def generate_video():
    """
    Generates a video from a specified directory of images and an audio file.
    Args:
        image_dir (str): Path to the directory containing the images.
        audio_path (str): Path to the audio file.
    Returns:
        str: HTML response with the generated video URL or error message if invalid input.
    """
    if request.method == "POST":
        image_dir = request.form.get("image_dir")
        audio_path = request.form.get("audio_path")

        if not image_dir or not os.path.exists(image_dir):
            return "<h2>Image folder not found or not specified.</h2>"

        if not audio_path or not os.path.isfile(audio_path):
            return "<h2>Audio file not found or not specified.</h2>"

        image_files = [
            f
            for f in os.listdir(image_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if len(image_files) < 10:
            return f"<h2>Need at least 10 images in '{image_dir}'. Found {len(image_files)}.</h2>"

        selected = random.sample(image_files, 10)
        selected_paths = [os.path.join(image_dir, img) for img in selected]
        ic("Selected images:", selected_paths)

        output_filename = f"{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join("static/results", output_filename)

        create_video_with_audio(selected_paths, audio_path, output_path)

        return render_template(
            "generate_video.html",
            video_url=url_for("serve_result", filename=output_filename),
        )

    return render_template(
        "generate_video.html", video_url=None, image_files=static_dir()
    )


# --------------------
@app.route("/10vid", methods=["GET"])
def video_form():
    files = os.listdir(PROJECT_DIR)
    mp3s = [f for f in files if f.lower().endswith(".mp3")]
    jpgs = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    mp3s.sort()
    jpgs.sort()
    return render_template("10vid.html", mp3s=mp3s, jpgs=jpgs)


# --------------------


@app.route("/make10vid", methods=["POST"])
def create_10video():
    """
    Create 10-Video Merging Function.
    Purpose:
    Merges an mp3 audio file with a list of images, creating a new video.
    Args:
        None
    Returns:
        A rendered HTML template displaying the processed video and its URL.
    """
    mp3_file = request.form.get("mp3")
    img_list = request.form.getlist("img")

    if not mp3_file or not img_list:
        return render_template_string("<p class='error'>Missing MP3 or images.</p>")

    if len(img_list) != 10:
        return render_template_string(
            "<p class='error'>You must select exactly 10 images.</p>"
        )

    mp3_path = os.path.join(PROJECT_DIR, mp3_file)
    if not os.path.isfile(mp3_path):
        return render_template_string(
            f"<p class='error'>MP3 file not found: {mp3_file}</p>"
        )

    for img in img_list:
        if not os.path.isfile(os.path.join(PROJECT_DIR, img)):
            return render_template_string(
                f"<p class='error'>Image not found: {img}</p>"
            )

    # Process audio
    audio = AudioFileClip(mp3_path)
    silence = AudioClip(lambda t: [0, 0], duration=0.5, fps=44100)
    full_audio = concatenate_audioclips([silence, audio, silence])
    total_duration = full_audio.duration
    ic(total_duration)

    # Build image sequence
    img_duration = total_duration / 10
    clips = []
    for img in img_list:
        img_path = os.path.join(PROJECT_DIR, img)
        clip = ImageClip(img_path).set_duration(img_duration)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose").set_audio(full_audio)
    filename = f"{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(PROJECT_DIR, filename)
    ic(output_path)

    video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
    file_path = add_titleimage(output_path, hex_color="#A52A2A")
    ic(file_path)

    # Clean up clips
    audio.close()
    full_audio.close()
    for clip in clips:
        clip.close()
    video.close()

    return render_template_string(
        f"""
    <body style='background:black; color:white; font-family:sans-serif'>
    <h2>✅ Video Created</h2>
    <p>Original Merged Video: <a href="{url_for("serve_processed", filename=filename)}" target="_blank">{filename}</a></p>
    <p>Final Titled Video: <a href="{url_for("serve_processed", filename=os.path.basename(file_path))}" target="_blank">{os.path.basename(file_path)}</a></p>
    </body>
    """
    )


# --------------------
def crop_center_top(image, crop_width=500, crop_height=500):
    img_width, img_height = image.size
    left = (img_width - crop_width) // 2
    top = 0
    right = left + crop_width
    bottom = crop_height
    return image.crop((left, top, right, bottom))


"""
@app.route('/size_paste', methods=['GET', 'POST'])
def size_paste():
    processed_files = []

    if request.method == 'POST':
        uploaded_files = request.files.getlist('image')
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                input_path = os.path.join(PROJECT_DIR, filename)
                file.save(input_path)

                try:
                    with Image.open(input_path).convert('RGBA') as image:
                        image = image.resize((512, 512), Image.LANCZOS)
                        imagen = crop_center_top(image, crop_width=470, crop_height=470)
                        
                        canvas = Image.new('RGBA', (512, 768), (0, 0, 0, 255))
                        x_offset = (512 - 470) // 2
                        y_offset = 20
                        canvas.paste(imagen, (x_offset, y_offset), imagen)

                        output_filename = f"pasted_{filename}"
                        output_path = os.path.join(PROJECT_DIR, output_filename)

                        if output_filename.lower().endswith(('.jpg', '.jpeg')):
                            canvas.convert('RGB').save(output_path)
                        else:
                            canvas.save(output_path)

                        processed_files.append(output_filename)
                        ic(f"Processed: {output_filename}")
                except Exception as e:
                    ic(f"Error processing image {filename}: {e}")

    return render_template('size_paste.html', processed_files=processed_files)
"""


@app.route("/size_paste", methods=["GET", "POST"])
def size_paste():
    """
    Processes uploaded images and resizes them to a fixed width of 480 pixels.
    Args:
        None
    Returns:
        A rendered HTML template with the list of processed files.
    """
    processed_files = []

    if request.method == "POST":
        uploaded_files = request.files.getlist("image")

        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                input_path = os.path.join(PROJECT_DIR, filename)
                file.save(input_path)
                ic(f"Saved upload: {input_path}")

                try:
                    # --------------------------------------------------
                    # LOAD IMAGE
                    # --------------------------------------------------
                    image = Image.open(input_path).convert("RGBA")
                    original_w, original_h = image.size
                    ic(f"Original size: {original_w}x{original_h}")

                    # --------------------------------------------------
                    # ALWAYS RESIZE TO EXACTLY WIDTH = 480
                    # --------------------------------------------------
                    target_w = 480
                    scale = target_w / float(original_w)
                    new_w = target_w
                    new_h = int(original_h * scale)

                    image = image.resize((new_w, new_h), Image.LANCZOS)
                    ic(f"Resized to: {new_w}x{new_h}")

                    # --------------------------------------------------
                    # CREATE CANVAS 512×768
                    # --------------------------------------------------
                    canvas_w = 512
                    canvas_h = 768
                    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 255))

                    # center horizontally, start near the top
                    x_offset = (canvas_w - new_w) // 2
                    y_offset = 20

                    canvas.paste(image, (x_offset, y_offset), image)
                    ic(f"Pasted image at: x={x_offset}, y={y_offset}")

                    # --------------------------------------------------
                    # SAVE OUTPUT
                    # --------------------------------------------------
                    output_filename = f"pasted_{filename}"
                    output_path = os.path.join(PROJECT_DIR, output_filename)

                    if output_filename.lower().endswith((".jpg", ".jpeg")):
                        canvas.convert("RGB").save(output_path)
                    else:
                        canvas.save(output_path)

                    processed_files.append(output_filename)
                    ic(f"Processed: {output_filename}")

                except Exception as e:
                    ic(f"Error processing image {filename}: {e}")

    return render_template("size_paste.html", processed_files=processed_files)


@app.route("/processed/<filename>")
def serve_processed(filename):
    return send_from_directory(PROJECT_DIR, filename)


# -------------------------------
# HELPER FUNCTION
# -------------------------------
def allowed_files(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------------
# ROUTE: UPLOAD COMPUTER IMAGE
# -------------------------------
@app.route("/upload_computer_image", methods=["GET", "POST"])
def upload_computer_image():
    """Upload Computer Image Route
    Purpose: Handles file uploads for computer images.
    Args:
        request (object): HTTP request object
        app (object): Flask application instance
    Returns:
        str or int: Successful response message, 400 if invalid request, otherwise rendered template HTML.
    """
    ic("Entered /upload_computer_image route")

    if request.method == "POST":
        ic("POST request received")

        if "file" not in request.files:
            ic("No file part in request")
            return "No file part in request.", 400

        file = request.files["file"]

        if file.filename == "":
            ic("No file selected for upload")
            return "No file selected.", 400

        if file and allowed_files(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["COMPUTER_IMAGE_DIRECTORY"], filename)
            directory = app.config["COMPUTER_IMAGE_DIRECTORY"]
            ensure_resized(directory)
            file.save(save_path)
            ic(f"Saved uploaded file: {save_path}")

            if not os.path.isdir(COMPUTER_IMAGE_DIRECTORY):
                flash(f"Image directory not found: {COMPUTER_IMAGE_DIRECTORY}")
                return render_template("get_images.html", image_files=[])
            image_files = [
                f
                for f in os.listdir(COMPUTER_IMAGE_DIRECTORY)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            return render_template("computer_images.html", image_files=image_files)
        else:
            ic("Invalid file type")
            return "Invalid file type. Allowed: png, jpg, jpeg, gif", 400

    # Simple HTML upload form
    return render_template_string(
        """
    <!doctype html>
    <html>
    <head><title>Upload Image</title></head>
    <body style="font-family:sans-serif;">
        <h2>Upload a Computer Image</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required>
            <input type="submit" value="Upload">
        </form>
    </body>
    </html>
    """
    )


# --------
@app.route("/join", methods=["GET", "POST"])
def join_image_audio():
    """
    Join Image and Audio Function
    Purpose:
      This function handles the creation of a joined MP4 video from
      selected image and audio files.
    Arguments:
      None (function parameters are handled within the code)
    Return Value:
      Rendered template with result or redirect to previous page if error occurs
    Display selectable images and audios, and create joined MP4 on submit."""
    if request.method == "POST":
        image_filename = request.form.get("image")
        audio_filename = request.form.get("audio")

        if not image_filename or not audio_filename:
            flash("Please select both an image and an audio file.")
            return redirect(url_for("join_image_audio"))

        ic(f"Selected image: {image_filename}")
        ic(f"Selected audio: {audio_filename}")

        image_path = os.path.join(VIDEO_DIRECTORY, image_filename)
        audio_path = os.path.join(UPLOAD_AUDIO, audio_filename)

        uuid_name = f"{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(VIDEO_DIRECTORY, uuid_name)
        ic(f"Output file will be: {output_path}")

        try:
            # Load and extend audio with 0.25s silence at start and end
            main_audio = AudioFileClip(audio_path)
            silence = AudioClip(lambda t: 0, duration=0.25).set_fps(main_audio.fps)
            full_audio = concatenate_audioclips([silence, main_audio, silence])
            ic(f"Audio duration (with silence): {full_audio.duration}")

            # Create image clip with audio
            image = ImageClip(image_path, duration=full_audio.duration)
            video = image.set_audio(full_audio).set_duration(full_audio.duration)
            video = video.resize(height=720).set_position("center")

            # Write video to file
            video.write_videofile(
                output_path, fps=24, codec="libx264", audio_codec="aac"
            )

            ic("Video created successfully.")
            return render_template("join_result.html", video_filename=uuid_name)

        except Exception as e:
            ic(f"Error joining image and audio: {e}")
            flash(f"An error occurred while creating the video: {e}")
            return redirect(url_for("join_image_audio"))

    # GET method: list available media
    images = get_sorted_files_by_date(VIDEO_DIRECTORY, image_exts)
    audios = get_sorted_files_by_date(UPLOAD_AUDIO, audio_exts)
    ic(f"Available images: {len(images)} | Available audios: {len(audios)}")

    return render_template("join.html", images=images, audios=audios)


HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Overlay Studio</title>
<style>
body { background:#1e1e1e; color:white; font-family:Arial; text-align:center; }
img.thumb { width:160px; margin:8px; border:3px solid #444; border-radius:6px; cursor:pointer; transition:0.3s; }
img.thumb:hover { border-color:#00ffff; transform:scale(1.05); }
#canvas-container { position:relative; display:inline-block; margin-top:20px; }
.overlay { position:absolute; cursor:move; z-index:10; }
button { background:#00ffff; color:black; border:none; padding:10px 20px; border-radius:5px; margin:5px; cursor:pointer; font-weight:bold; }
button:hover { background:white; }
</style>
</head>
<body>
<h1>Overlay Studio</h1>

<form action="/upload" method="post" enctype="multipart/form-data">
    <input type="file" name="image" accept="image/*" required>
    <button type="submit">Upload Base Image</button>
</form>

<form action="/upload_" method="post" enctype="multipart/form-data">
    <input type="file" name="" accept="image/*" required>
    <button type="submit">Upload Overlay</button>
</form>

<h2>Base Images</h2>
<div id="images">
{% for f in base_images %}
  <img src="/static/uploads/{{f}}" class="thumb" onclick="selectBase('{{f}}')">
{% endfor %}
</div>

<div id="canvas-container"></div>

<script>
let baseName = null;
let sData = [];

function selectBase(name){
  baseName = name;
  document.getElementById('canvas-container').innerHTML =
  `<img id='base' src='/static/uploads/${name}'><div id='Zone'></div><br>
  <button onclick='saveResult()'>Save Result</button><br><h3>Choose Overlay</h3><div id='ovlist'></div>`;
  fetch('/list_s').then(r=>r.json()).then(list=>{
    let odiv=document.getElementById('ovlist');
    odiv.innerHTML='';
    list.forEach(f=>{
      let i=document.createElement('img');
      i.src='/static/s/'+f;
      i.className='thumb';
      i.onclick=()=>addOverlay(f);
      odiv.appendChild(i);
    });
  });
}

function addOverlay(fname){
  let ov=document.createElement('img');
  ov.src='/static/s/'+fname;
  ov.className='overlay';
  ov.style.left='10px';
  ov.style.top='10px';
  ov.onload=()=>{ov.style.width=ov.naturalWidth+'px'; ov.style.height=ov.naturalHeight+'px';};
  ov.onmousedown=startDrag;
  document.getElementById('canvas-container').appendChild(ov);
  overlaysData.push({file:fname,x:10,y:10});
}

let drag=null, startX=0, startY=0, origX=0, origY=0;
function startDrag(e){
  drag=e.target;
  startX=e.clientX;
  startY=e.clientY;
  origX=parseInt(drag.style.left);
  origY=parseInt(drag.style.top);
  document.onmousemove=dragging;
  document.onmouseup=stopDrag;
}
function dragging(e){
  if(!drag) return;
  drag.style.left=(origX+e.clientX-startX)+'px';
  drag.style.top=(origY+e.clientY-startY)+'px';
}
function stopDrag(e){
  if(drag){
    overlaysData.forEach(o=>{
      if(o.file==drag.src.split('/').pop()){
        o.x=parseInt(drag.style.left);
        o.y=parseInt(drag.style.top);
      }
    });
  }
  drag=null;
  document.onmousemove=null;
  document.onmouseup=null;
}

function saveResult(){
  fetch('/save_overlay',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({base:baseName,overlays:overlaysData})
  }).then(r=>r.json()).then(d=>{
    alert('Saved '+d.result);
  });
}
</script>
</body>
</html>
"""


@app.route("/addlogo")
def addlogo():
    base_images = [
        f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith((".jpg", ".png"))
    ]
    ic(f"Loaded base images: {base_images}")
    return render_template_string(HTML, base_images=base_images)


@app.route("/upload", methods=["POST"])
def upload_base():
    """
    Uploads a base image.
    Purpose:
       Uploads and saves an image file to the server's storage directory.
    Arguments:
       None
    Returns:
       Redirect to '/addlogo' after successful upload.
    Raises:
       None
    """

    file = request.files["image"]
    ext = os.path.splitext(file.filename)[1].lower() or ".png"
    fname = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    Image.open(file).convert("RGBA").save(path)
    ic(f"Uploaded base {fname}")
    return redirect("/addlogo")


@app.route("/upload_overlay", methods=["POST"])
def upload_overlay():
    """
    Uploads an image as an overlay.
    Args:
        file: The uploaded file containing the overlay image.
    Returns:
        A redirect to the next page after successfully uploading the overlay image.
    """
    file = request.files["overlay"]
    ext = os.path.splitext(file.filename)[1].lower() or ".png"
    fname = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(OVERLAY_DIR, fname)
    Image.open(file).convert("RGBA").save(path)
    ic(f"Uploaded overlay {fname}")
    return redirect("/addlogo")


@app.route("/list_overlays")
def list_overlays():
    """
    Retrieves a list of available overlay images.
    Args:
        None
    Returns:
        A JSON response containing the list of overlays in the form of a string.
        The function returns a JSON encoded list of file names from the OVERLAY_DIR directory
        that have PNG or JPG extensions.
    Note: This function uses the os and jsonify libraries to interact with the file system and
    serialize the response. It is intended for use within a web application framework such as Flask.
    """
    overlays = [
        f for f in os.listdir(OVERLAY_DIR) if f.lower().endswith((".png", ".jpg"))
    ]
    ic(f"Overlays available: {overlays}")
    return jsonify(overlays)


@app.route("/save_overlay", methods=["POST"])
def save_overlay():
    """
    Saves an overlay image and updates the database.
    Parameters
    ----------
    base (str): Name of the base image.
    overlays (list): List of overlays with their respective file names, x and y coordinates.
    Returns
    -------
    A JSON response containing the status ("ok") and the result name.
    """
    data = request.get_json()
    base_name = data["base"]
    overlays = data["overlays"]
    base_path = os.path.join(UPLOAD_DIR, base_name)
    base = Image.open(base_path).convert("RGBA")

    for o in overlays:
        ov_path = os.path.join(OVERLAY_DIR, o["file"])
        ov_img = Image.open(ov_path).convert("RGBA")
        base.alpha_composite(ov_img, (o["x"], o["y"]))

    result_name = f"{uuid.uuid4().hex}.png"
    result_path = os.path.join(RESULT_DIR, result_name)
    base.save(result_path)
    ic(f"Saved result {result_name}")

    with open(DATA_FILE) as f:
        db = json.load(f)
    db.setdefault(base_name, []).append(
        {
            "overlays": overlays,
            "result": result_name,
            "saved_at": datetime.utcnow().isoformat(),
        }
    )
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)

    return jsonify({"status": "ok", "result": result_name})


# --------- adding the trim functions --------------


# --------------------------------------------------
# HTML PAGE (your same HTML with thumbnail support)
# --------------------------------------------------
INDEX_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>LAN Timeline Editor (FFmpeg)</title>
  <style>
    body{font-family: Arial;background:#121212;color:#eee;margin:0;padding:18px}
    .panel{background:#1b1b1b;padding:12px;border-radius:8px;margin-bottom:12px}
    .videos{display:flex;flex-wrap:wrap;gap:12px}
    .video-card{width:220px;background:#222;padding:8px;border-radius:6px}
    .timeline{background:#111;padding:8px;border-radius:6px;min-height:120px}
    .clip-row{display:flex;gap:8px;align-items:center;margin:6px 0;flex-wrap:wrap}
    label{display:block;margin-bottom:6px}
    input[type=file]{display:block;margin-bottom:8px}
    button{background:#2b7;border:none;padding:8px 10px;border-radius:6px;cursor:pointer}
    .danger{background:#c55}
    .muted{color:#aaa;font-size:0.9em}
    a{font-size:3vw;color:orange;}
  </style>
</head>

<body>
<h2>LAN Timeline Editor — FFmpeg</h2>
    <a href="text_to_mp3">text_to_mp3</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="/">HOME</a>
<div class="panel">
  <h3>Upload a video</h3>
  <form id="uploadForm">
    <input type="file" id="fileInput" name="file" accept="video/*" />
    <button type="submit">Upload</button>
  </form>
  <div id="uploadStatus" class="muted"></div>
</div>

<div class="panel">
  <h3>Available Videos & Clips</h3>
  <div id="videos" class="videos"></div>
</div>

<div class="panel">
  <h3>Timeline</h3>
  <div class="timeline" id="timeline"></div>
</div>

<script>
async function api(path, opts){ const r = await fetch(path, opts); return r.json(); }

async function refreshVideos(){
  const data = await api('/videos');
  const wrap = document.getElementById('videos');
  wrap.innerHTML = '';

  data.videos.forEach(v=>{
    const card = document.createElement('div');
    card.className='video-card';

    let src = '';
    let thumb = '';

    if(v.location === 'uploads'){
      src = `/static/uploads/${encodeURIComponent(v.filename)}`;
      thumb = `/static/thumbs/${encodeURIComponent(v.thumb)}`;
    } else if(v.location === 'clips'){
      src = `/static/clips/${encodeURIComponent(v.filename)}`;
      thumb = `/static/thumbs/${encodeURIComponent(v.thumb)}`;
    } else {
      src = `/static/audio/${encodeURIComponent(v.filename)}`;
    }

    let mediaHTML = '';
    if(v.location === 'audio'){
      mediaHTML = `<audio src="${src}" controls style="width:200px"></audio>`;
    } else {
      mediaHTML = `
        <video 
          width="200"
          controls
          muted
          playsinline
          preload="metadata"
          poster="${thumb}"
          src="${src}">
        </video>`;
    }

    card.innerHTML = `
      <div style="font-size:0.85em;word-break:break-all">${v.filename}</div>
      ${mediaHTML}
      <div class="muted">${v.location}</div>
    `;

    wrap.appendChild(card);
  });
}

window.onload = ()=>{
  refreshVideos();
  document.getElementById("uploadForm").addEventListener("submit", async ev=>{
    ev.preventDefault();
    const f = document.getElementById('fileInput').files[0];
    if(!f){ alert("Pick a file"); return; }

    let fd = new FormData();
    fd.append("file", f);

    let r = await fetch("/upload", { method:"POST", body: fd });
    let j = await r.json();
    document.getElementById("uploadStatus").textContent = JSON.stringify(j);

    refreshVideos();
  });
}
</script>
</body>
</html>
"""


# --------------------------------------------------
# VIDEO THUMBNAIL CREATION
# --------------------------------------------------
def create_thumbnail(video_path, output_thumb):
    """
    Creates a JPG thumbnail at 10% into the video.
    If video is 60s long → captures frame at 6 seconds.
    """
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            "thumbnail,scale=320:-1",
            "-frames:v",
            "1",
            output_thumb,
        ]
        ic("FFmpeg thumb cmd:", cmd)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        ic("Thumbnail error:", e)
        return False


# --------------------------------------------------
# ROUTES
# --------------------------------------------------


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


@app.route("/upload", methods=["POST"])
def upload():
    """
    Uploads a file to the server.
    Purpose:
            Uploads a single file to the server's upload directory.
    Arguments:
            None
    Return Value:
            Returns a JSON response with 'ok' set to True if the upload was successful,
                and 'filename' and 'thumb' keys containing the uploaded filename and
                thumbnail filename respectively. If no file is provided, returns an error response.
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"ok": False, "error": "No file"})

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOADS, filename)
    file.save(save_path)
    ic("Uploaded:", save_path)

    # Create thumbnail
    thumb_name = filename + ".jpg"
    thumb_path = os.path.join(THUMBS, thumb_name)
    create_thumbnail(save_path, thumb_path)

    return jsonify({"ok": True, "filename": filename, "thumb": thumb_name})


@app.route("/videos")
def list_videos():
    """
    List videos endpoint.
    Purpose:
      Returns a list of available video files in the system.
    Arguments:
      None
    Return Value:
      A JSON response containing a list of video objects with filename, thumb and location properties.
      The list contains all video files found in the 'uploads', 'clips' and 'audio' directories.
    """
    vids = []

    # UPLOADS
    for f in os.listdir(UPLOADS):
        if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
            vids.append({"filename": f, "thumb": f + ".jpg", "location": "uploads"})

    # CLIPS
    for f in os.listdir(CLIPS):
        if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
            vids.append({"filename": f, "thumb": f + ".jpg", "location": "clips"})

    # AUDIO
    for f in os.listdir(AUDIO):
        if f.lower().endswith((".mp3", ".wav")):
            vids.append({"filename": f, "thumb": "", "location": "audio"})

    return jsonify({"videos": vids})


# add text to tts (voice narration)
UPLOADS = "static/uploads"
VOICE_FOLDER = "static/voice"

os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(VOICE_FOLDER, exist_ok=True)

# ----------------------------
# Route: Text to MP3
# ----------------------------
@app.route("/text_to_mp3", methods=["GET", "POST"])
def text_to_mp3():
    """
    Converts user-provided text into a voice MP3 file using Kokoro TTS.
    Saves to static/voice/ and static/projects/use.mp3 for avatar lipsync.
    """
    mp3_file = None
    text = ""
    selected_voice = "af_heart"
    speed = 1.0

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        selected_voice = request.form.get("voice", "af_heart").strip()
        try:
            speed = float(request.form.get("speed", 1.0))
        except (ValueError, TypeError):
            speed = 1.0

        if not text:
            flash("Please enter some text to generate MP3.")
            return redirect(url_for("text_to_mp3"))

        text_clean_for_name = re.sub(r"\[.*?\]", "", text).strip()
        safe_name = "_".join(text_clean_for_name[:20].split())
        safe_name = re.sub(r"[^\w\-]", "", safe_name) or "speech"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        mp3_file = f"{safe_name}_{timestamp}.mp3"
        mp3_path = os.path.join(VOICE_FOLDER, mp3_file)

        result, error = generate_mp3_with_kokoro_tts(
            text, mp3_path, voice=selected_voice, speed=speed
        )
        if error:
            flash(error)
            mp3_file = None
        else:
            flash(f"Voice MP3 generated successfully with voice '{selected_voice}'!")
            ic(f"Voice MP3 generated successfully: {mp3_file}")
            # Also copy to static/projects/use.mp3 for avatar lipsync
            try:
                os.makedirs("static/projects", exist_ok=True)
                shutil.copy(mp3_path, "static/projects/use.mp3")
                ic("Copied speech to static/projects/use.mp3")
            except Exception as e:
                ic(f"Error copying voice to static/projects: {e}")

    # Recent voices for sidebar
    recent_voices = []
    try:
        if os.path.exists(VOICE_FOLDER):
            files = [
                f
                for f in os.listdir(VOICE_FOLDER)
                if f.lower().endswith(".mp3") and not f.startswith(".")
            ]
            files.sort(
                key=lambda f: os.path.getmtime(os.path.join(VOICE_FOLDER, f)),
                reverse=True,
            )
            recent_voices = files[:20]
    except Exception as e:
        ic(f"Error listing recent voices: {e}")

    return render_template(
        "text_to_mp3.html",
        mp3_file=mp3_file,
        text=text,
        voice_groups=KOKORO_VOICES,
        selected_voice=selected_voice,
        speed=speed,
        recent_voices=recent_voices,
    )


# ----------------------------
# Serve generated MP3
# ----------------------------
@app.route("/results/<filename>")
def serve_file(filename):
    """
    Serves a generated MP3 file from VOICE_FOLDER or RESULTS_FOLDER.
    """
    if os.path.exists(os.path.join(VOICE_FOLDER, filename)):
        return send_from_directory(VOICE_FOLDER, filename)
    return send_from_directory(RESULTS_FOLDER, filename)


# ---------------- upload mp4 ----------------------

RESULTS_FOLDER = "static/results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# RESULTS_FOLDER = 'static/results' # Already in app.config


# Simple HTML form (no templates needed)
UPLOAD_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Upload MP4</title>
</head>
<body>
    <h2>Upload MP4 to static/results</h2>
    <p> index2>Upload MP4 </p>
    <a href ="index2">RETURN</a>
    <form action="/upload_mp4" method="POST" enctype="multipart/form-data">
        <input type="file" name="video" accept="video/mp4" required>
        <button type="submit">Upload</button>
    </form>
</body>
</html>
"""


@app.route("/uploadmp4", methods=["GET"])
def uploadmp4():
    """
    simple upload form Flask sends raw HTML immediately
    not requiring render_template_string
    Has no Jinja variables
    Has no Jinja control blocks
    Is just a plain HTML string
    So when Flask/Jinja receives it, there’s nothing to process
    — it simply passes it through unchanged.
    """
    return UPLOAD_FORM


@app.route("/upload_mp4", methods=["POST","GET"])
def upload_mp4():
    """
    Uploads an MP4 video file.
    Args:
        request (object): The HTTP request object containing the uploaded file.
    Returns:
        str: A success message indicating the upload location of the uploaded file.
        int: An HTTP status code (400 for invalid requests).
        None: No return value is expected.
    Raises:
        ValueError: If the uploaded file is not an MP4 video file.
    """

    UPLOAD_DIR = "static/results"
    # Ensure file exists
    if "video" not in request.files:
        ic("No file part in request")
        return "No file uploaded", 400

    file = request.files["video"]

    if file.filename == "":
        ic("Empty filename")
        return "No selected file", 400

    # Only mp4 allowed
    if not file.filename.lower().endswith(".mp4"):
        ic("Rejected non-mp4 upload:", file.filename)
        return "Only MP4 files allowed", 400

    # Generate a safe unique filename
    unique_name = f"{uuid.uuid4()}.mp4"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    ic("Saving uploaded file to:", save_path)
    file.save(save_path)

    ic("Upload complete")
    return f"Uploaded successfully: {unique_name}"


# Optional: serve files from static/results
@app.route("/results/<path:filename>")
def results_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ------------- join mp3 and mp4

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_duration(input_file):
    """
    Returns the duration of a media file in seconds using ffprobe.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        input_file,
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    duration = float(result.stdout.strip())
    return duration


def run_cmd(cmd):
    """
    Run subprocess command and show it using ic.
    """
    ic(" ".join(cmd))
    subprocess.run(cmd, check=True)


def join_audio_video(mp3_file, mp4_file):
    """
    Your full script logic wrapped into a function so Flask can call it.
    """
    ic(f"Input audio: {mp3_file}")
    ic(f"Input video: {mp4_file}")

    audio_duration = get_duration(mp3_file)
    video_duration = get_duration(mp4_file)

    ic(f"Original audio duration: {audio_duration}")
    ic(f"Original video duration: {video_duration}")

    padded_audio = os.path.join(UPLOAD_DIR, "audio_padded.mp3")
    pad_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        mp3_file,
        "-af",
        "apad=pad_dur=0.5,adelay=500|500",
        padded_audio,
    ]
    run_cmd(pad_cmd)

    new_audio_duration = get_duration(padded_audio)
    ic(f"Padded audio duration: {new_audio_duration}")

    if video_duration == 0:
        raise ValueError("Video duration is zero!")

    speed_factor = video_duration / new_audio_duration
    ic(f"Speed factor (video stretched x {speed_factor})")

    adjusted_video = os.path.join(UPLOAD_DIR, "video_adjusted.mp4")
    speed_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        mp4_file,
        "-filter:v",
        f"setpts={speed_factor}*PTS",
        "-an",
        adjusted_video,
    ]
    run_cmd(speed_cmd)

    unique_id = str(uuid4())
    final_output = os.path.join(UPLOAD_DIR, f"final_joined_{unique_id}.mp4")

    merge_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        adjusted_video,
        "-i",
        padded_audio,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-shortest",
        final_output,
    ]
    run_cmd(merge_cmd)

    ic(f"Created final video: {final_output}")
    return final_output


@app.route("/joinmp3mp4", methods=["GET", "POST"])
def joinmp3mp4():
    if request.method == "POST":
        mp3 = request.files.get("mp3")
        mp4 = request.files.get("mp4")

        if not mp3 or not mp4:
            return "Please upload both MP3 and MP4."

        mp3_path = os.path.join(UPLOAD_DIR, mp3.filename)
        mp4_path = os.path.join(UPLOAD_DIR, mp4.filename)

        mp3.save(mp3_path)
        mp4.save(mp4_path)

        result_video = join_audio_video(mp3_path, mp4_path)
        filename = os.path.basename(result_video)

        return f"""
        <h2>File processed!</h2>
        <a href="/download/{filename}">Download Final Video</a>
        """

    return render_template_string(
        """
    <h2>Join Audio + Video</h2>
    <form method="POST" enctype="multipart/form-data">
        <p>MP3: <input type="file" name="mp3"></p>
        <p>MP4: <input type="file" name="mp4"></p>
        <button type="submit">Process</button>
    </form>
    """
    )


@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


# ---------------- get video frames ----------------
# delete images in 'static/keepers_resourses/
def keepers_resourses():
    for file in os.listdir("static/keepers_resourses"):
        file_path = os.path.join("static/keepers_resourses", file)
        if os.path.isfile(file_path):
            os.remove(file_path)


COPY_FRAMES = """<!DOCTYPE html>
<html>
<head>
    <title>Image Review and Keep</title>
    <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
        <h1>Select a Video to Process</h1>
                <p>Source: /media/jack/9930-14E11/ProductionWareHouse/DOCKER/static/videos/</p>
        <a href="/">HOME</a>&nbsp;&nbsp; | &nbsp;&nbsp;

        <a href="get_frames">Choose Another Video</a>
    <form action="/process_frames" method="post">
        <label for="video">Choose a video:</label>
        <select name="video" id="video">
            {% for video in video_files %}
                <option value="{{ video }}">{{ video }}</option>
            {% endfor %}
        </select>
        <br><br>
        <input type="submit" value="Process Video">
    </form>
    <h1>Review and Keep Images</h1>
    <form action="/add_frames" method="post">
        {% for frame in frames %}
            <div style="display: inline-block; text-align: center; margin: 10px;">
                <img src="{{ url_for('static', filename='frames/' + frame) }}" width="200">
                <br>
                <input type="checkbox" name="image" value="{{ frame }}"> Keep
            </div>
        {% endfor %}
        <br><br>
        <input type="submit" value="Keep Selected Images">
    </form>
</body>
</html>
"""


# Function to extract frames from MP4 using OpenCV
def extract_frames(video_path, output_folder):
    cap = cv2.VideoCapture(video_path)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(os.path.join(output_folder, f"frame_{count}.jpg"), frame)
        count += 1
    cap.release()


# Route to display video selection and form submission
@app.route("/get_frames_two", methods=["GET", "POST"])
def get_frames_two():
    delete_frames()
    video_dir = "static/results"
    keepers_resourses()
    # Use glob to find all .mp4 files in the directory
    video_files = glob.glob(os.path.join(video_dir, "*.mp4"))
    # sort the files by modification time
    #video_files = sorted(video_files, key=os.path.getmtime, reverse=True)
    video_files = sorted(video_files, key=os.path.getmtime)
    #video_files = sorted(video_files)
    # Get only the filenames (basename)
    video_files = [os.path.basename(video) for video in video_files]
    video_images = glob.glob("static/results/*.jpg")
    video_images = sorted(
        video_images, key=os.path.getmtime, reverse=True
    )  # post the images in reverse order
    return render_template_string(
        COPY_FRAMES, video_files=video_files, video_images=video_images
    )


# Route to handle form submission and extract frames from the selected video
@app.route("/process_frames", methods=["POST"])
def process_video():
    # Get selected video from form in COPY_FRAMES
    video_filename = request.form.get("video")
    # This is the location of the archive videos
    video_dir = "static/results"
    video_path = os.path.join(video_dir, video_filename)
    output_folder = "static/frames"

    # Clear frames folder before extracting new frames
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Extract frames from the selected video
    extract_frames(video_path, output_folder)

    # List all frames in the frames directory
    frames = os.listdir(output_folder)
    return render_template_string(COPY_FRAMES, frames=frames)


def limit_backups(source_dir="static/archived_images", max_files=45):
    backup_dir = "static/backups_resources"

    # Ensure backup directory exists
    os.makedirs(backup_dir, exist_ok=True)

    # Get all files in the source directory, sorted by modification time (oldest first)
    files = sorted(
        [
            f
            for f in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, f))
        ],
        key=lambda f: os.path.getmtime(os.path.join(source_dir, f)),
    )

    # If there are more than the max allowed, move the oldest files to the backup directory
    if len(files) > max_files:
        files_to_backup = files[:-max_files]  # Select all but the last 15 files

        for file in files_to_backup:
            file_path = os.path.join(source_dir, file)
            # Create a unique backup filename with a timestamp, preserving the extension
            file_extension = os.path.splitext(file)[1]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.splitext(file)[0]}_{timestamp}{file_extension}"
            backup_file_path = os.path.join(backup_dir, backup_filename)

            # Move the file to the backup directory
            shutil.move(file_path, backup_file_path)
            print(f"Moved {file} to {backup_file_path}")


# Route to handle form submission for image deletion
@app.route("/add_frames", methods=["POST", "GET"])
def add_frames_route():
    selected_images = request.form.getlist("image")
    for image in selected_images:
        id_ = str(uuid.uuid4())
        source = os.path.join("static/frames", image)
        destination1 = os.path.join("static/results", id_ + image)
        shutil.copy(source, destination1)
        destination2 = os.path.join("static/projects", id_ + image)
        shutil.copy(source, destination2)
        # destination3 = os.path.join('static/archived-images', id_ + image)
        # shutil.copy(source, destination3)
        # destination4 = os.path.join('static/archived-images', id_ + image)
        # shutil.copy(source, destination4)
    limit_backups(source_dir="static/archived-images", max_files=60)
    limit_backups(source_dir="static/archived-images")
    return redirect(url_for("get_frames"))


# Function to delete all files in 'static/frames/'
def delete_frames():
    frames_dir = "static/frames"
    for file in os.listdir(frames_dir):
        file_path = os.path.join(frames_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


# -------------- delete_app_images -----------------

"""
@app.route('/delete_app_images', methods=['GET', 'POST'])
def delete_app_images():
    image_dirs = {
        'static-sized_images': 'static/sized_images',
        'static-images': 'static/results',
        'static-selected': 'static/selected',
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

"""


@app.route("/delete_app_images", methods=["GET", "POST"])
def delete_app_images():
    from icecream import ic
    import os

    # Labels -> static-relative paths (IMPORTANT)
    image_dirs = {
        "Novel Images": "novel_images",
        "Sized Images": "sized_images",
        "Results Images": "results",
        "Selected Images": "selected",
        "Archived Images": "archived-images",
        "VideoResources": "videoresources",
        "Video Resources": "vid_resources",
    }

    selected_label = None
    selected_static_path = None
    images = []

    if request.method == "POST":
        # Directory selection
        if "directory" in request.form:
            selected_label = request.form["directory"]
            selected_static_path = image_dirs.get(selected_label)

            ic(selected_label, selected_static_path)

            if selected_static_path:
                disk_path = os.path.join("static", selected_static_path)
                images = [
                    f
                    for f in os.listdir(disk_path)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
                ]

        # Delete images
        if "delete_images" in request.form:
            selected_label = request.form["current_dir"]
            selected_static_path = image_dirs.get(selected_label)
            images_to_delete = request.form.getlist("selected_images")

            ic(images_to_delete)

            if selected_static_path:
                disk_path = os.path.join("static", selected_static_path)
                for image in images_to_delete:
                    img_file = os.path.join(disk_path, image)
                    try:
                        if selected_static_path == "novel_images":
                            move_novel_image_to_resource_images(img_file)
                            ic(f"Moved novel image to static/resource_images: {image}")
                        else:
                            os.remove(img_file)
                            ic(f"Deleted {image}")
                    except OSError as e:
                        ic(f"Error deleting/moving {image}", e)

                # Refresh list
                images = [
                    f
                    for f in os.listdir(disk_path)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
                ]

    return render_template(
        "delete_app_images.html",
        image_dirs=image_dirs.keys(),
        selected_dir=selected_label,
        selected_static_path=selected_static_path,
        images=images,
    )


# --------------  trim -----------------------------


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")  # raw input
CLIP_DIR = os.path.join(BASE_DIR, "static", "clips")  # temp segments
FINAL_DIR = os.path.join(BASE_DIR, "static", "results")  # final output

for d in [UPLOAD_DIR, CLIP_DIR, FINAL_DIR]:
    os.makedirs(d, exist_ok=True)

# --------------------------------------------------
# HTML UI
# --------------------------------------------------

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>FFmpeg Video Trimmer</title>
    <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='css/dark.css') }}">
</head>
<body>
<h2>LAN Video Trimmer & Stitcher</h2>
<a href="/index2">INDEX2</a>
<div class="panel">
<h3>Upload Video</h3>
<input type="file" id="file">
<button onclick="uploadt()">Upload</button>
<div id="uploadStatus"></div>
</div>

<div class="panel">
<h3>Videos</h3>
<select id="videoSelect" onchange="loadVideo()"></select>
<video id="player" controls></video>
</div>

<div class="panel">
<h3>Trim Segments</h3>
Start <input id="start" placeholder="00:00:05">
End <input id="end" placeholder="00:00:10">
<button onclick="addSegment()">Add Segment</button>
<div id="segments"></div>
<button onclick="render()">Render Final Video</button>
</div>

<div class="panel">
<h3>Final Output</h3>
<video id="finalVideo" controls></video>
</div>

<script>
let segments = []

async function uploadt(){
    let f = document.getElementById("file").files[0]
    let fd = new FormData()
    fd.append("file", f)
    let r = await fetch("/uploadt",{method:"POST",body:fd})
    let j = await r.json()
    document.getElementById("uploadStatus").innerText = JSON.stringify(j)
    loadVideos()
}

async function loadVideos(){
    let r = await fetch("/videos")
    let j = await r.json()

    let sel = document.getElementById("videoSelect")
    sel.innerHTML = ""

    j.videos.forEach(v => {
        // 🔧 DEFENSIVE FIX: handle string OR object
        let filename = (typeof v === "string") ? v : v.filename

        let o = document.createElement("option")
        o.value = filename
        o.text  = filename
        sel.appendChild(o)
    })

    loadVideo()
}

function loadVideo(){
    let v = document.getElementById("videoSelect").value
    if(!v) return
    document.getElementById("player").src = "/static/uploads/" + v
}

function addSegment(){
    let s = document.getElementById("start").value
    let e = document.getElementById("end").value
    segments.push({start:s,end:e})
    renderSegments()
}

function renderSegments(){
    let d = document.getElementById("segments")
    d.innerHTML = ""
    segments.forEach((s,i)=>{
        let div = document.createElement("div")
        div.className = "segment"
        div.innerText = i + ": " + s.start + " → " + s.end
        d.appendChild(div)
    })
}

async function render(){
    let v = document.getElementById("videoSelect").value
    let r = await fetch("/render",{
        method:"POST",
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({video:v,segments:segments})
    })
    let j = await r.json()
    document.getElementById("finalVideo").src = "/static/results/" + j.output
}

loadVideos()
</script>
</body>
</html>
"""

# --------------------------------------------------
# ROUTES
# --------------------------------------------------


@app.route("/trim")
def trim():
    return render_template_string(HTML)


@app.route("/uploadt", methods=["POST"])
def uploadt():
    f = request.files["file"]
    fname = f.filename
    path = os.path.join(UPLOAD_DIR, fname)
    f.save(path)
    ic("Uploaded", path)
    return jsonify(ok=True, file=fname)


@app.route("/videos")
def videos():
    vids = sorted(os.listdir(UPLOAD_DIR))
    ic("Videos", vids)
    return jsonify(videos=vids)


@app.route("/render", methods=["POST"])
def render_video():
    data = request.json
    video = data["video"]
    segments = data["segments"]

    src = os.path.join(UPLOAD_DIR, video)
    clip_files = []

    for i, seg in enumerate(segments):
        clip_name = f"clip_{i}_{uuid.uuid4().hex}.mp4"
        clip_path = os.path.join(CLIP_DIR, clip_name)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            src,
            "-ss",
            seg["start"],
            "-to",
            seg["end"],
            "-c",
            "copy",
            clip_path,
        ]
        ic("TRIM", cmd)
        subprocess.run(cmd, check=True)
        clip_files.append(clip_path)

    list_file = os.path.join(CLIP_DIR, "concat.txt")
    with open(list_file, "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\\n")

    out_name = f"final_{uuid.uuid4().hex}.mp4"
    out_path = os.path.join(FINAL_DIR, out_name)

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_file,
        "-c",
        "copy",
        out_path,
    ]
    ic("CONCAT", cmd)
    subprocess.run(cmd, check=True)

    return jsonify(output=out_name)


# -------------- special ai path ------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SHARED_PATH = os.path.join(BASE_DIR, "static", "images", "AI_images")

FRAME_PATH = os.path.join(BASE_DIR, "static", "assets", "talks.png")

TARGET_SIZE = (512, 768)
UNIQUE = str(randint(100000, 999999))

os.makedirs(SHARED_PATH, exist_ok=True)

ic("Using shared path:", SHARED_PATH)


# --------------------------------------------------
# IMAGE RESIZE (SAFE – IMAGES ONLY)
# --------------------------------------------------
def resize_ai_images():
    for f in os.listdir(SHARED_PATH):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            p = os.path.join(SHARED_PATH, f)
            try:
                with Image.open(p) as img:
                    if img.size != TARGET_SIZE:
                        ic(f"Resizing {f} from {img.size} to {TARGET_SIZE}...")
                        img.resize(TARGET_SIZE, Image.LANCZOS).save(p)
            except Exception as e:
                ic("Resize error:", f, e)


resize_ai_images()

# --------------------------------------------------
# HTML UI
# --------------------------------------------------
HTML7 = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Video Builder</title>
<style>
body { background:#111; color:#eee; font-family:Arial; text-align:center; }
.box { display:inline-block; margin:10px; padding:10px; border:1px solid #333; }
img { width:150px; }
button { padding:10px 20px; margin-top:20px; }
a {font-size:2.5wv; color:orange;}
</style>
</head>
<body>

<h1>Shared Path Video Builder</h1>
<a href="/text_to_ai_mp3">TEXTAREA TO MP3</a>
<p>{{ path }}</p>

<form method="post" action="/create_ai_video">

<h2>Images</h2>
{% for img in images %}
<div class="box">
<img src="{{ url_for('static', filename='images/AI_images/' + img) }}"><br>
<input type="checkbox" name="images" value="{{ img }}"> use<br>
seq <input type="number" name="seq_{{ img }}" min="1" max="7">
</div>
{% endfor %}

<h2>Audio</h2>
{% for mp3 in mp3s %}
<div class="box">
<input type="radio" name="audio" value="{{ mp3 }}"><br>
{{ mp3 }}<br>
<audio controls>
<source src="{{ url_for('static', filename='images/AI_images/' + mp3) }}">
</audio>
</div>
{% endfor %}

<br>
<button type="submit">Create Video</button>
</form>

<hr>
<a href="/text_to_ai_mp3">Text → MP3 (Kokoro)</a>

</body>
</html>
"""


# --------------------------------------------------
# HOME
# --------------------------------------------------
@app.route("/ai_path")
def ai_path():
    images = []
    mp3s = []

    for f in os.listdir(SHARED_PATH):
        if f.lower().endswith((".jpg", ".png")):
            images.append(f)
        elif f.lower().endswith(".mp3"):
            mp3s.append(f)

    ic("Images:", images)
    ic("MP3s:", mp3s)

    return render_template_string(HTML7, images=images, mp3s=mp3s, path=SHARED_PATH)


# --------------------------------------------------
# IMAGE OVERLAY
# --------------------------------------------------
def overlay_frame(src, frame, out):
    base = Image.open(src).convert("RGBA")
    frame = Image.open(frame).convert("RGBA").resize(base.size)
    Image.alpha_composite(base, frame).convert("RGB").save(out)


# --------------------------------------------------
# AUDIO PAD
# --------------------------------------------------
def pad_audio(src, out, ms=250):
    ic("Padding audio:", src)
    audio = AudioSegment.from_mp3(src)
    silence = AudioSegment.silent(duration=ms)
    (silence + audio + silence).export(out, format="mp3")


# --------------------------------------------------
# CREATE VIDEO
# --------------------------------------------------
@app.route("/create_ai_video", methods=["POST"])
def create_ai_video():
    selected_images = request.form.getlist("images")
    selected_audio = request.form.get("audio")

    ic("Selected images:", selected_images)
    ic("Selected audio:", selected_audio)

    if len(selected_images) != 7:
        return "Select exactly 7 images", 400

    ordered = []
    for img in selected_images:
        seq = request.form.get(f"seq_{img}")
        if not seq:
            return f"Missing sequence for {img}", 400
        ordered.append((int(seq), img))

    ordered_images = [x[1] for x in sorted(ordered)]
    ic("Ordered images:", ordered_images)

    processed = []

    for i, img in enumerate(ordered_images):
        src = os.path.join(SHARED_PATH, img)
        out = os.path.join(SHARED_PATH, f"_frame_{i}.jpg")

        if os.path.exists(FRAME_PATH):
            overlay_frame(src, FRAME_PATH, out)
        else:
            Image.open(src).convert("RGB").save(out)

        processed.append(out)

    audio_src = os.path.join(SHARED_PATH, secure_filename(selected_audio))
    padded_audio = os.path.join(SHARED_PATH, "_audio_pad.mp3")

    pad_audio(audio_src, padded_audio)

    audio_clip = AudioFileClip(padded_audio)
    duration = audio_clip.duration / len(processed)

    clips = [ImageClip(p).set_duration(duration) for p in processed]
    final = concatenate_videoclips(clips).set_audio(audio_clip)

    final_video = os.path.join(SHARED_PATH, f"{UNIQUE}_final.mp4")

    ic("Writing video:", final_video)

    final.write_videofile(final_video, fps=24, codec="libx264", audio_codec="aac")

    return redirect(url_for("serve_ai_video", filename=os.path.basename(final_video)))


# --------------------------------------------------
# SERVE VIDEO FROM SAME PATH
# --------------------------------------------------
@app.route("/video/<filename>")
def serve_ai_video(filename):
    return send_file(os.path.join(SHARED_PATH, filename), mimetype="video/mp4")


# --------------------------------------------------
# KOKORO TTS
# --------------------------------------------------
KOKORO_URL = "http://localhost:8880/v1/audio/speech"
VOICE = "af_bella"


def generate_kokoro_mp3(text, out):
    res, err = generate_mp3_with_kokoro_tts(text, out, voice=VOICE)
    if err:
        raise RuntimeError(err)


# --------------------------------------------------
# TEXT → MP3
# --------------------------------------------------
@app.route("/text_to_ai_mp3", methods=["GET", "POST"])
def text_to_ai_mp3():
    mp3 = None
    text = ""

    if request.method == "POST":
        text = request.form.get("text", "")
        safe = "_".join(text[:20].split())
        mp3 = f"{safe}.mp3"
        out = os.path.join(SHARED_PATH, mp3)
        generate_kokoro_mp3(text, out)

    return render_template_string(
        """
    <style>
    body { background:#111; color:#eee; font-family:Arial; text-align:center; }
    .box { display:inline-block; margin:10px; padding:10px; border:1px solid #333; }
    img { width:150px; }
    button { padding:10px 20px; margin-top:20px; }
    a {font-size:2.5wv; color:orange;}
    </style>
    <body>
    <h1>Kokoro TTS</h1>
    <a href="/">HOME</a>
    <form method="post">
    <textarea name="text" style="width:100%;height:200px;">{{text}}</textarea><br>
    <button>Generate</button>
    </form>

    {% if mp3 %}
    <audio controls>
    <source src="{{ url_for('static', filename='images/AI_images/' + mp3) }}">
    </audio>
    {% endif %}
    </body>
    """,
        mp3=mp3,
        text=text,
    )


# -------------------------------------------------
# CONFIG
# -------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STITCH_DIR = os.path.join(BASE_DIR, "static", "stitch")
RESULT_DIR = os.path.join(BASE_DIR, "static", "results")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

IMAGE_WIDTH = 768
IMAGE_HEIGHT = 512
TARGET_HEIGHT = 768
VIEWPORT_WIDTH = 512
FEATHER_PX = 100
REQUIRED = 4

TITLE_IMAGE_PATH = "static/assets/trans.png"
SCROLL_DURATION = 344  # seconds for full scroll

os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# -------------------------------------------------
# HELPERS
# -------------------------------------------------


def list_images():
    files = sorted(
        [
            f
            for f in os.listdir(STITCH_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]
    )
    ic("Available images:", files)
    return files


def feather_mask(width, height, fade_left=False, fade_right=False):
    mask = Image.new("L", (width, height), 255)
    px = mask.load()
    for x in range(width):
        alpha = 255
        if fade_left and x < FEATHER_PX:
            alpha = int(255 * (x / FEATHER_PX))
        if fade_right and x > width - FEATHER_PX:
            alpha = int(255 * ((width - x) / FEATHER_PX))
        for y in range(height):
            px[x, y] = alpha
    return mask


def stitch_images(ordered_files):
    ic("Final stitch order:", ordered_files)
    images = [
        Image.open(os.path.join(STITCH_DIR, f)).convert("RGBA") for f in ordered_files
    ]

    stitched_width = (IMAGE_WIDTH * REQUIRED) - (FEATHER_PX * (REQUIRED - 1))
    stitched_height = IMAGE_HEIGHT
    stitched = Image.new("RGBA", (stitched_width, stitched_height), (0, 0, 0, 0))

    x_offset = 0
    for idx, img in enumerate(images):
        fade_left = idx != 0
        fade_right = idx != REQUIRED - 1
        ic(f"Image {idx + 1}", "fade_left:", fade_left, "fade_right:", fade_right)
        mask = feather_mask(IMAGE_WIDTH, IMAGE_HEIGHT, fade_left, fade_right)
        img.putalpha(mask)
        stitched.alpha_composite(img, (x_offset, 0))
        ic("Pasted at x =", x_offset)
        x_offset += IMAGE_WIDTH - FEATHER_PX

    # Scale to target height
    scale = TARGET_HEIGHT / stitched_height
    new_width = int(stitched_width * scale)
    ic("Scaling", stitched.size, "->", (new_width, TARGET_HEIGHT))
    stitched = stitched.resize((new_width, TARGET_HEIGHT), resample=Image.LANCZOS)

    stitched_filename = f"stitched_{uuid.uuid4().hex}.png"
    stitched_path = os.path.join(TEMP_DIR, stitched_filename)
    stitched.convert("RGB").save(stitched_path)
    ic("Saved stitched PNG:", stitched_path)

    # ----------------------------
    # FFmpeg scroll + frame overlay
    # ----------------------------
    uid = uuid.uuid4().hex
    final_mp4 = os.path.join(RESULT_DIR, f"Ready_Stitched_{uid}.mp4")

    ffmpeg_cmd = f"""
    ffmpeg -hide_banner -loop 1 -i "{stitched_path}" -loop 1 -i "{TITLE_IMAGE_PATH}" \
    -filter_complex "[0:v]scale={new_width}:{TARGET_HEIGHT},scroll=horizontal=0.0001,crop={VIEWPORT_WIDTH}:{TARGET_HEIGHT}:0:0[bg]; \
    [bg][1:v]overlay=0:-5:format=auto:shortest=1" \
    -t {SCROLL_DURATION} -pix_fmt yuv420p -y "{final_mp4}"
    """

    ic("Running FFmpeg:", ffmpeg_cmd)
    subprocess.run(ffmpeg_cmd, shell=True, check=True)
    ic("Saved final video:", final_mp4)

    return os.path.basename(final_mp4)


# -------------------------------------------------
# ROUTES
# -------------------------------------------------


@app.route("/stitch", methods=["GET", "POST"])
def stitch():
    images = list_images()
    if request.method == "POST":
        positions = {}
        for img in images:
            pos = request.form.get(img)
            if pos and pos != "skip":
                positions[int(pos)] = img

        ic("Submitted positions:", positions)
        if len(positions) != REQUIRED or set(positions.keys()) != {1, 2, 3, 4}:
            flash("You must assign exactly one image to positions 1–4.")
            return redirect(url_for("stitch"))

        ordered = [positions[i] for i in range(1, 5)]
        result_file = stitch_images(ordered)
        session["last_result"] = result_file
        return redirect(url_for("result"))

    return render_template_string(
        """
    <!doctype html>
    <html>
    <head>
        <title>Visual Stitcher</title>
        <style>
            body { background:#111; color:#eee; font-family:sans-serif; }
            .grid { display:flex; flex-wrap:wrap; gap:15px; }
            .card { border:1px solid #333; padding:10px; width:220px; }
            img { width:200px; display:block; margin-bottom:8px; }
            select { width:100%; padding:5px; }
            button { margin-top:20px; padding:10px 20px; }
        </style>
    </head>
    <body>
        <h1>Preview Images & Choose Positions</h1>
        <form method="post">
            <div class="grid">
                {% for img in images %}
                <div class="card">
                    <img src="{{ url_for('static', filename='stitch/' + img) }}">
                    <select name="{{ img }}">
                        <option value="skip">skip</option>
                        <option value="1">position 1 (left)</option>
                        <option value="2">position 2</option>
                        <option value="3">position 3</option>
                        <option value="4">position 4 (right)</option>
                    </select>
                </div>
                {% endfor %}
            </div>
            <button type="submit">Stitch Selected Images</button>
        </form>
    </body>
    </html>
    """,
        images=images,
    )


@app.route("/result")
def result():
    filename = session.get("last_result")
    if not filename:
        return render_template_string(
            """
        <html>
        <body style="background:#111;color:#eee;font-family:sans-serif">
            <h1>No result available</h1>
            <a href="/">Go back</a>
        </body>
        </html>
        """
        )
    return render_template_string(
        """
    <!doctype html>
    <html><style>
    a {font-size:2.5wv; color:orange;}
    </style>
    <body style="background:#111;color:#eee;font-family:sans-serif">
        <h1>Stitched Result (512x768 Scrolling with Frame)</h1>
        <a href="/">HOME</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="/stitch">STITCH AGAIN</a><br /><br />
        <video src="{{ url_for('static', filename='results/' + filename) }}" controls autoplay loop></video>
        <br><br>
        <a href="/">Back</a>
    </body>
    </html>
    """,
        filename=filename,
    )
def get_mp3list():
    ic("Scanning MP3 directory:", AUDIO_DIR)

    if not os.path.exists(AUDIO_DIR):
        ic("ERROR: MP3 directory does not exist")
        return []

    files = []
    for f in sorted(os.listdir(AUDIO_DIR)):
        if f.lower().endswith(".mp3"):
            files.append(f)

    ic("MP3 files found:", files)
    return files

# -----------------------------
# ROUTE
# -----------------------------
AUDIO_FILE = "static/mp3/For_millions_of_year.mp3"
AUDIO= "mp3/For_millions_of_year.mp3"
@app.route("/play_audio")
def play_audio():
    mp3file_list = get_mp3list()
    ic("Serving music player page")

    if not os.path.exists(AUDIO_FILE):
        ic("ERROR: Main audio file not found:", AUDIO_FILE)

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Flask Music Player with Equalizer</title>
    <style>
        body {
            background: #0b0b0b;
            color: #eee;
            font-family: Arial;
            text-align: center;
        }
        canvas {
            width: 800px;
            height: 200px;
            background: #111;
            border-radius: 8px;
            margin: 20px auto;
            display: block;
        }
        .eq {
            display: flex;
            justify-content: center;
            gap: 8px;
        }
        .eq input {
            writing-mode: bt-lr;
            -webkit-appearance: slider-vertical;
            height: 150px;
        }
        .playlist {
            max-width: 800px;
            margin: 40px auto;
            text-align: left;
        }
        .track {
            background: #111;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 6px;
        }
        a {
            font-size: 2.5vw;
            color: orange;
        }
    </style>
</head>

<body>

<h2>🎵 Flask Music Player with Equalizer</h2>
<a href="/">HOME</a>

<br><br>

<!-- MAIN PLAYER (UNCHANGED) -->
<audio id="audio" controls crossorigin="anonymous">
    <source src="/static/mp3/For_millions_of_year.mp3" type="audio/mpeg">
</audio>

<canvas id="visualizer"></canvas>
<div class="eq" id="eq"></div>

<hr style="margin:40px 0; border-color:#222;">

<h3>📂 MP3 Playlist</h3>

<div class="playlist">
{% for mp3 in mp3file_list %}
    <div class="track">
        <strong>{{ mp3 }}</strong><br>
        <audio controls preload="none">
            <source src="/static/mp3/{{ mp3 }}" type="audio/mpeg">
        </audio>
    </div>
{% endfor %}
</div>

<script>
const audio = document.getElementById("audio");
const canvas = document.getElementById("visualizer");
const ctx = canvas.getContext("2d");

canvas.width = 800;
canvas.height = 200;

const AudioContext = window.AudioContext || window.webkitAudioContext;
const audioCtx = new AudioContext();

const source = audioCtx.createMediaElementSource(audio);
const analyser = audioCtx.createAnalyser();
analyser.fftSize = 256;

const frequencies = [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000];
const filters = [];
const eqContainer = document.getElementById("eq");

frequencies.forEach(freq => {
    const filter = audioCtx.createBiquadFilter();
    filter.type = "peaking";
    filter.frequency.value = freq;
    filter.Q.value = 1;
    filter.gain.value = 0;

    filters.push(filter);

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = -12;
    slider.max = 12;
    slider.value = 0;

    slider.oninput = () => filter.gain.value = slider.value;
    eqContainer.appendChild(slider);
});

source.connect(filters[0]);
for (let i = 0; i < filters.length - 1; i++) {
    filters[i].connect(filters[i + 1]);
}
filters[filters.length - 1].connect(analyser);
analyser.connect(audioCtx.destination);

audio.onplay = () => audioCtx.resume();

const bufferLength = analyser.frequencyBinCount;
const dataArray = new Uint8Array(bufferLength);

function draw() {
    requestAnimationFrame(draw);
    analyser.getByteFrequencyData(dataArray);

    ctx.fillStyle = "#111";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const barWidth = canvas.width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
        const barHeight = dataArray[i];
        ctx.fillStyle = `rgb(${barHeight + 50}, 100, 180)`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
        x += barWidth;
    }
}
draw();
</script>

</body>
</html>
""", mp3file_list=mp3file_list)



VIDEO_THUMB_SOURCE = os.path.join(app.static_folder, "videos")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi", ".webm")


@app.route("/video_browser")
def video_browser():
    ic("Loading SIMPLE video browser")

    video_files = []

    for filename in sorted(os.listdir(VIDEO_THUMB_SOURCE)):
        if filename.lower().endswith(VIDEO_EXTENSIONS):
            video_files.append(filename)

    ic(video_files)

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Video Browser</title>

<style>
body {
    background: #111;
    color: #eee;
    font-family: Arial, sans-serif;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
}
.item {
    background: #1e1e1e;
    border: 1px solid #333;
    padding: 10px;
    border-radius: 8px;
}
video {
    width: 100%;
    background: #000;
    border-radius: 6px;
}
.filename {
    margin-top: 8px;
    font-size: 14px;
    word-break: break-all;
}
            a {font-size:25px;color:orange;}
        </style>

</style>

</head>
<body>

<h1>🎬 Video Browser (No BS Edition)</h1>

        <a href="/">HOME</a>
<div class="grid">
{% for filename in video_files %}
    <div class="item">
        <video controls preload="metadata">
            <source src="/static/videos/{{ filename }}">
        </video>
        <div class="filename">{{ filename }}</div>
    </div>
{% endfor %}
</div>

</body>
</html>
""", video_files=video_files)

THUMB_DIR = "static/vidthumbs"

@app.route("/get_thumbs")
def get_thumbs():
    ic("Scanning thumbnail directory")

    if not os.path.exists(THUMB_DIR):
        ic("Thumbnail directory missing")
        return jsonify([])

    thumbs = [f for f in os.listdir(THUMB_DIR) if f.lower().endswith(".jpg")]
    thumbs.sort()
    ic(thumbs)
    return jsonify(thumbs)


@app.route("/thumbs")
def thumbs_page():
    ic("Rendering thumbs page")
    thumbs_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Video Thumbnails</title>
        <style>
            body { background: #111; color: #eee; font-family: sans-serif; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
            img { width: 100%; border-radius: 8px; box-shadow: 0 0 10px #000; }
            a {font-size:25px;color:orange;}
        </style>
    </head>
    <body>
        <h2>Video Thumbnails</h2>
        <a href="/">HOME</a>
        <div class="grid" id="thumbGrid"></div>
        <script>
        fetch("/get_thumbs")
            .then(res => res.json())
            .then(files => {
                const grid = document.getElementById("thumbGrid");
                files.forEach(f => {
                    const img = document.createElement("img");
                    img.src = "/static/vidthumbs/" + f;
                    img.loading = "lazy";
                    grid.appendChild(img);
                });
            });
        </script>
    </body>
    </html>
    """
    return Response(thumbs_html, mimetype="text/html")


@app.route("/videobrowser")
def videobrowser():
    ic("Loading SIMPLE video browser")

    video_files = []

    for filename in sorted(os.listdir(VIDEO_THUMB_SOURCE)):
        if filename.lower().endswith(VIDEO_EXTENSIONS):
            video_files.append(filename)

    ic(video_files)

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Video Browser</title>

<style>
body {
    background: #111;
    color: #eee;
    font-family: Arial, sans-serif;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
}
.item {
    background: #1e1e1e;
    border: 1px solid #333;
    padding: 10px;
    border-radius: 8px;
}
video {
    width: 100%;
    background: #000;
    border-radius: 6px;
}
.filename {
    margin-top: 8px;
    font-size: 14px;
    word-break: break-all;
}
a {font-size:25px;color:orange;}
</style>

</head>
<body>

<h1>🎬 Video Browser (No BS Edition)</h1>
<a href="/">HOME</a>
<div class="grid">
{% for filename in video_files %}
    <div class="item">
        <video controls preload="metadata">
            <source src="/static/videos/{{ filename }}">
        </video>
        <div class="filename">{{ filename }}</div>
    </div>
{% endfor %}
</div>

</body>
</html>
""", video_files=video_files)
# ADD Statable Defussion

SD_SERVER_URL = "http://127.0.0.1:5000"
SAVE_DIR = os.path.join("static", "novel_images")
os.makedirs(SAVE_DIR, exist_ok=True)

# Models directory configuration (prefers local Media_Studio/models, fallbacks to Comfy-UI)
LOCAL_MODELS_DIR = os.path.join(BASE_DIR, "models")
COMFY_MODELS_DIR = os.environ.get("COMFY_MODELS_DIR", "/home/jack/Desktop/Comfy-UI/models")

CHECKPOINTS_DIRS = [os.path.join(LOCAL_MODELS_DIR, "checkpoints"), os.path.join(COMFY_MODELS_DIR, "checkpoints")]
LORAS_DIRS = [os.path.join(LOCAL_MODELS_DIR, "loras"), os.path.join(COMFY_MODELS_DIR, "loras")]
VAE_DIRS = [os.path.join(LOCAL_MODELS_DIR, "vae"), os.path.join(COMFY_MODELS_DIR, "vae")]
CHECKPOINTS_DIR = CHECKPOINTS_DIRS[0] if os.path.exists(CHECKPOINTS_DIRS[0]) else CHECKPOINTS_DIRS[1]
LORAS_DIR = LORAS_DIRS[0] if os.path.exists(LORAS_DIRS[0]) else LORAS_DIRS[1]
VAE_DIR = VAE_DIRS[0] if os.path.exists(VAE_DIRS[0]) else VAE_DIRS[1]

def get_live_models():
    models = set()
    for c_dir in CHECKPOINTS_DIRS:
        if os.path.exists(c_dir):
            for root, dirs, files in os.walk(c_dir):
                for f in sorted(files):
                    if f.endswith((".safetensors", ".ckpt", ".pt", ".bin")) and not f.startswith("."):
                        models.add(os.path.basename(f))
    if os.path.exists(COMFY_MODELS_DIR):
        for f in sorted(os.listdir(COMFY_MODELS_DIR)):
            full_path = os.path.join(COMFY_MODELS_DIR, f)
            if os.path.isfile(full_path) and f.endswith((".safetensors", ".ckpt", ".pt", ".bin")) and not f.startswith("."):
                models.add(f)
    return sorted(list(models)) if models else ["realisticLCMBYStable_v10.safetensors"]

def get_live_loras():
    loras = set()
    for l_dir in LORAS_DIRS:
        if os.path.exists(l_dir):
            for root, dirs, files in os.walk(l_dir):
                for f in sorted(files):
                    if f.endswith((".safetensors", ".pt", ".ckpt", ".bin")) and not f.startswith("."):
                        loras.add(os.path.basename(f))
    return sorted(list(loras))

def get_live_vaes():
    vaes = set()
    for v_dir in VAE_DIRS:
        if os.path.exists(v_dir):
            for root, dirs, files in os.walk(v_dir):
                for f in sorted(files):
                    if f.endswith((".safetensors", ".pt", ".ckpt", ".bin")) and not f.startswith("."):
                        vaes.add(os.path.basename(f))
    return sorted(list(vaes))

AVAILABLE_MODELS = get_live_models()

HTMLD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stable Diffusion Client WebUI</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --bg-base: #060813;
            --bg-surface: #0c0f22;
            --bg-card: rgba(22, 28, 54, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(99, 102, 241, 0.2);
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --primary-glow: rgba(99, 102, 241, 0.4);
            
            --secondary: #8b5cf6;
            --accent: #14b8a6;
            
            --success: #10b981;
            --danger: #ef4444;
            
            --radius-sm: 8px;
            --radius-md: 14px;
            --radius-lg: 20px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background-image: 
                radial-gradient(circle at 5% 5%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 95% 95%, rgba(139, 92, 246, 0.08) 0%, transparent 40%);
            background-attachment: fixed;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.25rem 2rem;
            background-color: rgba(12, 15, 34, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
        }

        .logo-container {
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            width: 2.25rem;
            height: 2.25rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            box-shadow: 0 0 15px var(--primary-glow);
        }

        .logo-text {
            font-family: 'Outfit', sans-serif;
            font-size: 1.25rem;
            font-weight: 800;
            background: linear-gradient(to right, #ffffff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-badge {
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: rgba(14, 165, 233, 0.15);
            color: #38bdf8;
            padding: 0.2rem 0.5rem;
            border-radius: 99px;
            border: 1px solid rgba(14, 165, 233, 0.3);
        }

        main {
            display: grid;

            grid-template-columns: 420px 1fr;
            flex-grow: 1;
            max-width: 1500px;
            width: 100%;
            margin: 0 auto;

            gap: 1.5rem;
            padding: 1.5rem;
            align-items: center;
            
        }

        @media (max-width: 1024px) {
            main {

                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            transition: border-color 0.25s ease;
        }

        .card:hover {
            border-color: var(--border-glow);
        }

        .card-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.5rem;
            margin-bottom: 0.25rem;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }

        textarea {
            width: 100%;
            height: 100px;
            background-color: rgba(6, 8, 19, 0.8);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            padding: 0.75rem;
            font-family: inherit;
            font-size: 0.9rem;
            resize: vertical;
            outline: none;
            transition: all 0.2s ease;
        }

        textarea:focus, select:focus, input[type="number"]:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
            background-color: rgba(6, 8, 19, 0.95);
        }

        select, input[type="number"] {
            width: 100%;
            background-color: rgba(6, 8, 19, 0.8);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            padding: 0.75rem;
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.2s ease;
        }

        select {
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 0.75rem center;
            background-size: 1rem;
            padding-right: 2.2rem;
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
        }

        .range-container {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .range-container input[type="range"] {
            flex-grow: 1;
            height: 5px;
            background: rgba(255,255,255,0.1);
            border-radius: 99px;
            outline: none;
            -webkit-appearance: none;
            cursor: pointer;
        }

        .range-container input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: var(--primary);
            box-shadow: 0 0 8px var(--primary-glow);
        }

        .range-value {
            font-size: 0.85rem;
            font-weight: 700;
            color: #a5b4fc;
            min-width: 32px;
            text-align: right;
        }

        .mode-toggle-group {
            display: flex;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 4px;
            gap: 6px;
            margin-bottom: 0.75rem;
        }

        .mode-btn {
            flex: 1;
            padding: 8px 12px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-family: 'Outfit', sans-serif;
            font-size: 0.85rem;
            font-weight: 700;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .mode-btn.active {
            background: var(--primary);
            color: #ffffff;
            box-shadow: 0 0 12px var(--primary-glow);
        }

        .mode-btn:hover:not(.active) {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
        }

        .btn-action {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 6px 12px;
            font-size: 0.8rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            border: 1px solid var(--border-color);
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-primary);
            transition: all 0.2s ease;
        }

        .btn-action:hover {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.15);
            color: white;
        }

        button.primary-btn {
            width: 100%;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: 1rem;
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 15px var(--primary-glow);
            transition: all 0.25s ease;
        }

        button.primary-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }

        button.primary-btn:active {
            transform: translateY(1px);
        }

        button.primary-btn:disabled {
            background: rgba(22, 28, 54, 0.5);
            color: var(--text-muted);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        /* Workspace output styles */
        .workspace {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            min-height: 500px;
        }

        .display-card {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            background: rgba(12, 16, 33, 0.4);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 2rem;
            overflow: hidden;
            box-shadow: inset 0 0 30px rgba(0,0,0,0.6);
            max-width: 600px;
        }

        .image-container {
            max-width: 100%;
            max-height: 70vh;
            border-radius: var(--radius-md);
            overflow: hidden;
            box-shadow: 0 15px 35px rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.05);
            display: none;
            flex-direction: column;
            background-color: #04060c;
        }

        .image-container img {
            max-width: 100%;
            max-height: 60vh;
            object-fit: contain;
            display: block;
        }

        .image-meta {
            padding: .5rem;
            background: #0c0f22;
            border-top: 1px solid var(--border-color);
            font-size: 0.8rem;
            color: var(--text-secondary);
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .link-glow {
            color: #38bdf8;
            text-decoration: none;
            font-weight: 600;
            transition: text-shadow 0.2s ease;
        }

        .link-glow:hover {
            text-shadow: 0 0 8px rgba(56, 189, 248, 0.4);
            text-decoration: underline;
        }

        .status-container {
            font-size: 0.9rem;
            font-weight: 600;
            padding: 0.75rem 1.25rem;
            border-radius: var(--radius-sm);
            text-align: center;
            width: 100%;
            max-width: 450px;
            display: none;
            margin-bottom: 1.5rem;
            animation: fadeIn 0.3s ease;
        }

        .status-container.generating {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            background: rgba(99, 102, 241, 0.1);
            color: #a5b4fc;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }

        .status-container.success {
            display: block;
            background: rgba(16, 185, 129, 0.1);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .status-container.error {
            display: block;
            background: rgba(239, 68, 68, 0.1);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        /* Spinner animation */
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid transparent;
            border-top-color: currentColor;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-5px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .empty-state {
            text-align: center;
            max-width: 300px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
            color: var(--text-secondary);
        }

        .empty-icon {
            width: 60px;
            height: 60px;
            background: rgba(99, 102, 241, 0.03);
            border: 1px dashed rgba(99, 102, 241, 0.25);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }

        /* Clock timer display */
        .elapsed {
            font-family: monospace;
            font-size: 0.85rem;
            color: var(--accent);
            background: rgba(20, 184, 166, 0.1);
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
        }
        .no-wrap {
            white-space: nowrap;
        }
        .he {
            align-items: center;
        }

        /* Batch Studio Styles */
        .batch-tabs {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-bottom: 0.75rem;
        }
        .batch-tab-btn {
            padding: 7px 6px;
            font-size: 0.72rem;
            font-weight: 700;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }
        .batch-tab-btn:hover {
            border-color: var(--primary);
            color: var(--text-primary);
        }
        .batch-tab-btn.active {
            background: rgba(99, 102, 241, 0.25);
            border-color: var(--primary);
            color: #a5b4fc;
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
        }
        .batch-workspace {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            width: 100%;
        }
        .batch-header-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1rem;
            background: rgba(12, 16, 33, 0.7);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
        }
        .batch-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .batch-badge.idle {
            background: rgba(148, 163, 184, 0.15);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }
        .batch-badge.running {
            background: rgba(99, 102, 241, 0.25);
            color: #a5b4fc;
            border: 1px solid rgba(99, 102, 241, 0.4);
            animation: pulse 1.5s infinite;
        }
        .batch-badge.finished {
            background: rgba(16, 185, 129, 0.2);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }
        .batch-badge.stopped {
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .batch-console {
            background: #04060d;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 0.75rem;
            font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
            font-size: 0.75rem;
            color: #a5b4fc;
            height: 330px;
            min-height: 300px;
            max-height: 600px;
            resize: vertical;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.7);
        }
        .batch-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
            gap: 12px;
            max-height: 520px;
            overflow-y: auto;
            padding-right: 4px;
        }
        .batch-card {
            background: rgba(12, 16, 33, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .batch-card:hover {
            transform: translateY(-2px);
            border-color: var(--primary);
            box-shadow: 0 6px 20px rgba(0,0,0,0.6);
        }
        .batch-card img {
            width: 100%;
            aspect-ratio: 512 / 768;
            object-fit: cover;
            cursor: pointer;
            border-bottom: 1px solid var(--border-color);
            background: #020307;
            display: block;
        }
        .batch-card-info {
            padding: 6px 8px;
            font-size: 0.7rem;
            color: var(--text-secondary);
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        /* Hardware Monitor Telemetry Box */
        .telemetry-card {
            background: rgba(10, 14, 28, 0.85);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: var(--radius-sm);
            padding: 0.75rem 0.85rem;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            margin-top: 0.25rem;
            margin-bottom: 0.5rem;
        }
        .telemetry-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .telemetry-title {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: #e2e8f0;
            text-transform: uppercase;
        }
        .telemetry-badge {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            transition: all 0.2s ease;
        }
        .telemetry-badge.idle {
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .telemetry-badge.active {
            background: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.45);
            animation: telePulse 1.2s infinite ease-in-out;
        }
        .telemetry-badge.overloaded {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.45);
        }
        @keyframes telePulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(0.96); }
        }
        .telemetry-meters {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }
        .tele-meter-row {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        .tele-meter-labels {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.7rem;
        }
        .tele-lbl {
            color: #94a3b8;
            font-weight: 600;
        }
        .tele-val {
            font-family: 'JetBrains Mono', Consolas, monospace;
            color: #f1f5f9;
            font-weight: 700;
        }
        .tele-track {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 3px;
            overflow: hidden;
        }
        .tele-fill {
            height: 100%;
            width: 0%;
            border-radius: 3px;
            transition: width 0.35s ease, background-color 0.35s ease;
        }
        .telemetry-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding-top: 4px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        .tele-note {
            font-size: 0.68rem;
            color: #94a3b8;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex: 1;
        }
        .tele-clean-btn {
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: #38bdf8;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s;
            white-space: nowrap;
        }
        .tele-clean-btn:hover {
            background: #38bdf8;
            color: #050814;
        }
    </style>
</head>
<body>

    <header> 
        <div class="logo-container">
            <div class="logo-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
                    <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <span class="logo-text">FLASK SD CLIENT</span>
            <a class="logo-badge" href="/">HOME</a>
            <a class="logo-badge" href="/ask_gemini">✨ GEMINI</a>
            <span class="logo-badge">novel client</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            {% include 'system_monitor_widget.html' %}
        </div>
    </header>

    <main>

        <!-- Sidebar Column -->
        <div class="card">
            <div class="card-title">Generation Control</div>

            <!-- Hardware Resource Telemetry Panel -->
            <div class="telemetry-card">
                <div class="telemetry-head">
                    <div class="telemetry-title">
                        <span class="sys-status-dot dot-pulse" id="teleDot"></span>
                        <span>Hardware Monitor</span>
                    </div>
                    <span class="telemetry-badge idle" id="teleBadge">STANDBY</span>
                </div>
                <div class="telemetry-meters">
                    <div class="tele-meter-row">
                        <div class="tele-meter-labels">
                            <span class="tele-lbl">⚡ CPU Usage</span>
                            <span class="tele-val" id="teleCpuText">0%</span>
                        </div>
                        <div class="tele-track">
                            <div class="tele-fill" id="teleCpuBar" style="width: 0%; background: #10b981;"></div>
                        </div>
                    </div>
                    <div class="tele-meter-row">
                        <div class="tele-meter-labels">
                            <span class="tele-lbl">🧠 RAM Memory</span>
                            <span class="tele-val" id="teleRamText">0 / 0 GB (0%)</span>
                        </div>
                        <div class="tele-track">
                            <div class="tele-fill" id="teleRamBar" style="width: 0%; background: #10b981;"></div>
                        </div>
                    </div>
                </div>
                <div class="telemetry-footer">
                    <div id="teleSurgeNote" class="tele-note">Standby • Monitoring generation load</div>
                    <button type="button" class="tele-clean-btn" onclick="triggerFreeMemory(event)" title="Run Garbage Collector & Flush Caches">🧹 Flush RAM</button>
                </div>
            </div>

            <!-- Mode Selector: Text to Image vs Image to Image vs Batch Sweepers -->
            <div class="mode-toggle-group">
                <button type="button" class="mode-btn active" id="btnModeTxt2Img" onclick="setMode('txt2img')">
                    ✍️ Txt2Img
                </button>
                <button type="button" class="mode-btn" id="btnModeImg2Img" onclick="setMode('img2img')">
                    🖼️ Img2Img
                </button>
                <button type="button" class="mode-btn" id="btnModeBatch" onclick="setMode('batch')">
                    ⚡ Batch Studio
                </button>
            </div>

            <!-- Standard Controls (Txt2Img / Img2Img) -->
            <div id="standardControls">
                <!-- Img2Img Init Image Section -->
                <div id="img2imgSection" style="display: none; background: rgba(255,255,255,0.02); padding: 0.75rem; border-radius: var(--radius-sm); border: 1px dashed var(--primary); margin-bottom: 0.75rem;">
                    <label style="font-size: 0.75rem; color: var(--primary); display: block; margin-bottom: 0.5rem;">
                        Source Image (Init Image)
                    </label>
                    <input type="file" id="initImageInput" accept="image/*" onchange="handleInitImageUpload(this)" style="display: none;">
                    <div style="display: flex; gap: 8px; margin-bottom: 0.5rem;">
                        <button type="button" class="btn-action" onclick="document.getElementById('initImageInput').click()">
                            📁 Choose Image File
                        </button>
                        <button type="button" class="btn-action" onclick="useLastGeneratedImage()">
                            🔄 Use Last Generated
                        </button>
                    </div>
                    <div id="initImagePreviewContainer" style="display: none; text-align: center; margin: 8px 0;">
                        <img id="initImagePreview" src="" alt="Init Preview" style="max-width: 100%; max-height: 180px; border-radius: 6px; border: 1px solid var(--border-color);">
                    </div>
                    <div class="form-group" style="margin-top: 0.5rem;">
                        <label style="font-size: 0.65rem; color: var(--text-muted);">Transformation Strength (<span id="strengthVal">0.65</span>)</label>
                        <div class="range-container">
                            <input type="range" id="strength" min="0.05" max="1.0" step="0.05" value="0.65" oninput="document.getElementById('strengthVal').innerText = this.value">
                        </div>
                    </div>
                </div>

                <!-- Prompt -->
                <div class="form-group">
                    <label for="prompt">Prompt</label>
                    <textarea id="prompt">A beautiful alien cyborg with robotic body and human face long wild wild hair sitting on a rock near a waterfall, wearing a tarnished and stained brass bikini.</textarea>
                </div>

                <!-- Model Selection -->
                <div class="form-group">
                    <label for="model">Base Checkpoint (Models)</label>
                    <select id="model">
                        <option value="" disabled selected>Loading Models...</option>
                    </select>
                </div>

                <!-- VAE Selection -->
                <div class="form-group">
                    <label for="vae">VAE (Variational Autoencoder)</label>
                    <select id="vae">
                        <option value="">Default (Baked into Model)</option>
                    </select>
                </div>

                <!-- LoRA 1 selection -->
                <div class="form-group" style="background: rgba(255,255,255,0.02); padding: 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
                    <label for="lora1">LoRA Adapter 1</label>
                    <select id="lora1" style="margin-bottom: 0.5rem;">
                        <option value="">None (Disabled)</option>
                    </select>
                    <div class="form-group">
                        <label style="font-size: 0.65rem; color: var(--text-muted);">LoRA 1 Weight</label>
                        <div class="range-container">
                            <input type="range" id="lora1_weight" min="-2" max="2" step="0.05" value="0.75" oninput="document.getElementById('lora1Val').innerText = this.value">
                            <span class="range-value" id="lora1Val">0.75</span>
                        </div>
                    </div>
                </div>

                <!-- LoRA 2 selection -->
                <div class="form-group" style="background: rgba(255,255,255,0.02); padding: 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
                    <label for="lora2">LoRA Adapter 2</label>
                    <select id="lora2" style="margin-bottom: 0.5rem;">
                        <option value="">None (Disabled)</option>
                    </select>
                    <div class="form-group">
                        <label style="font-size: 0.65rem; color: var(--text-muted);">LoRA 2 Weight</label>
                        <div class="range-container">
                            <input type="range" id="lora2_weight" min="-2" max="2" step="0.05" value="0.75" oninput="document.getElementById('lora2Val').innerText = this.value">
                            <span class="range-value" id="lora2Val">0.75</span>
                        </div>
                    </div>
                </div>

                <!-- Hyperparameters Grid -->
                <div class="grid-2">
                    <div class="form-group">
                        <label for="steps">Steps</label>
                        <input id="steps" type="number" value="6" min="1" max="150">
                    </div>
                    <div class="form-group">
                        <label for="guidance">Guidance Scale</label>
                        <input id="guidance" type="number" step="0.1" value="1.5" min="0.5" max="30">
                    </div>
                </div>

                <div class="grid-2">
                    <div class="form-group">
                        <label for="width">Width</label>
                        <select id="width">
                            <option value="256">256 px</option>
                            <option value="384">384 px</option>
                            <option value="512" selected>512 px</option>
                            <option value="768">768 px</option>
                            <option value="1024">1024 px</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="height">Height</label>
                        <select id="height">
                            <option value="256">256 px</option>
                            <option value="384">384 px</option>
                            <option value="512">512 px</option>
                            <option value="768" selected>768 px</option>
                            <option value="1024">1024 px</option>
                        </select>
                    </div>
                </div>

                <!-- Seed -->
                <div class="form-group">
                    <label for="seed">Seed (0 = Random)</label>
                    <input id="seed" type="number" value="0" min="0">
                </div>

                <button type="button" class="primary-btn" id="generateBtn" onclick="generateImage()">Generate Image (Txt2Img)</button>
            </div>

            <!-- Batch Studio Controls -->
            <div id="batchControls" style="display: none; flex-direction: column; gap: 0.85rem;">
                <!-- Sub-Tool Tabs -->
                <div>
                    <label style="margin-bottom: 0.4rem; display: block;">Batch Generation Mode</label>
                    <div class="batch-tabs">
                        <button type="button" class="batch-tab-btn active" id="tab_cfg_sweep" onclick="setBatchTool('cfg_sweep')">🎛️ CFG Sweep</button>
                        <button type="button" class="batch-tab-btn" id="tab_slerp" onclick="setBatchTool('slerp')">🔀 Long Prompt SLERP</button>
                        <button type="button" class="batch-tab-btn" id="tab_long_prompt" onclick="setBatchTool('long_prompt')">📜 Long Prompt</button>
                        <button type="button" class="batch-tab-btn" id="tab_seed_explorer" onclick="setBatchTool('seed_explorer')">🎲 Seed Explorer</button>
                        <button type="button" class="batch-tab-btn" id="tab_all_models" onclick="setBatchTool('all_models')">🏆 Benchmark All</button>
                    </div>
                </div>

                <!-- Tool Info Banner -->
                <div id="batchToolInfo" style="font-size: 0.72rem; color: #c7d2fe; background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.25); padding: 0.5rem 0.75rem; border-radius: 6px;">
                    Fixed-seed CFG scale sweeper generating 512×768 image sequences across step increments.
                </div>

                <!-- Active Sweep Detection Banner -->
                <div id="activeSweepBanner" style="display: none; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 8px; padding: 10px 12px; font-size: 0.8rem; color: #a7f3d0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: #34d399;">⚡ Existing Sweep Found (Seed <span id="sweepSeedVal">3360</span>)</span>
                        <span style="font-size: 0.75rem; background: rgba(16, 185, 129, 0.25); padding: 2px 8px; border-radius: 12px;" id="sweepCountVal">74 images</span>
                    </div>
                    <div style="color: #e2e8f0; font-size: 0.78rem; margin-bottom: 8px;">
                        Last Image: <code style="color: #6ee7b7;" id="sweepLastFileVal">3360_2-23.png</code> (CFG: <strong id="sweepLastCfgVal">2.23</strong>)
                    </div>
                    <button type="button" class="btn-action" onclick="applyExistingSweep()" style="background: rgba(16, 185, 129, 0.25); border: 1px solid #34d399; color: #fff; font-size: 0.78rem; padding: 5px 12px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: 600;">
                        ▶️ Resume This Sweep (CFG <span id="sweepNextCfgBtn">2.24</span>)
                    </button>
                </div>

                <!-- Active SLERP Tracking Banner -->
                <div id="activeSlerpBanner" style="display: none; background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 8px; padding: 10px 12px; font-size: 0.8rem; color: #c7d2fe;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: #818cf8;">🔀 Existing SLERP Tracking (Seed <span id="slerpSeedVal">3360</span>)</span>
                        <span style="font-size: 0.75rem; background: rgba(99, 102, 241, 0.3); padding: 2px 8px; border-radius: 12px;" id="slerpCountVal">0 frames</span>
                    </div>
                    <div style="color: #e2e8f0; font-size: 0.78rem; margin-bottom: 8px;">
                        Last Frame: <code style="color: #a5b4fc;" id="slerpLastFileVal">None</code> (Progress: <strong id="slerpProgressVal">0%</strong>)
                    </div>
                    <button type="button" class="btn-action" onclick="applyExistingSlerp()" style="background: rgba(99, 102, 241, 0.3); border: 1px solid #818cf8; color: #fff; font-size: 0.78rem; padding: 5px 12px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: 600;">
                        ▶️ Load SLERP Parameters (Frame <span id="slerpNextFrameBtn">1</span>)
                    </button>
                </div>

                <!-- Active All Models Benchmark Tracking Banner -->
                <div id="activeAllModelsBanner" style="display: none; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 8px; padding: 10px 12px; font-size: 0.8rem; color: #bae6fd;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: #38bdf8;">🏆 Existing Models Benchmark (Seed <span id="allModelsSeedVal">3407</span>)</span>
                        <span style="font-size: 0.75rem; background: rgba(56, 189, 248, 0.25); padding: 2px 8px; border-radius: 12px;" id="allModelsCountVal">0 / 24 models</span>
                    </div>
                    <div style="color: #e2e8f0; font-size: 0.78rem; margin-bottom: 8px;">
                        Last Checkpoint: <code style="color: #7dd3fc;" id="allModelsLastModelVal">None</code> (Progress: <strong id="allModelsProgressVal">0%</strong>)
                    </div>
                    <button type="button" class="btn-action" onclick="applyExistingAllModels()" style="background: rgba(56, 189, 248, 0.25); border: 1px solid #38bdf8; color: #fff; font-size: 0.78rem; padding: 5px 12px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: 600;">
                        ▶️ Resume Benchmark (Keep Existing models.json)
                    </button>
                </div>

                <!-- Batch Prompt 1 -->
                <div class="form-group">
                    <label for="batch_prompt" id="batchPromptLabel">Prompt</label>
                    <textarea id="batch_prompt" style="height: 80px;">A close up of a beautiful alien cyborg, steampunk robotic body, human face, long wild hair, sitting on a mossy rock near a waterfall, wearing battle armor, staring directly into camera, highly detailed, photorealistic 8k</textarea>
                </div>

                <!-- Destination Prompt (for SLERP Morph Target) -->
                <div class="form-group" id="batchPrompt2Group" style="display: none;">
                    <label for="batch_prompt2" style="color: #67e8f9;">Destination Prompt (Prompt B - Morph Target)</label>
                    <textarea id="batch_prompt2" style="height: 80px;">A futuristic cyberpunk metropolis at midnight, neon blue and magenta reflections, towering holographic skyscrapers in the pouring rain, flying futuristic spinners, cinematic lighting, ultra detailed 8k architectural concept art</textarea>
                </div>

                <!-- Negative Prompt (for Long Prompt LCM & SLERP) -->
                <div class="form-group" id="batchNegPromptGroup" style="display: none;">
                    <label for="batch_negative_prompt">Negative Prompt</label>
                    <textarea id="batch_negative_prompt" style="height: 55px;">blurry, bad anatomy, bad hands, cropped, low quality, artifacts, watermark</textarea>
                </div>

                <!-- Checkpoint Model Group -->
                <div class="form-group" id="batchModelGroup">
                    <label for="batch_model">Base Checkpoint</label>
                    <select id="batch_model">
                        <option value="" disabled selected>Loading Models...</option>
                    </select>
                </div>

                <!-- All Models Notice -->
                <div id="batchAllModelsNotice" style="display: none; font-size: 0.75rem; color: #34d399; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); padding: 0.6rem; border-radius: 6px;">
                    ✨ Will benchmark across <strong>all 24 Comfy-UI model checkpoints</strong> sequentially using identical seed and prompt!
                </div>

                <!-- VAE Selection -->
                <div class="form-group">
                    <label for="batch_vae">VAE</label>
                    <select id="batch_vae">
                        <option value="">Default (Baked into Model)</option>
                    </select>
                </div>

                <!-- LoRA Selection & Scale -->
                <div class="form-group" style="background: rgba(255,255,255,0.02); padding: 0.65rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
                    <label for="batch_lora">LoRA Adapter (Optional)</label>
                    <select id="batch_lora" style="margin-bottom: 0.5rem;">
                        <option value="">None (Disabled)</option>
                    </select>
                    <div class="form-group">
                        <label style="font-size: 0.65rem; color: var(--text-muted);">LoRA Scale (<span id="batchLoraVal">0.25</span>)</label>
                        <div class="range-container">
                            <input type="range" id="batch_lora_scale" min="0.0" max="1.5" step="0.05" value="0.25" oninput="document.getElementById('batchLoraVal').innerText = this.value">
                        </div>
                    </div>
                </div>

                <!-- Hyperparameters Grid -->
                <div class="grid-2">
                    <div class="form-group" id="batchStepsGroup">
                        <label for="batch_steps">Steps</label>
                        <input id="batch_steps" type="number" value="5" min="1" max="100">
                    </div>
                    <div class="form-group" id="batchGuidanceGroup" style="display: none;">
                        <label for="batch_guidance">CFG Scale</label>
                        <input id="batch_guidance" type="number" step="0.1" value="1.5" min="0.5" max="30">
                    </div>
                    <div class="form-group" id="batchSeedGroup">
                        <label for="batch_seed" id="batchSeedLabel">Seed (0 = Random)</label>
                        <input id="batch_seed" type="number" value="3360" min="0">
                    </div>
                    <div class="form-group" id="batchNumImagesGroup">
                        <label for="batch_num_images" id="batchNumImagesLabel">Num Images</label>
                        <input id="batch_num_images" type="number" value="30" min="1" max="200">
                    </div>
                    <div class="form-group" id="batchFpsGroup" style="display: none;">
                        <label for="batch_fps">Video FPS</label>
                        <input id="batch_fps" type="number" value="10" min="1" max="60">
                    </div>
                </div>

                <!-- CFG Sweep Specifics -->
                <div class="grid-2" id="batchCfgGroup">
                    <div class="form-group">
                        <label for="batch_cfg_start">CFG Start</label>
                        <input id="batch_cfg_start" type="number" step="0.001" value="1.0" min="0.5" max="15">
                    </div>
                    <div class="form-group">
                        <label for="batch_cfg_step">CFG Step (+)</label>
                        <input id="batch_cfg_step" type="number" step="0.001" value="0.01" min="0.001" max="2.0">
                    </div>
                </div>

                <div style="font-size: 0.72rem; color: #a5b4fc; background: rgba(99,102,241,0.08); padding: 6px 10px; border-radius: 6px; border: 1px solid rgba(99,102,241,0.2);">
                    📐 Resolution: <strong>512 × 768</strong> &nbsp;|&nbsp; 🔒 4 CPU Threads Locked
                </div>

                <button type="button" class="primary-btn" id="batchRunBtn" onclick="runBatchGenerator()">🚀 Launch CFG Sweeper</button>
                <button type="button" class="btn-action" id="batchStopBtn" onclick="stopBatch()" style="display:none; width:100%; margin-top: 4px; background: rgba(239, 68, 68, 0.2); border-color: rgba(239, 68, 68, 0.4); color: #fca5a5;">🛑 Stop Batch Task</button>
            </div>
        </div>

        <!-- Output Canvas Column -->
        <div class="workspace now-rap">
            <!-- Single Workspace (Txt2Img / Img2Img) -->
            <div id="singleWorkspace" style="display: flex; flex-direction: column; width: 100%; align-items: center;">
                <!-- Loading Status Indicator -->
                <div class="status-container" id="statusBox"></div>

                <!-- Display Area -->
                <div class="display-card">
                    <!-- Empty Placeholder -->
                    <div class="empty-state" id="emptyState">
                        <div class="empty-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5"/>
                                <polyline points="21 15 16 10 5 21"/>
                            </svg>
                        </div>
                        <h3 style="font-family: 'Outfit', sans-serif; font-size: 1rem; font-weight: 600; color: white;">No Image Generated</h3>
                        <p style="font-size: 0.85rem; margin-top: 0.25rem;">Choose Text to Image or Image to Image, select your base checkpoint, and click Generate.</p>
                    </div>

                    <!-- Generated Image Display -->
                    <div class="image-container" id="imageWrapper">
                        <img id="image" src="" alt="Stable Diffusion Render">
                        <div style="padding: 0.5rem 0.75rem; background: #0c0f22; display: flex; gap: 8px; justify-content: flex-end; border-top: 1px solid var(--border-color);">
                            <button type="button" class="btn-action" onclick="sendOutputToImg2Img()">
                                🔁 Send to Image to Image
                            </button>
                        </div>
                        <div class="image-meta now-rap" id="imageMeta">
                            <!-- Loaded stats rendered dynamically -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Batch Studio Workspace -->
            <div id="batchWorkspace" class="batch-workspace" style="display: none;">
                <!-- Batch Header & Metrics -->
                <div class="batch-header-bar">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.95rem; color: white;">⚡ Batch Studio</span>
                        <span class="batch-badge idle" id="batchStatusPill">IDLE</span>
                        <span class="elapsed" id="batchTimer">00.0s</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">Images: <strong id="batchImageCount" style="color: #38bdf8;">0</strong></span>
                        <button type="button" class="btn-action" style="padding: 3px 8px; font-size: 0.7rem;" onclick="clearBatchView()">🧹 Clear Log</button>
                    </div>
                </div>

                <!-- Real-time Terminal Log Console -->
                <div>
                    <label style="font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.35rem; display: block;">LIVE PROCESS STDOUT CONSOLE</label>
                    <div id="batchConsole" class="batch-console">Awaiting batch task execution. Select a tool and launch.</div>
                </div>

                <!-- 512x768 Real-time Image Gallery -->
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 8px;">
                        <label style="font-size: 0.75rem; color: var(--text-primary); font-weight: 700;">✨ GENERATED 512×768 IMAGES</label>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <a href="/static/live_slerp.html" target="_blank" class="btn-action" style="padding: 3px 10px; font-size: 0.72rem; text-decoration: none; color: #38bdf8; border-color: #0284c7; background: rgba(2, 132, 199, 0.15);">📡 Fullscreen Live Viewer & Flipbook</a>
                            <span style="font-size: 0.7rem; color: var(--accent);">Target Dir: static/novel_images/</span>
                        </div>
                    </div>

                    <!-- Active Latest Generated Frame Preview Card -->
                    <div id="batchPreviewCard" style="display: none; margin-bottom: 1rem; background: var(--card-bg, #1a1a24); border: 1px solid var(--accent, #6366f1); border-radius: var(--radius-sm, 8px); padding: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 0.85rem; font-weight: 700; color: #38bdf8;">🖼️ LATEST GENERATED FRAME PREVIEW (512×768)</span>
                                <span id="batchPreviewBadge" class="batch-badge running" style="font-size: 0.65rem; padding: 2px 6px;">STREAMING</span>
                            </div>
                            <span id="batchPreviewMeta" style="font-size: 0.75rem; color: #a5b4fc;">Frame --</span>
                        </div>
                        <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap;">
                            <div style="flex: 0 0 auto; max-width: 280px; width: 100%;">
                                <a id="batchPreviewLink" href="#" target="_blank" title="Click to view full 512x768 resolution">
                                    <img id="batchPreviewImg" src="" alt="Latest frame preview" style="width: 100%; border-radius: 6px; border: 1px solid var(--border-color); background: #000; aspect-ratio: 512/768; object-fit: contain; display: block;">
                                </a>
                            </div>
                            <div style="flex: 1; min-width: 220px; display: flex; flex-direction: column; gap: 8px; font-size: 0.8rem; color: var(--text-secondary);">
                                <div><strong style="color: var(--text-primary);">Filename:</strong> <span id="batchPreviewFilename" style="color: #38bdf8; font-family: monospace;">--</span></div>
                                <div><strong style="color: var(--text-primary);">Total Generated:</strong> <span id="batchPreviewCount" style="color: #a3e635;">0 frames</span></div>
                                <div><strong style="color: var(--text-primary);">Resolution:</strong> <span style="color: #cbd5e1;">512 × 768 (LCM Diffusion)</span></div>
                                <div style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                                    <button type="button" class="btn-action" style="padding: 4px 10px; font-size: 0.75rem;" onclick="sendLatestBatchToImg2Img()">🔁 Img2Img</button>
                                    <a id="batchPreviewDownloadBtn" href="#" download class="btn-action" style="padding: 4px 10px; font-size: 0.75rem; text-decoration: none;">⬇️ Download Full PNG</a>
                                    <a href="/static/live_slerp.html" target="_blank" class="btn-action" style="padding: 4px 10px; font-size: 0.75rem; text-decoration: none; color: #a855f7; border-color: #9333ea;">🎬 Flipbook Player</a>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Compiled Video Preview Box -->
                    <div id="batchVideoPreviewContainer" style="display: none; margin-bottom: 1rem; background: var(--card-bg, #1a1a24); border: 1px solid var(--accent, #6366f1); border-radius: var(--radius-sm, 8px); padding: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span id="batchVideoTitle" style="font-size: 0.85rem; font-weight: 700; color: #a5b4fc;">🎬 COMPILED BATCH VIDEO</span>
                            <div style="display: flex; gap: 8px; align-items: center;">
                                <span style="font-size: 0.7rem; color: #a3e635;">✓ Copied to static/temp_exp/</span>
                                <a id="batchVideoDownloadLink" href="#" download class="btn-action" style="padding: 2px 8px; font-size: 0.7rem; text-decoration: none;">⬇️ Download MP4</a>
                            </div>
                        </div>
                        <video id="batchVideoPlayer" controls autoplay loop muted style="width: 100%; max-height: 460px; border-radius: 6px; background: #000; display: block;"></video>
                    </div>

                    <div id="batchEmptyGallery" style="text-align: center; padding: 2.5rem; color: var(--text-muted); border: 1px dashed var(--border-color); border-radius: var(--radius-sm); font-size: 0.85rem;">
                        No batch images detected for this run yet.<br>Generated 512×768 frames will stream into this gallery in real time!
                    </div>
                    <div id="batchGallery" class="batch-gallery"></div>
                </div>
            </div>
        </div>

    </main>

    <script>
        let timerInterval = null;
        let startTimestamp = null;
        let currentMode = "txt2img";
        let initImageData = null;

        // Batch Studio state
        let currentBatchTool = "cfg_sweep";
        let currentBatchTaskId = null;
        let batchPollInterval = null;
        let batchStartTime = null;

        function setMode(mode) {
            currentMode = mode;
            let btnTxt = document.getElementById("btnModeTxt2Img");
            let btnImg = document.getElementById("btnModeImg2Img");
            let btnBatch = document.getElementById("btnModeBatch");

            let standardControls = document.getElementById("standardControls");
            let img2imgSection = document.getElementById("img2imgSection");
            let batchControls = document.getElementById("batchControls");
            let genBtn = document.getElementById("generateBtn");

            let singleWorkspace = document.getElementById("singleWorkspace");
            let batchWorkspace = document.getElementById("batchWorkspace");

            btnTxt.classList.remove("active");
            btnImg.classList.remove("active");
            btnBatch.classList.remove("active");

            if (mode === "img2img") {
                btnImg.classList.add("active");
                standardControls.style.display = "block";
                img2imgSection.style.display = "block";
                batchControls.style.display = "none";
                singleWorkspace.style.display = "flex";
                batchWorkspace.style.display = "none";
                genBtn.innerText = "Transform Image (Img2Img)";
            } else if (mode === "batch") {
                btnBatch.classList.add("active");
                standardControls.style.display = "none";
                img2imgSection.style.display = "none";
                batchControls.style.display = "flex";
                singleWorkspace.style.display = "none";
                batchWorkspace.style.display = "flex";
                setBatchTool(currentBatchTool);
            } else {
                btnTxt.classList.add("active");
                standardControls.style.display = "block";
                img2imgSection.style.display = "none";
                batchControls.style.display = "none";
                singleWorkspace.style.display = "flex";
                batchWorkspace.style.display = "none";
                genBtn.innerText = "Generate Image (Txt2Img)";
            }
        }

        const toolDescriptions = {
            "cfg_sweep": "Fixed-seed CFG scale sweeper generating 512×768 image sequences across step increments.",
            "slerp": "Spherical Linear Interpolation (SLERP) morphing smoothly between two long prompts of arbitrary length, compiling to static/temp_exp/slerpX.mp4.",
            "long_prompt": "Long-prompt chunked embedding encoder generating 512×768 LCM images with unlimited token length.",
            "seed_explorer": "Multi-seed batch generator producing 512×768 images across multiple checkpoints or seeds.",
            "all_models": "Model comparative benchmarking script synthesizing 512×768 outputs across all 24 Comfy-UI checkpoints."
        };

        function setBatchTool(tool) {
            currentBatchTool = tool;
            ["cfg_sweep", "slerp", "long_prompt", "seed_explorer", "all_models"].forEach(t => {
                let el = document.getElementById("tab_" + t);
                if (el) el.classList.remove("active");
            });
            let activeTab = document.getElementById("tab_" + tool);
            if (activeTab) activeTab.classList.add("active");

            document.getElementById("batchToolInfo").innerText = toolDescriptions[tool] || "";

            let modelGroup = document.getElementById("batchModelGroup");
            let allModelsNotice = document.getElementById("batchAllModelsNotice");
            let promptLabel = document.getElementById("batchPromptLabel");
            let prompt2Group = document.getElementById("batchPrompt2Group");
            let negPromptGroup = document.getElementById("batchNegPromptGroup");
            let cfgGroup = document.getElementById("batchCfgGroup");
            let numImagesGroup = document.getElementById("batchNumImagesGroup");
            let numImagesLabel = document.getElementById("batchNumImagesLabel");
            let guidanceGroup = document.getElementById("batchGuidanceGroup");
            let seedLabel = document.getElementById("batchSeedLabel");
            let fpsGroup = document.getElementById("batchFpsGroup");
            let runBtn = document.getElementById("batchRunBtn");

            let sweepBanner = document.getElementById("activeSweepBanner");
            let slerpBanner = document.getElementById("activeSlerpBanner");
            let allModelsBanner = document.getElementById("activeAllModelsBanner");
            if (tool === "cfg_sweep") {
                modelGroup.style.display = "flex";
                allModelsNotice.style.display = "none";
                if (promptLabel) promptLabel.innerText = "Prompt";
                if (prompt2Group) prompt2Group.style.display = "none";
                negPromptGroup.style.display = "none";
                cfgGroup.style.display = "grid";
                numImagesGroup.style.display = "block";
                if (numImagesLabel) numImagesLabel.innerText = "Num Images";
                guidanceGroup.style.display = "none";
                if (fpsGroup) fpsGroup.style.display = "none";
                if (seedLabel) seedLabel.innerText = "Seed (0 = Random)";
                runBtn.innerText = "🚀 Launch CFG Sweeper (512×768)";
                if (slerpBanner) slerpBanner.style.display = "none";
                if (allModelsBanner) allModelsBanner.style.display = "none";
                checkExistingSweep();
            } else {
                if (sweepBanner) sweepBanner.style.display = "none";
            }
            if (tool === "slerp") {
                modelGroup.style.display = "flex";
                allModelsNotice.style.display = "none";
                if (promptLabel) promptLabel.innerText = "Start Prompt (Prompt A - Morph Origin)";
                if (prompt2Group) prompt2Group.style.display = "block";
                negPromptGroup.style.display = "flex";
                cfgGroup.style.display = "none";
                numImagesGroup.style.display = "block";
                if (numImagesLabel) numImagesLabel.innerText = "Morph Frames";
                guidanceGroup.style.display = "block";
                if (fpsGroup) fpsGroup.style.display = "block";
                if (seedLabel) seedLabel.innerText = "Fixed Morph Seed";
                runBtn.innerText = "🚀 Generate Long Prompt SLERP Video (512×768)";
                if (sweepBanner) sweepBanner.style.display = "none";
                if (allModelsBanner) allModelsBanner.style.display = "none";
                checkExistingSlerp();
            } else {
                if (slerpBanner) slerpBanner.style.display = "none";
            }
            if (tool === "long_prompt") {
                if (allModelsBanner) allModelsBanner.style.display = "none";
                modelGroup.style.display = "flex";
                allModelsNotice.style.display = "none";
                if (promptLabel) promptLabel.innerText = "Prompt (Unlimited Tokens)";
                if (prompt2Group) prompt2Group.style.display = "none";
                negPromptGroup.style.display = "flex";
                cfgGroup.style.display = "none";
                numImagesGroup.style.display = "none";
                guidanceGroup.style.display = "block";
                if (fpsGroup) fpsGroup.style.display = "none";
                if (seedLabel) seedLabel.innerText = "Seed (0 = Random)";
                runBtn.innerText = "🚀 Synthesize Long Prompt (512×768)";
            } else if (tool === "seed_explorer") {
                if (allModelsBanner) allModelsBanner.style.display = "none";
                modelGroup.style.display = "flex";
                allModelsNotice.style.display = "none";
                if (promptLabel) promptLabel.innerText = "Prompt";
                if (prompt2Group) prompt2Group.style.display = "none";
                negPromptGroup.style.display = "none";
                cfgGroup.style.display = "none";
                numImagesGroup.style.display = "block";
                if (numImagesLabel) numImagesLabel.innerText = "Num Images";
                guidanceGroup.style.display = "block";
                if (fpsGroup) fpsGroup.style.display = "none";
                if (seedLabel) seedLabel.innerText = "Base Seed";
                runBtn.innerText = "🚀 Run Seed Explorer (512×768)";
            } else if (tool === "all_models") {
                modelGroup.style.display = "none";
                allModelsNotice.style.display = "block";
                if (promptLabel) promptLabel.innerText = "Prompt";
                if (prompt2Group) prompt2Group.style.display = "none";
                negPromptGroup.style.display = "none";
                cfgGroup.style.display = "none";
                numImagesGroup.style.display = "none";
                guidanceGroup.style.display = "block";
                if (fpsGroup) fpsGroup.style.display = "none";
                if (seedLabel) seedLabel.innerText = "Benchmark Seed";
                runBtn.innerText = "🚀 Benchmark All 24 Models (512×768)";
                if (sweepBanner) sweepBanner.style.display = "none";
                if (slerpBanner) slerpBanner.style.display = "none";
                checkExistingAllModels();
            }
        }

        async function runBatchGenerator() {
            let promptVal = document.getElementById("batch_prompt").value.trim();
            if (!promptVal) {
                alert("Please enter a prompt for the batch generator.");
                return;
            }

            let runBtn = document.getElementById("batchRunBtn");
            let stopBtn = document.getElementById("batchStopBtn");
            let consoleEl = document.getElementById("batchConsole");
            let statusPill = document.getElementById("batchStatusPill");

            runBtn.disabled = true;
            stopBtn.style.display = "inline-flex";
            statusPill.className = "batch-badge running";
            statusPill.innerText = "RUNNING";
            consoleEl.innerText = `[*] Starting ${currentBatchTool} batch process...\n[*] Enforcing 4 CPU threads and 512x768 output resolution...\n`;

            let vBox = document.getElementById("batchVideoPreviewContainer");
            if (vBox) vBox.style.display = "none";

            let payload = {
                tool: currentBatchTool,
                prompt: promptVal,
                prompt2: document.getElementById("batch_prompt2") ? document.getElementById("batch_prompt2").value.trim() : "",
                fps: document.getElementById("batch_fps") ? parseInt(document.getElementById("batch_fps").value) : 10,
                model: document.getElementById("batch_model") ? document.getElementById("batch_model").value : "",
                vae: document.getElementById("batch_vae") ? document.getElementById("batch_vae").value : "",
                lora: document.getElementById("batch_lora") ? document.getElementById("batch_lora").value : "",
                lora_scale: parseFloat(document.getElementById("batch_lora_scale").value),
                seed: parseInt(document.getElementById("batch_seed").value),
                steps: parseInt(document.getElementById("batch_steps").value),
                guidance: parseFloat(document.getElementById("batch_guidance").value),
                num_images: parseInt(document.getElementById("batch_num_images").value),
                cfg_start: parseFloat(document.getElementById("batch_cfg_start").value),
                cfg_step: parseFloat(document.getElementById("batch_cfg_step").value),
                negative_prompt: document.getElementById("batch_negative_prompt") ? document.getElementById("batch_negative_prompt").value : ""
            };

            try {
                let resp = await fetch("/run_batch_generator", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(payload)
                });
                let res;
                const ct = resp.headers.get("content-type");
                if (ct && ct.includes("application/json")) {
                    res = await resp.json();
                } else {
                    const text = await resp.text();
                    throw new Error(`HTTP ${resp.status}: ${text.slice(0, 150)}`);
                }
                if (res.success) {
                    currentBatchTaskId = res.task_id;
                    batchStartTime = Date.now();
                    consoleEl.innerText += `[*] Process spawned (Task ID: ${currentBatchTaskId})\n`;
                    if (typeof setTelemetryGenerating === 'function') setTelemetryGenerating(true);
                    if (window.setSystemPollSpeed) window.setSystemPollSpeed(1000);
                    if (window.pollSystemStatus) window.pollSystemStatus();
                    if (batchPollInterval) clearInterval(batchPollInterval);
                    batchPollInterval = setInterval(pollBatchStatus, 1500);
                } else {
                    consoleEl.innerText += `[!] Error starting task: ${res.error}\n`;
                    runBtn.disabled = false;
                    stopBtn.style.display = "none";
                    statusPill.className = "batch-badge stopped";
                    statusPill.innerText = "ERROR";
                    if (typeof setTelemetryGenerating === 'function') setTelemetryGenerating(false);
                    if (window.setSystemPollSpeed) window.setSystemPollSpeed(3500);
                }
            } catch (err) {
                consoleEl.innerText += `[!] Network exception: ${err}\n`;
                runBtn.disabled = false;
                stopBtn.style.display = "none";
                statusPill.className = "batch-badge stopped";
                statusPill.innerText = "ERROR";
                if (typeof setTelemetryGenerating === 'function') setTelemetryGenerating(false);
                if (window.setSystemPollSpeed) window.setSystemPollSpeed(3500);
            }
        }

        async function pollBatchStatus() {
            if (!currentBatchTaskId) return;
            try {
                let resp = await fetch(`/batch_status/${currentBatchTaskId}`);
                if (!resp.ok) return;
                let data = await resp.json();

                let consoleEl = document.getElementById("batchConsole");
                if (data.recent_log) {
                    consoleEl.innerText = data.recent_log;
                    consoleEl.scrollTop = consoleEl.scrollHeight;
                }

                if (batchStartTime) {
                    let elapsed = ((Date.now() - batchStartTime) / 1000).toFixed(1);
                    document.getElementById("batchTimer").innerText = elapsed + "s";
                }
                document.getElementById("batchImageCount").innerText = data.image_count || 0;

                if (data.images && data.images.length > 0) {
                    renderBatchGallery(data.images);

                    // Update Active Frame Preview Card
                    let latest = data.latest_image || data.images[data.images.length - 1];
                    if (latest) {
                        let pCard = document.getElementById("batchPreviewCard");
                        let pImg = document.getElementById("batchPreviewImg");
                        let pLink = document.getElementById("batchPreviewLink");
                        let pFile = document.getElementById("batchPreviewFilename");
                        let pCount = document.getElementById("batchPreviewCount");
                        let pMeta = document.getElementById("batchPreviewMeta");
                        let pDl = document.getElementById("batchPreviewDownloadBtn");

                        if (pCard) pCard.style.display = "block";
                        if (pImg) pImg.src = latest.path;
                        if (pLink) pLink.href = latest.path;
                        if (pFile) pFile.innerText = latest.filename || latest.path.split('/').pop();
                        if (pCount) pCount.innerText = `${data.image_count || data.images.length} frames generated`;
                        if (pMeta) pMeta.innerText = "Latest: " + (latest.filename || "");
                        if (pDl) {
                            pDl.href = latest.path;
                            pDl.setAttribute("download", latest.filename || "latest_frame.png");
                        }
                    }
                }

                if (data.video_url) {
                    let vBox = document.getElementById("batchVideoPreviewContainer");
                    let vPlayer = document.getElementById("batchVideoPlayer");
                    let vLink = document.getElementById("batchVideoDownloadLink");
                    let vTitle = document.getElementById("batchVideoTitle");
                    if (vBox && vPlayer) {
                        vBox.style.display = "block";
                        if (vTitle) {
                            let fname = data.video_url.split('/').pop();
                            vTitle.innerText = "🎬 COMPILED VIDEO (" + fname + ")";
                        }
                        if (!vPlayer.src || !vPlayer.src.includes(data.video_url)) {
                            vPlayer.src = data.video_url + "?t=" + Date.now();
                        }
                        if (vLink) vLink.href = data.video_url;
                    }
                }

                if (!data.running) {
                    clearInterval(batchPollInterval);
                    batchPollInterval = null;
                    if (typeof setTelemetryGenerating === 'function') setTelemetryGenerating(false);
                    if (window.setSystemPollSpeed) window.setSystemPollSpeed(3500);
                    document.getElementById("batchRunBtn").disabled = false;
                    document.getElementById("batchStopBtn").style.display = "none";
                    let statusPill = document.getElementById("batchStatusPill");
                    if (data.status === "finished") {
                        statusPill.className = "batch-badge finished";
                        statusPill.innerText = "COMPLETED";
                    } else if (data.status === "stopped") {
                        statusPill.className = "batch-badge stopped";
                        statusPill.innerText = "STOPPED";
                    } else {
                        statusPill.className = "batch-badge stopped";
                        statusPill.innerText = data.status || "EXITED";
                    }
                }
            } catch (err) {
                console.error("Batch polling error:", err);
            }
        }

        async function stopBatch() {
            if (!currentBatchTaskId) return;
            try {
                let resp = await fetch(`/stop_batch/${currentBatchTaskId}`, { method: "POST" });
                let data = await resp.json();
                let consoleEl = document.getElementById("batchConsole");
                consoleEl.innerText += `\n[*] Stop signal sent: ${data.message || data.error}\n`;
                document.getElementById("batchStopBtn").style.display = "none";
                if (typeof setTelemetryGenerating === 'function') setTelemetryGenerating(false);
                if (window.setSystemPollSpeed) window.setSystemPollSpeed(3500);
            } catch (err) {
                console.error("Stop batch error:", err);
            }
        }

        function clearBatchView() {
            document.getElementById("batchConsole").innerText = "Console cleared.";
        }

        function renderBatchGallery(images) {
            let container = document.getElementById("batchGallery");
            let emptyEl = document.getElementById("batchEmptyGallery");
            if (!images || images.length === 0) {
                emptyEl.style.display = "block";
                container.innerHTML = "";
                return;
            }
            emptyEl.style.display = "none";

            // If images have image_id, sort sequentially by image_id
            if (images.length > 0 && images[0].image_id !== undefined) {
                images.sort((a, b) => (a.image_id || 0) - (b.image_id || 0));
            } else {
                images.sort((a, b) => {
                    let fa = a.filename || a.path || "";
                    let fb = b.filename || b.path || "";
                    return fa.localeCompare(fb, undefined, {numeric: true, sensitivity: 'base'});
                });
            }

            let html = "";
            images.forEach((img, idx) => {
                let name = img.filename || `frame_${idx}.png`;
                let displayTitle = img.model ? `#${img.image_id || idx+1}: ${img.model.replace('.safetensors', '')}` : name;
                html += `
                <div class="batch-card">
                    <a href="${img.path}" target="_blank" title="Click to view full 512x768 resolution">
                        <img src="${img.path}" loading="lazy" alt="${name}">
                    </a>
                    <div class="batch-card-info">
                        <div style="font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${displayTitle}">${displayTitle}</div>
                        <div style="display: flex; gap: 4px; margin-top: 4px;">
                            <button type="button" class="btn-action" style="padding: 2px 6px; font-size: 0.65rem; flex: 1;" onclick="sendBatchImageToImg2Img('${img.path}')">🔁 Img2Img</button>
                            <a href="${img.path}" download class="btn-action" style="padding: 2px 6px; font-size: 0.65rem; text-decoration: none;" title="Download PNG">⬇️</a>
                        </div>
                    </div>
                </div>
                `;
            });
            container.innerHTML = html;
        }

        function sendLatestBatchToImg2Img() {
            let pImg = document.getElementById("batchPreviewImg");
            if (pImg && pImg.src) {
                sendBatchImageToImg2Img(pImg.src);
            }
        }

        function sendBatchImageToImg2Img(imgPath) {
            initImageData = imgPath;
            document.getElementById("initImagePreview").src = initImageData;
            document.getElementById("initImagePreviewContainer").style.display = "block";
            setMode("img2img");
            showStatus("Loaded " + imgPath.split('/').pop() + " into Image-to-Image mode!", "success");
        }

        function handleInitImageUpload(input) {
            if (input.files && input.files[0]) {
                let reader = new FileReader();
                reader.onload = function(e) {
                    initImageData = e.target.result;
                    document.getElementById("initImagePreview").src = initImageData;
                    document.getElementById("initImagePreviewContainer").style.display = "block";
                    showStatus("Loaded source image for Img2Img", "success");
                };
                reader.readAsDataURL(input.files[0]);
            }
        }

        function useLastGeneratedImage() {
            let rendered = document.getElementById("image").src;
            if (rendered && !rendered.endsWith("/#") && rendered !== window.location.href) {
                initImageData = rendered;
                document.getElementById("initImagePreview").src = initImageData;
                document.getElementById("initImagePreviewContainer").style.display = "block";
                showStatus("Loaded last generated image into Img2Img!", "success");
            } else {
                showStatus("No generated image available to use yet.", "error");
            }
        }

        function sendOutputToImg2Img() {
            let rendered = document.getElementById("image").src;
            if (rendered) {
                initImageData = rendered;
                document.getElementById("initImagePreview").src = initImageData;
                document.getElementById("initImagePreviewContainer").style.display = "block";
                setMode("img2img");
                showStatus("Sent rendered image to Image-to-Image mode!", "success");
            }
        }

        // Initialize lists
        async function loadModelsAndLoras() {
            try {
                let res = await fetch("/models");
                let data = await res.json();
                
                // Populate models
                let selectModel = document.getElementById("model");
                let batchSelectModel = document.getElementById("batch_model");
                selectModel.innerHTML = "";
                if (batchSelectModel) batchSelectModel.innerHTML = "";
                
                if (data.models && data.models.length > 0) {
                    data.models.forEach(m => {
                        let opt = document.createElement("option");
                        opt.value = m;
                        opt.textContent = m;
                        selectModel.appendChild(opt);

                        if (batchSelectModel) {
                            let optB = document.createElement("option");
                            optB.value = m;
                            optB.textContent = m;
                            batchSelectModel.appendChild(optB);
                        }
                    });
                } else {
                    selectModel.innerHTML = '<option value="" disabled selected>No models available</option>';
                    if (batchSelectModel) batchSelectModel.innerHTML = '<option value="" disabled selected>No models available</option>';
                }

                // Populate VAEs
                let selectVae = document.getElementById("vae");
                let batchSelectVae = document.getElementById("batch_vae");
                if (selectVae) {
                    selectVae.innerHTML = '<option value="">Default (Baked into Model)</option>';
                    if (batchSelectVae) batchSelectVae.innerHTML = '<option value="">Default (Baked into Model)</option>';
                    if (data.vaes && data.vaes.length > 0) {
                        data.vaes.forEach(v => {
                            let opt = document.createElement("option");
                            opt.value = v;
                            opt.textContent = v;
                            selectVae.appendChild(opt);

                            if (batchSelectVae) {
                                let optB = document.createElement("option");
                                optB.value = v;
                                optB.textContent = v;
                                batchSelectVae.appendChild(optB);
                            }
                        });
                    }
                }

                // Populate LoRAs
                let lora1 = document.getElementById("lora1");
                let lora2 = document.getElementById("lora2");
                let batchLora = document.getElementById("batch_lora");
                
                lora1.innerHTML = '<option value="">None (Disabled)</option>';
                lora2.innerHTML = '<option value="">None (Disabled)</option>';
                if (batchLora) batchLora.innerHTML = '<option value="">None (Disabled)</option>';
                
                if (data.loras && data.loras.length > 0) {
                    data.loras.forEach(l => {
                        let opt1 = document.createElement("option");
                        opt1.value = l;
                        opt1.textContent = l;
                        lora1.appendChild(opt1);
                        
                        let opt2 = document.createElement("option");
                        opt2.value = l;
                        opt2.textContent = l;
                        lora2.appendChild(opt2);

                        if (batchLora) {
                            let optB = document.createElement("option");
                            optB.value = l;
                            optB.textContent = l;
                            batchLora.appendChild(optB);
                        }
                    });
                }
            } catch (err) {
                showStatus("Failed to communicate with local model directory", "error");
            }
        }

        let isGenerating = false;
        let genPeakRam = 0;
        let genPeakCpu = 0;

        function setTelemetryGenerating(active) {
            isGenerating = active;
            const badge = document.getElementById('teleBadge');
            const note = document.getElementById('teleSurgeNote');
            if (active) {
                if (badge) {
                    badge.textContent = "DIFFUSING...";
                    badge.className = "telemetry-badge active";
                }
                genPeakRam = 0;
                genPeakCpu = 0;
                if (note) note.textContent = "⚡ Diffusion active • Monitoring CPU & RAM surge...";
            } else {
                if (badge) {
                    badge.textContent = "STANDBY";
                    badge.className = "telemetry-badge idle";
                }
                if (note && genPeakRam > 0) {
                    note.textContent = `Completed! Peak RAM: ${genPeakRam} GB | Peak CPU: ${genPeakCpu}%`;
                }
            }
        }

        window.addEventListener('systemStatusUpdate', function(e) {
            const d = e.detail;
            if (!d) return;

            // CPU Usage
            const cpuTxt = document.getElementById('teleCpuText');
            const cpuBar = document.getElementById('teleCpuBar');
            if (cpuTxt) cpuTxt.textContent = `${d.cpu_percent}%`;
            if (cpuBar) {
                cpuBar.style.width = `${Math.min(d.cpu_percent, 100)}%`;
                cpuBar.style.backgroundColor = (window.getLoadColor ? window.getLoadColor(d.cpu_percent) : '#10b981');
            }

            // RAM Memory
            const ramTxt = document.getElementById('teleRamText');
            const ramBar = document.getElementById('teleRamBar');
            if (ramTxt) ramTxt.textContent = `${d.ram_used_gb} / ${d.ram_total_gb} GB (${d.ram_percent}%)`;
            if (ramBar) {
                ramBar.style.width = `${Math.min(d.ram_percent, 100)}%`;
                ramBar.style.backgroundColor = (window.getLoadColor ? window.getLoadColor(d.ram_percent) : '#10b981');
            }

            // Status Banner pill
            const statusTele = document.getElementById('statusSysTelemetry');
            if (statusTele) {
                statusTele.textContent = `CPU: ${d.cpu_percent}% | RAM: ${d.ram_used_gb}GB (${d.ram_percent}%)`;
            }

            // Track peaks during active generation
            if (isGenerating) {
                if (d.ram_used_gb > genPeakRam) genPeakRam = d.ram_used_gb;
                if (d.cpu_percent > genPeakCpu) genPeakCpu = d.cpu_percent;
                const note = document.getElementById('teleSurgeNote');
                if (note) {
                    note.textContent = `⚡ Surging: RAM ${d.ram_used_gb} GB (Peak ${genPeakRam} GB) | CPU ${d.cpu_percent}%`;
                }
            }
        });

        function showStatus(message, type) {
            let box = document.getElementById("statusBox");
            box.className = "status-container " + type;
            box.style.display = "flex";
            
            if (type === "generating") {
                box.innerHTML = `<div class="spinner"></div><span>${message}</span> <span class="elapsed" id="timer">00.0s</span><span id="statusSysTelemetry" style="font-size:0.75rem; background:rgba(0,0,0,0.35); padding:2px 8px; border-radius:4px; margin-left:8px; border:1px solid rgba(255,255,255,0.1); color:#38bdf8; font-family:monospace;">CPU: ... | RAM: ...</span>`;
            } else {
                box.innerHTML = `<span>${message}</span>`;
            }
        }

        function hideStatus() {
            document.getElementById("statusBox").style.display = "none";
        }

        function startTimer() {
            startTimestamp = Date.now();
            let timerEl = document.getElementById("timer");
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(() => {
                let diff = (Date.now() - startTimestamp) / 1000;
                if (timerEl) {
                    timerEl.innerText = diff.toFixed(1) + "s";
                }
            }, 100);
        }

        function stopTimer() {
            if (timerInterval) {
                clearInterval(timerInterval);
                timerInterval = null;
            }
        }

        async function generateImage() {
            let btn = document.getElementById("generateBtn");
            let prompt = document.getElementById("prompt").value.trim();
            if (!prompt) {
                showStatus("Please write a prompt.", "error");
                return;
            }

            if (currentMode === "img2img" && !initImageData) {
                showStatus("Please choose an initial image file or click 'Use Last Generated' for Img2Img.", "error");
                return;
            }

            btn.disabled = true;
            document.getElementById("imageWrapper").style.display = "none";
            document.getElementById("emptyState").style.display = "flex";
            showStatus(currentMode === "img2img" ? "Running Image-to-Image transformation..." : "Running Text-to-Image synthesis...", "generating");
            startTimer();
            setTelemetryGenerating(true);
            if (window.setSystemPollSpeed) window.setSystemPollSpeed(1000);
            if (window.pollSystemStatus) window.pollSystemStatus();

            let payload = {
                mode: currentMode,
                init_image: currentMode === "img2img" ? initImageData : null,
                strength: currentMode === "img2img" ? parseFloat(document.getElementById("strength").value) : 0.65,
                model: document.getElementById("model").value,
                vae: document.getElementById("vae") ? document.getElementById("vae").value : "",
                prompt: prompt,
                steps: parseInt(document.getElementById("steps").value),
                guidance_scale: parseFloat(document.getElementById("guidance").value),
                width: parseInt(document.getElementById("width").value),
                height: parseInt(document.getElementById("height").value),
                seed: parseInt(document.getElementById("seed").value),
                lora1: document.getElementById("lora1").value,
                lora1_weight: parseFloat(document.getElementById("lora1_weight").value),
                lora2: document.getElementById("lora2").value,
                lora2_weight: parseFloat(document.getElementById("lora2_weight").value)
            };

            try {
                let response = await fetch("/generate_image", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(payload)
                });
                
                let data;
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                    data = await response.json();
                } else {
                    const text = await response.text();
                    throw new Error(`HTTP ${response.status}: ${text.slice(0, 150)}`);
                }
                stopTimer();
                btn.disabled = false;
                setTelemetryGenerating(false);
                if (window.setSystemPollSpeed) window.setSystemPollSpeed(3500);
                
                if (data.success) {
                    let totalDuration = ((Date.now() - startTimestamp) / 1000).toFixed(1);
                    showStatus(`Synthesized (${payload.mode}) successfully in ${totalDuration}s.`, "success");
                    
                    document.getElementById("emptyState").style.display = "none";
                    let wrapper = document.getElementById("imageWrapper");
                    wrapper.style.display = "flex";
                    
                    document.getElementById("image").src = data.image_url;
                    
                    let meta = document.getElementById("imageMeta");
                    let fileLink = "";
                    if (data.saved_path) {
                        let webUrl = "/" + data.saved_path;
                        fileLink = ` | Saved File: <a href="${webUrl}" target="_blank" class="link-glow">${data.saved_path}</a>`;
                    }
                    
                    let loraApplied = "";
                    if (payload.lora1) {
                        loraApplied += ` | LoRA 1: ${payload.lora1.slice(0, 15)}... (${payload.lora1_weight})`;
                    }
                    if (payload.lora2) {
                        loraApplied += ` | LoRA 2: ${payload.lora2.slice(0, 15)}... (${payload.lora2_weight})`;
                    }
                    let vaeApplied = payload.vae ? ` | VAE: ${payload.vae.slice(0, 20)}...` : "";
                    let modeBadge = `<span style="background: rgba(99,102,241,0.25); color:#a5b4fc; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-right: 6px;">${payload.mode.toUpperCase()}</span>`;
                    
                    meta.innerHTML = `
                        <div style="font-weight:600; color:white; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${prompt}">${modeBadge}${prompt}</div>
                        <div style="margin-top:0.25rem; font-size:0.75rem;">Seed: ${data.seed || payload.seed} | CFG: ${payload.guidance_scale} | Steps: ${payload.steps} | Dimensions: ${payload.width}x${payload.height}${vaeApplied}${loraApplied}${fileLink}</div>
                    `;
                } else {
                    showStatus("Error generating image: " + data.error, "error");
                }
            } catch (err) {
                stopTimer();
                btn.disabled = false;
                setTelemetryGenerating(false);
                if (window.setSystemPollSpeed) window.setSystemPollSpeed(3500);
                showStatus("Network connection error to backend: " + err, "error");
            }
        }

        let existingSweepData = null;

        async function checkExistingSweep() {
            try {
                let resp = await fetch("/api/cfg_sweep_status");
                let res = await resp.json();
                if (res.success && res.exists && res.seed) {
                    existingSweepData = res;
                    let banner = document.getElementById("activeSweepBanner");
                    if (banner) {
                        document.getElementById("sweepSeedVal").innerText = res.seed;
                        document.getElementById("sweepCountVal").innerText = `${res.completed_count} images`;
                        document.getElementById("sweepLastFileVal").innerText = res.last_completed_file || "None";
                        document.getElementById("sweepLastCfgVal").innerText = res.last_completed_cfg != null ? res.last_completed_cfg : "N/A";
                        let nextCfg = res.next_suggested_cfg || 1.0;
                        document.getElementById("sweepNextCfgBtn").innerText = nextCfg;
                        banner.style.display = "block";
                    }
                }
            } catch (e) {
                console.error("Could not check existing sweep:", e);
            }
        }

        function applyExistingSweep() {
            if (!existingSweepData) return;
            let d = existingSweepData;
            if (d.prompt) document.getElementById("batch_prompt").value = d.prompt;
            if (d.seed) document.getElementById("batch_seed").value = d.seed;
            if (d.next_suggested_cfg) document.getElementById("batch_cfg_start").value = d.next_suggested_cfg;
            document.getElementById("batch_cfg_step").value = 0.01;
            let remaining = Math.max(10, 200 - (d.completed_count || 0));
            document.getElementById("batch_num_images").value = remaining;
            if (d.model) {
                let modelSel = document.getElementById("batch_model");
                for (let i = 0; i < modelSel.options.length; i++) {
                    if (modelSel.options[i].value.includes(d.model) || d.model.includes(modelSel.options[i].value)) {
                        modelSel.selectedIndex = i;
                        break;
                    }
                }
            }
            showStatus(`Loaded sweep parameters for Seed ${d.seed}! Ready to resume from CFG ${d.next_suggested_cfg}.`, "success");
        }

        let existingSlerpData = null;

        async function checkExistingSlerp() {
            try {
                let resp = await fetch("/api/slerp_status");
                let res = await resp.json();
                if (res.success && res.exists && res.seed) {
                    existingSlerpData = res;
                    let banner = document.getElementById("activeSlerpBanner");
                    if (banner) {
                        document.getElementById("slerpSeedVal").innerText = res.seed;
                        document.getElementById("slerpCountVal").innerText = `${res.completed_count} / ${res.total_frames || 30} frames`;
                        document.getElementById("slerpLastFileVal").innerText = res.last_completed_frame || "None";
                        document.getElementById("slerpProgressVal").innerText = `${res.progress_pct || 0}%`;
                        let nextF = (res.last_completed_index != null && res.last_completed_index >= 0) ? (res.last_completed_index + 1) : 0;
                        document.getElementById("slerpNextFrameBtn").innerText = nextF;
                        banner.style.display = "block";
                    }
                }
            } catch (e) {
                console.error("Could not check existing slerp:", e);
            }
        }

        function applyExistingSlerp() {
            if (!existingSlerpData) return;
            let d = existingSlerpData;
            if (d.prompt1) document.getElementById("batch_prompt").value = d.prompt1;
            if (d.prompt2) document.getElementById("batch_prompt2").value = d.prompt2;
            if (d.negative_prompt) document.getElementById("batch_negative_prompt").value = d.negative_prompt;
            if (d.seed) document.getElementById("batch_seed").value = d.seed;
            if (d.total_frames) document.getElementById("batch_num_images").value = d.total_frames;
            if (d.fps) document.getElementById("batch_fps").value = d.fps;
            if (d.steps) document.getElementById("batch_steps").value = d.steps;
            if (d.guidance) document.getElementById("batch_guidance").value = d.guidance;
            if (d.model) {
                let modelSel = document.getElementById("batch_model");
                for (let i = 0; i < modelSel.options.length; i++) {
                    if (modelSel.options[i].value.includes(d.model) || d.model.includes(modelSel.options[i].value)) {
                        modelSel.selectedIndex = i;
                        break;
                    }
                }
            }
            showStatus(`Loaded SLERP parameters for Seed ${d.seed}! Ready to resume from frame ${d.next_suggested_frame || 0}.`, "success");
        }

        async function checkActiveBatchTask() {
            try {
                let resp = await fetch("/api/active_batch");
                if (resp.ok) {
                    let d = await resp.json();
                    if (d.running && d.task_id) {
                        currentBatchTaskId = d.task_id;
                        currentBatchTool = d.tool || "slerp";
                        setMode("batch");
                        setBatchTool(currentBatchTool);
                        let runBtn = document.getElementById("batchRunBtn");
                        let stopBtn = document.getElementById("batchStopBtn");
                        let statusPill = document.getElementById("batchStatusPill");
                        if (runBtn) runBtn.disabled = true;
                        if (stopBtn) stopBtn.style.display = "inline-flex";
                        if (statusPill) {
                            statusPill.className = "batch-badge running";
                            statusPill.innerText = "RUNNING";
                        }
                        if (batchPollInterval) clearInterval(batchPollInterval);
                        batchPollInterval = setInterval(pollBatchStatus, 1500);
                        pollBatchStatus();
                    }
                }
            } catch (e) {}
        }

        let existingAllModelsData = null;

        async function checkExistingAllModels() {
            try {
                let resp = await fetch("/api/all_models_status");
                let res = await resp.json();
                if (res.success && res.exists && res.seed) {
                    existingAllModelsData = res;
                    let banner = document.getElementById("activeAllModelsBanner");
                    if (banner) {
                        document.getElementById("allModelsSeedVal").innerText = res.seed;
                        document.getElementById("allModelsCountVal").innerText = `${res.completed_count} / ${res.total_models || 24} models`;
                        document.getElementById("allModelsLastModelVal").innerText = res.last_completed_model || "None";
                        document.getElementById("allModelsProgressVal").innerText = `${res.progress_pct || 0}%`;
                        banner.style.display = "block";
                    }
                    // Automatically fill prompt and seed so user just has to press the button
                    if (res.prompt) document.getElementById("batch_prompt").value = res.prompt;
                    if (res.seed) document.getElementById("batch_seed").value = res.seed;
                }
            } catch (e) {
                console.error("Could not check existing all_models:", e);
            }
        }

        function applyExistingAllModels() {
            setMode('batch');
            setBatchTool('all_models');
            if (existingAllModelsData) {
                let d = existingAllModelsData;
                if (d.prompt) document.getElementById("batch_prompt").value = d.prompt;
                if (d.seed) document.getElementById("batch_seed").value = d.seed;
            }
            showStatus("Resuming benchmark for Seed " + (existingAllModelsData ? existingAllModelsData.seed : 3400) + "...", "success");
            runBatchGenerator();
        }

        window.onload = function() {
            loadModelsAndLoras();
            let urlParams = new URLSearchParams(window.location.search);
            let toolParam = urlParams.get('tool');
            if (toolParam) {
                setMode('batch');
                setBatchTool(toolParam);
            } else {
                setBatchTool("cfg_sweep");
            }
            checkExistingSweep();
            checkExistingSlerp();
            checkExistingAllModels();
            checkActiveBatchTask();
        };
    </script>

</body>
</html>
"""
GALLERY="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Gallery</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #2c3e50;
            color: #ecf0f1;
            text-align: center;
        }
        .gallery {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
        }
        .gallery-item {
            margin: 20px;
        }
        .gallery-item img {
            max-width: 200px;
            max-height: 240px;
            display: block;
            margin: 10px auto;
        }
        .sp {
            display: block;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin-top: 10px;
            max-width: 300px;
            white-space: pre-wrap;
            word-wrap: break-word;
            
        }

        .spi {
            display: block;
            text-align: center;
            color:yellow;
            font-size: 18px;
            font-weight: bold;
            margin-top: 10px;
            max-width: 300px;
            white-space: pre-wrap;
            word-wrap: break-word;
            
        }        
        a {
            color: #3498db;
            font-size: 3em;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>Image Gallery / gallery.html </h1>
    <!-- changed index to stable_diffusion -->
    <a href="{{ url_for('home2') }}">Home2</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="{{ url_for('stable_diffusion') }}">Home</a>
    <div class="gallery">
        {% for item in gallery_data %}
        <div class="gallery-item">
            <h3 class='spi' >Directory: {{ item.directory }}</h3>
            {% for image in item.images %}
            <img src="{{ image }}" alt="Image">
            <p class='sp'>{{ image }}</p>
            {% endfor %}<hr>
        </div><hr>
        {% endfor %}
    </div>
</body>
</html>
"""
STATIC_IMAGE_DIR = os.path.join(BASE_DIR, "static", "novel_images")



@app.route("/stable_diffusion")
def stable_diffusion():
    return render_template_string(HTMLD)
# get a list of images in STATIC_IMAGE_DIR
def resource_images():
    images = glob.glob(os.path.join(STATIC_IMAGE_DIR, "*.jpg"))
    images += glob.glob(os.path.join(STATIC_IMAGE_DIR, "*.png"))
    return images
'''
@app.route("/gallery")
def gallery():
    remove_gallery_images()
    scan_data = load_scan_data()
    if not scan_data:
        print("No scan data found. Scanning directories.")
        scan_data = scan_directories()
        save_scan_data(scan_data)
        gallery_data = select_random_images(scan_data)
        static_gallery_data = copy_images_to_static(gallery_data)
    else:
        static_gallery_data = load_static_gallery_data()
        if not static_gallery_data:
            print("No static gallery data found. Creating new static gallery data.")
            gallery_data = select_random_images(scan_data)
            static_gallery_data = copy_images_to_static(gallery_data)
            save_static_gallery_data(static_gallery_data)
    return render_template("gallery.html", gallery_data=resource_images())
'''

@app.route("/sdgallery")
def sdgallery():
    return render_template_string(GALLERY, gallery_data=resource_images())

def resolve_model_path(model_name):
    if not model_name:
        return None
    if os.path.isabs(model_name) and os.path.exists(model_name):
        return model_name
    for c_dir in CHECKPOINTS_DIRS + [os.path.join(BASE_DIR, "models")]:
        candidate = os.path.join(c_dir, model_name)
        if os.path.exists(candidate):
            return candidate
    candidate2 = os.path.join(COMFY_MODELS_DIR, model_name)
    if os.path.exists(candidate2):
        return candidate2
    return model_name

def resolve_vae_path(vae_name):
    if not vae_name:
        return None
    if os.path.isabs(vae_name) and os.path.exists(vae_name):
        return vae_name
    for v_dir in VAE_DIRS:
        candidate = os.path.join(v_dir, vae_name)
        if os.path.exists(candidate):
            return candidate
    return vae_name

def resolve_lora_path(lora_name):
    if not lora_name:
        return None
    if os.path.isabs(lora_name) and os.path.exists(lora_name):
        return lora_name
    for l_dir in LORAS_DIRS:
        candidate = os.path.join(l_dir, lora_name)
        if os.path.exists(candidate):
            return candidate
    return lora_name

@app.route("/models", methods=["GET"])
def models():
    # Return live scanned Comfy-UI models, loras, and vaes
    return jsonify({
        "models": get_live_models(),
        "loras": get_live_loras(),
        "vaes": get_live_vaes()
    })

@app.route("/api/cfg_sweep_status", methods=["GET"])
def api_cfg_sweep_status():
    cfg_file = os.path.join(BASE_DIR, "static", "novel_images", "cfg.json")
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r") as f:
                data = json.load(f)
            runs = data.get("runs", [])
            last_run = runs[-1] if runs else {}
            seed = last_run.get("seed", data.get("seed", 3360))
            prompt = last_run.get("prompt", data.get("prompt", ""))
            model = last_run.get("model", data.get("model", ""))
            last_cfg = data.get("last_completed_cfg", last_run.get("guidance_scale", 1.0))
            last_file = data.get("last_completed_file", last_run.get("file", ""))
            existing_seed_files = sorted(glob.glob(os.path.join(BASE_DIR, "static", "novel_images", f"{seed}_*.png")), reverse=True)
            try:
                next_cfg = round(float(last_cfg) + 0.001, 3)
            except Exception:
                next_cfg = 1.0
            return jsonify({
                "success": True,
                "exists": True,
                "seed": seed,
                "prompt": prompt,
                "model": model,
                "last_completed_cfg": last_cfg,
                "last_completed_file": last_file,
                "next_suggested_cfg": next_cfg,
                "completed_count": len(existing_seed_files),
                "total_runs": len(runs)
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": True, "exists": False})

@app.route("/api/novel_images", methods=["GET"])
def api_novel_images():
    """Returns a list of all images in static/novel_images, with optional prefix/seed filter."""
    img_dir = os.path.join(BASE_DIR, "static", "novel_images")
    filter_prefix = request.args.get("prefix", "").strip()
    sort_by = request.args.get("sort", "name")

    if not os.path.exists(img_dir):
        return jsonify({"success": True, "count": 0, "images": []})

    valid_exts = (".png", ".jpg", ".jpeg", ".webp")
    files = [f for f in os.listdir(img_dir) if f.lower().endswith(valid_exts) and not f.startswith(".")]

    if filter_prefix:
        files = [f for f in files if filter_prefix.lower() in f.lower()]

    if sort_by == "time":
        files.sort(key=lambda x: os.path.getmtime(os.path.join(img_dir, x)))
    else:
        def natural_key(text):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]
        files.sort(key=natural_key)

    images = []
    for idx, f in enumerate(files):
        images.append({
            "index": idx,
            "filename": f,
            "path": f"/static/novel_images/{f}",
            "mtime": os.path.getmtime(os.path.join(img_dir, f))
        })

    return jsonify({
        "success": True,
        "count": len(images),
        "images": images
    })

@app.route("/flipbook")
def flipbook_viewer_route():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "live_slerp.html")

@app.route("/api/slerp_status", methods=["GET"])
def api_slerp_status():
    slerp_file = os.path.join(BASE_DIR, "static", "novel_images", "slerp.json")
    if not os.path.exists(slerp_file):
        slerp_file = os.path.join(BASE_DIR, "static", "temp_exp", "slerp.json")

    if os.path.exists(slerp_file):
        try:
            with open(slerp_file, "r") as f:
                data = json.load(f)
            frames = data.get("frames", [])
            seed = data.get("seed", 3360)
            existing_frames = sorted(glob.glob(os.path.join(BASE_DIR, "static", "novel_images", f"slerp_{seed}_*.*")))
            last_frame = data.get("last_completed_frame", frames[-1]["file"] if frames else "")
            last_index = data.get("last_completed_index", frames[-1]["index"] if frames else -1)
            last_t = data.get("last_completed_t", frames[-1]["t"] if frames else 0.0)
            next_index = (last_index + 1) if (last_index is not None and last_index >= 0) else 0
            total_frames = data.get("total_frames", 30)
            pct = round((len(frames) / max(1, total_frames)) * 100, 1)

            return jsonify({
                "success": True,
                "exists": True,
                "seed": seed,
                "prompt1": data.get("prompt1", ""),
                "prompt2": data.get("prompt2", ""),
                "negative_prompt": data.get("negative_prompt", ""),
                "model": data.get("model", ""),
                "total_frames": total_frames,
                "fps": data.get("fps", 10),
                "steps": data.get("steps", 5),
                "guidance": data.get("guidance", 1.5),
                "last_completed_frame": last_frame,
                "last_completed_index": last_index,
                "last_completed_t": last_t,
                "next_suggested_frame": next_index,
                "completed_count": max(len(frames), len(existing_frames)),
                "progress_pct": pct,
                "video_url": data.get("video_url")
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    # Fallback to scanning disk if slerp.json is missing
    existing_slerp_files = sorted(glob.glob(os.path.join(BASE_DIR, "static", "novel_images", "slerp_*.*")))
    if existing_slerp_files:
        try:
            latest_file = os.path.basename(existing_slerp_files[-1])
            parts = latest_file.rsplit(".", 1)[0].split("_")
            seed = int(parts[1]) if len(parts) >= 3 else 3360
            seed_files = [f for f in existing_slerp_files if f"slerp_{seed}_" in f]
            return jsonify({
                "success": True,
                "exists": True,
                "seed": seed,
                "prompt1": "",
                "prompt2": "",
                "model": "",
                "total_frames": 30,
                "last_completed_frame": latest_file,
                "completed_count": len(seed_files),
                "next_suggested_frame": len(seed_files),
                "progress_pct": round((len(seed_files) / 30.0) * 100, 1)
            })
        except Exception:
            pass

    return jsonify({"success": True, "exists": False})

@app.route("/api/all_models_status", methods=["GET"])
def api_all_models_status():
    models_file = os.path.join(BASE_DIR, "static", "novel_images", "models.json")
    if os.path.exists(models_file):
        try:
            with open(models_file, "r") as f:
                data = json.load(f)
            runs = data.get("runs", [])
            seed = data.get("seed", 3407)
            chk_dir = os.path.join(BASE_DIR, "models", "checkpoints")
            if os.path.exists(chk_dir):
                chk_files = [f for f in os.listdir(chk_dir) if f.endswith(('.safetensors', '.ckpt', '.pt'))]
                total = len(chk_files) if chk_files else 27
            else:
                total = 27
            last_file = data.get("last_completed_file", runs[-1]["file"] if runs else "")
            last_model = data.get("last_completed_model", runs[-1]["model"] if runs else "")
            pct = round((len(runs) / max(1, total)) * 100, 1)

            return jsonify({
                "success": True,
                "exists": True,
                "seed": seed,
                "prompt": data.get("prompt", ""),
                "completed_count": len(runs),
                "total_models": total,
                "last_completed_model": last_model,
                "last_completed_file": last_file,
                "progress_pct": pct,
                "is_complete": len(runs) >= total,
                "video_url": "/static/temp_exp/modelsX.mp4" if os.path.exists(os.path.join(BASE_DIR, "static", "temp_exp", "modelsX.mp4")) else None
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": True, "exists": False})

@app.route("/generate_image", methods=["POST"])
def generate_image():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "txt2img")
    user_prompt = data.get("prompt", "a beautiful landscape")
    negative_prompt = data.get("negative_prompt", "")
    steps = int(data.get("steps", 6))
    guidance_scale = float(data.get("guidance_scale", 1.5))
    width = int(data.get("width", 512))
    height = int(data.get("height", 768))
    seed = int(data.get("seed", 0))
    if seed == 0:
        seed = randint(1111111, 9999999)

    model_sel = data.get("model", "")
    vae_sel = data.get("vae", "")
    lora1_sel = data.get("lora1", "")
    lora1_weight = float(data.get("lora1_weight", 0.75))
    lora2_sel = data.get("lora2", "")
    lora2_weight = float(data.get("lora2_weight", 0.75))
    strength = float(data.get("strength", 0.65))
    init_image_data = data.get("init_image", None)

    # Use offline generate.py directly without exterior server
    if not os.path.exists("generate.py"):
        return jsonify({"success": False, "error": "generate.py script not found"}), 400

    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs("temp", exist_ok=True)

    # Handle init_image for img2img mode
    init_img_file = None
    if mode == "img2img" and init_image_data:
        if init_image_data.startswith("data:image"):
            try:
                b64_str = init_image_data.split(",", 1)[1] if "," in init_image_data else init_image_data
                img_bytes = base64.b64decode(b64_str)
                temp_path = os.path.join("temp", f"init_{int(time.time()*1000)}.png")
                with open(temp_path, "wb") as f:
                    f.write(img_bytes)
                init_img_file = temp_path
            except Exception as e:
                return jsonify({"success": False, "error": f"Failed to decode init_image: {e}"}), 400
        elif init_image_data.startswith("/") and os.path.exists(init_image_data[1:]):
            init_img_file = init_image_data[1:]
        elif os.path.exists(init_image_data):
            init_img_file = init_image_data
        else:
            return jsonify({"success": False, "error": f"init_image file not found: {init_image_data}"}), 400

    # Resolve file paths
    resolved_model = resolve_model_path(model_sel)
    resolved_vae = resolve_vae_path(vae_sel) if vae_sel else None
    resolved_lora1 = resolve_lora_path(lora1_sel) if lora1_sel else None
    resolved_lora2 = resolve_lora_path(lora2_sel) if lora2_sel else None

    # Detect python executable (prefer local Media_Studio venv with diffusers & torch)
    python_exec = sys.executable
    local_venv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
    if os.path.exists(local_venv):
        python_exec = local_venv
    elif os.path.exists("/home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/python"):
        python_exec = "/home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/python"

    cmd = [
        python_exec, "generate.py",
        "--prompt", user_prompt,
        "--mode", mode,
        "--steps", str(steps),
        "--guidance", str(guidance_scale),
        "--width", str(width),
        "--height", str(height),
        "--seed", str(seed),
        "--output_dir", SAVE_DIR,
        "--device", "auto",
        "--num_images", "1",
        "--threads", "4"
    ]

    if negative_prompt:
        cmd.extend(["--negative_prompt", negative_prompt])
    if resolved_model:
        cmd.extend(["--model", resolved_model])
    if resolved_vae:
        cmd.extend(["--vae", resolved_vae])
    if resolved_lora1:
        cmd.extend(["--lora", resolved_lora1, "--lora_scale", str(lora1_weight)])
    if resolved_lora2:
        cmd.extend(["--lora2", resolved_lora2, "--lora2_scale", str(lora2_weight)])
    if mode == "img2img" and init_img_file:
        cmd.extend(["--init_image", init_img_file, "--strength", str(strength)])

    # Limit CPU execution threads
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "4"
    env["MKL_NUM_THREADS"] = "4"
    env["OPENBLAS_NUM_THREADS"] = "4"
    env["NUMEXPR_NUM_THREADS"] = "4"
    env["VECLIB_MAXIMUM_THREADS"] = "4"

    task_id = f"sd_gen_{int(time.time()*1000)}"
    register_task(task_id, f"SD Generating ({mode} {width}x{height})")
    try:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1000, env=env)
            if res.returncode != 0:
                err_output = res.stderr.strip() or res.stdout.strip()
                ic("Offline generation error:", err_output)
                return jsonify({"success": False, "error": f"generate.py failed: {err_output}"}), 500

            files = sorted(glob.glob(os.path.join(SAVE_DIR, "*.png")), key=os.path.getmtime)
            latest = files[-1] if files else None
            rel_path = "/" + latest if latest else ""
            return jsonify({
                "success": True,
                "image_url": rel_path,
                "saved_path": latest,
                "seed": seed,
                "info": f"Generated offline via local diffusers ({mode})"
            })
        except subprocess.TimeoutExpired:
            ic("Offline generation timeout expired (500s)")
            return jsonify({"success": False, "error": "Image generation timed out after 500 seconds."}), 504
        except Exception as e:
            ic("Offline generation exception:", e)
            return jsonify({"success": False, "error": f"Offline generation exception: {e}"}), 500
    finally:
        unregister_task(task_id)

active_batch_tasks = {}

@app.route("/run_batch_generator", methods=["POST"])
def run_batch_generator():
    data = request.get_json(silent=True) or {}
    tool = data.get("tool", "cfg_sweep")
    prompt = data.get("prompt", "a beautiful alien cyborg with robotic body")
    model = data.get("model", "")
    seed = int(data.get("seed", 123456))
    if seed == 0:
        seed = randint(111111, 999999)
    steps = int(data.get("steps", 4))
    guidance = float(data.get("guidance", 1.5))
    num_images = int(data.get("num_images", 10))
    cfg_start = float(data.get("cfg_start", 1.0))
    cfg_step = float(data.get("cfg_step", 0.04))
    lora = data.get("lora", "")
    lora_scale = float(data.get("lora_scale", 0.25))
    vae = data.get("vae", "")
    negative_prompt = data.get("negative_prompt", "")

    # Detect python executable (prefer local Media_Studio venv with diffusers & torch)
    python_exec = sys.executable
    local_venv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
    if os.path.exists(local_venv):
        python_exec = local_venv
    elif os.path.exists("/home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/python"):
        python_exec = "/home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/python"

    # Resolve paths
    resolved_model = resolve_model_path(model) if model else ""
    model_filename = os.path.basename(resolved_model) if resolved_model else model

    cmd = [python_exec]
    if tool == "cfg_sweep":
        cmd.extend(["ONE_model_cfg.py", "-p", prompt, "-s", str(seed), "-n", str(num_images), "--cfg-start", str(cfg_start), "--cfg-step", str(cfg_step), "--steps", str(steps)])
        if model_filename:
            cmd.extend(["-m", model_filename])
        if lora:
            res_lora = resolve_lora_path(lora)
            if res_lora:
                cmd.extend(["--lora", res_lora, "--lora-scale", str(lora_scale)])
        if vae:
            res_vae = resolve_vae_path(vae)
            if res_vae:
                cmd.extend(["--vae", res_vae])

    elif tool == "long_prompt":
        cmd.extend(["ONEv2.py", "-p", prompt, "-s", str(seed), "--steps", str(steps), "--guidance", str(guidance)])
        if model_filename:
            cmd.extend(["-m", model_filename])
        if negative_prompt:
            cmd.extend(["--negative-prompt", negative_prompt])
        if lora:
            res_lora = resolve_lora_path(lora)
            if res_lora:
                cmd.extend(["--lora", res_lora, "--lora-scale", str(lora_scale)])
        if vae:
            res_vae = resolve_vae_path(vae)
            if res_vae:
                cmd.extend(["--vae", res_vae])

    elif tool == "seed_explorer":
        cmd.extend(["ONE_model_seeds.py", "-p", prompt, "-s", str(seed), "-n", str(num_images), "--steps", str(steps), "--guidance", str(guidance)])
        if model_filename:
            cmd.extend(["-m", model_filename])
        if lora:
            res_lora = resolve_lora_path(lora)
            if res_lora:
                cmd.extend(["--lora", res_lora, "--lora-scale", str(lora_scale)])
        if vae:
            res_vae = resolve_vae_path(vae)
            if res_vae:
                cmd.extend(["--vae", res_vae])

    elif tool == "all_models":
        models_json_path = os.path.join(SAVE_DIR, "models.json")
        if os.path.exists(models_json_path):
            try:
                with open(models_json_path, "r") as f:
                    mdata = json.load(f)
                if mdata.get("seed") and (seed == 0 or len(mdata.get("runs", [])) < 24):
                    seed = mdata["seed"]
                    if (not prompt or prompt == "Prompt" or prompt == "a beautiful alien cyborg with robotic body") and mdata.get("prompt"):
                        prompt = mdata["prompt"]
            except Exception:
                pass
        cmd.extend(["ONE_allmodels.py", "-p", prompt, "-s", str(seed), "--steps", str(steps), "--guidance", str(guidance), "--fps", "2"])
        if lora:
            res_lora = resolve_lora_path(lora)
            if res_lora:
                cmd.extend(["--lora", res_lora, "--lora-scale", str(lora_scale)])
        if vae:
            res_vae = resolve_vae_path(vae)
            if res_vae:
                cmd.extend(["--vae", res_vae])

    elif tool == "slerp":
        prompt2 = data.get("prompt2", "A futuristic cyberpunk metropolis at midnight, neon blue and magenta reflections, towering holographic skyscrapers in the pouring rain, flying futuristic spinners, cinematic lighting, ultra detailed 8k architectural concept art")
        fps = int(data.get("fps", 10))
        cmd.extend([
            "ONE_slerp.py",
            "-p1", prompt,
            "-p2", prompt2,
            "-s", str(seed),
            "-n", str(num_images),
            "--steps", str(steps),
            "--guidance", str(guidance),
            "--fps", str(fps)
        ])
        if model_filename:
            cmd.extend(["-m", model_filename])
        if negative_prompt:
            cmd.extend(["-np", negative_prompt])
        if lora:
            res_lora = resolve_lora_path(lora)
            if res_lora:
                cmd.extend(["--lora", res_lora, "--lora-scale", str(lora_scale)])
        if vae:
            res_vae = resolve_vae_path(vae)
            if res_vae:
                cmd.extend(["--vae", res_vae])
    else:
        return jsonify({"success": False, "error": f"Unknown batch tool: {tool}"}), 400

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "4"
    env["MKL_NUM_THREADS"] = "4"
    env["OPENBLAS_NUM_THREADS"] = "4"
    env["NUMEXPR_NUM_THREADS"] = "4"
    env["VECLIB_MAXIMUM_THREADS"] = "4"

    task_id = f"{tool}_{int(time.time()*1000)}"
    start_time = time.time()

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    register_task(task_id, f"Batch SD: {tool}")
    active_batch_tasks[task_id] = {
        "process": proc,
        "log": [],
        "status": "running",
        "start_time": start_time,
        "tool": tool,
        "cmd": " ".join(cmd)
    }

    def read_output(tid, p):
        try:
            for line in iter(p.stdout.readline, ''):
                active_batch_tasks[tid]["log"].append(line)
            p.stdout.close()
            ret = p.wait()
            active_batch_tasks[tid]["status"] = "finished" if ret == 0 else f"exited with code {ret}"
        except Exception as err:
            active_batch_tasks[tid]["status"] = f"error: {err}"
        finally:
            unregister_task(tid)

    threading.Thread(target=read_output, args=(task_id, proc), daemon=True).start()
    return jsonify({"success": True, "task_id": task_id, "tool": tool})

@app.route("/batch_status/<task_id>", methods=["GET"])
def batch_status(task_id):
    task = active_batch_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    is_running = task["process"].poll() is None
    recent_log = "".join(task["log"][-30:])

    # Collect newly generated images since task started
    st = task.get("start_time", 0)
    new_images = []
    tool = task.get("tool", "")

    if tool == "all_models":
        models_file = os.path.join(SAVE_DIR, "models.json")
        if os.path.exists(models_file):
            try:
                with open(models_file, "r") as f:
                    mdata = json.load(f)
                for idx, r in enumerate(mdata.get("runs", [])):
                    fn = r.get("file")
                    if fn:
                        fp = os.path.join(SAVE_DIR, fn)
                        if os.path.exists(fp):
                            mtime = os.path.getmtime(fp)
                            new_images.append({
                                "path": f"/static/novel_images/{fn}",
                                "time": mtime,
                                "filename": fn,
                                "model": r.get("model", ""),
                                "image_id": r.get("image_id", idx + 1)
                            })
            except Exception:
                pass
    else:
        if os.path.exists(SAVE_DIR):
            for root, dirs, files in os.walk(SAVE_DIR):
                for f in files:
                    if f.endswith((".png", ".jpg")):
                        fp = os.path.join(root, f)
                        try:
                            mtime = os.path.getmtime(fp)
                            if mtime >= st - 1.0:
                                rel = "/" + os.path.relpath(fp, ".")
                                new_images.append({"path": rel, "time": mtime, "filename": f})
                        except Exception:
                            pass
        # If no new images generated during task (e.g. all resumed/already existed), show latest images from SAVE_DIR
        if not new_images and os.path.exists(SAVE_DIR):
            for root, dirs, files in os.walk(SAVE_DIR):
                for f in files:
                    if f.endswith((".png", ".jpg")):
                        fp = os.path.join(root, f)
                        try:
                            mtime = os.path.getmtime(fp)
                            rel = "/" + os.path.relpath(fp, ".")
                            new_images.append({"path": rel, "time": mtime, "filename": f})
                        except Exception:
                            pass

        # Strictly natural/sequential sort images so frames appear in order (0000, 0001, 0002...)
        def natural_sort_key(item):
            f = item.get("filename", "")
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', f)]

        new_images.sort(key=natural_sort_key)

    latest_image = new_images[-1] if new_images else None

    # Detect compiled batch video ONLY when task is finished (NEVER while running)
    video_url = None
    if not is_running:
        if tool == "cfg_sweep":
            candidate_videos = [
                "static/novel_images/cgfX.mp4", "static/novel_images/cfgX.mp4",
                "static/temp_exp/cgfX.mp4", "static/temp_exp/cfgX.mp4"
            ]
        elif tool == "seed_explorer":
            candidate_videos = [
                "static/novel_images/seedX.mp4", "static/novel_images/seedsX.mp4",
                "static/temp_exp/seedX.mp4", "static/temp_exp/seedsX.mp4"
            ]
        elif tool == "all_models":
            candidate_videos = [
                "static/novel_images/modelsX.mp4", "static/novel_images/modelX.mp4",
                "static/temp_exp/modelsX.mp4", "static/temp_exp/modelX.mp4"
            ]
        elif tool == "slerp":
            candidate_videos = [
                "static/temp_exp/slerpX.mp4",
                "static/novel_images/slerpX.mp4"
            ]
        else:
            candidate_videos = [
                "static/novel_images/cgfX.mp4", "static/novel_images/cfgX.mp4",
                "static/novel_images/seedX.mp4", "static/novel_images/seedsX.mp4",
                "static/novel_images/modelsX.mp4", "static/novel_images/modelX.mp4",
                "static/temp_exp/cgfX.mp4", "static/temp_exp/cfgX.mp4",
                "static/temp_exp/seedX.mp4", "static/temp_exp/seedsX.mp4",
                "static/temp_exp/modelsX.mp4", "static/temp_exp/modelX.mp4"
            ]

        for cv in candidate_videos:
            if os.path.exists(cv) and os.path.getsize(cv) > 0:
                try:
                    video_url = "/" + cv
                    break
                except Exception:
                    pass

    return jsonify({
        "running": is_running,
        "status": task["status"],
        "recent_log": recent_log,
        "images": new_images,
        "image_count": len(new_images),
        "latest_image": latest_image,
        "video_url": video_url
    })

@app.route("/api/active_batch", methods=["GET"])
def api_active_batch():
    for tid, task in list(active_batch_tasks.items()):
        if task.get("process") and task["process"].poll() is None:
            return jsonify({
                "running": True,
                "task_id": tid,
                "tool": task.get("tool"),
                "status": task.get("status"),
                "start_time": task.get("start_time")
            })
    return jsonify({"running": False})

@app.route("/stop_batch/<task_id>", methods=["POST"])
def stop_batch(task_id):
    task = active_batch_tasks.get(task_id)
    if task and task["process"].poll() is None:
        try:
            task["process"].terminate()
            task["status"] = "stopped"
            return jsonify({"success": True, "message": "Batch process stopped."})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "message": "Task is not running."})

def save_sd_image(image_url, prompt):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prompt = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in prompt[:30]).strip().replace(' ', '_')
        filename = f"{timestamp}_{safe_prompt}.png"
        filepath = os.path.join(SAVE_DIR, filename)
        if image_url.startswith("data:image"):
            base64_data = image_url.split(",")[1]
            image_bytes = base64.b64decode(base64_data)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
        elif image_url.startswith("http://") or image_url.startswith("https://"):
            img_response = requests.get(image_url, timeout=1200)
            img_response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(img_response.content)
        elif image_url.startswith("/"):
            full_url = f"{SD_SERVER_URL}{image_url}"
            img_response = requests.get(full_url, timeout=1200)
            img_response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(img_response.content)
        else:
            try:
                image_bytes = base64.b64decode(image_url)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
            except Exception:
                full_url = f"{SD_SERVER_URL}/{image_url}"
                img_response = requests.get(full_url, timeout=1200)
                img_response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
        return filepath
    except Exception as e:
        ic("save failed", e)
        return None


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    def exit_gracefully(signum, frame):
        print("\n[*] Ctrl+C / termination signal received. Shutting down Latent Horizon server instantly...")
        os._exit(0)
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    create_caption_db()
    init_db()
    # Start the GC monitoring thread independently
    start_gc_monitor()
    directory = "static/TEXT"
    load_txt_files(directory)
    app.run(debug=True, host="0.0.0.0", port=5200)
