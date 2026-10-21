---
name: rendered-video-critique
description: "Inspect the final encoded MP4, contact sheet, and extracted frames to evaluate narration sync, legibility, dead space, black frames, and visual monotony."
---

# Rendered Video Critique & Visual Quality Inspection

Never judge a video by its source code alone. Inspect actual rendered frames, contact sheets, and media playback.

## Visual Inspection Points

1. **Cover & Hook Frame (`cover-frame.png` at 1.2s)**:
   - Does the headline grab attention immediately?
   - Is text high-contrast and legible at mobile thumbnail sizes?
2. **Contact Sheet (`contact-sheet.png`)**:
   - Inspect all 4 keyframe moments simultaneously.
   - Do the scenes look meaningfully distinct, or does the layout feel copy-pasted?
   - Is there visual progression from problem -> architecture -> code -> conclusion?
3. **Pacing & Dead Space**:
   - Do transitions align seamlessly with speech pauses?
   - Are there lingering empty cards or frozen animations?
4. **Captions & Safe Zones**:
   - Are active words synchronized with the voice?
   - Are captions cut off by YouTube's bottom overlay?

## Programmatic Verification

Run automated checks via `pipeline/qa-gate.mjs`:
- FFprobe stream properties (1080x1920, 30fps, AAC 48kHz audio).
- FFmpeg full decode error pass (`ffmpeg -v error -i final.mp4 -f null -`).
- FFmpeg `blackdetect` filter.

## Observable Completion Criteria

- `contact-sheet.png` and `cover-frame.png` exist in `exports/`.
- Zero decode errors reported by FFmpeg.
- Contact sheet confirms clear visual diversity across all scenes.
