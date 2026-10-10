#!/bin/bash
# Auto-generated compassionate narrator script
echo "Generating narration..."
mkdir -p output

echo 'I am  Vladimir, The night watcher.' > seg1.txt
echo 'Generating segment 1...'
kokoro-tts seg1.txt seg1.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5
echo 'I patrol the streets at night to keep them safe.' > seg2.txt
echo 'Generating segment 2...'
kokoro-tts seg2.txt seg2.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5
echo 'Not because I am a nice guy, but because I love kicking the asses of criminals.' > seg3.txt
echo 'Generating segment 3...'
kokoro-tts seg3.txt seg3.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5
echo 'When i go out at night for fun, I am the bad guys, worst nightmare.' > seg4.txt
echo 'Generating segment 4...'
kokoro-tts seg4.txt seg4.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5
echo 'Merging segments with pauses...'
python utils/add_silence_between.py seg1.wav seg2.wav temp1.wav --pause 1.9
sleep 0.1
python utils/add_silence_between.py temp1.wav seg3.wav temp2.wav --pause 1.0
sleep 0.1
python utils/add_silence_between.py temp2.wav seg4.wav temp3.wav --pause 1.7
sleep 0.1
cp temp3.wav output/story.wav
rm seg*.txt seg*.wav temp*.wav || true
echo "Done: output/story.wav"

# Create final MP4 with timestamped filename
file="output/$(date +%Y-%m-%d_%H-%M-%S).mp3"
ffmpeg -i output/story.wav -y "$file"
echo "✅ Final video created: $file"