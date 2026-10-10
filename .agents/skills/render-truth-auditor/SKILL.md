---
name: render-truth-auditor
description: Audits actual encoded MP4 media properties, audio streams, frame activity, and freeze detection using ffprobe and pixel analysis, rejecting declared metadata.
---

# render-truth-auditor

## Purpose
Establishes the encoded MP4 file as the sole authority of render success. Prohibits trusting self-declared metadata like `"render_success": true` or `"visual_diversity": 9.5`. Inspects actual pixels, actual frames, and actual audio streams.

## Trigger Conditions
- Triggered after any video render completion.
- Triggered during automated technical QA gates (`scripts/qa_editorial_video.py` and `scripts/run_local_production.py::run_qa`).
- Triggered before any video is marked ready for publication.

## Exact Inspection Targets
1. **Container & Stream Properties**: `ffprobe` format and streams array (video codec, audio codec, width, height, FPS, duration).
2. **Video Stream**: 1080x1920, 30fps (or profile specified), H.264 high profile.
3. **Audio Stream**: AAC or PCM, non-zero duration matching edit timeline within ±0.5s tolerance.
4. **Frame Extraction**: Decile frames (0% to 100%), transition boundary windows, CTA window.
5. **Pixel Quality**: Black frame detection (mean luminance < 8), blank frame detection (stddev < 3), freeze detection (identical adjacent frames = 0), activity delta (mean histogram delta >= 0.20).

## Commands / Tools to Use
- `ffprobe -v error -show_entries format=duration,size -show_streams -of json <video.mp4>`
- `ffmpeg -y -ss <t> -i <video.mp4> -frames:v 1 <frame.png>`
- `python scripts/qa_editorial_video.py --video <video.mp4> --edit <edit.json>`

## Failure Conditions
- Video duration deviates from edit decisions by > 0.5s.
- Video stream resolution or fps disagrees with the platform profile.
- Audio stream is missing, muted, or has zero duration.
- Consecutive frames at different timestamps are bitwise/statistically identical (frozen render).
- Mean inter-frame activity is below the dual floors: histogram delta < 0.12 or spatial pixel delta < 0.015.

## Evidence Requirements
- Raw JSON output of `ffprobe` containing video and audio stream parameters.
- Frame statistics table (mean, stddev, extrema, diff) for all sampled timestamps.
- Contact sheet PNG saved in `projects/<id>/qa/contact_sheet.png`.

## Output Format
```markdown
### Render Truth Audit: [video.mp4]
- Probed Streams: Video (h264, 1080x1920 @ 30fps), Audio (aac, 48kHz, stereo)
- Probed Duration: 29.8s (Edit Target: 29.5s, Delta: +0.3s) -> PASS
- Black Frames: 0 detected (Min mean: 42.1) -> PASS
- Freeze Check: 0 frozen pairs across 11 deciles -> PASS
- Visual Activity: Mean delta 0.38 (Threshold >= 0.20) -> PASS
- Verdict: VERIFIED ENCODED MEDIA
```

## Stop Conditions
If the MP4 file is missing, corrupted, unplayable, frozen, or contradicts declared duration/resolution, mark the production failed immediately.

## Interaction with Other Skills
- Independent evaluator of **typescript-remotion-auditor** outputs.
- Feeds measured evidence into **visual-semantic-adversary**.
