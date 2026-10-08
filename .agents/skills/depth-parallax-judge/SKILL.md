---
name: depth-parallax-judge
description: Verifies that bg/mid/fg depth is visibly real in the rendered pixels.
---
# Depth & Parallax Judge

Verify the actual visual layers.

Required evidence:
- independently visible background elements
- independently visible midground subject/content
- independently visible foreground framing/interaction
- occlusion or scale relationships
- relative movement between depth layers
- camera displacement consistent with the scene

Do not accept z-index, layer filenames, or metadata as proof.

A single flattened image with three transparent metadata labels fails.

A valid depth scene should show measurable relative displacement or other visible spatial cues between layers.

For each scene produce:
- layer occupancy estimates
- visible layer separation
- relative motion vectors
- occlusion evidence
- timestamps/frame references
- PASS/FAIL
