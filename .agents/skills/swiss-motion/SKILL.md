---
name: swiss-motion
description: "Create clean typographic sequences with modular grids, disciplined alignment, scale contrast and precise motion. Use for hooks, chapter transitions, comparisons, numbers and concise visual statements."
---

# Swiss Motion — Grid-Led Kinetic Typography

> Source inspiration: Lemo-Opuscar swiss-motion — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/swiss-motion/STYLE.md

## Use this skill when
- A short, high-impact statement should lead the visual beat.
- The story needs a clear numerical or typographic reveal.
- The video needs a restrained transition or visual rhythm between more complex scenes.

## Directing and implementation rules
- Choose a content-derived grid and align type, rules and blocks to it. The grid must organize the message rather than become visible decoration.
- Use strong scale contrast: one dominant word or number, supported by a small amount of contextual text.
- Move elements with precise timing and clear endpoints. Use snaps, wipes, clipping and measured slides; reserve bounce for a deliberate material action.
- Reveal copy in short meaningful fragments. Give the viewer enough hold time to read before the next change.
- Keep the channel's existing typography and palette. Swiss motion is a layout and timing discipline, not a requirement to use black, white or a foreign brand palette.

## Workflow
1. Extract one sentence or number that deserves the full frame and remove everything that does not help it.
2. Choose a grid based on the phrase length, mobile crop and supporting visual.
3. Design a static frame at 1080x1920 before animating.
4. Animate the hierarchy in reading order with timeline-locked holds and exits.
5. Review the frame paused and in motion at phone scale.

## Do not
- Filling every beat with moving text, random word-by-word animation or lyric-video behaviour.
- Kicker labels, stacked taglines or decorative microcopy with no informational value.
- Grid-heavy layouts that turn into charts or slides rather than editorial compositions.
- Changing brand fonts, palette or visual identity just to mimic the source style.

## Factory integration
- Use existing fonts, GSAP and local assets; do not import remote font or animation CDNs.
- Keep headline and captions inside the canonical title/caption safe zones.
- Use the skill for selected beats, not automatically for every scene.

## Acceptance check
- The message is understood in a paused frame and at a glance.
- Every element has a clear grid relationship and hierarchy.
- Motion timing gives viewers enough time to read without flattening the video into a text slideshow.
