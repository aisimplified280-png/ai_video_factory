---
name: video-renderer
description: Runs and inspects the current Remotion production path and validates actual encoded output.
---
# Video Renderer

Use the current canonical production path.

Before rendering:
- verify the active production/runtime lock
- inspect edit_decisions, scene_plan, asset_manifest, and props lineage
- verify no stale legacy renderer is selected

After rendering:
- run ffprobe against the encoded MP4
- sample the full duration
- generate a contact sheet
- inspect actual frames for semantic relevance, composition, motion, depth, transitions, captions, and CTA
- run the visual-judge ensemble

Do not use create_short.py or legacy PIL renderer instructions unless explicitly auditing historical compatibility code.
