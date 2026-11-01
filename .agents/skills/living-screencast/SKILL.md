---
name: living-screencast
description: "Direct software and AI-tool walkthroughs as coherent, redrawn interfaces with cursor actions and visible state changes. Use for tutorials, product features, settings, workflows and technical demos."
---

# Living Screencast — UI as a Cause-and-Effect Stage

> Source inspiration: Lemo-Opuscar living-screencast — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/living-screencast/STYLE.md

## Use this skill when
- A feature or workflow must be demonstrated step by step.
- The explanation depends on an input, click, toggle, result, error or changed state.
- A simulated product UI is more legible and controllable than a screen recording.

## Directing and implementation rules
- Redraw the interface with the existing HTML/CSS/SVG composition system. Use real screenshots only when the source material is explicitly a real screenshot and its fidelity matters.
- The cursor represents the operator. The existing presenter, when the selected style has one, represents the guide. Do not add a mascot by default.
- Every click must have a target, a visible click event, and a truthful result. Model the before-state and after-state explicitly; the cursor must not click a control whose state never changes.
- Anchor cursor positions to actual element geometry or stable composition coordinates. Do not guess offsets by eye when a target element already exists in the DOM.
- Keep UI copy and demo data coherent across the whole walkthrough. Match real product labels, terminology and behaviour when making a real-product tutorial.
- Let the camera follow the active control or result, then pull back when the viewer needs the full workflow. Keep the cursor, target and important label readable together.

## Workflow
1. Write the exact task the viewer is watching the software complete; reduce the walkthrough to the smallest set of actions that proves it.
2. Define each UI state and the transition that changes it before animating the cursor.
3. Build the UI elements and their state changes first, then add cursor path, click pulse, focus shift and presenter gaze.
4. Map each interaction to a narration boundary and only add a click sound when a real visible action occurs.
5. Render the interaction moments and confirm the control, state change, result and narration all agree.

## Do not
- A fake interface presented as a real product capture; label illustrative simulations accurately.
- Decorative cursor movement, click ripples without state changes, random terminal output or invented product claims.
- Text too small to read, camera zoom that crops the selected control, or the presenter covering the UI.
- Replacing a user's existing split-canvas or presenter composition with a new mascot-led template.

## Factory integration
- Use HyperFrames and GSAP already in the repository; do not add Remotion or an external screen-recording service.
- Drive all interaction states and cursor positions from the existing composition timeline so direct frame rendering is deterministic.
- Preserve the existing presenter and layout rules of technical-notebook-explainer when that style is selected.

## Acceptance check
- At every click, the cursor visibly reaches the correct target and the UI changes to the expected state.
- No invented UI labels, values or product behaviour remain in a real-product tutorial.
- The selected control and its result are both legible in the rendered frames.
