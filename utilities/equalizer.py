#!/usr/bin/env python3
"""
Flask Music Player with Real-Time Equalizer
- Uses Web Audio API in the browser
- Flask only serves content (correct architecture)
- Real EQ sliders + animated frequency bars
"""

import os
from flask import Flask, render_template_string
from icecream import ic

# -----------------------------
# CONFIG
# -----------------------------
APP_PORT = 5000
AUDIO_FILE = "static/mp3/For_millions_of_year.mp3"
AUDIO= "mp3/For_millions_of_year.mp3"
# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__)

# -----------------------------
# ROUTE
# -----------------------------
@app.route("/")
def index():
    ic("Serving main music player page")

    if not os.path.exists(AUDIO_FILE):
        ic("ERROR: Audio file not found:", AUDIO_FILE)

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
    </style>
</head>

<body>
<h2>🎵 Flask Music Player with Equalizer</h2>

<audio id="audio" controls crossorigin="anonymous">
    <source src="static/mp3/For_millions_of_year.mp3" type="audio/mpeg">
</audio>

<canvas id="visualizer"></canvas>

<div class="eq" id="eq"></div>

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

// Create EQ bands
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

    slider.oninput = () => {
        filter.gain.value = slider.value;
    };

    eqContainer.appendChild(slider);
});

// Wire audio graph
source.connect(filters[0]);
for (let i = 0; i < filters.length - 1; i++) {
    filters[i].connect(filters[i + 1]);
}
filters[filters.length - 1].connect(analyser);
analyser.connect(audioCtx.destination);

// Resume audio context on play (browser policy)
audio.onplay = () => {
    audioCtx.resume();
};

// Visualizer
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
    <audio controls>
    <source src="static/mp3/For_millions_of_year.mp3" type="audio/mpeg">
    Your browser does not support the audio element.
    </audio>
</body>
</html>
""")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    ic("Starting Flask Equalizer App")
    ic("Listening on port", APP_PORT)
    app.run(host="0.0.0.0", port=APP_PORT, debug=True)
