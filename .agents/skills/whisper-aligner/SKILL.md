---
name: whisper-aligner
description: Validates word-level audio/caption timing against the current Remotion composition.
---
# Audio / Caption Alignment

Use the active voice pipeline and canonical audio asset references.

Verify:
- audio files exist
- actual audio duration with ffprobe
- caption timestamps cover spoken content
- captions align with the encoded video
- caption safe zones do not cover the focal subject or character action
- scene timing comes from canonical edit decisions

Do not rely on legacy create_short.py parsing paths.

A timing field in metadata is not proof of visual sync; inspect representative encoded frames and audio duration.
