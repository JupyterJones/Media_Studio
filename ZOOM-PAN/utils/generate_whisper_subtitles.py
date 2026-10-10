#!/usr/bin/env python3
import sys
import os
import whisper

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_whisper_subtitles.py <audio_wav> <ass_path> [title]", file=sys.stderr)
        sys.exit(1)

    audio_wav = sys.argv[1]
    ass_path = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else "Whisper Subtitles"

    if not os.path.exists(audio_wav):
        print(f"Error: Audio file not found: {audio_wav}", file=sys.stderr)
        sys.exit(1)

    try:
        model = whisper.load_model("base")
        res = model.transcribe(audio_wav, word_timestamps=True, language="en")
        
        header = f"""[Script Info]
Title: {title}
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: WhisperScroll,Outfit,13,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1.5,1,2,15,15,25,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        def sec_to_ass(s):
            h, m, sec, cs = int(s//3600), int((s%3600)//60), int(s%60), int((s-int(s))*100)
            return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"

        fad_tag = r"{\fad(80,80)}"

        for seg in res.get("segments", []):
            words = seg.get("words", [])
            if words:
                for i in range(0, len(words), 4):
                    chunk = words[i:i+4]
                    st = sec_to_ass(chunk[0]["start"])
                    et = sec_to_ass(chunk[-1]["end"])
                    txt = " ".join([w["word"].strip() for w in chunk])
                    events.append(f"Dialogue: 0,{st},{et},WhisperScroll,,0,0,0,,{fad_tag}{txt}")
            else:
                st = sec_to_ass(seg["start"])
                et = sec_to_ass(seg["end"])
                txt = seg["text"].strip()
                events.append(f"Dialogue: 0,{st},{et},WhisperScroll,,0,0,0,,{fad_tag}{txt}")

        os.makedirs(os.path.dirname(os.path.abspath(ass_path)), exist_ok=True)
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events))
            
        print("WHISPER_SUBTITLES_SUCCESS")
    except Exception as e:
        print(f"WHISPER_SUBTITLES_ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
