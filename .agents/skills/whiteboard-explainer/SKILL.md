---
name: whiteboard-explainer
description: "Explain a mechanism or concept by drawing its parts in meaningful stroke order on one navigable board. Use for science, AI concepts, equations, comparisons and myth-busting."
---

# Whiteboard Explainer — Draw the Reasoning

> Source inspiration: Lemo-Opuscar whiteboard — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/whiteboard/STYLE.md

## Use this skill when
- The viewer needs to understand how parts connect or how a process unfolds.
- A diagram is clearer when it is drawn in the order the narration explains it.
- The topic benefits from returning to earlier regions of one visual board.

## Directing and implementation rules
- Treat the board as one continuous world with regions that represent stages in the argument. Camera travel should follow the logic, not exist only for spectacle.
- Reveal handwriting and diagrams stroke by stroke in actual drawing order. Keep the marker nib aligned to the active stroke endpoint throughout the reveal.
- The marker must lift between separate strokes, travel with a purposeful path and park when idle. Use an eraser or movable marker only when it helps explain reversal, correction or comparison.
- One narrated idea should produce one meaningful visual addition. Prefer a simple diagram that explains the mechanism over a fully labelled diagram shown all at once.
- Use a small consistent marker palette with semantic meaning. Keep prior marks faintly available only when they provide useful context.

## Workflow
1. Divide the explanation into board regions and define the visual question answered by each region.
2. Plan the exact stroke order, marker travel, erase/rewrite beats and camera path before coding.
3. Implement paths as SVG with time-based reveal and a marker transform derived from the same path progress.
4. Animate the camera with one world-to-screen transform so the marker, drawing and labels remain aligned.
5. Inspect the beginning, middle and end of every stroke sequence, including lifts and camera transitions.

## Do not
- Typing whole text blocks onto the board and calling it handwriting.
- Decorative arrows, labels or diagrams that do not advance the explanation.
- A camera move that loses the active marker, clips the board text or makes the audience reorient without reason.
- Changing the established ELI5 studio identity into a generic whiteboard-only layout.

## Factory integration
- Use SVG path reveal and GSAP timelines; do not add a hand-tracking model, 3D renderer or new animation dependency.
- Preserve the current ELI5 Whiteboard Dialogue stage, desk and presenter as the host environment.
- Use canonical caption safe-zone settings from the repository rather than defining a competing coordinate system.

## Acceptance check
- Marker nib and visible ink stay aligned throughout the draw, not only in one sampled frame.
- Each camera move has a clear narrative destination and returns to a useful wide view.
- The diagram can be understood without relying on narration alone.
