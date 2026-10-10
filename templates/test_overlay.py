import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from moviepy.editor import VideoFileClip, ImageClip
import logging

app = Flask(__name__)

# Define paths for uploads
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/outputs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Logging configuration
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    # Serve the html form to select files and set the overlay options
    return render_template('png_overlay.html')

@app.route('/png_on_mp4', methods=['POST'])
def png_on_mp4():
    # Get the uploaded files and overlay parameters
    video_file = request.files['mp4']
    png_file = request.files['png']
    start_time = float(request.form['start_time'])
    stop_time = float(request.form['stop_time'])
    position = request.form['position']

    # Save the uploaded files to the upload folder
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
    png_path = os.path.join(app.config['UPLOAD_FOLDER'], png_file.filename)
    video_file.save(video_path)
    png_file.save(png_path)

    logging.debug(f"Video file saved at: {video_path}")
    logging.debug(f"PNG file saved at: {png_path}")
    logging.debug(f"Overlay start time: {start_time}, stop time: {stop_time}, position: {position}")

    # Load the video
    video_clip = VideoFileClip(video_path)

    # Load the PNG image
    png_clip = ImageClip(png_path, transparent=True)

    # Resize the PNG if necessary (comment out if you don't want resizing)
    png_clip = png_clip.resize(height=100)  # Resize logo to height 100px (adjust as needed)

    # Set the duration of the PNG overlay
    png_clip = png_clip.set_start(start_time).set_duration(stop_time - start_time)

    # Set the position of the PNG
    if position == 'top-left':
        png_clip = png_clip.set_position(('left', 'top'))
    elif position == 'top-right':
        png_clip = png_clip.set_position(('right', 'top'))
    elif position == 'bottom-left':
        png_clip = png_clip.set_position(('left', 'bottom'))
    elif position == 'bottom-right':
        png_clip = png_clip.set_position(('right', 'bottom'))
    else:
        png_clip = png_clip.set_position(('center', 'center'))  # Default to center

    # Composite the overlay on the video
    final_clip = video_clip.set_duration(video_clip.duration).fx(lambda c: c.overlay(png_clip))

    # Output video file
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"output_{video_file.filename}")
    final_clip.write_videofile(output_path, codec='libx264', fps=24, audio=True)

    logging.debug(f"Output video saved at: {output_path}")

    # Return the output video file to the user
    return redirect(url_for('serve_output_file', filename=os.path.basename(output_path)))

@app.route('/output/<filename>')
def serve_output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
print("Starting server... Press Ctrl+C to stop. port 5300")
    app.run(debug=True, host='0.0.0.0', port=5300)
