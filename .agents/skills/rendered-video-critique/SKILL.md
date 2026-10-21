---
name: rendered-video-critique
description: "Inspect the final encoded MP4, contact sheet, and extracted frames to evaluate narration sync, legibility, dead space, black frames, visual monotony, and AI Simplified Lab Purple Collage styling."
---

# Rendered Video Critique & Visual Quality Inspection
(Inspired by `claude-motion` motion intelligence & `motion-graphics-skills` design judgment)

Never judge a video by its source code alone. Inspect actual rendered frames, diagnostic contact sheets, and media playback.

## Multi-Moment Visual Inspection (`motion-contact-sheet.png`)

Inspect all 3 critical moments for each scene across the 12-frame diagnostic grid (4 scenes x 3 moments):
1. **Entrance Moment (`+0.35s`)**:
   - Does the scene enter with a motivated movement (e.g. lateral scan, curved bridge arc, vertical drop, stamp bounce) rather than a generic fade-in?
   - Does text clear safe zones: top >= 220px (avoiding YouTube Shorts channel header) and bottom <= 1450px (preserving caption & UI clearance)?
2. **Action / Traversal Moment (Midpoint)**:
   - Does the primary focal subject move in physical cause-and-effect with other elements?
   - Do visited nodes, lines, and tracks react (illuminating, pulsing, or dimming irrelevant background dots)?
   - Are live numbers and counters rolling/ticking into place synchronized with speech?
3. **Payoff / Resolution Moment (`duration - 0.25s`)**:
   - Does the final composition simplify and lock onto the target or takeaway?
   - Does continuous object transformation persist or morph cleanly into the next beat's entrance?

## Ranked Polish Checklist (Triage Hierarchy)

All visual findings are categorized and resolved by priority:

- **P0 — Critical Blockers (Release Blocked)**:
  - Black frame segments detected by FFmpeg `blackdetect`.
  - Zero motion during spoken narration (static frozen frame).
  - Text or graphic elements encroaching into safe zones (< 200px or > 1520px).
  - Broken asset targets or missing scene graph structures.
- **P1 — High Polish (Quality Standard)**:
  - Repetitive entrance movements (> 50% scenes using identical entrance tween).
  - Isolated movement without cause-and-effect (focal element moves, but no background or node responds).
  - Broken transition continuity (persisting element in Scene N fails to connect to morph target in Scene N+1).
- **P2 — Medium Polish (Aesthetic Refinement)**:
  - Missing SFX audio cue on high-impact visual actions (bounce, laser descend, stamp thud, target lock).
  - Insufficient contrast between secondary subtitle and canvas.

## Programmatic Verification

Run automated checks via `pipeline/qa-gate.mjs`, `pipeline/visual-linter.mjs`, and `pipeline/visual-critique.mjs`:
- FFprobe stream properties (1080x1920, 30fps, H.264 video, AAC 48kHz audio).
- FFmpeg full decode error pass (`ffmpeg -v error -i final.mp4 -f null -`).
- FFmpeg `blackdetect` filter output (0 black segments).
- `lintVisualDiversity()` verifying no accidental asset reuse and score >= 75.
- `critiqueRenderedSceneMoments()` verifying 0 P0 blockers and ranked polish report.

## Observable Completion Criteria

- `final.mp4` rendered with zero decode errors.
- `motion-contact-sheet.png` (3 columns: Entrance | Action | Payoff x 4 rows) and `cover-frame.png` exist in `exports/`.
- `visual-critique-report.json` generated with ranked polish checklist and score >= 85.
- Multi-moment inspection confirms genuine element-level motion and cause-and-effect responses.
