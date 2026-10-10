#!/bin/bash
# Example: Simple 1-Minute Breathing Meditation

cd "$(dirname "$0")/.."
source venv/bin/activate

echo "🎙️ Generating Simple Breathing Meditation..."

# Create text segments
echo "Take a long slow, deep breath in." > seg1.txt
echo "Hold for a moment." > seg2.txt
echo "And exhale slowly." > seg3.txt
echo "Feel yourself relaxing." > seg4.txt
echo "I will try this exercise" > seg5.txt
echo "so I can relax." > seg6.txt
# Generate audio
kokoro-tts seg1.txt seg1.wav --voice af_nicole --speed 0.85 --lang en-us
kokoro-tts seg2.txt seg2.wav --voice af_nicole --speed 0.85 --lang en-us
kokoro-tts seg3.txt seg3.wav --voice af_nicole --speed 0.85 --lang en-us
kokoro-tts seg4.txt seg4.wav --voice af_nicole --speed 0.85 --lang en-us
kokoro-tts seg5.txt seg5.wav --voice am_adam --speed 0.95 --lang en-us
kokoro-tts seg6.txt seg6.wav --voice am_adam --speed 0.95 --lang en-us

# Merge with pauses
python utils/add_silence_between.py seg1.wav seg2.wav temp1.wav --pause 4.0
python utils/add_silence_between.py temp1.wav seg3.wav temp2.wav --pause 5.0
python utils/add_silence_between.py seg4.wav seg5.wav temp1.wav --pause 4.0
python utils/add_silence_between.py temp1.wav seg5.wav temp2.wav --pause 5.0
python utils/add_silence_between.py temp2.wav seg6.wav output/simple_breathing_min.wav --pause 3.0

# Cleanup
rm seg*.txt seg*.wav temp*.wav

echo "✅ Meditation created: output/simple_breathing_1min.wav"

