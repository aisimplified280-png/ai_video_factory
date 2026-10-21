---
name: storyboard-director
description: "Direct story-first, beat-by-beat storyboards for YouTube Shorts in the AI Simplified Lab Purple Collage style: assign narrative purposes, match viewer questions to visual modes, and eliminate monotonous template repetition."
---

# Storyboard Director (AI Simplified Lab Purple Collage)

Direct narrative-driven visual pacing for technical and educational Shorts. Avoid generic stock clips dropped behind every paragraph and avoid repetitive white card templates; direct the exact visual mode that teaches what the spoken line describes.

## Visual Identity: AI Simplified Lab Purple Collage

- **Palette**: Deep ink canvas (`#0d0819`), rich violet (`#8b5cf6`), lavender (`#e9d5ff`), neon chartreuse (`#a3e635`), and crisp white (`#ffffff`).
- **Texture**: Tactile halftone dot-matrix pattern with dimensional atmospheric glows.
- **Composition Diversity**: Moves beyond uniform rounded cards. Uses full-frame hooks, large illuminated architecture diagrams, physical metaphors (conveyor tracks, memory vaults), dark syntax terminals, and asymmetric comparison collages.

## Narrative Purpose & Visual Mode Mapping

Each narrative beat must answer a specific viewer question using an appropriate visual mode:

| Narrative Purpose | Viewer Question | Visual Mode | Treatment |
|---|---|---|---|
| Isolate core operational bottleneck | What mistake is slowing down my system? | `hook-bold-object` | Oversized white hero title, neon chartreuse badge, surreal dimensional icon |
| Visually demonstrate data flow / lifecycle | How does data move through system components? | `architecture-diagram` | Large illuminated glass frame with verified SVG asset or glowing node pipeline |
| Make abstract software concepts concrete | What physical object illustrates this invisible dynamic? | `physical-metaphor` | Tangible metaphor (conveyor belt, pinned RAM block, multi-tier graph highway) |
| Show copy-pasteable authentic syntax | What exact configuration or syntax is needed? | `code` or `terminal` | Deep violet syntax terminal with glowing active line highlight and cursor |
| Contrast legacy friction with automation | How does the improved methodology differ? | `comparison` | Asymmetric split: red strikethrough legacy vs neon chartreuse optimized |
| Deliver verifiable evidence-backed takeaway | What is the concrete takeaway and rule of thumb? | `concept-explainer` | Architectural stamp, bold summary, authentic documentation citation |
| Reveal physical or software artifact | What does the real asset or interface look like? | `asset-reveal` | Verified media frame with license attribution badge |

## Procedure

1. **Sentence Alignment**: Anchor each beat to exact start and end timestamps extracted from TTS sentence boundaries.
2. **Visual Diversity Linting**: Ensure consecutive beats do not use the same visual mode and no single mode exceeds 50% of the video.
3. **Asset Association**: If a beat explains an architecture or requires visible proof, associate a strictly approved asset ID from the `AssetRegistry`.
4. **Intermediate Representation**: Export `storyboard.json` (version 2) with `styleProfile: "ai_simplified_purple_collage"`.

## Observable Completion Criteria

- `storyboard.json` exists with structured beats, narrative purposes, and viewer questions.
- `lintVisualDiversity()` passes with score >= 75.
- No two consecutive scenes use identical layouts or visual modes without explicit narrative reason.
- Exact millisecond timestamps match speech audio boundaries.
