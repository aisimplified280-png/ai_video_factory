---
name: whisper-aligner
description: Automatically call local forced-alignment tools to generate TTS JSON timestamps.
---
# Instructions
When checking or generating precise word-level synchronization for captions:
- Utilize `edge-tts` to write subtitles to `.vtt`, then parse them (as already handled in `create_short.py:parse_vtt()`).
- If absolute sub-second precision is required, fallback to running `ffmpeg` audio filters or `ffprobe` to verify track lengths.
- Always check that `.vtt` output properly maps to the karaoke subtitle pill in the engine by evaluating `subs` dictionaries.
