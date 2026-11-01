---
name: motion-direction
description: "Direct a short video or motion sequence around a distinctive story device, a single beat timeline and purposeful sound-picture relationships. Use before building scenes when a video risks becoming a sequence of effects or generic cards."
---

# Motion Direction — Concept, Rhythm and Picture-Sound Unity

> Source inspiration: Cinetic (adapted directing principles only) — https://github.com/Leonxlnx/cinetic

## Use this skill when
- Starting a new video, launch teaser, feature explainer or visual sequence.
- The first concept feels generic or too close to an existing template.
- Motion, copy, camera and sound need one shared rhythm.

## Directing and implementation rules
- Develop several genuinely different story devices before coding. Pick the one that best explains the subject, not the one with the most visual effects.
- Give the film one subject, one central question or goal, one meaningful turn and an ending that resolves or echoes the opening.
- Let the picture carry the idea; narration and on-screen copy should clarify rather than repeat a paragraph.
- Keep one timeline as the source of truth for visual actions, caption timing and sound cues. Every impact sound must correspond to a visible event.
- Vary pace intentionally: use fast explanation, readable holds, a slower reveal and at least one moment of visual breathing space.
- Treat benchmarks as lessons in camera, rhythm, hierarchy and material—not as permission to copy a brand, frame, character, soundtrack or signature design.

## Workflow
1. Write three distinct concepts using different story structures or visual metaphors.
2. Choose one concept and write a one-sentence logline, opening image, turning point and payoff.
3. Create a shot/beat map with purpose, framing, camera move, duration and narration anchor for each beat.
4. Create a cue map for music, sound effects, silences and transitions before building the GSAP timeline.
5. Render, inspect and revise the actual MP4; do not accept the design from source code or a preview still alone.

## Do not
- Copying Cinetic's visual bans or taste defaults when they conflict with AI Simplified Lab's established purple identity.
- Adding Python audio packages, a new sound engine, Remotion or external services as part of this skill.
- Using a new transition or camera move merely to make a scene feel busy.
- A hook that makes a claim the evidence or rest of the video does not support.

## Factory integration
- Use the existing storyboard-director, composition-builder, edit-video and rendered-video-critique skills as the implementation path.
- Keep the established 1080x1920, 30fps HyperFrames pipeline and the repository's low-memory render settings.
- Reuse existing sound assets and audio sync tools; do not download an unlicensed sample library.

## Acceptance check
- The chosen story device is specific to the topic and can be explained in one sentence.
- Every scene has a narrative job and the pace varies intentionally.
- Picture, narration, captions and sound cues stay synchronized in the rendered output.
