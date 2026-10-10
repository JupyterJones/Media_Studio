#!/usr/bin/env python3
"""
interpret_story.py

Reads a plain text file (example: story.txt)
Generates sentence-aware TTS segments with human-like pauses
Merges them into a final narrated MP3
"""

import os
import sys
import re
from icecream import ic

# ------------------------------------------------------------
# 🎛 PAUSE PROFILE — EASY TO TUNE
# ------------------------------------------------------------
COMMA_PAUSE = 0.5           # pause at comma
SENTENCE_PAUSE = 1.0        # end of normal sentence
QUESTION_PAUSE = 1.2        # end of question
PARAGRAPH_PAUSE = 1.75       # between paragraphs
SHORT_SENTENCE_THRESHOLD = 6
SHORT_SENTENCE_MULTIPLIER = 1.4
DRAMATIC_KEYWORDS = ["but", "however", "until", "except", "though", "suddenly", "then", "yet"]
DRAMATIC_MULTIPLIER = 1.2
DIALOGUE_SENTENCE_PAUSE = 0.95
NARRATOR_RETURN_PAUSE = 2.0  # after dialogue ends

# ------------------------------------------------------------
# 🎭 UTILITY FUNCTIONS
# ------------------------------------------------------------
def is_dialogue(line):
    s = line.strip()
    return (s.startswith('"') and s.endswith('"')) or (s.startswith('“') and s.endswith('”')) or (s.startswith("'") and s.endswith("'"))

def count_words(text):
    return len(text.strip().split())

def contains_dramatic_word(text):
    lower = text.lower()
    return any(word in lower for word in DRAMATIC_KEYWORDS)

def split_into_sentences(paragraph):
    # Split on sentence-ending punctuation (., ?, !) while keeping punctuation and any closing quotes
    sentence_end_re = re.compile(r'([.!?]["\'”’]*)')
    parts = sentence_end_re.split(paragraph)
    sentences = []
    for i in range(0, len(parts)-1, 2):
        sentence = parts[i].strip() + parts[i+1]
        if sentence.strip():
            sentences.append(sentence.strip())
    if len(parts) % 2 != 0 and parts[-1].strip():
        sentences.append(parts[-1].strip())
    return sentences

def clean_line(line):
    # Remove leading bullets *, hyphens, and spaces
    line = line.lstrip("*").lstrip("-").lstrip()
    return line

def calculate_pause(sentence, is_dialogue_line):
    word_count = count_words(sentence)
    if is_dialogue_line:
        pause = DIALOGUE_SENTENCE_PAUSE
    else:
        clean_end = sentence.strip(' "\'”’')
        pause = QUESTION_PAUSE if clean_end.endswith("?") else SENTENCE_PAUSE
    if word_count <= SHORT_SENTENCE_THRESHOLD:
        pause *= SHORT_SENTENCE_MULTIPLIER
    if contains_dramatic_word(sentence):
        pause *= DRAMATIC_MULTIPLIER
    return round(min(pause, 3.0), 2)

def calculate_comma_pauses(sentence):
    return sentence.count(",") * COMMA_PAUSE

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

    # Remove empty lines and preserve paragraphs
    paragraphs = []
    current_para = []
    for line in raw_lines:
        if line.strip():
            current_para.append(line.strip())
        else:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
    if current_para:
        paragraphs.append(" ".join(current_para))

    ic("Total paragraphs:", len(paragraphs))

    script = []
    script.append("#!/bin/bash")
    script.append("# Auto-generated compassionate narrator script")
    script.append('echo "Generating narration..."')
    script.append("mkdir -p output")
    script.append("")

    seg_index = 1
    all_segments = []

    # --------------------------
    # 1️⃣ Generate sentence-level segments
    # --------------------------
    for para_index, paragraph in enumerate(paragraphs):
        sentences = split_into_sentences(paragraph)
        for sentence in sentences:
            dialogue = is_dialogue(sentence)
            clean_text = clean_line(sentence)
            script.append(f"echo {repr(clean_text)} > seg{seg_index}.txt")

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
            script.append("sleep 0.5")
            all_segments.append((f"seg{seg_index}.wav", clean_text, dialogue))
            seg_index += 1

        # Paragraph pause
        if para_index < len(paragraphs) - 1:
            script.append(f"# Paragraph pause of {PARAGRAPH_PAUSE}s")
            script.append(f"python utils/add_silence_between.py seg{seg_index-1}.wav seg{seg_index-1}.wav temp_para{para_index}.wav --pause {PARAGRAPH_PAUSE}")
            script.append(f"mv temp_para{para_index}.wav seg{seg_index-1}.wav")
            script.append("sleep 0.1")

    # --------------------------
    # 2️⃣ Merge all segments sequentially
    # --------------------------
    script.append("echo 'Merging segments with pauses...'")
    merged_file = "output/story.wav"

    if len(all_segments) == 1:
        script.append(f"cp {all_segments[0][0]} {merged_file}")
    else:
        current_file = all_segments[0][0]
        for i in range(1, len(all_segments)):
            next_file = all_segments[i][0]
            prev_sentence, prev_dialogue = all_segments[i-1][1], all_segments[i-1][2]

            pause = calculate_pause(prev_sentence, prev_dialogue)
            pause += calculate_comma_pauses(prev_sentence)
            pause = min(pause, 3.0)

            if prev_dialogue and not all_segments[i][2]:
                pause = NARRATOR_RETURN_PAUSE

            temp_file = f"temp{i}.wav"
            script.append(
                f"python utils/add_silence_between.py {current_file} {next_file} {temp_file} --pause {pause}"
            )
            script.append("sleep 0.1")
            current_file = temp_file

        script.append(f"cp {current_file} {merged_file}")

    # --------------------------
    # 3️⃣ Cleanup
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

    with open(script_name, "w", encoding="utf-8") as f:
        f.write("\n".join(script))

    os.chmod(script_name, 0o755)
    print(f"Generated: {script_name}")

# ------------------------------------------------------------
# 🚀 MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python interpret_story.py story.txt")
        sys.exit(1)

    ic("Starting interpretation engine...")
    generate_script(sys.argv[1])
    ic("Finished.")