---
name: visual-diversity-detector
description: Detects structural visual repetition that survives metadata, text, and color changes.
---
# Visual Diversity Detector

Compare actual rendered scenes using:
- perceptual similarity
- layout/geometry similarity
- focal-point location
- major shape/region masks
- camera framing
- background structure
- character placement
- object arrangement
- motion trajectory
- transition signature

Do not treat changed text, hue, or tiny decorative effects as meaningful diversity.

Detect patterns such as:
same composition + same camera + same character pose + different text
same grid/card geometry across unrelated topics
same background architecture with different labels
same focal point and scale across every scene

Produce pairwise and whole-video similarity evidence.

Fail when unrelated scenes or topics are structurally near-identical beyond the configured threshold.

Planning diversity scores are advisory. Encoded-pixel diversity is the final authority.
