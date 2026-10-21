---
name: storyboard-director
description: "Direct story-first, beat-by-beat storyboards for YouTube Shorts and video explainers: assign narrative purposes, match viewer questions to visual modes, and eliminate monotonous template repetition."
---

# Storyboard Director

Direct narrative-driven visual pacing for technical and educational Shorts. Avoid generic stock clips dropped behind every paragraph; direct the exact visual mode that teaches what the spoken line describes.

## Narrative Purpose & Visual Mode Mapping

Each narrative beat must answer a specific viewer question using an appropriate visual mode:

| Narrative Purpose | Viewer Question | Visual Mode | Treatment |
|---|---|---|---|
| Isolate core operational bottleneck | What mistake is slowing down my system? | `hook` | Hero headline, glowing badge, high-contrast problem card |
| Visually demonstrate data flow / lifecycle | How does data move through system components? | `architecture-diagram` | Verified diagram asset or animated node pipeline |
| Show copy-pasteable authentic syntax | What exact configuration or syntax is needed? | `code` or `terminal` | Real code block, CLI window with syntax highlights |
| Sequential execution checklist | What step-by-step stages must be followed? | `step-process` | Numbered sequential badges with animated reveals |
| Deliver verifiable evidence-backed takeaway | What is the concrete takeaway and proof? | `concept-explainer` | Core takeaway card citing authentic documentation |
| Reveal physical or software artifact | What does the real asset or interface look like? | `asset-reveal` | Verified media frame with attribution badge |

## Procedure

1. **Sentence Alignment**: Anchor each beat to exact start and end timestamps extracted from TTS sentence boundaries.
2. **Visual Diversity Check**: Ensure consecutive beats do not use the same card type or visual mode.
3. **Asset Association**: If a beat explains an architecture or requires visible proof, associate a verified asset ID from the `AssetRegistry`.
4. **Intermediate Representation**: Export `storyboard.json` to project directory before rendering HTML compositions.

## Observable Completion Criteria

- `storyboard.json` exists, containing structured beats with `narrativePurpose`, `viewerQuestion`, and `visualMode`.
- No two consecutive scenes use identical layouts or visual modes.
- Exact millisecond timestamps match speech audio boundaries.
