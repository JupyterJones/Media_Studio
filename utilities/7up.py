from flask import Flask, render_template, request, redirect, send_file, render_template_string
import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image
from pydub import AudioSegment
from icecream import ic
from werkzeug.utils import secure_filename

app = Flask(__name__)

IMAGE_FOLDER = 'static/projects'
AUDIO_FOLDER = 'static/projects'
OUTPUT_FOLDER = 'static/output'
FRAME_PATH = 'static/assates/frame.png'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

TARGET_SIZE = (512, 768)

def resize_all_images():
    ic("Starting image resizing...")
    if not os.path.exists(IMAGE_FOLDER):
        ic(f"Image folder not found: {IMAGE_FOLDER}")
        return

    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    ic(f"Found {len(image_files)} images")

    for filename in image_files:
        image_path = os.path.join(IMAGE_FOLDER, filename)
        try:
            with Image.open(image_path) as img:
                ic(f"Resizing {filename}")
                resized_img = img.resize(TARGET_SIZE, Image.LANCZOS)
                resized_img.save(image_path)
        except Exception as e:
            ic(f"Error processing {filename}: {e}")

resize_all_images()

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Video</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #1e1e1e;
            color: white;
        }
        .container {
            margin-top: 50px;
            text-align: center;
        }
        .images-container, .audio-container {
            margin-top: 20px;
        }
        .image-option, .audio-option {
            display: inline-block;
            margin: 10px;
            cursor: pointer;
            border: 2px solid #333;
            padding: 5px;
            transition: transform 0.3s ease;
        }
        .image-option:hover, .audio-option:hover {
            transform: scale(1.1);
        }
        .image-option img {
            width: 150px;
            height: 150px;
            object-fit: cover;
        }
        .selected {
            border-color: #00ff00;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            margin-top: 20px;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        .audio-player {
            margin: 10px;
            padding: 10px;
            background-color: #333;
            border-radius: 5px;
            display: inline-block;
            text-align: center;
        }
    </style>
</head>
<body>

    <div class="container">
        <h1>Select Images and Audio for Your Video</h1>
        
        <form action="/create_video" method="POST" enctype="multipart/form-data">
            <div class="images-container">
                <h3>Select 7 images:</h3>
                {% for image in images %}
                    <label class="image-option">
                        <input type="checkbox" name="images" value="{{ image }}">
                        <img src="{{ url_for('static', filename='projects/' + image) }}" alt="{{ image }}">
                    </label>
                {% endfor %}
            </div>

            <div class="audio-container">
                <h3>Select one audio file:</h3>
                {% for mp3 in mp3s %}
                    <label class="audio-option">
                        <input type="radio" name="audio" value="{{ mp3 }}">
                        <div class="audio-player">
                            <p>{{ mp3 }}</p>
                            <audio controls>
                                <source src="{{ url_for('static', filename='projects/' + mp3) }}" type="audio/mp3">
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                    </label>
                {% endfor %}
            </div>

            <button type="submit">Create Video</button>
        </form>
    </div>

</body>
</html>
"""

@app.route('/')
def index():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    mp3s = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.mp3')]
    ic(images, mp3s)
    return render_template_string(HTML, images=images, mp3s=mp3s)

def overlay_frame(image_path, frame_path, output_path):
    base = Image.open(image_path).convert("RGBA")
    frame = Image.open(frame_path).convert("RGBA").resize(base.size)
    combined = Image.alpha_composite(base, frame)
    combined.convert("RGB").save(output_path, "JPEG")

def pad_audio_with_silence(audio_path, output_path, pad_duration_ms=250):
    original = AudioSegment.from_mp3(audio_path)
    silence = AudioSegment.silent(duration=pad_duration_ms)
    padded = silence + original + silence
    padded.export(output_path, format="mp3")

@app.route('/create_video', methods=['POST'])
def create_video():
    selected_images = request.form.getlist('images')
    selected_audio = request.form.get('audio')
    ic(selected_images, selected_audio)

    if len(selected_images) != 7:
        return "Please select exactly 7 images.", 400

    frame_exists = os.path.exists(FRAME_PATH)
    processed_paths = []

    for i, image_name in enumerate(selected_images):
        src = os.path.join(IMAGE_FOLDER, image_name)
        output_img = os.path.join(OUTPUT_FOLDER, f"processed_{i}.jpg")
        if frame_exists:
            overlay_frame(src, FRAME_PATH, output_img)
        else:
            Image.open(src).convert("RGB").save(output_img, "JPEG")
        processed_paths.append(output_img)

    original_audio_path = os.path.join(AUDIO_FOLDER, secure_filename(selected_audio))
    padded_audio_path = os.path.join(OUTPUT_FOLDER, "temp_audio.mp3")
    pad_audio_with_silence(original_audio_path, padded_audio_path)

    audio_clip = AudioFileClip(padded_audio_path)
    total_duration = audio_clip.duration
    ic(f"Audio duration: {total_duration:.2f} seconds")

    image_duration = total_duration / len(processed_paths)
    ic(f"Each image duration: {image_duration:.2f} seconds")

    clips = []
    for path in processed_paths:
        img_clip = ImageClip(path).set_duration(image_duration)
        clips.append(img_clip)

    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)

    output_video_path = os.path.join(OUTPUT_FOLDER, 'final_video.mp4')
    try:
        final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac', fps=24)
        return redirect(f"/{output_video_path}")
    except Exception as e:
        ic(e)
        return "An error occurred during video creation."

@app.route('/static/output/final_video.mp4')
def serve_video():
    return send_file(os.path.join(OUTPUT_FOLDER, 'final_video.mp4'), mimetype='video/mp4')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5002)
