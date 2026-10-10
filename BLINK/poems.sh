#!/bin/bash
# Auto-generated compassionate narrator script
echo "Generating narration..."
mkdir -p output

echo 'Title: Whispers of the Wind' > seg1.txt
echo 'Generating segment 1...'
kokoro-tts seg1.txt seg1.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg1.wav

echo 'In the realm where dreams and reality intertwine,' > seg2.txt
echo 'Generating segment 2...'
kokoro-tts seg2.txt seg2.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg2.wav

echo 'Lies a canvas painted with the hues of time.' > seg3.txt
echo 'Generating segment 3...'
kokoro-tts seg3.txt seg3.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg3.wav

echo 'A dance between the sun and moon so divine,' > seg4.txt
echo 'Generating segment 4...'
kokoro-tts seg4.txt seg4.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg4.wav

echo 'And in this grand stage, the wind takes its prime.' > seg5.txt
echo 'Generating segment 5...'
kokoro-tts seg5.txt seg5.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg5.wav

echo "With whispers soft as the first light's kiss," > seg6.txt
echo 'Generating segment 6...'
kokoro-tts seg6.txt seg6.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg6.wav

echo 'It sings tales of lands far beyond this.' > seg7.txt
echo 'Generating segment 7...'
kokoro-tts seg7.txt seg7.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg7.wav

echo 'Its voice echoes through the valleys and abyss,' > seg8.txt
echo 'Generating segment 8...'
kokoro-tts seg8.txt seg8.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg8.wav

echo 'Carrying secrets that even the stars miss.' > seg9.txt
echo 'Generating segment 9...'
kokoro-tts seg9.txt seg9.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg9.wav

echo 'It weaves tapestries of memories untold,' > seg10.txt
echo 'Generating segment 10...'
kokoro-tts seg10.txt seg10.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg10.wav

echo 'Of love stories etched in ancient gold.' > seg11.txt
echo 'Generating segment 11...'
kokoro-tts seg11.txt seg11.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg11.wav

echo 'Through rustling leaves, its secrets unfold,' > seg12.txt
echo 'Generating segment 12...'
kokoro-tts seg12.txt seg12.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg12.wav

echo "A ballad sung by nature's bold." > seg13.txt
echo 'Generating segment 13...'
kokoro-tts seg13.txt seg13.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg13.wav

echo 'The wind whispers tales of courage and strife,' > seg14.txt
echo 'Generating segment 14...'
kokoro-tts seg14.txt seg14.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg14.wav

echo 'Of battles fought, and lives sacrificed for life.' > seg15.txt
echo 'Generating segment 15...'
kokoro-tts seg15.txt seg15.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg15.wav

echo "It carries the laughter of children's cries," > seg16.txt
echo 'Generating segment 16...'
kokoro-tts seg16.txt seg16.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg16.wav

echo 'Promising echoes of their endless spies.' > seg17.txt
echo 'Generating segment 17...'
kokoro-tts seg17.txt seg17.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg17.wav

echo 'In the quiet hush of a moonlit night,' > seg18.txt
echo 'Generating segment 18...'
kokoro-tts seg18.txt seg18.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg18.wav

echo 'Its melodious symphony sets everything right.' > seg19.txt
echo 'Generating segment 19...'
kokoro-tts seg19.txt seg19.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg19.wav

echo 'A soothing balm that soothes our plight,' > seg20.txt
echo 'Generating segment 20...'
kokoro-tts seg20.txt seg20.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg20.wav

echo 'The wind is the soul of a world in flight.' > seg21.txt
echo 'Generating segment 21...'
kokoro-tts seg21.txt seg21.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg21.wav

echo 'So listen close to its gentle sighs,' > seg22.txt
echo 'Generating segment 22...'
kokoro-tts seg22.txt seg22.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg22.wav

echo 'To the whispers that make hearts fly high.' > seg23.txt
echo 'Generating segment 23...'
kokoro-tts seg23.txt seg23.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg23.wav

echo 'For within those breaths, the world lies,' > seg24.txt
echo 'Generating segment 24...'
kokoro-tts seg24.txt seg24.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg24.wav

echo 'In a poetic dance, beneath the skies.' > seg25.txt
echo 'Generating segment 25...'
kokoro-tts seg25.txt seg25.wav --voice am_adam --speed 0.95 --lang en-us
sleep 0.5  # allow TTS to finish writing seg25.wav

echo 'Merging segments with pauses...'
python utils/add_silence_between.py seg1.wav seg2.wav temp1.wav --pause 1.84
sleep 0.1
python utils/add_silence_between.py temp1.wav seg3.wav temp2.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp2.wav seg4.wav temp3.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp3.wav seg5.wav temp4.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp4.wav seg6.wav temp5.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp5.wav seg7.wav temp6.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp6.wav seg8.wav temp7.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp7.wav seg9.wav temp8.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp8.wav seg10.wav temp9.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp9.wav seg11.wav temp10.wav --pause 1.84
sleep 0.1
python utils/add_silence_between.py temp10.wav seg12.wav temp11.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp11.wav seg13.wav temp12.wav --pause 1.84
sleep 0.1
python utils/add_silence_between.py temp12.wav seg14.wav temp13.wav --pause 1.84
sleep 0.1
python utils/add_silence_between.py temp13.wav seg15.wav temp14.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp14.wav seg16.wav temp15.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp15.wav seg17.wav temp16.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp16.wav seg18.wav temp17.wav --pause 1.84
sleep 0.1
python utils/add_silence_between.py temp17.wav seg19.wav temp18.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp18.wav seg20.wav temp19.wav --pause 1.84
sleep 0.1
python utils/add_silence_between.py temp19.wav seg21.wav temp20.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp20.wav seg22.wav temp21.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp21.wav seg23.wav temp22.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp22.wav seg24.wav temp23.wav --pause 1.15
sleep 0.1
python utils/add_silence_between.py temp23.wav seg25.wav temp24.wav --pause 1.15
sleep 0.1
mv temp24.wav output/story.wav
rm seg*.txt seg*.wav temp*.wav || true
echo "Done: output/story.wav"

# Create final MP4 with timestamped filename
file="output/$(date +%Y-%m-%d_%H-%M-%S).mp3"
ffmpeg -i output/story.wav -y "$file"
echo "✅ Final video created: $file"