---
name: brand-mark-motion
description: "Create a restrained, reusable channel logo reveal, end-card sting or subscribe mark animation from clean SVG geometry. Use when the brand mark itself needs motion, not for general scene animation."
---

# Brand Mark Motion — Clean SVG Identity Animation

> Source inspiration: Pixel2Motion (adapted principles only) — https://github.com/nolangz/pixel2motion

## Use this skill when
- The channel logo needs a short intro, outro or transition sting.
- A supplied raster logo must be converted into a simple motion-ready vector and the result can be checked visually.
- A reusable brand mark animation is being developed for several videos.

## Directing and implementation rules
- Use the supplied official logo artwork as the source of truth. Prefer an existing SVG or vector asset over redrawing it.
- If vectorization is necessary, identify semantic parts and use the simplest smooth geometry that faithfully preserves the mark. Avoid tracing every pixel into a jagged path.
- Choose a small motion personality from the brand—such as precise, energetic or warm—and use it to select timing, easing and movement.
- Animate parts in a meaningful order with anticipation, readable movement, follow-through and a stable final hold.
- Enforce a final-frame contract: the final animation frame must match the approved static logo in shape, proportions, colors and spacing.

## Workflow
1. Inspect the supplied logo, identify its semantic components and confirm the approved background variants.
2. Write a short motion specification with personality, duration, component order and intended use.
3. Build the animation using SVG and GSAP with a static fallback frame.
4. Capture entrance, mid-motion and final frames; compare the final frame directly with the approved logo.
5. Export a transparent or solid-background version only when the existing render/mux pipeline supports it reliably.

## Do not
- Changing the logo, inventing a new channel mark or redrawing a low-quality asset without approval.
- Adding Python, NumPy, Pillow, Playwright or another dependency solely to animate the existing logo.
- A long logo intro before the story hook or a large subscribe animation that competes with the content.
- Unmeasured morphs that distort the approved logo or fail to land on the exact final artwork.

## Factory integration
- Reuse existing AI Simplified Lab logo assets and the current subscribe outro conventions.
- Use local SVG, CSS and GSAP in HyperFrames; preserve transparent backgrounds and deterministic seeking.
- Keep the animation short and light enough for the 8 GB Windows low-memory render environment.

## Acceptance check
- The final animation frame is visually identical to the approved static logo.
- The animation is crisp, smooth and legible at phone scale.
- The mark can be reused without changing its source artwork or adding a paid service.
