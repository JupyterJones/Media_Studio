#!/usr/bin/env python3

import os
import sys
from icecream import ic

"""
Narative_Orchestr.py

Reads a plain text file (example: story.txt)
Automatically evaluates human-like pauses
Generates story.sh using compassionate omniscient narrator pacing
This script is a sophisticated "Narrative Orchestrator." It doesn't just convert text to speech; it applies emotional intelligence to the timing and pacing of a story.

---

### 1. Evaluation of `Narative_Orchestr.py`

#### **Strengths**
*   **Narrative Intelligence:** The logic to differentiate between "Sarah" (Dialogue) and "Adam" (Narrator) based on quotation marks is a great touch for creating immersive audiobooks.
*   **Heuristic Pacing:** Using multipliers for "Dramatic Words" (but, suddenly, however) and "Short Sentences" shows a deep understanding of how humans actually tell stories.
*   **Decoupled Design:** By generating a `.sh` script instead of running the TTS directly, you allow the user to inspect the commands before execution and handle long-running processes outside of the Python GIL.
*   **Clean Configuration:** Putting the `PAUSE PROFILE` at the top makes it very easy for non-programmers to "tune" the performance.

#### **Areas for Improvement**
*   **O(n²) Merging Complexity:** The current `.sh` logic merges files one by one (`temp1`, `temp2`, etc.). If you have a 100-line story, the computer has to rewrite the entire accumulated audio file 100 times. For long books, this will become very slow. 
    *   *Fix:* Use an `ffmpeg` "concat demuxer" to join all segments in one single command.
*   **Dependency Risk:** The generated script relies on a specific file at `utils/add_silence_between.py`. If this folder structure changes, the `.sh` script breaks.
*   **Cleanup Logic:** The `rm temp*.wav || true` is a bit aggressive. If a user has other temp files in that folder, they will be lost.

---

### 2. README.md

Below is a comprehensive README for your project.

```markdown
# Interpret Story: Compassionate Narrator Engine 🎭

`Narative_Orchestr.py` is an intelligent Text-to-Speech (TTS) pipeline that transforms plain text stories into emotionally paced audio performances. It analyzes the structure of your text to determine when to pause, which voice to use, and how to emphasize dramatic moments.

## ✨ Features

-   **Dual-Voice Support:** Automatically switches between `af_sarah` (for dialogue) and `am_adam` (for narration).
-   **Contextual Pacing:**
    -   **Dramatic Emphasis:** Slows down for keywords like *“suddenly”*, *“however”*, or *“until”*.
    -   **Short Sentence Punch:** Automatically adjusts timing for punchy, short sentences.
    -   **Narrator Transitions:** Adds a longer "breath" when switching from a character back to the narrator.
-   **Human-Like Pauses:** Distinct timings for commas, periods, questions, and paragraph breaks.
-   **Automated Workflow:** Generates a standalone Bash script to handle the heavy lifting of TTS generation and audio merging.

## 🛠 Prerequisites

Before running the engine, ensure you have the following installed:

1.  **Python 3.x**
2.  **Icecream:** `pip install icecream`
3.  **Kokoro-TTS:** The `kokoro-tts` command must be available in your system PATH.
4.  **FFmpeg:** Required for final MP3 conversion.
5.  **Utils Folder:** A script located at `utils/add_silence_between.py` to handle precise audio concatenation.

## 🚀 Usage

1.  **Prepare your story:** Create a `.txt` file (e.g., `my_story.txt`). Use standard quotation marks `"` for dialogue.
2.  **Generate the script:**
    ```bash
    python3 Narative_Orchestr.py my_story.txt
    ```
3.  **Run the narration:**
    This creates a file named `my_story.sh`. Execute it to generate the audio:
    ```bash
    chmod +x my_story.sh
    ./my_story.sh
    ```
4.  **Find your output:** Your finished audiobook will be in the `output/` folder with a timestamped filename.

## 🎛 Customization: The "Pause Profile"

You can fine-tune the "personality" of the narrator by editing the constants at the top of `Narative_Orchestr.py`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `COMMA_PAUSE` | 0.50s | Brief pause at commas. |
| `SENTENCE_PAUSE` | 1.15s | Standard breath between sentences. |
| `QUESTION_PAUSE` | 1.35s | Longer pause after a question to let it "sink in". |
| `DRAMATIC_MULTIPLIER`| 1.25x | Percentage slowdown for dramatic keywords. |
| `NARRATOR_RETURN` | 2.80s | A long pause after a character stops speaking. |

## 📂 Project Structure

-   `Narative_Orchestr.py`: The logic engine.
-   `utils/add_silence_between.py`: Helper script for audio merging.
-   `output/`: Where your final `.wav` and `.mp3` files are stored.
-   `seg*.wav`: Intermediate files (automatically cleaned up after completion).

## 📄 License
MIT

**To use the README:** Copy the block above and save it as `README.md` in the same folder as your script.
"""


# ------------------------------------------------------------
# 🎛 PAUSE PROFILE — EASY TO TUNE
# ------------------------------------------------------------
COMMA_PAUSE = 0.50
SENTENCE_PAUSE = 1.15
QUESTION_PAUSE = 1.35
PARAGRAPH_PAUSE = 2.4

SHORT_SENTENCE_THRESHOLD = 6  # words
SHORT_SENTENCE_MULTIPLIER = 1.6

DRAMATIC_KEYWORDS = ["but", "however", "until", "next","except", "though", "suddenly", "then", "yet"]
DRAMATIC_MULTIPLIER = 1.25

DIALOGUE_SENTENCE_PAUSE = 0.95
NARRATOR_RETURN_PAUSE = 2.8

# ------------------------------------------------------------
# 🎭 UTILITY FUNCTIONS
# ------------------------------------------------------------
def is_dialogue(line):
    return line.strip().startswith('"') and line.strip().endswith('"')

def count_words(text):
    return len(text.strip().split())

def contains_dramatic_word(text):
    lower = text.lower()
    return any(word in lower for word in DRAMATIC_KEYWORDS)

def calculate_pause(line, is_dialogue_line):
    word_count = count_words(line)
    if is_dialogue_line:
        pause = DIALOGUE_SENTENCE_PAUSE
    else:
        pause = QUESTION_PAUSE if line.strip().endswith("?") else SENTENCE_PAUSE

    if word_count <= SHORT_SENTENCE_THRESHOLD:
        pause *= SHORT_SENTENCE_MULTIPLIER

    if contains_dramatic_word(line):
        pause *= DRAMATIC_MULTIPLIER

    return round(pause, 2)

# ------------------------------------------------------------
# 🎬 SCRIPT GENERATION
# ------------------------------------------------------------
def generate_script(text_file):
    if not os.path.exists(text_file):
        print("File not found.")
        sys.exit(1)

    base_name = os.path.splitext(text_file)[0]
    script_name = base_name + ".sh"

    with open(text_file, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    lines = [l.rstrip() for l in raw_lines if l.strip()]
    ic("Total lines:", len(lines))

    script = []
    script.append("#!/bin/bash")
    script.append("# Auto-generated compassionate narrator script")
    script.append('echo "Generating narration..."')
    script.append("mkdir -p output")
    script.append("")

    seg_index = 1
    dialogue_flags = []

    # --------------------------
    # 1️⃣ Generate all segments
    # --------------------------
    for i, line in enumerate(lines):
        dialogue = is_dialogue(line)
        dialogue_flags.append(dialogue)

        clean_line = line.strip().replace('"', '')
        script.append(f"echo {repr(clean_line)} > seg{seg_index}.txt")

        # Voice selection
        if dialogue:
            voice = "af_sarah"
            speed = "1.0"
        else:
            voice = "am_adam"
            speed = "0.95"

        # Generate wav
        script.append(f"echo 'Generating segment {seg_index}...'")
        script.append(
            f"kokoro-tts seg{seg_index}.txt seg{seg_index}.wav "
            f"--voice {voice} --speed {speed} --lang en-us"
        )
        script.append(f"sleep 0.5  # allow TTS to finish writing seg{seg_index}.wav")
        script.append("")

        seg_index += 1

    # --------------------------
    # 2️⃣ Merge all segments sequentially with pauses
    # --------------------------
    script.append("echo 'Merging segments with pauses...'")
    merged_file = "output/story.wav"

    if len(lines) == 1:
        script.append(f"cp seg1.wav {merged_file}")
    else:
        # Start with first segment
        current_file = "seg1.wav"

        for i in range(1, len(lines)):
            next_file = f"seg{i+1}.wav"
            temp_file = f"temp{i}.wav"

            pause = calculate_pause(lines[i-1], dialogue_flags[i-1])

            # Paragraph break detection
            if not lines[i].strip():
                pause = PARAGRAPH_PAUSE

            # Narrator return pause
            if dialogue_flags[i-1] and not dialogue_flags[i]:
                pause = NARRATOR_RETURN_PAUSE

            script.append(
                f"python utils/add_silence_between.py {current_file} {next_file} {temp_file} --pause {pause}"
            )
            script.append("sleep 0.1")

            # Update current file
            current_file = temp_file

        # Move final merged file
        script.append(f"mv {current_file} {merged_file}")

    # --------------------------
    # 3️⃣ Cleanup intermediate segments
    # --------------------------
    script.append("rm seg*.txt seg*.wav temp*.wav || true")
    script.append('echo "Done: output/story.wav"')

    # --------------------------
    # 4️⃣ Create timestamped MP4
    # --------------------------
    script.append("")
    script.append('# Create final MP4 with timestamped filename')
    script.append('file="output/$(date +%Y-%m-%d_%H-%M-%S).mp3"')
    script.append('ffmpeg -i output/story.wav -y "$file"')
    script.append('echo "✅ Final video created: $file"')

    # --------------------------
    # Write script file
    # --------------------------
    with open(script_name, "w", encoding="utf-8") as f:
        f.write("\n".join(script))

    os.chmod(script_name, 0o755)
    print(f"Generated: {script_name}")

# ------------------------------------------------------------
# 🚀 MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Narative_Orchestr.py story.txt")
        sys.exit(1)

    ic("Starting interpretation engine...")
    generate_script(sys.argv[1])
    ic("Finished.")