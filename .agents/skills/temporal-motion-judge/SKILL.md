---
name: temporal-motion-judge
description: Judges whether motion is visually meaningful across the encoded video.
---
# Temporal Motion Judge

Analyze the encoded MP4, not only planner metadata.

Measure:
- frame-to-frame activity
- scene-level motion coverage
- freeze intervals
- repeated frames
- camera movement
- subject movement
- character movement
- progressive reveals
- motion direction
- motion intensity variance across scenes

Reject meaningless motion added only to satisfy a metric, such as tiny pulses or constant glow.

A scene is not dynamic merely because opacity changes by a few percent.

Every scene should have a motion rationale tied to narration or visual purpose.

Output:
scene_id, active_motion_seconds, freeze_seconds, dominant_motion, motion_quality_score, evidence_frames, verdict.
