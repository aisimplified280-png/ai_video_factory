---
name: rendered-video-critique
description: "Inspect the final encoded MP4, contact sheet, and extracted frames to evaluate narration sync, legibility, dead space, black frames, visual monotony, and AI Simplified Lab Purple Collage styling."
---

# Rendered Video Critique & Visual Quality Inspection

Never judge a video by its source code alone. Inspect actual rendered frames, contact sheets, and media playback.

## Visual Inspection Points (AI Simplified Lab Purple Collage)

1. **Cover & Hook Frame (`cover-frame.png` at 1.2s)**:
   - Does the oversized title grab immediate attention on mobile screens?
   - Is text high-contrast (crisp white on deep ink violet canvas)?
   - Does the surreal physical icon provide an intriguing focal point?
2. **Contact Sheet (`contact-sheet.png`)**:
   - Inspect all 4 keyframe moments simultaneously.
   - Do the scenes look meaningfully distinct (e.g. hook -> metaphor/diagram -> code -> takeaway), avoiding repetitive card layouts?
   - Is the architecture diagram large and legible inside its frame?
   - Are the halftone dots subtle and tasteful without creating moiré distortion?
3. **Pacing & Dead Space**:
   - Do scene transitions align with speech pauses?
   - Are there lingering empty frames or frozen animations?
4. **Captions & Safe Zones**:
   - Are active words synchronized with the voice in glowing neon chartreuse (`#a3e635`)?
   - Are captions cut off by YouTube's bottom overlay?

## Programmatic Verification

Run automated checks via `pipeline/qa-gate.mjs` and `pipeline/visual-linter.mjs`:
- FFprobe stream properties (1080x1920, 30fps, H.264 video, AAC 48kHz audio).
- FFmpeg full decode error pass (`ffmpeg -v error -i final.mp4 -f null -`).
- FFmpeg `blackdetect` filter output.
- `lintVisualDiversity()` verifying no consecutive repeated layouts.

## Observable Completion Criteria

- `contact-sheet.png` and `cover-frame.png` exist in `exports/`.
- Zero decode errors reported by FFmpeg.
- Contact sheet confirms clear visual diversity across all scenes.
