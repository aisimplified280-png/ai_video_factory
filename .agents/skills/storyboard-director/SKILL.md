---
name: storyboard-director
description: "Direct story-first, beat-by-beat storyboards for YouTube Shorts in the AI Simplified Lab Purple Collage style: assign narrative purposes, match viewer questions to visual modes, and eliminate monotonous template repetition."
---

# Storyboard Director & Motion Choreographer (AI Simplified Lab Purple Collage)
(Inspired by `claude-motion` motion timing, `motion-graphics-skills` brand fidelity, and `motion-graphics` continuous transformations)

Direct narrative-driven visual pacing for technical and educational Shorts. Avoid generic stock clips dropped behind every paragraph and avoid repetitive card templates; direct the exact visual mode, asset selection, and motion choreography that teaches what the spoken line describes.

## Visual Identity: AI Simplified Lab Purple Collage

- **Palette**: Deep ink canvas (`#0b0518` to `#241147`), rich lavender (`#c084fc`), neon chartreuse (`#a3e635`), and crisp white (`#ffffff`).
- **Texture**: Tactile halftone dot-matrix pattern with dimensional atmospheric glows.
- **Composition Diversity**: Moves beyond uniform rounded cards. Uses full-frame hooks, large illuminated architecture diagrams, physical metaphors (conveyor tracks, memory vaults, multi-tier highways), dark syntax terminals, and asymmetric comparison collages.

## Asset Intelligence Decision Matrix

For every visual beat, evaluate material across 4 criteria:
1. **Semantic Relevance**: Direct keyword and conceptual alignment with the spoken sentence (not broad topic tags).
2. **Visual Suitability**: Scalable vector SVG with transparent background preferred over noisy stock photos.
3. **Scene Participation**: Can the asset move, highlight, or transform in choreography (probe, node, laser, meter) rather than sit as passive wallpaper?
4. **License Safety**: CC0 or verified commercial royalty-free license without NC/ND restrictions.

**Procedural Fallback Rule**: If external candidates score < 25 or if the concept is an abstract computational/geometric mechanism (vector indexing, token caching, hash tables, compiler ASTs), explicitly select bespoke procedural SVG. Never force an irrelevant stock photo into a technical scene.

## Motion Choreographer: Cause-and-Effect Architecture

Every scene must define a validated `sceneGraph` with:
- **Visual Metaphor**: Concrete metaphor explaining the underlying mechanism.
- **Primary Subject**: Explicit focal element leading viewer attention.
- **Actions with Cause-and-Effect**: Every action must specify:
  - `trigger`: Spoken phrase or audio anchor synchronized to transcript timing.
  - `sfxCue`: Synchronized sound design cue (e.g. `probe-launch`, `target-lock-snap`, `stamp-bounce-thud`).
  - `causeAndEffect`: Explicit `triggerElement`, `reactingElements`, and `reaction` (e.g. visited nodes pulse green, unvisited dots dim, shockwave radiates).
- **Transition Continuity**: Specify `persistentElement` and `morphTarget` to morph objects across scene cuts rather than jumping between disconnected cards.

## Procedure

1. **Sentence Alignment**: Anchor each beat to exact start and end timestamps extracted from TTS sentence boundaries.
2. **Asset Intelligence**: Run multi-criteria scoring; assign approved external media or generate bespoke procedural SVGs.
3. **Scene Graph & Motion Score**: Specify primary subject, elements, cause-and-effect actions, and transition continuities.
4. **Visual Diversity & Integrity Linting**: Run `lintVisualDiversity()` to enforce no consecutive layout repeats and sceneGraph integrity.
5. **Export Representation**: Export `storyboard.json` (version 2) with `styleProfile: "ai_simplified_purple_collage"`.

## Observable Completion Criteria

- `storyboard.json` (v2) contains structured beats, narrative purposes, viewer questions, and validated `sceneGraph` objects.
- Every beat contains actions with `causeAndEffect`, spoken phrase triggers, and `sfxCue` sound hooks.
- Transition continuities link moving focal objects across adjacent beats.
- `lintVisualDiversity()` passes with score >= 75.
