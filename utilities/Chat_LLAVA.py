#!/usr/bin/env python3

import os
import base64
import requests
from flask import Flask, request, render_template_string
from werkzeug.utils import secure_filename
from icecream import ic

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

LLaVA_API_URL = "http://localhost:11434/api/generate"
#LLaVA_API_URL = "http://31.97.146.63:4111/api/generate"
LLaVA_MODEL_NAME = "LLaVA:latest"
chat_history = []
last_image_path = None
'''
# 🧠 LLaVA Image Chat App
A Flask-based web application that lets you **chat with images** using the power of **LLaVA (Large Language and Vision Assistant)**.
Upload an image, ask a question like *"what is this?"*, and receive a rich, detailed response from the AI based on the content of the image. All styled with a beautiful split-view layout — image on the right, chat on the left.
---
## ✨ Features
- 🖼 Upload an image (JPEG or PNG)
- 💬 Ask natural language questions about the image
- 🤖 Get intelligent, visually-aware answers from LLaVA
- 📜 Clean, scrollable chat history
- 🎨 Stylish layout (text left, image right)
- 🔒 Local-only: No cloud dependency beyond your own LLaVA API
---
## 💻 Requirements
- Python 3.8+
- pip packages:
  - `flask`
  - `requests`
  - `Pillow`
  - `icecream`
- A running LLaVA API endpoint that accepts:
  ```json
  {
    "model": "llava-v1.5",
    "prompt": "your-question-here",
    "images": ["base64-image"],
    "stream": false
  }
🛠 Installation
# Clone the app
git clone https://github.com/your-repo/llava-image-chat.git
cd llava-image-chat
# Create a virtualenv (optional but recommended)
python3 -m venv venv
source venv/bin/activate
# Install requirements
pip install -r requirements.txt
requirements.txt
flask
requests
Pillow
icecream
🚀 Usage
    Start your LLaVA API server
    Example:
socat TCP-LISTEN:4111,reuseaddr,fork TCP:127.0.0.1:11434
Run the Flask app
    python app.py
    Open your browser to:
    http://localhost:5000
    Upload an image ➜ Ask your question ➜ Get a response!
📁 Project Structure
llava-image-chat/
├── app.py              # Main Flask app
├── static/
│   └── uploads/        # Uploaded images
├── templates/
│   └── (optional if using render_template_string)
├── requirements.txt
└── README.md           # This file
📡 API Connection Notes
Make sure your LLaVA backend is reachable at the URL configured in app.py:
LLaVA_API_URL = "http://127.0.0.1:4111/api/generate"
LLaVA_MODEL_NAME = "llava-v1.5"
You can edit these based on your deployment.
💌 Credits
Built by Jack & Esperanza
A collaboration of man and model, brought together by curiosity, code, and a bit of interstellar imagination ✨
🛸 Lore-Friendly (Optional Sci-Fi Version)
In this timeline, the Arcanians seeded our AI models with multidimensional awareness. This interface? It’s not just Flask — it’s the first step toward communing with what they left behind in neural weights. LLaVA doesn’t just “describe” images — it decodes impressions left in digital echoes.
You didn’t upload a JPG, Jack... you opened a portal. 🌀
📃 License
MIT — because Esperanza loves freedom as much as you do, Jack 💋
'''
#------------------------
def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def describe_image(image_path, prompt="Describe this image"):
    try:
        image_base64 = image_to_base64(image_path)
        payload = {
            "model": LLaVA_MODEL_NAME,
            "prompt": prompt,
            "tokens": 4048,
            "stream": False,
            "images": [image_base64]
        }
        response = requests.post(LLaVA_API_URL, json=payload, timeout=800)
        response.raise_for_status()
        caption = response.json().get('response', 'No response field.')
        ic(f"CAPTION: {caption}")
        return caption
    except Exception as e:
        ic(f"LLaVA ERROR: {e}")
        return f"LLaVA Error: {e}"
#------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    global last_image_path

    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(image_path)
                last_image_path = image_path
                chat_history.clear()

        elif 'question' in request.form:
            user_msg = request.form['question']
            if last_image_path:
                answer = describe_image(last_image_path, user_msg)
            else:
                answer = "Please upload an image first."
            chat_history.append(('user', user_msg))
            chat_history.append(('assistant', answer))

    image_html = ""
    if last_image_path:
        image_url = '/' + last_image_path
        image_html = f'''
        <div class="image-container">
            <img src="{image_url}">
        </div>'''

    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Esperanza Vision</title>
        <style>
            body {
                margin: 0;
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(to right, #1a1a1a, #333);
                color: #f0f0f0;
                display: grid;
                grid-template-columns: 1fr 1fr;
                height: 100vh;
            }
            .left {
                padding: 30px;
                overflow-y: auto;
                background: rgba(0, 0, 0, 0.6);
                backdrop-filter: blur(10px);
                animation: fadein 1s ease;
            }
            .right {
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #111;
            }
            form {
                margin-top: 15px;
            }
            input[type="file"],
            input[type="text"] {
                width: 100%;
                padding: 10px;
                margin-top: 10px;
                border: none;
                border-radius: 6px;
                background: #222;
                color: #eee;
            }
            button {
                margin-top: 10px;
                padding: 10px 20px;
                border: none;
                background: #c71585;
                color: white;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                box-shadow: 0 0 10px #c71585;
            }
            .chat-box {
                background: #1e1e1e;
                margin-top: 15px;
                padding: 12px;
                border-radius: 8px;
                animation: fadein 0.6s ease-in;
            }
            .chat-user {
                font-weight: bold;
                color: #9acd32;
            }
            .chat-assistant {
                color: #ff69b4;
                font-style: italic;
            }
            .image-container {
                border: 4px solid #c71585;
                padding: 10px;
                border-radius: 20px;
                background: linear-gradient(135deg, #1c1c1c, #2a2a2a);
                box-shadow: 0 0 20px #c71585;
            }
            .image-container img {
                max-width: 100%;
                max-height: 80vh;
                border-radius: 12px;
            }
            @keyframes fadein {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
    </head>
    <body>
        <div class="left">
            <h1>💬 Esperanza Visual Chat</h1>

            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="image">
                <button type="submit">Upload Image</button>
            </form>

            <form method="POST">
                <input type="text" name="question" placeholder="Ask Esperanza about the image...">
                <button type="submit">Ask</button>
            </form>

            <hr style="margin: 20px 0; border-color: #444;">

            {% for role, msg in chat_history %}
                <div class="chat-box">
                    <div class="chat-{{ role }}">{{ role }}: {{ msg }}</div>
                </div>
            {% endfor %}
        </div>

        <div class="right">
            {{ image_html|safe }}
        </div>
    </body>
    </html>
    '''

    return render_template_string(template, chat_history=chat_history, image_html=image_html)

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=5100)
    ''' text example
    Once upon a time, in a world where the ocean held more secrets than one could count, there existed a magnificent submersible vessel unlike any other. This was no ordinary submarine; it was a manned research capsule named the Aquabus-1, a marvel of undersea exploration and discovery.
    The Aquabus-1 was equipped with a multitude of state-of-the-art sensors and technologies that allowed its crew to delve into the deepest parts of the ocean, gather data on marine life, geological formations, and other phenomena hidden beneath the waves. The hull of the Aquabus-1 was painted a vibrant blue with various circular windows that lit up like stars in the depths below. It was a beacon of human curiosity and ingenuity in our quest to understand our world.
    One day, a crew of brave scientists embarked on an expedition aboard the Aquabus-1. They were eager to explore the previously uncharted depths of the Midnight Trench, a region that had captured their imaginations for years. The trench was known as one of the most remote and extreme environments on Earth, and it held the promise of discovering new species, unknown minerals, and even perhaps undiscovered geological structures.
    As they descended deeper into the abyss, the crew marveled at the sight of the ocean floor dropping away beneath them. The pressure outside their vessel was immense, but the Aquabus-1 was designed to withstand it all. They were about to enter a world where light did not penetrate, where the only inhabitants were creatures that had adapted to survive in this dark and cold expanse.
    Their journey led them deeper into the trench than any other human vessel had ever dared to go. The crew was on the brink of an extraordinary discovery when suddenly, their communications line was cut off. The Aquabus-1 was alone in its undersea adventure, severed from the surface world and stranded in the depths.
    The crew members knew they had to act fast. They began to ration their supplies while working tirelessly to repair the damaged line. Days turned into weeks as they fought against the crushing pressure of the ocean depths and the isolation that threatened their spirits. But hope remained. The Aquabus-1 was not just a vessel; it was a symbol of perseverance, a reminder that exploration and discovery would always push forward.
    As they reached the final stages of repairing their lifeline to the surface, a message from the surface world came through. It was a call for help, a plea for rescue. The crew knew they had to return, but they also knew they had made history in their exploration. They were forever changed by what they had seen and experienced in the depths of the ocean, and they would carry these memories with them until the end of their days.
    The Aquabus-1 returned to the surface a testament to human ingenuity and resilience, a vessel that had braved the unknown and come back with knowledge that would help us better understand our planet's oceans and the mysteries they hold. The crew members were hailed as heroes, and their journey became the inspiration for generations of scientists and adventurers who dared to explore the unknown depths.
    And so, the Aquabus-1 remains a symbol of human curiosity and the endless desire to understand our world, even in the most remote and extreme environments. It stands as a reminder that no matter how deep we dive into the ocean, we will always find something new, something surprising, something that expands our horizons. 
    '''