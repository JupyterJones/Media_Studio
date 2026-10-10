#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify
from icecream import ic
import os
import tempfile
from datetime import datetime
import speech_recognition as sr

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Flask Mic Recorder</title>
    <style>
        body{
            background:#1e1e1e;
            color:white;
            font-family:Arial;
            padding:30px;
        }
        h1{
            color:#00ffaa;
        }
        button{
            padding:12px 20px;
            margin-right:10px;
            margin-top:10px;
            border:none;
            border-radius:8px;
            font-size:16px;
            cursor:pointer;
        }
        #recordBtn{
            background:#cc3333;
            color:white;
        }
        #stopBtn{
            background:#3366cc;
            color:white;
        }
        #sendBtn{
            background:#009966;
            color:white;
        }
        textarea{
            width:100%;
            height:300px;
            margin-top:20px;
            background:#2b2b2b;
            color:#00ff99;
            border:1px solid #555;
            border-radius:10px;
            padding:15px;
            font-size:16px;
            resize:vertical;
        }
        #status{
            margin-top:20px;
            color:#ffaa00;
            font-size:18px;
        }
        audio{
            width:100%;
            margin-top:20px;
        }
    </style>
</head>
<body>

<h1>🎤 Flask Microphone Recorder</h1>

<button id="recordBtn">Start Recording</button>
<button id="stopBtn" disabled>Stop Recording</button>
<button id="sendBtn" disabled>Transcribe</button>

<div id="status">Idle</div>

<audio id="audioPlayback" controls></audio>

<textarea id="resultText" placeholder="Speech recognition results appear here..."></textarea>

<script>

let mediaRecorder;
let audioChunks = [];

const recordBtn = document.getElementById("recordBtn");
const stopBtn = document.getElementById("stopBtn");
const sendBtn = document.getElementById("sendBtn");

const statusDiv = document.getElementById("status");
const resultText = document.getElementById("resultText");
const audioPlayback = document.getElementById("audioPlayback");

recordBtn.onclick = async () => {

    audioChunks = [];

    const stream = await navigator.mediaDevices.getUserMedia({
        audio: true
    });

    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.start();

    statusDiv.innerHTML = "🎙️ Recording...";

    recordBtn.disabled = true;
    stopBtn.disabled = false;
    sendBtn.disabled = true;

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {

        const audioBlob = new Blob(audioChunks, {
            type: "audio/webm"
        });

        const audioUrl = URL.createObjectURL(audioBlob);

        audioPlayback.src = audioUrl;

        window.recordedBlob = audioBlob;

        statusDiv.innerHTML = "✅ Recording Finished";

        sendBtn.disabled = false;
    };
};

stopBtn.onclick = () => {

    mediaRecorder.stop();

    recordBtn.disabled = false;
    stopBtn.disabled = true;
};

sendBtn.onclick = async () => {

    statusDiv.innerHTML = "⏳ Uploading Audio...";

    const formData = new FormData();

    formData.append(
        "audio",
        window.recordedBlob,
        "recording.webm"
    );

    const response = await fetch("/transcribe", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    resultText.value = data.text;

    statusDiv.innerHTML = "✅ Transcription Complete";
};

</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/transcribe", methods=["POST"])
def transcribe():

    uploaded_file = request.files["audio"]

    temp_dir = tempfile.gettempdir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    webm_path = os.path.join(
        temp_dir,
        f"recording_{timestamp}.webm"
    )

    wav_path = os.path.join(
        temp_dir,
        f"recording_{timestamp}.wav"
    )

    uploaded_file.save(webm_path)

    ic(webm_path)

    ffmpeg_command = (
        f'ffmpeg -y -i "{webm_path}" '
        f'-ar 16000 -ac 1 "{wav_path}"'
    )

    ic(ffmpeg_command)

    os.system(ffmpeg_command)

    recognizer = sr.Recognizer()

    text = ""

    try:

        with sr.AudioFile(wav_path) as source:

            audio_data = recognizer.record(source)

            text = recognizer.recognize_google(audio_data)

            ic(text)

    except Exception as e:

        ic(e)

        text = f"ERROR: {str(e)}"

    if os.path.exists(webm_path):
        os.remove(webm_path)

    if os.path.exists(wav_path):
        os.remove(wav_path)

    return jsonify({
        "text": text
    })

if __name__ == "__main__":

    ic("Starting Flask App")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )