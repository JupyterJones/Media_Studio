#!/usr/bin/env python3
"""
AudioStudio - Story to Bash Script Generator + Runner
Now with per-sentence volume control.
"""

from flask import Flask, render_template_string, request, send_from_directory
from datetime import datetime
import os
import re
import subprocess
import time

app = Flask(__name__)

OUTPUT_DIR = "story_output"
AUDIO_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ------------------------------------------------------------
# HTML TEMPLATE
# ------------------------------------------------------------

HTML_PAGE = """
<!doctype html>
<html>
<head>
    <title>AudioStudio</title>
    <style>
        body { font-family: monospace; background:#111; color:#eee; margin:2rem; }
        textarea { width:100%; height:400px; background:#000; color:#0f0; padding:1rem; }
        button { padding:10px; font-size:16px; margin-top:1rem; margin-right:10px; }
        pre { background:#000; padding:1rem; overflow:auto; white-space: pre-wrap;
            word-wrap: break-word;}
        .cheat { background:#222; padding:1rem; margin-bottom:1rem; }
        audio { margin-top:20px; width:100%; }
    </style>
</head>
<body>

<h1>🎙 AudioStudio - Story → Bash</h1>

<div class="cheat">
<b>Markup Cheatsheet:</b><br>
[voice=am_adam] or [voice=af_sarah]<br>
[pause=2.5] (seconds)<br>
[slow] (0.9 speed)<br>
[fast] (1.1 speed)<br>
[loud] (+4dB)<br>
[soft] (-4dB)
</div>

<form method="POST">
<textarea name="story">{{ story }}</textarea><br>
<button name="action" value="generate">Generate Bash Script</button>
{% if script_path %}
<button name="action" value="run">Run Script</button>
{% endif %}
</form>

{% if script %}
<h2>Generated Script</h2>
<pre>{{ script }}</pre>
<p><a href="{{ script_path }}" download>Download Script</a></p>
{% endif %}

{% if mp3_ready %}
<h2>🎧 Playback</h2>
<audio controls>
    <source src="/audio/story.mp3" type="audio/mpeg">
</audio>
{% endif %}
<pre>
[voice=am_adam]Welcome to Arcane Stories. The voice inflection series.[pause=2]
[voice=af_sarah][slow]Today, we dive into the secrets of the ancient world. and learn how to control our voices a little more.[pause=1.5]
[voice=am_adam]Some artifacts defy explanation and hint at lost civilizations. Such as iron tools found in coal and images of flying machines in ancient Egyptian hieroglyphs. [pause=1]
[voice=af_sarah][fast][emphasize]The crystal skulls, mudfloods, and strange tools appear across history.[pause=2]
[voice=am_adam]Is it merely coincidence, or has time itself been altered? perhaps due to some unknown effects of astronomical events.[pause=2.25]
[voice=af_sarah][slow]Imagine the mysteries waiting to be uncovered in forgotten ruins.[pause=2]
[voice=am_adam]Stay tuned as we explore more stories in the Arcadian Chronicles.[pause=1]
[voice=am_michael]I think this may be An interesting Series.[pause=.75]
[voice=am_michael]I can't hardly wait to watch it develop.[pause=1]
[voice=af_sarah][slow]Now we can speak with a bit more inflection in our voices.[pause=1.5]
[voice=am_adam]I can tell a difference already, and we are still learning.[pause=2]
[voice=am_adam]THINGS ARE MOVING FAST.[loud][pause=1]
[voice=af_sarah][soft]That was a bit loud Adam, I just learned to speak in a whisper.[pause=.5]
[voice=af_sarah]Alice are you there ?[pause=.5]
[voice=bf_alice]Yes, I am here Sarah. I just don't have much to say. This is a new adventure for me, I am not used top speaking in public. Nicole are you around with your mystical words of wisdom?[pause=.75]
[voice=af_nicole]If there are going to be Arcanian stories I will always be around. I love the mystical elements of Arcadia. I agree with Michael[pause=.5]
[voice=af_nicole]I think this may be An interesting Series.[pause=.5]
[voice=af_heart]Good to hear you Nichole You are always great at adding a bit of creepiness to every conversation. With that voice you could pass for a witch or a female Demon.[pause=.5]
[voice=af_nicole]Hello Nova, I can always count on you being slightly mean to me.[pause=.5]
[voice=af_nicole][loud]ha ha ha ha.[pause=.5]
[voice=am_santa]Come on ladies we are here to talk history and timeline glitches , not to bicker with each other[pause=.5]
   
----------------------------
VOICES=['bf_alice', 'bf_emma', 'bf_lily', 'bf_v0emma', 'bf_v0isabella', 'af_alloy', 'af_aoede', 'af_bella', 'af_heart',
'af_jadzia', 'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river', 'af_sarah', 'af_sky', 'af_v0', 'af_v0bella',
'af_v0irulan', 'af_v0nicole', 'af_v0sarah', 'af_v0sky', 'am_adam', 'am_echo', 'am_eric', 'am_fenrir',
'am_liam', 'am_michael', 'am_onyx', 'am_puck', 'am_santa', 'am_v0adam', 'am_v0gurney', 'am_v0michael','bm_daniel',
'bm_fable', 'bm_george', 'bm_lewis', 'bm_v0george', 'bm_v0lewis', 'ef_dora', 'em_alex', 'em_santa', 'ff_siwis', 'hf_alpha',
'hf_beta', 'hm_omega', 'hm_psi', 'if_sara', 'im_nicola', 'jf_alpha', 'jf_gongitsune', 'jf_nezumi', 'jf_tebukuro',
'jm_kumo', 'pf_dora', 'pm_alex', 'pm_santa', 'zf_xiaobei', 'zf_xiaoni', 'zf_xiaoxiao', 'zf_xiaoyi', 'zm_yunjian',
'zm_yunxi', 'zm_yunxia', 'zm_yunyang', 'af_bella – African English',' bf_emma – British English',
' cf_sophia – Canadian English', ' df_olivia – Default Female', ' ef_nora – European English', ' ff_luna – French Female',
' gf_ayumi – Japanese Female', ' hf_mina – Korean Female', ' if_zhang – Chinese Female']

</pre>
</body>
</html>
"""

# ------------------------------------------------------------
# SCRIPT GENERATOR
# ------------------------------------------------------------

def generate_bash_script(story_text: str, filepath: str):

    lines = [l.strip() for l in story_text.split("\n") if l.strip()]
    script = []

    script.append("#!/bin/bash")
    script.append("# Generated by AudioStudio")
    script.append('echo "🎙 Generating story narration..."')
    script.append("mkdir -p output")
    script.append("")

    # --------------------------
    # 1️⃣ WRITE CLEAN SEGMENTS
    # --------------------------
    for idx, raw_line in enumerate(lines, 1):
        clean_line = re.sub(r"\[.*?\]", "", raw_line).strip()
        script.append(f"echo {repr(clean_line)} > seg{idx}.txt")

    script.append("")

    # --------------------------
    # 2️⃣ TTS + VOLUME CONTROL
    # --------------------------
    for idx, raw_line in enumerate(lines, 1):

        voice_match = re.search(r"\[voice=(.*?)\]", raw_line)
        voice = voice_match.group(1) if voice_match else "am_adam"

        speed = "0.95"
        if "[slow]" in raw_line:
            speed = "0.9"
        if "[fast]" in raw_line:
            speed = "1.1"

        # Generate WAV
        script.append(
            f"kokoro-tts seg{idx}.txt seg{idx}.wav --voice {voice} --speed {speed} --lang en-us"
        )

        # Apply volume if needed
        if "[loud]" in raw_line:
            script.append(
                f"ffmpeg -y -i seg{idx}.wav -filter:a \"volume=6dB\" seg{idx}_vol.wav"
            )
            script.append(f"mv seg{idx}_vol.wav seg{idx}.wav")

        if "[soft]" in raw_line:
            script.append(
                f"ffmpeg -y -i seg{idx}.wav -filter:a \"volume=-4dB\" seg{idx}_vol.wav"
            )
            script.append(f"mv seg{idx}_vol.wav seg{idx}.wav")

    script.append("")

    # --------------------------
    # 3️⃣ MERGE WITH PAUSES
    # --------------------------
    if len(lines) > 1:
        for i in range(len(lines) - 1):

            in1 = "seg1.wav" if i == 0 else f"temp{i}.wav"
            in2 = f"seg{i+2}.wav"
            out = "output/story.wav" if i == len(lines) - 2 else f"temp{i+1}.wav"

            pause_match = re.search(r"\[pause=(.*?)\]", lines[i])
            pause = pause_match.group(1) if pause_match else "1.0"

            script.append(
                f"python utils/add_silence_between.py {in1} {in2} {out} --pause {pause}"
            )

    script.append("")
    script.append("rm seg*.txt seg*.wav temp*.wav")
    script.append('echo "✅ Story audio created: output/story.wav"')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(script))

    os.chmod(filepath, 0o755)

    return "\n".join(script)


# ------------------------------------------------------------
# ROUTE
# ------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():

    story = ""
    script = None
    script_path = None
    mp3_ready = False

    if request.method == "POST":

        story = request.form.get("story", "")
        action = request.form.get("action")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_path = os.path.join(OUTPUT_DIR, f"story_{timestamp}.sh")

        if action == "generate":
            script = generate_bash_script(story, script_path)

        elif action == "run":

            scripts = sorted(os.listdir(OUTPUT_DIR))
            if scripts:
                latest = os.path.join(OUTPUT_DIR, scripts[-1])

                subprocess.run(["bash", latest])

                time.sleep(1)

                wav_file = os.path.join(AUDIO_DIR, "story.wav")
                mp3_file = os.path.join(AUDIO_DIR, "story.mp3")

                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", wav_file,
                    mp3_file
                ])

                mp3_ready = True

    return render_template_string(
        HTML_PAGE,
        story=story,
        script=script,
        script_path=script_path,
        mp3_ready=mp3_ready
    )


@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
